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

O **relatório histórico anterior à reestruturação** é o PDF publicado na raiz do repositório:

- [Relatório TP2 — Transferência de Arquivos Peer-to-Peer (PDF)](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/blob/main/Relatorio-TP2%20-%20Transfer%C3%AAncia%20de%20Arquivos%20Peer-to-Peer.pdf)

**Autoras:** Thainá Martins e Giovana Laura. Este PDF documenta a versão anterior e **não deve ser apresentado como relatório final da nova implementação** até a nova bateria de testes ser concluída.

## Executar

Requer Python 3.12. No terminal, na raiz do projeto:

```bash
python -m unittest discover -v
python validar_funcional.py --out validacao_local
python executar_testes.py --out resultados_local
```

A execução experimental original ocorreu em Linux, usando conexões TCP locais. Os tempos obtidos em outros ambientes podem variar.

## Revisão do teste funcional 1 (a validar)

Na branch `revisao-teste-malha-completa`, o primeiro teste funcional foi alterado para quatro peers em **malha completa**, em substituição à cadeia A–B–C–D. Cada peer conhece os outros três; A inicia com o arquivo completo e B, C e D podem baixar e redistribuir blocos. O teste verifica a integridade das três cópias, a configuração de vizinhos e seis transferências TCP GET/BLOCK, uma por par A-B, A-C, A-D, B-C, B-D e C-D, cada uma verificada por SHA-256, além de retransmissões durante o download.

**Importante:** a malha é validada em duas etapas distintas: (1) download simultâneo de B, C e D com evidência de colaboração entre receptores; (2) sondas TCP GET/BLOCK após a conclusão, garantindo uma transferência real de bloco em cada um dos seis pares. As sondas NÃO são contabilizadas como blocos úteis do download e não demonstram que os seis pares foram usados espontaneamente durante a distribuição. A execução nova deve ser validada no GitHub Actions.

Execute em um diretório novo:

```bash
python -m unittest discover -v
python validar_funcional.py --out validacao_malha_nova
python executar_testes.py --out resultados_malha_novos
```

## Experimentos e resultados originais

A matriz experimental contém **24 cenários**, combinando seis tamanhos de arquivo, dois tamanhos de bloco (1024 e 4096 bytes) e dois totais de peers (2 e 4). As cópias foram verificadas por tamanho e SHA-256. Foram realizados ainda testes funcionais de encaminhamento entre peers, transferência bidirecional e retomada após interrupção.

Para arquivos maiores, a configuração de 4096 bytes apresentou tempos menores nas medições originais. Como os testes ocorreram em um único host e com uma execução por combinação, os resultados não comprovam desempenho em redes reais.

## GitHub Actions

O workflow em `.github/workflows/testes-p2p.yml` foi configurado para executar os testes e guardar evidências em uma máquina Linux. O código está publicado na raiz. Consulte a aba *Actions* para ver a situação real das execuções e baixar os artefatos de evidência.

