"""Shared local Docker answer-generator defaults for developer workflows."""

from __future__ import annotations

import argparse
import os
import platform
import shlex
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
DEFAULT_HOST_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
DEFAULT_CONTAINER_OLLAMA_BASE_URL = "http://ollama:11434"
DEFAULT_HOST_OLLAMA_HEALTH_URL = "http://127.0.0.1:11434/api/tags"
_MANAGED_ENV_KEYS = (
    "DOC_FORGE_ANSWER_GENERATOR_BACKEND",
    "DOC_FORGE_ANSWER_GENERATOR_MODEL",
    "OLLAMA_BASE_URL",
)


@dataclass(frozen=True)
class DockerLocalGeneratorSelection:
    environment: dict[str, str]
    backend: str
    reason: str
    using_host_ollama: bool


def host_ollama_is_ready(
    *,
    health_url: str = DEFAULT_HOST_OLLAMA_HEALTH_URL,
    timeout_seconds: float = 0.5,
) -> bool:
    try:
        with urllib.request.urlopen(health_url, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 500)
            return 200 <= status < 300
    except (OSError, urllib.error.URLError):
        return False


def resolve_docker_local_generator(
    environ: Mapping[str, str] | None = None,
    *,
    system: str | None = None,
    machine: str | None = None,
    host_ollama_ready: bool | None = None,
) -> DockerLocalGeneratorSelection:
    env = dict(os.environ if environ is None else environ)
    resolved_system = platform.system() if system is None else system
    resolved_machine = platform.machine() if machine is None else machine
    apple_local = resolved_system == "Darwin" and resolved_machine == "arm64"

    explicit_backend = env.get("DOC_FORGE_ANSWER_GENERATOR_BACKEND", "").strip()
    explicit_model = env.get("DOC_FORGE_ANSWER_GENERATOR_MODEL", "").strip()
    explicit_base_url = env.get("OLLAMA_BASE_URL", "").strip()

    if explicit_backend:
        if explicit_backend.lower() != "ollama":
            environment = {"DOC_FORGE_ANSWER_GENERATOR_BACKEND": explicit_backend}
            if explicit_model:
                environment["DOC_FORGE_ANSWER_GENERATOR_MODEL"] = explicit_model
            if explicit_base_url:
                environment["OLLAMA_BASE_URL"] = explicit_base_url
            return DockerLocalGeneratorSelection(
                environment=environment,
                backend=explicit_backend,
                reason="explicit_backend",
                using_host_ollama=False,
            )

        if explicit_base_url:
            base_url = explicit_base_url
            using_host_ollama = base_url == DEFAULT_HOST_OLLAMA_BASE_URL
            reason = "explicit_backend"
        else:
            ready = (
                host_ollama_is_ready()
                if host_ollama_ready is None and apple_local
                else bool(host_ollama_ready)
            )
            if apple_local and ready:
                base_url = DEFAULT_HOST_OLLAMA_BASE_URL
                using_host_ollama = True
                reason = "explicit_backend_host_ollama"
            else:
                base_url = DEFAULT_CONTAINER_OLLAMA_BASE_URL
                using_host_ollama = False
                reason = "explicit_backend_container_ollama"

        return DockerLocalGeneratorSelection(
            environment={
                "DOC_FORGE_ANSWER_GENERATOR_BACKEND": explicit_backend,
                "DOC_FORGE_ANSWER_GENERATOR_MODEL": explicit_model or DEFAULT_OLLAMA_MODEL,
                "OLLAMA_BASE_URL": base_url,
            },
            backend=explicit_backend,
            reason=reason,
            using_host_ollama=using_host_ollama,
        )

    ready = (
        host_ollama_is_ready()
        if host_ollama_ready is None and apple_local
        else bool(host_ollama_ready)
    )
    if apple_local and ready:
        return DockerLocalGeneratorSelection(
            environment={
                "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "ollama",
                "DOC_FORGE_ANSWER_GENERATOR_MODEL": explicit_model or DEFAULT_OLLAMA_MODEL,
                "OLLAMA_BASE_URL": explicit_base_url or DEFAULT_HOST_OLLAMA_BASE_URL,
            },
            backend="ollama",
            reason="apple_silicon_host_ollama",
            using_host_ollama=True,
        )

    reason = (
        "deterministic_non_apple_host"
        if not apple_local
        else "deterministic_host_ollama_unavailable"
    )
    return DockerLocalGeneratorSelection(
        environment={
            "DOC_FORGE_ANSWER_GENERATOR_BACKEND": "deterministic",
        },
        backend="deterministic",
        reason=reason,
        using_host_ollama=False,
    )


def format_shell_env(selection: DockerLocalGeneratorSelection) -> str:
    lines: list[str] = []
    for key in _MANAGED_ENV_KEYS:
        value = selection.environment.get(key)
        if value is None:
            lines.append(f"unset {key}")
            continue
        lines.append(f"export {key}={shlex.quote(value)}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m doc_forge.devtools.docker_local_generator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "shell-env",
        help="print shell exports for Docker-local answer-generation defaults",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "shell-env":
        print(format_shell_env(resolve_docker_local_generator()))
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
