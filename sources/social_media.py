import asyncio
import random
from backend.core.models import SocialMediaHits
from typing import List

PLATFORM_DOMAINS = {
    "Twitter/X": "twitter.com",
    "LinkedIn": "linkedin.com/in",
    "GitHub": "github.com",
    "Instagram": "instagram.com",
    "Reddit": "reddit.com/user",
}

async def collect_social_data(target_username: str) -> List[SocialMediaHits]:
    """Simulates username checking across various platforms."""
    
    platforms = list(PLATFORM_DOMAINS.keys())
    results: List[SocialMediaHits] = []

    for platform in platforms:
        await asyncio.sleep(random.uniform(0.05, 0.2))
        
        is_found = random.choices([True, False], weights=[65, 35])[0]
        
        if is_found and len(target_username) > 3:
            url = f"https://{PLATFORM_DOMAINS[platform]}/{target_username}"
            results.append(SocialMediaHits(
                platform=platform,
                url_found=url,
                status="FOUND"
            ))
        else:
            results.append(SocialMediaHits(
                platform=platform,
                url_found=None,
                status="NOT_FOUND_OR_PRIVATE"
            ))
    
    return results

async def collect_data(target: str):
    return await collect_social_data(target)