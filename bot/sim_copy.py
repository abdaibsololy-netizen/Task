"""
sim_copy.py — محاكاة النسخ عبر بوت تيليقرام (Bloom/Trojan/…) على البيانات التاريخية.

الافتراضات (موثقة):
  - Bloom: 1% رسوم لكل صفقة (شراء+بيع)، مع كاشباك 10% → 0.9% فعلي  [bloombot.app]
  - Priority fee: 0.001–0.005 SOL + network ~0.00001
  - التأخير: 0.15–10 ثوانٍ → انحراف دخول (drift) على السيولة الصغيرة $2–8K
  - مسار السعر = نقاط البيع المرصودة (لا نخترع أسعاراً)

التشغيل: python sim_copy.py
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "master_wallet_analysis.csv")

# ---------- رسوم Bloom ----------
BLOOM_FEE_PCT = 0.9 / 100        # 1% − 10% cashback
PRIORITY_SOL = 0.002             # إعداد مقترح للسرعة
NETWORK_SOL = 0.00001


def fee_per_fill(fill_sol: float) -> float:
    return fill_sol * BLOOM_FEE_PCT + PRIORITY_SOL + NETWORK_SOL


def parse(ts: str) -> float:
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()


def load_trades():
    rows = list(csv.DictReader(open(DATA)))
    sec = lambda n: [r for r in rows if r["_Section_"] == n]
    buys = {r["Token"]: r for r in sec("Buy_Entry_Timing")}
    sells = defaultdict(list)
    for r in sec("Sell_Executions"):
        sells[r["Token"]].append(r)
    trades = []
    for tok, b in buys.items():
        entry = parse(b["Buy_Time"])
        spent = float(b["SOL_Spent"])
        trecv = float(b["Tokens_Received"])
        buy_p1m = spent / trecv * 1e6
        evs = []
        for s in sorted(sells.get(tok, []), key=lambda x: parse(x["Sell_Time"])):
            mult = float(s["Price_Per_1M_SOL"]) / buy_p1m
            evs.append((parse(s["Sell_Time"]), mult))
        trades.append({"mint": tok, "his_cost": spent, "entry_ts": entry, "evs": evs})
    return trades


# ---------- نسخة مبسطة من قواعد الخروج (نفس bot/strategy.py) ----------
def simulate_trade(trade, size_sol: float, drift_pct: float):
    """يعيد (realized_net, n_fills, outcome). يفترض دخولنا بسعره × (1+drift)."""
    drift = 1 + drift_pct / 100.0
    evs = trade["evs"]
    if not evs:
        # أكياس ميتة: نفس مصيره (Returned=0) — خسارة رأس المال + رسوم الشراء
        return -(size_sol + fee_per_fill(size_sol)), 0, "dead"

    remaining_frac = 1.0
    realized = 0.0
    n_fills = 0
    entry_ts = trade["entry_ts"]

    # قواعد مطابقة لـ bot/strategy.py (مضروبة في (1+drift) لأن مقياسنا مختلف)
    TP1, TP2, TP3 = 1.9 * drift, 3.5 * drift, 4.0 * drift
    FULL, SLOW, STOP = 1.1 * drift, 1.05 * drift, 0.92 * drift
    DEADLINE1, DEADLINE2, TSTOP = 36.0, 60.0, 72.0

    phase = 0  # 0=open 1=tp1 2=tp2
    peak = 1.0

    def sell(frac_of_remaining, mult_his, ts):
        nonlocal remaining_frac, realized, n_fills
        gross = size_sol * remaining_frac * frac_of_remaining * (mult_his / drift)
        realized += max(gross - fee_per_fill(gross), 0.0)
        remaining_frac *= (1 - frac_of_remaining)
        n_fills += 1

    for ts, m in evs:
        if remaining_frac <= 1e-9:
            break
        held = (ts - entry_ts) / 3600
        peak = max(peak, m)
        fired = True
        while fired and remaining_frac > 1e-9:
            fired = False
            if m <= STOP:
                sell(1.0, m, ts); fired = True; phase = 3; break
            if phase == 0:
                if m >= TP1:
                    sell(0.5, m, ts); phase = 1; fired = True
                elif m >= FULL:
                    sell(1.0, m, ts); phase = 3; fired = True
                elif held >= 8 and m >= SLOW:
                    sell(1.0, m, ts); phase = 3; fired = True
                elif held >= TSTOP:
                    sell(1.0, m, ts); phase = 3; fired = True
            elif phase == 1:
                if m >= TP2:
                    sell(0.5, m, ts); phase = 2; fired = True   # 50% من المتبقي = 25% أصلي
                elif held >= DEADLINE1:
                    sell(1.0, m, ts); phase = 3; fired = True
            elif phase == 2:
                if m >= TP3:
                    sell(1.0, m, ts); phase = 3; fired = True
                elif peak >= 3.5 and m <= peak * 0.8:
                    sell(1.0, m, ts); phase = 3; fired = True
                elif held >= DEADLINE2:
                    sell(1.0, m, ts); phase = 3; fired = True

    # قيمة المتبقي عند آخر نقطة معروفة (تقدير متحفظ — نبيع بالمربع الأخير)
    if remaining_frac > 1e-9:
        last_m = evs[-1][1]
        gross = size_sol * remaining_frac * (last_m / drift)
        realized += max(gross - fee_per_fill(gross), 0.0)
        n_fills += 1
        outcome = "open"
    else:
        outcome = "closed"

    buy_fee = fee_per_fill(size_sol)
    pnl = realized - size_sol - buy_fee     # الصافي: المبيعات − رأس المال − رسوم الشراء
    return pnl, n_fills, outcome


def run() -> None:
    trades = load_trades()
    print("=" * 84)
    print("محاكاة النسخ عبر بوت تيليقرام (Bloom-like: 0.9% + priority 0.002) — على 29 صفقة تاريخية")
    print("=" * 84)

    scenarios = [
        ("سريع جداً (0.2-1s)   ", 0.25, 2),
        ("سريع جداً (0.2-1s)   ", 0.50, 2),
        ("سريع (1-3s)          ", 0.50, 5),
        ("سريع (1-3s)          ", 1.02, 5),
        ("متوسط (3-10s)        ", 0.50, 10),
        ("متوسط (3-10s)        ", 1.02, 10),
        ("بطيء/منافسة (10-30s) ", 0.50, 20),
        ("بطيء/منافسة (10-30s) ", 1.02, 20),
    ]

    print(f"{'السيناريو':26} {'حجم':>5} {'drift':>6} {'صافي SOL':>9} {'ROI':>7} {'win%':>6} {'مغلق':>5} {'أكياس':>5}")
    for name, size, drift in scenarios:
        total, wins, closed, dead = 0.0, 0, 0, 0
        for t in trades:
            r, nf, outcome = simulate_trade(t, size, drift)
            total += r
            if t["evs"]:
                if r > 0:
                    wins += 1
                if outcome == "closed":
                    closed += 1
            else:
                dead += 1
        cost = size * len(trades)
        roi = total / cost * 100
        winp = wins / max(len(trades) - dead, 1) * 100
        print(f"{name:26} {size:5.2f} {drift:5}% {total:9.2f} {roi:6.1f}% {winp:5.0f}% {closed:5} {dead:5}")

    # ---------- جدول الهشاشة: متى تنقلب صفقاته الرابحة لخسائر ----------
    print("\n" + "=" * 84)
    print("هشاشة 'الحركات المحتشمة' (خروجه x1.1–1.9): كم يبقى ربحاً عند كل انحراف؟")
    print("=" * 84)
    modest = []
    for t in trades:
        if not t["evs"]:
            continue
        # أول نقطة خروج له = غالباً الخروج الكامل المحتشم
        first = t["evs"][0][1]
        if first < 1.9:
            modest.append((t["mint"][:12], first))
    print(f"{'العملة':14} {'xسعره':>6} | {'عند +2%':>8} {'+5%':>8} {'+10%':>8} {'+20%':>8}  (صافي أنت بعد 0.9%×2)")
    for mint, m in sorted(modest, key=lambda x: x[1]):
        vals = []
        for d in (2, 5, 10, 20):
            mine = m / (1 + d / 100)
            net = mine * (1 - 0.009) ** 2 - 0.008 / 1.0   # رسوم + priority موزعة
            vals.append(f"{(net-1)*100:+7.1f}%")
        flag = " ⚠️" if m / 1.10 < 1.0 else ""
        print(f"{mint:14} x{m:5.2f} | {vals[0]:>8} {vals[1]:>8} {vals[2]:>8} {vals[3]:>8}{flag}")

    # ---------- إعدادات Bloom المقترحة ----------
    print("\n" + "=" * 84)
    print("الإعدادات المقترحة في Bloom (أو أي بوت تيليقرام)")
    print("=" * 84)
    print("""
  نسخ المحفظة  : 2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb
  حجم الشراء    : 0.30–0.50 SOL ثابت (لا تنسخ الحجم الأصلي 1.02 — تأثيرك يقتلك)
  حد الشراء    : تخطى إذا اشترى أقل من 0.5 SOL أو أكثر من 2 SOL
  Slippage      : شراء 8–10% (لازم! شرائه يحرك 10%) | بيع 12–15%
  Priority fee  : 0.003–0.005 (High) — السرعة أهم من الـ 0.001
  Anti-MEV      : مفعّل | Rug Guard: مفعّل
  Auto Orders   : بيع 50% عند +90% | 25% عند +250% | الباقي عند +300%
                  (أو نسخ البيع follow-sell كخيار بديل)
  وقف خسارة    : −10% (إذا البوت يدعمه؛ وإلا AFK Mode بشرط)
  يومياً        : لا تزيد عن 4–6 نسخ | أوقف بعد 3 خسائر متتالية
  رأس المال     : 5–8 SOL كحد أقصى معرض (10 مراكز × 0.5)
""")


if __name__ == "__main__":
    run()
