import os
import asyncio
import random
from typing import List, Dict, Any
import httpx
from backend.core.models import WebSearchHit, SocialMediaHits
from backend.core.network_utils import get_random_user_agent

BING_API_KEY = os.getenv("BING_API_KEY")          
BING_ENDPOINT = os.getenv("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")         
MAX_BING_RESULTS = int(os.getenv("MAX_BING_RESULTS", "6"))
MAX_GITHUB_USERS = int(os.getenv("MAX_GITHUB_USERS", "5"))

async def _bing_search(query: str, ua: str) -> List[WebSearchHit]:
    results: List[WebSearchHit] = []
    if not BING_API_KEY:
        return results

    headers = {
        "Ocp-Apim-Subscription-Key": BING_API_KEY,
        "User-Agent": ua,
        "Accept": "application/json",
    }
    params = {"q": query, "count": str(MAX_BING_RESULTS), "textDecorations": "false", "textFormat": "Raw"}

    timeout = httpx.Timeout(15.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(BING_ENDPOINT, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            webpages = data.get("webPages", {}).get("value", [])
            for item in webpages[:MAX_BING_RESULTS]:
                results.append(WebSearchHit(
                    source="Bing Web Search",
                    result_type="WebPage",
                    data={"name": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet")}
                ))
        except Exception as e:

            print("Bing search error:", e)

    await asyncio.sleep(0.15)
    return results

async def _github_user_search(query: str, ua: str) -> List[SocialMediaHits]:
    results: List[SocialMediaHits] = []
    if not GITHUB_TOKEN:
        return results

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": ua,
        "Accept": "application/vnd.github+json",
    }
    params = {"q": f"{query} in:login", "per_page": str(MAX_GITHUB_USERS)}
    url = "https://api.github.com/search/users"

    timeout = httpx.Timeout(12.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])[:MAX_GITHUB_USERS]
            for u in items:
                results.append(SocialMediaHits(
                    platform="GitHub",
                    url_found=u.get("html_url"),
                    status="FOUND"
                ))
        except Exception as e:
            print("GitHub user search error:", e)
    await asyncio.sleep(0.12)
    return results

async def _github_code_search(query: str, ua: str) -> List[WebSearchHit]:
    hits: List[WebSearchHit] = []
    if not GITHUB_TOKEN:
        return hits

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": ua,
        "Accept": "application/vnd.github+json",
    }

    params = {"q": f"{query} in:file", "per_page": "5"}
    url = "https://api.github.com/search/code"

    timeout = httpx.Timeout(12.0, connect=8.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", [])[:5]:
                hits.append(WebSearchHit(
                    source="GitHub Code Search",
                    result_type="CodeMatch",
                    data={"repository": item.get("repository", {}).get("full_name"), "path": item.get("path"), "html_url": item.get("html_url")}
                ))
        except Exception as e:
            print("GitHub code search error:", e)
    await asyncio.sleep(0.12)
    return hits

async def _simulated_deep_hits(target: str, ua: str) -> List[Any]:
    """
    Conservative simulated fallback used when no real API keys are configured.
    Still useful for local testing; results are clearly marked as simulated.
    """
    results: List[Any] = []

    suffixes = ["", "01", "_dev", "_admin"]
    perms = [target + s for s in suffixes][:6]
    for p in perms:
        if random.random() < 0.20:
            results.append(WebSearchHit(
                source="Simulated Deep Crawl",
                result_type="Paste Mention",
                data={"permutation": p, "snippet": f"Simulated mention of {p}", "confidence": 0.45}
            ))

    if random.random() < 0.3:
        results.append(SocialMediaHits(
            platform="GitHub",
            url_found=f"https://github.com/{target}",
            status="FOUND (SIMULATED)"
        ))
    await asyncio.sleep(0.1)
    return results

async def collect_deep_search_data(target: str) -> List:
    """
    Law‑respecting deep search source.
    - Uses Bing Web Search API (when BING_API_KEY provided) for broad web discovery.
    - Uses GitHub Search API (when GITHUB_TOKEN provided) to find users or code references.
    - Falls back to a conservative simulated mode if no keys are available.
    Notes:
      * Do not enable unauthorized scraping. Use official APIs and respect rate limits / TOS.
      * Configure BING_API_KEY and/or GITHUB_TOKEN in your environment to enable real discovery.
    """
    ua = get_random_user_agent()
    combined: List = []

    tasks = []
    if BING_API_KEY:
        tasks.append(asyncio.create_task(_bing_search(target, ua)))
    if GITHUB_TOKEN:
        tasks.append(asyncio.create_task(_github_user_search(target, ua)))
        tasks.append(asyncio.create_task(_github_code_search(target, ua)))

    if not tasks:
        simulated = await _simulated_deep_hits(target, ua)
        combined.extend(simulated)
        return combined

    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for resp in responses:
        if isinstance(resp, Exception):
            print("Deep search provider error:", resp)
            continue
        if isinstance(resp, list):
            combined.extend(resp)

    seen_urls = set()
    deduped: List = []
    for item in combined:
        if isinstance(item, WebSearchHit):
            url = None
            data = getattr(item, "data", {}) or {}
            url = data.get("url") or data.get("html_url")
            key = f"web:{url}" if url else f"web:{data.get('name', '')}"
            if key in seen_urls:
                continue
            seen_urls.add(key)
            deduped.append(item)
            
        elif isinstance(item, SocialMediaHits):
            key = f"profile:{item.url_found}"
            if key in seen_urls:
                continue
            seen_urls.add(key)
            deduped.append(item)
        else:
            deduped.append(item)

    return deduped

async def collect_data(target: str):
    return await collect_deep_search_data(target)