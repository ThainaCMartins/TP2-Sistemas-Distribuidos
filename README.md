# TP2 — Transferência de Arquivos Peer-to-Peer (P2P)

**Disciplina:** Sistemas Distribuídos — CEFET-MG, 2026/2.
**Alunas:** Thainá Martins e Giovana Laura

## Objetivo

Implementar e avaliar uma aplicação de transferência de arquivos entre peers usando Python, TCP e `asyncio`. Cada peer pode solicitar blocos e disponibilizar aos demais os blocos já recebidos, mesmo antes de concluir o arquivo.

## Funcionalidades implementadas no projeto original

- Transferência de arquivos em blocos de **1024 ou 4096 bytes**.
- Protocolo de mensagens sobre TCP: `HELLO`, `HELLO_ACK`, `HAVE`, `BITFIELD`, `GET`, `BLOCK` e `ERROR`.
- Verificação de integridade por **SHA-256**, por bloco e por arquivo.
- Retomada de downloads após interrupções, reaproveitando blocos válidos.
- Compartilhamento simultâneo entre peers, sem tracker central.

## Organização do projeto

O pacote de entrega inclui a implementação Python (diretório `p2p/`), os testes automatizados (`tests/`), os scripts `validar_funcional.py` e `executar_testes.py`, as evidências (`evidencias/`) e os gráficos (`graficos/`).

Os arquivos de código, testes, evidências e gráficos estão publicados diretamente na raiz deste repositório. A documentação original do pacote está preservada em `docs/README_ORIGINAL.md`.

## Relatório final

O **relatório final de entrega** é o PDF publicado na raiz do repositório:

- [Relatório TP2 — Transferência de Arquivos Peer-to-Peer (PDF)](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/blob/main/Relatorio-TP2%20-%20Transfer%C3%AAncia%20de%20Arquivos%20Peer-to-Peer.pdf)

**Autoras:** Thainá Martins e Giovana Laura. Este PDF é a versão definitiva para consulta e entrega; não é necessário gerar um novo relatório com scripts antigos.

## Executar

Requer Python 3.12. No terminal, na raiz do projeto:

```bash
python -m unittest discover -v
python validar_funcional.py --out validacao_local
python executar_testes.py --out resultados_local
```

A execução experimental original ocorreu em Linux, usando conexões TCP locais. Os tempos obtidos em outros ambientes podem variar.

## Experimentos e resultados originais

A matriz experimental contém **24 cenários**, combinando seis tamanhos de arquivo, dois tamanhos de bloco (1024 e 4096 bytes) e dois totais de peers (2 e 4). As cópias foram verificadas por tamanho e SHA-256. Foram realizados ainda testes funcionais de encaminhamento entre peers, transferência bidirecional e retomada após interrupção.

Para arquivos maiores, a configuração de 4096 bytes apresentou tempos menores nas medições originais. Como os testes ocorreram em um único host e com uma execução por combinação, os resultados não comprovam desempenho em redes reais.

## GitHub Actions

O workflow em `.github/workflows/testes-p2p.yml` foi configurado para executar os testes e guardar evidências em uma máquina Linux. O código está publicado na raiz. Consulte a aba *Actions* para ver a situação real das execuções e baixar os artefatos de evidência.

