# 🧩 تصنيف المشاكل والحلول | Problem & Solution Taxonomy

> الأكواد ثابتة لا تتغيّر بعد بدء الترميز — تسمح بالعدّ والمقارنة لاحقاً.
> Codes are frozen once coding starts — they enable counting and comparison later.

**كيف تستخدمها:** حقل `problem_codes` و`solution_codes` في `literature/sources.csv` (مفصولة بفاصلة: `T1,T5`).
Usage: fill `problem_codes` / `solution_codes` in `sources.csv` (comma-separated).

---

## 🔧 T — المشاكل التقنية | Technical problems

| كود | المشكلة Problem | مثال Example |
|---|---|---|
| **T1** | الهلوسة وعدم الدقة الواقعية — Hallucination & factual inaccuracy | النموذج يختلق مرجعاً أو رقماً |
| **T2** | التحيز والإنصاف — Bias & fairness | تمييز في التوظيف/الائتمان |
| **T3** | الخصوصية وتسرّب البيانات — Privacy & data leakage | تسريب بيانات تدريب/مطالبات |
| **T4** | الأمن والهجمات — Security (prompt injection, jailbreak, poisoning) | حقن أوامر عبر مستند خارجي |
| **T5** | الشفافية وقابلية التفسير — Transparency & explainability | قرار ائتماني غير مبرَّر |
| **T6** | المتانة والموثوقية — Robustness & reliability | انهيار الأداء على بيانات خارج التوزيع |
| **T7** | التكلفة والحوسبة والطاقة — Cost, compute & energy | تكلفة استدلال مرتفعة |
| **T8** | جودة البيانات وحوكمتها — Data quality & governance | بيانات تدريب ملوّثة/قديمة |
| **T9** | التقييم والمقاييس — Evaluation & benchmarking | غياب معيار تقييم موحّد |
| **T10** | الملكية الفكرية وحقوق النشر — IP & copyright | تدريب على محتوى محمي |
| **T11** | المساءلة والتدقيق — Accountability & auditability | لا سجل لقرارات النموذج |
| **T12** | مخاطر الوكلاء المستقلين — Agentic AI risks | وكيل ينفّذ إجراءً خاطئاً دون رقابة |

---

## 🏢 O — المشاكل التنظيمية / نظم المعلومات | Organizational & IS problems

| كود | المشكلة Problem | مثال Example |
|---|---|---|
| **O1** | التبنّي والجاهزية — Adoption & readiness | لا استراتيجية واضحة للذكاء الاصطناعي |
| **O2** | الحوكمة والسياسات — Governance & policy | لا مالك للمخاطر (ownership) |
| **O3** | الثقة والقبول — Trust & acceptance | المستخدمون يتجاهلون توصيات النظام |
| **O4** | الفجوة المهارية — Skills & AI literacy | لا أحد يفهم مخرجات النموذج |
| **O5** | قياس العائد — ROI & value measurement | لا مؤشر أداء واضح للمشروع |
| **O6** | إدارة التغيير والوظائف — Change management & job displacement | مقاومة داخلية/خوف من الاستبدال |
| **O7** | الامتثال التنظيمي — Regulatory compliance | متطلبات لائحة الذكاء الاصطناعي الأوروبي |
| **O8** | التكامل مع الأنظمة القديمة — Legacy systems integration | لا يعمل مع ERP القديم |
| **O9** | الارتهان للمورّد — Vendor lock-in | اعتماد كامل على API مغلقة |
| **O10** | الاستدامة البيئية — Environmental sustainability | بصمة كربونية للتدريب |

---

## 💡 S — فئات الحلول | Solution categories

| كود | الحل Solution family | يشمل Includes |
|---|---|---|
| **S1** | التأصيل والاسترجاع — Retrieval grounding / RAG | RAG، قواعد معرفة، Graph-RAG |
| **S2** | الإنسان في الحلقة — Human-in-the-loop | مراجعة بشرية، تصويت، escalation |
| **S3** | الضبط والمحاذاة — Fine-tuning & alignment | SFT، RLHF/RLAIF، DPO |
| **S4** | التفسير — Explainability tooling | SHAP/LIME، attention maps، تقارير |
| **S5** | حفظ الخصوصية — Privacy-preserving | Differential privacy، federated learning |
| **S6** | الحواجز والاختبار الخصمي — Guardrails & red-teaming | فلاتر المدخلات/المخرجات، سياسات أمان |
| **S7** | أطر الحوكمة — Governance frameworks | NIST AI RMF، ISO/IEC 42001، EU AI Act |
| **S8** | التقييم والمقاييس — Benchmarks & evaluation | HalluLens، مقاييس واقعية، human eval |
| **S9** | العمليات والمراقبة — MLOps & monitoring | تسجيل الإصدارات، drift detection |
| **S10** | التدريب والتثقيف — Training & AI literacy | برامج تدريب، أدلة استخدام |
| **S11** | هندسة الأوامر — Prompt engineering | CoT، self-consistency، chain-of-verification |
| **S12** | تنسيق الوكلاء والتحقق — Agentic orchestration & verification | multi-agent verification، tool use، planning |

---

## 🧮 حقول تصنيف إضافية في جدول المصادر | Extra coding fields

| الحقل Field | القيم Allowed values |
|---|---|
| `type` | `journal` \| `conference` \| `preprint` \| `book` \| `report` \| `standard` |
| `method` | `slr` \| `survey_empirical` \| `case_study` \| `experiment` \| `benchmark` \| `position` \| `design_science` |
| `contribution` | `taxonomy` \| `framework` \| `empirical_evidence` \| `tool` \| `review` |
| `evidence_strength` | `high` \| `medium` \| `low` |
| `include` | `yes` \| `no` |
| `venue_rank` | `Q1` \| `Q2` \| `Q3` \| `Q4` \| `na` |

---

## 🔎 كيف تكتشف فجوتك من هذه الأكواد | Finding your gap with codes

```bash
python tools/litkit.py gaps
```

يقرأ الأداة `sources.csv` ويطبع: كم مصدراً يغطي كل كود مشكلة، وكم كود حلٍّ مقترح لكل مشكلة. **المشاكل ذات التغطية المنخفضة أو الحلول غير المقيَّمة = مرشحة لتكون فجوة بحثك.**
It prints coverage per problem code and proposed solutions per problem — **low-coverage or un-evaluated problems are your gap candidates.**
