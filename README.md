# MC714 — 2º Trabalho: Algoritmos Distribuídos

Implementação de três algoritmos clássicos de sistemas distribuídos sobre uma
única camada de **troca de mensagens real por sockets TCP** (não há simulação
por arquivo):

1. **Relógio Lógico de Lamport**
2. **Exclusão Mútua** — Ricart-Agrawala (usa os timestamps de Lamport para ordenar pedidos)
3. **Eleição de Líder** — Bully (Garcia-Molina)

Escrito em **Python 3.11**, usando apenas a biblioteca padrão (`socket`, `threading`, `json`).
Sem dependências externas.

## Estrutura

```
src/
  lamport.py     # relógio de Lamport (thread-safe)
  transport.py   # servidor TCP + envio de mensagens (JSON delimitado por '\n')
  node.py        # nó que integra os 3 algoritmos
  main.py        # ponto de entrada de um nó
  config.py      # topologia padrão (execução local)
  test_local.py  # teste automatizado dos 3 algoritmos
Dockerfile
docker-compose.yml
Relatorio.docx   # relatório do trabalho
```

## Como executar

### Opção 1 — Local (mais rápido, para validar)

Sobe 3 nós em threads no mesmo processo, comunicando por TCP em `127.0.0.1`,
e exercita os três algoritmos automaticamente:

```bash
cd src
python3 test_local.py
```

### Opção 2 — Docker (ambiente distribuído de verdade)

Cada nó roda em um contêiner próprio numa rede bridge. O `docker-compose.yml`
já está configurado para demonstrar exclusão mútua (nós 1 e 2 disputam a seção
crítica) e eleição (nó 3 dispara a eleição e vence por ter o maior id):

```bash
docker compose up --build
```

Acompanhe os logs: cada linha mostra `[no X] (clock=N) <evento>`.

### Opção 3 — VMs distintas (ex.: GCloud)

Em cada VM, rode um nó passando a topologia completa via variável `PEERS`
(formato `id:host:porta,...`) e liberando as portas no firewall:

```bash
# VM do nó 2, por exemplo:
cd src
PEERS="1:10.0.0.1:5001,2:10.0.0.2:5002,3:10.0.0.3:5003" python3 main.py 2
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `PEERS`  | Topologia: `id:host:porta,id:host:porta,...` |
| `ROLE`   | `demo_cs` (pede seção crítica), `demo_elec` (inicia eleição) ou vazio (passivo) |
| `DELAY`  | Segundos a esperar antes de disparar a ação de demonstração |

## Protocolo de mensagens

Todas as mensagens são JSON com `type`, `src` (id do remetente) e `ts`
(timestamp de Lamport). Tipos: `HELLO`, `REQUEST`, `REPLY`, `ELECTION`,
`ANSWER`, `COORDINATOR`.

## Fontes

Implementação escrita do zero, baseada na descrição dos algoritmos em:
Lamport (1978), Ricart & Agrawala (1981), Garcia-Molina (1982) e
Tanenbaum & van Steen, *Distributed Systems*. Nenhum código de terceiros foi
copiado. Detalhes no `Relatorio.docx`.
