"""
Ponto de entrada de um nó.

Uso:
  python main.py <node_id>

Variáveis de ambiente:
  PEERS   topologia (ver node.load_peers)
  ROLE    'demo_cs'  -> este nó dispara um pedido de seção crítica
          'demo_elec'-> este nó dispara uma eleição
          (vazio)    -> nó passivo, apenas responde
  DELAY   segundos a esperar antes de disparar a ação (default 5)
"""

import os
import sys
import time

from node import Node, load_peers


def main():
    if len(sys.argv) < 2:
        print("uso: python main.py <node_id>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    peers = load_peers()
    if node_id not in peers:
        print(f"node_id {node_id} nao esta em PEERS={peers}")
        sys.exit(1)

    node = Node(node_id, peers)
    node.start()

    role = os.environ.get("ROLE", "")
    delay = float(os.environ.get("DELAY", "5"))

    if role == "demo_cs":
        time.sleep(delay)
        node.request_critical_section()
        time.sleep(2)  # simula trabalho dentro da seção crítica
        node.release_critical_section()
    elif role == "demo_elec":
        time.sleep(delay)
        node.start_election()

    # mantém o nó vivo para receber mensagens
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()


if __name__ == "__main__":
    main()
