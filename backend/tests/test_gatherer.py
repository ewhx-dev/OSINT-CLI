import asyncio
import json
import importlib
import types
import pytest
from backend.core import gatherer
from backend.core.models import DomainInfo

pytestmark = pytest.mark.asyncio

async def test_run_osint_normalization(monkeypatch):
    async def domain_collect(target):
        return DomainInfo(is_registered=True, owner_simulated="Acme Inc", expiration_date="2030-01-01")

    async def social_collect(target):
        return [{"platform": "GitHub", "url_found": "https://github.com/test", "status": "FOUND"}]

    async def vuln_collect(target):
        return [{"source": "NVD", "cve_id": "CVE-2025-0001", "severity": "HIGH", "description": "Example"}]

    async def web_collect(target):
        return [{"source": "Bing", "result_type": "WebPage", "data": {"name": "X", "url": "http://x", "snippet": "s"}}]

    stub_map = {
        'sources.domain_checker': types.SimpleNamespace(collect_data=domain_collect),
        'sources.social_media': types.SimpleNamespace(collect_data=social_collect),
        'sources.vulnerability_db': types.SimpleNamespace(collect_data=vuln_collect),
        'sources.search_engine': types.SimpleNamespace(collect_data=web_collect),
        'sources.deep_search': types.SimpleNamespace(collect_data=lambda t: []),
    }

    def fake_import(name):
        return stub_map[name]

    monkeypatch.setattr(gatherer, "get_from_cache", lambda k: None)
    monkeypatch.setattr(gatherer, "set_to_cache", lambda k, v, ttl_seconds=3600: None)
    monkeypatch.setattr(importlib, "import_module", fake_import)

    monkeypatch.setattr(gatherer, "SOURCE_MODULES", list(stub_map.keys()))

    report = await gatherer.run_osint_analysis("example")

    assert report.target == "example"
    assert report.domain_results is not None
    assert len(report.social_media_hits) == 1
    assert len(report.vulnerability_hits) == 1
    assert len(report.web_search_data) == 1

async def test_run_osint_cache_hit(monkeypatch):
    sample = {
        "target": "cached",
        "timestamp": "2025-01-01T00:00:00Z",
        "summary": "Cached report",
        "is_cached": True,
        "domain_results": None,
        "social_media_hits": [],
        "vulnerability_hits": [],
        "web_search_data": [],
    }
    monkeypatch.setattr(gatherer, "get_from_cache", lambda k: json.dumps(sample))
    monkeypatch.setattr(gatherer, "set_to_cache", lambda k, v, ttl_seconds=3600: None)

    report = await gatherer.run_osint_analysis("cached")
    assert report.is_cached is True
    assert report.target == "cached"
    assert report.summary == "Cached report"