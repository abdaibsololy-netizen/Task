"""
alpha.py — البوت المستقل (AlphaBot) 🧠
يختار العملات بنفس معايير صاحب المحفظة (من البيانات) ويدخل عند الهبوط:

  معايير الاختيار (مطابقة لـ master_wallet_*):
    ✦ PumpSwap فقط (ما بعد التخرج)
    ✦ ماركت كاب $2,000–$8,000
    ✦ سيولة/ماركت كاب ≥ 85%
    ✦ عمر العملة 18–72 ساعة (المنطقة الذهبية — الرابحة وسيط 39h)
    ✦ حجم مركز ثابت ~1.02 SOL (أو 0.5 للتجربة) — بدون DCA أبداً

  توقيت الدخول (التطوير عليه):
    ✦ يشتري "عند الانهيار" — هبوط 5–35% عن قمة الساعة + تثبيت + بدون مطاردة

  الخروج: درّاجة 50% → 25% → 25% + وقف + إيقاف زمني (نفس الاستراتيجية المثبتة)

التشغيل:  python main.py --mode alpha          (paper)
          MODE=live python main.py --mode alpha (حقيقي — خزّن المفتاح في env فقط)
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

import aiohttp

from executor import LiveExecutor, PaperExecutor
from family import FamilyTracker
from market import DipConfig, DipDetector, PriceWindow
from portfolio import Portfolio, RiskManager
from scanner import MetadataFetcher, PumpPortalStream, parse_trade_event
from strategy import EntryConfig, ExitConfig, Position, Strategy, TokenSnapshot


class AlphaBot:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.entry_cfg = EntryConfig(**cfg["entry"])
        exit_params = {k: v for k, v in cfg["exit"].items() if k != "dust_overhead_sol"}
        self.strategy = Strategy(self.entry_cfg, ExitConfig(**exit_params))
        self.dip = DipDetector(DipConfig(**cfg.get("alpha", {}).get("dip", {})))
        fam_cfg = cfg.get("alpha", {}).get("family", {})
        self.family = FamilyTracker(
            wave_window_h=fam_cfg.get("wave_window_h", 72.0),
            min_members=fam_cfg.get("min_members", 2),
            family_stop_losses=fam_cfg.get("family_stop_losses", 2),
        )
        self.family_enabled = fam_cfg.get("enabled", True)
        self.family_wave_bonus = fam_cfg.get("wave_bonus", 1.6)
        self.family_require_wave = fam_cfg.get("require_wave", False)
        self.pf = Portfolio(cfg["persistence"].get("alpha_state_file", "alpha_state.json"))
        self.risk = RiskManager(cfg["risk"]["max_daily_loss_sol"],
                                cfg["risk"]["max_open_sol"],
                                cfg["risk"]["max_position_sol"])
        self.live = cfg.get("mode") == "live"
        self.ex = (LiveExecutor(cfg["pumpportal"]["trade_api"],
                                cfg["pumpportal"]["slippage_pct"],
                                cfg["pumpportal"]["priority_fee_sol"])
                   if self.live else PaperExecutor(cfg["exit"]["dust_overhead_sol"]))
        self.windows: dict[str, PriceWindow] = {}
        self.activity: dict[str, list] = {}          # mint -> [ts...]
        self.meta_cache: dict[str, tuple] = {}       # mint -> (ts, TokenSnapshot)
        self.meta: Optional[MetadataFetcher] = None
        self.stream: Optional[PumpPortalStream] = None
        self.sol_price = float(cfg.get("sol_price_usd") or 150.0)

    # ------------------------------------------------------------------
    def _activity_count(self, mint: str, now: float) -> int:
        ts_list = self.activity.setdefault(mint, [])
        window = self.dip.c.activity_window_min * 60
        self.activity[mint] = [t for t in ts_list if now - t < window]
        return len(self.activity[mint])

    async def _snapshot(self, mint: str) -> Optional[TokenSnapshot]:
        now = time.time()
        hit = self.meta_cache.get(mint)
        if hit and now - hit[0] < 120:
            return hit[1]
        if self.meta is None:
            return None
        c = await self.meta.coin(mint)
        if not c:
            return None
        created = c.get("created_timestamp") or c.get("createdTimestamp") or 0
        age_h = (now * 1000 - created) / 3.6e6 if created else 0.0
        mcap = float(c.get("usd_market_cap") or 0)
        vsol = float(c.get("virtual_sol_reserves") or 0)
        liq = vsol * self.sol_price if vsol else mcap * 0.9
        liq_pct = (liq / mcap * 100) if mcap else 0.0
        snap = TokenSnapshot(mint=mint, symbol=(c.get("symbol") or "").strip(),
                             mcap_usd=mcap, liq_usd=liq, liq_to_mcap_pct=liq_pct,
                             age_h=age_h, pool="pumpswap")
        self.meta_cache[mint] = (now, snap)
        # سجّل العضو في عائلة التيكر (سر الاختيار)
        if self.family_enabled and snap.symbol:
            in_zone = (self.strategy.entry_score(snap) > 0)
            self.family.observe(mint, snap.symbol, mcap, age_h, in_zone, now)
        return snap

    # ------------------------------------------------------------------
    async def on_event(self, msg: dict) -> None:
        ev = parse_trade_event(msg)
        now = time.time()

        if ev is None:
            mint = msg.get("mint") if isinstance(msg, dict) else None
            if mint and self.stream:
                await self.stream.subscribe_trades(mint)
            return

        mint = ev["mint"]
        price = (ev["sol_amount"] / ev["token_amount"]) if ev["token_amount"] > 0 else 0.0
        if price <= 0:
            return

        win = self.windows.setdefault(mint, PriceWindow())
        win.add(now, price)
        self.activity.setdefault(mint, []).append(now)

        # أ) إدارة المراكز المفتوحة أولاً (الخروج)
        pos = self.pf.positions.get(mint)
        if pos and pos.phase.value != "closed":
            await self._manage(pos, price)
            return

        # ب) فحص دخول جديد (نفس معاييره + موجة التيكر + الهبوط)
        await self._try_entry(mint, price, now)

    async def _manage(self, pos: Position, price: float) -> None:
        pos.peak_mult = max(pos.peak_mult, pos.mult(price))
        sig = self.strategy.exit_signal(pos, price)
        if sig:
            await self.ex.sell(pos, sig, price)
            if pos.phase.value == "closed":
                rec = self.pf.close_if_done(pos, price)
                if rec:
                    if self.family_enabled:
                        self.family.mark_result(pos.norm_symbol, won=rec["pnl_sol"] > 0)
                    print(f"[CLOSED] {rec['symbol'] or rec['mint'][:12]} | PnL {rec['pnl_sol']:+.3f} SOL | {rec['held_h']}h")

    async def _try_entry(self, mint: str, price: float, now: float) -> None:
        if mint in self.pf.positions:
            return
        snap = await self._snapshot(mint)
        if snap is None:
            return

        # معاييره — نفس اللي استخرجناها من بياناته (entry_score > 0)
        base_score = self.strategy.entry_score(snap)
        if base_score <= 0:
            return

        # 👑 سر الاختيار: موجة التيكر (GOIF×5, DOTF×5, SARP×4 في بياناته)
        norm = ""
        fam_score = 1.0
        if self.family_enabled and snap.symbol:
            norm = self.family.observe(mint, snap.symbol, snap.mcap_usd, snap.age_h,
                                       base_score > 0, now)
            if self.family.is_blacklisted(norm):
                return
            if self.family_require_wave and not self.family.is_wave(norm, now):
                return
            fam_score = self.family.score(norm, now)
            if fam_score >= 0.5:
                fam_score *= self.family_wave_bonus   # مضاعف الموجة
        if fam_score < 0.2 and self.family_require_wave:
            return

        # الهبوط — "يشتري عند الانهيار"
        win = self.windows.get(mint)
        recent = self._activity_count(mint, now)
        ok, why = self.dip.want_buy(win, price, recent, now)
        if not ok:
            return

        size = self.strategy.entry_size(snap)
        allowed, risk_why = self.risk.can_open(self.pf, size)
        if not allowed:
            print(f"[RISK] {snap.symbol or mint[:12]}: {risk_why}")
            return

        wave_tag = f"🌊{norm}×{self.family.family_size(norm, now)}" if norm and self.family.is_wave(norm, now) else "—"
        sig = type("S", (), {"mint": mint, "size_sol": size,
                             "reason": f"{snap.symbol} {wave_tag} MCap=${snap.mcap_usd:.0f} age={snap.age_h:.1f}h | {why}"})()
        pos = await self.ex.buy(sig, price, snap.symbol)
        if pos:
            pos.liq_usd_at_entry = snap.liq_usd
            pos.norm_symbol = norm
            self.pf.add_entry(pos)
            if self.stream:
                await self.stream.subscribe_trades(mint)

    # ------------------------------------------------------------------
    async def _reaper(self) -> None:
        """مراقب دوري: الإيقاف الزمني حتى بدون تداولات جديدة + تقرير."""
        while True:
            await asyncio.sleep(60)
            now = time.time()
            for pos in list(self.pf.open_positions()):
                win = self.windows.get(pos.mint)
                price = 0.0
                if win and win.ticks:
                    price = win.ticks[-1][1]
                if price > 0:
                    await self._manage(pos, price)
            n = len(self.pf.open_positions())
            print(f"[STATUS] مراكز مفتوحة: {n} | معرض: {self.pf.open_exposure_sol():.2f} SOL | "
                  f"دخول اليوم: {self.pf.entries_today} | PnL اليوم: {self.pf.daily_pnl_sol:+.3f}")

    async def run(self) -> None:
        async with aiohttp.ClientSession() as s:
            self.meta = MetadataFetcher(s)
            self.stream = PumpPortalStream(self.cfg["pumpportal"]["data_ws"], self.on_event)
            print("🧠 AlphaBot — فلترة معاييره + دخول عند الهبوط")
            print(f"   MCap ${self.entry_cfg.mcap_min_usd:.0f}-{self.entry_cfg.mcap_max_usd:.0f} | "
                  f"Liq≥{self.entry_cfg.liq_to_mcap_min:.0f}% | عمر {self.entry_cfg.age_min_h:.0f}-{self.entry_cfg.age_max_h:.0f}h | "
                  f"حجم {self.entry_cfg.size_sol} SOL")
            print(f"   الهبوط: {self.dip.c.min_dip_pct:.0f}-{self.dip.c.max_dip_pct:.0f}% عن قمة {self.dip.c.lookback_min:.0f}د + تثبيت")
            print(f"   الوضع: {'🔴 LIVE' if self.live else '🟢 PAPER'}")
            await asyncio.gather(self.stream.run(), self._reaper())
