from __future__ import annotations

import os
import time
from collections.abc import Sequence


def run_worker(*, poll_seconds: float | None = None) -> None:
    interval = poll_seconds
    if interval is None:
        interval = float(os.environ.get("DOC_FORGE_WORKER_POLL_SECONDS", "1.0"))

    while True:
        time.sleep(interval)


def main(argv: Sequence[str] | None = None) -> int:
    _ = argv
    run_worker()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
