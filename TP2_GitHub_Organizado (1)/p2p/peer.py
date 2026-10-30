"""Um processo por peer; servidor e clientes TCP executam no mesmo event loop."""

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


class EventLog:
    def __init__(self, peer_id, path):
        self.peer_id = peer_id
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.stream = open(path, "a", encoding="utf-8", buffering=1)

    def emit(self, event, **fields):
        row = dict(time=datetime.now(timezone.utc).isoformat(), peer=self.peer_id, event=event, **fields)
        line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        self.stream.write(line + "\n")
        if event not in {"BLOCK_RECEIVED", "BLOCK_SENT", "BITFIELD", "GET"}:
            print(line, flush=True)

    def checkpoint(self):
        self.stream.flush()
        os.fsync(self.stream.fileno())


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("id"), str) or not config["id"]:
        raise ValueError("Configuração precisa de id textual")
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
    seen = set()
    for neighbor in neighbors:
        endpoint(neighbor)
        addr = (neighbor["host"], neighbor["port"])
        if addr in seen or addr == (config["host"], config["port"]):
            raise ValueError("Vizinho duplicado ou igual ao próprio peer")
        seen.add(addr)
    return config


class Peer:
    def __init__(self, args):
        self.args = args
        self.config = load_config(args.config)
        self.meta = load_metadata(args.meta)
        self.store = BlockStore(self.meta, args.directory, args.seed_file)
        self.log = EventLog(self.config["id"], args.log)
        self.inflight = set()
        self.sources = Counter()
        self.connections = set()
        self.handlers = set()
        self.started = time.monotonic()
        self.completion = Path(args.directory) / "completion.json"
        self.completion.unlink(missing_ok=True)

    def progress(self):
        return dict(have=self.store.complete_count, total=self.store.count)

    async def handle_client(self, reader, writer):
        self.handlers.add(asyncio.current_task())
        self.connections.add(writer)
        remote = "?"
        try:
            hello, payload = await read_message(reader)
            if hello.get("type") != "HELLO" or payload or hello.get("file_id") != self.meta["file_id"]:
                raise ProtocolError("Handshake ou arquivo incompatível")
            remote = hello.get("peer_id")
            if not isinstance(remote, str) or not remote:
                raise ProtocolError("Identificador de peer inválido")
            await send_message(writer, {"type": "HELLO_ACK", "file_id": self.meta["file_id"],
                                        "peer_id": self.config["id"]})
            self.log.emit("CONNECTED_IN", remote=remote)
            while True:
                request, payload = await read_message(reader, timeout=60)
                if payload:
                    raise ProtocolError("Requisição não pode conter dados")
                kind = request["type"]
                if kind == "HAVE":
                    await send_message(writer, {"type": "BITFIELD", "count": self.store.count},
                                       pack_bitmap(self.store.have))
                    self.log.emit("BITFIELD", remote=remote, **self.progress())
                elif kind == "GET":
                    index = request.get("index")
                    self.log.emit("GET", remote=remote, index=index)
                    try:
                        data = self.store.read(index)
                    except ValueError as exc:
                        await send_message(writer, {"type": "ERROR", "reason": str(exc), "index": index})
                        continue
                    if self.args.delay:
                        await asyncio.sleep(self.args.delay)
                    await send_message(writer, {"type": "BLOCK", "index": index}, data)
                    self.log.emit("BLOCK_SENT", remote=remote, index=index, bytes=len(data),
                                  while_incomplete=not self.store.complete, **self.progress())
                else:
                    raise ProtocolError("Mensagem desconhecida")
        except (OSError, ValueError, asyncio.IncompleteReadError, asyncio.TimeoutError) as exc:
            self.log.emit("CONNECTION_CLOSED", remote=remote, reason=str(exc)[:180])
        finally:
            self.handlers.discard(asyncio.current_task())
            self.connections.discard(writer)
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()

    async def download_neighbor(self, endpoint):
        host, port = endpoint["host"], endpoint["port"]
        label = f"{host}:{port}"
        rng = random.Random(self.config["id"] + label)
        while not self.store.complete:
            writer = None
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), 3)
                await send_message(writer, {"type": "HELLO", "file_id": self.meta["file_id"],
                                            "peer_id": self.config["id"]})
                hello, _ = await read_message(reader)
                if (hello["type"] != "HELLO_ACK" or hello.get("file_id") != self.meta["file_id"]
                        or not isinstance(hello.get("peer_id"), str)):
                    raise ProtocolError("Resposta de handshake inválida")
                remote = hello["peer_id"]
                self.log.emit("CONNECTED_OUT", remote=remote, endpoint=label)
                while not self.store.complete:
                    await send_message(writer, {"type": "HAVE"})
                    header, bits = await read_message(reader)
                    if header["type"] != "BITFIELD" or header.get("count") != self.store.count:
                        raise ProtocolError("Resposta de disponibilidade inválida")
                    available = unpack_bitmap(bits, self.store.count)
                    candidates = [i for i, has in enumerate(available) if has and not self.store.have[i]]
                    rng.shuffle(candidates)
                    received = 0
                    for index in candidates:
                        if received >= 64 or self.store.complete:
                            break
                        if self.store.have[index] or index in self.inflight:
                            continue
                        self.inflight.add(index)
                        try:
                            await send_message(writer, {"type": "GET", "index": index})
                            answer, data = await read_message(reader)
                            if answer["type"] == "ERROR":
                                continue
                            if answer["type"] != "BLOCK" or answer.get("index") != index:
                                raise ProtocolError("Resposta de bloco inválida")
                            try:
                                accepted = self.store.accept(index, data)
                            except ValueError as exc:
                                self.log.emit("BLOCK_REJECTED", remote=remote, index=index, reason=str(exc))
                                raise ProtocolError("Bloco corrompido") from exc
                            if accepted:
                                self.sources[remote] += 1
                                received += 1
                                self.log.emit("BLOCK_RECEIVED", remote=remote, endpoint=label,
                                              index=index, bytes=len(data), **self.progress())
                        finally:
                            self.inflight.discard(index)
                    if not received:
                        await asyncio.sleep(0.05)
            except (OSError, ValueError, asyncio.IncompleteReadError, asyncio.TimeoutError) as exc:
                self.log.emit("RETRY", endpoint=label, reason=str(exc)[:180])
                await asyncio.sleep(0.15)
            finally:
                if writer:
                    writer.close()
                    with contextlib.suppress(OSError):
                        await writer.wait_closed()

    async def run(self):
        tasks, server = [], None
        try:
            server = await asyncio.start_server(self.handle_client, self.config["host"], self.config["port"])
            self.started = time.monotonic()
            self.log.emit("READY", host=self.config["host"], port=self.config["port"],
                          file_id=self.meta["file_id"], resumed_blocks=self.store.complete_count,
                          **self.progress())
            tasks = [asyncio.create_task(self.download_neighbor(n)) for n in self.config["neighbors"]]
            next_status = self.started
            while not self.store.complete:
                elapsed = time.monotonic() - self.started
                if elapsed > self.args.timeout:
                    self.log.emit("FAILED", reason="Prazo de download excedido", **self.progress())
                    raise TimeoutError("Download não terminou; verifique os vizinhos e reinicie para retomar")
                for task in tasks:
                    if task.done() and task.exception():
                        raise task.exception()
                if time.monotonic() >= next_status:
                    self.log.emit("STATUS", sources=dict(self.sources), **self.progress())
                    next_status = time.monotonic() + 1
                await asyncio.sleep(0.02)
            output = self.store.finalize()
            result = dict(peer=self.config["id"], file_id=self.meta["file_id"],
                          output=str(output.resolve()), size=output.stat().st_size,
                          sha256=self.meta["sha256"], seconds=round(time.monotonic() - self.started, 6),
                          sources=dict(self.sources), blocks=self.store.count)
            self.log.emit("COMPLETE", **{k: v for k, v in result.items() if k != "peer"})
            self.log.checkpoint()
            temp = self.completion.with_suffix(".tmp")
            temp.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            temp.replace(self.completion)
            # Por padrão permanece seeder. O controlador dos testes encerra os processos.
            if self.args.exit_after is None:
                await asyncio.Event().wait()
            else:
                await asyncio.sleep(self.args.exit_after)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if server:
                server.close()
                await server.wait_closed()
            for writer in list(self.connections):
                writer.close()
            for task in list(self.handlers):
                task.cancel()
            await asyncio.gather(*list(self.handlers), return_exceptions=True)
            self.store.close()
            self.log.emit("STOPPED", **self.progress())
            self.log.checkpoint()
            self.log.stream.close()
