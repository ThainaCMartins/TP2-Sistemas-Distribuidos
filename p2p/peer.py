# VISÃO GERAL: cada peer é um processo independente que oferece um servidor TCP
# e, simultaneamente, estabelece conexões de cliente com os vizinhos.
# asyncio coordena essas atividades no mesmo loop de eventos.
"""Um processo por peer; servidor e clientes TCP executam no mesmo event loop."""

# asyncio: tarefas concorrentes, conexões TCP e pausas não bloqueantes.
# contextlib: ajuda a ignorar erros esperados ao encerrar conexões.
# json/os: serialização de logs e persistência no disco.
# random: embaralhamento dos blocos candidatos.
# socket: validação de endereços IPv4.
# time: medição de duração sem depender do relógio do sistema.
# Counter: contagem dos blocos obtidos de cada vizinho.
# datetime: horários UTC nos logs. Path: caminhos de arquivos.
import asyncio
import contextlib
import json
import os
import random
import socket
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .protocol import ProtocolError, pack_bitmap, read_message, send_message, unpack_bitmap
from .storage import BlockStore, load_metadata


# 1) LOGS: cada peer registra os eventos em seu próprio arquivo JSONL.
# JSONL = um objeto JSON por linha, ideal para auditoria cronológica.
class EventLog:
    # Prepara o identificador do peer e abre o arquivo de logs em modo append.
    def __init__(self, peer_id, path):
        self.peer_id = peer_id
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.stream = open(path, "a", encoding="utf-8", buffering=1)

    # Cria um evento com horário UTC, peer e campos adicionais.
    # Registra TODOS os eventos no arquivo; só alguns aparecem no terminal,
    # evitando milhares de mensagens de bloco na saída padrão.
    def emit(self, event, **fields):
        row = dict(time=datetime.now(timezone.utc).isoformat(), peer=self.peer_id, event=event, **fields)
        line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        self.stream.write(line + "\n")
        if event not in {"BLOCK_RECEIVED", "BLOCK_SENT", "BITFIELD", "GET"}:
            print(line, flush=True)

    # Garante que os registros pendentes sejam gravados em disco.
    def checkpoint(self):
        self.stream.flush()
        os.fsync(self.stream.fileno())


# 2) CONFIGURAÇÃO: lê o JSON do peer e valida sua identidade,
# seu endereço TCP e a lista estática de vizinhos.
def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("id"), str) or not config["id"]:
        raise ValueError("Configuração precisa de id textual")
    # Valida um endereço IPv4 e uma porta TCP entre 1 e 65535.
    def endpoint(item):
        if not isinstance(item, dict) or not isinstance(item.get("host"), str):
            raise ValueError("Endereço de peer inválido")
        socket.inet_pton(socket.AF_INET, item["host"])
        if type(item.get("port")) is not int or not 1 <= item["port"] <= 65535:
            raise ValueError("Porta inválida")
    endpoint(config)
    neighbors = config.get("neighbors")
    if not isinstance(neighbors, list):
        raise ValueError("neighbors deve ser uma lista estática")
    # Impede vizinhos repetidos e impede que o peer aponte para si mesmo.
    seen = set()
    for neighbor in neighbors:
        endpoint(neighbor)
        addr = (neighbor["host"], neighbor["port"])
        if addr in seen or addr == (config["host"], config["port"]):
            raise ValueError("Vizinho duplicado ou igual ao próprio peer")
        seen.add(addr)
    return config


# 3) NÚCLEO P2P: um mesmo objeto oferece blocos (servidor)
# e solicita blocos de outros participantes (cliente).
class Peer:
    # Carrega configuração/metadados e cria armazenamento e log.
    # inflight evita solicitar o mesmo bloco simultaneamente a dois vizinhos.
    # sources contabiliza de quem vieram os blocos; connections/handlers
    # permitem encerrar conexões e tarefas corretamente.
    def __init__(self, args):
        self.args = args
        self.config = load_config(args.config)
        self.meta = load_metadata(args.meta)
        self.store = BlockStore(self.meta, args.directory, args.seed_file)
        self.log = EventLog(self.config["id"], args.log)
        self.inflight = set()
        self.sources = Counter()
