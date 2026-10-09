"""اختبارات قواعد الاستراتيجية — كل قاعدة مستخرجة من البيانات لها اختبار."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strategy import (EntryConfig, ExitConfig, Phase, Position, Strategy,
                      TokenSnapshot, apply_fill)

PX = 1e-6  # سعر الدخول المرجعي


def mk_pos(held_h: float = 1.0) -> Position:
    return Position(mint="M" * 32, symbol="TST", entry_price=PX,
                    tokens=5e7, remaining=5e7, cost_sol=1.02,
                    buy_ts=time.time() - held_h * 3600)


def test_entry_filter():
    s = Strategy(EntryConfig(), ExitConfig())
    good = TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=39)
    assert s.entry_score(good) > 0
    assert s.entry_score(TokenSnapshot(mint="x", mcap_usd=50000, liq_to_mcap_pct=92, age_h=39)) == 0
    assert s.entry_score(TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=60, age_h=39)) == 0
    assert s.entry_score(TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=200)) == 0
    assert s.entry_score(TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=5)) == 0
    a = s.entry_score(TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=39))
    b = s.entry_score(TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=60))
    assert a > b


def test_tp1_half_at_19():
    """وضع الركوب: النصف عند x1.9 (GGMm@x1.91, 6Wbi@x1.97, W7Lj@x2.16)."""
    s = Strategy(EntryConfig(), ExitConfig())
    p = mk_pos(held_h=0.1)
    sig = s.exit_signal(p, price=1.91 * PX)
    assert sig and "tp1" in sig.reason and abs(sig.frac - 0.5) < 1e-9
    # تحت x1.1 ولا تزال مبكراً للركود → لا إشارة
    assert s.exit_signal(mk_pos(held_h=0.1), price=1.08 * PX) is None


def test_full_exit_modest_pop():
    """الحركة المحتشمة x1.1–1.9 → خروج كامل (11 صفقة مرصودة)."""
    s = Strategy(EntryConfig(), ExitConfig())
    sig = s.exit_signal(mk_pos(held_h=0.2), price=1.12 * PX)   # DgrnP
    assert sig and sig.frac == 1.0 and "full_exit" in sig.reason
    sig = s.exit_signal(mk_pos(held_h=4.3), price=1.66 * PX)   # 5iUR
    assert sig and sig.frac == 1.0 and "full_exit" in sig.reason
    assert s.exit_signal(mk_pos(held_h=0.2), price=1.05 * PX) is None


def test_scale_out_ladder():
    """النمط المرصود: 50% → 25% → 25%"""
    s = Strategy(EntryConfig(), ExitConfig())
    p = mk_pos(held_h=1)
    apply_fill(p, 0.5, 2.0 * PX)
    assert p.phase == Phase.TP1 and abs(p.remaining / p.tokens - 0.5) < 1e-9
    sig = s.exit_signal(p, price=3.5 * PX, now=time.time())
    assert sig and "tp2" in sig.reason
    apply_fill(p, sig.frac, 3.5 * PX)
    assert p.phase == Phase.TP2 and abs(p.remaining / p.tokens - 0.25) < 1e-9
    sig = s.exit_signal(p, price=4.2 * PX, now=time.time())
    assert sig and "tp3" in sig.reason and sig.frac == 1.0
    apply_fill(p, sig.frac, 4.2 * PX)
    assert p.phase == Phase.CLOSED


def test_slow_full_exit():
    """الركود: x1.05 بعد 8h → خروج كامل (GkNB@x1.09@10.6h, PUXx@x1.07@24h)."""
    s = Strategy(EntryConfig(), ExitConfig())
    sig = s.exit_signal(mk_pos(held_h=9), price=1.09 * PX)
    assert sig and sig.frac == 1.0 and "slow" in sig.reason
    assert s.exit_signal(mk_pos(held_h=2), price=1.09 * PX) is None


def test_stop_loss():
    s = Strategy(EntryConfig(), ExitConfig())
    sig = s.exit_signal(mk_pos(held_h=3.7), price=0.91 * PX)  # Hv2Un
    assert sig and sig.frac == 1.0 and "stop_loss" in sig.reason


def test_time_stop_dead_bag():
    """الستة 'الأكياس الميتة' كان يمكن تفاديها بإيقاف 72h."""
    s = Strategy(EntryConfig(), ExitConfig())
    sig = s.exit_signal(mk_pos(held_h=73), price=1.00 * PX)
    assert sig and "time_stop" in sig.reason


def test_runner_giveup():
    """الركّاب إذا لم يمتدوا: tY5KS باع الباقي عند 48h بـ x2.41."""
    s = Strategy(EntryConfig(), ExitConfig())
    p = mk_pos(held_h=1)
    apply_fill(p, 0.5, 2.45 * PX)
    p.buy_ts = time.time() - 48 * 3600
    sig = s.exit_signal(p, price=2.41 * PX, now=time.time())
    assert sig and sig.frac == 1.0 and "giveup" in sig.reason


def test_trailing_after_tp2():
    s = Strategy(EntryConfig(), ExitConfig())
    p = mk_pos(held_h=5)
    apply_fill(p, 0.5, 2.23 * PX)   # TP1 (6DWH#1)
    apply_fill(p, 0.5, 3.83 * PX)   # TP2 (6DWH#2)
    p.peak_mult = 3.83
    sig = s.exit_signal(p, price=2.17 * PX, now=time.time())  # 6DWH#3
    assert sig and "trailing" in sig.reason
    assert s.exit_signal(p, price=3.6 * PX, now=time.time()) is None


def test_rug_protection():
    s = Strategy(EntryConfig(), ExitConfig())
    p = mk_pos()
    p.liq_usd_at_entry = 3000
    sig = s.exit_signal(p, price=PX, liq_now=1200)
    assert sig and sig.reason == "rug_liq_drop"


def test_high_conviction_size():
    s = Strategy(EntryConfig(), ExitConfig())
    a = TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=96, age_h=39)
    b = TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=88, age_h=39)
    assert s.entry_size(a) == 1.53 and s.entry_size(b) == 1.02


def test_no_dca_rules():
    s = Strategy(EntryConfig(), ExitConfig())
    snap = TokenSnapshot(mint="x", mcap_usd=4000, liq_to_mcap_pct=92, age_h=39)
    assert s.want_entry(snap, open_count=8, last_entry_ts=0, entries_today=0) is None


def test_config_matches_strategy():
    """ملف config.yaml يجب أن يحمّل بدون تعارض مع ExitConfig."""
    import yaml
    cfg = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "config.yaml")))
    exit_params = {k: v for k, v in cfg["exit"].items() if k != "dust_overhead_sol"}
    EntryConfig(**cfg["entry"])
    ExitConfig(**exit_params)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
