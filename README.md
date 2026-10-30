# TP2 — Transferência de Arquivos Peer-to-Peer (P2P)

**Disciplina:** Sistemas Distribuídos — CEFET-MG, 2026/2.
**Alunas:** Thainá Martins e Giovanna Laura

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

**Atenção:** um arquivo ZIP não disponibiliza seu conteúdo como código navegável no GitHub. É necessário extrair o pacote e publicar os arquivos e pastas separadamente. Confirme que `p2p/`, `tests/` e os scripts estão presentes antes de executar o workflow.

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

O workflow em `.github/workflows/testes-p2p.yml` foi configurado para executar os testes e guardar evidências em uma máquina Linux. Ele **só poderá executar corretamente quando o código e os scripts estiverem publicados**. Consulte a aba *Actions* para ver a situação real das execuções.
