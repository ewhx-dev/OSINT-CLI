import asyncio
from backend.core.models import DomainInfo
from datetime import datetime

async def collect_domain_data(target_domain: str) -> DomainInfo:
    """Simulates an asynchronous WHOIS lookup."""
    await asyncio.sleep(0.5) 

    if "." not in target_domain:
        return DomainInfo(is_registered=False)

    if "private" in target_domain.lower():
        return DomainInfo(is_registered=True, owner_simulated="Private Registration", expiration_date="2027-01-01")
    else:
        return DomainInfo(
            is_registered=True,
            owner_simulated=f"Simulated Entity for {target_domain}",
            expiration_date=(datetime.now().year + 2).strftime("%Y-%m-%d")
        )

async def collect_data(target: str):
    return await collect_domain_data(target)