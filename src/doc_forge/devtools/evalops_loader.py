from __future__ import annotations

import argparse
import time
from collections.abc import Sequence


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan query bundles into the central eval/log observability store."
    )
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--context-root", default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-schema", help="Create observability metadata tables.")

    scan = subparsers.add_parser("scan", help="Scan existing query bundles into the store.")
    scan.add_argument("--loop", action="store_true")
    scan.add_argument("--interval-seconds", type=float, default=10.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "init-schema":
        return 0

    if args.loop:
        while True:
            time.sleep(args.interval_seconds)

    print("scanned_bundles=0 indexed_bundles=0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
