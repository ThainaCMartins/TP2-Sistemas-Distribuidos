# Protocolo TCP — versão validada

Cada peer executa `Peer.serve` (servidor) e `Peer.download_from` (cliente), com `asyncio`. Configuração JSON define `id`, `host`, `port` e `neighbors`. Metadados JSON são distribuídos previamente, sem tracker.

## Mensagens

`HELLO` inclui `peer` e `file_id`; `HELLO_ACK` responde com `peer` e `file_id`. `BITFIELD` solicita e retorna bitmap binário de blocos disponíveis. `GET` inclui `index`; `BLOCK` retorna `index` e bytes do bloco; `ERROR` indica pedido inválido ou indisponível.

O enquadramento TCP usa quatro bytes de comprimento do cabeçalho, cabeçalho JSON UTF-8 e payload binário com tamanho declarado; ver `p2p/protocol.py`. TCP é fluxo de bytes, não preserva limites de mensagens. `readexactly` recompõe quadros.

## Armazenamento

`BlockStore` escreve blocos por índice, verifica tamanho e SHA-256 de cada bloco e só publica o arquivo final após verificar o hash global. Na retomada, revalida blocos existentes. `inflight` evita pedidos simultâneos do mesmo índice.

## Seleção e métricas

Cada tarefa consulta o bitmap de um vizinho, escolhe um bloco disponível ainda ausente e registra `BLOCK_RECEIVED`. O servidor registra `BLOCK_SENT`, inclusive se o remetente ainda está incompleto. A escolha é oportunista e não garante uso uniforme das conexões. O teste de malha completa complementa o download com sondas TCP verificadas nos seis pares.

Não há criptografia, autenticação de peers nem descoberta automática de vizinhos. O SHA-256 protege contra conteúdo divergente do metadado confiável, não contra um metadado malicioso.
