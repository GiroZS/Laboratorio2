"""
Nó de um sistema distribuído.

Integra três algoritmos clássicos, todos sobre troca de mensagens por TCP:

  1. Relógio Lógico de Lamport       (lamport.py)
  2. Exclusão Mútua: Ricart-Agrawala (usa timestamps de Lamport para ordenar pedidos)
  3. Eleição de Líder: Bully         (Garcia-Molina, 1982)

Tipos de mensagem (campo "type"):
  HELLO     - anúncio de presença (apenas log)
  REQUEST   - pedido de entrada na seção crítica (Ricart-Agrawala)
  REPLY     - permissão de entrada na seção crítica
  RELEASE   - aviso de saída da seção crítica (libera fila de adiados)
  ELECTION  - inicia/propaga eleição (Bully)
  ANSWER    - resposta "estou vivo e tenho id maior" (Bully)
  COORDINATOR - anúncio do novo líder (Bully)

Toda mensagem carrega "ts" (timestamp de Lamport) e "src" (id do remetente).
"""

import os
import sys
import threading
import time

from lamport import LamportClock
from transport import MessageServer, send_message


class Node:
    def __init__(self, node_id: int, peers: dict, host: str = "0.0.0.0", port: int = None):
        self.id = node_id
        # peers: {id: (host, port)} de TODOS os nós, inclusive este
        self.peers = peers
        self.host = host
        self.port = port if port is not None else peers[node_id][1]

        self.clock = LamportClock()

        # ---- Estado de exclusão mútua (Ricart-Agrawala) ----
        self.requesting_cs = False
        self.request_ts = None
        self.replies_needed = 0
        self.replies_received = 0
        self.deferred = set()           # nós cujo REPLY foi adiado
        self.cs_lock = threading.Lock()
        self.cs_can_enter = threading.Event()

        # ---- Estado de eleição (Bully) ----
        self.leader = None
        self.election_lock = threading.Lock()
        self.answer_received = threading.Event()

        self.server = MessageServer(self.host, self.port, self._on_message)

    # ------------------------------------------------------------------ #
    #  Infraestrutura
    # ------------------------------------------------------------------ #
    def log(self, msg: str):
        print(f"[no {self.id}] (clock={self.clock.time}) {msg}", flush=True)

    def start(self):
        self.server.start()
        time.sleep(1)
        threading.Thread(target=lambda: self._broadcast("HELLO", {}), daemon=True).start()
        self.log("no iniciado")

    def stop(self):
        self.server.stop()

    def _other_peers(self):
        return {pid: addr for pid, addr in self.peers.items() if pid != self.id}

    def _send(self, target_id: int, mtype: str, extra: dict):
        ts = self.clock.tick()
        msg = {"type": mtype, "src": self.id, "ts": ts}
        msg.update(extra)
        host, port = self.peers[target_id]
        send_message(host, port, msg)

    def _broadcast(self, mtype: str, extra: dict, only: list = None):
        targets = only if only is not None else list(self._other_peers().keys())
        for pid in targets:
            ts = self.clock.tick()
            msg = {"type": mtype, "src": self.id, "ts": ts}
            msg.update(extra)
            host, port = self.peers[pid]
            send_message(host, port, msg)

    # ------------------------------------------------------------------ #
    #  Recepção e despacho de mensagens
    # ------------------------------------------------------------------ #
    def _on_message(self, msg: dict):
        self.clock.update(msg.get("ts", 0))
        mtype = msg.get("type")
        src = msg.get("src")

        if mtype == "HELLO":
            self.log(f"recebeu HELLO de {src}")
        elif mtype == "REQUEST":
            self._handle_request(msg)
        elif mtype == "REPLY":
            self._handle_reply(msg)
        elif mtype == "RELEASE":
            self._handle_release(msg)
        elif mtype == "ELECTION":
            self._handle_election(msg)
        elif mtype == "ANSWER":
            self._handle_answer(msg)
        elif mtype == "COORDINATOR":
            self._handle_coordinator(msg)

    # ------------------------------------------------------------------ #
    #  EXCLUSÃO MÚTUA — Ricart-Agrawala
    # ------------------------------------------------------------------ #
    def request_critical_section(self):
        with self.cs_lock:
            self.requesting_cs = True
            self.request_ts = self.clock.tick()
            self.replies_received = 0
            self.replies_needed = len(self._other_peers())
            self.cs_can_enter.clear()

        self.log(f"PEDE seção crítica (ts={self.request_ts})")
        for pid in self._other_peers():
            self._send(pid, "REQUEST", {"req_ts": self.request_ts})

        if self.replies_needed == 0:
            self.cs_can_enter.set()
        self.cs_can_enter.wait()
        self.log(">>> ENTROU na seção crítica <<<")

    def release_critical_section(self):
        self.log("<<< SAIU da seção crítica >>>")
        with self.cs_lock:
            self.requesting_cs = False
            deferred = list(self.deferred)
            self.deferred.clear()
        for pid in deferred:
            self._send(pid, "REPLY", {})

    def _handle_request(self, msg):
        src = msg["src"]
        req_ts = msg["req_ts"]
        self.log(f"recebeu REQUEST de {src} (ts={req_ts})")

        with self.cs_lock:
            # Prioridade: menor (ts, id) ganha.
            mine = (self.request_ts, self.id)
            theirs = (req_ts, src)
            defer = self.requesting_cs and mine < theirs

        if defer:
            with self.cs_lock:
                self.deferred.add(src)
            self.log(f"ADIOU REPLY para {src} (tenho prioridade)")
        else:
            self._send(src, "REPLY", {})

    def _handle_reply(self, msg):
        src = msg["src"]
        with self.cs_lock:
            self.replies_received += 1
            self.log(f"recebeu REPLY de {src} ({self.replies_received}/{self.replies_needed})")
            if self.requesting_cs and self.replies_received >= self.replies_needed:
                self.cs_can_enter.set()

    def _handle_release(self, msg):
        # Mantido por compatibilidade; Ricart-Agrawala puro usa REPLY adiado.
        self.log(f"recebeu RELEASE de {msg['src']}")

    # ------------------------------------------------------------------ #
    #  ELEIÇÃO DE LÍDER — Bully (Garcia-Molina)
    # ------------------------------------------------------------------ #
    def start_election(self):
        higher = [pid for pid in self._other_peers() if pid > self.id]
        self.log(f"INICIA ELEIÇÃO. Nós com id maior: {higher}")

        if not higher:
            self._become_leader()
            return

        self.answer_received.clear()
        for pid in higher:
            self._send(pid, "ELECTION", {})

        # Aguarda ANSWER de algum nó maior.
        if self.answer_received.wait(timeout=3):
            self.log("alguem maior respondeu; aguardo o COORDINATOR")
        else:
            self.log("ninguem maior respondeu; eu venço")
            self._become_leader()

    def _become_leader(self):
        with self.election_lock:
            self.leader = self.id
        self.log(f"*** SOU O NOVO LÍDER (id={self.id}) ***")
        self._broadcast("COORDINATOR", {"leader": self.id})

    def _handle_election(self, msg):
        src = msg["src"]
        self.log(f"recebeu ELECTION de {src}")
        # Responde que está vivo (tem id maior que o remetente).
        self._send(src, "ANSWER", {})
        # E inicia sua própria eleição.
        threading.Thread(target=self.start_election, daemon=True).start()

    def _handle_answer(self, msg):
        self.log(f"recebeu ANSWER de {msg['src']}")
        self.answer_received.set()

    def _handle_coordinator(self, msg):
        leader = msg["leader"]
        with self.election_lock:
            self.leader = leader
        self.log(f"reconhece NOVO LÍDER = {leader}")


# ---------------------------------------------------------------------- #
#  Configuração via variáveis de ambiente / config.py
# ---------------------------------------------------------------------- #
def load_peers():
    """Lê PEERS no formato 'id:host:port,id:host:port,...'.
    Se ausente, usa a topologia local padrão (config.py)."""
    raw = os.environ.get("PEERS")
    if raw:
        peers = {}
        for part in raw.split(","):
            pid, host, port = part.split(":")
            peers[int(pid)] = (host, int(port))
        return peers
    from config import PEERS
    return PEERS
