from datetime import datetime, timezone


class UtcClock:
    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def now_epoch_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)
