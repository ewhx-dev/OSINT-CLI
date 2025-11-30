import random
from typing import Optional, List

try:
    import redis
    REDIS_AVAILABLE = True
except Exception:
    redis = None
    REDIS_AVAILABLE = False

REDIS_CLIENT = None
if REDIS_AVAILABLE:
    try:
        REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        # quick ping to validate
        REDIS_CLIENT.ping()
    except Exception:
        REDIS_CLIENT = None

USER_AGENTS_KEY = "osint:user_agents"

FALLBACK_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "curl/7.85.0",
    "Mozilla/5.0 (compatible; OSINT-PRO/1.0)",
]

def _seed_redis_user_agents():
    if not REDIS_CLIENT:
        return
    try:
        if not REDIS_CLIENT.exists(USER_AGENTS_KEY):
            REDIS_CLIENT.sadd(USER_AGENTS_KEY, *FALLBACK_USER_AGENTS)
            REDIS_CLIENT.expire(USER_AGENTS_KEY, 3600)
    except Exception:

        pass

def get_random_user_agent() -> str:
    """
    Retrieves a random User-Agent from Redis pool or uses a local fallback pool.
    """
    try:

        if REDIS_CLIENT:
            _seed_redis_user_agents()
            try:
                agent = REDIS_CLIENT.srandmember(USER_AGENTS_KEY)
                if agent:
                    return agent
            except Exception:

                pass
    
        return random.choice(FALLBACK_USER_AGENTS)
    except Exception:
        return "Mozilla/5.0 (compatible; OSINT-PRO/1.0)"

def get_from_cache(key: str) -> Optional[str]:
    """Retrieves a value from the Redis cache. Returns None on any failure or miss."""
    if not REDIS_CLIENT:
        return None
    try:
        return REDIS_CLIENT.get(key)
    except Exception:
        return None

def set_to_cache(key: str, value: str, ttl_seconds: int = 3600):
    """Saves a value to the Redis cache with a Time-To-Live. Silently no-ops on failure."""
    if not REDIS_CLIENT:
        return
    try:
        REDIS_CLIENT.setex(key, ttl_seconds, value)
    except Exception:
        pass