"""
cobuyer_hunter.py — سكربت Google Colab: من يشتري عملاته ويربح من ورائه؟
=========================================================================
المحرك (`bot/cluster.py`) يعمل بلا إنترنت. هذا الجامع هو الذي **يجلب** البيانات الخام.
لا يعمل داخل بيئة Arena (لا إنترنت لها) — شغّله في Colab حيث النت مفتوح.

⚠️ تنبيه عنوان: هذا السكربت مضبوط على
      7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi
   بينما تحليل المستودع الحالي (data/seed_mints.csv، 41 عملة) مبني على
      2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb
   تأكد أيهما هدفك. ضع `REBUILD_SEEDS = True` ليبني البذور من الصفر للعنوان الصحيح.

المراحل:
  1) بناء البذور  : كل العملات التي اشتراها الهدف + وقت كل شراء (أساس lead/lag)
  2) مسح العملات  : لكل عملة، كل من اشتراها ← المحافظ المرشحة
  3) تعميق المرشحين: للأفضل تشابهاً، كامل تاريخهم على هذه العملات ← PnL + مدة احتفاظ
  4) مصدر التمويل : من موّلهم ← كشف السيبل (محفظة واحدة بأسماء كثيرة)

المخرجات: seed_rebuilt.csv | cobuys_raw.csv | candidate_deep.csv | funding.csv
بعد التشغيل: حمّل cobuys_raw.csv وشغّل
      python3 bot/cluster.py --target <العنوان> --fills data/cobuys_raw.csv
"""
import csv
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

# ============ ضع مفتاحك هنا — أو الأفضل: متغير بيئة ============
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")
# ================================================================

TARGET_WALLET = "7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi"
SOL_MINT = "So11111111111111111111111111111111111111112"
LAMPORTS = 1e9

REBUILD_SEEDS = True          # False ← استخدم data/seed_mints.csv الجاهز
SEEDS_CSV = "seed_mints.csv"  # اسم الملف عند الرفع لـ Colab
MIN_SQUEEZE_SOL = 0.05        # تجاهل التحويلات الترابية

MAX_PAGES_PER_MINT = 30       # 30×100 = 3000 معاملة لكل عملة
MAX_PAGES_PER_WALLET = 20
DEEPEN_TOP_N = 60             # كم مرشحاً نحلله بعمق (يتحكم في الاستهلاك)
RATE_SLEEP = 0.12             # ~8 طلبات/ثانية (المجاني ~10)

BASE = "https://api-mainnet.helius-rpc.com"

FILLS_OUT = "cobuys_raw.csv"
FILL_FIELDS = ["wallet", "mint", "side", "ts", "sol", "tokens", "slot", "signature"]


# ------------------------------------------------------------------ الشبكة
def get_json(url, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                wait = 2 ** i
                print(f"    HTTP {e.code} — انتظار {wait}s")
                time.sleep(wait)
                continue
            print(f"    HTTP {e.code} — تخطي")
            return None
        except Exception as e:
            print(f"    retry {i + 1}: {e}")
            time.sleep(1.5)
    return None


def fetch_txs(address, max_pages=MAX_PAGES_PER_MINT):
    """كل معاملات عنوان (محفظة أو عملة) مع الترقيم التنازلي."""
    out, before, page = [], None, 0
    while page < max_pages:
        url = (f"{BASE}/v0/addresses/{address}/transactions"
               f"?api-key={HELIUS_API_KEY}&limit=100")
        if before:
            url += f"&before={before}"
        data = get_json(url)
        if not data:
            break
        out.extend(data)
        page += 1
        if len(data) < 100:
            break
        before = data[-1].get("signature")
        time.sleep(RATE_SLEEP)
    return out


# ------------------------------------------------------------------ التحليل
def parse_fills(tx, mint):
    """
    من معاملة واحدة على عملة معيَّنة ← صفقة المتداول الحقيقي (أو لا شيء).

    المتداول = feePayer (الموقّع الذي يدفع الرسوم). هذا القيد ضروري:
    بدون يظهر مجمع السيولة (AMM PDA) كبائع في **كل** عملية شراء — فيتصدر
    القائمة بتشابك كامل مع كل عملة، وهي ضوضاء تبتلع النتيجة كلها.
    حسابات الـ PDA لا تستطيع توقيع الرسوم، فـ feePayer هو دائماً محفظة حقيقية.
    """
    trader = tx.get("feePayer", "")
    if not trader:
        return []
    ts = float(tx.get("timestamp") or 0)
    slot = int(tx.get("slot") or 0)
    sig = tx.get("signature", "")

    side, tokens = None, 0.0
    for tt in tx.get("tokenTransfers") or []:
        if tt.get("mint") != mint:
            continue
        amt = float(tt.get("tokenAmount") or 0)
        if amt <= 0:
            continue
        if tt.get("toUserAccount") == trader:
            side, tokens = "buy", amt          # استلم التوكن = شراء
        elif tt.get("fromUserAccount") == trader:
            side, tokens = "sell", amt         # أرسل التوكن = بيع
    if side is None:
        return []

    sol = 0.0
    for nt in tx.get("nativeTransfers") or []:
        amt = float(nt.get("amount") or 0) / LAMPORTS
        if amt <= 0:
            continue
        if side == "buy" and nt.get("fromUserAccount") == trader:
            sol += amt                          # SOL خرج منه = ثمن الشراء
        elif side == "sell" and nt.get("toUserAccount") == trader:
            sol += amt                          # SOL دخله = حصيلة البيع
    return [(trader, side, sol, tokens, ts, slot, sig)]


def wallet_buys_from_history(txs):
    """من تاريخ محفظة ← (mint, وقت_الشراء) لكل شراء توكن (لبذر lead/lag)."""
    buys = []
    for tx in txs:
        ts = float(tx.get("timestamp") or 0)
        who = tx.get("feePayer", "")
        sol_out = defaultdict(float)
        for nt in tx.get("nativeTransfers") or []:
            if nt.get("fromUserAccount") == who:
                sol_out[who] += float(nt.get("amount") or 0) / LAMPORTS
        for tt in tx.get("tokenTransfers") or []:
            mint = tt.get("mint")
            if mint == SOL_MINT or tt.get("toUserAccount") != who:
                continue
            amt = float(tt.get("tokenAmount") or 0)
            if amt <= 0:
                continue
            buys.append((mint, ts, sol_out.get(who, 0.0)))
    return buys


def first_funder(txs):
    """أول عنوان حوّل SOL لهذه المحفظة — بصمة السيبيل."""
    oldest = sorted(txs, key=lambda t: t.get("timestamp") or 0)
    for tx in oldest:
        for nt in tx.get("nativeTransfers") or []:
            amt = float(nt.get("amount") or 0) / LAMPORTS
            if amt >= MIN_SQUEEZE_SOL and nt.get("toUserAccount"):
                return nt.get("fromUserAccount", "")
    return ""


# ------------------------------------------------------------------ الكتابة
def append_rows(path, fields, rows):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerows(rows)


def seen_signatures(path):
    """استئناف بعد انقطاع Colab — لا نعيد شراء نفس الصفقات."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {r.get("signature", "") for r in csv.DictReader(fh)}


# ------------------------------------------------------------------ المراحل
def stage1_seeds():
    print("\n" + "=" * 62)
    print(f"1) بناء البذور — عملات {TARGET_WALLET[:8]}…")
    print("=" * 62)
    if not REBUILD_SEEDS and os.path.exists(SEEDS_CSV):
        with open(SEEDS_CSV, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        print(f"  ← من الملف: {len(rows)} عملة")
        return {r["mint"]: r for r in rows}

    txs = fetch_txs(TARGET_WALLET, MAX_PAGES_PER_WALLET)
    print(f"  {len(txs)} معاملة")
    first = {}
    for mint, ts, sol in wallet_buys_from_history(txs):
        if mint not in first or ts < first[mint][0]:
            first[mint] = (ts, sol)
    rows = [{"mint": m, "symbol": "", "master_buy_ts": int(t), "master_sol": round(s, 6),
             "invested_sol": "", "returned_sol": "", "master_profit_sol": "",
             "master_status": "", "mcap_usd": "", "liq_usd": ""}
            for m, (t, s) in sorted(first.items())]
    append_rows("seed_rebuilt.csv", list(rows[0].keys()) if rows else ["mint"], rows)
    print(f"  ✅ {len(rows)} عملة → seed_rebuilt.csv")
    return {r["mint"]: r for r in rows}


def stage2_scan(seeds):
    print("\n" + "=" * 62)
    print(f"2) مسح كل مشترٍ في {len(seeds)} عملة…")
    print("=" * 62)
    done = seen_signatures(FILLS_OUT)
    overlap = defaultdict(set)
    for i, mint in enumerate(sorted(seeds), 1):
        txs = fetch_txs(mint, MAX_PAGES_PER_MINT)
        rows, wallets = [], set()
        for tx in txs:
            sig = tx.get("signature", "")
            if sig in done:
                continue
            for w, side, sol, tok, ts, slot, s in parse_fills(tx, mint):
                if w == SOL_MINT:
                    continue
                if side == "buy" and sol < MIN_SQUEEZE_SOL:
                    continue      # تحويل ترابي — ليس شراءً حقيقياً
                rows.append({"wallet": w, "mint": mint, "side": side, "ts": int(ts),
                             "sol": round(sol, 6), "tokens": round(tok, 4),
                             "slot": slot, "signature": s})
                wallets.add(w)
        append_rows(FILLS_OUT, FILL_FIELDS, rows)
        overlap[mint] = wallets
        print(f"  [{i}/{len(seeds)}] {mint[:12]}… → {len(wallets)} محفظة، {len(rows)} صف")
    buyers = defaultdict(set)
    for mint, ws in overlap.items():
        for w in ws:
            buyers[w].add(mint)
    buyers.pop(TARGET_WALLET, None)
    return buyers


def stage3_deepen(buyers):
    print("\n" + "=" * 62)
    print(f"3) تعميق أفضل {DEEPEN_TOP_N} مرشحاً (تاريخهم الكامل)…")
    print("=" * 62)
    top = sorted(buyers.items(), key=lambda kv: -len(kv[1]))[:DEEPEN_TOP_N]
    deep_rows = []
    for i, (wallet, mints) in enumerate(top, 1):
        txs = fetch_txs(wallet, MAX_PAGES_PER_WALLET)
        fund = first_funder(txs)
        deep_rows.append({"wallet": wallet, "overlap": len(mints),
                          "funder": fund, "tx_count": len(txs)})
        print(f"  [{i}/{len(top)}] {wallet[:10]}… تشابه={len(mints)} ممول={fund[:10] or '؟'}")
        time.sleep(RATE_SLEEP)
    append_rows("candidate_deep.csv", ["wallet", "overlap", "funder", "tx_count"], deep_rows)

    funding = defaultdict(list)
    for r in deep_rows:
        if r["funder"]:
            funding[r["funder"]].append(r["wallet"])
    clusters = {k: v for k, v in funding.items() if len(v) >= 2}
    append_rows("funding.csv", ["funder", "wallets", "size"],
                [{"funder": k, "wallets": "|".join(v), "size": len(v)}
                 for k, v in sorted(clusters.items(), key=lambda kv: -len(kv[1]))])
    print(f"  ✅ {len(clusters)} عنقود سيبيل محتمل → funding.csv")


# ------------------------------------------------------------------
def main():
    if not HELIUS_API_KEY:
        raise SystemExit("ضع HELIUS_API_KEY (متغير بيئة أو داخل الملف)")
    seeds = stage1_seeds()
    if not seeds:
        raise SystemExit("لم نجد شراءات — تحقق من العنوان")
    buyers = stage2_scan(seeds)
    print(f"\n  إجمالي المرشحين: {len(buyers)}")
    stage3_deepen(buyers)
    print("\n" + "=" * 62)
    print("✅ انتهى. حمّل cobuys_raw.csv ثم في المستودع:")
    print(f"   python3 bot/cluster.py --target {TARGET_WALLET} --fills cobuys_raw.csv")
    print("=" * 62)


if __name__ == "__main__":
    main()
