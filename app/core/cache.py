import functools
import json

from app.core.redis import redis_client


def cache(key_builder, ttl=300):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = key_builder(*args, **kwargs)
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)

            result = func(*args, **kwargs)

            redis_client.set(key, json.dumps(result), ex=ttl)
            return result

        return wrapper

    return decorator


def invalidate(key: str):
    redis_client.delete(key)
