"""Executa as 24 combinações da Tabela 1 e preserva evidências por peer."""

import argparse
import csv
import json
import platform
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from experimentos import Lab, audit_case, random_file, summarize_lab, write_json

SIZES = [("A_10KiB", 10 * 1024), ("A_20KiB", 20 * 1024),
         ("B_1MiB", 1024**2), ("B_5MiB", 5 * 1024**2),
         ("C_10MiB", 10 * 1024**2), ("C_20MiB", 20 * 1024**2)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="resultados_local")
    parser.add_argument("--repeticoes", type=int, default=1)
    parser.add_argument("--rapido", action="store_true", help="Somente 10 KiB: 4 combinações; não substitui a bateria completa")
    parser.add_argument("--manter-arquivos", action="store_true", help="Preservar arquivos binários; padrão remove cópias após validar")
    args = parser.parse_args()
    if args.repeticoes < 1:
        parser.error("repeticoes deve ser pelo menos 1")
    root = Path(args.out).resolve()
    if root.exists() and any(root.iterdir()):
        parser.error("A pasta de saída já contém dados; escolha outro --out para preservar evidências")
    root.mkdir(parents=True, exist_ok=True)
    env = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
               system=platform.platform(), machine=platform.machine(), processor=platform.processor(),
               topology="vizinhos estáticos em malha completa", network="IPv4 TCP 127.0.0.1 loopback",
               repetitions=args.repeticoes, units="KiB=1024 bytes; MiB=1048576 bytes",
               timing="max_download_seconds: maior READY->COMPLETE dos leechers; wall_seconds: lançamento->verificação",
               files_preserved=args.manter_arquivos)
    write_json(root / "ambiente.json", env)
    inputs = [(name, random_file(root / "inputs" / f"{name}.bin", size))
              for name, size in (SIZES[:1] if args.rapido else SIZES)]
    results = []
    planned = len(inputs) * 2 * 2 * args.repeticoes
    try:
        for name, source in inputs:
            for block in (1024, 4096):
                for count in (2, 4):
                    for rep in range(1, args.repeticoes + 1):
                        case = f"{name}_b{block}_p{count}_r{rep}"
                        lab = Lab(root / case, source, block, count)
                        try:
                            lab.start("A", seed=True)
                            for peer_id in lab.ids[1:]:
                                lab.start(peer_id)
                            completed = lab.wait_complete()
                            lab.verify()
                            verified_at = time.perf_counter()
                            lab.close()
                            write_json(lab.directory / "auditoria_logs.json",
                                       audit_case(lab.directory, lab.ids, lab.meta))
                            row = dict(case=case, file_label=name, repetition=rep, **summarize_lab(lab, completed))
                            row["wall_seconds"] = round(verified_at - lab.started, 6)
                            write_json(lab.directory / "resumo.json", row)
                            results.append(row)
                            write_json(root / "resultados.json", results)
                            print(f"[{len(results)}/{planned}] {case}: OK; "
                                  f"tempo={row['max_download_seconds']:.3f}s; "
                                  f"repasses={row['relayed_blocks']}", flush=True)
                        finally:
                            lab.close()
                        if not args.manter_arquivos:
                            for peer_id in lab.ids[1:]:
                                (lab.directory / peer_id / source.name).unlink(missing_ok=True)
    finally:
        if results:
            keys = [k for k in results[0] if k != "source_counts"]
            with (root / "resultados.csv").open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.DictWriter(stream, fieldnames=keys, delimiter=";")
                writer.writeheader()
                writer.writerows({k: row[k] for k in keys} for row in results)
    if not args.manter_arquivos:
        shutil.rmtree(root / "inputs")
    print(f"Concluído: {len(results)}/{planned} cenários. Evidências em {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
