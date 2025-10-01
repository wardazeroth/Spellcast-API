from app.redis_client import redis_client, DEFAULT_TTL, cache_get, cache_set

def get_voice_cache(region):
    key = f"voices:{region}"
    return cache_get(key)

def set_voice_cache(region, payload):
    key = f"voices:{region}"
    cache_set(key, payload, ttl=DEFAULT_TTL)
