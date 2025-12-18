import sqlite3
import datetime
import uuid
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional

# --- CONFIGURAÇÕES ---
app = FastAPI(title="Nexus Licensing System")
ADMIN_SECRET = "MINHA_SENHA_FORTE_123" 
DB_NAME = "nexus.db"

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Produtos
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (code TEXT PRIMARY KEY, name TEXT, created_at TEXT)''')
    
    # Licenças
    c.execute('''CREATE TABLE IF NOT EXISTS licenses 
                 (key TEXT PRIMARY KEY, product_code TEXT, hwid TEXT, status TEXT, 
                  source TEXT, created_at TEXT, expiration_date TEXT,
                  FOREIGN KEY(product_code) REFERENCES products(code))''')
    
    # Telemetria (AGORA COM IP)
    c.execute('''CREATE TABLE IF NOT EXISTS telemetry 
                 (license_key TEXT PRIMARY KEY, 
                  cpu_usage REAL, 
                  ram_usage_mb REAL, 
                  ip_address TEXT, 
                  updated_at TEXT)''')
                  
    conn.commit()
    conn.close()

init_db()

# --- MODELOS ---
class ProductCreate(BaseModel):
    name: str
    code: str

class LicenseCreate(BaseModel):
    product_code: str
    source: str = "manual"
    days_valid: int = 30

class LicenseCheck(BaseModel):
    key: str
    hwid: str
    cpu_percent: Optional[float] = 0.0
    ram_mb: Optional[float] = 0.0

# --- ROTAS ADMIN ---

@app.post("/admin/product/add")
def add_product(prod: ProductCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET: raise HTTPException(401, "Senha incorreta")
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.cursor().execute("INSERT INTO products VALUES (?, ?, ?)", 
                  (prod.code.upper(), prod.name, str(datetime.datetime.now())))
        conn.commit()
        return {"msg": "Criado"}
    except: raise HTTPException(400, "Erro ao criar")
    finally: conn.close()

@app.post("/admin/license/create")
def create_license(data: LicenseCreate, admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET: raise HTTPException(401, "Senha incorreta")
    key_suffix = str(uuid.uuid4()).split('-')[0].upper()
    new_key = f"{data.product_code.upper()}-{key_suffix}"
    expiration = datetime.datetime.now() + datetime.timedelta(days=data.days_valid)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verifica produto
    if not c.execute("SELECT name FROM products WHERE code=?", (data.product_code.upper(),)).fetchone():
        raise HTTPException(404, "Produto não existe")
        
    c.execute("INSERT INTO licenses VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (new_key, data.product_code.upper(), "", "ACTIVE", data.source, 
               str(datetime.datetime.now()), str(expiration)))
    conn.commit()
    conn.close()
    return {"key": new_key}

@app.get("/admin/stats")
def get_stats(admin_secret: str = Header(None)):
    if admin_secret != ADMIN_SECRET: raise HTTPException(401, "Senha incorreta")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # AGORA BUSCAMOS AS SESSÕES RECENTES (Últimos 10 min)
    # Mostra quem está ONLINE agora
    query = """
    SELECT l.product_code, t.license_key, t.ip_address, t.cpu_usage, t.ram_usage_mb
    FROM telemetry t
    JOIN licenses l ON t.license_key = l.key
    ORDER BY t.updated_at DESC
    LIMIT 20
    """
    c.execute(query)
    
    sessions = []
    for row in c.fetchall():
        sessions.append({
            "product": row[0],
            "key": row[1],
            "ip": row[2],
            "cpu": row[3],
            "ram": row[4]
        })
    
    conn.close()
    return {"sessions": sessions}

# --- ROTA CLIENTE ---

@app.post("/verify")
def verify_license(data: LicenseCheck, request: Request): # <--- REQUEST INJETADO AQUI
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Pega IP Real
    client_ip = request.client.host
    
    row = c.execute("SELECT hwid, status FROM licenses WHERE key=?", (data.key,)).fetchone()
    if not row: raise HTTPException(404, "Chave inválida")
    
    saved_hwid, status = row
    if status != "ACTIVE": raise HTTPException(403, "Bloqueado")
    
    if not saved_hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (data.hwid, data.key))
    elif saved_hwid != data.hwid:
        raise HTTPException(403, "HWID Inválido")

    # Salva Telemetria com IP
    c.execute("INSERT OR REPLACE INTO telemetry VALUES (?, ?, ?, ?, ?)",
              (data.key, data.cpu_percent, data.ram_mb, client_ip, str(datetime.datetime.now())))
    
    conn.commit()
    conn.close()
    return {"status": "valid"}