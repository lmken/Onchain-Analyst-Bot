import csv
import datetime as dt
import json
from pathlib import Path

from onchain import hl, timeutil

FIX = Path(__file__).resolve().parents[1] / "fixtures"
DAY = dt.date(2026, 10, 15)


def rows():
    return list(csv.DictReader(open(FIX / "builder_day_truncated.csv")))


def test_coverage_detects_truncation():
    c = hl.coverage(rows())
    assert c["feed_hours"] == 4
    assert c["last_feed_time"] == "2026-10-15T12:10:43Z"
    assert c["truncated"] is True


def test_feed_decode_roundtrip(monkeypatch, tmp_home):
    import lz4.frame
    blob = lz4.frame.compress((FIX / "builder_day_truncated.csv").read_bytes())
    monkeypatch.setattr(hl.http, "get_bytes", lambda url, **kw: blob)
    r = hl.feed_rows("0xABC", DAY)
    assert len(r) == 4 and r[0]["coin"] == "BTC"
    # cached raw file is reused
    monkeypatch.setattr(hl.http, "get_bytes", lambda url, **kw: (_ for _ in ()).throw(AssertionError("refetch")))
    assert len(hl.feed_rows("0xabc", DAY)) == 4


def test_feed_403_means_no_file(monkeypatch):
    def boom(url, **kw):
        raise hl.http.HTTPError(403, url)
    monkeypatch.setattr(hl.http, "get_bytes", boom)
    assert hl.feed_rows("0xabc", DAY) is None


def _sqd_stream(*a, **k):
    for line in (FIX / "sqd_tail.jsonl").read_text().splitlines():
        o = json.loads(line)
        for f in o.get("fills", []):
            yield o["header"]["number"], o["header"]["timestamp"], f


def test_gapfill_tail_no_double_count(monkeypatch):
    s_ms, e_ms = timeutil.day_bounds_ms(DAY)
    monkeypatch.setattr(hl, "feed_rows", lambda a, d: rows())
    monkeypatch.setattr(hl.sqd, "block_at_or_after", lambda ts, hi=None: 100 if ts < e_ms else 300)
    calls = []

    def stream(b0, b1, builders=None, **k):
        calls.append((b0, b1, builders))
        # shift fixture times into this day's tail: one fill equal to last feed second (must be dropped),
        # two after it, one HYPE-fee fill
        base = hl._iso_to_ms("2026-10-15T12:10:43Z")
        times = [base + 500, base + 1000, base + 3_600_000, base + 3_600_001]
        i = 0
        for n, ts, f in _sqd_stream():
            f = dict(f); f["time"] = times[i]; i += 1
            yield n, ts, f
    monkeypatch.setattr(hl.sqd, "stream", stream)
    d = hl.builder_day("0xabc", DAY)
    assert d["status"] == "gapfilled"
    assert d["feed_rows"] == 4 and d["sqd_rows"] == 3          # same-second fill dropped
    assert round(d["fee_usd"], 6) == round(0.5 + 2.0 + 0.4 + 0.1 + 0.3 + 1.0, 6)
    assert d["fee_other"] == {"HYPE": 0.2}
    assert round(d["volume"]) == 1000 + 4000 + 4000 + 1000 + 1000 + 2000 + 400
    assert round(d["taker_volume"]) == 1000 + 4000 + 1000 + 1000 + 2000
    assert set(d["users"]) == {"0xaaa", "0xbbb", "0xddd", "0xeee", "0xfff"}
    assert calls and calls[0][2] == ["0xabc"]


def test_sqd_failure_labels_partial(monkeypatch):
    monkeypatch.setattr(hl, "feed_rows", lambda a, d: rows())

    def fail(*a, **k):
        raise hl.http.HTTPError(529, "sqd", "overloaded")
    monkeypatch.setattr(hl.sqd, "block_at_or_after", fail)
    d = hl.builder_day("0xabc", DAY)
    assert d["status"] == "partial" and "529" in d["sqd_error"]
    assert d["gap_hours"] > 11


def test_complete_day_needs_no_sqd(monkeypatch):
    full = rows() + [dict(rows()[0], time=f"2026-10-15T{h:02d}:30:00Z") for h in range(24)]
    monkeypatch.setattr(hl, "feed_rows", lambda a, d: full)
    monkeypatch.setattr(hl.sqd, "block_at_or_after", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no sqd")))
    d = hl.builder_day("0xabc", DAY)
    assert d["status"] == "complete" and d["sqd_rows"] == 0


def test_internal_gap_on_busy_day(monkeypatch):
    busy = [dict(rows()[0], time=f"2026-10-15T{h:02d}:{m:02d}:00Z") for h in range(24) if h != 7 for m in range(30)]
    monkeypatch.setattr(hl, "feed_rows", lambda a, d: busy)
    seen = []
    monkeypatch.setattr(hl.sqd, "block_at_or_after", lambda ts, hi=None: seen.append(ts) or len(seen))
    monkeypatch.setattr(hl.sqd, "stream", lambda *a, **k: iter(()))
    d = hl.builder_day("0xabc", DAY)
    s_ms, _ = timeutil.day_bounds_ms(DAY)
    assert d["status"] == "gapfilled" and d["gap_hours"] == 1.0
    assert seen[0] == s_ms + 7 * 3_600_000


def test_missing_feed_whole_day_from_sqd(monkeypatch):
    monkeypatch.setattr(hl, "feed_rows", lambda a, d: None)
    monkeypatch.setattr(hl.sqd, "block_at_or_after", lambda ts, hi=None: 1 if ts < timeutil.day_bounds_ms(DAY)[1] else 9)
    monkeypatch.setattr(hl.sqd, "stream", lambda *a, **k: iter(()))
    assert hl.builder_day("0xabc", DAY)["status"] == "missing_feed_sqd"
    assert hl.builder_day("0xabc", DAY, gapfill=False)["status"] in ("missing", "missing_feed_sqd")
