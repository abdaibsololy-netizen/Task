"""
PumpBot — التشغيل الرئيسي

الاستخدام:
  python main.py                       # AlphaBot — بوت مستقل (اختيار مثله + دخول عند الهبوط)
  python main.py --mode copy           # وضع النسخ المباشر لمحفظته
  python main.py --backtest            # تشغيل القواعد على البيانات التاريخية
  MODE=live python main.py             # تداول حقيقي (⚠️ خطر — محفظة صغيرة فقط)

التمويل: حوّل SOL إلى عنوان المحفظة (المفتاح في PUMPBOT_PRIVATE_KEY) وشغّل.
"""
from __future__ import annotations

import argparse
import asyncio
import os

import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "config.yaml"))
    ap.add_argument("--mode", choices=["alpha", "copy"], default=None,
                    help="alpha = بوت مستقل (افتراضي) | copy = نسخ محفظته")
    ap.add_argument("--backtest", action="store_true")
    args = ap.parse_args()

    if args.backtest:
        import backtest
        backtest.run()
        return

    cfg = load_config(args.config)
    if args.mode:
        cfg["mode"] = args.mode if cfg.get("mode") != "live" else "live"

    if cfg.get("mode") == "copy" or args.mode == "copy":
        from copytrade import CopyTrader
        bot = CopyTrader(cfg)
    else:
        from alpha import AlphaBot
        bot = AlphaBot(cfg)

    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nإيقاف — الحالة محفوظة")


if __name__ == "__main__":
    main()
