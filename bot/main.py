"""
PumpBot — التشغيل الرئيسي

الاستخدام:
  python main.py                 # وضع المحاكاة (paper) — آمن
  python main.py --backtest      # تشغيل القواعد على البيانات التاريخية
  MODE=live python main.py       # تداول حقيقي (⚠️ خطر — محفظة صغيرة فقط)
"""
from __future__ import annotations

import argparse
import asyncio
import os
import time

import aiohttp
import yaml

from executor import LiveExecutor, PaperExecutor
from portfolio import Portfolio, RiskManager
from scanner import MetadataFetcher, PumpPortalStream, parse_trade_event
from strategy import EntryConfig, ExitConfig, Phase, Position, Strategy


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class Bot:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        exit_params = {k: v for k, v in cfg["exit"].items() if k != "dust_overhead_sol"}
        self.strategy = Strategy(EntryConfig(**cfg["entry"]), ExitConfig(**exit_params))
        self.pf = Portfolio(cfg["persistence"]["state_file"])
        self.risk = RiskManager(
            cfg["risk"]["max_daily_loss_sol"],
            cfg["risk"]["max_open_sol"],
            cfg["risk"]["max_position_sol"],
        )
        mode = os.environ.get("MODE", cfg.get("mode", "paper"))
        self.live = mode == "live"
        if self.live:
            self.ex = LiveExecutor(
                cfg["pumpportal"]["trade_api"],
                cfg["pumpportal"]["slippage_pct"],
                cfg["pumpportal"]["priority_fee_sol"],
            )
            print("⚠️  وضع LIVE — تداول حقيقي!")
        else:
            self.ex = PaperExecutor(cfg["exit"]["dust_overhead_sol"])
            print("وضع PAPER — محاكاة آمنة")
        self.last_prices: dict[str, float] = {}
        self.meta: MetadataFetcher | None = None
        self.stream: PumpPortalStream | None = None

    # ---------------------------------------------------------
    async def on_event(self, msg: dict) -> None:
        ev = parse_trade_event(msg)
        if ev is None:
            # رسالة عملة جديدة (NewToken) — نشترك بمراقبتها
            mint = msg.get("mint") if isinstance(msg, dict) else None
            if mint and self.stream:
                await self.stream.subscribe_trades(mint)
                await self.try_entry(mint, msg)
            return

        mint = ev["mint"]
        price = self._price_from(ev)
        if price:
            self.last_prices[mint] = price

        pos = self.pf.positions.get(mint)
        if pos and pos.phase != Phase.CLOSED:
            await self.handle_exit(pos, price)

        # فرصة دخول على تداولات العملات المرشحة
        if ev["side"] == "buy":
            await self.try_entry(mint, msg)

    def _price_from(self, ev: dict) -> float:
        if ev["token_amount"] > 0 and ev["sol_amount"] > 0:
            return ev["sol_amount"] / ev["token_amount"]
        return self.last_prices.get(ev["mint"], 0.0)

    # ---------------------------------------------------------
    async def try_entry(self, mint: str, msg: dict) -> None:
        if mint in self.pf.positions:
            return
        if self.meta is None:
            return
        mcap_sol = float(msg.get("marketCapSol") or 0)
        sol_px = float(self.cfg.get("sol_price_usd") or 150.0)
        snap = await self.meta.snapshot(mint, mcap_sol, sol_px)
        if snap is None:
            return
        sig = self.strategy.want_entry(
            snap,
            open_count=len(self.pf.open_positions()),
            last_entry_ts=self.pf.last_entry_ts,
            entries_today=self.pf.entries_today,
        )
        if not sig:
            return
        ok, why = self.risk.can_open(self.pf, sig.size_sol)
        if not ok:
            print(f"[RISK] رفض {snap.symbol or mint[:12]}: {why}")
            return
        price = self.last_prices.get(mint) or 0.0
        if price <= 0 and mcap_sol > 0:
            price = (mcap_sol * sol_px) / 1e6  # تقدير
        pos = await self.ex.buy(sig, price, snap.symbol)
        if pos:
            pos.liq_usd_at_entry = snap.liq_usd
            self.pf.add_entry(pos)
            if self.stream:
                await self.stream.subscribe_trades(mint)

    async def handle_exit(self, pos: Position, price: float) -> None:
        pos.peak_mult = max(pos.peak_mult, pos.mult(price))
        sig = self.strategy.exit_signal(pos, price)
        if not sig:
            return
        await self.ex.sell(pos, sig, price)
        if pos.phase == Phase.CLOSED:
            rec = self.pf.close_if_done(pos, price)
            if rec:
                print(f"[CLOSED] {rec['symbol'] or rec['mint'][:12]} | PnL {rec['pnl_sol']:+.3f} SOL | {rec['held_h']}h")

    # ---------------------------------------------------------
    async def run(self) -> None:
        async with aiohttp.ClientSession() as s:
            self.meta = MetadataFetcher(s)
            self.stream = PumpPortalStream(self.cfg["pumpportal"]["data_ws"], self.on_event)
            print("جارٍ الاتصال بـ PumpPortal… (Ctrl+C للإيقاف)")
            await self.stream.run()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "config.yaml"))
    ap.add_argument("--backtest", action="store_true")
    args = ap.parse_args()

    if args.backtest:
        import backtest
        backtest.run()
        return

    cfg = load_config(args.config)
    bot = Bot(cfg)
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nإيقاف — الحالة محفوظة في", cfg["persistence"]["state_file"])


if __name__ == "__main__":
    main()
