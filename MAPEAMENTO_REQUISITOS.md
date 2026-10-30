# Correspondência com o enunciado

Fonte: `SD_TP2_2_2026.pdf`, páginas 1 e 2, professora Michelle Hanne, CEFET-MG, 2026/2.

| Exigência | Implementação | Verificação incluída |
| --- | --- | --- |
| Peer funciona como cliente e servidor simultaneamente | `Peer.run`, `handle_client` e `download_neighbor` no mesmo processo | `evidencias/funcional/bidirecional`, ambos enviam e recebem incompletos |
| IP e porta próprios e vizinhos predefinidos | JSON validado por `load_config`; um worker por vizinho | Configurações `config_A.json` etc. em cada cenário e eventos de conexão |
| Pelo menos dois peers | Bateria cria processos separados com 2 e 4 peers totais | 24 cenários em `evidencias/matriz/resultados.json` |
| Fragmentação em blocos fixos | `create_metadata`; `BlockStore.expected_size` trata o último bloco | Dois tamanhos de bloco; teste de último bloco menor |
| Leecher conecta a todos os vizinhos | Tarefas criadas para cada entrada de `neighbors` | Eventos `CONNECTED_OUT` e eventuais `RETRY`; não se exige baixar de todos se o arquivo já concluiu |
| Solicitar até receber todos os blocos | Seleção por disponibilidade, `inflight` e tentativas até completar/prazo | `COMPLETE` e verificação externa de hash/tamanho em cada cópia |
| Compartilhar cada bloco válido antes de terminar | Estado comum ao cliente/servidor é atualizado após `accept` | Cadeia A-B-C-D, eventos `BLOCK_SENT` com `while_incomplete: true` em B e C |
| Biblioteca socket, concorrência e não bloqueio | Streams TCP do `asyncio`, implementados sobre sockets não bloqueantes | Mensagens e transferências de vários processos; teste bidirecional |
| Formato de metadados | JSON com nome, tamanho, blocos, hashes e identificador | `metadata.json` por cenário; testes de metadados adulterados |
| Protocolo para empacotar e desempacotar blocos | Prefixo uint32, cabeçalho JSON e dados binários | Testes de quadros fragmentados, agrupados, inválidos, truncados e timeout |
| Registro local de blocos disponíveis | `BlockStore.have` e `complete_count` | Bitmap de disponibilidade e progresso `have/total` em logs |
| Remontar, verificar e salvar arquivo | Escrita por deslocamento, hash global e publicação por renomeação | 48 cópias conferidas na matriz incluída |
| Conteúdo aleatório/único | Arquivos gerados por `os.urandom` | Tamanhos, hashes e metadados registrados por cenário |
| Arquivos de 10/20 KB, 1/5 MB e 10/20 MB | `SIZES` em `executar_testes.py`, base de 1024 explicitada | As seis dimensões cruzadas com 2/4 peers e 1024/4096 bytes |
| Mensagens e progresso registrados | Logs JSONL por peer, incluindo pedidos, dados e conclusão | `A.jsonl`, `B.jsonl`, `C.jsonl`, `D.jsonl` de cada cenário |
| Integridade, tamanho e fontes esperadas | `Lab.verify`, `summarize_lab` e validação em cadeia | SHA-256, tamanho exato, `source_counts` e origens nos logs |
| Relatório com até cinco páginas e URL do código | `relatorio/TP2_Relatorio.docx` e PDF com 5 páginas | Nome preenchido; URL real deve ser inserida antes da entrega |

O tracker é opcional e foi dispensado. A obtenção do metadado não foi atribuída a um tracker: o JSON é compartilhado previamente com os peers. Não existe exigência explícita de slides, vídeo ou testes em máquinas físicas diferentes no PDF fornecido.

