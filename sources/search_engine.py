import asyncio
import random
from backend.core.models import WebSearchHit
from backend.core.network_utils import get_random_user_agent
from typing import List

async def collect_search_engine_data(target: str) -> List[WebSearchHit]:
    """Simulates advanced Google Dorking and search volume analysis."""
    user_agent = get_random_user_agent()

    await asyncio.sleep(random.uniform(0.8, 1.4)) 
    
    results: List[WebSearchHit] = []

    if any(token in target.lower() for token in ("dev", "admin", "backup", "staging")):
        dorks = ["filetype:pdf password list", "intitle:index of /backup", "filetype:env secret"]
        results.append(WebSearchHit(
            source="Google Dorking (Simulated)",
            result_type="Sensitive File Exposure",
            data=random.sample(dorks, k=1)
        ))

    results.append(WebSearchHit(
        source="General Search Volume",
        result_type="Page Count",
        data={ "pages": random.randint(10, 5000) }
    ))

    return results

async def collect_data(target: str):
    return await collect_search_engine_data(target)