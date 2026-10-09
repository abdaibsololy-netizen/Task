# 📦 البيانات الناقصة — شنو تحتاج تجيبها (Google Colab)

أنت معك Colab = إنترنت مفتوح + Python. هذي 4 بيانات، **الأولى ضرورية والباقي ترفع الدقة**.
كل سكربت يطلع ملفات CSV — حمّلها وارفعها للمستودع (`data/`) وأنا أكمّل الباقي.

| # | البيانات | ليش | السكربت | الأولوية |
|---|---|---|---|---|
| 1 | **كامل تاريخ المحفظة** (كل الصفقات بالدقة) | يحل الـ12 صفقة الناقصة + غموض الـ 0.0139 | `collect_wallet.py` | 🔴 ضروري |
| 2 | **سياق الدخول** (سعر العملة حول لحظة شرائه) | نعرف: يشتري هبوط ولا صعود؟ (يحدد توقيت الدخول) | `collect_wallet.py` (قسم B) | 🔴 ضروري |
| 3 | **ملامح التوكن وقت الاختيار** (حالة المحفظة/الديف/الحجم) | يفرّق SARP الرابحة عن GOIF الخاسرة | `collect_wallet.py` (قسم C) | 🟡 مهم |
| 4 | **الكون المضاد** (كل العملات اللي في النطاق وما اشترها) | المصنّف يتعلم "وش يختار" من "وش يترك" | `shadow_collector.py` (3-7 أيام) | 🟡 مهم |

## 🚀 طريقة التشغيل (Colab)

### الخطوة 1 — تاريخ المحفظة (مرة واحدة)
1. افتح Colab جديد ← `Runtime > Run all` بعد لصق السكربت
2. احصل على **مفتاح Helius مجاني** من helius.dev (دقيقة واحدة)
3. الصق المفتاح في خانة `HELIUS_API_KEY` في أول خلية
4. شغّل — يطلع لك 3 ملفات CSV:
   - `wallet_full_history.csv` ← كامل الصفقات (يشمل الناقصة!)
   - `entry_context.csv` ← سياق كل شراء (هبوط/صعود + قوة الحركة)
   - `token_features.csv` ← ملامح كل عملة (holders, dev, volume)

### الخطوة 2 — الكون المضاد (3-7 أيام)
شغّل `shadow_collector.py` في Colab (فعّل auto-reconnect) أو على جهازك:
كل 5 دقائق يسجّل كل عملات pumpswap في نطاق $2–8K — وبعد أسبوع تعرف
**كل العملات اللي ما اشترها** (المقارنة الذهبية للتعلّم).

### الخطوة 3 — ارفع الملفات
ارفع الـ CSVs للمستودع في مجلد `data/` (أو أرسلها لي بالمحادثة) وأنا أكمل:
- ✅ أعرف هل يشتري هبوط ولا موجة صاعدة ← أضبط توقيت الدخول
- ✅ أبني مصنّف الاختيار (holders/dev/volume) ← البوت يختار **نفس ما يختار**
- ✅ أفرّق عائلات SARP عن GOIF ← حظر العائلات الفاشلة مسبقاً

## الملفات المتوقعة (البنية)
```
wallet_full_history.csv : time, signature, type(buy/sell/transfer), mint, symbol,
                          sol_amount, token_amount, price_sol, source
entry_context.csv       : mint, buy_time, price_at_buy, mcap_at_buy,
                          price_h1..h24 (قبل/بعد), trend(dip/pump/flat), dip_pct
token_features.csv      : mint, symbol, buy_time, holder_count, top10_pct,
                          dev_pct, dev_sold, volume_24h, unique_buyers, mcap, liq
universe_snapshot.csv   : ts, mint, symbol, mcap, liq, age_h, volume, holders (من shadow)
```
