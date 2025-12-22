import os
import datetime
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

# --- 1. CONFIGURAÇÃO DO BANCO (POSTGRESQL) ---
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

    # Status em tempo real
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Float, default=0.0)
    is_online = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)

# --- 3. APLICAÇÃO (API) ---
app = FastAPI()
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    return {
        "system": "Nexus V2 Kernel",
        "status": "online",
        "security": "HWID LOCK ACTIVE",
    }


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


@app.post("/admin/license/create")
def create_license(data: LicenseCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET:
        raise HTTPException(401, "Senha errada")
    import uuid

    new_key = f"{data.product_code}-{str(uuid.uuid4())[:8].upper()}"
    db = SessionLocal()
    if not db.query(ProductDB).filter(ProductDB.code == data.product_code).first():
        db.close()
        raise HTTPException(404, "Produto não encontrado.")
    db_license = LicenseDB(key=new_key, product_code=data.product_code)
    db.add(db_license)
    db.commit()
    db.close()
    return {"key": new_key, "status": "generated"}


# --- O GUARDIÃO (VERIFY) ---
@app.post("/verify")
def verify_license(payload: VerifyPayload, request: Request = None):  # type: ignore
    db = SessionLocal()
    license = db.query(LicenseDB).filter(LicenseDB.key == payload.key).first()

    # 1. Chave existe?
    if not license:
        db.close()
        raise HTTPException(404, "Chave inválida.")

    # 2. Está banida?
    if license.is_banned:
        db.close()
        raise HTTPException(403, "Esta licença foi banida permanentemente.")

    # 3. HWID LOCK 2.0 (A Blindagem) 🛡️
    if license.hwid is None:
        # Primeiro uso: O Casamento! Grava o HWID deste PC.
        license.hwid = payload.hwid
    else:
        # Usos seguintes: Verifica fidelidade.
        if license.hwid != payload.hwid:
            db.close()
            # O "Amigo" recebe isto na cara:
            raise HTTPException(
                403,
                "ACESSO NEGADO: Esta chave está vinculada a outro computador (HWID Mismatch). Compre sua própria licença.",
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
        raise HTTPException(401, "Sai daqui")
    db = SessionLocal()
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
