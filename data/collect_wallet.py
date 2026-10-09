"""
collect_wallet.py — سكربت Google Colab (1): تاريخ المحفظة الكامل + سياق الدخول + ملامح التوكن
==========================================================================================
تشغيل في Colab: ضع HELIUS_API_KEY ثم Runtime > Run all. يخرج 3 ملفات CSV.

المصادر (مجانية):
  - Helius REST   : كامل معاملات المحفظة (بالدقة — يحل الـ12 صفقة الناقصة)
  - DexScreener   : بيانات الزوج/الحجم (بدون مفتاح)
  - GeckoTerminal : سعر العملة حول لحظة الشراء (OHLCV — بدون مفتاح)
  - Helius RPC    : أكبر 20 حساباً (تركيز الحاملين) + معلومات الديف
"""
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone

# ============ ضع مفتاحك هنا (helius.dev — مجاني) ============
HELIUS_API_KEY = ""
# =============================================================
WALLET = "2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb"
SOL_MINT = "So11111111111111111111111111111111111111112"


def get_json(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"  retry {i+1}: {e}")
            time.sleep(2)
    return None


def post_json(url, payload):
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  post fail: {e}")
        return None


# ================================================================
# القسم A — كامل تاريخ المحفظة (يحل الـ12 صفقة الناقصة!)
# ================================================================
def fetch_full_history():
    print("=" * 60)
    print("A) جلب كامل تاريخ المحفظة من Helius…")
    print("=" * 60)
    rows, before = [], None
    page = 0
    while True:
        url = (f"https://api-mainnet.helius-rpc.com/v0/addresses/{WALLET}/transactions"
               f"?api-key={HELIUS_API_KEY}&limit=100")
        if before:
            url += f"&before={before}"
        data = get_json(url)
        if not data:
            break
        page += 1
        print(f"  صفحة {page}: {len(data)} معاملة")
        for tx in data:
            ts = tx.get("timestamp", 0)
            t = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            sig = tx.get("signature", "")
            ttype = tx.get("type", "")
            src = tx.get("source", "")
            # عمليات التوكن
            tok_transfers = tx.get("tokenTransfers", []) or []
            native = tx.get("nativeTransfers", []) or []
            sol_in = sum(x.get("amount", 0) for x in native
                         if x.get("toUserAccount") == WALLET) / 1e9
            sol_out = sum(x.get("amount", 0) for x in native
                          if x.get("fromUserAccount") == WALLET) / 1e9
            for tr in tok_transfers:
                mint = tr.get("mint", "")
                rows.append({
                    "time": t, "signature": sig, "type": ttype, "source": src,
                    "mint": mint, "symbol": tr.get("tokenSymbol", ""),
                    "token_amount": tr.get("tokenAmount", 0),
                    "sol_in": sol_in if tr.get("toUserAccount") == WALLET else 0,
                    "sol_out": sol_out if tr.get("fromUserAccount") == WALLET else 0,
                })
            if not tok_transfers:
                rows.append({"time": t, "signature": sig, "type": ttype, "source": src,
                             "mint": "", "symbol": "", "token_amount": 0,
                             "sol_in": sol_in, "sol_out": sol_out})
        if len(data) < 100:
            break
        before = data[-1]["signature"]
        time.sleep(0.5)

    # استنتاج buy/sell بالاتجاه
    for r in rows:
        if r["mint"] and r["mint"] != SOL_MINT:
            if r["token_amount"] > 0 and r["sol_out"] > 0:
                r["action"] = "buy"
                r["price_sol"] = r["sol_out"] / r["token_amount"]
            elif r["token_amount"] < 0 and r["sol_in"] > 0:
                r["action"] = "sell"
                r["price_sol"] = r["sol_in"] / abs(r["token_amount"])
            else:
                r["action"] = "transfer"
                r["price_sol"] = 0
        else:
            r["action"] = "sol_transfer"
            r["price_sol"] = 0

    fields = ["time", "signature", "type", "action", "source", "mint", "symbol",
              "token_amount", "sol_in", "sol_out", "price_sol"]
    with open("wallet_full_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    n_buy = sum(1 for r in rows if r["action"] == "buy")
    n_sell = sum(1 for r in rows if r["action"] == "sell")
    print(f"✅ wallet_full_history.csv — {len(rows)} سطر | {n_buy} شراء | {n_sell} بيع")
    return rows


# ================================================================
# القسم B — سياق الدخول: كان يشتري هبوط ولا صعود؟
# ================================================================
def fetch_entry_context(buy_rows):
    print("=" * 60)
    print("B) سياق الدخول (OHLCV حول كل شراء) من GeckoTerminal…")
    print("=" * 60)
    out = []
    buys = [r for r in buy_rows if r["action"] == "buy"]
    # تجميع الشراءات الفريدة (mint, time)
    seen = set()
    for b in buys:
        key = (b["mint"], b["time"])
        if not b["mint"] or key in seen:
            continue
        seen.add(key)
        t0 = int(datetime.strptime(b["time"], "%Y-%m-%d %H:%M:%S")
                 .replace(tzinfo=timezone.utc).timestamp())
        # نأخذ السعر حول اللحظة (أيام قبل/بعد) — 4h candles
        url = (f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{b['mint']}/ohlcv/hour"
               f"?limit=168&before_timestamp={t0 + 48*3600}")
        data = get_json(url)
        prices = []
        if data:
            try:
                prices = data["data"]["attributes"]["ohlcv_list"]  # [ts, o,h,l,c, v]
            except Exception:
                prices = []
        # أقرب الأسعار قبل/بعد اللحظة
        before_p = [p for p in prices if p[0] <= t0]
        after_p = [p for p in prices if p[0] > t0]
        entry_px = before_p[-1][4] if before_p else b["price_sol"]
        px_1h = before_p[-2][4] if len(before_p) >= 2 else entry_px
        px_24h = before_p[-24][4] if len(before_p) >= 24 else (before_p[0][4] if before_p else entry_px)
        px_after6h = after_p[6][4] if len(after_p) >= 6 else None
        high_before24 = max((p[2] for p in before_p[-24:]), default=entry_px)
        dip_pct = (1 - entry_px / high_before24) * 100 if high_before24 else 0
        trend = "dip" if dip_pct >= 5 else ("pump" if entry_px > px_24h * 1.1 else "flat")
        out.append({
            "mint": b["mint"], "symbol": b["symbol"], "buy_time": b["time"],
            "price_at_buy": entry_px,
            "price_1h_before": px_1h, "price_24h_before": px_24h,
            "high_24h_before": high_before24, "dip_pct": round(dip_pct, 2),
            "trend_at_entry": trend,
            "price_6h_after": px_after6h if px_after6h else "",
            "move_6h_pct": round((px_after6h / entry_px - 1) * 100, 2) if px_after6h and entry_px else "",
        })
        print(f"  {b['symbol'] or b['mint'][:10]}.. {b['time']} → {trend} (هبوط {dip_pct:.1f}%)")
        time.sleep(1.5)

    fields = ["mint", "symbol", "buy_time", "price_at_buy", "price_1h_before",
              "price_24h_before", "high_24h_before", "dip_pct", "trend_at_entry",
              "price_6h_after", "move_6h_pct"]
    with open("entry_context.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f"✅ entry_context.csv — {len(out)} شراء بسياقها")
    return out


# ================================================================
# القسم C — ملامح التوكن: الحاملين، الديف، الحجم
# ================================================================
def fetch_token_features(buy_rows):
    print("=" * 60)
    print("C) ملامح التوكن (holders/dev/volume)…")
    print("=" * 60)
    out = []
    mints = {}
    for r in buy_rows:
        if r["action"] == "buy" and r["mint"]:
            mints.setdefault(r["mint"], r)
    for mint, r in mints.items():
        feat = {"mint": mint, "symbol": r["symbol"], "buy_time": r["time"]}
        # DexScreener: حجم/سيولة/ماركت كاب
        ds = get_json(f"https://api.dexscreener.com/latest/dex/tokens/{mint}")
        pair = (ds.get("pairs") or [{}])[0] if ds else {}
        feat["volume_24h"] = pair.get("volume", {}).get("h24", "")
        feat["mcap"] = pair.get("marketCap") or pair.get("fdv", "")
        feat["liq_usd"] = (pair.get("liquidity") or {}).get("usd", "")
        feat["pair_created"] = pair.get("pairCreatedAt", "")
        # Helius RPC: أكبر 20 حساباً = تركيز الحاملين
        res = post_json(f"https://api-mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
                        {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts",
                         "params": [mint]})
        top = (res or {}).get("result", {}).get("value", [])
        if top:
            amounts = [float(a.get("uiAmount") or 0) for a in top]
            total_top = sum(amounts)
            feat["top10_pct_of_top20"] = round(sum(amounts[:10]) / total_top * 100, 2) if total_top else ""
            feat["largest_holder_pct_of_top20"] = round(max(amounts) / total_top * 100, 2) if total_top else ""
        else:
            feat["top10_pct_of_top20"] = ""
            feat["largest_holder_pct_of_top20"] = ""
        # معلومات التوكن (الديف/المنشئ)
        das = post_json(f"https://api-mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
                        {"jsonrpc": "2.0", "id": 1, "method": "getAsset", "params": {"id": mint}})
        content = ((das or {}).get("result") or {}).get("content", {})
        meta = content.get("metadata", {})
        feat["token_name"] = meta.get("name", "")
        feat["creator"] = ((das or {}).get("result") or {}).get("creators", [{}])[0].get("address", "") \
            if ((das or {}).get("result") or {}).get("creators") else ""
        out.append(feat)
        print(f"  {r['symbol'] or mint[:10]}.. volume={feat['volume_24h']} mcap={feat['mcap']}")
        time.sleep(0.7)

    fields = ["mint", "symbol", "buy_time", "token_name", "creator", "volume_24h",
              "mcap", "liq_usd", "pair_created", "top10_pct_of_top20",
              "largest_holder_pct_of_top20"]
    with open("token_features.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f"✅ token_features.csv — {len(out)} توكن")
    return out


# ================================================================
if __name__ == "__main__":
    assert HELIUS_API_KEY, "⚠️ ضع HELIUS_API_KEY من helius.dev في أول السكربت"
    history = fetch_full_history()
    fetch_entry_context(history)
    fetch_token_features(history)
    print("\n🎉 خلص! حمّل الملفات الثلاثة وارفعها في مجلد data/ بالمستودع:")
    print("   wallet_full_history.csv | entry_context.csv | token_features.csv")
