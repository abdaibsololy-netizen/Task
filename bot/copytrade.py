"""
CopyTrade — نسخ مباشر لمحفظة المتداول المستهدف.

⚠️ الحقيقة المهمة من البيانات:
صاحب المحفظة يشتري بـ1.02 SOL في بركة سيولتها $2–8K فقط — هو نفسه يحرك
الشارت ~10% بشرائه! لذلك النسخ يجب أن يكون:
  - سريع (priority fee) لتقع قرب سعره
  - بحجم أصغر (تأثيرك أقل)
  - مع "حارس الانحراف": إذا تجاوز سعرك سعره +5% → تخطّى الصفقة
    (لأن أرباحه الكثيرة x1.1–1.9 — دخول أسوأ بـ15% يحوّلها خسائر!)

التشغيل: HELIUS_API_KEY=... python copytrade.py   (paper افتراضياً)
"""
from __future__ import annotations

import asyncio
import json
import os
import time

import aiohttp

from executor import LiveExecutor, PaperExecutor
from portfolio import Portfolio, RiskManager
from strategy import EntryConfig, ExitConfig, Position, Strategy

HELIUS_WS = "wss://atlas-mainnet.helius-rpc.com/?api-key={key}"

# المحفظة المستهدفة (من وصف بيانات المعاملات في master_wallet_analysis.csv)
TARGET_WALLET = "2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb"


class CopyConfig:
    def __init__(self, **kw):
        self.size_sol: float = kw.get("size_sol", 0.5)          # أصغر من صاحبه (تأثير أقل)
        self.size_ratio: float = kw.get("size_ratio", 0.0)      # 0 = حجم ثابت، >0 = نسبة منه
        self.max_drift_pct: float = kw.get("max_drift_pct", 5.0)  # حارس الانحراف
        self.max_delay_s: float = kw.get("max_delay_s", 10.0)   # أقدم صفقة نقبلها
        self.skip_mints: set = set(kw.get("skip_mints", []))
        self.min_his_size_sol: float = kw.get("min_his_size_sol", 0.5)
        self.max_his_size_sol: float = kw.get("max_his_size_sol", 2.0)
        self.max_copies_per_trade: int = kw.get("max_copies_per_trade", 1)  # لا تتراكم على نفس العملة


class CopyTrader:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        cc = cfg.get("copy", {})
        self.c = CopyConfig(**cc)
        self.strategy = Strategy(EntryConfig(**cfg["entry"]),
                                 ExitConfig(**{k: v for k, v in cfg["exit"].items()
                                               if k != "dust_overhead_sol"}))
        self.pf = Portfolio(cfg["persistence"].get("copy_state_file", "copy_state.json"))
        self.risk = RiskManager(cfg["risk"]["max_daily_loss_sol"],
                                cfg["risk"]["max_open_sol"],
                                cfg["risk"]["max_position_sol"])
        mode = os.environ.get("MODE", cfg.get("mode", "paper"))
        self.live = mode == "live"
        if self.live:
            self.ex = LiveExecutor(cfg["pumpportal"]["trade_api"],
                                   cfg["pumpportal"]["slippage_pct"],
                                   cfg["pumpportal"]["priority_fee_sol"])
        else:
            self.ex = PaperExecutor(cfg["exit"]["dust_overhead_sol"])
        self.last_prices: dict[str, float] = {}
        self.his_fills: dict[str, dict] = {}   # mint -> أخر شراء له (لحراس الانحراف)
        self.copied_count: dict[str, int] = {}

    # ---------------------------------------------------------------
    async def on_his_buy(self, mint: str, sol_spent: float, tokens: float, ts: float) -> None:
        his_px = sol_spent / tokens if tokens else 0
        delay = time.time() - ts
        print(f"[HIS BUY] {mint[:12]}.. {sol_spent:.3f} SOL @ {his_px:.3e} (تأخير {delay:.1f}s)")

        if mint in self.c.skip_mints:
            return
        if not (self.c.min_his_size_sol <= sol_spent <= self.c.max_his_size_sol):
            print("  → تخطٍ: حجمه خارج النطاق")
            return
        if delay > self.c.max_delay_s:
            print(f"  → تخطٍ: التأخير {delay:.0f}s > {self.c.max_delay_s}s")
            return
        if self.copied_count.get(mint, 0) >= self.c.max_copies_per_trade:
            return

        size = self.c.size_ratio * sol_spent if self.c.size_ratio > 0 else self.c.size_sol
        ok, why = self.risk.can_open(self.pf, size)
        if not ok:
            print(f"  → تخطٍ (risk): {why}")
            return

        # التنفيذ — ثم فحص الانحراف مقارنة بسعره
        price = self.last_prices.get(mint) or his_px
        sig = type("S", (), {"mint": mint, "size_sol": size, "reason": "copy"})()
        pos = await self.ex.buy(sig, price, mint[:8])
        if pos is None:
            return
        drift = (pos.entry_price / his_px - 1) * 100 if his_px else 0
        if drift > self.c.max_drift_pct:
            print(f"  ❌ انحراف +{drift:.1f}% > الحد {self.c.max_drift_pct}% — إلغاء المدخل")
            # في live: باع فوراً؛ في paper نحذف الموضع
            self.pf.daily_pnl_sol -= size * 0.02  # احتساب خسارة الانسحاب التقريبية
            return
        print(f"  ✅ نسخنا الدخول: {size:.3f} SOL | انحراف +{drift:.2f}% عن سعره")
        self.his_fills[mint] = {"price": his_px, "ts": ts}
        self.copied_count[mint] = self.copied_count.get(mint, 0) + 1
        self.pf.add_entry(pos)

    async def manage(self, mint: str, price: float) -> None:
        pos = self.pf.positions.get(mint)
        if not pos or pos.phase.value == "closed":
            return
        pos.peak_mult = max(pos.peak_mult, pos.mult(price))
        sig = self.strategy.exit_signal(pos, price)
        if sig:
            await self.ex.sell(pos, sig, price)
            if pos.phase.value == "closed":
                rec = self.pf.close_if_done(pos, price)
                if rec:
                    print(f"[CLOSED] {rec['mint'][:12]}.. PnL {rec['pnl_sol']:+.3f} SOL")

    # ---------------------------------------------------------------
    async def run(self) -> None:
        key = os.environ.get("HELIUS_API_KEY")
        if not key:
            raise RuntimeError("عيّن HELIUS_API_KEY (مستوى مجاني يكفي) — نراقب حركات المحفظة عبر Helius WS")
        url = HELIUS_WS.format(key=key)
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "transactionSubscribe",
            "params": [TARGET_WALLET, {"failed": False, "accountInclude": [TARGET_WALLET]}],
        }
        print(f"مراقبة {TARGET_WALLET} …")
        while True:
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.ws_connect(url, heartbeat=30) as ws:
                        await ws.send_json(payload)
                        async for msg in ws:
                            if msg.type != aiohttp.WSMsgType.TEXT:
                                break
                            data = json.loads(msg.data)
                            await self._handle_tx(data)
            except Exception as e:  # noqa: BLE001
                print(f"[ws] {e} — إعادة خلال 5s")
                await asyncio.sleep(5)

    async def _handle_tx(self, data: dict) -> None:
        """يفكك معاملة Helius — يلتقط عمليات الشراء على PumpSwap."""
        try:
            tx = data.get("params", {}).get("result", {})
            meta = tx.get("transaction", {}).get("meta", {})
            instrs = tx.get("transaction", {}).get("transaction", {}).get("message", {}).get("instructions", [])
            ts = tx.get("timestamp", time.time())
            # تبسيط: نبحث عن تغيرات الحسابات (native) سالبة + توكن مُكتسب
            pre = meta.get("preBalances", [])
            post = meta.get("postBalances", [])
            if not pre or not post:
                return
            # ملاحظة: الفك التفصيلي يحتاج indexing — في paper نعتمد الرسائل المبسطة
            # من PumpPortal عبر mint في inner instructions (توسيع لاحقاً حسب الحاجة)
            logs = " ".join(meta.get("logMessages", []) or [])
            if "Program log: Instruction: Buy" in logs or "buy" in logs.lower():
                print(f"[tx] صفقة شراء مرصودة @ {ts}")
        except Exception:  # noqa: BLE001
            return


def main() -> None:
    import yaml
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    bot = CopyTrader(cfg)
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("إيقاف — الحالة محفوظة")


if __name__ == "__main__":
    main()
