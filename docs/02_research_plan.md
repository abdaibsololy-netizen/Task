# 🗓️ الخطة الزمنية | Research Plan (9 months)

> عدّل التواريخ حسب تقويمك الجامعي. كل شهر له **مخرج واحد واضح** تضعه في ملف.
> Adjust dates to your academic calendar. Each month has **one concrete deliverable**.

| # | الشهر Month | الهدف Goal | المخرج Deliverable | أداة المستودع Tool |
|---|---|---|---|---|
| 1 | M1 | تحديد الموضوع + السؤال + الفجوة الأولية | `docs/01_topic_selection.md` مكتمل + بروتوكول بحث | `litkit.py add` (20 مصدراً أولياً) |
| 2 | M2 | بناء استراتيجية البحث وتنفيذها | `literature/search_strings.md` + `screening_log.csv` | `prisma.py` |
| 3 | M3 | الفرز (title/abstract) والاستخراج | `literature/sources.csv` مكتمل (٤٠–٦٠ ورقة مستخرجة) | `validate_sources.py` |
| 4 | M4 | التحليل الموضوعي + مصفوفة المشكلة↔الحل | `literature/problem_solution_matrix.md` | `litkit.py gaps` |
| 5 | M5 | التحليل الكمّي/الببليومتري | `experiments/notebooks/` + أشكال في `results/figures/` | Jupyter |
| 6 | M6 | المسودة الأولى للمخطوطة | `manuscript/01…08` (مسودة كاملة ولو ضعيفة) | `docs/04_writing_guide.md` |
| 7 | M7 | مراجعة المشرف + تحسين الحجة + فحص المراجع | نسخة v2 + `references/references.bib` نظيف | `validate_sources.py` |
| 8 | M8 | تجهيز الإرسال | `submission/` كامل (خطاب + قائمة مجلات + تشيك ليست) | `docs/05_publishing_guide.md` |
| 9 | M9 | الإرسال + الاستجابة للتحكيم | رسالة إرسال + (لاحقاً) `response_to_reviewers.md` | — |

---

## ⏱️ توزيع الوقت الأسبوعي | Weekly rhythm (10–12 h/week)

```
3 h   قراءة واستخراج (ورقتان إلى ثلاث أوراق)   → literature/sources.csv
2 h   كتابة (٥٠٠ كلمة/أسبوع = ٦٠٠٠ كلمة في ٣ أشهر)
2 h   تنظيم المستودع وتشغيل الأدوات            → tools/
2 h   اجتماع/مراجعة مع المشرف
1 h   متابعة جديد المجال (arXiv alerts, Google Scholar alerts)
```

> **قاعدة الـ٥٠٠ كلمة | The 500-word rule:** اكتب ٥٠٠ كلمة أسبوعياً بلا استثناء — أهم من أي جلسة "إلهام".

---

## 🚨 نقاط فشل شائعة | Common failure points

| الخطر Risk | العلامة المبكرة | التدبير Mitigation |
|---|---|---|
| الموضوع يتوسع بلا حد | +١٠٠ ورقة وما زلت تقرأ | أوقف الإضافة عند ١٢٠ مصدراً؛ ثبّت السؤال في M1 |
| مراجع مكرّرة/ناقصة | أخطاء في BibTeX | شغّل `validate_sources.py` أسبوعياً |
| مسودة بلا حجة | فصول مليانة اقتباسات بدون رأيك | ابدأ كل قسم بجملة **أنت** تربط المصادر |
| تأخير في إثبات الفجوة | لا أرقام | `litkit.py gaps` من M3 |
| ضياع الوقت في التنسيق | تعديل شكل الورقة قبل اكتمالها | التنسيق في M8 فقط |

---

## ✅ معايير "جاهز للإرسال" | Ready-to-submit criteria

- [ ] السؤال البحثي مجاب عنه صراحةً في **الملخص** و**الخاتمة**.
- [ ] جدول PRISMA مكتمل وصحيح الأرقام (إن كانت SLR).
- [ ] كل مرجع في `references.bib` له DOI أو URL، وكل `citekey` مستخدم في المتن.
- [ ] قسم *Limitations* صادق (المحكمون يكشفون المبالغة فوراً).
- [ ] إفصاح استخدام الذكاء الاصطناعي مكتوب (راجع `06_ethics_integrity.md`).
- [ ] الكلمات ضمن حد المجلة (عادة ٦٠٠٠–١٠٠٠٠).
