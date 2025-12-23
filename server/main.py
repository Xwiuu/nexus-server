import os
import datetime
import uuid
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS ---
# Tenta pegar a URL do Render (Postgres). Se não tiver, usa arquivo local (SQLite).
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./nexus_v2_local.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. TABELAS (MODELOS) ---
class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)


class LicenseDB(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    product_code = Column(String, ForeignKey("products.code"))
    hwid = Column(String, nullable=True)  # A impressão digital do PC
    ip = Column(String, nullable=True)
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    is_banned = Column(Boolean, default=False)

    # Estatísticas de uso em tempo real
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    is_online = Column(Boolean, default=False)


# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)


# --- 🔄 AUTO-RESTAURAÇÃO (GARANTIA DE FUNCIONAMENTO) ---
# Esta função roda sempre que o servidor liga.
# Ela garante que o PerfScan exista, mesmo que o Render apague o banco.
def restore_products():
    db = SessionLocal()

    # Lista de Produtos Oficiais (Só o PerfScan agora)
    required_products = [{"code": "PERF", "name": "PerfScan Pro"}]

    print("🔄 [NEXUS KERNEL] Verificando Catálogo de Produtos...")

    for prod in required_products:
        # Verifica se já existe no banco
        exists = db.query(ProductDB).filter(ProductDB.code == prod["code"]).first()
        if not exists:
            print(f"⚠️ Produto faltando: {prod['name']} -> RECRIANDO AGORA...")
            new_prod = ProductDB(name=prod["name"], code=prod["code"])
            db.add(new_prod)
        else:
            print(f"✅ Produto verificado e ativo: {prod['name']}")

    db.commit()
    db.close()


# Executa a restauração IMEDIATAMENTE ao iniciar o script
restore_products()


# --- 3. APLICAÇÃO (API) ---
app = FastAPI()
# ⚠️ IMPORTANTE: Mantenha a mesma senha que está no seu dash.py
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- MODELOS DE DADOS (Pydantic) ---
class ProductCreate(BaseModel):
    name: str
    code: str


class LicenseCreate(BaseModel):
    product_code: str
    source: Optional[str] = "admin"


class VerifyPayload(BaseModel):
    key: str
    hwid: str
    cpu_percent: float
    ram_mb: float


# --- ROTAS DA API ---


@app.get("/")
def read_root():
    return {
        "system": "Nexus V2 Kernel",
        "status": "online",
        "product_focus": "PerfScan Pro",
        "security": "HWID LOCK ACTIVE",
    }


@app.post("/admin/product/add")
def add_product(prod: ProductCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Senha de Admin incorreta")
    db = SessionLocal()
    if db.query(ProductDB).filter(ProductDB.code == prod.code).first():
        db.close()
        raise HTTPException(400, "Este código de produto já existe.")
    new_prod = ProductDB(name=prod.name, code=prod.code)
    db.add(new_prod)
    db.commit()
    db.close()
    return {"status": "created", "product": prod.name}


@app.post("/admin/license/create")
def create_license(data: LicenseCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Senha de Admin incorreta")

    # Gera uma chave única: PERF-A1B2C3D4
    new_key = f"{data.product_code}-{str(uuid.uuid4())[:8].upper()}"

    db = SessionLocal()
    # Verifica se o produto existe antes de criar a chave
    if not db.query(ProductDB).filter(ProductDB.code == data.product_code).first():
        db.close()
        raise HTTPException(
            404, "Produto não encontrado. O servidor pode ter reiniciado sem restaurar."
        )

    db_license = LicenseDB(key=new_key, product_code=data.product_code)
    db.add(db_license)
    db.commit()
    db.close()
    return {"key": new_key, "status": "generated"}


# --- O GUARDIÃO (VERIFY) ---
# É aqui que o NexusGuard bate para perguntar se pode entrar
@app.post("/verify")
def verify_license(payload: VerifyPayload, request: Request = None):  # type: ignore
    db = SessionLocal()
    license = db.query(LicenseDB).filter(LicenseDB.key == payload.key).first()

    # 1. Chave existe?
    if not license:
        db.close()
        raise HTTPException(404, "Chave inválida ou não encontrada.")

    # 2. Está banida?
    if license.is_banned:
        db.close()
        raise HTTPException(
            403, "Esta licença foi banida permanentemente por violação dos termos."
        )

    # 3. HWID LOCK 2.0 (A Blindagem) 🛡️
    if license.hwid is None:
        # Primeiro uso: O Casamento! Grava o HWID deste PC para sempre.
        license.hwid = payload.hwid
    else:
        # Usos seguintes: Verifica fidelidade.
        if license.hwid != payload.hwid:
            db.close()
            # O "Amigo" recebe isto na cara:
            raise HTTPException(
                403,
                "ACESSO NEGADO: HWID Mismatch. Esta chave pertence a outro computador.",
            )

    # Se passou por tudo, atualiza status e libera
    license.last_login = datetime.datetime.utcnow()
    license.ip = request.client.host if request else "0.0.0.0"
    license.cpu_usage = payload.cpu_percent
    license.ram_usage = payload.ram_mb
    license.is_online = True

    db.commit()
    db.close()
    return {"status": "valid", "expires": "never"}


@app.get("/admin/stats")
def get_stats(admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Acesso não autorizado")
    db = SessionLocal()
    # Pega usuários ativos nos últimos 2 minutos
    limit_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=2)
    active = db.query(LicenseDB).filter(LicenseDB.last_login > limit_time).all()
    results = []
    for s in active:
        results.append(
            {
                "product": s.product_code,
                "key": s.key,
                "ip": s.ip,
                "cpu": s.cpu_usage,
                "ram": s.ram_usage,
            }
        )
    db.close()
    return {"sessions": results}
