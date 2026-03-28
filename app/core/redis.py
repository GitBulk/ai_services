import redis

from app.core.settings import settings


def get_redis_client():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)


redis_client = get_redis_client()
