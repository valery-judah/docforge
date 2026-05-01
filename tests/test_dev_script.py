from __future__ import annotations

import os
import re
from pathlib import Path


def test_dev_script_contract() -> None:
    script_path = Path("scripts/dev.sh")
    script = script_path.read_text(encoding="utf-8")

    assert os.access(script_path, os.X_OK)
    assert (
        "Usage: scripts/dev.sh {up-demo|docker|local|seed-demo|playground|reset-demo|down|logs}"
        in script
    )
    assert "up-demo)" in script
    assert "playground)" in script
    assert "up_demo" in script
    assert "make docker-up-build" in script
    assert "uv run poe run-api" in script
    assert 'curl -fsS "$API_URL/readyz"' in script
    assert '-F "file=@${document_path}"' in script
    assert '"$API_URL/corpora/$DEMO_CORPUS_ID/documents"' in script
    assert '"$API_URL/corpora/$DEMO_CORPUS_ID/documents/$document_id/inspection"' in script


def test_dev_script_default_demo_docs_exist() -> None:
    script = Path("scripts/dev.sh").read_text(encoding="utf-8")
    match = re.search(r'DEMO_DOCS="\$\{DOC_FORGE_DEMO_DOCS:-(?P<paths>[^}]+)\}"', script)

    assert match is not None

    demo_paths = match.group("paths").split()
    assert demo_paths == [
        "evals/corpus/research-notes-1.md",
        "evals/corpus/config-reference-1.md",
    ]
    assert all(Path(path).is_file() for path in demo_paths)
