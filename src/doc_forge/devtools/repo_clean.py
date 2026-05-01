from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CleanupTarget:
    relative_path: str
    kind: str
    reason: str


_STATIC_DIR_TARGETS: tuple[CleanupTarget, ...] = (
    CleanupTarget(".pytest_cache", "dir", "pytest cache"),
    CleanupTarget(".ruff_cache", "dir", "ruff cache"),
    CleanupTarget(".mypy_cache", "dir", "mypy cache"),
    CleanupTarget(".pyright", "dir", "pyright cache"),
    CleanupTarget(".tmp_uv_cache", "dir", "uv package cache"),
    CleanupTarget("htmlcov", "dir", "coverage HTML output"),
    CleanupTarget("data/raw", "dir", "raw lifecycle artifacts"),
    CleanupTarget("data/normalized", "dir", "normalized lifecycle artifacts"),
    CleanupTarget("data/extracted", "dir", "extracted lifecycle artifacts"),
    CleanupTarget("data/logs", "dir", "archived compose and e2e logs"),
    CleanupTarget("data/context/queries", "dir", "collected query context bundles"),
)

_OPTIONAL_DIR_TARGETS: tuple[CleanupTarget, ...] = (
    CleanupTarget("data/models", "dir", "prepared local embedding models"),
    CleanupTarget("data/huggingface", "dir", "downloaded local model cache"),
)

_STATIC_FILE_TARGETS: tuple[CleanupTarget, ...] = (
    CleanupTarget("pyright_output.json", "file", "pyright report output"),
)

_STATIC_FILE_GLOBS: tuple[CleanupTarget, ...] = (
    CleanupTarget(".coverage", "file", "coverage data file"),
    CleanupTarget(".coverage.*", "file", "coverage data file"),
)

_SKIP_WALK_PREFIXES: tuple[Path, ...] = (
    Path(".git"),
    Path("data/models"),
    Path("data/huggingface"),
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove generated local state while preserving durable repo inputs."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the cleanup plan without deleting anything.",
    )
    parser.add_argument(
        "--include-model-cache",
        action="store_true",
        help="Also remove prepared local models and downloaded model caches if present.",
    )
    return parser.parse_args(list(argv))


def _run_git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _resolve_repo_root() -> Path:
    completed = _run_git(["rev-parse", "--show-toplevel"], cwd=Path.cwd())
    return Path(completed.stdout.strip())


def _should_skip_walk(relative_path: Path) -> bool:
    if not relative_path.parts:
        return False
    if any(part.startswith(".venv") or part.startswith(".tmp_") for part in relative_path.parts):
        return True
    return any(
        relative_path == prefix or prefix in relative_path.parents for prefix in _SKIP_WALK_PREFIXES
    )


def _should_skip_tool_walk(relative_path: Path) -> bool:
    if not relative_path.parts:
        return False
    if any(part.startswith(".tmp_") for part in relative_path.parts):
        return True
    return any(
        relative_path == prefix or prefix in relative_path.parents for prefix in _SKIP_WALK_PREFIXES
    )


def _discover_pycache_dirs(repo_root: Path) -> Iterable[CleanupTarget]:
    for current_root, dirnames, _ in os.walk(repo_root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(repo_root)
        dirnames[:] = [
            dirname for dirname in dirnames if not _should_skip_walk(relative_root / dirname)
        ]
        if current_path.name != "__pycache__":
            continue
        yield CleanupTarget(
            relative_path=str(relative_root),
            kind="dir",
            reason="Python bytecode cache",
        )
        dirnames[:] = []


def _discover_tool_env_dirs(repo_root: Path) -> Iterable[CleanupTarget]:
    tools_root = repo_root / "tools"
    if not tools_root.exists():
        return

    for current_root, dirnames, _ in os.walk(tools_root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(repo_root)
        dirnames[:] = [
            dirname for dirname in dirnames if not _should_skip_tool_walk(relative_root / dirname)
        ]
        if current_path.name != ".venv":
            continue
        yield CleanupTarget(
            relative_path=str(relative_root),
            kind="dir",
            reason="tool virtual environment",
        )
        dirnames[:] = []


def _existing_static_targets(
    repo_root: Path,
    *,
    include_model_cache: bool,
) -> Iterable[CleanupTarget]:
    directory_targets = list(_STATIC_DIR_TARGETS)
    if include_model_cache:
        directory_targets.extend(_OPTIONAL_DIR_TARGETS)

    for target in directory_targets:
        if (repo_root / target.relative_path).exists():
            yield target

    for target in _STATIC_FILE_TARGETS:
        if (repo_root / target.relative_path).exists():
            yield target

    for target in _STATIC_FILE_GLOBS:
        for matched_path in repo_root.glob(target.relative_path):
            if matched_path.exists():
                yield CleanupTarget(
                    relative_path=str(matched_path.relative_to(repo_root)),
                    kind=target.kind,
                    reason=target.reason,
                )


def build_cleanup_plan(
    repo_root: Path,
    *,
    include_model_cache: bool = False,
) -> list[CleanupTarget]:
    discovered_targets = [
        *_existing_static_targets(repo_root, include_model_cache=include_model_cache),
        *_discover_tool_env_dirs(repo_root),
        *_discover_pycache_dirs(repo_root),
    ]
    deduped = {(target.relative_path, target.kind): target for target in discovered_targets}
    return sorted(deduped.values(), key=lambda target: target.relative_path)


def _remove_target(repo_root: Path, target: CleanupTarget) -> None:
    path = repo_root / target.relative_path
    if target.kind == "dir":
        shutil.rmtree(path)
        return
    path.unlink()


def _render_plan(targets: Sequence[CleanupTarget], *, dry_run: bool) -> str:
    action = "Would remove" if dry_run else "Removed"
    if not targets:
        return "Nothing to remove."
    lines = [f"{action} {len(targets)} path(s):"]
    for target in targets:
        lines.append(f"- {target.kind.upper():4} {target.relative_path} ({target.reason})")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = _resolve_repo_root()
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        print(f"Cleanup could not run: {message}", file=sys.stderr)
        return 2

    targets = build_cleanup_plan(
        repo_root=repo_root,
        include_model_cache=args.include_model_cache,
    )
    if args.dry_run:
        print(_render_plan(targets, dry_run=True))
        return 0

    removed_targets: list[CleanupTarget] = []
    for target in targets:
        _remove_target(repo_root, target)
        removed_targets.append(target)
    print(_render_plan(removed_targets, dry_run=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
