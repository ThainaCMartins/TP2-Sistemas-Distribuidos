# TP2 — Transferência de Arquivos Peer-to-Peer (P2P)

**CEFET-MG — Sistemas Distribuídos (2026/2)**  
**Autoras:** Thainá Martins e Giovana Laura

## Versão validada

Implementação Python 3.12 de transferência TCP P2P, com servidor e cliente em cada peer, metadados compartilhados previamente, blocos verificados por SHA-256, armazenamento parcial, retomada e compartilhamento antes da conclusão. Vizinhos estáticos, sem tracker.

**GitHub Actions: [execução nº 27 — sucesso](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482)**; commit testado `e5c7a906`, branch `revisao-teste-malha-completa`. Foram aprovados **13 testes unitários, 3 testes funcionais e 24 cenários experimentais**. Os artefatos originais estão [disponíveis na execução](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482/artifacts/12988391409). Resultados históricos de versões anteriores foram removidos da árvore atual para evitar confusão; permanecem no histórico Git.

## Estrutura

- `p2p/`: comandos, peer TCP, protocolo de mensagens, armazenamento e SHA-256.
- `tests/test_core.py`: 13 testes unitários.
- `validar_funcional.py`: três testes funcionais.
- `executar_testes.py`: 24 combinações de tamanho, bloco e número de peers.
- `experimentos.py`: inicialização de processos, verificação e auditoria.
- `RELATORIO_FINAL.md`: relatório atualizado, metodologia e resultados verificados.
- `.github/workflows/testes-p2p.yml`: validação automatizada no Ubuntu.

## Executar

Na raiz do repositório, com Python 3.12:

```bash
python -m unittest discover -v
python validar_funcional.py --out validacao_local
python executar_testes.py --out resultados_local
```

Escolha pastas de saída novas para preservar as evidências existentes.

## Testes funcionais

1. **Malha completa:** A, B, C e D conhecem os outros três peers. B/C/D baixam o arquivo e podem redistribuir blocos antes de terminar. Após o download, seis sondas TCP GET/BLOCK, com SHA-256, verificam comunicação efetiva em A–B, A–C, A–D, B–C, B–D e C–D. 
2. **Troca bidirecional:** dois peers iniciam com metades complementares, enviam e recebem até completar.
3. **Interrupção e retomada:** recuperação de blocos válidos e correção de bloco adulterado.

## Experimentos

Seis tamanhos (10 KiB, 20 KiB, 1 MiB, 5 MiB, 10 MiB e 20 MiB), dois tamanhos de bloco (1024 e 4096 bytes) e dois números de peers (2 e 4) totalizam **24 cenários**. Uma repetição por cenário; loopback TCP IPv4, Linux, Python 3.12. Os tempos e a análise estão em `RELATORIO_FINAL.md`. Os dados originais estão no artefato da execução aprovada.

**Observação:** uma execução manual posterior na `main` antiga (nº 28) falhou por usar o código anterior. Ela não substitui a execução aprovada nº 27.
