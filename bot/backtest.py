"""
Backtest — يعيد تشغيل قواعد البوت على نقاط الدخول/الخروج المرصودة في
master_wallet_analysis.csv ويقارن النتيجة مع أداء المتداول الحقيقي.

المنهجية (متحفظة): نعرف سعر الدخول ونقاط (وقت × مضاعف سعر) عند عمليات البيع الفعلية فقط.
نطبّق قواعد البوت على هذه النقاط؛ موضع بلا نقاط خروج يبقى "مفتوحاً" (لا نختلق سعراً).
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime

from strategy import EntryConfig, ExitConfig, Phase, Position, Strategy, apply_fill

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "master_wallet_analysis.csv")


def load():
    rows = list(csv.DictReader(open(DATA)))
    sec = lambda n: [r for r in rows if r["_Section_"] == n]
    return sec("Buy_Entry_Timing"), sec("Sell_Executions"), sec("Tokens_PnL_Detailed")


def parse(ts: str) -> float:
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()


def run() -> None:
    buys, sells, pnl = load()
    buys_by = {r["Token"]: r for r in buys}
    sells_by = defaultdict(list)
    for r in sells:
        sells_by[r["Token"]].append(r)

    strat = Strategy(EntryConfig(), ExitConfig())
    dust = 0.015

    print("=" * 78)
    print("BACKTEST — قواعد البوت على البيانات التاريخية (29 شراءً موثقاً)")
    print("=" * 78)

    bot_realized, human_realized, bot_open_cost = 0.0, 0.0, 0.0
    rows_out = []

    for tok, b in buys_by.items():
        entry = parse(b["Buy_Time"])
        spent = float(b["SOL_Spent"])
        trecv = float(b["Tokens_Received"])
        entry_px = spent / trecv                      # SOL لكل توكن
        evs = []
        for s in sorted(sells_by.get(tok, []), key=lambda x: parse(x["Sell_Time"])):
            mult = float(s["Price_Per_1M_SOL"]) / (entry_px * 1e6)
            evs.append((parse(s["Sell_Time"]), mult))

        pos = Position(mint=tok, entry_price=entry_px, tokens=trecv, remaining=trecv,
                       cost_sol=spent, buy_ts=entry)
        realized = 0.0
        trail = []
        for ts, mult in evs:
            # قد تتوالى إشارات عند نفس اللقطة (tp2 ثم tp3 مثلاً)
            for _ in range(4):
                if pos.phase == Phase.CLOSED:
                    break
                pos.peak_mult = max(pos.peak_mult, mult)
                sig = strat.exit_signal(pos, price=mult * entry_px, now=ts)
                if not sig:
                    break
                got = apply_fill(pos, sig.frac, mult * entry_px, dust)
                realized += got
                h = (ts - entry) / 3600
                trail.append(f"{sig.reason}@{h:.1f}h→{got:.2f}")
        bot_realized += realized
        open_cost = pos.cost_sol - pos.realized_sol
        if pos.phase != Phase.CLOSED:
            bot_open_cost += max(open_cost, 0)

        h_real = sum(float(s["SOL_Received"]) for s in sells_by.get(tok, []))
        human_realized += h_real
        status = "CLOSED" if pos.phase == Phase.CLOSED else "OPEN"
        rows_out.append((tok[:14], spent, realized, h_real, status, trail))

    print(f"{'token':16} {'cost':>6} {'BOT':>7} {'HUMAN':>7} {'st':>6}  مسار البوت")
    for t, c, r, h, st, trail in rows_out:
        print(f"{t:16} {c:6.3f} {r:7.3f} {h:7.3f} {st:>6}  {' | '.join(trail) or '(لا نقطة خروج معروفة)'}")

    total_cost = sum(float(b["SOL_Spent"]) for b in buys_by.values())
    print("-" * 78)
    print(f"التكلفة (29 شراء): {total_cost:.2f} SOL")
    print(f"BOT   : محقق {bot_realized:.3f} SOL + مفتوح بقيمة تكلفة {bot_open_cost:.3f} SOL")
    print(f"HUMAN : محقق {human_realized:.3f} SOL (29 شراءً فقط — بدون الـ12 صفقة الناقصة)")
    n_closed = sum(1 for *_, st, __ in rows_out if st == "CLOSED")
    print(f"مغلق بالبوت: {n_closed}/{len(rows_out)} | مفتوح: {len(rows_out)-n_closed}")
    print("\nملاحظات:")
    print("- HUMAN الحقيقي أشمل: +15.7 SOL من 12 صفقة بلا سجل شراء غير محسوبة هنا.")
    print("- البوت يطبق الحماية (وقف −10%، إيقاف 72h)؛ المتداول ترك 6 أكياس ميتة (−6.65 SOL ورقياً).")
    print("- النقاط المعروفة هي لحظات بيع المتداول فقط؛ مسار السعر الكامل غير متوفر.")


if __name__ == "__main__":
    run()
