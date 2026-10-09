"""
market.py — متابعة السوق اللحظية + كشف "الهبوط" (Dip) للدخول
منطق نقي بدون شبكة — قابل للاختبار.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional, Tuple


@dataclass
class PriceWindow:
    """نافذة أسعار متحركة (ts, price) — تُغذّى من تدفق التداولات."""
    maxlen: int = 720                      # ~ساعة عند صفقة/5 ثواني
    ticks: Deque[Tuple[float, float]] = field(default_factory=deque)
    window_high: float = 0.0
    window_low: float = 1e18
    last_ts: float = 0.0

    def add(self, ts: float, price: float) -> None:
        if price <= 0:
            return
        self.ticks.append((ts, price))
        while self.ticks and ts - self.ticks[0][0] > self._span_s:
            self.ticks.popleft()
        self.last_ts = ts

    @property
    def _span_s(self) -> float:
        return self.maxlen * 5

    def high(self, minutes: float, now: Optional[float] = None) -> float:
        now = now or (self.last_ts or time.time())
        cutoff = now - minutes * 60
        vals = [p for t, p in self.ticks if t >= cutoff]
        return max(vals) if vals else 0.0

    def low(self, minutes: float, now: Optional[float] = None) -> float:
        now = now or (self.last_ts or time.time())
        cutoff = now - minutes * 60
        vals = [p for t, p in self.ticks if t >= cutoff]
        return min(vals) if vals else 0.0

    def drawdown_from_high(self, price: float, minutes: float, now: Optional[float] = None) -> float:
        """نسبة الهبوط عن قمة النافذة (موجب = هابط)."""
        h = self.high(minutes, now)
        return (1 - price / h) * 100 if h > 0 else 0.0

    def stabilized(self, n: int = 2) -> bool:
        """التوقف عن السقوط: آخر n حركات صاعدة أو مستقرة."""
        if len(self.ticks) < n + 1:
            return False
        recent = [p for _, p in list(self.ticks)[-(n + 1):]]
        return all(recent[i + 1] >= recent[i] * 0.999 for i in range(n))

    def dip_low(self, minutes: float, now: Optional[float] = None) -> float:
        """قاع الهبوط = أدنى سعر بعد قمة النافذة (مو من قبل الصعود)."""
        now = now or (self.last_ts or time.time())
        cutoff = now - minutes * 60
        vals = [(t, p) for t, p in self.ticks if t >= cutoff]
        if not vals:
            return 0.0
        peak_t = max(vals, key=lambda x: x[1])[0]
        after = [p for t, p in vals if t >= peak_t]
        return min(after) if after else 0.0

    def bounced_from_low(self, price: float, minutes: float, now: Optional[float] = None) -> float:
        """كم ارتد السعر عن قاع الهبوط (موجب = ارتد)."""
        lo = self.dip_low(minutes, now)
        return (price / lo - 1) * 100 if lo > 0 else 0.0


@dataclass
class DipConfig:
    lookback_min: float = 60.0      # نافذة القمة
    dip_pct: float = 10.0           # الهبوط المطلوب عن القمة
    min_dip_pct: float = 5.0        # أدنى هبوط (لا نشتري "هبوط" وهمي)
    max_dip_pct: float = 35.0       # فوق كذا = انهيار/rug — لا تمسّه
    confirm_ticks: int = 2          # تثبيت: آخر حركتين مستقرتين
    bounce_limit_pct: float = 5.0   # لا تطارد إذا ارتد عن القاع
    min_activity_trades: int = 5    # تداولات كافية في آخر 30 دقيقة (حياة)
    activity_window_min: float = 30.0


class DipDetector:
    """قرار الدخول عند الهبوط — نفس منطق 'يشتري عند الانهيار'."""

    def __init__(self, cfg: DipConfig):
        self.c = cfg

    def want_buy(self, win: Optional[PriceWindow], price: float,
                 recent_trades: int, now: Optional[float] = None) -> Tuple[bool, str]:
        if win is None or len(win.ticks) < 5:
            return False, "بيانات ناقصة"
        now = now or time.time()

        # 1) فلتر الحياة: نشاط تداول كافٍ
        if recent_trades < self.c.min_activity_trades:
            return False, f"نشاط ضعيف ({recent_trades} صفقة)"

        # 2) الهبوط عن القمة
        dd = win.drawdown_from_high(price, self.c.lookback_min, now)
        if dd < self.c.min_dip_pct:
            return False, f"لا هبوط كافٍ ({dd:.1f}%)"
        if dd > self.c.max_dip_pct:
            return False, f"هبوط مميت ({dd:.1f}%) — لا نمسّ الانهيار"

        # 3) التثبيت (السقوط توقف)
        if not win.stabilized(self.c.confirm_ticks):
            return False, "ما زال يسقط — لا تمس السكين"

        # 4) لا مطاردة: إذا ارتد كثيراً عن القاع تخطَّ
        bounce = win.bounced_from_low(price, self.c.lookback_min, now)
        if bounce > self.c.bounce_limit_pct:
            return False, f"ارتد {bounce:.1f}% عن القاع — فات القطار"

        return True, f"هبوط {dd:.1f}% + تثبيت + ارتداد {bounce:.1f}%"
