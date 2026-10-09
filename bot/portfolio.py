"""إدارة المراكز والحفظ الدائم + مخاطر."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from typing import Dict, List, Optional

from strategy import Phase, Position


class Portfolio:
    def __init__(self, state_file: str = "bot_state.json"):
        self.state_file = state_file
        self.positions: Dict[str, Position] = {}
        self.closed: List[dict] = []
        self.last_entry_ts: float = 0.0
        self.entries_today: int = 0
        self.day_stamp: str = ""
        self.daily_pnl_sol: float = 0.0
        self.load()

    # ---------- persistence ----------
    def load(self) -> None:
        if not os.path.exists(self.state_file):
            return
        with open(self.state_file) as f:
            data = json.load(f)
        for mint, p in data.get("positions", {}).items():
            p["phase"] = Phase(p["phase"])
            self.positions[mint] = Position(**p)
        self.closed = data.get("closed", [])
        self.last_entry_ts = data.get("last_entry_ts", 0.0)
        self.entries_today = data.get("entries_today", 0)
        self.day_stamp = data.get("day_stamp", "")
        self.daily_pnl_sol = data.get("daily_pnl_sol", 0.0)

    def save(self) -> None:
        data = {
            "positions": {m: asdict(p) for m, p in self.positions.items()},
            "closed": self.closed,
            "last_entry_ts": self.last_entry_ts,
            "entries_today": self.entries_today,
            "day_stamp": self.day_stamp,
            "daily_pnl_sol": self.daily_pnl_sol,
        }
        tmp = self.state_file + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    # ---------- day rollover ----------
    def _roll_day(self) -> None:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if today != self.day_stamp:
            self.day_stamp = today
            self.entries_today = 0
            self.daily_pnl_sol = 0.0

    # ---------- operations ----------
    def open_positions(self) -> List[Position]:
        return [p for p in self.positions.values() if p.phase != Phase.CLOSED]

    def open_exposure_sol(self) -> float:
        return sum(p.cost_sol - p.realized_sol for p in self.open_positions())

    def add_entry(self, pos: Position) -> None:
        self._roll_day()
        self.positions[pos.mint] = pos
        self.last_entry_ts = time.time()
        self.entries_today += 1
        self.save()

    def close_if_done(self, pos: Position, exit_price: float) -> Optional[dict]:
        if pos.phase != Phase.CLOSED:
            return None
        pnl = pos.realized_sol - pos.cost_sol
        record = {
            "mint": pos.mint,
            "symbol": pos.symbol,
            "cost_sol": round(pos.cost_sol, 4),
            "realized_sol": round(pos.realized_sol, 4),
            "pnl_sol": round(pnl, 4),
            "held_h": round(pos.held_h(), 1),
            "exit_mult": round(exit_price / pos.entry_price, 3) if pos.entry_price else 0,
            "closed_ts": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        }
        self.closed.append(record)
        self._roll_day()
        self.daily_pnl_sol += pnl
        del self.positions[pos.mint]
        self.save()
        return record


class RiskManager:
    def __init__(self, max_daily_loss_sol: float, max_open_sol: float, max_position_sol: float):
        self.max_daily_loss_sol = max_daily_loss_sol
        self.max_open_sol = max_open_sol
        self.max_position_sol = max_position_sol

    def can_open(self, pf: Portfolio, size_sol: float) -> tuple[bool, str]:
        pf._roll_day()
        if size_sol > self.max_position_sol:
            return False, f"حجم المركز {size_sol} > الحد {self.max_position_sol}"
        if pf.open_exposure_sol() + size_sol > self.max_open_sol:
            return False, "تجاوز الحد الأقصى لرأس المال المعرض"
        if pf.daily_pnl_sol <= -self.max_daily_loss_sol:
            return False, "توقف: تجاوز حد الخسارة اليومي"
        return True, "ok"
