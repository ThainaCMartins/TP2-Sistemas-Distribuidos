# Roteiro de demonstração — versão validada

1. **Arquitetura:** cada peer é servidor TCP e cliente dos vizinhos. Mostrar `p2p/peer.py`, `p2p/protocol.py` e `p2p/storage.py`.
2. **Malha completa:** quatro peers A/B/C/D, cada um com três vizinhos. B/C/D baixam e retransmitem blocos. Seis sondas adicionais GET/BLOCK verificam cada par com SHA-256; não são contadas como downloads úteis.
3. **Troca bidirecional:** A e B começam com metades complementares e completam o arquivo.
4. **Retomada:** reinício após interrupção, validação dos blocos preservados e nova obtenção de bloco corrompido.
5. **Matriz:** 24 cenários = 6 tamanhos × 2 blocos × 2 contagens de peers. Mostrar `RELATORIO_FINAL.md` e os artefatos da [execução aprovada](https://github.com/ThainaCMartins/TP2-Sistemas-Distribuidos/actions/runs/41076176482).
6. **Resultados:** arquivos grandes com blocos de 4096 bytes tiveram tempos substancialmente menores nesta medição; quatro peers não garantiram melhor tempo em loopback.
7. **Limitações:** uma repetição por cenário, loopback no mesmo computador, sem estimativa de rede física; SHA-256 verifica integridade, mas não autentica o emissor.
