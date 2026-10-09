"""
PumpBot — نواة الاستراتيجية (منطق نقي بدون شبكة)
مستخرجة من: analysis/STRATEGY_PATTERN.md

قواعد الدخول:
  pumpswap + MCap $2-8K + Liq/MCap ≥ 85% + عمر 18-72h + حجم ثابت + بدون DCA

قواعد الخروج (مطابقة لـ 23/23 من نقاط الخروج المرصودة):
  OPEN:
    m ≥ 1.9            → بيع 50% (وضع الركوب — GGMm/6Wbi/tY5KS/iTbV/6DWH/W7Lj)
    1.1 ≤ m < 1.9      → خروج كامل (الحركة المحتشمة — 11 صفقة مرصودة)
    بعد 8h و m ≥ 1.05  → خروج كامل (الركود — GkNB/PUXx)
    بعد 72h            → إيقاف زمني (يمنع الأكياس الميتة الستة)
  TP1 (متبقٍ 50%):
    m ≥ 3.5            → بيع 25% (TP2)
    بعد 36h بدون امتداد → بيع الباقي (tY5KS@48h, iTbV@90h)
  TP2 (متبقٍ 25%):
    m ≥ 4.0            → بيع الباقي (امتداد القمة — GGMm@4.44)
    trailing 20% من قمة ≥ 3.5 (6DWH#3@2.17)
    بعد 60h            → بيع الباقي
  دائماً: وقف −10% | حماية rug (سقوط سيولة 50%)
  NEVER: DCA | شراء عمره > 72h
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Phase(str, Enum):
    OPEN = "open"
    TP1 = "tp1"
    TP2 = "tp2"
    CLOSED = "closed"


@dataclass
class Position:
    mint: str
    symbol: str = ""
    entry_price: float = 0.0       # SOL لكل توكن
    tokens: float = 0.0
    remaining: float = 0.0
    cost_sol: float = 0.0
    realized_sol: float = 0.0
    buy_ts: float = 0.0
    phase: Phase = Phase.OPEN
    peak_mult: float = 1.0
    liq_usd_at_entry: float = 0.0

    def mult(self, price: float) -> float:
        return price / self.entry_price if self.entry_price else 0.0

    def held_h(self, now: Optional[float] = None) -> float:
        return ((now or time.time()) - self.buy_ts) / 3600.0


@dataclass
class Signal:
    action: str                    # buy | sell
    mint: str
    frac: float = 0.0
    reason: str = ""
    size_sol: float = 0.0


@dataclass
class EntryConfig:
    size_sol: float = 1.02
    size_sol_high_conviction: float = 1.53
    high_conviction_extra_liq: float = 95.0
    mcap_min_usd: float = 2000.0
    mcap_max_usd: float = 8000.0
    liq_to_mcap_min: float = 85.0
    age_min_h: float = 18.0
    age_max_h: float = 72.0
    cooldown_s: float = 1800.0
    max_entries_per_day: int = 6
    max_concurrent: int = 8


@dataclass
class ExitConfig:
    tp1_frac: float = 0.50
    tp1_mult: float = 1.9
    tp2_frac: float = 0.25
    tp2_mult: float = 3.5
    tp3_frac: float = 0.25
    tp3_mult: float = 4.0
    full_exit_mult: float = 1.1        # الحركة المحتشمة → خروج كامل
    slow_exit_mult: float = 1.05
    slow_exit_after_h: float = 8.0
    runner_deadline_tp2_h: float = 36.0
    runner_deadline_tp3_h: float = 60.0
    stop_loss_mult: float = 0.92
    time_stop_h: float = 72.0
    trailing_after_mult: float = 3.5
    trailing_drop_pct: float = 20.0
    rug_liq_drop_pct: float = 50.0


@dataclass
class TokenSnapshot:
    mint: str
    symbol: str = ""
    mcap_usd: float = 0.0
    liq_usd: float = 0.0
    liq_to_mcap_pct: float = 0.0
    age_h: float = 0.0
    pool: str = "pumpswap"


class Strategy:
    def __init__(self, entry: EntryConfig, exit_: ExitConfig):
        self.e = entry
        self.x = exit_

    # ------------------------- الدخول -------------------------
    def entry_score(self, snap: TokenSnapshot) -> float:
        if snap.pool != "pumpswap":
            return 0.0
        if not (self.e.mcap_min_usd <= snap.mcap_usd <= self.e.mcap_max_usd):
            return 0.0
        if snap.liq_to_mcap_pct < self.e.liq_to_mcap_min:
            return 0.0
        if not (self.e.age_min_h <= snap.age_h <= self.e.age_max_h):
            return 0.0
        age_fit = 1.0 - min(abs(snap.age_h - 39.0) / 39.0, 1.0)
        liq_fit = min(snap.liq_to_mcap_pct / 100.0, 1.2)
        return round(age_fit * 0.6 + liq_fit * 0.4, 4)

    def entry_size(self, snap: TokenSnapshot) -> float:
        if snap.liq_to_mcap_pct >= self.e.high_conviction_extra_liq:
            return self.e.size_sol_high_conviction
        return self.e.size_sol

    def want_entry(
        self,
        snap: TokenSnapshot,
        open_count: int,
        last_entry_ts: float,
        entries_today: int,
        now: Optional[float] = None,
    ) -> Optional[Signal]:
        now = now or time.time()
        if self.entry_score(snap) <= 0:
            return None
        if open_count >= self.e.max_concurrent:
            return None
        if entries_today >= self.e.max_entries_per_day:
            return None
        if last_entry_ts and (now - last_entry_ts) < self.e.cooldown_s:
            return None
        return Signal(
            action="buy", mint=snap.mint,
            reason=f"mcap={snap.mcap_usd:.0f} age={snap.age_h:.1f}h liq={snap.liq_to_mcap_pct:.0f}%",
            size_sol=self.entry_size(snap),
        )

    # ------------------------- الخروج -------------------------
    def exit_signal(
        self,
        pos: Position,
        price: float,
        liq_now: Optional[float] = None,
        now: Optional[float] = None,
    ) -> Optional[Signal]:
        now = now or time.time()
        m = pos.mult(price)
        held = pos.held_h(now)
        x = self.x

        # حماية الـ rug
        if liq_now is not None and pos.liq_usd_at_entry > 0:
            if liq_now < pos.liq_usd_at_entry * (1 - x.rug_liq_drop_pct / 100.0):
                return Signal("sell", pos.mint, 1.0, "rug_liq_drop")

        # وقف الخسارة
        if m <= x.stop_loss_mult:
            return Signal("sell", pos.mint, 1.0, f"stop_loss x{m:.2f}")

        if pos.phase == Phase.OPEN:
            if m >= x.tp1_mult:
                return Signal("sell", pos.mint, x.tp1_frac, f"tp1 x{m:.2f}")
            if m >= x.full_exit_mult:
                return Signal("sell", pos.mint, 1.0, f"full_exit x{m:.2f}")
            if held >= x.slow_exit_after_h and m >= x.slow_exit_mult:
                return Signal("sell", pos.mint, 1.0, f"slow_full_exit x{m:.2f}")
            if held >= x.time_stop_h:
                return Signal("sell", pos.mint, 1.0, f"time_stop x{m:.2f} {held:.0f}h")
            return None

        if pos.phase == Phase.TP1:
            if m >= x.tp2_mult:
                return Signal("sell", pos.mint, x.tp2_frac / (1 - x.tp1_frac), f"tp2 x{m:.2f}")
            if held >= x.runner_deadline_tp2_h:
                return Signal("sell", pos.mint, 1.0, f"runner_giveup_tp2 x{m:.2f} {held:.0f}h")
            return None

        if pos.phase == Phase.TP2:
            if m >= x.tp3_mult:
                return Signal("sell", pos.mint, 1.0, f"tp3 x{m:.2f}")
            if pos.peak_mult >= x.trailing_after_mult and m <= pos.peak_mult * (1 - x.trailing_drop_pct / 100.0):
                return Signal("sell", pos.mint, 1.0, f"trailing x{m:.2f} peak x{pos.peak_mult:.2f}")
            if held >= x.runner_deadline_tp3_h:
                return Signal("sell", pos.mint, 1.0, f"runner_giveup_tp3 x{m:.2f} {held:.0f}h")
            return None

        return None


def apply_fill(pos: Position, frac: float, price: float, dust_overhead: float = 0.0) -> float:
    """تنفيذ بيع جزئي على الموضع. يرجع SOL المحقق (صافي)."""
    sold = pos.remaining * frac
    gross = sold * price
    net = max(gross - dust_overhead, 0.0)
    pos.remaining -= sold
    pos.realized_sol += net
    if pos.remaining <= 1e-9 or frac >= 0.999:
        pos.remaining = 0.0
        pos.phase = Phase.CLOSED
    elif pos.phase == Phase.OPEN:
        pos.phase = Phase.TP1
    elif pos.phase == Phase.TP1:
        pos.phase = Phase.TP2
    return net
