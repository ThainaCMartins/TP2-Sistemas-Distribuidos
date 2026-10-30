import argparse
import json

from experimentos import events


def main():
    parser = argparse.ArgumentParser(description="Exibir eventos selecionados de um log JSONL")
    parser.add_argument("file")
    parser.add_argument("--evento")
    parser.add_argument("--parcial", action="store_true")
    parser.add_argument("--limite", type=int, default=10)
    args = parser.parse_args()
    count = 0
    for row in events(args.file):
        if args.evento and row["event"] != args.evento:
            continue
        if args.parcial and not row.get("while_incomplete", False):
            continue
        print(json.dumps(row, ensure_ascii=False))
        count += 1
        if count >= args.limite:
            break
    print(f"Exibidos: {count}")


if __name__ == "__main__":
    main()
