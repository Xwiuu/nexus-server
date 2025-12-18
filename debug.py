import requests
import platform
import uuid
import hashlib
import sys

# --- COLOQUE O SEU LINK DO RENDER AQUI ---
API_URL = "https://nexus-server-kjfv.onrender.com" 
# (Garanta que não tem barra / no final)

def get_hwid():
    info = platform.node() + platform.machine() + platform.processor() + str(uuid.getnode())
    return hashlib.sha256(info.encode()).hexdigest()

def debug_connection():
    print(f"\n🔍 --- INICIANDO DIAGNÓSTICO ---")
    print(f"📡 Alvo: {API_URL}")
    
    # 1. Teste de Ping (O servidor existe?)
    print("\n1. Testando se o servidor está online...")
    try:
        r = requests.get(f"{API_URL}/admin/stats", headers={"admin-secret": "MINHA_SENHA_FORTE_123"}, timeout=10)
        print(f"   STATUS: {r.status_code}")
        if r.status_code == 200:
            print("   ✅ Servidor respondeu! (Ele está vivo)")
        else:
            print(f"   ❌ Servidor respondeu com erro: {r.text}")
    except Exception as e:
        print(f"   ❌ FALHA TOTAL: Não consegui conectar. Verifique a URL. Erro: {e}")
        return

    # 2. Teste da Chave (A chave existe no banco?)
    key = input("\n🔑 Digite a Chave (Key) para testar: ").strip()
    hwid = get_hwid()
    
    print(f"\n2. Tentando validar chave: {key}")
    payload = {
        "key": key,
        "hwid": hwid,
        "cpu_percent": 10.0,
        "ram_mb": 1024.0
    }
    
    try:
        # AQUI É O PULO DO GATO: Vamos imprimir a resposta crua
        resp = requests.post(f"{API_URL}/verify", json=payload)
        
        print(f"   📥 Resposta do Servidor (Status Code): {resp.status_code}")
        print(f"   📜 Conteúdo da Resposta: {resp.text}")
        
        if resp.status_code == 200:
            print("\n🎉 SUCESSO! A chave funciona. O problema estava no script do cliente antigo.")
        elif resp.status_code == 404:
            print("\n⛔ ERRO 404: O Servidor diz que essa chave NÃO EXISTE.")
            print("   👉 Solução: O banco de dados do Render reiniciou e limpou tudo.")
            print("   👉 Você TEM que ir no Dash, criar o produto e a chave DE NOVO agora.")
        elif resp.status_code == 403:
             print("\n⛔ ERRO 403: Chave banida ou HWID incorreto.")
        else:
            print("\n⚠ ERRO DESCONHECIDO. Mande o print disso.")
            
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")

if __name__ == "__main__":
    debug_connection()