from __future__ import annotations

from doc_forge import __version__
from doc_forge.app.api import readyz


def test_package_imports() -> None:
    assert __version__ == "0.1.0"


def test_readyz_payload() -> None:
    assert readyz() == {"status": "ok"}
