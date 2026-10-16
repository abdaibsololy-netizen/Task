# -*- coding: utf-8 -*-
"""
live_profit.py — ترتيب المحافظ حسب نسبة الربح من التداولات الحية (GeckoTerminal).

ملاحظة صريحة عن البيانات:
- الـ API يعطي آخر ~300 صفقة للحوض فقط (شباك زمني قصير، ساعات).
- المركز يُحسب ربحه فقط إذا اشترى المحفظة وباع داخل الشباك. أي بيع لعملة
  اشترتها قبل الشباك يُتجاهل (ما نعرف تكلفته). لذلك النتيجة لقطة حية وليست
  ربحاً تاريخياً كاملاً.
- الربح = (قيمة البيع بالدولار - تكلفة الشراء بالدولار) / تكلفة الشراء.

الاستعمال في Colab:
    %run live_profit.py
"""
import csv
import time
import json
import urllib.request
from collections import defaultdict

# ═════════════ الإعدادات ═════════════
TARGET_WALLET = "7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi"
MINTS = [
    "MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump",   # OTC
    "3G1GckMxBRXL5r5THVmqXcjzULF5tgt8RXvgfBEepump",  # Givepixel
    "5436RHYCRnxDVLh9s5p1A7qsh6J8ArTW2isQWiAnpump",
    "E9uTKRzemitCqHivuL4d4MiRtY3hYUMrGTbJpEuXpump",
    "HgTGdc29D5bDMrDvsCLnorxz899VyDj7ZN7FPa6vpump",
    "68AGsjomsgTtiTaDhF6XGCeVJDnFeh415ngYYgVxGzns",
]
NET = "solana"
BASE = "https://api.geckoterminal.com/api/v2"
MIN_CLOSED = 2          # أقل عدد مراكز مغلقة داخل الشباك
MIN_USD = 20.0          # تجاهل الصفقات الصغيرة جداً
RATE_SLEEP = 2.2        # GeckoTerminal يحدد الطلبات بحوالي 30/دقيقة
OUT = "live_profit.csv"


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "live-profit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def top_pool(mint):
    """أكبر حوض سيولة للعملة (بعد WSOL)."""
    d = get_json(f"{BASE}/networks/{NET}/tokens/{mint}/pools")
    pools = d.get("data") or []
    if not pools:
        return None
    best = max(pools, key=lambda p: float(p["attributes"].get("reserve_in_usd") or 0))
    return best["attributes"]["address"]


def pool_trades(pool):
    d = get_json(f"{BASE}/networks/{NET}/pools/{pool}/trades")
    out = []
    for t in d.get("data") or []:
        a = t["attributes"]
        out.append({
            "wallet": a.get("tx_from_address", ""),
            "kind": a.get("kind", ""),
            "ts": a.get("block_timestamp", ""),
            "usd": float(a.get("volume_in_usd") or 0),
            "token_amt": float(a.get("from_token_amount") if a.get("kind") == "sell"
                               else a.get("to_token_amount") or 0),
            "mint": a.get("from_token_address") if a.get("kind") == "sell"
                    else a.get("to_token_address"),
        })
    return out


def realized_positions(trades):
    """
    يحسب المراكز المغلقة لكل (محفظة, عملة) داخل الشباك.
    يستخدم متوسط التكلفة. أي بيع أكثر من الكمية المتاحة يُتجاهل جزئياً.
    يرجع: {wallet: {"cost": usd, "proceeds": usd, "closed": n, "wins": n,
                    "first_buy": ts, "last_sell": ts}}
    """
    from datetime import datetime

    def parse(ts):
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()

    trades = sorted(trades, key=lambda t: parse(t["ts"]))
    pos = defaultdict(lambda: {"tok": 0.0, "cost": 0.0})   # (w, mint) -> holdings
    res = defaultdict(lambda: {"cost": 0.0, "proceeds": 0.0, "closed": 0,
                               "wins": 0, "first_buy": None, "last_sell": None})
    for t in trades:
        w, m = t["wallet"], t["mint"]
        if not w or not m or t["usd"] < MIN_USD or t["token_amt"] <= 0:
            continue
        k = (w, m)
        ts = parse(t["ts"])
        if t["kind"] == "buy":
            p = pos[k]
            p["tok"] += t["token_amt"]
            p["cost"] += t["usd"]
            r = res[w]
            r["first_buy"] = ts if r["first_buy"] is None else min(r["first_buy"], ts)
        elif t["kind"] == "sell":
            p = pos[k]
            if p["tok"] <= 0:
                continue                       # اشتراها قبل الشباك — مجهولة التكلفة
            sell_tok = min(t["token_amt"], p["tok"])
            avg = p["cost"] / p["tok"]
            cost_part = avg * sell_tok
            p["tok"] -= sell_tok
            p["cost"] -= cost_part
            r = res[w]
            r["cost"] += cost_part
            r["proceeds"] += t["usd"] * (sell_tok / t["token_amt"])
            r["last_sell"] = ts
            r["closed"] += 1
            if t["usd"] * (sell_tok / t["token_amt"]) > cost_part:
                r["wins"] += 1
    return res


def rank(res):
    rows = []
    for w, r in res.items():
        if w == TARGET_WALLET or r["closed"] < MIN_CLOSED or r["cost"] <= 0:
            continue
        roi = (r["proceeds"] - r["cost"]) / r["cost"]
        hold_h = ((r["last_sell"] or 0) - (r["first_buy"] or 0)) / 3600 \
            if r["first_buy"] and r["last_sell"] else 0
        rows.append({"wallet": w, "roi_pct": round(roi * 100, 1),
                     "profit_usd": round(r["proceeds"] - r["cost"], 2),
                     "cost_usd": round(r["cost"], 2), "closed": r["closed"],
                     "win_pct": round(100 * r["wins"] / r["closed"], 1),
                     "hold_hours": round(hold_h, 2)})
    rows.sort(key=lambda x: -x["roi_pct"])
    return rows


def main():
    all_trades = []
    print(f"جلب الصفقات الحية لـ {len(MINTS)} عملة…")
    for i, mint in enumerate(MINTS, 1):
        try:
            pool = top_pool(mint)
            time.sleep(RATE_SLEEP)
            if not pool:
                print(f"  [{i}] {mint[:10]}… لا يوجد حوض"); continue
            tr = pool_trades(pool)
            for t in tr:
                t.setdefault("mint", mint)
            all_trades += tr
            print(f"  [{i}] {mint[:10]}… {len(tr)} صفقة")
        except Exception as e:
            print(f"  [{i}] {mint[:10]}… خطأ: {e}")
        time.sleep(RATE_SLEEP)

    res = realized_positions(all_trades)
    rows = rank(res)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)

    print("\n" + "=" * 70)
    print(f"المحافظ اللي عندها مراكز مغلقة داخل الشباك: {len(rows)}")
    print("=" * 70)
    print("ROI%   ربح$      تكلفة$   مغلقة  فوز%  ساعات  المحفظة")
    for x in rows[:20]:
        print(f"{x['roi_pct']:>6} {x['profit_usd']:>8} {x['cost_usd']:>9} "
              f"{x['closed']:>6} {x['win_pct']:>5} {x['hold_hours']:>6}  {x['wallet']}")
    print(f"\nالملف: {OUT}")
    return rows


if __name__ == "__main__":
    main()
