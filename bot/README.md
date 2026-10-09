# PumpBot 🤖

بوتان مبنيان على تحليل محفظة Pump.fun (`master_wallet_*`):

1. **AlphaBot** (`alpha.py`) — بوت **مستقل** يختار العملات بنفس معاييره
   (MCap $2–8K | Liq≥85% | عمر 18–72h) ويدخل **عند الهبوط** — بدون ضريبة النسخ!
2. **CopyBot** (`copytrade.py`) — نسخ مباشر لمحفظته بفلاتر النسخ الآمن.

## 🧠 AlphaBot — البوت الحقيقي (ودّع فيه ويشتغل)

### 1) التركيب
```bash
cd bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) إنشاء المحفظة والتمويل
```bash
# أنشئ مفتاحاً (مرة واحدة) — أو استخدم مفتاحك
python - <<'EOF'
import json, os, base64
# نصيحة: استخدم Solana CLI أو Phantom لتصدير مفتاح جديد
EOF

export PUMPBOT_PRIVATE_KEY="base58-or-json-keypair"   # ⚠️ لا تكتبه في أي ملف!
python -c "import os,json,base64; print('مفتاح موجود ✅' if os.environ.get('PUMPBOT_PRIVATE_KEY') else 'ناقص ❌')"
```
حوّل **SOL** إلى عنوان المحفظة (Phantom/Solflare → Send).  
رأس المال المقترح للبداية: **2–5 SOL** (الحد المعرض مضبوط في `config.yaml`).

### 3) التشغيل
```bash
python tests/test_strategy.py && python tests/test_market.py   # تأكد كل شي أخضر
python main.py                    # 🟢 PAPER — محاكاة حيّة (أسبوع أول)
MODE=live python main.py          # 🔴 LIVE — تداول حقيقي
```
شغّله 24/7 على VPS: `screen -S bot` ثم `python main.py` ثم `Ctrl+A D`.

### كيف يشتغل
1. **الاختيار مثله:** PumpSwap + MCap $2–8K + سيولة ≥85% + عمر 18–72h
2. **الدخول عند الانهيار:** هبوط 5–35% عن قمة الساعة + توقف السقوط + بدون مطاردة
3. **الخروج:** درّاجة 50% @ x1.9 → 25% @ x3.5 → 25% @ x4 (trailing) + وقف −8% + إيقاف 72h
4. **الحماية:** حد خسارة يومي 3 SOL | حد تعرض 10 SOL | بدون DCA أبداً

## 📁 الملفات

| ملف | الدور |
|---|---|
| `alpha.py` | البوت المستقل (اختيار + هبوط + إدارة) |
| `market.py` | نوافذ السعر + كشف الهبوط |
| `strategy.py` | القواعد المشتركة (دخول/خروج) |
| `copytrade.py` | النسخ المباشر الآمن |
| `scanner.py` | تدفق PumpPortal + البيانات الوصفية |
| `executor.py` | تنفيذ paper / live (PumpPortal Trade API) |
| `portfolio.py` | المراكز + الحفظ + المخاطر |
| `safe_copy.py` | محاكاة فلاتر النسخ الآمن |
| `sim_copy.py` | محاكاة النسخ عبر Bloom |
| `backtest.py` | مقارنة القواعد ببياناته |
| `../analysis/` | تقرير النمط + إعدادات Bloom |

## ⚙️ الإعدادات (`config.yaml`)
كل الأرقام من تحليل البيانات — الأهم:
- `entry.size_sol: 1.02` (جرب 0.5 أولاً)
- `alpha.dip.dip_pct: 10` | `max_dip_pct: 35` (لا تمس الانهيار)
- `risk.max_daily_loss_sol: 3` | `risk.max_open_sol: 10`

## ⚠️ ملاحظات أمان
- الوضع الافتراضي **paper**. لا تحوّل لـ live إلا بعد أسبوع محاكاة ناجح.
- المفتاح من متغير البيئة فقط — لا يُكتب في ملفات ولا يُرفع لـ Git.
- البيانات أداء سابق (7 أيام) — لا يضمن نتائج مستقبلية. ابدأ صغيراً.
