from enum import Enum


class CacheType(str, Enum):
    STRING = "string"
    HASH = "hash"  # Object → Redis Hash (tốt cho user info, partial update)
    LIST = "list"  # Danh sách có thứ tự
    SET = "set"  # Tập hợp unique
    SORTED_SET = "sorted_set"  # Xếp hạng, leaderboard
    VECTOR = "vector"
