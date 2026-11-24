"""Command-line interface for NYX."""
import argparse
from pathlib import Path
import sys

from . import run
from .errors import NyxError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="nyx", description="NYX language prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="execute a .nyx source file")
    run_parser.add_argument("file", type=Path, help="path to source file")
    args = parser.parse_args(argv)

    if not args.file.is_file():
        print(f"nyx: file not found: {args.file}", file=sys.stderr)
        return 2
    try:
        # utf-8-sig transparently accepts UTF-8 files with or without a BOM.
        run(
            args.file.read_text(encoding="utf-8-sig"),
            source_path=args.file.resolve(),
        )
    except (NyxError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
