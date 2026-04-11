from app.core.cache_decorator.cache_type import CacheType
from app.core.cache_decorator.hash_strategy import HashStrategy
from app.core.cache_decorator.list_strategy import ListStrategy
from app.core.cache_decorator.set_strategy import SetStrategy
from app.core.cache_decorator.sorted_set_strategy import SortedSetStrategy
from app.core.cache_decorator.strategy import Strategy
from app.core.cache_decorator.string_strategy import StringStrategy
from app.core.cache_decorator.vector_strategy import VectorStrategy

CACHE_STRATEGIES: dict[CacheType, Strategy] = {
    CacheType.STRING: StringStrategy(),
    CacheType.HASH: HashStrategy(),
    CacheType.LIST: ListStrategy(),
    CacheType.SET: SetStrategy(),
    CacheType.SORTED_SET: SortedSetStrategy(),
    CacheType.VECTOR: VectorStrategy(),
}
