import datetime as dt
import io
import json
import urllib.error

import pytest

from onchain import cli, http, output, registry, timeutil


def test_parse_window_complete_days():
    now = dt.datetime(2026, 10, 17, 21, 0, tzinfo=dt.timezone.utc)
    assert timeutil.parse_window("30d", now) == (dt.date(2026, 9, 17), dt.date(2026, 10, 16))
    assert timeutil.parse_window("2026-10-01:2026-10-03") == (dt.date(2026, 10, 1), dt.date(2026, 10, 3))
    with pytest.raises(ValueError):
        timeutil.parse_window("yesterday")


def test_registry_seed():
    apps = registry.load()
    assert registry.validate(apps) == []
    verified = [b["address"] for a in apps for b in (a.get("hyperliquid") or {}).get("builders", []) if b.get("verified")]
    assert len(verified) == 11
    assert registry.hl_builders(registry.find("fomo")) == ["0x2a2b6b093a9813fbd8cddae800c3d17d46460d17",
                                                           "0xb838e4d1c8bcf71fa8e63299d5aa3258c83d6adb"]
    assert registry.find("0xb84168cf3be63c6b8dad05ff5d755e97432ff80b")["id"] == "phantom"
    assert registry.find("betmoar")["polymarket"]["builder_codes"][0].startswith("0xceeb")


def test_registry_validate_catches_errors():
    bad = [{"id": "X", "name": "x", "category": "wallet", "hyperliquid": {"builders": [{"address": "0xABC"}]}}]
    errs = registry.validate(bad)
    assert any("bad id" in e for e in errs) and any("bad HL address" in e for e in errs)


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_http_retries_overloaded_body(monkeypatch):
    calls = []

    def fake(req, timeout=0):
        calls.append(1)
        if len(calls) == 1:
            return _Resp(b'{"error":{"type":"rate_limit_error","code":"overloaded"}}')
        return _Resp(b'{"ok":1}')
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)
    assert http.post_json("https://portal.sqd.dev/x", {"a": 1}) == {"ok": 1}
    assert len(calls) == 2


def test_http_no_retry_on_403(monkeypatch):
    def fake(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, io.BytesIO(b"no"))
    monkeypatch.setattr(http.urllib.request, "urlopen", fake)
    with pytest.raises(http.HTTPError) as e:
        http.get_bytes("https://stats-data.hyperliquid.xyz/x")
    assert e.value.status == 403


def test_output_formats():
    rows = [{"a": 1, "b": 2.5}, {"a": 3, "b": None}]
    buf = io.StringIO()
    output.render(rows, "csv", out=buf)
    assert buf.getvalue().splitlines()[0] == "a,b"
    buf = io.StringIO()
    output.render(rows, "json", {"sources": "x"}, out=buf)
    assert json.loads(buf.getvalue())["meta"]["sources"] == "x"
    buf = io.StringIO()
    output.render(rows, "table", {"sources": "x"}, out=buf)
    assert "sources: x" in buf.getvalue()


def test_cli_offline_commands(capsys):
    assert cli.main(["pm", "fee", "--shares", "100", "--price", "0.5", "--category", "crypto"]) == 0
    assert "1.75" in capsys.readouterr().out
    assert cli.main(["registry", "validate"]) == 0
    assert cli.main(["keys", "status"]) == 0
    assert "MVP needs no keys" in capsys.readouterr().out


def test_keys_never_print_values(monkeypatch, capsys):
    monkeypatch.setenv("ONCHAIN_TEST_KEY", "supersecretvalue123")
    cli.main(["keys", "status"])
    out = capsys.readouterr().out
    assert "ONCHAIN_TEST_KEY" in out and "supersecretvalue123" not in out
