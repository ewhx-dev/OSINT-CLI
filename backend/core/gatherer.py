import asyncio
import importlib
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from .models import DigitalFootprintReport, DomainInfo, SocialMediaHits, VulnerabilityHit, WebSearchHit
from .network_utils import get_from_cache, set_to_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOURCE_MODULES = [
    'sources.domain_checker',
    'sources.social_media',
    'sources.vulnerability_db',
    'sources.search_engine',
    'sources.deep_search',   
]

async def _maybe_awaitable(obj):
    if asyncio.iscoroutine(obj):
        return await obj
    return obj

async def run_osint_analysis(target: str) -> DigitalFootprintReport:
    """
    Executes the OSINT analysis with caching and concurrent source execution.
    Normalizes results coming from each module (either a single model or a list).
    """
    cache_key = f"report:{target}"

    cached_report_json = get_from_cache(cache_key)
    if cached_report_json:
        try:
            report_data = json.loads(cached_report_json)
            report_data['is_cached'] = True
            report_data['timestamp'] = datetime.utcnow().isoformat() + "Z (Cached)"
            logger.info("Cache hit for target: %s", target)
            return DigitalFootprintReport(**report_data)
        except Exception:
            logger.warning("Corrupt cache entry for %s, regenerating.", target)

    tasks = []
    for module_path in SOURCE_MODULES:
        try:
            module = importlib.import_module(module_path)
            collect = getattr(module, "collect_data", None)
            if collect is None:
                logger.warning("Module %s has no collect_data function, skipping.", module_path)
                continue
            tasks.append(asyncio.create_task(_maybe_awaitable(collect(target))))
        except Exception as e:
            logger.error("Could not load module %s: %s", module_path, e)

    if not tasks:
        raise RuntimeError("No data sources available to perform analysis.")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_report_data: Dict[str, Any] = {
        "domain_results": None,
        "social_media_hits": [],
        "vulnerability_hits": [],
        "web_search_data": [],
    }

    for result in results:
        if isinstance(result, Exception):
            logger.error("Source task error: %s", result)
            continue

        if isinstance(result, DomainInfo):
            final_report_data['domain_results'] = result
            continue

        if isinstance(result, list):
            if len(result) > 0 and (isinstance(result[0], SocialMediaHits) or (isinstance(result[0], dict) and 'platform' in result[0])):
                parsed = []
                for item in result:
                    if isinstance(item, SocialMediaHits):
                        parsed.append(item)
                    else:
                        try:
                            parsed.append(SocialMediaHits.parse_obj(item))
                        except Exception:
                            logger.debug("Skipping invalid social media item: %s", item)
                final_report_data['social_media_hits'].extend(parsed)
                continue

            if len(result) > 0 and (isinstance(result[0], VulnerabilityHit) or (isinstance(result[0], dict) and 'source' in result[0] and 'severity' in result[0])):
                parsed = []
                for item in result:
                    if isinstance(item, VulnerabilityHit):
                        parsed.append(item)
                    else:
                        try:
                            parsed.append(VulnerabilityHit.parse_obj(item))
                        except Exception:
                            logger.debug("Skipping invalid vulnerability item: %s", item)
                final_report_data['vulnerability_hits'].extend(parsed)
                continue

            if len(result) > 0 and (isinstance(result[0], WebSearchHit) or (isinstance(result[0], dict) and 'source' in result[0] and 'result_type' in result[0])):
                parsed = []
                for item in result:
                    if isinstance(item, WebSearchHit):
                        parsed.append(item)
                    else:
                        try:
                            parsed.append(WebSearchHit.parse_obj(item))
                        except Exception:
                            logger.debug("Skipping invalid web search item: %s", item)
                final_report_data['web_search_data'].extend(parsed)
                continue

    found_profiles = len([h for h in final_report_data['social_media_hits'] if getattr(h, "status", "") == "FOUND"])
    vulns_found = len(final_report_data['vulnerability_hits'])

    summary = f"Analysis complete. Found {found_profiles} social profiles and {vulns_found} potential vulnerabilities."

    report = DigitalFootprintReport(
        target=target,
        timestamp=datetime.utcnow().isoformat() + "Z (Live)",
        summary=summary,
        is_cached=False,
        **final_report_data
    )

    try:
        set_to_cache(cache_key, report.model_dump_json(), ttl_seconds=3600)
    except Exception:
        logger.debug("Failed to set cache for %s", cache_key)

    return report