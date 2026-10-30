"""Gera arquivo aleatório, metadados e configurações manuais para 2/4 peers."""

import argparse
from pathlib import Path

from experimentos import random_file, write_json
from p2p.storage import create_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", default="demo")
    parser.add_argument("--size", type=int, default=1024 * 1024)
    parser.add_argument("--block-size", type=int, default=1024)
    parser.add_argument("--base-port", type=int, default=9000)
    args = parser.parse_args()
    if args.size < 0 or not 1 <= args.base_port <= 65531:
        parser.error("Tamanho ou porta inválidos")
    root = Path(args.dir)
    if root.exists() and any(root.iterdir()):
        parser.error("Pasta já contém dados; escolha outro --dir")
    original = random_file(root / "original.bin", args.size)
    create_metadata(original, args.block_size, root / "metadata.json")
    for count in (2, 4):
        for index in range(count):
            write_json(root / f"config{count}" / f"{'ABCD'[index]}.json",
                       dict(id="ABCD"[index], host="127.0.0.1", port=args.base_port + index + 1,
                            neighbors=[dict(host="127.0.0.1", port=args.base_port + j + 1)
                                       for j in range(count) if j != index]))
    print(f"Pronto: {root}. Consulte LEIA_PRIMEIRO.md para os comandos dos terminais.")


if __name__ == "__main__":
    main()
