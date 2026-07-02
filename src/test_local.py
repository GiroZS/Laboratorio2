"""
Teste local: sobe 3 nós em threads (mesmo processo, mas comunicando por
sockets TCP de verdade em 127.0.0.1) e exercita os três algoritmos.

Roda sem Docker. Apenas para validação rápida.
"""

import threading
import time

from node import Node

PEERS = {
    1: ("127.0.0.1", 5001),
    2: ("127.0.0.1", 5002),
    3: ("127.0.0.1", 5003),
}


def main():
    nodes = {pid: Node(pid, PEERS) for pid in PEERS}
    for n in nodes.values():
        n.start()
    time.sleep(2)

    print("\n===== TESTE 1: Relógio de Lamport (já ativo em toda troca) =====\n")
    time.sleep(1)

    print("\n===== TESTE 2: Exclusão Mútua (Ricart-Agrawala) =====")
    print("Nós 1 e 3 pedem a seção crítica quase ao mesmo tempo.\n")

    def cs(n, work=1.5):
        n.request_critical_section()
        time.sleep(work)
        n.release_critical_section()

    t1 = threading.Thread(target=cs, args=(nodes[1],))
    t3 = threading.Thread(target=cs, args=(nodes[3],))
    t1.start()
    time.sleep(0.05)
    t3.start()
    t1.join()
    t3.join()
    time.sleep(1)

    print("\n===== TESTE 3: Eleição de Líder (Bully) =====")
    print("Nó 1 (menor id) inicia a eleição; nó 3 deve vencer.\n")
    nodes[1].start_election()
    time.sleep(3)

    print("\n===== Estado final dos líderes =====")
    for pid, n in nodes.items():
        print(f"  no {pid} reconhece lider = {n.leader}")

    for n in nodes.values():
        n.stop()
    print("\nTeste concluído.")


if __name__ == "__main__":
    main()
