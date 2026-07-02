"""
Topologia padrão (execução local sem Docker).
Em Docker / VMs use a variável de ambiente PEERS para sobrescrever, por ex.:
  PEERS="1:node1:5001,2:node2:5002,3:node3:5003"
"""

PEERS = {
    1: ("127.0.0.1", 5001),
    2: ("127.0.0.1", 5002),
    3: ("127.0.0.1", 5003),
}
