# Protocolo e decisões de implementação

## Arquitetura

Um processo Python corresponde a um peer. `asyncio.start_server` aceita conexões TCP de entrada; uma tarefa `download_neighbor` por vizinho usa `asyncio.open_connection` para os downloads. As tarefas compartilham o mesmo `BlockStore`. A simetria está no mesmo executável: o argumento `--seed-file` apenas determina que o nó começa com todos os blocos.

Os vizinhos são definidos em JSON antes da inicialização. Não existe tracker. Um leecher tenta conectar a todos os vizinhos e reconecta após falha. O arquivo de metadados é previamente distribuído por fora do protocolo; a rede P2P transporta disponibilidade e blocos. Cada execução de peer gerencia um arquivo.

## Configuração

```json
{
  "id": "B",
  "host": "127.0.0.1",
  "port": 9002,
  "neighbors": [
    {"host": "127.0.0.1", "port": 9001},
    {"host": "127.0.0.1", "port": 9003}
  ]
}
```

O projeto aceita endereços IPv4 literais. Cada peer na mesma máquina precisa de porta diferente. Cada nó precisa ter caminho de destino e log próprios. A conectividade estática precisa permitir alcançar algum nó que possua cada bloco solicitado.

## Metadados

O comando `python3 -m p2p meta arquivo.bin --block-size 1024 --out metadata.json` lê o arquivo em blocos fixos. O último bloco pode ser menor. O JSON contém:

| Campo | Tipo e significado |
| --- | --- |
| `version` | Inteiro 1 |
| `file_name` | Nome simples de saída, sem diretórios |
| `file_size` | Quantidade exata de bytes do original |
| `block_size` | Tamanho nominal de cada bloco em bytes |
| `block_hashes` | Lista de SHA-256 hexadecimais por índice, começando em zero |
| `sha256` | SHA-256 do arquivo completo |
| `file_id` | SHA-256 dos demais campos em JSON canônico |

O JSON canônico usa chaves ordenadas, separadores `,` e `:`, `ensure_ascii=True` e codificação UTF-8, sem o campo `file_id`. Assim, tamanho de bloco ou lista de hashes diferentes produzem identificadores diferentes. O identificador detecta inconsistência entre os metadados; não autentica quem os criou. Os peers devem receber o metadado correto por um meio confiável.

## Enquadramento TCP

Cada mensagem tem, nesta ordem:

1. Quatro bytes: comprimento do cabeçalho JSON como inteiro sem sinal em ordem de rede, `struct.pack("!I", tamanho)`.
2. Cabeçalho JSON UTF-8 com `type`, `version: 1`, `payload_len` e campos específicos.
3. Exatamente `payload_len` bytes de conteúdo binário, que podem ser zero.

O cabeçalho é limitado a 64 KiB; o conteúdo binário, a 4 MiB. `readexactly` lê os comprimentos declarados mesmo se o TCP dividir ou agrupar envios. Um envio TCP não equivale necessariamente a uma mensagem inteira. `drain` aplica o controle de fluxo do stream. O protocolo não usa pickle nem Base64 para blocos.

| Pedido | Resposta | Campos específicos e dados |
| --- | --- | --- |
| `HELLO` | `HELLO_ACK` | Ambos incluem `file_id` e `peer_id`; nenhum conteúdo binário |
| `HAVE` | `BITFIELD` | Resposta inclui `count` e bitmap binário dos blocos locais verificados |
| `GET` | `BLOCK` | Pedido e resposta incluem `index`; a resposta transporta o bloco binário |
| `GET` indisponível/inválido | `ERROR` | Inclui `index` e `reason`, sem conteúdo binário |

O primeiro quadro de cada conexão é `HELLO`. Um `file_id` incompatível encerra a conexão. A conexão TCP é persistente: os pedidos seguintes reutilizam o mesmo stream. Mensagens com tamanho, versão ou tipo inválidos também encerram a conexão e são registradas.

No bitmap, o bloco `i` ocupa o bit `i % 8` do byte `i // 8`, começando pelo bit menos significativo. São necessários tantos bytes quanto a quantidade de blocos dividida por oito, arredondada para cima. Os bits que sobram no último byte não representam blocos.

## Seleção e concorrência

Cada tarefa consulta o bitmap do vizinho, filtra os blocos locais ausentes e embaralha candidatos. Um conjunto global `inflight` impede pedidos simultâneos do mesmo índice a fontes diferentes. Após até 64 blocos aceitos, a tarefa atualiza a disponibilidade. Se o vizinho não oferece trabalho útil, aguarda 50 ms e consulta novamente. Uma falha de conexão/protocolo provoca espera de 150 ms e nova tentativa. Conexão inicial tem prazo de 3 segundos; quadros e envios usam 10 segundos; o servidor aguarda até 60 segundos por novo pedido.

Não se usa seleção por raridade. O embaralhamento procura distribuir as solicitações e reduzir a repetição de escolhas entre peers, sem garantir divisão igual de carga. A lista de fontes efetivamente usadas fica em `completion.json` e nos eventos `BLOCK_RECEIVED`.

## Validação e armazenamento

Um `bytearray` registra a presença local de cada bloco, e um contador permite detectar a conclusão. O arquivo parcial tem o tamanho final reservado, mas sua mera existência não significa que os dados são válidos. Blocos são escritos no deslocamento correspondente ao índice, permitindo receber fora de ordem.

Antes de aceitar um bloco, o peer confere índice, tamanho esperado e SHA-256. O último bloco usa somente os bytes restantes. Após a gravação completa, o índice é marcado como disponível. Como não há `await` entre a escrita e a marcação, outra tarefa de rede não observa um bloco parcialmente gravado. O servidor pode atendê-lo na consulta seguinte, mesmo sem o arquivo completo.

Na conclusão, o peer sincroniza a gravação, confere o tamanho e o SHA-256 global e renomeia o parcial para o nome final. A remontagem é feita por posicionamento no arquivo, seguida de publicação; não exige carregar o arquivo inteiro na memória. O peer continua servidor por padrão.

No reinício, os blocos do parcial são lidos e revalidados. Os íntegros são aproveitados; os corrompidos permanecem ausentes e voltam a ser pedidos. O arquivo parcial e o metadado precisam permanecer no mesmo destino. Um arquivo final existente com conteúdo diferente não é substituído. Em falhas abruptas de energia, não há garantia de persistência de cada bloco individual; a revalidação evita anunciar como válido um bloco danificado.

## Escopo

Sockets de rede são não bloqueantes e as conexões são concorrentes. As pequenas operações locais de arquivo e hash são síncronas dentro do event loop, o que simplifica o controle do estado, mas pode limitar desempenho em disco lento ou arquivos muito maiores. Há timeout global de download, com padrão de 120 segundos, configurável por `--timeout`.

Não há autenticação, TLS, descoberta de peers, NAT traversal, anúncio a um tracker ou protocolo de obtenção dos metadados. Os testes foram locais, com processos independentes e vizinhança estática. Esses limites devem ser mantidos na apresentação dos resultados.

## Referências de implementação

- Python Software Foundation. Streams: https://docs.python.org/3/library/asyncio-stream.html
- Python Software Foundation. hashlib: https://docs.python.org/3/library/hashlib.html
- Python Software Foundation. struct: https://docs.python.org/3/library/struct.html
- Michelle Hanne. Sistemas Distribuídos, Trabalho Prático 2, CEFET-MG, 2026/2. Enunciado fornecido com a atividade.

