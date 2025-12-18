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
# ⚠ ATENÇÃO: Confirme se este link é o do SEU Render atual!
API_URL = "https://nexus-server-kjfv.onrender.com" 
# (Se mudou o projeto no Render, atualize o link acima)

APP_NAME = "INSTA-HACKER PRO" 
VERSION = "v4.5.1 (Stable)"

console = Console()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_hwid():
    """Gera o DNA único do PC (Hardware ID)"""
    info = platform.node() + platform.machine() + platform.processor() + str(uuid.getnode())
    return hashlib.sha256(info.encode()).hexdigest()

def fake_loading():
    """Simula o software carregando módulos"""
    steps = [
        "Carregando Interface Gráfica...", 
        "Conectando API do Instagram...", 
        "Bypassing SSL Pinning...", 
        "Otimizando Memória RAM...",
        "Validando Tokens de Sessão..."
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
            time.sleep(random.uniform(0.5, 1.0))
            progress.advance(task)

def main():
    clear()
    console.print(Panel(Align.center(f"[bold white]{APP_NAME}[/]\n[dim]{VERSION}[/]"), style="blue", border_style="blue"))
    
    # --- 1. VERIFICAÇÃO DE LICENÇA ---
    
    # Procura na raiz (onde o comando é executado)
    key_file = "license.key"
    key = ""

    if os.path.exists(key_file):
        try:
            with open(key_file, "r") as f:
                key = f.read().strip()
            console.print(f"[dim]📂 Chave encontrada no arquivo: {key}[/]")
        except: pass

    if not key:
        console.print("[yellow]⚠ Nenhuma licença salva encontrada.[/]")
        key = Prompt.ask("[bold cyan]Digite sua Chave de Acesso[/]").strip()

    hwid = get_hwid()
    console.print("\n[dim]🔄 Conectando ao servidor Nexus na Nuvem...[/]")
    
    try:
        # PING DE VALIDAÇÃO INICIAL
        payload = {"key": key, "hwid": hwid, "cpu_percent": 0, "ram_mb": 0}
        resp = requests.post(f"{API_URL}/verify", json=payload, timeout=10)
        
        if resp.status_code == 200:
            console.print("[bold green]✅ ACESSO AUTORIZADO![/]")
            time.sleep(1)
            # Salva a chave na raiz para a próxima vez
            with open(key_file, "w") as f: f.write(key)
            
        else:
            detail = resp.json().get('detail', 'Chave rejeitada pelo servidor.')
            console.print(f"[bold red]⛔ ACESSO NEGADO: {detail}[/]")
            # Se a chave for ruim, apaga o arquivo para não travar o usuário num loop
            if os.path.exists(key_file): os.remove(key_file)
            sys.exit()
            
    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ ERRO CRÍTICO: Não foi possível conectar ao Render.[/]")
        console.print("[dim]Verifique sua internet ou se a URL no código está certa.[/]")
        sys.exit()
    except Exception as e:
        console.print(f"[red]Erro: {e}[/]")
        sys.exit()

    # --- 2. O SOFTWARE RODANDO ---
    
    fake_loading() 
    
    clear()
    console.print(Panel(Align.center(f"[bold green]{APP_NAME} ATIVO[/]\n[white]Monitorando tarefas... (Ctrl+C para sair)[/]"), border_style="green"))
    
    try:
        task_count = 0
        while True:
            time.sleep(3) # Tempo entre ações
            task_count += 1
            
            # Coleta dados reais
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().used / (1024 * 1024)
            
            # Tenta enviar dados
            try:
                resp = requests.post(f"{API_URL}/verify", json={
                    "key": key,
                    "hwid": hwid,
                    "cpu_percent": cpu,
                    "ram_mb": ram
                }, timeout=5)
                
                # AQUI ESTÁ A CORREÇÃO: VERIFICA SE O SERVIDOR AINDA ACEITA A CHAVE
                if resp.status_code == 200:
                    timestamp = time.strftime("%H:%M:%S")
                    console.print(f"[dim]{timestamp}[/] [cyan]Action #{task_count}[/] Curtindo foto... [dim](Ping: {int(cpu)}% CPU)[/]")
                
                elif resp.status_code == 404:
                    # O servidor reiniciou e esqueceu a chave
                    console.print("\n[bold red blink]⛔ ERRO FATAL: SESSÃO EXPIRADA![/]")
                    console.print("[red]O servidor na nuvem reiniciou e sua chave não existe mais no banco temporário.[/]")
                    console.print("[yellow]>> SOLUÇÃO: Vá no Painel Admin, Crie o Produto e Gere uma NOVA CHAVE.[/]")
                    if os.path.exists(key_file): os.remove(key_file) # Apaga a chave velha
                    break # Sai do loop
                
                else:
                    console.print(f"[red]⚠ Erro de conexão: Status {resp.status_code}[/]")

            except requests.exceptions.ConnectionError:
                console.print("[red]⚠ Falha de conexão (Internet oscilando?)[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Software encerrado.[/]")

if __name__ == "__main__":
    main()