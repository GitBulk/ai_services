import functools
import hashlib
import inspect
import pickle
import re
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from nltk.corpus import stopwords
from redis.asyncio import Redis as AsyncRedis

from app.core.cache_decorator.cache_type import CacheType
from app.core.cache_decorator.strategy import CACHE_STRATEGIES
from app.core.redis import get_async_redis_client

P = ParamSpec("P")
R = TypeVar("R")


class CacheDecorator:
    def __init__(
        self,
        default_ttl: int = 300,
        key_prefix: str = "app:cache:",
        default_cache_type: CacheType = CacheType.STRING,
    ):
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.default_cache_type = default_cache_type

    def _make_key(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        key_pattern: str | None = None,
        normalized_params: dict | None = None,
    ) -> str:
        """Tạo key chỉ hỗ trợ {param_name} - An toàn khi code thay đổi"""
        if not key_pattern:
            return self._make_hash_key(func, args, kwargs)

        try:
            pattern = key_pattern
            if normalized_params:
                all_params = normalized_params
            else:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()  # Điền giá trị default nếu có
                all_params = bound_args.arguments  # dict: {"user_id": 123, "status": "active", ...}

            # Thay thế tất cả placeholder {param_name}
            for param_name, value in all_params.items():
                placeholder = f"{{{param_name}}}"
                if placeholder in pattern:
                    string_value = self._stringify_param(value)
                    pattern = pattern.replace(placeholder, string_value)

            # Kiểm tra còn placeholder nào không được thay thế
            if re.search(r"\{[^}]+\}", pattern):
                print(f"⚠️ Warning: Key pattern '{key_pattern}' chưa thay hết placeholder.")

            return f"{self.key_prefix}{pattern}"

        except Exception as e:
            print(f"❌ Error generating key with pattern '{key_pattern}': {e}")
            return self._make_hash_key(func, args, kwargs)

    def _stringify_param(self, value: Any) -> str:
        if isinstance(value, bytes):
            return hashlib.md5(value).hexdigest()

        if isinstance(value, str):
            if value.startswith(("http://", "https://")) or len(value) > 64:
                return hashlib.md5(value.encode()).hexdigest()

            return value

        return str(value)

    def _make_hash_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Fallback key dùng hash"""
        key_parts = [func.__module__, func.__qualname__]
        try:
            arg_str = pickle.dumps((args, frozenset(kwargs.items())))
            arg_hash = hashlib.sha256(arg_str).hexdigest()
        except Exception:
            arg_hash = hashlib.sha256(str((args, sorted(kwargs.items()))).encode()).hexdigest()

        return f"{self.key_prefix}{':'.join(key_parts)}:{arg_hash}"

    def _normalize_text_for_embedding(
        self, text: str, normalize: bool = True, remove_punct: bool = False, remove_stop: bool = False
    ) -> str:
        if not isinstance(text, str) or not normalize:
            return text

        # Bước cơ bản (luôn làm)
        normalized = text.strip()
        normalized = " ".join(normalized.split())  # collapse whitespace
        normalized = normalized.lower()

        if remove_punct:
            # Loại bỏ dấu câu, giữ chữ và số
            normalized = re.sub(r"[^\w\s]", "", normalized)

        if remove_stop:
            try:
                stop_words = set(stopwords.words("english"))
                tokens = normalized.split()
                normalized = " ".join([w for w in tokens if w not in stop_words])
            except ImportError:
                print("Warning: nltk not installed. Skip remove_stopwords.")
            except Exception:
                pass  # fallback nếu nltk chưa tải

        return normalized

    def __call__(
        self,
        ttl: int | None = None,
        cache_type: CacheType | None = None,
        key_pattern: str | None = None,
        list_max_len: int | None = None,
        sorted_set_score_field: str | None = None,
        normalize_text: bool = True,
        remove_punctuation: bool = False,
        remove_stopwords: bool = False,
    ):
        ttl = ttl or self.default_ttl
        cache_type = cache_type or self.default_cache_type

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                client: AsyncRedis = get_async_redis_client()
                # Map toàn bộ params (args + kwargs)
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # key_params dùng để tạo key, không ảnh hưởng đến kwargs truyền vào func gốc
                key_params = dict(bound_args.arguments)
                if key_pattern:
                    for name, value in key_params.items():
                        if isinstance(value, str) and not value.startswith(("http://", "https://")):
                            key_params[name] = self._normalize_text_for_embedding(
                                value, normalize_text, remove_punctuation, remove_stopwords
                            )

                # Tạo key từ các params đã được normalize (nếu có)
                cache_key = self._make_key(func, args, kwargs, key_pattern, normalized_params=key_params)

                strategy = CACHE_STRATEGIES[cache_type]

                try:
                    cached = await strategy.get(client, cache_key)
                    if cached is not None:
                        return cached
                except Exception:
                    pass

                # Thực thi hàm gốc với tham số nguyên bản (args, kwargs)
                result = await func(*args, **kwargs)

                try:
                    extra = {}
                    if list_max_len is not None:
                        extra["list_max_len"] = list_max_len
                    if sorted_set_score_field:
                        extra["sorted_set_score_field"] = sorted_set_score_field

                    await strategy.set(client, cache_key, result, ttl, **extra)
                except Exception:
                    pass

                return result

            return wrapper

        return decorator

    async def invalidate(self, func: Callable, *args, **kwargs) -> bool:
        try:
            client: AsyncRedis = get_async_redis_client()
            cache_key = self._make_key(func, args, kwargs, key_pattern=None)
            return bool(await client.delete(cache_key))
        except Exception:
            return False


cache_decorator = CacheDecorator(default_ttl=300, key_prefix="app:cache:", default_cache_type=CacheType.STRING)
