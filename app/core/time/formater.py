from datetime import datetime


class Rfc3339Formatter:
    @staticmethod
    def format(dt: datetime) -> str:
        return dt.isoformat().replace("+00:00", "Z")
