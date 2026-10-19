# 🧪 المنهجية | Methodology

اختر **مساراً واحداً** — الخلط بين المنهجيات سبب رئيسي للرفض.
Pick **one** path — mixing methods is a common rejection cause.

---

## المسار ١ — مراجعة منهجية SLR (PRISMA 2020) ⭐ الأفضل لطالب ماجستير
### Path 1 — Systematic Literature Review (recommended)

**متى تختاره:** لا تملك بيانات ميدانية، تريد نشراً خلال ٦–٩ أشهر.
**When:** no field data, want to publish in 6–9 months.

### الخطوات Steps

1. **بروتوكول Protocol** — سجّل: السؤال، قواعد البيانات، سلسلة البحث، معايير الإدراج/الاستبعاد، مستوى الجودة.
2. **التحديد Identification** — نفّذ الاستعلامات من `literature/search_strings.md` وسجّل الأعداد في `literature/screening_log.csv`.
3. **إزالة التكرار De-duplication** — `python tools/litkit.py dedupe` (مطابقة بالـDOI ثم بالعنوان المطبَّع).
4. **الفرز Screening** — مرحلتان: (أ) العنوان والملخص، (ب) النص الكامل. **مراجعَان مستقلان** إن أمكن + حساب Cohen's kappa لاتفاقهما.
5. **الاستخراج Extraction** — جدول `literature/sources.csv` (الحقول موثّقة في `literature/README.md`) + نسخة من `literature/templates/paper_note.md` لكل ورقة مهمة.
6. **التوليف Synthesis** — تحليل موضوعي (thematic analysis) + التجميع حسب أكواد `literature/taxonomy.md`.
7. **التقرير Reporting** — مخطط PRISMA + جدول PRISMA checklist.

```bash
python tools/prisma.py            # يطبع مخطط التدفق من screening_log.csv
python tools/validate_sources.py  # فحص اكتمال الحقول قبل التحكيم
```

### 📌 معايير إدراج مقترحة (عدّلها) | Suggested inclusion criteria

| المعيار | Include | Exclude |
|---|---|---|
| اللغة | الإنجليزية | غير الإنجليزية |
| الفترة | 2023–2026 | قبل 2023 (إلا الأوراق المؤسِّسة) |
| النوع | مجلات/مؤتمرات مفهرسة + preprints عالية التأثير | مدونات، أخبار، تقارير تسويقية |
| المحتوى | يعرّف مشكلة AI محددة **ويقترح/يقيّم حلاً** | يتحدث عن AI بشكل عام |
| الوصول | نص كامل متاح | ملخص فقط |

### ⚠️ أخطاء تسبّب الرفض الفوري | Desk-reject triggers
- سلسلة بحث غير مسجّلة / غير قابلة للتكرار (يجب إرفاقها كملحق).
- بحث في قاعدة بيانات واحدة فقط (يُفضَّل ٤+: Scopus, WoS, IEEE Xplore, ACM DL، وarXiv للمواد الحديثة).
- تجميع بلا نقد (وصف الأوراق ورقة بورقة ≠ توليف).

---

## المسار ٢ — دراسة ميدانية (Survey / SEM)
### Path 2 — Empirical survey

**متى:** عندك وصول لمنظمات/مستجيبين (n ≥ ٢٠٠ للنمذجة الهيكلية).
**When:** you have access to organizations/respondents (n ≥ 200 for SEM).

- أدوات: Qualtrics/Google Forms → تصدير CSV إلى `experiments/data/raw/`.
- موافقة أخلاقية (IRB) **قبل** جمع البيانات — راجع `06_ethics_integrity.md`.
- التحليل: موثوقية (Cronbach's α)، تحليل عاملي، ثم PLS-SEM أو CB-SEM.
- اكتب خطة التحليل **قبل** رؤية البيانات (pre-registration مبسّط) لمنع الانحياز.

---

## المسار ٣ — Design Science / بناء حل
### Path 3 — Design Science Research (DSR)

**متى:** تبني إطاراً/أداة/مصنّفاً لحل مشكلة AI محددة وتقيّمه.
**When:** you build an artifact (framework, tool, classifier) and evaluate it.

| المرحلة | المخرج |
|---|---|
| Problem identification | الفجوة من `litkit.py gaps` |
| Design & development | الكود في `experiments/scripts/` |
| Demonstration | حالة استخدام (use case) |
| Evaluation | مقارنة مع خط أساس + مقاييس واضحة |
| Communication | `manuscript/` |

---

## 📊 جدول مقارنة | Comparison

| | SLR (PRISMA) | Survey/SEM | DSR |
|---|---|---|---|
| زمن التنفيذ | ٦–٩ أشهر | ٩–١٢ شهراً | ٩–١٢ شهراً |
| يحتاج بيانات ميدانية | ❌ | ✅ | ⚠️ (حسب الحالة) |
| يحتاج برمجة | ❌ | ⚠️ إحصاء | ✅ |
| قبوله في مجلات IS/AI | عالي (إن كان التوليف قوياً) | عالي | متوسط–عالي |
| الأنسب لتخصص MIS | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## 🧾 ما يجب أن يظهر في قسم Methodology من مخطوطتك

```
- Research design and rationale (لماذا هذا المنهج يجيب سؤالك)
- Search / sampling strategy (قابلة للتكرار)
- Inclusion & exclusion criteria
- Data extraction & coding scheme (الأكواد T#/O#/S#)
- Quality appraisal (كيف حكمت على قوة الدليل)
- Analysis procedure
- Validity / reliability threats (internal, external, construct)
- Ethics statement
```
