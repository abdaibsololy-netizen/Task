"""
اختبارات محللات cobuyer_hunter — بأشكال معاملات Helius الحقيقية.
لا يحتاج إنترنت: نغذّي المحللات JSON مطابقاً لما يرجعه Helius Enhanced Transactions.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cobuyer_hunter as H

MINT = "1Atst4LcMEYfAXACbCaBpdk166CU8eopNkjyD8jpump"
BUYER = "7iVCXQn4u6tiTEfNVqbWSEsRdEi69E9oYsSMiepuECwi"
POOL = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
FUNDER = "Gmeap2HJ8SHsCRZAAaNU8JvC3mfienyAeGrLtkjWKVTX"
LAM = 1_000_000_000


def swap_tx(sig, ts, slot, wallet, mint, side, sol, tokens):
    """يبني معاملة Helius Enhanced بشكلها الحقيقي."""
    if side == "buy":
        tt = {"fromUserAccount": POOL, "toUserAccount": wallet,
              "mint": mint, "tokenAmount": tokens}
        nt = [{"fromUserAccount": wallet, "toUserAccount": POOL, "amount": int(sol * LAM)}]
    else:
        tt = {"fromUserAccount": wallet, "toUserAccount": POOL,
              "mint": mint, "tokenAmount": tokens}
        nt = [{"fromUserAccount": POOL, "toUserAccount": wallet, "amount": int(sol * LAM)}]
    return {"signature": sig, "timestamp": ts, "slot": slot, "type": "SWAP",
            "source": "PUMP_AMM", "feePayer": wallet,
            "nativeTransfers": nt, "tokenTransfers": [tt]}


def transfer_tx(sig, ts, frm, to, sol):
    return {"signature": sig, "timestamp": ts, "slot": 1, "type": "TRANSFER",
            "source": "SYSTEM_PROGRAM", "feePayer": frm,
            "nativeTransfers": [{"fromUserAccount": frm, "toUserAccount": to,
                                 "amount": int(sol * LAM)}],
            "tokenTransfers": []}


# ------------------------------------------------------------------ parse_fills
def test_buy_direction_and_amounts():
    tx = swap_tx("sig1", 1_791_300_000, 273417702, BUYER, MINT, "buy", 1.02, 5e7)
    fills = H.parse_fills(tx, MINT)
    assert len(fills) == 1
    w, side, sol, tok, ts, slot, sig = fills[0]
    assert (w, side, sig) == (BUYER, "buy", "sig1")
    assert abs(sol - 1.02) < 1e-9 and tok == 5e7
    assert ts == 1_791_300_000 and slot == 273417702


def test_sell_direction():
    tx = swap_tx("sig2", 1_791_390_000, 273500000, BUYER, MINT, "sell", 2.4, 5e7)
    fills = H.parse_fills(tx, MINT)
    assert len(fills) == 1 and fills[0][1] == "sell"
    assert abs(fills[0][2] - 2.4) < 1e-9


def test_amm_pool_is_not_a_trader():
    """انحدار: مجمع السيولة يقابل كل شراء — يجب ألا يظهر كمتداول إطلاقاً."""
    tx = {"signature": "s", "timestamp": 1, "slot": 9, "feePayer": BUYER,
          "nativeTransfers": [{"fromUserAccount": BUYER, "toUserAccount": POOL,
                               "amount": int(1.02 * LAM)}],
          "tokenTransfers": [{"fromUserAccount": POOL, "toUserAccount": BUYER,
                              "mint": MINT, "tokenAmount": 100.0}]}
    fills = H.parse_fills(tx, MINT)
    assert [f[0] for f in fills] == [BUYER]        # لا POOL في النتيجة
    assert fills[0][1] == "buy" and abs(fills[0][2] - 1.02) < 1e-9


def test_no_feepayer_yields_nothing():
    tx = {"signature": "s", "timestamp": 1, "slot": 1,
          "nativeTransfers": [], "tokenTransfers": []}
    assert H.parse_fills(tx, MINT) == []


def test_sell_sol_is_proceeds_not_fee():
    """في البيع: نعدّ SOL الداخل له فقط — لا الرسوم التي يدفعها."""
    tx = {"signature": "s", "timestamp": 1, "slot": 1, "feePayer": BUYER,
          "nativeTransfers": [
              {"fromUserAccount": POOL, "toUserAccount": BUYER, "amount": int(2.4 * LAM)},
              {"fromUserAccount": BUYER, "toUserAccount": "TREASURY", "amount": int(0.01 * LAM)}],
          "tokenTransfers": [{"fromUserAccount": BUYER, "toUserAccount": POOL,
                              "mint": MINT, "tokenAmount": 100.0}]}
    fills = H.parse_fills(tx, MINT)
    assert fills[0][1] == "sell" and abs(fills[0][2] - 2.4) < 1e-9



def test_other_mint_ignored():
    tx = swap_tx("sig3", 1, 1, BUYER, "OTHERmintpump", "buy", 1.0, 100.0)
    assert H.parse_fills(tx, MINT) == []


def test_zero_amount_skipped():
    tx = swap_tx("sig4", 1, 1, BUYER, MINT, "buy", 1.0, 0.0)
    assert H.parse_fills(tx, MINT) == []


# ------------------------------------------------------- wallet_buys_from_history
def test_history_extracts_token_buys_only():
    txs = [swap_tx("a", 100, 1, BUYER, MINT, "buy", 1.02, 1e7),
           swap_tx("b", 200, 2, BUYER, MINT, "sell", 2.0, 1e7)]
    buys = H.wallet_buys_from_history(txs)
    assert buys == [(MINT, 100.0, 1.02)]        # البيع لا يُعد شراءً


def test_history_skips_native_sol_transfers():
    txs = [transfer_tx("t", 50, FUNDER, BUYER, 8.0)]
    assert H.wallet_buys_from_history(txs) == []


def test_history_skips_received_sol():
    """استلام SOL ليس شراء توكن (فخ شائع في التحليل)."""
    tx = {"signature": "x", "timestamp": 1, "slot": 1, "feePayer": POOL,
          "nativeTransfers": [{"fromUserAccount": POOL, "toUserAccount": BUYER,
                               "amount": int(2.4 * LAM)}],
          "tokenTransfers": [{"fromUserAccount": BUYER, "toUserAccount": POOL,
                              "mint": H.SOL_MINT, "tokenAmount": 0.0024}]}
    assert H.wallet_buys_from_history([tx]) == []


# ------------------------------------------------------------------ first_funder
def test_first_funder_is_earliest_sender():
    txs = [transfer_tx("l", 300, "LATE", BUYER, 5.0),
           transfer_tx("f", 100, FUNDER, BUYER, 8.0),
           transfer_tx("m", 200, "MID", BUYER, 3.0)]
    assert H.first_funder(txs) == FUNDER


def test_first_funder_ignores_dust():
    txs = [transfer_tx("d", 100, "DUSTSENDER", BUYER, 0.000005),
           transfer_tx("r", 200, FUNDER, BUYER, 6.0)]
    assert H.first_funder(txs) == FUNDER


def test_first_funder_empty_history():
    assert H.first_funder([]) == ""


# ------------------------------------------------------------------ استئناف
def test_append_and_resume(tmp=None):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "cobuys_raw.csv")
    rows = [{"wallet": "w1", "mint": MINT, "side": "buy", "ts": 1,
             "sol": 1.02, "tokens": 100.0, "slot": 1, "signature": "sig1"}]
    H.append_rows(p, H.FILL_FIELDS, rows)
    assert H.seen_signatures(p) == {"sig1"}
    H.append_rows(p, H.FILL_FIELDS, rows + [{**rows[0], "signature": "sig2"}])
    assert H.seen_signatures(p) == {"sig1", "sig2"}
    with open(p, encoding="utf-8") as fh:
        assert sum(1 for _ in fh) == 4          # ترويسة + 3 صفوف (لا ترويسة مكررة)


def test_seen_signatures_missing_file():
    assert H.seen_signatures("/nonexistent/nope.csv") == set()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"\n{len(fns)} اختبار ناجح")
