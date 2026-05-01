from __future__ import annotations

import pytest

from doc_forge.app.runtime_checks import validate_runtime
from doc_forge.app.settings import Settings


def test_runtime_check_skips_transformer_cache_env_for_deterministic_model() -> None:
    validate_runtime(Settings(embedding_model="deterministic"), {})


def test_runtime_check_requires_hf_home_for_transformer_model(tmp_path) -> None:
    env = {"TORCHINDUCTOR_CACHE_DIR": str(tmp_path / "torch-cache")}

    with pytest.raises(RuntimeError, match="HF_HOME must be set"):
        validate_runtime(Settings(embedding_model="transformer"), env)


def test_runtime_check_requires_torch_cache_for_transformer_model(tmp_path) -> None:
    env = {"HF_HOME": str(tmp_path / "huggingface")}

    with pytest.raises(RuntimeError, match="TORCHINDUCTOR_CACHE_DIR must be set"):
        validate_runtime(Settings(embedding_model="transformer"), env)


def test_runtime_check_preserves_existing_env_and_creates_dirs(tmp_path) -> None:
    env = {
        "HF_HOME": str(tmp_path / "custom-hf"),
        "TORCH_COMPILE_DISABLE": "0",
        "TORCHINDUCTOR_CACHE_DIR": str(tmp_path / "custom-torch"),
    }

    validate_runtime(Settings(embedding_model="transformer"), env)

    assert env["HF_HOME"] == str(tmp_path / "custom-hf")
    assert env["TORCH_COMPILE_DISABLE"] == "0"
    assert env["TORCHINDUCTOR_CACHE_DIR"] == str(tmp_path / "custom-torch")
    assert (tmp_path / "custom-hf").is_dir()
    assert (tmp_path / "custom-torch").is_dir()


def test_runtime_check_reports_unwritable_cache_path(tmp_path) -> None:
    hf_home = tmp_path / "not-a-directory"
    hf_home.write_text("occupied", encoding="utf-8")
    env = {
        "HF_HOME": str(hf_home),
        "TORCHINDUCTOR_CACHE_DIR": str(tmp_path / "torch-cache"),
    }

    with pytest.raises(RuntimeError, match="Set HF_HOME to a writable directory"):
        validate_runtime(Settings(embedding_model="transformer"), env)
