import os
import sys
import subprocess
import threading
import time
import signal

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

def main():
    admin = start("admin", ADMIN_PATH)
    consulta = start("consulta", CONSULTA_PATH)

    procs = [("admin", admin), ("consulta", consulta)]

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
            for name, p in procs:
                if p is not None and p.poll() is None:
                    alive = True
                elif p is not None and p.poll() is not None:
                    # já terminou, print returncode uma vez
                    print(f"[{name}] terminou (returncode={p.returncode})")
                    # set to None so we don't print repeatedly
                    for i in range(len(procs)):
                        if procs[i][0] == name:
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