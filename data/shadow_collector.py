"""
shadow_collector.py — سكربت Google Colab (2): "الكون المضاد" — 3 إلى 7 أيام
=================================================================================
كل 5 دقائق يسجّل كل عملات pumpswap في نطاق $2–8K (اللي ما اشترها أيضاً!)
ويتتبع شراءات المحفظة المستهدفة — فنحصل على المقارنة الذهبية:

  المختار (اشتراه)  vs  المرفوض (كان في النطاق وما اشتره)

بدون هذي المقارنة نعرف صفاته — ومعها نعرف **وش ينقص غيره**.

تشغيل Colab: فعّل Runtime > Restart بعد 12h أو شغّله على جهاز/VPS.
الملف الناتج: universe_snapshot.csv (يُضاف إليه باستمرار)
"""
import csv
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

WALLET = "2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb"
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")   # اختياري — لتتبع شراءاته
OUT = "universe_snapshot.csv"
SNAPSHOT_EVERY_S = 300          # 5 دقائق
MCAP_MIN, MCAP_MAX = 1500, 12000   # نطاق أوسع قليلاً لالتقاط الحدود
FIELDS = ["ts", "mint", "symbol", "mcap", "liq_usd", "vol_24h", "price",
          "pair_created", "in_zone", "wallet_bought"]


def get_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_pumpswap_pools():
    """كل أزواج pumpswap النشطة (صفحات GeckoTerminal)."""
    pools = []
    for page in range(1, 4):
        url = (f"https://api.geckoterminal.com/api/v2/networks/solana/dexes/pumpswap/pools"
               f"?sort=h24_volume_usd_desc&page={page}")
        data = get_json(url)
        if not data:
            break
        for p in data.get("data", []):
            attrs = p.get("attributes", {})
            pools.append({
                "mint": attrs.get("base_token_address", ""),
                "symbol": (attrs.get("name") or "").split("/")[0].strip(),
                "mcap": float(attrs.get("market_cap_usd") or attrs.get("fdv_usd") or 0),
                "liq_usd": float(attrs.get("reserve_in_usd") or 0),
                "vol_24h": float(attrs.get("volume_usd", {}).get("h24") or 0),
                "price": float(attrs.get("base_token_price_usd") or 0),
                "pair_created": attrs.get("pool_created_at", ""),
            })
        time.sleep(1.5)
    return pools


def wallet_new_buys(since_ts):
    """شراءات المحفظة منذ لحظة (عبر Helius — اختياري)."""
    if not HELIUS_API_KEY:
        return set()
    url = (f"https://api-mainnet.helius-rpc.com/v0/addresses/{WALLET}/transactions"
           f"?api-key={HELIUS_API_KEY}&limit=20")
    data = get_json(url) or []
    bought = set()
    for tx in data:
        if tx.get("timestamp", 0) < since_ts:
            continue
        if tx.get("type") == "SWAP":
            for tr in tx.get("tokenTransfers", []) or []:
                if tr.get("toUserAccount") == WALLET:
                    bought.add(tr.get("mint", ""))
    return bought


def age_h(pair_created):
    if not pair_created:
        return ""
    try:
        t = datetime.fromisoformat(str(pair_created).replace("Z", "+00:00")).timestamp()
        return round((time.time() - t) / 3600, 1)
    except Exception:
        return ""


def run():
    print("🌌 shadow_collector — يسجل الكون كل", SNAPSHOT_EVERY_S, "ثانية")
    new_file = not os.path.exists(OUT)
    last_wallet_check = time.time() - 3600
    bought_mints = wallet_new_buys(last_wallet_check)
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        while True:
            now = time.time()
            ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            pools = fetch_pumpswap_pools()
            n_zone = 0
            for p in pools:
                in_zone = MCAP_MIN <= p["mcap"] <= MCAP_MAX
                n_zone += in_zone
                w.writerow({
                    "ts": ts, "mint": p["mint"], "symbol": p["symbol"],
                    "mcap": p["mcap"], "liq_usd": p["liq_usd"],
                    "vol_24h": p["vol_24h"], "price": p["price"],
                    "pair_created": p["pair_created"],
                    "in_zone": int(in_zone),
                    "wallet_bought": int(p["mint"] in bought_mints),
                })
            f.flush()
            print(f"[{ts}] {len(pools)} زوج | في النطاق: {n_zone} | مشترياته: {len(bought_mints)}")
            time.sleep(SNAPSHOT_EVERY_S)


if __name__ == "__main__":
    run()
