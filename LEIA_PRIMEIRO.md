# Guia de execução — TP2 P2P

**Versão de referência:** execução aprovada [GitHub Actions nº 27](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482). Consulte `README.md` e `RELATORIO_FINAL.md` para o estado atual.

Requer Python 3.12. O programa usa somente a biblioteca padrão.

```bash
python -m unittest discover -v
python validar_funcional.py --out validacao_local
python executar_testes.py --out resultados_local
```

Os scripts criam processos TCP independentes e geram `validacao.json`, logs JSONL por peer, `resultados.csv`, `resultados.json` e auditorias. Não reutilize diretórios de saída já preenchidos. Para conferir a versão validada, consulte o artefato [evidencias-execucao-p2p](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482/artifacts/12988391409).

**Teste funcional 1:** malha completa de quatro peers, com download colaborativo e seis sondas GET/BLOCK posteriores, cada uma validada por SHA-256. **Teste 2:** troca bidirecional de metades complementares. **Teste 3:** retomada após interrupção e corrupção de um bloco.

**Matriz:** 24 cenários = seis tamanhos de arquivo × dois tamanhos de bloco × dois números de peers. A execução aprovada concluiu todos. Os arquivos antigos de evidências e gráficos foram retirados da árvore principal porque não representam esta implementação.

O relatório final deve ter no máximo cinco páginas, conforme o enunciado analisado, e incluir a URL do repositório.
