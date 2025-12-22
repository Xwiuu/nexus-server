import os
import datetime
from fastapi import FastAPI, HTTPException, Header
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

# --- 1. CONFIGURAÇÃO DO BANCO (POSTGRESQL) ---
# Pega a URL do Render. Se não tiver (teste local), usa um arquivo local.
DATABASE_URL = os.getenv("DATABASE_URL")

# Correção para o Render (ele usa postgres:// mas o SQLAlchemy quer postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # Fallback para local se você for testar no PC antes de subir
    DATABASE_URL = "sqlite:///./nexus_v2_local.db"

# Criando o motor do banco
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. TABELAS (MODELOS) ---
class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)  # Ex: "INSTA"


class LicenseDB(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    product_code = Column(String, ForeignKey("products.code"))
    hwid = Column(String, nullable=True)  # Trava no Hardware ID
    ip = Column(String, nullable=True)
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    is_banned = Column(Boolean, default=False)

    # Status em tempo real (não salvo pra sempre, só snapshot)
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    is_online = Column(Boolean, default=False)


# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

# --- 3. APLICAÇÃO (API) ---
app = FastAPI()
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"  # Mantenha a mesma do dash.py


# Dependência para pegar o banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- SCHEMAS (Dados que vão e vêm) ---
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


# --- ROTAS ---


@app.get("/")
def read_root():
    return {"system": "Nexus V2 Kernel", "status": "online", "db": "PostgreSQL"}


# 1. CRIAR PRODUTO (Admin)
@app.post("/admin/product/add")
def add_product(prod: ProductCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Senha errada")

    db = SessionLocal()
    if db.query(ProductDB).filter(ProductDB.code == prod.code).first():
        db.close()
        raise HTTPException(400, "Produto já existe")

    new_prod = ProductDB(name=prod.name, code=prod.code)
    db.add(new_prod)
    db.commit()
    db.close()
    return {"status": "created", "product": prod.name}


# 2. GERAR LICENÇA (Admin)
@app.post("/admin/license/create")
def create_license(data: LicenseCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Senha errada")

    import uuid

    new_key = f"{data.product_code}-{str(uuid.uuid4())[:8].upper()}"

    db = SessionLocal()
    # Verifica se o produto existe
    if not db.query(ProductDB).filter(ProductDB.code == data.product_code).first():
        db.close()
        raise HTTPException(404, "Produto não encontrado. Crie o produto antes.")

    db_license = LicenseDB(key=new_key, product_code=data.product_code)
    db.add(db_license)
    db.commit()
    db.close()
    return {"key": new_key, "status": "generated"}


# 3. VERIFICAR / LOGIN (Cliente)
@app.post("/verify")
def verify_license(payload: VerifyPayload, request: Request = None):  # type: ignore
    db = SessionLocal()
    license = db.query(LicenseDB).filter(LicenseDB.key == payload.key).first()

    if not license:
        db.close()
        raise HTTPException(404, "Chave inválida ou não existe no banco.")

    if license.is_banned:
        db.close()
        raise HTTPException(403, "Esta licença foi banida.")

    # HWID LOCK (Segurança V2): Se for o primeiro uso, grava o HWID.
    # Se já tiver HWID e for diferente, bloqueia (opcional, aqui vou só atualizar para facilitar o teste)
    if not license.hwid:
        license.hwid = payload.hwid

    # Atualiza Status
    license.last_login = datetime.datetime.utcnow()
    license.ip = request.client.host if request else "0.0.0.0"  # Pega o IP real
    license.cpu_usage = payload.cpu_percent
    license.ram_usage = payload.ram_mb
    license.is_online = True

    db.commit()
    db.close()
    return {"status": "valid", "expires": "never"}


# 4. DASHBOARD STATS (Admin)
@app.get("/admin/stats")
def get_stats(admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Sai daqui curioso")

    db = SessionLocal()
    # Pega licenças que logaram nos últimos 2 minutos (considera "Online")
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


# Importante para pegar o IP real no FastAPI
from fastapi import Request
