# 3. A Taxonomy of Contemporary AI Problems

> {هنا تقدّم تصنيفك (أو التصنيف الذي تبنّيته/وسّعته). مصدره: `literature/taxonomy.md`.
> Present your coding scheme — the backbone of the paper's argument.}

---

## 3.1 كيف بُني التصنيف | How the taxonomy was derived

{اشرح: استقرائي (من البيانات) أم استنباطي (من الأدبيات) أم هجين؟ كم دورة ترميز؟ اتفاق المرمّزين؟}

> *"We adopted a hybrid approach: an initial coding frame derived from {framework} was refined inductively over two coding rounds. Inter-coder agreement on 20% of the sample reached Cohen's κ = 0.xx."*

## 3.2 البعد التقني | Technical dimension (T1–T12)

| كود | المشكلة Problem | الوصف المختصر Brief | n |
|---|---|---|---|
| T1 | Hallucination & factual inaccuracy | … | {من `results/tables/tab_problems.csv`} |
| T2 | Bias & fairness | … | |
| … | … | | |

## 3.3 البعد التنظيمي | Organisational dimension (O1–O10)

| كود | المشكلة Problem | الوصف المختصر Brief | n |
|---|---|---|---|
| O1 | Adoption & readiness | … | |
| … | … | | |

## 3.4 العلاقة بين البعدين | Linking the two dimensions

{نقطة قوتك: كيف تتحول مشكلة تقنية (T1) إلى مشكلة تنظيمية (O3 ثقة، O5 عائد)؟
ارسم إن أمكن شكلاً: `experiments/results/figures/fig4_problem_linkage.png`}

> *"Technical and organisational problems are not independent: a hallucination rate that is tolerable in a creative task becomes an adoption barrier (O3) in a decision-support context."*

---

## ✅ قائمة تحقق | Checklist

- [ ] كل كود مُعرَّف بجملة واحدة + مثال.
- [ ] الأكواد **شاملة ومانعة** (mutually exclusive & collectively exhaustive قدر الإمكان).
- [ ] الأرقام (n) مطابقة لملف النتائج.
- [ ] مذكور مصدر كل كود: أدبيات سابقة أم استقراء من بياناتك.
