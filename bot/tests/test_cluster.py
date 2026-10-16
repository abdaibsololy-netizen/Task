"""اختبارات محرك الصياد الشبحي — كل مسار يُختبر ببيانات تركيبية معلومة الجواب."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cluster import (BUNDLE_EDGE_S, LEADER_EDGE_S, Fill, Seed, analyze,
                     bundle_peer_count, classify_role, cosine, detect_bundles,
                     exits_before_master, filter_smart_money, funding_clusters,
                     hold_band, jaccard, lead_lag, median, position_pnl,
                     render_report, score_wallet, size_fingerprint,
                     wallet_pnl, WalletStats)

TARGET = "2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb"
M1 = "1Atst4LcMEYfAXACbCaBpdk166CU8eopNkjyD8jpump"
M2 = "4cYJ8eGZaKMF1iuoUXskhfTHSi6VxL7Jq7xaTJHbpump"
M3 = "5iURQEWL4NcbqhXRnhssfCzhAnghWbEGUoTWiWhpump"
T0 = 1_791_300_000.0


def _seeds():
    return [Seed(mint=M1, symbol="AROS", master_buy_ts=T0, master_sell_ts=T0 + 3600, master_sol=1.02),
            Seed(mint=M2, symbol="DOTF", master_buy_ts=T0 + 7200, master_sell_ts=T0 + 90000, master_sol=1.02),
            Seed(mint=M3, symbol="UDR", master_buy_ts=T0 + 14400, master_sell_ts=0, master_sol=1.53)]


def test_hold_bands_match_user_request():
    """المستخدم طلب: يوم أو يومين أو أسبوع — تحقق الأحزمة."""
    assert hold_band(30 * 60) == "scalp<1h"
    assert hold_band(6 * 3600) == "intraday<24h"
    assert hold_band(25 * 3600) == "hold~1d"
    assert hold_band(50 * 3600) == "hold~2d"
    assert hold_band(9 * 24 * 3600) == "hold~1w+"


def test_classify_role_direction():
    """سالب = يقوده، موجب = يتبعه، حول الصفر = حزمة."""
    assert classify_role(-300) == "LEADER"
    assert classify_role(LEADER_EDGE_S) == "LEADER"
    assert classify_role(0) == "BUNDLE"
    assert classify_role(BUNDLE_EDGE_S) == "FOLLOWER"
    assert classify_role(600) == "FOLLOWER"


def test_median_even_and_odd():
    assert median([5.0]) == 5.0
    assert median([1.0, 3.0]) == 2.0
    assert median([]) == 0.0
    assert median([9.0, 1.0, 5.0]) == 5.0


def test_similarity_penalises_whales():
    """الحوت الذي يشتري 1000 عملة لا يستحق درجة تشابه عالية."""
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard({"a"}, {"z"}) == 0.0
    whale = {f"t{i}" for i in range(1000)} | {"a", "b"}
    assert cosine({"a", "b"}, whale) < 0.05
    assert cosine({"a", "b"}, {"a", "b", "c"}) > 0.7


def test_position_pnl_closed_and_open():
    closed = [Fill("w", M1, "buy", T0, 1.0), Fill("w", M1, "sell", T0 + 86400, 3.0)]
    inv, ret, hold, net = position_pnl(closed)
    assert (inv, ret, hold, net) == (1.0, 3.0, 86400.0, 2.0)

    open_pos = [Fill("w", M1, "buy", T0, 1.0)]
    assert position_pnl(open_pos) == (1.0, 0.0, 0.0, -1.0)


def test_wallet_pnl_ignores_unrealised():
    """الربح المحقَّق فقط — المركز المفتوح لا يرفع ROI."""
    fills = [Fill("w", M1, "buy", T0, 1.0), Fill("w", M1, "sell", T0 + 86400, 3.0),
             Fill("w", M2, "buy", T0, 1.0)]                                  # مفتوح
    p = wallet_pnl(fills)
    assert p["invested"] == 2.0 and p["returned"] == 3.0
    assert p["closed"] == 1 and p["open"] == 1
    assert abs(p["roi"] - 0.5) < 1e-9          # (3-2)/2 لا (3-1)/1
    assert p["winrate"] == 1.0


def test_leader_is_detected_before_target():
    """محفظة تشتري قبله دائماً → LEADER (هو يتبعها، لا العكس)."""
    fills = [Fill("leader", M1, "buy", T0 - 500, 2.0),
             Fill("leader", M1, "sell", T0 - 500 + 86400, 6.0),
             Fill("leader", M2, "buy", T0 + 7200 - 900, 2.0),
             Fill("leader", M2, "sell", T0 + 7200 - 900 + 86400, 7.0)]
    st = analyze(fills, _seeds(), TARGET)[0]
    assert st.wallet == "leader" and st.role == "LEADER"
    assert st.lead_before == 2 and st.lead_after == 0
    assert st.median_lead_s < LEADER_EDGE_S


def test_follower_is_detected_after_target():
    fills = [Fill("copy", M1, "buy", T0 + 600, 1.0),
             Fill("copy", M1, "sell", T0 + 600 + 86400, 2.5),
             Fill("copy", M2, "buy", T0 + 7200 + 1200, 1.0),
             Fill("copy", M2, "sell", T0 + 7200 + 1200 + 86400, 3.0)]
    st = analyze(fills, _seeds(), TARGET)[0]
    assert st.role == "FOLLOWER" and st.lead_after == 2 and st.lead_before == 0


def test_target_excluded_from_results():
    """لا نريد أن نكتشف الهدف نفسه في القائمة."""
    fills = [Fill(TARGET, M1, "buy", T0, 1.02), Fill("other", M1, "buy", T0 + 10, 1.0)]
    wallets = {s.wallet for s in analyze(fills, _seeds(), TARGET)}
    assert wallets == {"other"}


def test_no_overlap_wallets_dropped():
    fills = [Fill("stranger", "ZZZnotaseedpump", "buy", T0, 1.0)]
    assert analyze(fills, _seeds(), TARGET) == []


def test_bundle_detection_same_slot():
    """ثلاث محافظ تشتري نفس العملة في نفس الثانية = فريق واحد."""
    fills = [Fill("a", M1, "buy", T0, 1.0),
             Fill("b", M1, "buy", T0 + 0.5, 1.0),
             Fill("c", M1, "buy", T0 + 1.0, 1.0),
             Fill("d", M1, "buy", T0 + 900, 1.0)]        # لاحق منفرد
    b = detect_bundles(fills, window_s=2.0)
    assert b[M1] == ["a", "b", "c"]
    assert bundle_peer_count(fills, "a") == 2
    assert bundle_peer_count(fills, "d") == 0


def test_bundle_role_assigned():
    fills = [Fill(TARGET, M1, "buy", T0, 1.02),
             Fill("insider", M1, "buy", T0 + 10, 2.0),
             Fill("insider", M1, "sell", T0 + 10 + 86400, 8.0)]
    st = analyze(fills, _seeds(), TARGET)[0]
    assert st.role == "BUNDLE"


def test_size_fingerprint():
    """تكرار 1.02 SOL = نفس المشغّل (بصمته المعروفة من analysis/)."""
    assert size_fingerprint([1.02, 1.02, 1.02], 1.02) == 1.0
    assert size_fingerprint([1.02, 5.0], 1.02) == 0.5
    assert size_fingerprint([1.02], 0) == 0.0
    assert size_fingerprint([], 1.02) == 0.0


def test_exits_before_master_counts_dumps_on_him():
    """يبيع قبل خروجه → يفرّغ عليه."""
    fills = [Fill("w", M1, "buy", T0 - 100, 1.0),
             Fill("w", M1, "sell", T0 + 1800, 2.0)]       # قبل خروجه @T0+3600
    assert exits_before_master(fills, {s.mint: s for s in _seeds()}) == 1
    later = [Fill("w", M1, "sell", T0 + 99999, 2.0)]
    assert exits_before_master(later, {s.mint: s for s in _seeds()}) == 0


def test_funding_clusters_finds_sybils():
    f = {"w1": "FUND", "w2": "FUND", "w3": "OTHER", "w4": ""}
    assert funding_clusters(f) == {"FUND": ["w1", "w2"]}


def test_score_prefers_leader_over_follower():
    """نفس ROI والتشابه — القائد يتفوق على الناسخ."""
    def mk(role):
        s = WalletStats(wallet=role, overlap=5, realized_roi=3.0, winrate=1.0,
                        closed_mints=5, role=role, mints=frozenset({M1}))
        return score_wallet(s)
    assert mk("LEADER") > mk("BUNDLE") > mk("FOLLOWER") > mk("NONE")


def test_score_is_bounded():
    s = WalletStats(wallet="w", overlap=99, realized_roi=99.0, winrate=1.0,
                    closed_mints=99, role="LEADER", mints=frozenset({M1}))
    assert 0.0 <= score_wallet(s) <= 1.0


def test_score_zero_for_empty():
    s = WalletStats(wallet="w", mints=frozenset({M1}))
    assert score_wallet(s) == 0.0


def test_filter_smart_money_user_criteria():
    """الفلتر الحرفي: تشابه≥2 + احتفاظ يوم/يومين/أسبوع + ROI عالٍ."""
    good = WalletStats(wallet="good", overlap=3, realized_roi=2.0, winrate=0.8,
                       closed_mints=3, role="LEADER",
                       hold_bands={"hold~2d": 3})
    scalper = WalletStats(wallet="scalper", overlap=3, realized_roi=2.0,
                          closed_mints=3, hold_bands={"scalp<1h": 3})
    thin = WalletStats(wallet="thin", overlap=1, realized_roi=9.0,
                       closed_mints=3, hold_bands={"hold~1w+": 1})
    broke = WalletStats(wallet="broke", overlap=3, realized_roi=-0.4,
                        closed_mints=3, hold_bands={"hold~1d": 3})
    out = {s.wallet for s in filter_smart_money([good, scalper, thin, broke],
                                                min_overlap=2, min_roi=0.5)}
    assert out == {"good"}


def test_dominant_band_accepts_plain_dict():
    """انحدار: dataclass لا يفرض Counter — dict عادي يجب ألا يكسر الحزمة الغالبة."""
    assert WalletStats(wallet="w", hold_bands={"hold~2d": 3,
                                               "hold~1d": 1}).dominant_hold_band == "hold~2d"
    assert WalletStats(wallet="w").dominant_hold_band == ""


def test_filter_by_role():
    a = WalletStats(wallet="a", overlap=2, realized_roi=1.0, closed_mints=2,
                    role="LEADER", hold_bands={"hold~1d": 2})
    b = WalletStats(wallet="b", overlap=2, realized_roi=1.0, closed_mints=2,
                    role="FOLLOWER", hold_bands={"hold~1d": 2})
    assert {s.wallet for s in filter_smart_money([a, b], roles=("LEADER",))} == {"a"}


def test_full_pipeline_end_to_end():
    """قائد مربح + ناسخ خاسر + غريب ← الترتيب والقيم صحيحة."""
    seeds = _seeds()
    fills = [
        # قائد: يشتري قبله في عملتين، يبيع بعد يومين بربح كبير
        Fill("leader", M1, "buy", T0 - 400, 2.0), Fill("leader", M1, "sell", T0 - 400 + 2 * 86400, 7.0),
        Fill("leader", M2, "buy", T0 + 6900, 2.0), Fill("leader", M2, "sell", T0 + 6900 + 2 * 86400, 6.0),
        # ناسخ: يشتري بعده، يخسر
        Fill("copy", M1, "buy", T0 + 900, 1.0), Fill("copy", M1, "sell", T0 + 900 + 86400, 0.3),
        Fill("copy", M2, "buy", T0 + 9000, 1.0), Fill("copy", M2, "sell", T0 + 9000 + 86400, 0.4),
        # الهدف نفسه — يجب استبعاده
        Fill(TARGET, M1, "buy", T0, 1.02),
    ]
    stats = analyze(fills, seeds, TARGET)
    assert [s.wallet for s in stats] == ["leader", "copy"]

    leader = stats[0]
    assert leader.role == "LEADER" and leader.overlap == 2
    assert abs(leader.realized_roi - 2.25) < 1e-9      # (13-4)/4
    assert leader.dominant_hold_band == "hold~2d"
    assert leader.winrate == 1.0
    assert leader.score > stats[1].score
    assert stats[1].role == "FOLLOWER" and stats[1].realized_roi < 0

    rep = render_report(stats, TARGET)
    assert "leader" in rep and "LEADER" in rep


def test_render_report_handles_empty():
    rep = render_report([], TARGET)
    assert "cobuyer_hunter" in rep


def test_rejects_bad_side():
    try:
        Fill("w", M1, "hold", T0, 1.0)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
