"""Peer TCP assíncrono: cada processo serve e baixa blocos verificados."""
import asyncio
import contextlib
import json
import os
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .protocol import read_message, send_message, pack_bitmap, unpack_bitmap
from .storage import BlockStore, load_metadata

class EventLog:
    def __init__(self, peer_id, path):
        self.peer_id = peer_id
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.stream = open(path, "a", encoding="utf-8", buffering=1)

    def emit(self, event, **fields):
        row = dict(time=datetime.now(timezone.utc).isoformat(), peer=self.peer_id,
                   event=event, **fields)
        self.stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        if event not in {"BLOCK_SENT", "BLOCK_RECEIVED", "GET", "BITFIELD"}:
            print(json.dumps(row, ensure_ascii=False), flush=True)

    def close(self):
        self.stream.close()

def load_config(path):
    import socket
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config.get("id"), str) or not config["id"]:
        raise ValueError("id de peer inválido")
    endpoints = [(config["host"], config["port"])]
    for item in [config] + config.get("neighbors", []):
        socket.inet_pton(socket.AF_INET, item["host"])
        if type(item["port"]) is not int or not 1 <= item["port"] <= 65535:
            raise ValueError("porta inválida")
    neighbors = [(n["host"], n["port"]) for n in config.get("neighbors", [])]
    if len(neighbors) != len(set(neighbors)) or endpoints[0] in neighbors:
        raise ValueError("vizinhos duplicados ou próprio peer")
    return config

class Peer:
    def __init__(self, args):
        self.args = args
        self.config = load_config(args.config)
        self.meta = load_metadata(args.meta)
        self.store = BlockStore(self.meta, args.directory, args.seed_file)
        self.log = EventLog(self.config["id"], args.log)
        self.sources = Counter()
        self.inflight = set()
        self.started = time.monotonic()
        self.ready = None
        self.finished = False
        self.server = None
        self.tasks = []

    async def serve(self, reader, writer):
        remote = None
        try:
            hello, _ = await read_message(reader)
            if hello.get("type") != "HELLO" or hello.get("file_id") != self.meta["file_id"]:
                await send_message(writer, {"type": "ERROR", "reason": "arquivo incompatível"})
                return
            remote = hello.get("peer", "?")
            await send_message(writer, {"type": "HELLO_ACK", "peer": self.config["id"],
                                        "file_id": self.meta["file_id"]})
            while True:
                request, _ = await read_message(reader, timeout=20)
                kind = request.get("type")
                if kind == "BITFIELD":
                    await send_message(writer, {"type": "BITFIELD"}, pack_bitmap(self.store.have))
                elif kind == "GET":
                    index = request.get("index")
                    if type(index) is not int or not 0 <= index < self.store.count or not self.store.have[index]:
                        await send_message(writer, {"type": "ERROR", "index": index, "reason": "indisponível"})
                        continue
                    data = self.store.read(index)
                    if self.args.delay:
                        await asyncio.sleep(self.args.delay)
                    await send_message(writer, {"type": "BLOCK", "index": index}, data)
                    self.log.emit("BLOCK_SENT", remote=remote, index=index, bytes=len(data),
                                  while_incomplete=not self.store.complete)
                else:
                    await send_message(writer, {"type": "ERROR", "reason": "comando desconhecido"})
        except (asyncio.IncompleteReadError, ConnectionError, OSError, TimeoutError, ValueError):
            pass
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def download_from(self, neighbor, order):
        host, port = neighbor["host"], neighbor["port"]
        endpoint = f"{host}:{port}"
        while not self.store.complete:
            writer = None
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 2)
                await send_message(writer, {"type": "HELLO", "peer": self.config["id"],
                                            "file_id": self.meta["file_id"]})
                hello, _ = await read_message(reader)
                if hello.get("type") != "HELLO_ACK":
                    raise ValueError("handshake inválido")
                remote = hello["peer"]
                while not self.store.complete:
                    await send_message(writer, {"type": "BITFIELD"})
                    response, payload = await read_message(reader)
                    if response.get("type") != "BITFIELD":
                        raise ValueError("BITFIELD inválido")
                    available = unpack_bitmap(payload, self.store.count)
                    candidates = [i for i, have in enumerate(available)
                                  if have and not self.store.have[i] and i not in self.inflight]
                    if not candidates:
                        await asyncio.sleep(0.012)
                        continue
                    # Distribui os pedidos por diferentes fontes quando possível.
                    index = candidates[(order + random.randrange(len(candidates))) % len(candidates)]
                    self.inflight.add(index)
                    try:
                        await send_message(writer, {"type": "GET", "index": index})
                        block, data = await read_message(reader)
                        if block.get("type") != "BLOCK" or block.get("index") != index:
                            continue
                        if self.store.accept(index, data):
                            self.sources[remote] += 1
                            self.log.emit("BLOCK_RECEIVED", remote=remote, endpoint=endpoint,
                                          index=index, bytes=len(data))
                    finally:
                        self.inflight.discard(index)
            except (asyncio.IncompleteReadError, ConnectionError, OSError, TimeoutError, ValueError) as exc:
                self.log.emit("RECONNECT", endpoint=endpoint, reason=str(exc))
                await asyncio.sleep(0.08)
            finally:
                if writer:
                    writer.close()
                    with contextlib.suppress(Exception):
                        await writer.wait_closed()

    async def run(self):
        try:
            self.server = await asyncio.start_server(
                self.serve, self.config["host"], self.config["port"])
            resumed = self.store.complete_count
            self.ready = time.monotonic()
            self.log.emit("READY", resumed_blocks=resumed, blocks=self.store.count)
            if self.store.complete:
                self.publish()
            else:
                self.tasks = [asyncio.create_task(self.download_from(n, i))
                              for i, n in enumerate(self.config["neighbors"])]
                while not self.store.complete:
                    if time.monotonic() - self.ready > self.args.timeout:
                        raise TimeoutError("download excedeu timeout")
                    await asyncio.sleep(0.01)
                self.publish()
            if self.args.exit_after is not None:
                await asyncio.sleep(self.args.exit_after)
            else:
                # Mantém o seeder e receptores completos disponíveis para outros peers.
                while True:
                    await asyncio.sleep(1)
        finally:
            for task in self.tasks:
                task.cancel()
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            self.store.close()
            self.log.close()

    def publish(self):
        if self.finished:
            return
        path = self.store.finalize()
        seconds = time.monotonic() - self.ready
        info = dict(status="OK", peer=self.config["id"], seconds=round(seconds, 6),
                    sources=dict(self.sources), sha256=self.meta["sha256"],
                    file=str(path))
        target = Path(self.args.directory) / "completion.json"
        target.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        self.log.emit("COMPLETE", seconds=info["seconds"], sha256=info["sha256"])
        self.finished = True
