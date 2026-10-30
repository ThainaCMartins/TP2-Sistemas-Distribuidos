# TP2 de Sistemas Distribuídos

Este pacote contém a implementação do sistema de transferência de arquivos P2P, os testes automatizados, as evidências de execução e o relatório editável. Use Python 3.10 ou superior. O programa e os testes usam apenas a biblioteca padrão: não é necessário instalar pacotes com pip, criar ambiente virtual ou usar Docker.

## 1. O que precisa ser entregue

O enunciado pede a implementação testada e um relatório de **no máximo 5 páginas**, contendo as decisões de projeto, a avaliação dos testes e a **URL do código-fonte**. O trabalho pode ser individual ou em dupla. Não há pedido explícito de slides, vídeo ou quantidade mínima de páginas. A forma de submissão e o prazo não aparecem no PDF; siga a orientação da professora no sistema da disciplina.

O relatório está em `relatorio/TP2_Relatorio.docx` e `relatorio/TP2_Relatorio.pdf`. Antes de enviar, confira o nome e substitua `INSIRA_A_URL_DO_REPOSITORIO` pela URL real. O PDF entregue aqui apresenta os resultados da execução que acompanha este pacote. Se substituir pelos resultados da sua máquina, atualize os números e a descrição do ambiente antes de exportar novamente.

## 2. Arquivos do pacote

| Caminho | Função |
| --- | --- |
| `p2p/__main__.py` | Comandos `meta`, `peer` e `verify` |
| `p2p/peer.py` | Servidor, clientes concorrentes e registro de eventos |
| `p2p/protocol.py` | Empacotamento TCP e bitmap de disponibilidade |
| `p2p/storage.py` | Fragmentação, SHA-256, arquivo parcial e remontagem |
| `preparar_demo.py` | Prepara a demonstração manual com 2 ou 4 peers |
| `executar_testes.py` | Executa as 24 combinações da tabela do enunciado |
| `validar_funcional.py` | Verifica repasse parcial, troca bidirecional e retomada |
| `tests/test_core.py` | Testes do protocolo e do armazenamento |
| `experimentos.py` | Inicia e verifica os processos reais dos experimentos |
| `PROTOCOLO.md` | Especificação das mensagens e dos metadados |
| `MAPEAMENTO_REQUISITOS.md` | Correspondência do enunciado com código e evidências |
| `ROTEIRO_DEMONSTRACAO.md` | Explicação curta para demonstrar e defender as escolhas |
| `evidencias/` | Logs e resultados reais da execução incluída |
| `relatorio/` | Relatório em Word e PDF |

## 3. Preparar o computador

### Ubuntu ou WSL

1. Extraia o ZIP. Abra o terminal Ubuntu/WSL.
2. Entre na pasta extraída, que precisa conter a pasta `p2p` e este guia. Por exemplo, se extraiu em Downloads no Windows:

```bash
cd /mnt/c/Users/SEU_USUARIO/Downloads/TP2_P2P
```

Troque `SEU_USUARIO` e o caminho de acordo com a pasta real. Se o caminho tiver espaços, coloque-o entre aspas.

3. Confira o Python:

```bash
python3 --version
```

É necessário Python 3.10 ou superior. Se o comando não existir no Ubuntu:

```bash
sudo apt update
sudo apt install python3 git
```

4. Confira se está na pasta correta:

```bash
ls
python3 -m p2p --help
```

### Windows sem WSL

Instale Python 3.10 ou superior, extraia o ZIP, abra o PowerShell dentro da pasta e confirme `py -3 --version`. Nos comandos Python deste guia, substitua o prefixo `python3` por `py -3`. Os scripts Python funcionam sem comandos Linux. Para ver arquivos, use o Explorador; para interromper um peer, pressione Ctrl+C. O funcionamento foi verificado no Linux; a execução nativa no Windows deve ser conferida na sua máquina.

## 4. Rodar toda a validação

Execute os comandos **um de cada vez**, na pasta do projeto. Não é necessário abrir terminais de peers para esta etapa: os scripts fazem isso automaticamente.

### 4.1 Testes do protocolo e armazenamento

```bash
python3 -m unittest discover -v
```

O resultado esperado é `Ran 13 tests` seguido de `OK`. Os testes incluem mensagens TCP divididas ou agrupadas, timeout, bitmap, recebimento fora de ordem, último bloco menor, hash incorreto, metadados inválidos e retomada.

### 4.2 Testes funcionais com processos separados

```bash
python3 validar_funcional.py --out validacao_local
```

O resultado esperado são três registros com `status: OK` em `validacao_local/validacao.json`:

1. Cadeia A-B-C-D: B e C encaminham blocos enquanto ainda estão incompletos; C recebe de B e D recebe de C.
2. Troca bidirecional: A e B começam com metades complementares e ambos enviam e recebem até concluir, sem seeder completo inicial.
3. Retomada: o script interrompe B, corrompe um bloco local, reinicia B e verifica o aproveitamento dos blocos válidos e a correção do bloco danificado.

Os atrasos artificiais de 1 ou 2 ms por bloco existem apenas nessas demonstrações para tornar observável o compartilhamento antes da conclusão. A matriz de desempenho usa atraso zero.

### 4.3 Todos os estudos de caso do enunciado

```bash
python3 executar_testes.py --out resultados_local --manter-arquivos
```

Espere aparecer `Concluído: 24/24 cenários`. Não feche o terminal enquanto executa. O tempo depende do computador; a execução gera muitos logs e arquivos. Reserve cerca de 1 GB livre para a bateria com uma repetição e os binários preservados.

O cruzamento usado é:

| Variável | Valores |
| --- | --- |
| Peers totais | 2 e 4, incluindo o seeder |
| Bloco | 1024 e 4096 bytes |
| Arquivo | 10 KiB, 20 KiB, 1 MiB, 5 MiB, 10 MiB e 20 MiB |
| Combinações | 2 × 2 × 6 = 24 |

O enunciado exemplifica 1 KB como 1024 bytes. Por isso o projeto adota a base binária e registra os tamanhos exatos. Cada cenário usa um processo por peer. Em 4 peers, A possui o original e B, C e D remontam cópias independentes.

Resultados gerados:

- `resultados_local/resultados.csv`: tabela de resultados, separada por ponto e vírgula; pode abrir no Excel.
- `resultados_local/resultados.json`: resultados e contagem de blocos recebidos de cada fonte.
- `resultados_local/ambiente.json`: versão do Python, sistema e método de medição.
- `resultados_local/<cenario>/A.jsonl`, `B.jsonl`, etc.: conexões, pedidos, blocos enviados/recebidos, progresso e conclusão.
- `resultados_local/<cenario>/<peer>/completion.json`: hash, tamanho, fontes e tempo do peer.
- `resultados_local/<cenario>/<peer>/<arquivo>.bin`: cópia final, quando há `--manter-arquivos`.

Sem `--manter-arquivos`, o script verifica hash e tamanho e depois remove os binários para economizar espaço. Os logs, hashes e resultados permanecem. Foi essa modalidade que gerou a matriz incluída em `evidencias/matriz`.

Para uma conferência rápida de instalação, há `--rapido`, que roda somente as quatro combinações do arquivo de 10 KiB. Essa opção não substitui a bateria completa. Para repetir a matriz três vezes:

```bash
python3 executar_testes.py --out resultados_3_repeticoes --repeticoes 3 --manter-arquivos
```

Use uma pasta de saída nova a cada execução. Os scripts recusam pastas com dados para preservar os resultados anteriores.

## 5. Executar manualmente com dois peers

### 5.1 Preparar o arquivo e os metadados

```bash
python3 preparar_demo.py --dir demo
```

Isso cria um original aleatório de 1 MiB, `demo/metadata.json`, configurações com portas 9001 a 9004 e duas listas estáticas de vizinhos, para 2 e 4 peers. Distribua o mesmo metadado aos peers. O arquivo original fica somente no seeder. Não coloque o original nas pastas dos leechers.

### 5.2 Abrir o peer A

Abra um terminal na pasta do projeto e execute:

```bash
python3 -m p2p peer --config demo/config2/A.json --meta demo/metadata.json --dir demo/saida2/A --seed-file demo/original.bin --log demo/logs2/A.jsonl
```

Espere `READY` e `COMPLETE`. **Deixe esse terminal aberto**: A continua como servidor.

### 5.3 Abrir o peer B

Abra outro terminal na mesma pasta e execute:

```bash
python3 -m p2p peer --config demo/config2/B.json --meta demo/metadata.json --dir demo/saida2/B --log demo/logs2/B.jsonl
```

B imprime o progresso e `COMPLETE` ao terminar. O arquivo baixado fica em `demo/saida2/B/original.bin`. B permanece atendendo outros peers depois da conclusão.

### 5.4 Conferir o resultado

Em um terceiro terminal:

```bash
python3 -m p2p verify demo/saida2/B/original.bin --meta demo/metadata.json
```

O resultado deve conter `status: OK`, tamanho `1048576` e o hash do original. No Ubuntu, uma segunda conferência é:

```bash
sha256sum demo/original.bin demo/saida2/B/original.bin
wc -c demo/original.bin demo/saida2/B/original.bin
```

Os dois hashes e os tamanhos precisam coincidir. Termine A e B com Ctrl+C antes de usar as mesmas portas em outra demonstração.

## 6. Executar manualmente com quatro peers

Use quatro terminais na pasta do projeto. A mesma preparação da etapa anterior já criou as configurações. Confirme que os peers da demonstração de dois nós foram encerrados.

Terminal A:

```bash
python3 -m p2p peer --config demo/config4/A.json --meta demo/metadata.json --dir demo/saida4/A --seed-file demo/original.bin --log demo/logs4/A.jsonl
```

Terminal B:

```bash
python3 -m p2p peer --config demo/config4/B.json --meta demo/metadata.json --dir demo/saida4/B --log demo/logs4/B.jsonl
```

Terminal C:

```bash
python3 -m p2p peer --config demo/config4/C.json --meta demo/metadata.json --dir demo/saida4/C --log demo/logs4/C.jsonl
```

Terminal D:

```bash
python3 -m p2p peer --config demo/config4/D.json --meta demo/metadata.json --dir demo/saida4/D --log demo/logs4/D.jsonl
```

Depois de B, C e D mostrarem `COMPLETE`, verifique cada cópia:

```bash
python3 -m p2p verify demo/saida4/B/original.bin --meta demo/metadata.json
python3 -m p2p verify demo/saida4/C/original.bin --meta demo/metadata.json
python3 -m p2p verify demo/saida4/D/original.bin --meta demo/metadata.json
```

Para observar os repasses antes da conclusão de forma garantida, use `validar_funcional.py`, que monta a topologia em cadeia. Na malha completa, as fontes podem variar conforme a ordem e a velocidade de inicialização.

## 7. Ler os logs

Cada linha `.jsonl` é um objeto JSON independente. Exemplo estrutural:

```json
{"peer":"B","event":"BLOCK_RECEIVED","remote":"A","index":17,"bytes":1024,"have":18,"total":1024}
```

| Evento | Significado |
| --- | --- |
| `READY` | Porta aberta e quantidade de blocos locais revalidados |
| `CONNECTED_OUT` e `CONNECTED_IN` | Conexão de saída ou entrada com outro peer |
| `GET` | Pedido de um bloco recebido pelo servidor |
| `BITFIELD` | Resposta com a disponibilidade local |
| `BLOCK_RECEIVED` | Bloco verificado e gravado; identifica fonte, índice e progresso |
| `BLOCK_SENT` | Bloco servido; `while_incomplete: true` prova compartilhamento parcial |
| `BLOCK_REJECTED` | Tamanho ou hash incorreto; bloco não é marcado como disponível |
| `RETRY` | Falha de conexão/protocolo; nova tentativa é programada |
| `STATUS` | Resumo periódico do progresso |
| `COMPLETE` | Arquivo integral verificado e disponível |
| `FAILED` | Download ultrapassou o prazo configurado |

Para extrair apenas os repasses durante download de uma evidência incluída:

```bash
python3 inspecionar_logs.py evidencias/funcional/cadeia/B.jsonl --evento BLOCK_SENT --parcial --limite 5
```

Para ver a origem dos blocos recebidos por C:

```bash
python3 inspecionar_logs.py evidencias/funcional/cadeia/C.jsonl --evento BLOCK_RECEIVED --limite 5
```

Se forem solicitadas capturas de tela, registre o resultado dos testes, a mensagem de 24/24 cenários, a comparação de hashes e os eventos de repasse parcial. O PDF do enunciado não exige capturas explicitamente; os logs são as evidências primárias.

## 8. Publicar o código e completar o relatório

1. Entre na sua conta do GitHub e crie um repositório vazio, por exemplo `TP2-Sistemas-Distribuidos-P2P`. Para facilitar o acesso da professora, use um repositório público, ou conceda o acesso necessário se escolher privado.
2. No terminal, dentro da pasta do projeto, rode os comandos abaixo. Substitua `SEU_USUARIO` pela sua conta e use a URL exata do repositório criado:

```bash
git init
git add .
git commit -m "Implementa TP2 de transferencia de arquivos P2P"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/TP2-Sistemas-Distribuidos-P2P.git
git push -u origin main
```

O GitHub pode solicitar autenticação. Se o Git pedir identidade no primeiro commit, configure seu nome e email no repositório e repita o commit:

```bash
git config user.name "SEU NOME"
git config user.email "SEU EMAIL"
```

Alternativa sem Git: no repositório do GitHub, use **Add file > Upload files**, arraste as pastas do código e confirme o commit. Inclua os arquivos da raiz, `p2p`, `tests`, os guias e as evidências em texto que desejar preservar. Não é necessário publicar arquivos binários de teste.

3. Abra `relatorio/TP2_Relatorio.docx` no Word ou LibreOffice. Confira `Giovanna Silva`, acrescente a outra pessoa se houver dupla e troque `INSIRA_A_URL_DO_REPOSITORIO` pela URL real.
4. Opcionalmente, preencha nome e link por comando, sem instalar dependências:

```bash
python3 personalizar_relatorio.py --repo https://github.com/SEU_USUARIO/TP2-Sistemas-Distribuidos-P2P --autor "Giovanna Silva"
```

Esse comando cria `relatorio/TP2_Relatorio_Preenchido.docx` e preserva o original. Ele não atualiza o PDF automaticamente.

5. Se usar os resultados locais, substitua as tabelas e o ambiente pelos dados de `resultados_local`. Preserve a distinção entre tempo medido e qualquer estimativa. Se usar as evidências incluídas, mantenha a descrição do ambiente em que foram obtidas.
6. Exporte o DOCX atualizado para PDF no Word/LibreOffice. Confira que o relatório continua com **até 5 páginas**, incluindo identificação e referências.
7. Confira se a URL abre o código na conta que a professora usará. Envie o relatório e o código/link conforme a forma de entrega da disciplina. Se o portal aceitar o código como anexo, anexe também o ZIP do projeto.

## 9. Executar em dois computadores

É opcional para este pacote: os testes incluídos usam processos separados no mesmo computador. Para usar uma rede local:

1. Coloque o código e o mesmo `metadata.json` nas duas máquinas. Somente A precisa do original.
2. Em cada configuração JSON, use o IPv4 da máquina em `host`; coloque o IP e a porta reais da outra máquina em `neighbors`. `127.0.0.1` identifica somente o computador atual, portanto não serve para a outra máquina.
3. Libere apenas as portas escolhidas no firewall da rede local e confirme que as máquinas se alcançam.
4. Rode os mesmos comandos de `peer`, ajustando os caminhos locais e a configuração.
5. Verifique o arquivo recebido com `python3 -m p2p verify ... --meta ...`.

Cada processo transfere um único arquivo identificado pelo metadado. O sistema usa IPv4, vizinhos estáticos e metadados previamente distribuídos. Não implementa tracker, descoberta automática, autenticação ou criptografia de transporte.

## 10. Resolver problemas comuns

| Problema | O que fazer |
| --- | --- |
| `No module named p2p` | Entre na pasta que contém `p2p` antes de executar |
| Porta em uso ou `Address already in use` | Encerre o peer antigo com Ctrl+C ou prepare outra demo com `--base-port 9100` |
| `RETRY` logo no início | Confira se os vizinhos já estão abertos; o programa tenta novamente |
| Prazo excedido | Confira IP, porta, metadado e vizinhos; reinicie na mesma pasta para retomar; aumente `--timeout 300` em rede lenta |
| Metadados incompatíveis | Todos os peers devem usar o mesmo JSON; gerar outro bloco muda o identificador |
| Pasta de saída já contém dados | Escolha novo `--out` ou `--dir`; preserve as evidências anteriores |
| Arquivo final com outro conteúdo | Use outra pasta de destino para não substituir arquivos existentes |
| Peer não fecha depois de concluir | É o comportamento esperado: ele permanece seeder; encerre com Ctrl+C |
| Tamanhos pequenos têm tempos parecidos | Inicialização e controle pesam mais; analise os arquivos maiores e as condições do teste |

