"""
Safe wrappers for external API connectors.
Use environment variables to provide credentials (BING_API_KEY, GITHUB_TOKEN).
These functions return normalized Pydantic-model compatible objects and are intended
to be used by sources (e.g. deep_search).
"""
import os
from typing import List
import httpx
from backend.core.models import WebSearchHit, SocialMediaHits

BING_API_KEY = os.getenv("BING_API_KEY")
BING_ENDPOINT = os.getenv("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


async def bing_search(query: str, limit: int = 5, timeout_seconds: float = 12.0) -> List[WebSearchHit]:
    if not BING_API_KEY:
        return []
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY, "Accept": "application/json"}
    params = {"q": query, "count": str(limit), "textDecorations": "false", "textFormat": "Raw"}
    timeout = httpx.Timeout(timeout_seconds, connect=6.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(BING_ENDPOINT, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    results: List[WebSearchHit] = []
    for item in data.get("webPages", {}).get("value", [])[:limit]:
        results.append(WebSearchHit(
            source="Bing Web Search",
            result_type="WebPage",
            data={"name": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet")}
        ))
    return results


async def github_user_search(query: str, per_page: int = 5, timeout_seconds: float = 10.0) -> List[SocialMediaHits]:
    if not GITHUB_TOKEN:
        return []
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    params = {"q": f"{query} in:login", "per_page": str(per_page)}
    url = "https://api.github.com/search/users"
    timeout = httpx.Timeout(timeout_seconds, connect=6.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    results: List[SocialMediaHits] = []
    for u in data.get("items", [])[:per_page]:
        results.append(SocialMediaHits(platform="GitHub", url_found=u.get("html_url"), status="FOUND"))
    return results