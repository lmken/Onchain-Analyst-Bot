"""Sample the inflow into one Solana SPL token account over the last N minutes (stdlib only, keyless).

Use it to VERIFY a fee-wallet product line (e.g. an app's USDC fee account) against an aggregator:
extrapolate the sampled rate and compare with the aggregator's daily figure for that chain.
It is a spot check, not a full measurement: the public RPC is rate limited and keeps limited history.

Busy fee accounts see thousands of transactions an hour, so it counts ALL signatures in the window
(cheap, 1000 per call) and fetches only an evenly spaced SAMPLE of transactions (expensive), then
estimates inflow = mean inflow per sampled tx x signature count.

usage: python solana_token_inflow.py <token_account> [minutes=30] [sample=150] [rpc=https://api.mainnet-beta.solana.com]
"""
import json, sys, time, urllib.request

ACCT = sys.argv[1]
MINUTES = float(sys.argv[2]) if len(sys.argv) > 2 else 30
SAMPLE = int(sys.argv[3]) if len(sys.argv) > 3 else 150
RPC = sys.argv[4] if len(sys.argv) > 4 else "https://api.mainnet-beta.solana.com"


def rpc(method, params, tries=6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "onchain-analyst"})
            r = json.load(urllib.request.urlopen(req, timeout=30))
            if "error" in r:  # RPC-level errors (bad params, unsupported tx version) are not retryable
                return {"__error__": r["error"]}
            return r["result"]
        except Exception as e:
            last = e
            time.sleep(2.0 * (i + 1))
    raise RuntimeError(f"{method} failed: {last}")


since = time.time() - MINUTES * 60
sigs, before = [], None
while True:
    opts = {"limit": 1000, **({"before": before} if before else {})}
    page = rpc("getSignaturesForAddress", [ACCT, opts])
    if isinstance(page, dict):
        sys.exit(f"rpc error: {page['__error__']}")
    if not page:
        break
    sigs += [s for s in page if s.get("blockTime") and s["blockTime"] >= since and not s.get("err")]
    if page[-1].get("blockTime", 0) < since:
        break
    before = page[-1]["signature"]

inflow = outflow = 0.0
n = skipped = 0
print(f"{len(sigs)} signatures in window", file=sys.stderr)
step = max(1, len(sigs) // SAMPLE)
for s in sigs[::step][:SAMPLE]:
    try:
        tx = rpc("getTransaction", [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}])
    except RuntimeError:
        skipped += 1
        continue
    if isinstance(tx, dict) and "__error__" in tx:
        skipped += 1
        print("rpc error:", tx["__error__"].get("message", "")[:120], file=sys.stderr)
        continue
    time.sleep(0.4)  # public RPC allows only a few heavy calls per second
    if not tx:
        continue
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
    if ACCT not in keys:
        continue
    idx = keys.index(ACCT)
    pre = {b["accountIndex"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in tx["meta"].get("preTokenBalances", [])}
    post = {b["accountIndex"]: float(b["uiTokenAmount"]["uiAmount"] or 0) for b in tx["meta"].get("postTokenBalances", [])}
    d = post.get(idx, 0.0) - pre.get(idx, 0.0)
    inflow += max(d, 0); outflow += max(-d, 0); n += 1

span_h = MINUTES / 60
scale = len(sigs) / n if n else 0
est = inflow * scale
print(json.dumps({"account": ACCT, "signatures": len(sigs), "sampled_txs": n, "skipped": skipped,
                  "window_minutes": MINUTES, "sample_inflow": round(inflow, 2), "sample_outflow": round(outflow, 2),
                  "mean_inflow_per_tx": round(inflow / n, 4) if n else None,
                  "est_window_inflow": round(est, 0), "est_inflow_per_day": round(est / span_h * 24, 0),
                  "caveat": "token units (USDC = USD); short samples are noisy; time-of-day effects apply"}, indent=1))
