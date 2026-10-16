"""
find_leader.py — الصق هذا في Colab وحدّه: يجيب لك القادة (LEADERS)
====================================================================
ملف واحد مكتفٍ بذاته. يجلب من Helius، يحلل، ويطبع **ترتيب المحافظ التي تشتري
نفس عملاته قبله وتربح** — بدون خطوة ثانية.

    LEADER   = يشتري قبله بـ 60 ثانية أو أكثر  ← هو يتبعهم (هؤلاء ما تبيهم)
    BUNDLE   = يشتري في نفس البلوك (±60ث)      ← فريق داخليين
    FOLLOWER = يشتري بعده                       ← من يربح من ورائه فعلاً

طريقة التشغيل:
    1) افتح Colab جديد
    2) ارفع هذا الملف (أو الصق محتواه في خلية)
    3) ضع مفتاحك في الخلية الأولى — **مفتاح جديد**، لا المفتاح المكشوف
    4) Runtime ▸ Run all

⚠️ العنوان: مضبوط على 7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi
   (تحليل المستودع القديم كان على 2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb)
"""
import csv
import json
import math
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict

# ══════════════════════ الإعدادات ══════════════════════
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")   # ← ضع مفتاحك الجديد هنا
TARGET_WALLET = "7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi"

MIN_OVERLAP = 2          # أقل عدد عملات مشتركة (أقل من 2 = غالباً مصادفة)
MIN_CLOSED = 3           # أقل عدد مراكز مغلقة قبل أن نثق بنسبة الربح
DEEPEN_LEADERS = True    # اجلب التاريخ الكامل للقادة (نسبة ربحهم الحقيقية)
TOP_DEEPEN = 40

MAX_PAGES_MINT = 30      # 30×100 = 3000 معاملة لكل عملة
MAX_PAGES_WALLET = 20
RATE_SLEEP = 0.12
MIN_SOL = 0.05

LAMPORTS = 1e9
SOL_MINT = "So11111111111111111111111111111111111111112"
BASE = "https://api-mainnet.helius-rpc.com"

LEADER_EDGE_S = -60.0
BUNDLE_EDGE_S = 60.0
HOLD_BANDS = (("scalp<1h", 0, 3600), ("intraday<24h", 3600, 24 * 3600),
              ("hold~1d", 24 * 3600, 48 * 3600), ("hold~2d", 48 * 3600, 7 * 86400),
              ("hold~1w+", 7 * 86400, float("inf")))


# ══════════════════════ الشبكة ══════════════════════
def get_json(url, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** i)
                continue
            return None
        except Exception:
            time.sleep(1.5)
    return None


def fetch_txs(address, max_pages):
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


# ══════════════════════ المحللات ══════════════════════
def parse_fill(tx, mint):
    """
    المتداول = feePayer فقط. ضروري: وإلا ظهر مجمع السيولة كبائع في كل شراء
    فتصدّر القائمة بتشابك كامل مع كل عملة وابتلع النتيجة.
    """
    trader = tx.get("feePayer", "")
    if not trader:
        return None
    side, tokens = None, 0.0
    for tt in tx.get("tokenTransfers") or []:
        if tt.get("mint") != mint:
            continue
        amt = float(tt.get("tokenAmount") or 0)
        if amt <= 0:
            continue
        if tt.get("toUserAccount") == trader:
            side, tokens = "buy", amt
        elif tt.get("fromUserAccount") == trader:
            side, tokens = "sell", amt
    if side is None:
        return None
    sol = 0.0
    # SOL الأصلي + WSOL (الملفوف). pump AMM يدفع غالباً بـ WSOL، وإغفاله
    # يجعل كل شراء قيمته 0 فيُتجاهل، ويصفّر مبيعات المحافظ كلها.
    for nt in tx.get("nativeTransfers") or []:
        amt = float(nt.get("amount") or 0) / LAMPORTS
        if amt <= 0:
            continue
        if (side == "buy" and nt.get("fromUserAccount") == trader) or \
           (side == "sell" and nt.get("toUserAccount") == trader):
            sol += amt
    for tt in tx.get("tokenTransfers") or []:
        if tt.get("mint") != SOL_MINT:
            continue
        amt = float(tt.get("tokenAmount") or 0)
        if amt <= 0:
            continue
        if (side == "buy" and tt.get("fromUserAccount") == trader) or \
           (side == "sell" and tt.get("toUserAccount") == trader):
            sol += amt
    return {"wallet": trader, "mint": mint, "side": side,
            "ts": float(tx.get("timestamp") or 0), "sol": sol,
            "tokens": tokens, "slot": int(tx.get("slot") or 0),
            "signature": tx.get("signature", "")}


def token_buys(txs):
    """من تاريخ محفظة ← {mint: أول وقت شراء} (يتجاهل تحويلات SOL الصرفة)."""
    first = {}
    for tx in txs:
        who = tx.get("feePayer", "")
        ts = float(tx.get("timestamp") or 0)
        for tt in tx.get("tokenTransfers") or []:
            mint = tt.get("mint")
            if mint == SOL_MINT or tt.get("toUserAccount") != who:
                continue
            if float(tt.get("tokenAmount") or 0) <= 0:
                continue
            if mint not in first or ts < first[mint]:
                first[mint] = ts
    return first


def first_funder(txs):
    for tx in sorted(txs, key=lambda t: t.get("timestamp") or 0):
        for nt in tx.get("nativeTransfers") or []:
            if float(nt.get("amount") or 0) / LAMPORTS >= MIN_SOL and nt.get("toUserAccount"):
                return nt.get("fromUserAccount", "")
    return ""


# ══════════════════════ التحليل ══════════════════════
def hold_band(s):
    for name, lo, hi in HOLD_BANDS:
        if lo <= s < hi:
            return name
    return "hold~1w+"


def median(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def wallet_metrics(fills, seeds):
    """PnL محقَّق (مراكز مغلقة فقط) + lead/lag + أحزمة الاحتفاظ."""
    per = defaultdict(list)
    for f in fills:
        per[f["mint"]].append(f)

    inv = ret = 0.0
    closed = wins = 0
    holds, leads, sizes = [], [], []
    for mint, fs in per.items():
        b = [f for f in fs if f["side"] == "buy"]
        s = [f for f in fs if f["side"] == "sell"]
        i = sum(f["sol"] for f in b)
        r = sum(f["sol"] for f in s)
        inv += i
        ret += r
        if s:
            closed += 1
            wins += 1 if r - i > 0 else 0
            holds.append(max(0.0, max(f["ts"] for f in s) - min(f["ts"] for f in b)))
            sizes.append(i)
        if b and mint in seeds and seeds[mint]:
            leads.append(min(f["ts"] for f in b) - seeds[mint])

    roi = (ret - inv) / inv if inv > 0 else 0.0
    return {"invested": inv, "returned": ret, "roi": roi,
            "winrate": wins / closed if closed else 0.0,
            "closed": closed, "holds": holds, "leads": leads, "sizes": sizes}


def score(overlap, roi, role, winrate, closed):
    conf = min(1.0, closed / 4.0)
    edge = {"LEADER": 1.0, "BUNDLE": 0.75, "FOLLOWER": 0.3}.get(role, 0.0)
    return round(0.35 * min(1.0, roi / 3.0) + 0.25 * min(1.0, overlap / 5.0)
                 + 0.20 * edge + 0.20 * winrate * conf, 4)


def cosine(a, b):
    return len(a & b) / math.sqrt(len(a) * len(b)) if a and b else 0.0


# ══════════════════════ المراحل ══════════════════════
def main():
    if not HELIUS_API_KEY:
        raise SystemExit("ضع HELIUS_API_KEY أولاً (مفتاح جديد — القديم مكشوف)")

    print("=" * 70)
    print(f"1) بذور {TARGET_WALLET[:10]}…")
    txs = fetch_txs(TARGET_WALLET, MAX_PAGES_WALLET)
    seeds = token_buys(txs)
    print(f"   {len(txs)} معاملة → {len(seeds)} عملة")
    if not seeds:
        raise SystemExit("لا شراءات — تحقق من العنوان")

    print("=" * 70)
    print(f"2) مسح كل مشترٍ في {len(seeds)} عملة…")
    fills_by_wallet = defaultdict(list)
    with open("cobuys_raw.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["wallet", "mint", "side", "ts",
                                           "sol", "tokens", "slot", "signature"])
        w.writeheader()
        for i, mint in enumerate(sorted(seeds), 1):
            n = 0
            for tx in fetch_txs(mint, MAX_PAGES_MINT):
                f = parse_fill(tx, mint)
                if not f:
                    continue
                if f["wallet"] == SOL_MINT:
                    continue
                if f["side"] == "buy" and f["sol"] < MIN_SOL:
                    continue          # تحويل ترابي، ليس شراءً
                w.writerow({k: (round(f[k], 6) if k in ("sol", "tokens")
                                else int(f[k]) if k in ("ts", "slot") else f[k])
                            for k in ("wallet", "mint", "side", "ts", "sol",
                                      "tokens", "slot", "signature")})
                fills_by_wallet[f["wallet"]].append(f)
                n += 1
            print(f"   [{i}/{len(seeds)}] {mint[:14]}… {n} صفقة")
    fills_by_wallet.pop(TARGET_WALLET, None)
    print(f"   ✅ {len(fills_by_wallet)} محفظة مرشحة → cobuys_raw.csv")

    print("=" * 70)
    print(f"3) ترتيب المرشحين (تشابه ≥ {MIN_OVERLAP})…")
    rows = []
    for wallet, fs in fills_by_wallet.items():
        shared = {f["mint"] for f in fs} & set(seeds)
        if len(shared) < MIN_OVERLAP:
            continue
        m = wallet_metrics(fs, seeds)
        if m["closed"] < MIN_CLOSED:
            continue
        med_lead = median(m["leads"]) if m["leads"] else 0.0
        role = ("LEADER" if med_lead <= LEADER_EDGE_S
                else "FOLLOWER" if med_lead >= BUNDLE_EDGE_S else "BUNDLE")
        bands = Counter(hold_band(h) for h in m["holds"])
        rows.append({"wallet": wallet, "overlap": len(shared),
                     "cosine": round(cosine(shared, set(seeds)), 4),
                     "role": role, "lead_s": round(med_lead, 1),
                     "roi": round(m["roi"], 4), "winrate": round(m["winrate"], 4),
                     "closed": m["closed"], "pnl": round(m["returned"] - m["invested"], 4),
                     "band": bands.most_common(1)[0][0] if bands else "",
                     "score": score(len(shared), m["roi"], role, m["winrate"], m["closed"])})
    rows.sort(key=lambda r: -r["score"])
    print(f"   {len(rows)} محفظة تجاوزت الفلاتر")

    with open("candidates_ranked.csv", "w", newline="", encoding="utf-8") as fh:
        if rows:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    # ── التاريخ الكامل للداخليين (القادة + فريق البلوك) ──
    # يجب جلب الفريقين معاً: عنقود السيبيل لا يتكوّن إلا إذا قارنّا مصادر تمويل
    # أكثر من محفظة. لو اكتفينا بالقادة لما ظهر عنقود أبداً.
    if DEEPEN_LEADERS:
        insiders = [r for r in rows if r["role"] in ("LEADER", "BUNDLE")][:TOP_DEEPEN]
        print("=" * 70)
        print(f"4) التاريخ الكامل لـ {len(insiders)} داخلياً + مصدر التمويل…")
        clusters = defaultdict(list)
        for i, r in enumerate(insiders, 1):
            t = fetch_txs(r["wallet"], MAX_PAGES_WALLET)
            fund = first_funder(t)
            if fund:
                clusters[fund].append(r["wallet"])
            r["funder"] = fund
            r["total_tx"] = len(t)
            print(f"   [{i}/{len(insiders)}] {r['wallet'][:12]}… "
                  f"{r['role']:<8} ممول={fund[:12] or '؟'}")
            time.sleep(RATE_SLEEP)
        with open("insiders.csv", "w", newline="", encoding="utf-8") as fh:
            if insiders:
                w = csv.DictWriter(fh, fieldnames=list(insiders[0].keys()))
                w.writeheader()
                w.writerows(insiders)
        dup = {k: v for k, v in clusters.items() if len(v) >= 2}
        with open("sybil_clusters.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["funder", "wallets", "size"])
            w.writeheader()
            for k, v in sorted(dup.items(), key=lambda kv: -len(kv[1])):
                w.writerow({"funder": k, "wallets": "|".join(v), "size": len(v)})
        print(f"   ✅ {len(dup)} عنقود سيبيل → sybil_clusters.csv")

    # ══════════════════════ النتيجة ══════════════════════
    print("\n" + "═" * 70)
    print("★ القادة — يشترون نفس عملاته **قبله** ويربحون (انسخهم هم)")
    print("═" * 70)
    leaders = [r for r in rows if r["role"] == "LEADER"]
    if not leaders:
        print("لا قائد تجاوز الفلاتر — جرّب MIN_OVERLAP=2 و MIN_CLOSED=2،")
        print("أو وسّع MAX_PAGES_MINT. يعني غالباً: هو المصدر، لا التابع.")
    print(f"{'#':>2} {'المحفظة':<46} {'عملات':>5} {'قبله':>9} {'ROI':>7} "
          f"{'فوز':>5} {'احتفاظ':<13} {'درجة':>5}")
    print("-" * 108)
    for i, r in enumerate(leaders[:25], 1):
        lead = f"{abs(r['lead_s']) / 3600:.1f}h"
        print(f"{i:>2} {r['wallet']:<46} {r['overlap']:>5} {lead:>9} "
              f"{r['roi'] * 100:>6.0f}% {r['winrate'] * 100:>4.0f}% "
              f"{r['band']:<13} {r['score']:>5.2f}")

    print("\n" + "═" * 70)
    print("★ من يربح من ورائه فعلاً (يشتري بعده) — FOLLOWER")
    print("═" * 70)
    fol = [r for r in rows if r["role"] == "FOLLOWER"]
    if not fol:
        print("لا أحد.")
    print(f"{'#':>2} {'المحفظة':<46} {'عملات':>5} {'بعده':>9} {'ROI':>7} {'درجة':>5}")
    print("-" * 92)
    for i, r in enumerate(fol[:15], 1):
        print(f"{i:>2} {r['wallet']:<46} {r['overlap']:>5} {r['lead_s'] / 3600:>8.1f}h "
              f"{r['roi'] * 100:>6.0f}% {r['score']:>5.2f}")

    bun = [r for r in rows if r["role"] == "BUNDLE"]
    print(f"\n★ فريق البلوك الواحد (BUNDLE): {len(bun)} — انظر candidates_ranked.csv")
    print("\nالملفات: cobuys_raw.csv · candidates_ranked.csv · insiders.csv · sybil_clusters.csv")

    # ════════════════ كتلة للنسخ المباشر في المحادثة ════════════════
    # حتى ما تحتاج ترفع ملفات — انسخ ما بين الخطين وأرسله.
    print("\n\n" + "▓" * 70)
    print("▓ انسخ من السطر التالي إلى آخر كتلة — والصقه في المحادثة")
    print("▓" * 70)
    print("```")
    print(f"TARGET: {TARGET_WALLET}")
    print(f"SEEDS: {len(seeds)}  CANDIDATES: {len(rows)}  "
          f"LEADERS: {len(leaders)}  FOLLOWERS: {len(fol)}  BUNDLES: {len(bun)}")
    print("ROLE,WALLET,OVERLAP,LEAD_S,ROI,WINRATE,CLOSED,BAND,SCORE,FUNDER")
    for r in rows[:40]:
        print(f"{r['role']},{r['wallet']},{r['overlap']},{r['lead_s']},"
              f"{r['roi']},{r['winrate']},{r['closed']},{r['band']},"
              f"{r['score']},{r.get('funder', '')}")
    dup2 = {k: v for k, v in (clusters.items() if DEEPEN_LEADERS else [])
            if len(v) >= 2}
    for k, v in sorted(dup2.items(), key=lambda kv: -len(kv[1])):
        print(f"SYBIL,{k},{len(v)},{'|'.join(v)}")
    print("```")


if __name__ == "__main__":
    main()
