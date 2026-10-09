"""
family.py — كشف "موجة التيكر" (Ticker-Wave) — سر اختياره المستخرج

النمط المكتشف (analysis/SELECTION_PATTERN.md):
  76% من مشترياته داخل عائلات: توكنات متعددة بنفس التيكر (GOIF×5, DOTF×5, SARP×4).
  المنشئون ينسخون التيكر بمسافات unicode (D O T F) — ونحن نزيل الحيل ونوحّد.

القواعد:
  - توحيد التيكر: إزالة مسافات/حيل unicode + كبر
  - موجة نشطة: ≥ min_members توكنات بنفس التيكر في النطاق خلال wave_window_h
  - حرارة العائلة: عدد الأعضاء × الحداثة (تُستخدم لترتيب المرشحين)
  - حظر العائلة: بعد family_stop_losses خسائر — لا نمسّ الموجة الميتة (GOIF)
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

ZW_CHARS = re.compile(r"[\s\u200a\u200b\u200c\u200d\u2060\u3000]+")


def normalize_symbol(symbol: str) -> str:
    """يوحد التيكر: 'D O T F' → 'DOTF' (يقلب حيل المنشئين)."""
    if not symbol or symbol == "nan":
        return ""
    s = "".join(ch for ch in symbol if unicodedata.category(ch) != "Cf")
    s = ZW_CHARS.sub("", s)
    return s.upper().strip()


@dataclass
class Member:
    mint: str
    symbol: str
    norm: str
    first_seen: float
    mcap_usd: float = 0.0
    age_h: float = 0.0
    in_zone: bool = False          # داخل نطاق المعايير ($2–8K + عمر)


@dataclass
class FamilyTracker:
    wave_window_h: float = 72.0
    min_members: int = 2
    family_stop_losses: int = 2
    members: Dict[str, List[Member]] = field(default_factory=dict)
    losses: Dict[str, int] = field(default_factory=dict)
    wins: Dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def observe(self, mint: str, symbol: str, mcap_usd: float, age_h: float,
                in_zone: bool, now: Optional[float] = None) -> str:
        """يسجل عضواً ويرجع التيكر الموحد."""
        now = now or time.time()
        norm = normalize_symbol(symbol)
        if not norm:
            return ""
        lst = self.members.setdefault(norm, [])
        for m in lst:
            if m.mint == mint:
                m.mcap_usd = mcap_usd
                m.in_zone = in_zone
                return norm
        lst.append(Member(mint, symbol, norm, now, mcap_usd, age_h, in_zone))
        return norm

    def wave_members(self, norm: str, now: Optional[float] = None) -> List[Member]:
        now = now or time.time()
        cutoff = now - self.wave_window_h * 3600
        return [m for m in self.members.get(norm, [])
                if m.first_seen >= cutoff and m.in_zone]

    def family_size(self, norm: str, now: Optional[float] = None) -> int:
        return len(self.wave_members(norm, now))

    def is_wave(self, norm: str, now: Optional[float] = None) -> bool:
        """موجة نشطة = أعضاء كافون في النطاق خلال النافذة."""
        return self.family_size(norm, now) >= self.min_members

    def heat(self, norm: str, now: Optional[float] = None) -> float:
        """حرارة 0–1: عدد الأعضاء + حداثة آخر عضو."""
        now = now or time.time()
        mem = self.wave_members(norm, now)
        if not mem:
            return 0.0
        n_score = min(len(mem) / 4.0, 1.0)                     # 4 أعضاء = حرارة كاملة
        newest = max(m.first_seen for m in mem)
        age_score = max(0.0, 1.0 - (now - newest) / (self.wave_window_h * 3600))
        return round(0.6 * n_score + 0.4 * age_score, 3)

    # ------------------------------------------------------------------
    def mark_result(self, norm: str, won: bool) -> None:
        key = norm or "__none__"
        if won:
            self.wins[key] = self.wins.get(key, 0) + 1
        else:
            self.losses[key] = self.losses.get(key, 0) + 1

    def is_blacklisted(self, norm: str) -> bool:
        """العائلة الميتة: خسر منها family_stop_losses — لا نمسّ موجتها (GOIF)."""
        key = norm or "__none__"
        return self.losses.get(key, 0) >= self.family_stop_losses

    def score(self, norm: str, now: Optional[float] = None) -> float:
        """درجة الاختيار النهائية للعائلة: موجة × حرارة − الحظر."""
        if not norm or self.is_blacklisted(norm):
            return 0.0
        if not self.is_wave(norm, now):
            return 0.15          # فرد منفرد: أضعف بكثير من موجة
        return 0.5 + self.heat(norm, now)   # موجة: 0.5–1.0
