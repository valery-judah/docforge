from __future__ import annotations

from pathlib import Path

import pytest

from doc_forge.app.runtime_checks import validate_runtime
from doc_forge.app.settings import Settings


def test_runtime_check_skips_transformer_cache_env_for_deterministic_model() -> None:
    validate_runtime(Settings(embedding_model="deterministic", _env_file=None), {})


def test_runtime_check_uses_default_transformer_cache_paths(tmp_path: Path) -> None:
    env: dict[str, str] = {}
    settings = Settings(
        embedding_model="transformer",
        artifact_root=tmp_path / "artifacts",
        _env_file=None,
    )

    validate_runtime(settings, env)

    assert env["HF_HOME"] == str(tmp_path / "artifacts" / "huggingface")
    assert env["TORCHINDUCTOR_CACHE_DIR"] == str(tmp_path / "artifacts" / "torchinductor-cache")
    assert (tmp_path / "artifacts" / "huggingface").is_dir()
    assert (tmp_path / "artifacts" / "torchinductor-cache").is_dir()


def test_runtime_check_sets_transformer_env_and_creates_dirs(tmp_path: Path) -> None:
    env = {
        "TORCH_COMPILE_DISABLE": "0",
    }
    settings = Settings(
        embedding_model="transformer",
        hf_home=tmp_path / "custom-hf",
        torchinductor_cache_dir=tmp_path / "custom-torch",
        hf_hub_offline=True,
        transformers_offline=False,
        _env_file=None,
    )

    validate_runtime(settings, env)

    assert env["HF_HOME"] == str(tmp_path / "custom-hf")
    assert env["TORCH_COMPILE_DISABLE"] == "0"
    assert env["TORCHINDUCTOR_CACHE_DIR"] == str(tmp_path / "custom-torch")
    assert env["HF_HUB_OFFLINE"] == "1"
    assert env["TRANSFORMERS_OFFLINE"] == "0"
    assert (tmp_path / "custom-hf").is_dir()
    assert (tmp_path / "custom-torch").is_dir()


def test_runtime_check_overwrites_third_party_env_from_settings(tmp_path: Path) -> None:
    env = {
        "HF_HOME": str(tmp_path / "old-hf"),
        "TORCHINDUCTOR_CACHE_DIR": str(tmp_path / "old-torch"),
    }
    settings = Settings(
        embedding_model="transformer",
        hf_home=tmp_path / "configured-hf",
        torchinductor_cache_dir=tmp_path / "configured-torch",
        _env_file=None,
    )

    validate_runtime(settings, env)

    assert env["HF_HOME"] == str(tmp_path / "configured-hf")
    assert env["TORCHINDUCTOR_CACHE_DIR"] == str(tmp_path / "configured-torch")


def test_runtime_check_reports_unwritable_cache_path(tmp_path: Path) -> None:
    hf_home = tmp_path / "not-a-directory"
    hf_home.write_text("occupied", encoding="utf-8")
    settings = Settings(
        embedding_model="transformer",
        hf_home=hf_home,
        torchinductor_cache_dir=tmp_path / "torch-cache",
        _env_file=None,
    )

    with pytest.raises(RuntimeError, match="Set DOC_FORGE_HF_HOME to a writable directory"):
        validate_runtime(settings, {})
