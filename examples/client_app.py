import requests
import platform
import uuid
import hashlib
import time
import psutil # Para ler CPU/RAM
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()

# URL do Servidor (Na vida real, seria https://seu-app.onrender.com)
API_URL = "http://127.0.0.1:8000"

def get_machine_fingerprint():
    """Gera o DNA único do PC"""
    info = platform.node() + platform.machine() + platform.processor() + str(uuid.getnode())
    return hashlib.sha256(info.encode()).hexdigest()

def main():
    console.clear()
    console.print(Panel("[bold cyan]🤖 SUPER INSTA BOT 3000 (Cliente)[/]", expand=False))
    
    # 1. Autenticação
    key = console.input("[yellow]Digite sua Licença de Acesso: [/]").strip()
    hwid = get_machine_fingerprint()
    
    console.print("\n[dim]🔄 Conectando ao servidor Nexus...[/]")
    
    try:
        # Tenta validar a licença
        payload = {
            "key": key,
            "hwid": hwid,
            "cpu_percent": 0,
            "ram_mb": 0
        }
        response = requests.post(f"{API_URL}/verify", json=payload)
        
        if response.status_code == 200:
            console.print("[bold green]✅ ACESSO AUTORIZADO![/]")
            console.print(f"[dim]Mensagem do Server: {response.json()['message']}[/]\n")
            
            # --- AQUI COMEÇA O SEU PROGRAMA REAL ---
            iniciar_programa_real(key, hwid)
            
        else:
            console.print(f"[bold red]⛔ ACESSO NEGADO: {response.json().get('detail')}[/]")
            sys.exit()
            
    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ Erro: Não foi possível conectar ao servidor de licença.[/]")

def iniciar_programa_real(key, hwid):
    """Simula o bot rodando e enviando telemetria"""
    console.print("[bold white]🚀 O Bot está rodando... (Pressione Ctrl+C para parar)[/]")
    
    count = 0
    while True:
        try:
            time.sleep(5) # O bot trabalha...
            
            # Coleta dados do PC para enviar ao Painel
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().used / (1024 * 1024) # Converte para MB
            
            count += 1
            console.print(f"[dim]⚡ Loop {count}: Enviando heartbeat... (CPU: {cpu}% | RAM: {int(ram)}MB)[/]")
            
            # Envia Ping para o servidor (Estou vivo + Meus dados)
            try:
                requests.post(f"{API_URL}/verify", json={
                    "key": key,
                    "hwid": hwid,
                    "cpu_percent": cpu,
                    "ram_mb": ram
                })
            except:
                pass # Se falhar o ping, o bot continua rodando (opcional bloquear)
                
        except KeyboardInterrupt:
            console.print("\n[red]Bot encerrado pelo usuário.[/]")
            break

if __name__ == "__main__":
    main()