"""
التنفيذ — وضعان:
  paper: محاكاة بأسعار السوق (الافتراضي، آمن)
  live:  PumpPortal Trade API (يتطلب مفتاح محفظة — خطر! استخدم على محفظة صغيرة)
"""
from __future__ import annotations

import time
from typing import Optional

import aiohttp

from strategy import Position, Signal


class PaperExecutor:
    """تنفيذ وهمي — يملأ بسعر السوق اللحظي."""

    def __init__(self, dust_overhead_sol: float = 0.015):
        self.dust = dust_overhead_sol
        self.fills: list[dict] = []

    async def buy(self, sig: Signal, price: float, symbol: str = "") -> Optional[Position]:
        tokens = (sig.size_sol - self.dust) / price if price > 0 else 0
        pos = Position(
            mint=sig.mint,
            symbol=symbol,
            entry_price=price,
            tokens=tokens,
            remaining=tokens,
            cost_sol=sig.size_sol,
            buy_ts=time.time(),
        )
        pos.liq_usd_at_entry = 0.0
        self.fills.append({"side": "buy", "mint": sig.mint, "sol": sig.size_sol, "price": price, "ts": time.time()})
        print(f"[PAPER][BUY] {symbol or sig.mint[:12]} | {sig.size_sol:.3f} SOL @ {price:.3e} | {sig.reason}")
        return pos

    async def sell(self, pos: Position, sig: Signal, price: float) -> float:
        from strategy import apply_fill
        sol = apply_fill(pos, sig.frac, price, self.dust)
        self.fills.append({"side": "sell", "mint": pos.mint, "sol": sol, "price": price, "ts": time.time()})
        print(f"[PAPER][SELL] {pos.symbol or pos.mint[:12]} | {sig.frac*100:.0f}% → {sol:.3f} SOL | {sig.reason}")
        return sol


class LiveExecutor:
    """
    تنفيذ حقيقي عبر PumpPortal Trade API.
    ⚠️ ضع المفتاح في متغير البيئة PUMPBOT_PRIVATE_KEY فقط — لا تكتبه في الملفات.
    """

    def __init__(self, trade_api: str, slippage_pct: float, priority_fee_sol: float):
        self.trade_api = trade_api
        self.slippage = slippage_pct
        self.priority_fee = priority_fee_sol

    async def _trade(self, action: str, mint: str, amount: float, denominated_in_sol: bool) -> Optional[dict]:
        import os
        key = os.environ.get("PUMPBOT_PRIVATE_KEY")
        if not key:
            raise RuntimeError("PUMPBOT_PRIVATE_KEY غير مضبوط — لا يمكن التداول الحقيقي")
        payload = {
            "action": action,                    # buy | sell
            "mint": mint,
            "amount": amount,                    # SOL للشراء، توكنات/نسبة للبيع
            "denominatedInSol": "true" if denominated_in_sol else "false",
            "slippage": self.slippage,
            "priorityFee": self.priority_fee,
            "pool": "pumpswap",
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(self.trade_api + "?api-key=" + key, json=payload,
                              timeout=aiohttp.ClientTimeout(total=30)) as r:
                text = await r.text()
                if r.status != 200:
                    print(f"[LIVE][FAIL] {action} {mint[:12]}: {r.status} {text[:200]}")
                    return None
                print(f"[LIVE][OK] {action} {mint[:12]}: {text[:200]}")
                return await r.json() if text else {}

    async def buy(self, sig: Signal, price: float, symbol: str = "") -> Optional[Position]:
        res = await self._trade("buy", sig.mint, sig.size_sol, True)
        if res is None:
            return None
        tokens = float(res.get("amount") or (sig.size_sol / price if price else 0))
        pos = Position(mint=sig.mint, symbol=symbol, entry_price=price, tokens=tokens,
                       remaining=tokens, cost_sol=sig.size_sol, buy_ts=time.time())
        return pos

    async def sell(self, pos: Position, sig: Signal, price: float) -> float:
        from strategy import apply_fill
        amount = pos.remaining * sig.frac
        res = await self._trade("sell", pos.mint, amount, False)
        if res is None:
            return 0.0
        got = float(res.get("solAmount") or amount * price)
        est = apply_fill(pos, sig.frac, price, 0.0)
        pos.realized_sol += max(got - est, 0.0)  # تسوية مع الفعلي المستلم
        return got
