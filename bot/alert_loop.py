"""
حلقة تنبيهات 24/7 — تعمل على GitHub Actions كل 5 دقائق (مجاني للمستودعات العامة)
============================================
تبحث عن فرص الماستر وترسلها لتيليجرام على الجوال:

  الطبقة 1 🌊 موجة العائلة (آخر 4 حروف، ≥2 عملة نشطة)
  الطبقة 2 📏 النطاق (MCap $2-8K | عمر 18-72h | سيولة ≥85%)
  الطبقة 3 ⏱️ الـ wick (اندلاع حجم $50K+ بساعة + انهيار 25-70% + تثبيت عند القاع ±10%)

المصادر (كلها عامة بدون مفتاح): GeckoTerminal للأسعار + DexScreener للروابط.
التنفيذ والخروج: على Bloom (Auto Orders) — هذا السكربت يراقب ويصرخ فقط.

التشغيل محلياً:  python bot/alert_loop.py --selftest   (اختبار المنطق بدون إنترنت)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market import DipConfig, DipDetector, PriceWindow  # noqa: E402

GT = "https://api.geckoterminal.com/api/v2/networks/solana"

# قواعد الماستر (مرآة bot/config.yaml — مكتوبة هنا لتفادي pip install وقت التشغيل)
ZONE = {
    "mcap_min": 2000.0, "mcap_max": 8000.0,
    "age_h_min": 18.0, "age_h_max": 72.0,
    "liq_ratio_min": 0.85,
    "min_h24_buys": 2,
}
FAMILY_SUFFIX_LEN = 4
FAMILY_MIN_MEMBERS = 2
ERUPTION_VOL_60M = 50000.0
ALERT_COOLDOWN_S = 2 * 3600  # لا نزعج نفس العملة كل 5 دقائق
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".alert_state.json")


# ───────────────────────── أدوات ─────────────────────────
def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": "alpha-alert/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def ticker_family(sym: str) -> str:
    s = "".join(c for c in sym.upper() if c.isalnum())
    return s[-FAMILY_SUFFIX_LEN:] if len(s) >= FAMILY_SUFFIX_LEN else s


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st: dict) -> None:
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(st, f)
    except Exception:
        pass


# ───────────────────────── الفحص ─────────────────────────
def fetch_zone_candidates() -> tuple[list[dict], list[dict]]:
    """يرجع (المرشحون في النطاق+موجة، كل المجموعات لحساب حرارة العائلة)."""
    pools: list[dict] = []
    for page in (1, 2):
        try:
            data = get_json(f"{GT}/pools?page={page}&sort=h24_tx_count_desc")
        except Exception as e:
            print(f"! pools page{page}: {e}")
            continue
        for item in data.get("data", []):
            a = item.get("attributes", {})
            name = a.get("name", "")  # "SARP/SOL"
            sym = name.split("/")[0].strip()
            if not sym or "/SOL" not in name:
                continue
            try:
                mcap = float(a.get("market_cap_usd") or a.get("fdv_usd") or 0)
                liq = float(a.get("reserve_in_usd") or 0)
                created = a.get("pool_created_at") or ""
                age_h = (time.time() - time.mktime(time.strptime(created[:19], "%Y-%m-%dT%H:%M:%S"))) / 3600 if created else -1
                tx = (a.get("transactions") or {}).get("h24", {})
                buys = int(tx.get("buys") or 0)
            except Exception:
                continue
            pools.append({
                "sym": sym, "family": ticker_family(sym),
                "addr": item.get("id", ""),  # مثل "solana_8ZMk..."
                "mcap": mcap, "liq": liq, "age_h": age_h, "buys": buys,
            })
    return pools, pools


def in_zone(p: dict) -> bool:
    return (ZONE["mcap_min"] <= p["mcap"] <= ZONE["mcap_max"]
            and ZONE["age_h_min"] <= p["age_h"] <= ZONE["age_h_max"]
            and p["mcap"] > 0 and p["liq"] / p["mcap"] >= ZONE["liq_ratio_min"]
            and p["buys"] >= ZONE["min_h24_buys"])


def family_heats(pools: list[dict]) -> dict[str, int]:
    h: dict[str, int] = {}
    for p in pools:
        h[p["family"]] = h.get(p["family"], 0) + 1
    return h


def check_wick(pool_addr: str) -> tuple[bool, str, dict]:
    """ينزل شموع الدقيقة ويطبق قاعدة الـ wick (نفس DipDetector)."""
    try:
        data = get_json(f"{GT}/pools/{pool_addr}/ohlcv/minute?limit=90")
    except Exception as e:
        return False, f"ohlcv: {e}", {}
    candles = (data.get("data", {}).get("attributes", {}) or {}).get("ohlcv_list", [])
    if len(candles) < 30:
        return False, "بيانات قليلة", {}
    # أقدم → أحدث (شموع دقيقة → نافذة 1200×5ث = ~100 دقيقة)
    candles = list(reversed(candles))
    win = PriceWindow(maxlen=1200)
    vol_60m = 0.0
    live_candles_15m = 0
    now = float(candles[-1][0])
    for ts, o, h, l, c, v in candles:
        win.add(float(ts), float(c))
        if ts >= now - 3600:
            vol_60m += float(v)
        if ts >= now - 900 and float(v) > 0:
            live_candles_15m += 1
    price = float(candles[-1][4])
    det = DipDetector(DipConfig())
    ok, why = det.want_buy(win, price, recent_trades=live_candles_15m, now=now)
    info = {"price": price, "vol_60m": vol_60m,
            "low": win.dip_low(15, now), "high": win.high(15, now)}
    if not ok:
        return False, why, info
    if vol_60m < ERUPTION_VOL_60M:
        return False, f"لا اندلاع (حجم ${vol_60m:,.0f}/ساعة)", info
    return True, why, info


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("[تنبيه — بدون تيليجرام]", text)
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat, "text": text, "parse_mode": "HTML",
                          "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


def build_message(p: dict, why: str, info: dict, heat: int) -> str:
    return (
        "🚨 <b>فرصة الآن</b>\n"
        f"🪙 <b>{p['sym']}</b> (عائلة {p['family']} ×{heat} 🔥)\n"
        f"📊 مcap ${p['mcap']:,.0f} | عمر {p['age_h']:.0f}h | "
        f"سيولة {p['liq']/max(p['mcap'],1)*100:.0f}%\n"
        f"💥 اندلاع حجم ${info.get('vol_60m',0):,.0f} آخر ساعة\n"
        f"📉 {why}\n"
        "👉 <b>اشترِ على Bloom: 0.5 SOL</b> (الأوامر التلقائية تتولى الخروج)\n"
        f"🔗 <a href=\"https://dexscreener.com/solana/{p['addr'].split('_',1)[-1]}\">DexScreener</a>"
    )


# ───────────────────────── الحلقة ─────────────────────────
def run_once() -> int:
    state = load_state()
    pools, allpools = fetch_zone_candidates()
    heats = family_heats(allpools)
    candidates = [p for p in pools if in_zone(p) and heats.get(p["family"], 0) >= FAMILY_MIN_MEMBERS]
    print(f"مفحوصة {len(pools)} | في النطاق+موجة: {len(candidates)}")
    alerts = 0
    for p in candidates[:6]:  # حد 6 فحوص دقيقة لكل تشغيل
        if time.time() - state.get(p["sym"], 0) < ALERT_COOLDOWN_S:
            continue
        ok, why, info = check_wick(p["addr"])
        print(f"  {p['sym']}: {'✅' if ok else '—'} {why}")
        if ok:
            try:
                send_telegram(build_message(p, why, info, heats[p["family"]]))
                state[p["sym"]] = time.time()
                alerts += 1
            except Exception as e:
                print(f"  ! telegram: {e}")
    save_state(state)
    print(f"تنبيهات: {alerts}")
    return alerts


# ───────────────────────── اختبار ذاتي ─────────────────────────
def selftest() -> None:
    import datetime

    def ts(m: int) -> float:
        return (datetime.datetime(2026, 1, 1, 0, 0) + datetime.timedelta(minutes=m)).timestamp()

    # سيناريو: اندلاع ثم wick −38% ثم تثبيت → يجب أن يُعلن
    win = PriceWindow(maxlen=1200)
    path = [1.0] * 10 + [1.2, 1.4, 1.6, 1.5, 1.3, 1.1, 1.0, 1.0, 1.0]
    for i, p in enumerate(path):
        win.add(ts(i), p)
    det = DipDetector(DipConfig())
    ok, why = det.want_buy(win, 1.0, recent_trades=8, now=ts(len(path)))
    assert ok, f"كان متوقعاً ✅ لكن: {why}"
    # سيناريو ميت: انهيار 75% → رفض
    win2 = PriceWindow(maxlen=1200)
    for i, p in enumerate([1.5, 1.4, 1.2, 0.9, 0.5, 0.38, 0.37, 0.37]):
        win2.add(ts(i), p)
    ok2, why2 = det.want_buy(win2, 0.37, recent_trades=8, now=ts(8))
    assert not ok2 and "مميت" in why2, why2
    # حرارة العائلة
    heats = family_heats([
        {"family": "SARP"}, {"family": "SARP"}, {"family": "SARP"}, {"family": "ZSOL"}])
    assert heats["SARP"] == 3 and heats["ZSOL"] == 1
    # النطاق
    assert in_zone({"mcap": 3000, "liq": 2700, "age_h": 24, "buys": 10})
    assert not in_zone({"mcap": 3000, "liq": 2700, "age_h": 5, "buys": 10})   # صغير
    assert not in_zone({"mcap": 20000, "liq": 18000, "age_h": 24, "buys": 10})  # كبير
    assert not in_zone({"mcap": 3000, "liq": 1500, "age_h": 24, "buys": 10})   # سيولة ضعيفة
    print("✅ selftest: منطق التنبيهات سليم")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run_once()
