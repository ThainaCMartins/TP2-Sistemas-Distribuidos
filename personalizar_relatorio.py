"""Preenche nome e URL no DOCX com a biblioteca padrão, sem alterar o original."""

import argparse
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape
from zipfile import ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--autor", default="Giovanna Silva")
    args = parser.parse_args()
    parsed = urlparse(args.repo)
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path.strip("/"):
        parser.error("Informe uma URL HTTPS completa do repositório")
    root = Path(__file__).resolve().parent / "relatorio"
    source = root / "TP2_Relatorio.docx"
    target = root / "TP2_Relatorio_Preenchido.docx"
    with ZipFile(source) as original, ZipFile(target, "w") as updated:
        for item in original.infolist():
            data = original.read(item.filename)
            if item.filename == "word/document.xml":
                data = data.replace(b"INSIRA_A_URL_DO_REPOSITORIO", escape(args.repo).encode("utf-8"))
                data = data.replace(b"Giovanna Silva", escape(args.autor).encode("utf-8"))
            updated.writestr(item, data)
    print(f"Criado: {target}. Abra, confira a paginação e exporte para PDF.")


if __name__ == "__main__":
    main()
