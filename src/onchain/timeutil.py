"""UTC day windows. All maths is in complete UTC days; labels may be shown in local time."""
from __future__ import annotations

import datetime as dt
import re

UTC = dt.timezone.utc


def utc_now() -> dt.datetime:
    return dt.datetime.now(UTC)


def last_complete_day(now: dt.datetime | None = None) -> dt.date:
    now = now or utc_now()
    return (now - dt.timedelta(days=1)).date()


def parse_window(w: str, now: dt.datetime | None = None) -> tuple[dt.date, dt.date]:
    """'30d' → last 30 complete UTC days; 'YYYY-MM-DD:YYYY-MM-DD' inclusive."""
    w = w.strip()
    m = re.fullmatch(r"(\d+)d", w)
    if m:
        end = last_complete_day(now)
        return end - dt.timedelta(days=int(m.group(1)) - 1), end
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})", w)
    if m:
        a, b = dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2))
        if b < a:
            raise ValueError("window end before start")
        return a, b
    raise ValueError(f"bad window {w!r}; use 7d/30d/90d or YYYY-MM-DD:YYYY-MM-DD")


def days(a: dt.date, b: dt.date):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def day_bounds_ms(d: dt.date) -> tuple[int, int]:
    start = dt.datetime(d.year, d.month, d.day, tzinfo=UTC)
    return int(start.timestamp() * 1000), int((start + dt.timedelta(days=1)).timestamp() * 1000)


def iso_week(d: dt.date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def ms_to_iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
