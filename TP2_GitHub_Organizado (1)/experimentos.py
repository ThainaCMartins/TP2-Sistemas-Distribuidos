"""Utilitários da bateria: peers são processos Python independentes e reais."""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from p2p.storage import create_metadata, sha256_file

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def random_file(path, size):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        remaining = size
        while remaining:
            amount = min(1024 * 1024, remaining)
            stream.write(os.urandom(amount))
            remaining -= amount
    return path


def free_ports(count):
    # Reserva todas juntas para evitar números repetidos nesta configuração.
    sockets = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def events(path):
    rows = []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # Última linha pode estar em gravação durante monitoramento.
    return rows


def audit_case(directory, peer_ids, meta):
    """Confere índices, fontes estáticas e correspondência envio/recebimento."""
    directory = Path(directory)
    all_events = {p: events(directory / f"{p}.jsonl") for p in peer_ids}
    configs = {p: json.loads((directory / f"config_{p}.json").read_text(encoding="utf-8"))
               for p in peer_ids}
    addresses = {f"{c['host']}:{c['port']}": p for p, c in configs.items()}
    sent = {(p, row['remote'], row['index'], row['bytes'])
            for p, rows in all_events.items() for row in rows if row['event'] == 'BLOCK_SENT'}
    checked = 0
    count = len(meta['block_hashes'])
    for peer_id in peer_ids[1:]:
        received = [row for row in all_events[peer_id] if row['event'] == 'BLOCK_RECEIVED']
        if len(received) != count or {row['index'] for row in received} != set(range(count)):
            raise AssertionError(f"Log de {peer_id} não possui exatamente todos os blocos")
        neighbors = {f"{n['host']}:{n['port']}" for n in configs[peer_id]['neighbors']}
        for row in received:
            endpoint = row['endpoint']
            if endpoint not in neighbors or addresses.get(endpoint) != row['remote']:
                raise AssertionError(f"Fonte fora da vizinhança de {peer_id}")
            expected = min(meta['block_size'], meta['file_size'] - row['index'] * meta['block_size'])
            if row['bytes'] != expected:
                raise AssertionError("Tamanho incorreto no log")
            if (row['remote'], peer_id, row['index'], row['bytes']) not in sent:
                raise AssertionError("Recebimento sem envio correspondente nos logs")
            checked += 1
    return dict(status="OK", received_blocks_checked=checked, peers_checked=len(peer_ids)-1)


class Lab:
    def __init__(self, directory, source, block_size=1024, count=2, topology="full"):
        self.directory = Path(directory).resolve()
        if self.directory.exists() and any(self.directory.iterdir()):
            raise ValueError(f"Pasta de experimento já contém dados: {self.directory}; use uma pasta nova")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.source = Path(source).resolve()
        self.meta_path = self.directory / "metadata.json"
        self.meta = create_metadata(self.source, block_size, self.meta_path)
        self.ids = list("ABCD"[:count])
        ports = free_ports(count)
        self.configs, self.processes, self.consoles = {}, {}, {}
        for i, peer_id in enumerate(self.ids):
            indices = [j for j in range(count) if j != i and
                       (topology == "full" or abs(j - i) == 1)]
            config = dict(id=peer_id, host="127.0.0.1", port=ports[i],
                          neighbors=[dict(host="127.0.0.1", port=ports[j]) for j in indices])
            self.configs[peer_id] = self.directory / f"config_{peer_id}.json"
            write_json(self.configs[peer_id], config)
        self.started = time.perf_counter()

    def start(self, peer_id, seed=False, delay=0, timeout=180):
        command = [sys.executable, "-m", "p2p", "peer", "--config", str(self.configs[peer_id]),
                   "--meta", str(self.meta_path), "--dir", str(self.directory / peer_id),
                   "--log", str(self.directory / f"{peer_id}.jsonl"), "--timeout", str(timeout),
                   "--delay", str(delay)]
        if seed:
            command += ["--seed-file", str(self.source)]
        console = (self.directory / f"{peer_id}_console.txt").open("a", encoding="utf-8")
        self.consoles[peer_id] = console
        self.processes[peer_id] = subprocess.Popen(command, cwd=ROOT, stdout=console, stderr=subprocess.STDOUT)

    def peer_events(self, peer_id):
        return events(self.directory / f"{peer_id}.jsonl")

    def wait_for(self, condition, timeout=180):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return
            for peer_id, proc in self.processes.items():
                if proc.poll() is not None:
                    raise RuntimeError(f"Peer {peer_id} encerrou com código {proc.returncode}; "
                                       f"consulte {self.directory / (peer_id + '_console.txt')}")
            time.sleep(0.025)
        raise TimeoutError(f"Tempo esgotado em {self.directory}")

    def wait_complete(self, peer_ids=None, timeout=180):
        selected = peer_ids or self.ids
        self.wait_for(lambda: all((self.directory / p / "completion.json").exists() for p in selected), timeout)
        return {p: json.loads((self.directory / p / "completion.json").read_text(encoding="utf-8"))
                for p in selected}

    def verify(self, peer_ids=None):
        selected = peer_ids or self.ids[1:]
        expected = sha256_file(self.source)
        for peer_id in selected:
            target = self.directory / peer_id / self.source.name
            if target.stat().st_size != self.meta["file_size"] or sha256_file(target) != expected:
                raise AssertionError(f"Arquivo inválido em {peer_id}")

    def stop(self, peer_id):
        proc = self.processes.pop(peer_id, None)
        if proc and proc.poll() is None:
            if os.name == "posix":
                proc.send_signal(signal.SIGINT)
            else:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        console = self.consoles.pop(peer_id, None)
        if console:
            console.close()

    def close(self):
        for peer_id in list(self.processes):
            self.stop(peer_id)


def summarize_lab(lab, completed):
    leecher = [p for p in lab.ids if p != "A"]
    rows = [row for p in lab.ids for row in lab.peer_events(p)]
    relays = [row for row in rows if row["event"] == "BLOCK_SENT" and row["peer"] != "A"]
    return dict(peers=len(lab.ids), file_bytes=lab.meta["file_size"], block_bytes=lab.meta["block_size"],
                block_count=len(lab.meta["block_hashes"]), leechers_verified=len(leecher),
                max_download_seconds=round(max(completed[p]["seconds"] for p in leecher), 6),
                wall_seconds=round(time.perf_counter() - lab.started, 6),
                relayed_blocks=len(relays),
                relayed_while_incomplete=sum(row["while_incomplete"] for row in relays),
                source_counts={p: completed[p]["sources"] for p in leecher},
                sha256=lab.meta["sha256"], status="OK")
