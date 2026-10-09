"""اختبارات موجة التيكر — سر الاختيار (76% من مشترياته في عائلات)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from family import FamilyTracker, normalize_symbol


def test_normalize_strips_unicode_tricks():
    """حيلة المنشئين: 'D O T F' بمسافات خفية → 'DOTF'."""
    assert normalize_symbol("D O T F") == "DOTF"
    assert normalize_symbol("DOTF") == "DOTF"
    assert normalize_symbol("d\u200ao\u200bt\u200bf") == "DOTF"  # zero-width
    assert normalize_symbol("SARP") == "SARP"
    assert normalize_symbol("") == ""
    assert normalize_symbol("nan") == ""


def test_wave_detection():
    """موجة = توكنان+ بنفس التيكر في النطاق خلال 72 ساعة (SARP×4 في بياناته)."""
    ft = FamilyTracker(min_members=2, wave_window_h=72)
    now = time.time()
    ft.observe("m1", "SARP", 4000, 30, True, now - 48 * 3600)
    assert not ft.is_wave("SARP", now)          # فرد واحد = لا موجة بعد
    ft.observe("m2", "SARP", 3500, 40, True, now - 10 * 3600)
    assert ft.is_wave("SARP", now)              # ✅ موجة
    assert ft.family_size("SARP", now) == 2


def test_wave_expires():
    """الموجة القديمة تموت (كل الأعضاء خارج النافذة)."""
    ft = FamilyTracker(min_members=2, wave_window_h=72)
    now = time.time()
    ft.observe("m1", "GOIF", 4000, 30, True, now - 100 * 3600)
    ft.observe("m2", "GOIF", 4000, 30, True, now - 90 * 3600)
    assert not ft.is_wave("GOIF", now)


def test_out_of_zone_members_dont_count():
    """العضو خارج النطاق (MCap/عمر) لا يحسب في الموجة."""
    ft = FamilyTracker(min_members=2, wave_window_h=72)
    now = time.time()
    ft.observe("m1", "DOTF", 4000, 30, True, now - 5 * 3600)
    ft.observe("m2", "DOTF", 50000, 30, False, now - 5 * 3600)   # خارج النطاق
    assert not ft.is_wave("DOTF", now)


def test_family_blacklist_after_losses():
    """GOIF ماتت 4 من 6 — احظر العائلة بعد خسارتين."""
    ft = FamilyTracker(family_stop_losses=2)
    ft.mark_result("GOIF", won=False)
    ft.mark_result("GOIF", won=False)
    assert ft.is_blacklisted("GOIF")
    assert ft.score("GOIF") == 0.0


def test_wave_scores_higher_than_single():
    """الموجة تتفوق على الفرد المنفرد (SARP الموجية vs USDP المنفردة)."""
    ft = FamilyTracker(min_members=2, wave_window_h=72)
    now = time.time()
    ft.observe("m1", "SARP", 4000, 30, True, now - 2 * 3600)
    ft.observe("m2", "SARP", 4000, 30, True, now - 1 * 3600)
    ft.observe("m3", "USDP", 4000, 30, True, now - 1 * 3600)
    assert ft.score("SARP", now) > 0.5
    assert ft.score("USDP", now) < 0.3


def test_unicode_clones_same_family():
    """'D O T F' و'DOTF' نفس العائلة — يركبان نفس الموجة."""
    ft = FamilyTracker(min_members=2, wave_window_h=72)
    now = time.time()
    ft.observe("m1", "DOTF", 4000, 30, True, now - 20 * 3600)
    ft.observe("m2", "D O T F", 3800, 25, True, now - 5 * 3600)
    assert ft.is_wave("DOTF", now)
    assert ft.family_size("DOTF", now) == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
