"""
اختبار find_leader من طرف لطرف — **بلا إنترنت**.
نستبدل fetch_txs ببيانات Helius تركيبية، ثم نشغّل main() كاملة ونتأكد أن
القائد يُكتشف ويُرتَّب أولاً. هذا ينفّذ مسار الكود الذي يطبع قائمة القادة فعلاً.
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import find_leader as FL

TARGET = FL.TARGET_WALLET
LEADER_W = "LEAD" + "1" * 40
FOLLOW_W = "FOLL" + "2" * 40
BUNDLE_W = "BUND" + "3" * 40
FUNDER = "FUND" + "9" * 40
POOL = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
MINTS = [f"MINT{i:02d}" + "x" * 30 + "pump" for i in range(5)]
T0 = 1_791_300_000.0
LAM = 1_000_000_000


def swap(sig, ts, slot, trader, mint, side, sol, tokens=1e7):
    if side == "buy":
        tt = {"fromUserAccount": POOL, "toUserAccount": trader,
              "mint": mint, "tokenAmount": tokens}
        nt = [{"fromUserAccount": trader, "toUserAccount": POOL, "amount": int(sol * LAM)}]
    else:
        tt = {"fromUserAccount": trader, "toUserAccount": POOL,
              "mint": mint, "tokenAmount": tokens}
        nt = [{"fromUserAccount": POOL, "toUserAccount": trader, "amount": int(sol * LAM)}]
    return {"signature": sig, "timestamp": ts, "slot": slot, "type": "SWAP",
            "source": "PUMP_AMM", "feePayer": trader,
            "nativeTransfers": nt, "tokenTransfers": [tt]}


def xfer(sig, ts, frm, to, sol):
    return {"signature": sig, "timestamp": ts, "slot": 1, "type": "TRANSFER",
            "source": "SYSTEM_PROGRAM", "feePayer": frm,
            "nativeTransfers": [{"fromUserAccount": frm, "toUserAccount": to,
                                 "amount": int(sol * LAM)}],
            "tokenTransfers": []}


def buy_ts(i):
    return T0 + i * 7200


def fake_fetch_txs(address, max_pages):
    """شبكة وهمية: ترجع ما سيرجعه Helius لكل عنوان."""
    if address == TARGET:
        # الهدف يشتري 5 عملات (بذور) — ويبيعها لاحقاً
        out = [xfer("fund0", T0 - 99999, FUNDER, TARGET, 10.0)]
        for i, m in enumerate(MINTS):
            out.append(swap(f"tb{i}", buy_ts(i), 100 + i, TARGET, m, "buy", 1.02))
            out.append(swap(f"ts{i}", buy_ts(i) + 3600, 200 + i, TARGET, m, "sell", 1.5))
        return out
    if address in MINTS:
        i = MINTS.index(address)
        bt = buy_ts(i)
        return [
            swap(f"lb{i}", bt - 86400, 50 + i, LEADER_W, address, "buy", 2.0),      # قبله بيوم
            swap(f"ls{i}", bt - 86400 + 2 * 86400, 60 + i, LEADER_W, address, "sell", 6.0),
            swap(f"tb{i}", bt, 100 + i, TARGET, address, "buy", 1.02),
            swap(f"ts{i}", bt + 3600, 200 + i, TARGET, address, "sell", 1.5),
            swap(f"ub{i}", bt + 5, 101 + i, BUNDLE_W, address, "buy", 1.5),          # نفس البلوك
            swap(f"us{i}", bt + 5 + 86400, 102 + i, BUNDLE_W, address, "sell", 3.0),
            swap(f"fb{i}", bt + 1800, 150 + i, FOLLOW_W, address, "buy", 1.0),       # بعده
            swap(f"fs{i}", bt + 1800 + 7 * 86400, 151 + i, FOLLOW_W, address, "sell", 1.6),
            swap(f"db{i}", bt + 900, 160 + i, "DUST" + "0" * 40, address, "buy", 0.001),
        ]
    if address == LEADER_W:
        return [xfer("lf", T0 - 999999, FUNDER, LEADER_W, 5.0)]
    if address == BUNDLE_W:
        return [xfer("bf", T0 - 999999, FUNDER, BUNDLE_W, 5.0)]
    return []


def run_pipeline(monkeypatched=True):
    """يشغّل main() كاملة في مجلد مؤقت ويعيد مسارات الملفات."""
    d = tempfile.mkdtemp()
    old_cwd, old_key, old_fetch = os.getcwd(), FL.HELIUS_API_KEY, FL.fetch_txs
    os.chdir(d)
    FL.HELIUS_API_KEY = "test-key"
    FL.fetch_txs = fake_fetch_txs
    try:
        FL.main()
    finally:
        FL.fetch_txs = old_fetch
        FL.HELIUS_API_KEY = old_key
        os.chdir(old_cwd)
    return d


def read(d, name):
    with open(os.path.join(d, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


D = run_pipeline()


def test_insiders_file_has_funder_and_both_roles():
    ins = read(D, "insiders.csv")
    assert {r["wallet"] for r in ins} == {LEADER_W, BUNDLE_W}
    assert all(r["funder"] == FUNDER for r in ins)


def test_pipeline_writes_all_outputs():
    for f in ("cobuys_raw.csv", "candidates_ranked.csv",
              "insiders.csv", "sybil_clusters.csv"):
        assert os.path.exists(os.path.join(D, f)), f


def test_target_and_pool_and_dust_excluded():
    """المجمع والتراب لا يدخلان الملف الخام إطلاقاً؛ الهدف يُستبعد من الترتيب."""
    wallets = {r["wallet"] for r in read(D, "cobuys_raw.csv")}
    assert POOL not in wallets                        # المجمع ليس feePayer أبداً
    assert not any(w.startswith("DUST") for w in wallets)   # 0.001 SOL تحت الحد
    assert TARGET in wallets                          # الخام يشمل صفقاته للتدقيق

    ranked = {r["wallet"] for r in read(D, "candidates_ranked.csv")}
    assert TARGET not in ranked                       # لكنه لا يُرتَّب مع نفسه


def test_leader_detected_and_ranked_first():
    rows = read(D, "candidates_ranked.csv")
    leaders = [r for r in rows if r["role"] == "LEADER"]
    assert leaders, "لم يُكتشف قائد"
    assert leaders[0]["wallet"] == LEADER_W
    assert rows[0]["wallet"] == LEADER_W          # يتصدر الترتيب العام


def test_leader_lead_time_is_one_day_early():
    lead = [r for r in read(D, "candidates_ranked.csv") if r["role"] == "LEADER"][0]
    assert abs(float(lead["lead_s"]) + 86400) < 1        # −24h بالضبط
    assert lead["overlap"] == "5"


def test_leader_roi_is_realised_200pct():
    """اشترى بـ2 وباع بـ6 في 5 عملات → ROI = (30-10)/10 = 200%."""
    lead = [r for r in read(D, "candidates_ranked.csv") if r["role"] == "LEADER"][0]
    assert abs(float(lead["roi"]) - 2.0) < 1e-9
    assert lead["winrate"] == "1.0" and lead["closed"] == "5"
    assert lead["band"] == "hold~2d"


def test_follower_and_bundle_roles_split_correctly():
    roles = {r["wallet"]: r["role"] for r in read(D, "candidates_ranked.csv")}
    assert roles[FOLLOW_W] == "FOLLOWER"
    assert roles[BUNDLE_W] == "BUNDLE"
    assert float(roles and [r for r in read(D, "candidates_ranked.csv")
                            if r["wallet"] == FOLLOW_W][0]["lead_s"]) == 1800.0


def test_leader_outranks_follower_and_bundle():
    rows = read(D, "candidates_ranked.csv")
    s = {r["wallet"]: float(r["score"]) for r in rows}
    assert s[LEADER_W] > s[BUNDLE_W] > s[FOLLOW_W]


def test_sybil_cluster_found():
    """القائد وفريق البلوك مموّلان من نفس العنوان → عنقود سيبيل."""
    cl = read(D, "sybil_clusters.csv")
    assert len(cl) == 1
    assert cl[0]["funder"] == FUNDER
    assert set(cl[0]["wallets"].split("|")) == {LEADER_W, BUNDLE_W}
    assert cl[0]["size"] == "2"


WSOL = FL.SOL_MINT


def _wsol_tx(side):
    """صفقة pump AMM تدفع بـ WSOL فقط، بلا أي تحويل SOL أصلي."""
    trader = "WSOLTRADER" + "w" * 31
    mint = "MINTW" + "x" * 30 + "pump"
    if side == "buy":   # يدفع 1.5 WSOL ويستلم توكن
        tt = [{"mint": mint, "toUserAccount": trader, "tokenAmount": 1000},
              {"mint": WSOL, "fromUserAccount": trader, "tokenAmount": 1.5}]
    else:               # يبيع توكن ويستلم 3 WSOL
        tt = [{"mint": mint, "fromUserAccount": trader, "tokenAmount": 1000},
              {"mint": WSOL, "toUserAccount": trader, "tokenAmount": 3.0}]
    return {"feePayer": trader, "tokenTransfers": tt, "nativeTransfers": [],
            "timestamp": 100, "slot": 1, "signature": "sig"}, mint


def test_wsol_buy_is_counted_not_dropped():
    """الشراء بـ WSOL كان قيمته 0 فيُتجاهل كـ 'تحويل ترابي'. يجب أن يُحسب."""
    tx, mint = _wsol_tx("buy")
    f = FL.parse_fill(tx, mint)
    assert f is not None and f["side"] == "buy"
    assert abs(f["sol"] - 1.5) < 1e-9


def test_wsol_sell_value_is_counted():
    """مبيع يستلم WSOL يجب أن تظهر قيمته، وإلا ROI يصير سالباً زوراً."""
    tx, mint = _wsol_tx("sell")
    f = FL.parse_fill(tx, mint)
    assert f is not None and f["side"] == "sell"
    assert abs(f["sol"] - 3.0) < 1e-9


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
