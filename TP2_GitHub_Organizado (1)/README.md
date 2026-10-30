# Transferência de arquivos P2P

Trabalho Prático 2 de Sistemas Distribuídos, CEFET-MG, 2026/2, professora Michelle Hanne.

O projeto implementa peers simétricos com TCP e asyncio. Cada peer recebe e serve blocos, verifica SHA-256, remonta o arquivo e pode retomar uma transferência interrompida. Usa Python 3.10 ou superior, sem dependências externas.

**Comece pelo [guia de execução](LEIA_PRIMEIRO.md).** Ele apresenta os comandos de instalação, testes, execução em 2/4 terminais e conclusão do relatório.

```bash
python3 -m unittest discover -v
python3 validar_funcional.py --out validacao_local
python3 executar_testes.py --out resultados_local --manter-arquivos
```

As evidências incluídas abrangem 24 cenários, 48 cópias verificadas e três experimentos funcionais. Os testes usam processos independentes em loopback. A auditoria dos logs confere fontes, índices, tamanhos e correspondência entre envios e recebimentos.

Veja também a [especificação do protocolo](PROTOCOLO.md), o [mapeamento dos requisitos](MAPEAMENTO_REQUISITOS.md) e o [roteiro de demonstração](ROTEIRO_DEMONSTRACAO.md). O relatório está em `relatorio`, em Word e PDF. Antes da entrega, confira a autoria e preencha a URL real do repositório.
