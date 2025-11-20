import subprocess
import sys
import time

def start_servers():
    processes = []
    scripts = ["start_admin_only.py", "start_search_only.py"]

    print("Iniciando servidores...")

    for script in scripts:
        try:
            # Usa o mesmo interpretador Python que está executando este script
            p = subprocess.Popen([sys.executable, script])
            processes.append(p)
            print(f"Iniciado: {script} (PID: {p.pid})")
        except Exception as e:
            print(f"Erro ao iniciar {script}: {e}")

    try:
        # Mantém o script principal rodando para monitorar os processos
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"Processo {p.pid} terminou inesperadamente.")
                    # Se um processo cair, encerra o outro e sai
                    for proc in processes:
                        if proc.poll() is None:
                            proc.terminate()
                    return
    except KeyboardInterrupt:
        print("\nEncerrando servidores...")
        for p in processes:
            if p.poll() is None:
                p.terminate()
        print("Servidores encerrados.")

if __name__ == "__main__":
    start_servers()
