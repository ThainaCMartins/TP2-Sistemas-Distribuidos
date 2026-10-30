import asyncio
import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path

from p2p.protocol import ProtocolError, encode_message, pack_bitmap, read_message, unpack_bitmap
from p2p.storage import BlockStore, create_metadata, metadata_id, validate_metadata


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_fragmented_tcp_frame(self):
        reader = asyncio.StreamReader()
        frame = encode_message({"type": "BLOCK", "index": 5}, b"\x00\xff\x13binary")
        async def feed():
            for index in range(0, len(frame), 3):
                reader.feed_data(frame[index:index + 3])
                await asyncio.sleep(0)
        task = asyncio.create_task(feed())
        header, data = await read_message(reader)
        await task
        self.assertEqual(header["index"], 5)
        self.assertEqual(data, b"\x00\xff\x13binary")

    async def test_coalesced_frames(self):
        reader = asyncio.StreamReader()
        reader.feed_data(encode_message({"type": "HAVE"}) + encode_message({"type": "GET", "index": 2}))
        self.assertEqual((await read_message(reader))[0]["type"], "HAVE")
        self.assertEqual((await read_message(reader))[0]["index"], 2)

    async def test_reject_invalid_length(self):
        reader = asyncio.StreamReader()
        reader.feed_data(struct.pack("!I", 1000000))
        with self.assertRaises(ProtocolError):
            await read_message(reader)

    async def test_truncated_message(self):
        reader = asyncio.StreamReader()
        reader.feed_data(encode_message({"type": "BLOCK"}, b"abc")[:-1])
        reader.feed_eof()
        with self.assertRaises(asyncio.IncompleteReadError):
            await read_message(reader)

    async def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            await read_message(asyncio.StreamReader(), timeout=0.01)

    async def test_bitmap_roundtrip(self):
        have = bytearray([1, 0, 1, 0, 0, 1, 0, 1, 1])
        self.assertEqual(unpack_bitmap(pack_bitmap(have), len(have)), have)
        with self.assertRaises(ProtocolError):
            unpack_bitmap(b"", len(have))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "original.bin"
        self.data = bytes(range(256)) * 8 + b"final"
        self.source.write_bytes(self.data)
        self.meta = create_metadata(self.source, 1024, self.root / "meta.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_out_of_order_last_block_and_duplicate(self):
        store = BlockStore(self.meta, self.root / "B")
        try:
            for index in (2, 0, 1):
                offset = index * 1024
                self.assertTrue(store.accept(index, self.data[offset:offset + store.expected_size(index)]))
            self.assertFalse(store.accept(0, self.data[:1024]))
            self.assertEqual(store.finalize().read_bytes(), self.data)
        finally:
            store.close()

    def test_reject_corrupt_and_wrong_size(self):
        store = BlockStore(self.meta, self.root / "B")
        try:
            with self.assertRaises(ValueError):
                store.accept(0, b"x" * 1024)
            with self.assertRaises(ValueError):
                store.accept(0, b"short")
            self.assertEqual(store.complete_count, 0)
            with self.assertRaises(ValueError):
                store.finalize()
        finally:
            store.close()

    def test_resume_rehashes_blocks(self):
        store = BlockStore(self.meta, self.root / "B")
        store.accept(0, self.data[:1024])
        store.accept(1, self.data[1024:2048])
        partial = store.partial
        store.close()
        with partial.open("r+b") as stream:
            stream.write(b"x")
        resumed = BlockStore(self.meta, self.root / "B")
        try:
            self.assertEqual(list(resumed.have), [0, 1, 0])
        finally:
            resumed.close()

    def test_empty_file(self):
        empty = self.root / "empty.bin"
        empty.write_bytes(b"")
        meta = create_metadata(empty, 1024, self.root / "empty.json")
        store = BlockStore(meta, self.root / "B")
        try:
            self.assertTrue(store.complete)
            self.assertEqual(store.finalize().stat().st_size, 0)
        finally:
            store.close()

    def test_metadata_tamper(self):
        broken = copy.deepcopy(self.meta)
        broken["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_metadata(broken)

    def test_reject_path_traversal(self):
        broken = copy.deepcopy(self.meta)
        broken["file_name"] = "../outside.bin"
        broken["file_id"] = metadata_id({k: v for k, v in broken.items() if k != "file_id"})
        with self.assertRaises(ValueError):
            validate_metadata(broken)

    def test_seed_mismatch(self):
        self.source.write_bytes(b"different")
        with self.assertRaises(ValueError):
            BlockStore(self.meta, self.root / "B", self.source)


if __name__ == "__main__":
    unittest.main()
