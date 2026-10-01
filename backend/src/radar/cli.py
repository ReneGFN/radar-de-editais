import argparse
import json
from pathlib import Path

from .ingestion import prepare, select_and_download, hydrate


def main():
    parser = argparse.ArgumentParser(description="Preparação local do Radar de Editais")
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--start", required=True)
    collect.add_argument("--end", required=True)
    collect.add_argument("--uf", default="SP")
    collect.add_argument("--count", type=int, default=10)
    extract = commands.add_parser("prepare")
    extract.add_argument("manifest", type=Path)
    download = commands.add_parser("hydrate")
    download.add_argument("manifest",type=Path)
    commands.add_parser("init-db")
    load = commands.add_parser("load")
    load.add_argument("manifest", type=Path)
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--snapshot", required=True)
    search.add_argument("--edital", required=True)
    args = parser.parse_args()
    if args.command == "collect":
        result = select_and_download(args.start, args.end, args.count, args.uf)
        result = {"snapshot_id": result["snapshot_id"], "editais": len(result["editais"]), "selection_complete": result["selection_complete"], "rejections": len(result["rejections"])}
    elif args.command == "prepare":
        result = prepare(args.manifest)
    elif args.command == "hydrate":
        result = hydrate(args.manifest)
    else:
        from .storage import initialize, load_corpus, search_corpus
        if args.command == "init-db":
            result = initialize()
        elif args.command == "load":
            result = load_corpus(args.manifest)
        else:
            result = search_corpus(args.query, args.snapshot, args.edital)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
