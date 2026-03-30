from datetime import datetime

from app.core.time.clock import UtcClock
from app.core.time.converter import TimeConverter
from app.core.time.formater import Rfc3339Formatter
from app.core.time.models import TimePayload


class DateTimeService:
    @staticmethod
    def now() -> TimePayload:
        dt = UtcClock.now()

        return TimePayload(epoch_ms=TimeConverter.to_epoch_ms(dt), rfc3339=Rfc3339Formatter.format(dt), current=dt)

    @staticmethod
    def now_dt() -> datetime:
        return UtcClock.now()

    @staticmethod
    def now_epoch_ms() -> int:
        return UtcClock.now_epoch_ms()

    @staticmethod
    def now_rfc3339() -> str:
        return Rfc3339Formatter.format(UtcClock.now())
