from __future__ import annotations

from pathlib import Path

from doc_forge.devtools import embedding_models, repo_clean


class _FakeSentenceTransformerModel:
    def __init__(self) -> None:
        self.saved_paths: list[str] = []

    def save(self, path: str) -> None:
        self.saved_paths.append(path)
        Path(path, "model.txt").write_text("fake model", encoding="utf-8")


def test_model_directory_name_uses_model_basename() -> None:
    assert (
        embedding_models.model_directory_name("sentence-transformers/all-MiniLM-L6-v2")
        == "all-MiniLM-L6-v2"
    )
    assert embedding_models.model_directory_name("example/model name") == "model-name"


def test_prepare_sentence_transformer_model_saves_under_data_models_shape(tmp_path) -> None:
    fake_model = _FakeSentenceTransformerModel()
    seen_models: list[str] = []

    def loader(model_id: str) -> _FakeSentenceTransformerModel:
        seen_models.append(model_id)
        return fake_model

    path = embedding_models.prepare_sentence_transformer_model(
        "sentence-transformers/all-MiniLM-L6-v2",
        output_root=tmp_path / "data" / "models",
        loader=loader,
    )

    assert path == tmp_path / "data" / "models" / "all-MiniLM-L6-v2"
    assert seen_models == ["sentence-transformers/all-MiniLM-L6-v2"]
    assert fake_model.saved_paths == [str(path)]
    assert (path / "model.txt").read_text(encoding="utf-8") == "fake model"


def test_repo_clean_model_cache_targets_are_opt_in(tmp_path) -> None:
    (tmp_path / "data" / "models").mkdir(parents=True)
    (tmp_path / "data" / "huggingface").mkdir(parents=True)
    (tmp_path / ".pytest_cache").mkdir()

    default_targets = repo_clean.build_cleanup_plan(tmp_path)
    assert [target.relative_path for target in default_targets] == [".pytest_cache"]

    model_targets = repo_clean.build_cleanup_plan(tmp_path, include_model_cache=True)
    assert [target.relative_path for target in model_targets] == [
        ".pytest_cache",
        "data/huggingface",
        "data/models",
    ]


def test_compose_exposes_local_model_runtime_env() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "HF_HOME: ${HF_HOME:-/artifacts/huggingface}" in compose
    assert "HF_HUB_OFFLINE: ${HF_HUB_OFFLINE:-0}" in compose
    assert "TRANSFORMERS_OFFLINE: ${TRANSFORMERS_OFFLINE:-0}" in compose
    assert "DOC_FORGE_EMBEDDING_MODEL: ${DOC_FORGE_EMBEDDING_MODEL:-deterministic}" in compose
