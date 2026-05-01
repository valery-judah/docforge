"""Resolve the local DocForge API endpoint across host/container boundaries."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

DEFAULT_API_PORT = "8000"
DEFAULT_DISCOVERY_HOSTS = ("127.0.0.1", "host.docker.internal", "172.17.0.1")


@dataclass(frozen=True)
class ApiBaseUrlResolution:
    base_url: str
    source: str
    checked: bool


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("API base URL must not be empty.")
    parsed = urllib.parse.urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("API base URL must include an http:// or https:// scheme and host.")
    return normalized


def candidate_base_urls(environ: Mapping[str, str] | None = None) -> list[ApiBaseUrlResolution]:
    env = os.environ if environ is None else environ
    explicit_base_url = env.get("DOC_FORGE_API_BASE_URL", "").strip()
    if explicit_base_url:
        return [
            ApiBaseUrlResolution(
                base_url=normalize_base_url(explicit_base_url),
                source="DOC_FORGE_API_BASE_URL",
                checked=False,
            )
        ]

    port = env.get("DOC_FORGE_API_PORT", "").strip() or env.get("PORT", "").strip()
    if not port:
        port = DEFAULT_API_PORT

    configured_hosts = env.get("DOC_FORGE_API_DISCOVERY_HOSTS", "").strip()
    hosts = (
        tuple(host.strip() for host in configured_hosts.split(",") if host.strip())
        if configured_hosts
        else DEFAULT_DISCOVERY_HOSTS
    )

    return [
        ApiBaseUrlResolution(
            base_url=f"http://{host}:{port}",
            source=f"host:{host}",
            checked=False,
        )
        for host in hosts
    ]


def probe_readyz(base_url: str, *, timeout_seconds: float = 0.5) -> bool:
    readyz_url = f"{normalize_base_url(base_url)}/readyz"
    try:
        with urllib.request.urlopen(readyz_url, timeout=timeout_seconds) as response:
            status = cast(int, getattr(response, "status", 500))
            if status < 200 or status >= 300:
                return False
            payload = cast(bytes, response.read())
    except (OSError, ValueError, urllib.error.URLError):
        return False

    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    return decoded == {"status": "ok"}


def resolve_api_base_url(
    environ: Mapping[str, str] | None = None,
    *,
    check: bool = True,
    timeout_seconds: float = 0.5,
) -> ApiBaseUrlResolution:
    candidates = candidate_base_urls(environ)
    if not check:
        return candidates[0]

    for candidate in candidates:
        if probe_readyz(candidate.base_url, timeout_seconds=timeout_seconds):
            return ApiBaseUrlResolution(
                base_url=candidate.base_url,
                source=candidate.source,
                checked=True,
            )

    raise RuntimeError(
        "DocForge API is not reachable. Set DOC_FORGE_API_BASE_URL explicitly, "
        "or start the Docker stack with `make docker-up-build`."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m doc_forge.devtools.api_discovery")
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Print the first configured candidate without probing /readyz.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help="Connection timeout in seconds for each /readyz probe.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print source metadata as JSON instead of only the URL.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        resolution = resolve_api_base_url(check=not args.no_check, timeout_seconds=args.timeout)
    except (RuntimeError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")

    if args.verbose:
        payload: dict[str, Any] = {
            "base_url": resolution.base_url,
            "source": resolution.source,
            "checked": resolution.checked,
        }
        print(json.dumps(payload, sort_keys=True))
        return 0

    print(resolution.base_url)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
