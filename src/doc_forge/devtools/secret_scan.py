from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_DIFF_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]
    description: str


@dataclass(frozen=True)
class SecretFinding:
    pattern_name: str
    path: str
    line_number: int
    matched_text: str
    line_text: str


PATTERNS: tuple[SecretPattern, ...] = (
    SecretPattern(
        name="gemini_api_key",
        regex=re.compile(r"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
        description="Gemini API key",
    ),
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan the repository for leaked secrets.")
    parser.add_argument(
        "--scope",
        choices=("staged-added", "repo"),
        required=True,
        help="Choose whether to scan staged additions or the tracked repository tree.",
    )
    return parser.parse_args(argv)


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


def _findings_for_line(path: str, line_number: int, line_text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for pattern in PATTERNS:
        for match in pattern.regex.finditer(line_text):
            findings.append(
                SecretFinding(
                    pattern_name=pattern.name,
                    path=path,
                    line_number=line_number,
                    matched_text=match.group(0),
                    line_text=line_text,
                )
            )
    return findings


def scan_text(path: str, text: str) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    for line_number, line_text in enumerate(text.splitlines(), start=1):
        findings.extend(_findings_for_line(path=path, line_number=line_number, line_text=line_text))
    return findings


def _scan_repo(repo_root: Path) -> list[SecretFinding]:
    tracked_files = _run_git(["ls-files", "-z"], cwd=repo_root).stdout.split("\0")
    findings: list[SecretFinding] = []
    for raw_path in tracked_files:
        if not raw_path:
            continue
        file_path = repo_root / raw_path
        if not file_path.is_file():
            continue
        content = file_path.read_bytes()
        if b"\0" in content:
            continue
        findings.extend(scan_text(path=raw_path, text=content.decode("utf-8", errors="replace")))
    return findings


def _scan_staged_added(repo_root: Path) -> list[SecretFinding]:
    diff_text = _run_git(
        [
            "diff",
            "--cached",
            "--unified=0",
            "--no-color",
            "--no-ext-diff",
            "--diff-filter=ACMR",
        ],
        cwd=repo_root,
    ).stdout

    findings: list[SecretFinding] = []
    current_path: str | None = None
    next_line_number: int | None = None

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            if line == "+++ /dev/null":
                current_path = None
            else:
                current_path = line.removeprefix("+++ b/")
            next_line_number = None
            continue

        if line.startswith("@@ "):
            match = _DIFF_HUNK_RE.match(line)
            if match is None:
                next_line_number = None
                continue
            next_line_number = int(match.group(1))
            continue

        if line.startswith("Binary files "):
            current_path = None
            next_line_number = None
            continue

        if line.startswith("+") and not line.startswith("+++"):
            if current_path is not None and next_line_number is not None:
                findings.extend(
                    _findings_for_line(
                        path=current_path,
                        line_number=next_line_number,
                        line_text=line[1:],
                    )
                )
                next_line_number += 1
            continue

        if line.startswith(" ") and next_line_number is not None:
            next_line_number += 1

    return findings


def _redacted_snippet(finding: SecretFinding) -> str:
    return finding.line_text.replace(finding.matched_text, "[REDACTED]")


def _format_report(findings: Sequence[SecretFinding]) -> str:
    lines = ["Secret scan failed. Potential Gemini API key(s) detected:"]
    for finding in findings:
        lines.append(
            "- "
            f"{finding.pattern_name} "
            f"{finding.path}:{finding.line_number} "
            f"{_redacted_snippet(finding)}"
        )
    lines.append("Remove the secret from the codebase and rotate the key before committing.")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        repo_root = _resolve_repo_root()
        findings = (
            _scan_staged_added(repo_root=repo_root)
            if args.scope == "staged-added"
            else _scan_repo(repo_root=repo_root)
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        print(f"Secret scan could not run: {message}", file=sys.stderr)
        return 2

    if findings:
        print(_format_report(findings), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
