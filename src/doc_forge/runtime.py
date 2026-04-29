from __future__ import annotations

import argparse
import os
from collections.abc import Sequence


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m doc_forge.runtime")
    parser.add_argument("command", choices=("api", "worker"))
    return parser.parse_args(argv)


def _run_api() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("doc_forge.app.api:app", host="0.0.0.0", port=port)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "api":
        _run_api()
        return 0

    from doc_forge.lifecycle.worker import run_worker

    run_worker()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
