"""Demonstrações reais de encaminhamento parcial, simetria e retomada."""

import argparse
import json
import sys
from pathlib import Path

from experimentos import Lab, random_file, write_json
from p2p.storage import BlockStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="validacao_local")
    args = parser.parse_args()
    root = Path(args.out).resolve()
    if root.exists() and any(root.iterdir()):
        parser.error("Pasta de saída já contém dados; use outra pasta")
    root.mkdir(parents=True, exist_ok=True)
    source = random_file(root / "original.bin", 1024 * 1024 + 37)
    outcomes = []

    # Malha completa: A, B, C e D conhecem todos os demais.
    # A inicia como seeder; os receptores também podem compartilhar blocos.
    lab = Lab(root / "malha_completa", source, count=4, topology="full")
    try:
        for peer in "ABCD":
            config = json.loads(lab.configs[peer].read_text(encoding="utf-8"))
            assert len(config["neighbors"]) == 3, f"{peer} não conhece os três vizinhos"
        lab.start("A", seed=True, delay=0.002)
        for peer in "BCD":
            lab.start(peer)
        completed = lab.wait_complete()
        lab.verify()
        # A topologia permite todas as conexões; os logs comprovam
        # quais transferências efetivamente ocorreram.
        source_counts = {p: completed[p]["sources"] for p in "BCD"}
        relays = {p: sum(
            e["event"] == "BLOCK_SENT" and e.get("while_incomplete", False)
            for e in lab.peer_events(p)) for p in "BCD"}
        assert sum(relays.values()) > 0, "Não houve compartilhamento parcial entre receptores"
        assert any(source_counts[p].get(q, 0) > 0
                   for p in "BCD" for q in "BCD" if p != q), (
                       "Nenhum receptor recebeu blocos de outro receptor")
        outcomes.append(dict(
            test="Compartilhamento parcial em malha completa A-B-C-D",
            status="OK", topology="full", neighbors_per_peer=3,
            evidence=relays, sources=source_counts,
            note="A configuração permite todos os pares; as fontes registradas mostram as trocas reais."))
    finally:
        lab.close()

    # Dois nós começam com metades complementares; não há seeder completo.
    lab = Lab(root / "bidirecional", source, count=2)
    try:
        with source.open("rb") as stream:
            content = stream.read()
        for parity, peer in enumerate("AB"):
            store = BlockStore(lab.meta, lab.directory / peer)
            try:
                for index in range(parity, store.count, 2):
                    start = index * lab.meta["block_size"]
                    store.accept(index, content[start:start + store.expected_size(index)])
            finally:
                store.close()
        lab.start("A", delay=0.001)
        lab.start("B", delay=0.001)
        completed = lab.wait_complete()
        lab.verify(["A", "B"])
        assert completed["A"]["sources"].get("B", 0) > 0
        assert completed["B"]["sources"].get("A", 0) > 0
        intervals = {}
        for peer in "AB":
            rows = lab.peer_events(peer)
            received = [r["time"] for r in rows if r["event"] == "BLOCK_RECEIVED"]
            sent = [r for r in rows if r["event"] == "BLOCK_SENT" and r["while_incomplete"]]
            assert sent, "Ambos devem enviar enquanto incompletos"
            intervals[peer] = dict(received=len(received), sent_before_complete=len(sent))
        outcomes.append(dict(test="Troca bidirecional sem seeder completo", status="OK", evidence=intervals))
    finally:
        lab.close()

    # Interrompe B, corrompe um bloco já gravado e reinicia o mesmo diretório.
    lab = Lab(root / "retomada", source, count=2)
    try:
        lab.start("A", seed=True, delay=0.002)
        lab.start("B")
        lab.wait_for(lambda: sum(e["event"] == "BLOCK_RECEIVED" for e in lab.peer_events("B")) >= 30)
        lab.stop("B")
        received = [e for e in lab.peer_events("B") if e["event"] == "BLOCK_RECEIVED"]
        index = received[0]["index"]
        partial = next((lab.directory / "B").glob("*.part"))
        with partial.open("r+b") as stream:
            stream.seek(index * lab.meta["block_size"])
            data = stream.read(1)
            stream.seek(index * lab.meta["block_size"])
            stream.write(bytes([data[0] ^ 255]))
        lab.start("B")
        completed = lab.wait_complete()
        lab.verify()
        ready = [e for e in lab.peer_events("B") if e["event"] == "READY"][-1]
        assert ready["resumed_blocks"] >= 29
        assert ready["resumed_blocks"] < len(received)
        downloads_of_bad = [e for e in lab.peer_events("B")
                            if e["event"] == "BLOCK_RECEIVED" and e["index"] == index]
        assert len(downloads_of_bad) == 2
        outcomes.append(dict(test="Retomada após interrupção e bloco local corrompido", status="OK",
                             before_stop=len(received), reused=ready["resumed_blocks"],
                             corrupted_index=index, downloads_of_corrupted_index=len(downloads_of_bad),
                             sha256=completed["B"]["sha256"]))
    finally:
        lab.close()
    write_json(root / "validacao.json", outcomes)
    print(json.dumps(outcomes, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
