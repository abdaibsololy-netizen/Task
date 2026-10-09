"""اختبارات كشف الهبوط (Dip) والدخول عند الانهيار."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from market import DipConfig, DipDetector, PriceWindow


def mk_window(prices, start=None, step=10.0):
    w = PriceWindow()
    t = start or (time.time() - len(prices) * step)
    for p in prices:
        t += step
        w.add(t, p)
    return w, t


def test_window_high_low_drawdown():
    w, now = mk_window([1.0, 1.2, 1.5, 1.3, 1.1])
    assert abs(w.high(10, now) - 1.5) < 1e-9
    assert abs(w.low(10, now) - 1.0) < 1e-9 or abs(w.low(10, now) - 1.1) < 1e-9
    dd = w.drawdown_from_high(1.2, 10, now)
    assert abs(dd - (1 - 1.2 / 1.5) * 100) < 1e-6


def test_dip_detected_on_stabilized_dump():
    """هبوط 20% عن القمة + توقف السقوط → دخول."""
    det = DipDetector(DipConfig())
    # قمة 1.5 ثم سقوط لـ 1.15 (−23%) مع تثبيت
    w, now = mk_window([1.0, 1.5, 1.35, 1.2, 1.15, 1.15, 1.15])
    ok, why = det.want_buy(w, 1.15, recent_trades=10, now=now)
    assert ok, why


def test_no_buy_without_dip():
    det = DipDetector(DipConfig())
    w, now = mk_window([1.0, 1.05, 1.1, 1.12, 1.15, 1.16])  # صاعد — لا هبوط
    ok, why = det.want_buy(w, 1.16, recent_trades=10, now=now)
    assert not ok and "لا هبوط" in why


def test_no_buy_falling_knife():
    """ما زال يسقط → لا تمس السكين (بدون تثبيت)."""
    det = DipDetector(DipConfig())
    w, now = mk_window([1.5, 1.4, 1.3, 1.2, 1.1, 1.0])  # سقوط مستمر
    ok, why = det.want_buy(w, 1.0, recent_trades=10, now=now)
    assert not ok and ("يثبت" in why or "يسقط" in why)


def test_no_buy_dead_dump():
    """هبوط > 35% = rug — لا تمس."""
    det = DipDetector(DipConfig())
    w, now = mk_window([1.5, 1.2, 0.95, 0.9, 0.9, 0.9])
    ok, why = det.want_buy(w, 0.9, recent_trades=10, now=now)
    assert not ok and "مميت" in why


def test_no_chase_after_bounce():
    """ارتد عن القاع أكثر من 5% → فات القطار."""
    det = DipDetector(DipConfig())
    # قمة 1.5، قاع 1.2، الآن 1.28 (ارتداد 6.7%)
    w, now = mk_window([1.5, 1.35, 1.2, 1.22, 1.25, 1.28])
    ok, why = det.want_buy(w, 1.28, recent_trades=10, now=now)
    assert not ok and "القطار" in why


def test_no_buy_dead_token():
    """نشاط ضعيف = عملة ميتة."""
    det = DipDetector(DipConfig())
    w, now = mk_window([1.5, 1.3, 1.2, 1.15, 1.15, 1.15])
    ok, why = det.want_buy(w, 1.15, recent_trades=2, now=now)
    assert not ok and "ضعيف" in why


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
