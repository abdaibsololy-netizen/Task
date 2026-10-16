"""
cluster.py — محرك "الصياد الشبحي": من يشتري عملاته ويربح منها؟
================================================================
هذا المحرك **لا يلمس الإنترنت** — يأخذ صفوف صفقات خام (من `data/cobuyer_hunter.py`)
ويستخرج منها المحافظ الشبحية. كل الدوال نقية وقابلة للاختبار (bot/tests/test_cluster.py).

الفرضية التي يفحصها المستخدم: "في محافظ تشتري العملات اللي يشتريها وتربح من وراه."
المحرك لا يفترض الجواب — يقيس **الاتجاه الزمني** ويقرر أيهما يتبع الآخر:

    lead_s = وقت_شراء_المحفظة − وقت_شراء_الهدف

      lead_s <  −60s   → LEADER   : تشتري **قبله** = هو يتبعها (هي المصدر)
      −60s ≤ lead_s ≤ +60s → BUNDLE  : نفس البلوك تقريباً = فريق واحد/منسق
      lead_s >  +60s   → FOLLOWER : تشتري **بعده** = تنسخه (يربح من ورائه فعلاً)

الزوايا غير الاعتيادية المضمّنة (ما لا تعطيه لك شاشة مستكشف البلوكشين):
  1) lead/lag      — ترتيب زمني لكل عملة على حدة، لا مجرد "اشترى نفس العملة"
  2) bundle        — شراءات في نفس الـ slot = فريق الديف/الداخليين
  3) بصمة الحجم    — تكرار نفس حجم الدخول (1.02 SOL) = نفس المشغّل/السكربت
  4) خروج مبكر     — يبيع **قبل** خروجه هو = يفرّغ عليه
  5) مصدر التمويل  — محافظ مموّلة من نفس العنوان = سيبيل واحد بأسماء كثيرة
  6) Jaccard/cosine— قوة التشابه مع سلّته، لا العدد المطلق (يعاقب الحيتان)
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

# ------------------------------ الثوابت --------------------------------------
SOL_MINT = "So11111111111111111111111111111111111111112"

LEADER_EDGE_S = -60.0      # يشتري قبله بأكثر من دقيقة → قائد
BUNDLE_EDGE_S = 60.0       # ± دقيقة → نفس البلوك/حزمة منسقة

# أحزمة الاحتفاظ التي طلبها المستخدم: يوم / يومين / أسبوع
HOLD_BANDS: Tuple[Tuple[str, float, float], ...] = (
    ("scalp<1h", 0.0, 3600.0),
    ("intraday<24h", 3600.0, 24 * 3600.0),
    ("hold~1d", 24 * 3600.0, 48 * 3600.0),
    ("hold~2d", 48 * 3600.0, 7 * 24 * 3600.0),
    ("hold~1w+", 7 * 24 * 3600.0, float("inf")),
)

# أوزان درجة "المال الذكي" — موثقة ومقابلة للاختبار
W_ROI = 0.35
W_OVERLAP = 0.25
W_EDGE = 0.20
W_QUALITY = 0.20
ROI_FULL = 3.0             # 300% ROI = الدرجة الكاملة
OVERLAP_FULL = 5           # 5 عملات مشتركة = الدرجة الكاملة
MIN_CLOSED_FOR_QUALITY = 4


# ------------------------------ النماذج --------------------------------------
@dataclass
class Seed:
    """عملة اشتراها الهدف (نقطة البذرة للبحث)."""
    mint: str
    symbol: str = ""
    master_buy_ts: float = 0.0     # وقت شراء الهدف — أساس قياس الـ lead/lag
    master_sell_ts: float = 0.0    # وقت خروجه — لكشف من يفرّغ عليه
    master_sol: float = 0.0


@dataclass
class Fill:
    """صفقة واحدة على عملة من البذور — من أي محفظة كانت (تشمل الهدف نفسه)."""
    wallet: str
    mint: str
    side: str                      # "buy" | "sell"
    ts: float
    sol: float
    tokens: float = 0.0
    slot: int = 0

    def __post_init__(self) -> None:
        if self.side not in ("buy", "sell"):
            raise ValueError(f"side must be buy/sell, got {self.side!r}")


@dataclass
class WalletStats:
    """النتيجة النهائية لمحفظة مرشحة."""
    wallet: str
    mints: FrozenSet[str] = frozenset()
    overlap: int = 0
    jaccard: float = 0.0
    cosine: float = 0.0
    role: str = "NONE"             # LEADER | BUNDLE | FOLLOWER | NONE
    median_lead_s: float = 0.0
    lead_before: int = 0           # كم عملة اشتراها قبله
    lead_after: int = 0
    lead_bundled: int = 0
    exits_before_master: int = 0   # باع قبل خروجه (تفريغ عليه)
    invested_sol: float = 0.0
    returned_sol: float = 0.0
    realized_pnl_sol: float = 0.0
    realized_roi: float = 0.0
    winrate: float = 0.0
    closed_mints: int = 0
    open_mints: int = 0
    median_hold_s: float = 0.0
    hold_bands: Counter = field(default_factory=Counter)
    entry_sizes: List[float] = field(default_factory=list)
    size_fingerprint: float = 0.0  # نسبة الدخولات المتطابقة مع حجمه المميز
    score: float = 0.0
    bundle_peers: int = 0          # كم محفظة شاركت معه نفس البلوك

    @property
    def dominant_hold_band(self) -> str:
        """أغلب حزمة احتفاظ — يقبل Counter أو dict عادي (الـ dataclass لا يفرض النوع)."""
        if not self.hold_bands:
            return ""
        return max(self.hold_bands.items(), key=lambda kv: kv[1])[0]


# ------------------------------ أدوات مساعدة ---------------------------------
def hold_band(seconds: float) -> str:
    """يصنّف مدة الاحتفاظ في أحزمة: يوم / يومين / أسبوع."""
    for name, lo, hi in HOLD_BANDS:
        if lo <= seconds < hi:
            return name
    return "hold~1w+"


def median(xs: Sequence[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def cosine(a: Iterable[str], b: Iterable[str]) -> float:
    """تشابه جيب التمام على مجموعات — يعاقب الحوت الذي يشتري كل شيء."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / math.sqrt(len(sa) * len(sb))


# ------------------------------ 1) رسم الخرائط -------------------------------
def index_by_wallet(fills: Iterable[Fill]) -> Dict[str, List[Fill]]:
    idx: Dict[str, List[Fill]] = defaultdict(list)
    for f in fills:
        idx[f.wallet].append(f)
    for v in idx.values():
        v.sort(key=lambda f: (f.mint, f.ts))
    return idx


def index_by_mint(fills: Iterable[Fill]) -> Dict[str, List[Fill]]:
    idx: Dict[str, List[Fill]] = defaultdict(list)
    for f in fills:
        idx[f.mint].append(f)
    return idx


# ------------------------------ 2) lead / lag --------------------------------
def classify_role(median_lead_s: float) -> str:
    """من يقود من؟ سالب = يشتري قبله (قائد)، موجب = ينسخه."""
    if median_lead_s <= LEADER_EDGE_S:
        return "LEADER"
    if median_lead_s >= BUNDLE_EDGE_S:
        return "FOLLOWER"
    return "BUNDLE"


def lead_lag(wallet_fills: Sequence[Fill],
             seeds: Dict[str, Seed]) -> Dict[str, float]:
    """لكل عملة مشتركة: وقت شرائه − وقت شرائه هو. يلغي ما لا وقت له."""
    out: Dict[str, float] = {}
    for f in wallet_fills:
        if f.side != "buy":
            continue
        s = seeds.get(f.mint)
        if not s or not s.master_buy_ts:
            continue
        out.setdefault(f.mint, f.ts - s.master_buy_ts)   # أول شراء له
    return out


def exits_before_master(wallet_fills: Sequence[Fill],
                        seeds: Dict[str, Seed]) -> int:
    """كم عملة باعها **قبل** خروج الهدف منها (يفرّغ عليه)."""
    n = 0
    for f in wallet_fills:
        s = seeds.get(f.mint)
        if f.side == "sell" and s and s.master_sell_ts and f.ts < s.master_sell_ts:
            n += 1
    return n


# ------------------------------ 3) PnL والاحتفاظ -----------------------------
def position_pnl(fills: Sequence[Fill]) -> Tuple[float, float, float, float]:
    """
    من صفقات محفظة على عملة واحدة ← (مستثمَر, مسترجَع, مدة_احتفاظ_ث, صافي).
    مدة الاحتفاظ = آخر بيع − أول شراء (0 إذا لم يبع → مركز مفتوح).
    """
    buys = [f for f in fills if f.side == "buy"]
    sells = [f for f in fills if f.side == "sell"]
    invested = sum(f.sol for f in buys)
    returned = sum(f.sol for f in sells)
    if buys and sells:
        hold = max(0.0, max(f.ts for f in sells) - min(f.ts for f in buys))
    else:
        hold = 0.0
    return invested, returned, hold, returned - invested


def wallet_pnl(fills: Sequence[Fill]) -> Dict[str, float]:
    """PnL محقَّق على المراكز **المغلقة فقط** — لا نعدّ الربح الورقي."""
    per_mint: Dict[str, List[Fill]] = defaultdict(list)
    for f in fills:
        per_mint[f.mint].append(f)

    invested = returned = 0.0
    closed = wins = open_mints = 0
    holds: List[float] = []
    for _mint, fs in per_mint.items():
        inv, ret, hold, net = position_pnl(fs)
        invested += inv
        returned += ret
        if any(f.side == "sell" for f in fs):
            closed += 1
            wins += 1 if net > 0 else 0
            holds.append(hold)
        else:
            open_mints += 1
    return {
        "invested": invested,
        "returned": returned,
        "pnl": returned - invested,
        "roi": (returned - invested) / invested if invested > 0 else 0.0,
        "closed": closed,
        "open": open_mints,
        "winrate": wins / closed if closed else 0.0,
        "median_hold": median(holds),
    }


# ------------------------------ 4) حزم منسقة (bundles) -----------------------
def detect_bundles(fills: Iterable[Fill], window_s: float = 2.0) -> Dict[str, List[str]]:
    """
    محافظ تشترك في شراء **نفس العملة داخل نفس النافذة الزمنية** (≈ نفس البلوك).
    هذا أقوى دليل على فريق واحد — لا أحد يصل مصادفةً في نفس الثانية مرتين.
    يعيد {mint: [محافظ الحزمة الأكبر]}.
    """
    by_mint: Dict[str, List[Fill]] = defaultdict(list)
    for f in fills:
        if f.side == "buy":
            by_mint[f.mint].append(f)

    out: Dict[str, List[str]] = {}
    for mint, fs in by_mint.items():
        fs.sort(key=lambda f: f.ts)
        best: List[str] = []
        i = 0
        while i < len(fs):
            j = i
            while j + 1 < len(fs) and fs[j + 1].ts - fs[i].ts <= window_s:
                j += 1
            wallets = sorted({f.wallet for f in fs[i:j + 1]})
            if len(wallets) > len(best):
                best = wallets
            i += 1
        if len(best) >= 2:
            out[mint] = best
    return out


def bundle_peer_count(fills: Iterable[Fill], wallet: str,
                      window_s: float = 2.0) -> int:
    """كم محفظة مختلفة اشتركت مع هذه المحفظة في حزمة زمنية واحدة (عبر كل العملات)."""
    bundles = detect_bundles(fills, window_s)
    peers = set()
    for mint, members in bundles.items():
        if wallet in members:
            peers.update(m for m in members if m != wallet)
    return len(peers)


# ------------------------------ 5) بصمة الحجم --------------------------------
def size_fingerprint(entry_sizes: Sequence[float], target: float,
                     tol: float = 0.05) -> float:
    """نسبة الدخولات المطابقة لحجم الهدف ±tol → نفس المشغّل/السكربت."""
    if not entry_sizes or target <= 0:
        return 0.0
    return sum(1 for s in entry_sizes if abs(s - target) <= tol) / len(entry_sizes)


# ------------------------------ 6) الدرجة المركبة ----------------------------
def score_wallet(s: WalletStats) -> float:
    roi = _clamp(s.realized_roi / ROI_FULL)
    ovl = _clamp(s.overlap / OVERLAP_FULL)
    edge = {"LEADER": 1.0, "BUNDLE": 0.75, "FOLLOWER": 0.3, "NONE": 0.0}[s.role]
    conf = _clamp(s.closed_mints / MIN_CLOSED_FOR_QUALITY)
    qual = s.winrate * conf
    s.score = round(W_ROI * roi + W_OVERLAP * ovl + W_EDGE * edge + W_QUALITY * qual, 4)
    return s.score


# ------------------------------ المحرك الكامل --------------------------------
def analyze(fills: Sequence[Fill],
            seeds: Sequence[Seed],
            target_wallet: str,
            master_size_sol: float = 1.02) -> List[WalletStats]:
    """
    المدخل الرئيسي: صفوف خام + بذور + عنوان الهدف ← قائمة محافظ مرتبة.
    يستثني الهدف نفسه (لا نريد أن نكتشفه هو).
    """
    seed_map = {s.mint: s for s in seeds}
    seed_mints = set(seed_map)
    by_wallet = index_by_wallet(fills)

    out: List[WalletStats] = []
    for wallet, wf in by_wallet.items():
        if wallet == target_wallet:
            continue
        mints = {f.mint for f in wf} & seed_mints
        if not mints:
            continue

        stats = WalletStats(wallet=wallet, mints=frozenset(mints), overlap=len(mints))
        stats.jaccard = round(jaccard(mints, seed_mints), 4)
        stats.cosine = round(cosine(mints, seed_mints), 4)

        leads = lead_lag(wf, seed_map)
        if leads:
            stats.median_lead_s = round(median(list(leads.values())), 1)
            stats.lead_before = sum(1 for v in leads.values() if v <= LEADER_EDGE_S)
            stats.lead_after = sum(1 for v in leads.values() if v >= BUNDLE_EDGE_S)
            stats.lead_bundled = len(leads) - stats.lead_before - stats.lead_after
            stats.role = classify_role(stats.median_lead_s)

        stats.exits_before_master = exits_before_master(wf, seed_map)

        pnl = wallet_pnl(wf)
        stats.invested_sol = round(pnl["invested"], 6)
        stats.returned_sol = round(pnl["returned"], 6)
        stats.realized_pnl_sol = round(pnl["pnl"], 6)
        stats.realized_roi = round(pnl["roi"], 4)
        stats.winrate = round(pnl["winrate"], 4)
        stats.closed_mints = int(pnl["closed"])
        stats.open_mints = int(pnl["open"])
        stats.median_hold_s = round(pnl["median_hold"], 1)

        per_mint: Dict[str, List[Fill]] = defaultdict(list)
        for f in wf:
            per_mint[f.mint].append(f)
        for _m, fs in per_mint.items():
            inv, _ret, hold, _n = position_pnl(fs)
            if any(f.side == "sell" for f in fs):
                stats.hold_bands[hold_band(hold)] += 1
            stats.entry_sizes.append(inv)
        stats.median_hold_s = stats.median_hold_s or 0.0
        stats.size_fingerprint = round(
            size_fingerprint(stats.entry_sizes, master_size_sol), 4)
        score_wallet(stats)
        out.append(stats)

    out.sort(key=lambda s: (-s.score, -s.overlap))
    return out


def filter_smart_money(stats: Sequence[WalletStats],
                       min_overlap: int = 2,
                       bands: Sequence[str] = ("hold~1d", "hold~2d", "hold~1w+"),
                       min_roi: float = 0.0,
                       roles: Optional[Sequence[str]] = None) -> List[WalletStats]:
    """
    الفلتر الذي طلبه المستخدم حرفياً:
    يشتري نفس العملات + يحتفظ يوم/يومين/أسبوع + نسبة ربح عالية.
    """
    keep: List[WalletStats] = []
    for s in stats:
        if s.overlap < min_overlap:
            continue
        if s.dominant_hold_band not in bands:
            continue
        if s.realized_roi < min_roi:
            continue
        if roles and s.role not in roles:
            continue
        keep.append(s)
    return keep


# ------------------------------ مصدر التمويل ---------------------------------
def funding_clusters(first_funder: Dict[str, str],
                     min_wallets: int = 2) -> Dict[str, List[str]]:
    """محافظ مموّلة من نفس العنوان = سيبيل واحد بأسماء كثيرة."""
    groups: Dict[str, List[str]] = defaultdict(list)
    for wallet, funder in first_funder.items():
        if funder:
            groups[funder].append(wallet)
    return {k: sorted(v) for k, v in groups.items() if len(v) >= min_wallets}


# ------------------------------ IO -------------------------------------------
def load_seeds(path: str) -> List[Seed]:
    import csv
    out: List[Seed] = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(Seed(
                mint=r["mint"], symbol=r.get("symbol", ""),
                master_buy_ts=float(r["master_buy_ts"] or 0),
                master_sell_ts=float(r.get("master_sell_ts") or 0),
                master_sol=float(r.get("master_sol") or 0),
            ))
    return out


def load_fills(path: str) -> List[Fill]:
    import csv
    out: List[Fill] = []
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(Fill(
                wallet=r["wallet"], mint=r["mint"], side=r["side"],
                ts=float(r["ts"]), sol=float(r["sol"]),
                tokens=float(r.get("tokens") or 0), slot=int(r.get("slot") or 0),
            ))
    return out


def render_report(stats: Sequence[WalletStats],
                  target_wallet: str,
                  top_n: int = 15) -> str:
    lines = ["=" * 78,
             f"تقرير المحافظ الشبحية — الهدف: {target_wallet}",
             "=" * 78]
    if not stats:
        lines.append("لا توجد بيانات — شغّل data/cobuyer_hunter.py في Colab أولاً.")
        return "\n".join(lines)

    roles = Counter(s.role for s in stats)
    lines.append(f"مرشحون: {len(stats)} | الأدوار: {dict(roles)}")
    lines.append("")
    lines.append(f"{'#':>2} {'المحفظة':<46} {'دور':<9} {'تشابه':>4} {'ROI':>7} "
                 f"{'ربح':>7} {'احتفاظ':<13} {'درجة':>5}")
    lines.append("-" * 108)
    for i, s in enumerate(stats[:top_n], 1):
        lines.append(
            f"{i:>2} {s.wallet:<46} {s.role:<9} {s.overlap:>4} "
            f"{s.realized_roi * 100:>6.0f}% {s.realized_pnl_sol:>7.2f} "
            f"{s.dominant_hold_band:<13} {s.score:>5.2f}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="تحليل المحافظ الشبحية")
    ap.add_argument("--target", required=True, help="عنوان المحفظة الهدف")
    ap.add_argument("--seeds", default="data/seed_mints.csv")
    ap.add_argument("--fills", required=True, help="cobuys_raw.csv من الجامع")
    ap.add_argument("--min-overlap", type=int, default=2)
    ap.add_argument("--min-roi", type=float, default=0.0)
    ap.add_argument("--bands", default="hold~1d,hold~2d,hold~1w+")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()

    seeds = load_seeds(a.seeds)
    fills = load_fills(a.fills)
    all_stats = analyze(fills, seeds, a.target)
    print(render_report(all_stats, a.target, a.top))
    picked = filter_smart_money(all_stats, a.min_overlap,
                               tuple(a.bands.split(",")), a.min_roi)
    print("\n" + "=" * 78)
    print(f"فلتر المستخدم (تشابه≥{a.min_overlap} | احتفاظ {a.bands} | ROI≥{a.min_roi:.0%})")
    print("=" * 78)
    print(render_report(picked, a.target, a.top))
