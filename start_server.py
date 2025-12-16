import subprocess
import sys
import time
import os
import signal
from datetime import datetime

# ANSI Colors for friendly output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, color=Colors.ENDC, prefix="SYSTEM"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.BLUE}[{timestamp}]{Colors.ENDC} {color}[{prefix}] {message}{Colors.ENDC}")

def print_banner():
    print(f"{Colors.GREEN}{Colors.BOLD}")
    print("  /$$$$$$            /$$                         /$$ /$$$$$$$                            ")
    print(" /$$__  $$          | $$                        | $$| $$__  $$                           ")
    print("| $$  \\__/  /$$$$$$$| $$$$$$$   /$$$$$$   /$$$$$$ | $$| $$  \\ $$ /$$$$$$   /$$$$$$$ /$$$$$$$")
    print("|  $$$$$$  /$$_____/| $$__  $$ /$$__  $$ /$$__  $$| $$| $$$$$$$/|____  $$ /$$_____//$$_____/")
    print(" \\____  $$| $$      | $$  \\ $$| $$  \\ $$| $$  \\ $$| $$| $$____/  /$$$$$$$|  $$$$$$|  $$$$$$")
    print(" /$$  \\ $$| $$      | $$  | $$| $$  | $$| $$  | $$| $$| $$      /$$__  $$ \\____  $$\\____  $$")
    print("|  $$$$$$/|  $$$$$$$| ??  | $$|  $$$$$$/|  $$$$$$/| $$| $$     |  $$$$$$$ /$$$$$$$//$$$$$$$/")
    print(" \\______/  \\_______/|__/  |__/ \\______/  \\______/ |__/|__/      \\_______/|_______/|_______/ ")
    print(f"{Colors.ENDC}")
    print(f"{Colors.CYAN}================================================================================{Colors.ENDC}")
    print(f" {Colors.BOLD}Sistema Iniciado e Pronto para Uso{Colors.ENDC}")
    print(f"{Colors.CYAN}================================================================================{Colors.ENDC}")
    log(f"Painel Administrativo: {Colors.BOLD}http://localhost:5000{Colors.ENDC} (Login/Config)", Colors.GREEN)
    log(f"Consulta Pública:      {Colors.BOLD}http://localhost:5010{Colors.ENDC} (Alunos/Pais)", Colors.GREEN)
    print(f"{Colors.CYAN}================================================================================{Colors.ENDC}\n")

PROCESSES = {}
SCRIPTS = {
    "start_admin_only.py": "ADMIN",
    "start_search_only.py": "SEARCH"
}

def start_process(script_name):
    """Inicia um processo e o registra."""
    try:
        # Usa sys.executable para garantir que usamos o mesmo python
        p = subprocess.Popen([sys.executable, script_name])
        PROCESSES[script_name] = p
        log(f"Iniciado: {SCRIPTS[script_name]} (PID: {p.pid})", Colors.GREEN)
    except Exception as e:
        log(f"Falha ao iniciar {script_name}: {e}", Colors.FAIL)

def stop_all():
    """Encerra todos os processos filhos."""
    print("\n")
    log("Encerrando serviços...", Colors.WARNING)
    for script, p in PROCESSES.items():
        if p.poll() is None:
            p.terminate()
            log(f"Processo {SCRIPTS[script]} parado.", Colors.WARNING)
    log("Sistema encerrado.", Colors.FAIL)
    sys.exit(0)

def main():
    # Habilitar cores ANSI no Windows terminal legacy se necessário
    os.system('') 

    print_banner()

    # Iniciar processos
    for script in SCRIPTS:
        start_process(script)

    try:
        while True:
            time.sleep(2)
            for script, p in list(PROCESSES.items()):
                # Verifica se o processo morreu
                if p.poll() is not None:
                    log(f"ALERTA: O serviço {SCRIPTS[script]} parou inesperadamente.", Colors.FAIL)
                    log(f"Reiniciando {SCRIPTS[script]} em 1 segundo...", Colors.WARNING)
                    time.sleep(1)
                    start_process(script)
                    
    except KeyboardInterrupt:
        stop_all()

if __name__ == "__main__":
    main()
