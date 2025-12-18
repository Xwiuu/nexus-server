import requests
import json

# --- SUAS CONFIGURAÇÕES ---
# ⚠ TEM QUE SER O LINK DO RENDER (SEM BARRA NO FINAL)
API_URL = "https://nexus-server-kjfv.onrender.com"
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"

print(f"📡 Tentando conectar em: {API_URL}")
print("🔍 Buscando dados em /admin/stats...")

try:
    response = requests.get(
        f"{API_URL}/admin/stats", 
        headers={"admin-secret": ADMIN_SECRET},
        timeout=10
    )
    
    print(f"\n📥 STATUS CODE: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ DADOS RECEBIDOS:\n{json.dumps(data, indent=4)}")
        
        sessions = data.get('sessions', [])
        if len(sessions) == 0:
            print("\n⚠ A lista de sessões está VAZIA.")
            print("Isso significa que o servidor não achou ninguém conectado no banco de dados.")
        else:
            print(f"\n🎉 SUCESSO! Encontrei {len(sessions)} conexões ativas.")
    else:
        print(f"❌ ERRO: O servidor respondeu com {response.status_code}")
        print(f"RESPOSTA: {response.text}")

except Exception as e:
    print(f"\n💀 ERRO CRÍTICO DE CONEXÃO: {e}")
    print("Verifique se a URL está certa e se você tem internet.")