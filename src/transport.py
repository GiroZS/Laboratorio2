"""
Camada de transporte por troca de mensagens (sockets TCP).

Cada nó abre um servidor TCP e se conecta aos demais sob demanda.
As mensagens são objetos JSON delimitados por '\n' (newline-delimited JSON).

Esta é troca de mensagens REAL pela rede (não simulação via arquivo).
Funciona tanto entre contêineres Docker quanto entre VMs (basta ajustar
os endereços no arquivo de configuração / variáveis de ambiente).
"""

import json
import socket
import threading
import time


def send_message(host: str, port: int, message: dict, retries: int = 30, delay: float = 0.5) -> bool:
    """Envia uma mensagem JSON para (host, port). Tenta reconectar enquanto o
    destino ainda não estiver no ar (útil na subida simultânea dos contêineres)."""
    payload = (json.dumps(message) + "\n").encode("utf-8")
    last_err = None
    for _ in range(retries):
        try:
            with socket.create_connection((host, port), timeout=3) as sock:
                sock.sendall(payload)
            return True
        except (ConnectionRefusedError, socket.gaierror, OSError) as e:
            last_err = e
            time.sleep(delay)
    print(f"[transport] falha ao enviar para {host}:{port}: {last_err}")
    return False


class MessageServer(threading.Thread):
    """Servidor TCP que recebe mensagens e as entrega a um callback."""

    def __init__(self, host: str, port: int, on_message):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.on_message = on_message
        self._running = True
        self._sock = None

    def run(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(64)
        while self._running:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        with conn:
            buffer = b""
            while self._running:
                try:
                    data = conn.recv(4096)
                except OSError:
                    break
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        message = json.loads(line.decode("utf-8"))
                        self.on_message(message)
                    except json.JSONDecodeError:
                        pass

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
