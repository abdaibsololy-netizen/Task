"""
الماسح — تدفق PumpPortal الحقيقي + بيانات العملة (العمر/السيولة).
- WS: wss://pumpportal.fun/api/data  (مجاني، بدون مفتاح)
  * subscribeNewToken  → عملات جديدة
  * subscribeTokenTrade → تداولات عملة محددة (للخروج)
- بيانات وصفية: pump.fun / birdeye (العمر والماركت كاب بالدولار)

في وضع paper يعمل التدفق نفسه؛ التنفيذ وهمي.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Awaitable, Callable, Optional

import aiohttp

from strategy import TokenSnapshot

PUMPFUN_COIN_API = "https://frontend-api.pump.fun/coins/{mint}"


class PumpPortalStream:
    def __init__(self, ws_url: str, on_trade: Callable[[dict], Awaitable[None]]):
        self.ws_url = ws_url
        self.on_trade = on_trade
        self._ws = None

    async def run(self) -> None:
        """اتصال دائم مع إعادة محاولة."""
        while True:
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.ws_connect(self.ws_url, heartbeat=30) as ws:
                        self._ws = ws
                        await ws.send_json({"method": "subscribeNewToken"})
                        async for msg in ws:
                            if msg.type != aiohttp.WSMsgType.TEXT:
                                break
                            data = json.loads(msg.data)
                            await self.on_trade(data)
            except Exception as e:  # noqa: BLE001
                print(f"[stream] انقطع الاتصال: {e} — إعادة خلال 5s")
                await asyncio.sleep(5)

    async def subscribe_trades(self, mint: str) -> None:
        if self._ws is not None:
            await self._ws.send_json({"method": "subscribeTokenTrade", "keys": [mint]})


class MetadataFetcher:
    """عمر العملة والماركت كاب — من pump.fun API (مع fallback)."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.cache: dict[str, tuple[float, dict]] = {}

    async def coin(self, mint: str, ttl: float = 120.0) -> Optional[dict]:
        hit = self.cache.get(mint)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        try:
            async with self.session.get(PUMPFUN_COIN_API.format(mint=mint), timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                self.cache[mint] = (time.time(), data)
                return data
        except Exception:  # noqa: BLE001
            return None

    async def snapshot(self, mint: str, live_mcap_sol: float, sol_price: float) -> Optional[TokenSnapshot]:
        c = await self.coin(mint)
        if not c:
            return None
        created = c.get("created_timestamp") or c.get("createdTimestamp") or 0
        age_h = (time.time() * 1000 - created) / 3.6e6 if created else 0.0
        mcap = float(c.get("usd_market_cap") or c.get("market_cap") or 0) or live_mcap_sol * sol_price
        liq = float(c.get("virtual_sol_reserves", 0)) * sol_price * 2 if c.get("virtual_sol_reserves") else mcap * 0.92
        liq_pct = (liq / mcap * 100) if mcap else 0.0
        return TokenSnapshot(
            mint=mint,
            symbol=c.get("symbol", "") or "",
            mcap_usd=mcap,
            liq_usd=liq,
            liq_to_mcap_pct=liq_pct,
            age_h=age_h,
            pool="pumpswap" if (c.get("raydium_pool") or mcap > 0) else "pump",
        )


def parse_trade_event(msg: dict) -> Optional[dict]:
    """يحوّل رسالة PumpPortal إلى حدث موحد."""
    if not isinstance(msg, dict):
        return None
    tx_type = msg.get("txType")
    mint = msg.get("mint")
    if tx_type not in ("buy", "sell") or not mint:
        return None
    return {
        "mint": mint,
        "side": tx_type,
        "sol_amount": float(msg.get("solAmount") or 0),
        "token_amount": float(msg.get("tokenAmount") or 0),
        "market_cap_sol": float(msg.get("marketCapSol") or 0),
        "ts": float(msg.get("timestamp") or time.time()),
    }
