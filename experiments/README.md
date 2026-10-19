# 📊 التجارب والتحليل | Experiments & Analysis

> كل ما هو كمّي في بحثك يوضع هنا — ليكون **قابلاً للتكرار** (reproducibility).
> Everything quantitative lives here so results are **reproducible**.

```
experiments/
├── notebooks/     # تحليل استكشافي + رسوم (Jupyter)
├── scripts/       # سكربتات نهائية قابلة لإعادة التشغيل
├── data/
│   ├── raw/       # بيانات خام (مستثناة من Git — سرية/كبيرة)
│   ├── processed/# بيانات بعد التنظيف (مستثناة من Git)
│   └── external/ # بيانات عامة/مرجعية
└── results/
    ├── figures/   # أشكال للنشر (PNG/PDF بدقة 300+ dpi)
    └── (جداول، مخرجات إحصائية)
```

---

## 🚀 البداية | Getting started

```bash
pip install -r requirements.txt
jupyter lab experiments/notebooks/00_bibliometric_starter.ipynb
```

النوتبوك `00_bibliometric_starter.ipynb` يقرأ `literature/sources.csv` ويخرج:
1. توزيع المصادر بالسنة
2. توزيع أنواع المنشورات
3. أكثر أكواد المشاكل تكراراً
4. خريطة حرارية: مشكلة × حل (أين الحلول مركّزة وأين الفجوة)

---

## 📁 قواعد البيانات | Data rules

| القاعدة | السبب |
|---|---|
| لا ترفع بيانات شخصية إلى `raw/` | السرية والامتثال (`.gitignore` يستثنيها) |
| اكتب وصفاً لكل متغير في `data/README.md` أو في النوتبوك | التوثيق = قابلية التكرار |
| ثبّت العشوائية `random_state=42` | نتائج قابلة للتكرار |
| لا تعدّل `raw/` أبداً — اكتب الناتج في `processed/` | الأثر الكامل (audit trail) |
| سجّل إصدارات المكتبات | `pip freeze > results/requirements_snapshot.txt` |

---

## 🧪 السكربتات | Scripts

- `scripts/` يحتوي مثالاً جاهزاً: `analyze_sources.py` (تحليل سطري بدون مكتبات خارجية).
- أي سكربت جديد: اقبل مسارات كوسائط، واكتب المخرجات إلى `results/`.

```bash
python experiments/scripts/analyze_sources.py \
    --sources literature/sources.csv --outdir experiments/results
```

---

## 📈 مخرجات جاهزة للنشر | Publication-ready outputs

- الأشكال: `results/figures/fig1_year_distribution.png` (٣٠٠ dpi، خطوط مقروءة بعد التصغير).
- الجداول: أنشئها من نفس البيانات (لا تنسخ الأرقام يدوياً إلى الورقة).
- اذكر في المخطوطة: الأداة، الإصدار، والمعاملات المستخدمة.
