import requests
import sys
import os
import time
import random
import psutil
from datetime import datetime
from collections import deque
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.text import Text
from rich.align import Align
from rich import box
from rich.prompt import Prompt
from pyfiglet import Figlet

# --- CONFIGURAÇÕES ---
# LINK TRAVADO NO CÓDIGO (Para garantir)
API_URL = "https://nexus-server-kjfv.onrender.com"
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"

console = Console()
log_history = deque(maxlen=8)

# --- BOOT SIMPLIFICADO ---
def cinematic_boot():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print("[bold yellow]INICIANDO MODO DE DIAGNÓSTICO VISUAL...[/]")
    time.sleep(1)

# --- BUSCA DE DADOS COM DEBUG VISUAL ---
def fetch_data():
    """Busca sessões. Se der erro, RETORNA O ERRO NA LISTA para ver na tabela."""
    try:
        # Tenta conectar
        resp = requests.get(f"{API_URL}/admin/stats", headers={"admin-secret": ADMIN_SECRET}, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            sessions = data.get('sessions', [])
            
            # SE A LISTA ESTIVER VAZIA MAS O STATUS FOR 200
            if not sessions:
                 return [{
                    "product": "AVISO",
                    "key": "BANCO VAZIO",
                    "ip": "Nenhum cliente conectado",
                    "cpu": 0,
                    "ram": 0
                }]
            return sessions
        else:
            # ERRO DE STATUS (Ex: 401, 500)
            return [{
                "product": "ERRO HTTP",
                "key": f"Status {resp.status_code}",
                "ip": "Verifique a Senha/Server",
                "cpu": 0,
                "ram": 0
            }]
            
    except Exception as e:
        # ERRO DE CONEXÃO (Ex: Internet, SSL, URL errada)
        error_msg = str(e)[:20] # Corta para caber
        return [{
            "product": "FALHA CRÍTICA",
            "key": "CONEXÃO",
            "ip": str(e), # AQUI VAI APARECER O MOTIVO REAL
            "cpu": 0,
            "ram": 0
        }]

def generate_log():
    return f"[yellow]Tentando conectar em: {API_URL}[/]\nUse Ctrl+C para sair."

def make_layout():
    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="body", ratio=1), Layout(name="footer", size=6))
    layout["body"].split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=1))
    return layout

def render_view(layout, sessions):
    layout["header"].update(Panel(Text("NEXUS DEBUG MODE", justify="center", style="bold black on yellow"), style="yellow"))
    
    # TABELA
    table = Table(expand=True, border_style="yellow", box=box.SIMPLE)
    table.add_column("STATUS/PRODUTO", style="bold")
    table.add_column("KEY / INFO", style="dim")
    table.add_column("MENSAGEM DE ERRO / IP", style="bold red") # Coluna de destaque
    table.add_column("CPU")
    
    for s in sessions:
        # Se for um dos nossos erros falsos, pinta de vermelho
        style = "red" if s['product'] in ["FALHA CRÍTICA", "ERRO HTTP"] else "green"
        
        table.add_row(
            f"[{style}]{s['product']}[/]", 
            s['key'],
            f"[{style}]{s['ip']}[/]", # O ERRO VAI APARECER AQUI
            str(s['cpu'])
        )
            
    layout["left"].update(Panel(table, title="🔍 DIAGNÓSTICO", border_style="yellow"))
    
    # DIREITA
    layout["right"].update(Panel("Aguardando dados...", title="HOST", border_style="white"))
    layout["footer"].update(Panel(generate_log(), title="LOGS"))

# --- LOOP PRINCIPAL ---
def main():
    cinematic_boot()
    layout = make_layout()
    
    with Live(layout, refresh_per_second=1, screen=True) as live:
        while True:
            sessions = fetch_data()
            render_view(layout, sessions)
            time.sleep(2) # Mais lento para dar tempo de ler

if __name__ == "__main__":
    main()