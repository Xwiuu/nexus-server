import requests
import platform
import uuid
import hashlib
import time
import psutil
import sys
import os
import random
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.align import Align
from rich.prompt import Prompt

# --- CONFIGURAÇÕES ---
API_URL = "http://127.0.0.1:8000"
APP_NAME = "INSTA-HACKER PRO" 
VERSION = "v4.2.0"

console = Console()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_hwid():
    """Gera o DNA único do PC (Hardware ID)"""
    # Pega info da placa mãe, processador e nó de rede
    info = platform.node() + platform.machine() + platform.processor() + str(uuid.getnode())
    # Transforma num hash seguro
    return hashlib.sha256(info.encode()).hexdigest()

def fake_loading():
    """Simula o software carregando módulos (Pura estética)"""
    steps = [
        "Carregando Interface Gráfica...", 
        "Conectando API do Instagram...", 
        "Bypassing SSL Pinning...", 
        "Preparando Motores de Automação...",
        "Otimizando Memória..."
    ]
    
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(style="dim blue", complete_style="cyan"),
        transient=True
    ) as progress:
        task = progress.add_task("Init", total=len(steps))
        for step in steps:
            progress.update(task, description=step)
            time.sleep(random.uniform(0.5, 1.5)) # Tempo aleatório
            progress.advance(task)

def main():
    clear()
    # Banner do Software
    console.print(Panel(Align.center(f"[bold white]{APP_NAME}[/]\n[dim]{VERSION}[/]"), style="blue", border_style="blue"))
    
    # --- 1. VERIFICAÇÃO DE LICENÇA ---
    
    # Tenta ler arquivo local primeiro (pra não pedir a chave toda hora)
    key = ""
    if os.path.exists("license.key"):
        try:
            with open("license.key", "r") as f:
                key = f.read().strip()
            console.print(f"[dim]📂 Chave encontrada no arquivo: {key}[/]")
        except: pass

    # Se não achou arquivo, pede pro usuário digitar
    if not key:
        console.print("[yellow]⚠ Nenhuma licença ativa encontrada.[/]")
        key = Prompt.ask("[bold cyan]Digite sua Chave de Acesso[/]").strip()

    hwid = get_hwid()
    console.print("\n[dim]🔄 Conectando ao servidor Nexus...[/]")
    
    try:
        # PING DE VALIDAÇÃO (Momento da verdade)
        # Enviamos Key + HWID para ver se o servidor deixa entrar
        payload = {"key": key, "hwid": hwid, "cpu_percent": 0, "ram_mb": 0}
        resp = requests.post(f"{API_URL}/verify", json=payload, timeout=5)
        
        if resp.status_code == 200:
            console.print("[bold green]✅ ACESSO AUTORIZADO![/]")
            time.sleep(1)
            
            # Sucesso! Salva a chave para a próxima vez
            with open("license.key", "w") as f: f.write(key)
            
        else:
            # Erro (Banido, Inválido ou HWID Errado)
            detail = resp.json().get('detail', 'Erro desconhecido')
            console.print(f"[bold red]⛔ ACESSO NEGADO: {detail}[/]")
            
            # Se a chave for inválida, deletamos o arquivo local para não travar o usuário
            if os.path.exists("license.key"): os.remove("license.key")
            sys.exit()
            
    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ ERRO CRÍTICO: Servidor Offline ou Sem Internet.[/]")
        console.print("[dim]Verifique se o 'server/main.py' está rodando.[/]")
        sys.exit()
    except Exception as e:
        console.print(f"[red]Erro inesperado: {e}[/]")
        sys.exit()

    # --- 2. O SOFTWARE RODANDO (Simulação) ---
    
    fake_loading() # Efeito visual
    
    clear()
    console.print(Panel(Align.center(f"[bold green]{APP_NAME} RODANDO[/]\n[white]Pressione Ctrl+C para parar[/]"), border_style="green"))
    
    try:
        task_count = 0
        while True:
            # Simula o bot trabalhando
            time.sleep(3) 
            task_count += 1
            
            # Coleta dados reais do TEU PC para enviar ao Painel Tático
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().used / (1024 * 1024) # Converte bytes para MB
            
            # Envia Heartbeat pro Nexus (Telemetria)
            try:
                requests.post(f"{API_URL}/verify", json={
                    "key": key,
                    "hwid": hwid,
                    "cpu_percent": cpu,
                    "ram_mb": ram
                })
                
                # Log visual para o cliente saber que está tudo bem
                timestamp = time.strftime("%H:%M:%S")
                console.print(f"[dim]{timestamp}[/] [cyan]Action #{task_count}[/] Curtindo foto... [dim](Ping: {int(cpu)}% CPU | {int(ram)}MB RAM)[/]")
            
            except:
                console.print("[red]⚠ Falha ao contatar servidor... (Modo Offline Temporário)[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Software encerrado pelo usuário.[/]")

if __name__ == "__main__":
    main()