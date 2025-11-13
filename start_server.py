import os
import sys
import subprocess
import threading
import time
import signal
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_PATH = os.path.join(SCRIPT_DIR, "start_admin_only.py")
CONSULTA_PATH = os.path.join(SCRIPT_DIR, "start_search_only.py")
PY = sys.executable  # interpreta atual

def read_stream(prefix, stream):
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            print(f"{prefix} {line.rstrip()}")
    finally:
        stream.close()

def start(name, path):
    if not os.path.exists(path):
        print(f"[erro] arquivo não encontrado: {path}")
        return None
    proc = subprocess.Popen([PY, path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1)
    threading.Thread(target=read_stream, args=(f"[{name}][OUT]", proc.stdout), daemon=True).start()
    threading.Thread(target=read_stream, args=(f"[{name}][ERR]", proc.stderr), daemon=True).start()
    return proc

def terminate(proc, name):
    if proc is None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception:
        pass
    print(f"[{name}] finalizado (returncode={proc.poll()})")


def _daily_restart_scheduler(procs_list):
    """Agendador que reinicia os processos filhos às 00:05 todos os dias.
    
    Calcula o tempo até a próxima ocorrência de 00:05, dorme, termina os processos
    atuais, aguarda 3 segundos e reinicia-os.
    """
    while True:
        now = datetime.now()
        # próxima ocorrência de 00:05
        # se já passou hoje, calcule para amanhã
        target_time = datetime(now.year, now.month, now.day, 0, 5, 0)
        if now >= target_time:
            target_time += timedelta(days=1)
        
        wait_seconds = (target_time - now).total_seconds()
        print(f"[scheduler] aguardando {wait_seconds:.0f}s até a próxima reinicialização às 00:05")
        time.sleep(wait_seconds)
        
        # reiniciar processos
        print("[scheduler] iniciando reinicialização diária (00:05)")
        try:
            for name, proc in procs_list:
                if proc is not None:
                    terminate(proc, name)
            
            time.sleep(3)  # aguardar 3 segundos
            
            # reiniciar
            for i in range(len(procs_list)):
                name, proc = procs_list[i]
                procs_list[i] = (name, start(name, ADMIN_PATH if name == "admin" else CONSULTA_PATH))
            
            print("[scheduler] reinicialização concluída")
        except Exception as e:
            print(f"[scheduler] erro durante reinicialização: {e}")

def main():
    admin = start("admin", ADMIN_PATH)
    consulta = start("consulta", CONSULTA_PATH)

    procs = [["admin", admin], ["consulta", consulta]]

    # Iniciar agendador de reinicialização diária às 00:05
    scheduler_thread = threading.Thread(target=_daily_restart_scheduler, args=(procs,), daemon=True)
    scheduler_thread.start()

    def handle_sigint(signum, frame):
        print("Recebido sinal de interrupção, finalizando processos...")
        for name, p in procs:
            terminate(p, name)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        # Espera até que ambos terminem
        while True:
            alive = False
            for i, (name, p) in enumerate(procs):
                if p is not None and p.poll() is None:
                    alive = True
                elif p is not None and p.poll() is not None:
                    # já terminou, print returncode uma vez
                    print(f"[{name}] terminou (returncode={p.returncode})")
                    # set to None so we don't print repeatedly
                    procs[i] = (name, None)
            if not alive:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        handle_sigint(None, None)

    # Certifica-se de terminar qualquer processo restante
    for name, p in procs:
        terminate(p, name)


if __name__ == "__main__":
    main()