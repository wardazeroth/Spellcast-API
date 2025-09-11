import os
import redis
import logging
from typing import Optional
from contextlib import suppress

#Configuración de logging
logger = logging.getLogger('cache')
logger.setLevel(logging.INFO)

DEFAULT_TTL = int(os.getenv('SPELLCAST_VOICES_CACHE_TTL_SECONDS', 900))

redis_client: Optional[redis.Redis] = None

def init_redis():
    global redis_client
    try:
        redis_client = redis.Redis(
            host= os.getenv('REDIS_HOST', 'localhost'),
            port = int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None),
            db= 0,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        redis_client.ping()
        logger.info('COnexión a Redis establecida')
    except redis.RedisError as e:
        logger.warning(f'Redis no disponible: {e}')
        redis_client = None

#Wrappers de caché
def cache_set(key:str, value:str, ttl: Optional[int]= None):
    if redis_client is None:
        #TODO raise Exception
        return
    try:
        redis_client.set(key, value, ex=ttl or DEFAULT_TTL)
    except redis.RedisError as e:
        logger.warning(f'No se pudo guardar en caché {key}: {e}')

def cache_get(key:str) -> Optional[str]:
    if redis_client is None:
        return None
    try:   
        value = redis_client.get(key)
        return value.decode() if value else None
    except redis.RedisError as e:
        logger.warning(f'No se pudo obtener{key} de la caché: {e}')

def cache_delete(key: str):
    if redis_client is None:
        return
    try:
        redis_client.delete(key)
    except redis.RedisError as e:
        logger.warning(f'No se pudo borrar {key} de la caché: {e}')

def cache_keys(pattern:str):
    if redis_client is None:
        return []
    try:
        return [k.decode('utf-8') for k in redis_client.keys(pattern)]
    except redis.RedisError as e:
        logger.warning(f'No se pudo listar claves con patrón {pattern}: {e}')
        return []


