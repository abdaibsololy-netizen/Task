# 🎯 تحديد الموضوع | Topic Selection

> المستودع مبني بـ **هيكل مرن**: أي فكرة من الأفكار التالية تشتغل داخل نفس المجلدات والأكواد.
> The workspace is **topic-agnostic**: any idea below plugs into the same folders and code taxonomy.

موضوعك العام: *الذكاء الاصطناعي — أحدث المشاكل والحلول*.
Your umbrella topic: *AI — recent problems and solutions*.

---

## A) ورقة القرار | Decision worksheet

قيّم كل فكرة من ١ إلى ٥ ثم اجمع. أي فكرة أقل من ١٨ → استبعدها.
Score each idea 1–5; sum. Anything below 18 → drop it.

| المعيار Criterion | ماذا يعني What it means |
|---|---|
| **الاهتمام Interest** | هل تقدر تقرأ ٦٠ ورقة عنها بدون ملل؟ Can you read 60 papers on it? |
| **توفّر البيانات Data access** | هل البيانات/الأدبيات متاحة مجاناً؟ Is data/literature freely available? |
| **قابلية التنفيذ Feasibility** | تنجزها في فصلين بجهازك؟ Done in two semesters with your laptop? |
| **قوة الفجوة Gap strength** | هل تستطيع إثبات الفجوة بالأرقام؟ Can you evidence the gap numerically? |
| **خبرة المشرف Supervisor fit** | هل يفهم مشرفك المنهجية؟ Does your supervisor know the method? |
| **ملاءمة المجلة Journal fit** | هل مجلة Q1/Q2 تنشر هذا النوع؟ Does a Q1/Q2 journal publish this type? |

> 🔎 **كيف تثبت الفجوة بالأرقام** (خطوة يطلبها المحكمون دائماً):
> شغّل `python tools/litkit.py gaps` بعد إدخال ٣٠–٥٠ مصدراً — يطبع لك المشاكل الأقل تغطيةً = **فجوتك**.
> How to evidence the gap: run `python tools/litkit.py gaps` after entering 30–50 sources.

---

## B) ١٢ فكرة بحثية جاهزة | 12 ready-made research ideas

كل فكرة: **Problem → RQ → Method → Data → Why it is publishable → Target journals**
(الأكواد بين قوسين تشير إلى `literature/taxonomy.md`)

---

### 1. خرائط حلول الهلوسة في نماذج اللغة الكبيرة: مراجعة منهجية للتقنيات وحدودها
**LLM hallucination mitigation map: a systematic review (T1 → S1,S3,S6,S11,S12)**

- **RQ1:** ما فئات تقنيات التخفيف من الهلوسة التي ظهرت بين 2023–2026؟
- **RQ2:** ما حدود كل فئة (prompting, retrieval/RAG, reasoning, training, agentic verification) من حيث التكلفة والقياس؟
- **Method:** SLR (PRISMA 2020) + تحليل موضوعي + تصنيف تصاعدي.
- **Data:** Scopus + IEEE Xplore + ACM DL + arXiv (سجل الكل في `literature/screening_log.csv`).
- **Why publishable:** المجال يتحرك بسرعة وهناك عدة تصنيفات متنافسة — يعني **حاجة لتصنيف موحّد**، وهذه مساهمة واضحة.
- **Journals:** *ACM TOIS* (Q1), *Artificial Intelligence Review* (Q1), *Information Fusion*, *Expert Systems with Applications*.

### 2. فجوة القياس: كيف تُقيَّم حلول الهلوسة؟ — مراجعة نقدية للمقاييس
**The evaluation gap: how are hallucination mitigations actually measured? (T1,T9)**

- **RQ:** هل المقاييس المستخدمة (benchmarks) كافية للحكم على نجاح الحل؟
- **Method:** مراجعة نقدية + تحليل Benchmarks + تصنيف أنواع الفشل.
- **Why publishable:** أبحاث عدة تشير لغياب معايير تقييم موحّدة — نقد منظومة القياس مساهمة مطلوبة.

### 3. من التقنية إلى التنظيم: إطار لتبنّي حلول الذكاء الاصطناعي التوليدي في المنظمات
**From technique to organization: a TOE-based adoption framework for GenAI safeguards (O1,O2,O3,O8)**

- **RQ:** ما العوامل التنظيمية التي تحدد اختيار المنظمة لحلٍّ تقني معيّن (مثل RAG مقابل human-in-the-loop)؟
- **Method:** SLR ثم دراسة حالة متعددة (3–5 منظمات) أو Delphi مع خبراء.
- **Theory:** **TOE** (Technology–Organization–Environment) أو DOI أو Institutional Theory.
- **Why publishable:** أغلب حلول الهلوسة تُدرَس تقنياً، وتبنّيها تنظيمياً **شبه مفقود** — زاوية قوية لطالب نظم معلومات.

### 4. الحوكمة بين الأطر الدولية: مقارنة NIST AI RMF و ISO/IEC 42001 ومتطلبات قانون الذكاء الاصطناعي الأوروبي
**Governance convergence: comparing NIST AI RMF, ISO/IEC 42001 and the EU AI Act (O2,O7)**

- **Method:** تحليل محتوى مقارن لأطر الحوكمة + مؤشرات امتثال قابلة للقياس.
- **Data:** وثائق رسمية (NIST AI RMF 1.0، ISO/IEC 42001:2023، لائحة الاتحاد الأوروبي 2024/1689).
- **Why publishable:** الحوكمة موضوع ساخن، و**المقارنة المنهجية** بين الأطر نادرة.

### 5. التكلفة الخفية: استهلاك الطاقة والموارد في حلول الذكاء الاصطناعي
**The hidden cost: energy and compute footprint of AI mitigation strategies (T7,O10)**

### 6. الثقة وقابلية التفسير: هل تحلّ XAI مشكلة الثقة في القرارات التنظيمية؟
**Does explainability buy trust? A review of XAI effects on organizational decision-making (T5,O3)**

### 7. الخصوصية مقابل الفائدة: تقنيات الخصوصية (DP/Federated) في تبنّي الذكاء الاصطناعي
**Privacy vs. utility: privacy-preserving AI in organizational adoption (T3,O7)**

### 8. أمن الذكاء الاصطناعي التوليدي: حقن الأوامر والتلاعب — تصنيف الهجمات والدفاعات
**Prompt injection and jailbreaks: a taxonomy of attacks and defenses (T4,S6,S9)**

### 9. جودة البيانات كعائق أول: لماذا تفشل مشاريع الذكاء الاصطناعي قبل النمذجة؟
**Data quality as the primary barrier: why AI projects fail before modelling (T8,O1,O8)**

### 10. قياس العائد (ROI) لمشاريع الذكاء الاصطناعي في المنظمات
**Measuring AI business value: a framework and evidence synthesis (O5)**

### 11. الفجوة المهارية: أثر التدريب والذكاء الاصطناعي الوظيفي (AI literacy) على التبنّي
**AI literacy and workforce readiness as adoption antecedents (O4,O6)**

### 12. الوكلاء المستقلون (Agentic AI): مشاكل جديدة وحلول ناشئة
**Agentic AI reliability: failure modes, verification, and governance (T1,T11,T12)**

---

## C) كيف تضيّق الفكرة في سؤال واحد | Narrowing to one RQ

استخدم قالب **PICOC** (يطلبه كثير من المجلات في مراجعات الأدبيات):

| الحرف | المعنى | مثال (فكرة ١) |
|---|---|---|
| **P**opulation | مجال التطبيق | أنظمة توليد النصوص المؤسسية |
| **I**ntervention | الحل المُدرَس | تقنيات التخفيف من الهلوسة |
| **C**omparison | المقارنة | بدون تخفيف / تقنية أخرى |
| **O**utcome | النتيجة | دقة واقعية، تكلفة، قابلية القياس |
| **C**ontext | السياق | نشر مؤسسي 2023–2026 |

**النتيجة | Output:** سطر واحد تضعه في مقدمة بحثك:
> *"This study systematically reviews and classifies hallucination-mitigation techniques for enterprise text-generation systems (2023–2026), comparing them on factual accuracy, cost, and measurability."*

---

## D) فحوصات قبل التثبيت | Pre-commitment checks

- [ ] الفكرة ضيقة بما يكفي لتُغطّى في ٦٠٠٠–٩٠٠٠ كلمة؟
- [ ] يوجد **٣–٥ أوراق حديثة (2024+) قريبة جداً** منها؟ (إذا لا → المجال ميت أو غير منشور)
- [ ] يوجد **اختلاف واضح** بينها وبين تلك الأوراق؟ (هذا هو "الـcontribution statement")
- [ ] المجلة المستهدفة نشرت شيئاً مشابهاً في آخر سنتين؟
- [ ] تستطيع إنجازها بلا تمويل ولا بيانات سرية؟

> بعد الاختيار: انسخ السؤال إلى `manuscript/01_introduction.md` وابدأ.
