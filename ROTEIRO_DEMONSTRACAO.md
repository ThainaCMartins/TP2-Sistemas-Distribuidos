# Roteiro para demonstrar o trabalho

## Explicar o objetivo

“O sistema transfere um arquivo por blocos entre peers. Cada processo tem um servidor e tarefas de cliente. O nó que começa com o original é o seeder; os demais baixam e já podem compartilhar cada bloco que recebem e verificam.”

## Mostrar a organização

Abra `p2p/peer.py` e identifique `run`, `handle_client` e `download_neighbor`. Explique que todas as conexões usam o mesmo armazenamento. Em `p2p/storage.py`, mostre o `have`, a validação em `accept` e a publicação em `finalize`.

## Mostrar a transferência

Siga as seções 5 e 6 de `LEIA_PRIMEIRO.md`. Mostre A como seeder, B como leecher, `COMPLETE`, o arquivo recebido e `python3 -m p2p verify`. Depois apresente `validar_funcional.py` e os eventos de B/C com `while_incomplete: true`.

## Mostrar os estudos de caso

Abra `evidencias/matriz/resultados.csv` ou os seus próprios resultados. Foram cruzados seis tamanhos, dois blocos e duas quantidades de peers: 24 cenários. Em cada um, o controlador inicia processos reais, aguarda a conclusão, compara tamanho/hash e registra de quem vieram os blocos. São 48 cópias verificadas por repetição da matriz.

## Explicar o protocolo

“O TCP entrega um fluxo de bytes, então o protocolo precisa informar onde cada mensagem termina. Primeiro envio quatro bytes com o tamanho do JSON, depois o JSON e depois os bytes do bloco. O JSON informa o tamanho desses bytes. `readexactly` garante que o receptor leia a quantidade declarada, mesmo se o TCP repartir o envio.”

## Perguntas que podem aparecer

**Por que isso é P2P se existe um seeder inicial?** Todos executam o mesmo código e podem enviar e receber. O seeder só começa com todos os blocos. A cadeia mostra leechers distribuindo blocos e o teste bidirecional começa sem nenhum nó completo.

**Por que não usou tracker?** O enunciado torna o tracker opcional e permite vizinhos estáticos. O JSON de configuração já contém os endereços necessários.

**Como um peer sabe o que outro possui?** Solicita `HAVE`, recebe `BITFIELD` e escolhe índices ausentes localmente que o vizinho tem.

**Como evita baixar o mesmo bloco de dois vizinhos ao mesmo tempo?** O conjunto `inflight` reserva o índice durante a solicitação. A presença também é verificada antes de pedir e ao aceitar.

**Como sabe que o arquivo está correto?** Confere tamanho e SHA-256 de cada bloco, depois tamanho e SHA-256 do arquivo completo. O controlador dos experimentos faz uma comparação externa adicional.

**Como monta os blocos fora de ordem?** Escreve cada bloco no deslocamento correspondente ao índice. O último usa apenas os bytes restantes. O nome final só é publicado após conferir o arquivo inteiro.

**O que acontece se o peer cair?** Os vizinhos podem tentar outras fontes conhecidas e reconectar. Ao reiniciar o destino, o programa revalida os blocos do arquivo parcial e baixa somente os que faltam ou estão corrompidos. Se nenhum vizinho acessível tiver um bloco necessário, não há como completá-lo; o prazo de download termina com erro.

**Mais peers sempre deixam o download mais rápido?** Não. Há concorrência por CPU, disco e conexões. Os testes são em loopback, com uma observação por combinação. Eles comprovam funcionamento e mostram tempos daquele ambiente, sem estimar o desempenho de uma rede real.

**Por que blocos maiores podem reduzir o tempo?** São menos pedidos, mensagens, operações de hash e registros de log para a mesma quantidade de bytes. O efeito depende da rede e do ambiente.

**O arquivo parcial já tem o tamanho completo. Isso significa que terminou?** Não. O tamanho é reservado para permitir escrita fora de ordem. Somente o bitmap de blocos verificados e o hash final determinam a conclusão.

**O hash torna a transmissão segura?** Ele detecta alterações em relação ao metadado esperado. Não autentica os peers nem cifra o tráfego. O metadado precisa ser confiável.

**O código foi testado onde?** A evidência incluída registra Linux x86_64, Python 3.12.14 e TCP IPv4 em loopback, em 27 de outubro de 2026. Caso você rode em outro ambiente, use os dados efetivamente obtidos na sua execução.

