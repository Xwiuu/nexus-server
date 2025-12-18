import requests
import sys
import os
import time
import random
import psutil
from datetime import datetime
from collections import deque

# --- IMPORTAÇÕES VISUAIS ---
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
API_URL = "http://127.0.0.1:8000"
ADMIN_SECRET = "MINHA_SENHA_FORTE_123"

console = Console()
log_history = deque(maxlen=8)


# --- 1. INTRO CINEMATOGRÁFICA ---
def cinematic_boot():
    os.system("cls" if os.name == "nt" else "clear")

    # Efeito Matrix Rápido
    for _ in range(15):
        line = "".join([random.choice("01XYZA") for _ in range(80)])
        console.print(f"[dim green]{line}[/]")
        time.sleep(0.02)
    os.system("cls" if os.name == "nt" else "clear")

    f = Figlet(font="block")
    console.print(f"[bold cyan]{f.renderText('NEXUS')}[/]", justify="center")
    console.print(
        "[bold white on black] INICIANDO RASTREAMENTO GLOBAL... [/]", justify="center"
    )

    # Barra falsa
    with Progress(
        SpinnerColumn("aesthetic"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=30, style="dim green", complete_style="green"),
        transient=True,
    ) as progress:
        task = progress.add_task("Conectando Satélites...", total=100)
        while not progress.finished:
            progress.update(task, advance=2)
            time.sleep(0.02)
    time.sleep(0.5)


# --- 2. LAYOUT DO MONITORAMENTO (COM IP) ---


def fetch_data():
    """Busca sessões ativas com IP"""
    try:
        resp = requests.get(
            f"{API_URL}/admin/stats",
            headers={"admin-secret": ADMIN_SECRET},
            timeout=0.2,
        )
        return resp.json()["sessions"] if resp.status_code == 200 else []
    except:
        return []


def generate_log():
    cmds = ["UPLINK", "PACKET", "TRACE", "PING", "HANDSHAKE"]
    msg = f"[dim green]{datetime.now().strftime('%H:%M:%S')}[/] [bold cyan]{random.choice(cmds)}[/] stream:active status:[white]200[/]"
    log_history.append(msg)
    return "\n".join(log_history)


def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=8),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=2), Layout(name="right", ratio=1)
    )
    return layout


def render_view(layout, sessions):
    # HEADER
    layout["header"].update(
        Panel(
            Text(
                "NEXUS GLOBAL MONITORING v4.5 [LIVE]",
                justify="center",
                style="bold white on blue",
            ),
            style="blue",
            box=box.HEAVY_EDGE,
        )
    )

    # ESQUERDA: LISTA DE SESSÕES (COM IP)
    table = Table(expand=True, border_style="green", box=box.SIMPLE)
    table.add_column("PRODUTO", style="cyan bold")
    table.add_column("LICENSE KEY", style="dim white")
    table.add_column("IP ADDRESS", style="bold yellow")
    table.add_column("CPU", justify="right")
    table.add_column("RAM", justify="right")

    if not sessions:
        table.add_row("Procurando sinais...", "-", "-", "-", "-")
    else:
        for s in sessions:
            short_key = s["key"][:4] + ".." + s["key"][-3:]
            cpu_style = "green" if s["cpu"] < 50 else "red blink"
            table.add_row(
                s["product"],
                short_key,
                s["ip"],
                f"[{cpu_style}]{s['cpu']}%[/]",
                f"{int(s['ram'])}MB",
            )

    layout["left"].update(
        Panel(table, title="🌍 [bold green]ACTIVE CONNECTIONS[/]", border_style="green")
    )

    # DIREITA: ADMIN STATS
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    graph = "█" * int(cpu / 5)

    info = f"""
[bold white]HOST LOCAL[/]
CPU: [green]{cpu}%[/]
RAM: [yellow]{ram}%[/]

[dim]LOAD:[/][red]{graph}[/]
    """
    layout["right"].update(Panel(info, title="🖥️ ADMIN NODE", border_style="white"))

    # FOOTER
    layout["footer"].update(
        Panel(
            generate_log()
            + "\n\n[blink yellow]PRESSIONE CTRL+C PARA ABRIR O MENU TÁTICO[/]",
            title="LOGS",
            border_style="dim",
        )
    )


# --- 3. MENU TÁTICO (O VISUAL FODA VOLTOU) ---
def action_menu():
    os.system("cls" if os.name == "nt" else "clear")

    # CABEÇALHO DE ALERTA
    alert = Text(
        "⚠ SYSTEM OVERRIDE DETECTED ⚠",
        justify="center",
        style="bold white on red blink",
    )
    console.print(Panel(alert, border_style="red"))
    console.print(Align.center("[dim]Monitoramento pausado. Aguardando ordens...[/]\n"))

    # TABELA TÁTICA
    table = Table(expand=True, border_style="blue", box=box.HEAVY_HEAD)
    table.add_column("ID", justify="center", style="bold cyan", width=4)
    table.add_column("PROTOCOL / ACTION", style="bold white")
    table.add_column("STATUS", justify="center")

    table.add_row("[1]", "DEPLOY_PAYLOAD (Criar Produto)", "[green]READY[/]")
    table.add_row("[2]", "GENERATE_TOKEN (Gerar Chave)", "[green]READY[/]")
    table.add_row("", "", "")
    table.add_row("[3]", "RESUME_UPLINK (Voltar ao Monitor)", "[blue]WAITING[/]")
    table.add_row("[0]", "KILL_SESSION (Sair)", "[red]DANGER[/]")

    console.print(table)

    # USER INFO
    console.print(
        Panel(
            f"[bold yellow]USER:[/] root   [bold yellow]IP:[/] 127.0.0.1   [bold yellow]ID:[/] {random.randint(1000,9999)}",
            border_style="dim",
        )
    )

    # INPUT ESTILIZADO
    try:
        opt = Prompt.ask(
            "\n[bold red]root@nexus:~/admin#[/]", choices=["1", "2", "3", "0"]
        )
    except KeyboardInterrupt:
        sys.exit()

    # LÓGICA DOS COMANDOS
    if opt == "1":
        console.rule("[bold cyan]FACTORY PROTOCOL[/]")
        name = Prompt.ask("[cyan]Nome do Produto[/]")
        code = Prompt.ask("[cyan]Código Único[/]")
        try:
            requests.post(
                f"{API_URL}/admin/product/add",
                json={"name": name, "code": code},
                headers={"admin-secret": ADMIN_SECRET},
            )
            console.print("[bold green]>> SUCESSO. PRODUTO REGISTRADO.[/]")
            time.sleep(1)
        except:
            pass
        action_menu()

    elif opt == "2":
        console.rule("[bold green]ACCESS PROTOCOL[/]")
        code = Prompt.ask("[green]Target Product[/]")
        src = Prompt.ask("[green]Client Source[/]")

        with console.status("[bold green]Criptografando chave...[/]", spinner="dots12"):
            time.sleep(1)
            try:
                r = requests.post(
                    f"{API_URL}/admin/license/create",
                    json={"product_code": code, "source": src},
                    headers={"admin-secret": ADMIN_SECRET},
                )

                # CHAVE EM DESTAQUE
                console.print(
                    Panel(
                        Align.center(f"[bold yellow]{r.json()['key']}[/]"),
                        title="ACCESS TOKEN",
                        border_style="green",
                        padding=(1, 5),
                    )
                )
            except:
                console.print("[red]Erro ao criar chave.[/]")

        Prompt.ask("\n[dim]Enter para continuar...[/]")
        action_menu()

    elif opt == "3":
        return
    elif opt == "0":
        sys.exit()


# --- LOOP PRINCIPAL ---
def main():
    try:
        requests.get(API_URL)
    except:
        console.print("[red]ERRO: Servidor Offline.[/]")
        return

    cinematic_boot()
    layout = make_layout()

    while True:
        try:
            with Live(layout, refresh_per_second=2, screen=True) as live:
                while True:
                    sessions = fetch_data()
                    render_view(layout, sessions)
                    time.sleep(1)
        except KeyboardInterrupt:
            action_menu()


if __name__ == "__main__":
    main()
