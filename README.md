# Task — PumpBot 🤖

بوت تداول Pump.fun مستقل + نسخة **حزمة فحص أمني** 🔐

| الجزء | الوصف |
|---|---|
| `bot/` | AlphaBot + CopyBot (بوت التداول) — [README](bot/README.md) |
| `data/` | سكربتات جمع بيانات المحفظة (Colab) — [README](data/README.md) |
| `analysis/` | تحليل نمط المتداول واستخراج قواعد الاستراتيجية |
| `security/` | **حزمة الفحص الأمني** — أدوات فحص الموقع المنشور + مراجعة الكود — [README](security/README.md) |

## 🔐 الفحص الأمني (سريع)

```bash
python3 -m venv .venv && .venv/bin/pip install -r security/requirements.txt

# فحص شامل لنظامك المنشور
./security/run_audit.sh https://your-site.com

# إثاق أن الأدوات تعمل (خادم مصاب محلياً)
.venv/bin/python security/selftest.py
```

- تقرير نتائج الكود: [`security/SECURITY_NOTES.md`](security/SECURITY_NOTES.md)
- قالب التقرير: [`security/FINDINGS_TEMPLATE.md`](security/FINDINGS_TEMPLATE.md)
