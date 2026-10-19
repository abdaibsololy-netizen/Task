# 4. The Solution Landscape

> {الحلول المقترحة في الأدبيات مرتّبة حسب عائلات `S1–S12`، مع تقييم قوة الدليل لكل عائلة.
> Solution families S1–S12 with strength of evidence for each.}

---

## 4.1 عائلات الحلول | Solution families

| عائلة Family | الآلية Mechanism | المشاكل التي تعالجها Problems addressed | قوة الدليل Evidence strength |
|---|---|---|---|
| **S1** Retrieval grounding / RAG | تأصيل المخرجات في مصادر خارجية | T1, T6, T9 | high / medium / low |
| **S2** Human-in-the-loop | مراجعة بشرية قبل الاعتماد | T1, O3, T11 | |
| **S3** Fine-tuning & alignment | تعديل السلوك بالتدريب | T1, T2 | |
| **S4** Explainability tooling | تفسير المخرجات | T5, O3 | |
| **S5** Privacy-preserving | DP / federated learning | T3, O7 | |
| **S6** Guardrails & red-teaming | فلاتر واختبار خصمي | T4, T12 | |
| **S7** Governance frameworks | أطر ومعايير (NIST, ISO 42001, EU AI Act) | O2, O7, T11 | |
| **S8** Benchmarks & evaluation | قياس منهجي | T9, T1 | |
| **S9** MLOps & monitoring | مراقبة مستمرة بعد النشر | T6, T7, T11 | |
| **S10** Training & AI literacy | بناء القدرات | O4, O6 | |
| **S11** Prompt engineering | CoT / self-consistency / verification | T1 | |
| **S12** Agentic orchestration & verification | وكلاء متعددون + تحقق | T12, T1 | |

## 4.2 خريطة التغطية | Coverage map

{أدرج الشكل: `experiments/results/figures/fig3_problem_solution_heatmap.png`}

> **Figure 3.** Coverage of problem–solution pairs across the N included studies. Empty cells indicate unaddressed combinations.

## 4.3 ملاحظات نقدية | Critical observations

1. {أين تركّزت الحلول؟}
2. {أي الحلول مُقيَّمة ميدانياً مقابل النظرية؟}
3. {أي مشكلة **بلا** حل مدروس؟ (هذه فجوتك)}

> نموذج صياغة | Template:
> *"Mitigation effort is highly uneven: X% of the included studies target T1, whereas T7 (cost and energy) appears in only Y% despite its documented impact on adoption."*

---

## ✅ قائمة تحقق | Checklist

- [ ] كل عائلة حلول مشروحة في ٢–٣ جمل + مرجع تمثيلي.
- [ ] قوة الدليل مبنية على معيار معلن (مثلاً: هل يوجد تقييم كمّي؟ حجم العينة؟ خط الأساس؟).
- [ ] الشكل مذكور ومفسَّر في المتن (لا تترك شكلاً بلا شرح).
- [ ] الحلول التنظيمية (S7, S10) معاملةٌ بجدية مساوية للحلول التقنية.
