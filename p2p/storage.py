"""Metadados, validação, armazenamento parcial e publicação do arquivo final."""

import hashlib
import json
import os
import re
from pathlib import Path

MAX_BLOCK = 4 * 1024 * 1024


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_id(fields):
    raw = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_metadata(source, block_size, output):
    source = Path(source)
    if type(block_size) is not int or not 1 <= block_size <= MAX_BLOCK:
        raise ValueError("Tamanho de bloco deve estar entre 1 e 4194304 bytes")
    blocks, full, size = [], hashlib.sha256(), 0
    with source.open("rb") as stream:
        for chunk in iter(lambda: stream.read(block_size), b""):
            blocks.append(hashlib.sha256(chunk).hexdigest())
            full.update(chunk)
            size += len(chunk)
    meta = dict(version=1, file_name=source.name, file_size=size,
                block_size=block_size, block_hashes=blocks, sha256=full.hexdigest())
    meta["file_id"] = metadata_id(meta)
    validate_metadata(meta)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta


def validate_metadata(meta):
    required = {"version", "file_name", "file_size", "block_size", "block_hashes", "sha256", "file_id"}
    if not isinstance(meta, dict) or set(meta) != required or meta["version"] != 1:
        raise ValueError("Formato de metadados inválido")
    name = meta["file_name"]
    if (not isinstance(name, str) or name in ("", ".", "..")
            or any(c in name for c in '/\\:\x00') or Path(name).name != name):
        raise ValueError("Nome de arquivo inválido")
    size, block = meta["file_size"], meta["block_size"]
    if type(size) is not int or size < 0 or type(block) is not int or not 1 <= block <= MAX_BLOCK:
        raise ValueError("Tamanho de arquivo/bloco inválido")
    count = (size + block - 1) // block
    hashes = meta["block_hashes"]
    if not isinstance(hashes, list) or len(hashes) != count:
        raise ValueError("Quantidade de hashes de bloco inválida")
    for digest in hashes + [meta["sha256"], meta["file_id"]]:
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Hash SHA-256 inválido")
    fields = {k: v for k, v in meta.items() if k != "file_id"}
    if metadata_id(fields) != meta["file_id"]:
        raise ValueError("Identificador dos metadados não confere")
    return meta


def load_metadata(path):
    return validate_metadata(json.loads(Path(path).read_text(encoding="utf-8")))


class BlockStore:
    def __init__(self, meta, directory, seed_file=None):
        self.meta = validate_metadata(meta)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.final = self.directory / meta["file_name"]
        self.partial = self.directory / ("." + meta["file_name"] + "." + meta["file_id"][:12] + ".part")
        self.count = len(meta["block_hashes"])
        self.have = bytearray(self.count)
        self.complete_count = 0
        self.published = False
        if seed_file is not None:
            self.path = Path(seed_file)
            if self.path.stat().st_size != meta["file_size"] or sha256_file(self.path) != meta["sha256"]:
                raise ValueError("Arquivo do seeder não corresponde aos metadados")
            self.stream = self.path.open("rb")
            self.published = True
        elif self.final.exists():
            self.path = self.final
            if self.path.stat().st_size != meta["file_size"] or sha256_file(self.path) != meta["sha256"]:
                raise ValueError("Arquivo final já existe com outro conteúdo; use outra pasta")
            self.stream = self.path.open("rb")
            self.published = True
        else:
            self.path = self.partial
            exists = self.path.exists()
            self.stream = self.path.open("r+b" if exists else "w+b", buffering=0)
            self.stream.truncate(meta["file_size"])
        # A retomada verifica o conteúdo real; não confia em um bitmap antigo.
        for index in range(self.count):
            self.stream.seek(index * meta["block_size"])
            data = self.stream.read(self.expected_size(index))
            if hashlib.sha256(data).hexdigest() == meta["block_hashes"][index]:
                self.have[index] = 1
                self.complete_count += 1
        if self.published and not self.complete:
            self.close()
            raise ValueError("Hashes dos blocos do seeder não correspondem aos metadados")

    @property
    def complete(self):
        return self.complete_count == self.count

    def expected_size(self, index):
        if type(index) is not int or not 0 <= index < self.count:
            raise ValueError("Índice de bloco inválido")
        return min(self.meta["block_size"], self.meta["file_size"] - index * self.meta["block_size"])

    def read(self, index):
        size = self.expected_size(index)
        if not self.have[index]:
            raise ValueError("Bloco indisponível")
        self.stream.seek(index * self.meta["block_size"])
        data = self.stream.read(size)
        if len(data) != size or hashlib.sha256(data).hexdigest() != self.meta["block_hashes"][index]:
            raise ValueError("Bloco local corrompido")
        return data

    def accept(self, index, data):
        if len(data) != self.expected_size(index):
            raise ValueError("Tamanho do bloco incorreto")
        if hashlib.sha256(data).hexdigest() != self.meta["block_hashes"][index]:
            raise ValueError("SHA-256 do bloco incorreto")
        if self.have[index]:
            return False
        self.stream.seek(index * self.meta["block_size"])
        written = self.stream.write(data)
        if written != len(data):
            raise OSError("Gravação incompleta do bloco")
        # Nenhum await entre escrita e marcação: outras tarefas não veem bloco parcial.
        self.have[index] = 1
        self.complete_count += 1
        return True

    def finalize(self):
        if not self.complete:
            raise ValueError("Arquivo ainda está incompleto")
        if not self.published:
            self.stream.flush()
            os.fsync(self.stream.fileno())
        if self.path.stat().st_size != self.meta["file_size"] or sha256_file(self.path) != self.meta["sha256"]:
            raise ValueError("Falha na integridade do arquivo remontado")
        if not self.published:
            self.stream.close()
            os.replace(self.partial, self.final)
            self.path = self.final
            self.stream = self.path.open("rb")
            self.published = True
        return self.path

    def close(self):
        self.stream.close()
