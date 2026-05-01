from __future__ import annotations

from doc_forge.devtools import api_discovery


def test_explicit_api_base_url_wins() -> None:
    candidates = api_discovery.candidate_base_urls(
        {
            "DOC_FORGE_API_BASE_URL": "http://example.test:9000/",
            "PORT": "8000",
        }
    )

    assert candidates == [
        api_discovery.ApiBaseUrlResolution(
            base_url="http://example.test:9000",
            source="DOC_FORGE_API_BASE_URL",
            checked=False,
        )
    ]


def test_candidate_urls_include_localhost_and_host_gateway() -> None:
    candidates = api_discovery.candidate_base_urls({"PORT": "18081"})

    assert [candidate.base_url for candidate in candidates] == [
        "http://127.0.0.1:18081",
        "http://host.docker.internal:18081",
        "http://172.17.0.1:18081",
    ]


def test_resolve_uses_first_reachable_candidate(monkeypatch) -> None:
    attempts: list[str] = []

    def fake_probe(base_url: str, *, timeout_seconds: float = 0.5) -> bool:
        attempts.append(base_url)
        return base_url == "http://host.docker.internal:18081"

    monkeypatch.setattr(api_discovery, "probe_readyz", fake_probe)

    resolution = api_discovery.resolve_api_base_url({"PORT": "18081"})

    assert resolution == api_discovery.ApiBaseUrlResolution(
        base_url="http://host.docker.internal:18081",
        source="host:host.docker.internal",
        checked=True,
    )
    assert attempts == ["http://127.0.0.1:18081", "http://host.docker.internal:18081"]


def test_custom_discovery_hosts_are_supported() -> None:
    candidates = api_discovery.candidate_base_urls(
        {
            "DOC_FORGE_API_DISCOVERY_HOSTS": "docforge-api,api",
            "DOC_FORGE_API_PORT": "8000",
        }
    )

    assert [candidate.base_url for candidate in candidates] == [
        "http://docforge-api:8000",
        "http://api:8000",
    ]
