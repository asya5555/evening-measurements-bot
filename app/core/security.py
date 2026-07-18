from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


def is_allowed_user(
    user_id: int | None,
    allowed_ids: list[int],
    username: str | None = None,
    allowed_usernames: list[str] | None = None,
) -> bool:
    if user_id is not None and user_id in set(allowed_ids):
        return True
    if username and allowed_usernames:
        return username.lower().lstrip("@") in set(allowed_usernames)
    return False


def mask_secret(value: str, visible: int = 4) -> str:
    if len(value) <= visible * 2:
        return "***"
    return f"{value[:visible]}...{value[-visible:]}"


@dataclass
class MinuteRateLimiter:
    limit: int
    _hits: dict[int, list[datetime]] = field(default_factory=lambda: defaultdict(list))

    def allow(self, user_id: int, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        cutoff = current - timedelta(minutes=1)
        hits = [hit for hit in self._hits[user_id] if hit >= cutoff]
        self._hits[user_id] = hits
        if len(hits) >= self.limit:
            return False
        hits.append(current)
        return True
