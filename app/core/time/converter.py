from datetime import datetime, timezone


class TimeConverter:
    @staticmethod
    def to_epoch_ms(dt: datetime) -> int:
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")

        return int(dt.timestamp() * 1000)

    @staticmethod
    def from_epoch_ms(ms: int) -> datetime:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
