# TP2 — Transferência de Arquivos Peer-to-Peer

Trabalho Prático 2 de Sistemas Distribuídos (CEFET-MG, 2026/2).

Sistema P2P em Python usando TCP e asyncio. Os peers podem receber e compartilhar blocos simultaneamente, verificar a integridade por SHA-256 e retomar uma transferência interrompida.

## Situação da publicação

Este repositório está sendo preparado para receber o código, testes, documentação e evidências do projeto. **O README sozinho não representa a entrega completa.**

## Organização prevista

- `p2p/`: implementação do protocolo, armazenamento e peers
- `tests/`: testes automatizados
- `evidencias/`: resultados experimentais em CSV/JSON e registros
- `graficos/`: gráficos dos tempos de transferência
- `executar_testes.py`: matriz de experimentos
- `validar_funcional.py`: testes funcionais

## Resultados registrados na execução original

24 cenários concluídos, 48 cópias verificadas por SHA-256, 13 testes unitários e 3 experimentos funcionais (Linux, Python 3.12, TCP local). Os dados originais devem acompanhar o código na publicação final.
