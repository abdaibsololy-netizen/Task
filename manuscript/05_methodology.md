# 5. Methodology

> {يجب أن يكون **قابلاً للتكرار ١٠٠٪** — المحكمون يعيدون تنفيذ استعلامك أحياناً.
> Fully reproducible: a reviewer may re-run your search.}

---

## 5.1 تصميم البحث | Research design

{صفّ المنهج (SLR بحسب PRISMA 2020 / Survey / DSR) وسبب اختياره.}

> *"Given the fragmented and fast-moving nature of the literature, a systematic literature review (SLR) was deemed appropriate: it enables …"*

## 5.2 استراتيجية البحث | Search strategy

- **قواعد البيانات Databases:** Scopus, Web of Science, IEEE Xplore, ACM Digital Library, arXiv
- **سلسلة البحث Search string:** (انسخها حرفياً من `literature/search_strings.md` — أو ضعها في Appendix A)
- **الفترة الزمنية Coverage:** 2023–2026
- **اللغة:** English
- **تاريخ آخر بحث Last search date:** {YYYY-MM-DD}

## 5.3 معايير الإدراج والاستبعاد | Inclusion & exclusion

| # | معيار الإدراج Inclusion | معيار الاستبعاد Exclusion |
|---|---|---|
| 1 | يعالج مشكلة AI محددة ويقترح/يقيّم حلاً | يتناول AI بشكل عام |
| 2 | 2023+ | قبل 2023 (إلا المؤسِّسة) |
| 3 | نص كامل متاح | ملخص فقط |
| 4 | مجلة/مؤتمر مفهرس أو preprint عالي التأثير | مدونات/تقارير تسويقية |

## 5.4 الفرز والاستخراج | Screening & extraction

{مرحلتان، مرمّزان، حساب الاتفاق. ثم وصف حقول الاستخراج (المخطط في `literature/README.md`).}

- **الترميز Coding scheme:** أكواد المشاكل `T1–T12` و`O1–O10`، وأكواد الحلول `S1–S12` (انظر §3).
- **جودة الدليل Quality appraisal:** مقياس من ٠ إلى ٥ (وضوح المنهجية، حجم/تمثيل العينة، التقييم الكمّي، التكرار، صلة السؤال).
- **الأداة Tooling:** مستودع Git + `tools/litkit.py` (مفتوح المصدر، قابل للتدقيق).

## 5.5 تحليل البيانات | Analysis

{تحليل وصفي + تحليل موضوعي + مصفوفة مشكلة×حل. اذكر الأدوات والإصدارات.}

## 5.6 مخطط PRISMA | PRISMA flow

{ولّده بـ: `python tools/prisma.py` ثم الصق الجدول/الشكل هنا.}

```
Identification → Screening → Eligibility → Included
      N              n1           n2          n3
```

## 5.7 تهديدات الصلاحية | Validity threats

| النوع | التهديد | التدبير Mitigation |
|---|---|---|
| Internal | تحيز في الترميز | ترميز مزدوج + κ |
| External | تحيز قاعدة البيانات (الإنجليزية فقط) | ٥ قواعد بيانات + arXiv |
| Construct | تعريف فضفاض لـ"الحل" | معيار إدراج صريح |
| Conclusion | الاعتماد على تقارير ذاتية | تقييم قوة الدليل |

## 5.8 الأخلاقيات | Ethics

{لا بيانات بشرية / أو موافقة IRB رقم … يونيو ٢٠٢٦. بيان إفصاح استخدام أدوات الذكاء الاصطناعي.}
