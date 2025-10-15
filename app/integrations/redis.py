import os
import redis
import logging
from typing import Optional
from contextlib import suppress
from app.config import REDIS_PASSWORD, SPELLCAST_VOICES_CACHE_TTL_SECONDS

# Logger configuration
logger = logging.getLogger('cache')
logger.setLevel(logging.INFO)

DEFAULT_TTL = int(SPELLCAST_VOICES_CACHE_TTL_SECONDS or 900)

redis_client: Optional[redis.Redis] = None
 
def init_redis():
    global redis_client
    try:
        redis_client = redis.Redis(
            host= os.getenv('REDIS_HOST', 'localhost'),
            port = int(os.getenv('REDIS_PORT', 6379)),
            password=(REDIS_PASSWORD, None),
            db= 0,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        redis_client.ping()
        logger.info('Redis connection established')
    except redis.RedisError as e:
        logger.warning(f'Unabled connection: {e}')
        redis_client = None

# Cache wrappers
def set_cache(key:str, value:str, ttl: Optional[int]= None):
    if redis_client is None:
        #TODO raise Exception
        return
    try:
        redis_client.set(key, value, ex=ttl or DEFAULT_TTL)
    except redis.RedisError as e:
        logger.warning(f'Could not save {key} to cache: {e}')

def get_cache(key:str) -> Optional[str]:
    if redis_client is None:
        return None
    try:   
        value = redis_client.get(key)
        return value.decode() if value else None
    except redis.RedisError as e:
        logger.warning(f'Could not retrieve {key} from cache: {e}')

def delete_cache(key: str):
    if redis_client is None:
        return
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        logger.warning(f'Could not delete {key} from cache: {e}')

def keys_cache(pattern:str):
    if redis_client is None:
        return []
    try:
        return [k.decode('utf-8') for k in redis_client.keys(pattern)]
    except redis.RedisError as e:
        logger.warning(f'Could not list keys with pattern {pattern}: {e}')
        return []