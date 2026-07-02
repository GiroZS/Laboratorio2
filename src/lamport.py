"""
Relógio Lógico de Lamport.

Regras (Lamport, 1978):
  1. Antes de cada evento local, incrementa o relógio.
  2. Ao enviar uma mensagem, incrementa e anexa o timestamp.
  3. Ao receber uma mensagem com timestamp t:
        clock = max(clock, t) + 1
"""

import threading


class LamportClock:
    def __init__(self, start: int = 0):
        self._time = start
        self._lock = threading.Lock()

    @property
    def time(self) -> int:
        with self._lock:
            return self._time

    def tick(self) -> int:
        """Evento local / antes de enviar: incrementa e retorna."""
        with self._lock:
            self._time += 1
            return self._time

    def update(self, received_ts: int) -> int:
        """Ao receber uma mensagem: clock = max(local, recebido) + 1."""
        with self._lock:
            self._time = max(self._time, received_ts) + 1
            return self._time
