import argparse
import asyncio
import json
import sys
from pathlib import Path

from .storage import create_metadata, load_metadata, sha256_file


def main():
    parser = argparse.ArgumentParser(description="TP2 - Transferência de arquivos P2P")
    commands = parser.add_subparsers(dest="command", required=True)
    meta = commands.add_parser("meta", help="Gerar os metadados antes da transferência")
    meta.add_argument("file")
    meta.add_argument("--block-size", type=int, default=1024)
    meta.add_argument("--out", required=True)
    peer = commands.add_parser("peer", help="Iniciar servidor e cliente do peer")
    peer.add_argument("--config", required=True)
    peer.add_argument("--meta", required=True)
    peer.add_argument("--dir", dest="directory", required=True)
    peer.add_argument("--seed-file")
    peer.add_argument("--log", required=True)
    peer.add_argument("--timeout", type=float, default=120)
    peer.add_argument("--exit-after", type=float, default=None,
                      help="Sair N segundos após concluir; omitir para continuar compartilhando")
    peer.add_argument("--delay", type=float, default=0,
                      help="Atraso artificial em segundos por bloco servido, apenas para demonstração")
    verify = commands.add_parser("verify", help="Comparar tamanho e SHA-256 com os metadados")
    verify.add_argument("file")
    verify.add_argument("--meta", required=True)
    args = parser.parse_args()
    try:
        if args.command == "meta":
            info = create_metadata(args.file, args.block_size, args.out)
            print(json.dumps(dict(status="OK", file_id=info["file_id"], blocks=len(info["block_hashes"]),
                                  size=info["file_size"], sha256=info["sha256"]), indent=2))
        elif args.command == "verify":
            info = load_metadata(args.meta)
            digest = sha256_file(args.file)
            size = Path(args.file).stat().st_size
            good = digest == info["sha256"] and size == info["file_size"]
            print(json.dumps(dict(status="OK" if good else "FALHOU", size=size, sha256=digest), indent=2))
            return 0 if good else 1
        else:
            if args.timeout <= 0 or args.delay < 0 or (args.exit_after is not None and args.exit_after < 0):
                raise ValueError("Tempos inválidos")
            from .peer import Peer
            asyncio.run(Peer(args).run())
    except KeyboardInterrupt:
        print("Peer encerrado. Os blocos parciais podem ser retomados.")
    except (OSError, ValueError, TimeoutError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
