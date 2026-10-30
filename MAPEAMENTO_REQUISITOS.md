# Requisitos e evidências — versão validada

| Requisito | Implementação | Evidência |
|---|---|---|
| Cliente e servidor em cada peer | `Peer.run`, `Peer.serve`, `Peer.download_from` | Testes funcionais |
| TCP e concorrência | `asyncio.start_server`, `asyncio.open_connection` | Logs por peer |
| Vizinhos estáticos | `load_config` e JSON por peer | Malha completa A/B/C/D |
| Blocos 1024/4096 bytes | `create_metadata`, `BlockStore` | Matriz de 24 cenários |
| SHA-256 por bloco e arquivo | `BlockStore.accept/finalize`, `Lab.verify` | Testes e auditoria |
| Compartilhamento antes de completar | `Peer.serve` usa `BlockStore` compartilhado | Eventos `BLOCK_SENT` e contagem de repasses |
| Retomada | Verificação de blocos parciais no `BlockStore` | Teste funcional de retomada |
| Troca bidirecional | Dois peers com blocos complementares | Teste funcional 2 |
| Malha de quatro peers | Cada peer tem três vizinhos | Teste funcional 1 |
| Seis pares com transferência real | Sondas GET/BLOCK com SHA-256 após o download | `verified_tcp_transfers`; não equivalem ao download espontâneo |
| Seis tamanhos de arquivo | `executar_testes.py` | 24/24 OK |
| Relatório com URL do código | `RELATORIO_FINAL.md` e PDF de entrega | Execução aprovada nº 27 |

Evidências: https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482
