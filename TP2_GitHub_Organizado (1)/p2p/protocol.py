"""Enquadramento TCP: uint32 big-endian + JSON UTF-8 + conteúdo binário."""

import asyncio
import json
import struct

MAX_HEADER = 64 * 1024
MAX_PAYLOAD = 4 * 1024 * 1024
VERSION = 1


class ProtocolError(ValueError):
    pass


def encode_message(message, payload=b""):
    if not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD:
        raise ProtocolError("Conteúdo binário inválido ou muito grande")
    header = dict(message, version=VERSION, payload_len=len(payload))
    raw = json.dumps(header, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if not 0 < len(raw) <= MAX_HEADER:
        raise ProtocolError("Cabeçalho muito grande")
    return struct.pack("!I", len(raw)) + raw + payload


async def send_message(writer, message, payload=b"", timeout=10):
    writer.write(encode_message(message, payload))
    await asyncio.wait_for(writer.drain(), timeout)


async def read_message(reader, timeout=10):
    async def read_frame():
        length = struct.unpack("!I", await reader.readexactly(4))[0]
        if not 0 < length <= MAX_HEADER:
            raise ProtocolError("Tamanho de cabeçalho inválido")
        try:
            header = json.loads((await reader.readexactly(length)).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("JSON inválido") from exc
        if not isinstance(header, dict) or header.get("version") != VERSION:
            raise ProtocolError("Versão de protocolo inválida")
        size = header.get("payload_len")
        if type(size) is not int or not 0 <= size <= MAX_PAYLOAD:
            raise ProtocolError("Tamanho de conteúdo inválido")
        if not isinstance(header.get("type"), str):
            raise ProtocolError("Tipo de mensagem ausente")
        return header, await reader.readexactly(size)

    return await asyncio.wait_for(read_frame(), timeout)


def pack_bitmap(have):
    data = bytearray((len(have) + 7) // 8)
    for index, present in enumerate(have):
        if present:
            data[index // 8] |= 1 << (index % 8)
    return bytes(data)


def unpack_bitmap(data, count):
    if len(data) != (count + 7) // 8:
        raise ProtocolError("Bitmap com tamanho incorreto")
    return bytearray(bool(data[i // 8] & (1 << (i % 8))) for i in range(count))
