# 📥 بروتوكول الإدخال | Intake Protocol

> **القاعدة الذهبية | Golden rule**
> لا تُضاف أي مادة بحثية (مشكلة، دليل، اقتباس، تجربة، هدف، فائدة، خطر) إلا **بموافقة صريحة من الباحثة**.
> No research material is added without the researcher's explicit approval.
>
> الباحثة ترسل المادة → أنا أصنّفها وأحدد مكانها → **أعرضها عليها** → بعد التأكيد أحفظها وأعمل commit.
> Researcher sends → I classify → **I confirm with her** → then save + commit.

---

## 1) المناطق: مفتوح / مقفل | Zones

### 🔓 مفتوح دائماً (أعمال تنظيمية وصيانة)
`tools/` · `tests/` · `.github/` · `experiments/scratch/` · `inbox/` · `docs/` (هذا الملف وأخواته التنظيمية)

### 🔒 مقفل — لا يُفتح إلا بكلمة "دخّلها / approved"
| المسار | يفتح عند |
|---|---|
| `manuscript/*.md` | أي نص يخصّ الورقة (مقدمة، نتائج، مناقشة…) |
| `literature/sources.csv` | إضافة مصدر/دليل جديد |
| `literature/notes/*.md` | ملاحظة أو اقتباس من ورقة |
| `literature/problem_solution_matrix.md` | مشكلة أو حل أو فجوة |
| `literature/taxonomy.md` | كود جديد (T#/O#/S#) |
| `references/references.bib` | مرجع جديد |
| `submission/*` | قرار نشر أو مجلة |

---

## 2) جدول التوجيه | Routing table

| النوع Type | الوجهة الأساسية Destination | ما يُكتب بالضبط What is written | بادئة الـCommit |
|---|---|---|---|
| **مشكلة Problem** | `literature/taxonomy.md` → `literature/problem_solution_matrix.md` → `manuscript/03_problem_taxonomy.md` | كود `T#`/`O#` + تعريف بجملة + مثال + صف في المصفوفة + وصف في §3 | `taxonomy(problem):` |
| **حل Solution** | `literature/taxonomy.md` (كود `S#`) → `manuscript/04_solution_landscape.md` | عائلة الحل + آليته + المشاكل التي يعالجها + قوة الدليل | `taxonomy(solution):` |
| **دليل / دراسة / رقم Evidence** | `literature/sources.csv` (عبر `tools/litkit.py add`) → `literature/notes/<citekey>.md` → `references/references.bib` | صف استخراج كامل + ملاحظة الورقة + مدخل BibTeX | `lit(evidence):` |
| **اقتباس Quote** | قسم «اقتباسات حرفية» في `literature/notes/<citekey>.md` | النص بين علامات تنصيص + الصفحة/القسم + أين يُستخدم في المخطوطة | `lit(quote):` |
| **تجربة Experiment** | `experiments/scripts/` → `experiments/results/` → `manuscript/06_results.md` | سكربت قابل للتكرار + جدول/شكل + سطر نتائج في §6 | `exp(experiment):` |
| **هدف / سؤال بحثي Objective** | `manuscript/01_introduction.md` (¶4) + `docs/01_topic_selection.md` | صياغة RQ + المساهمة المقابلة | `ms(objective):` |
| **فائدة / أثر Implication** | `manuscript/07_discussion.md` (جدول الآثار: نظرية / عملية / سياساتية) | سطر لكل جهة مستفيدة | `ms(implication):` |
| **خطر / قصور / تهديد Risk** | `manuscript/05_methodology.md` (تهديدات الصلاحية) + `08_conclusion.md` (الحدود) | التهديد + أثره + التدبير المقابل | `ms(risk):` |
| **مساهمتنا Contribution** | `manuscript/04` أو قسم Design Science في `05_methodology.md` | الفكرة / الأداة / الإطار + كيف نقيّمه | `ms(contribution):` |
| **مصطلح Term** | قاموس المصطلحات في نهاية `04_writing_guide.md` | المصطلح + تعريفه + مرادفاته | `docs(glossary):` |
| **نشر / مجلة Venue** | `submission/journal_shortlist.md` | صف في الجدول + سبب الملاءمة + تاريخ التحقق | `sub(venue):` |
| **مادة خام غير مصنّفة Raw** | `inbox/YYYY-MM-DD-slug.md` | تُحفظ كما هي → تُصنَّف لاحقاً | `inbox(raw):` |

---

## 3) دورة الإدخال | Intake cycle (٤ خطوات)

```
1. RECEIVE   — الباحثة ترسل المادة بأي شكل (نص، رابط، فكرة، ملاحظة صوتية مفرّغة…)
2. CLASSIFY  — أحدد: النوع → الوجهة → الكود → هل يحتاج مصدر/DOI؟
3. CONFIRM   — أعرض عليها بالضبط: «سأضيفها كـ(نوع) في (المسار) بهذا الشكل … approved؟»
4. PLACE     — بعد الموافقة: أكتبها في مكانها + أشغّل الأدوات + commit برسالة واضحة
```

**مثال على رسالة التأكيد | Confirmation example:**
> سأضيفها كـ **مشكلة (Problem)**:
> • كود: `T13 — Over-reliance / automation bias` في `literature/taxonomy.md`
> • صف في `problem_solution_matrix.md` (الحلول: S2, S10)
> • فقرة في `manuscript/03_problem_taxonomy.md` §3.4
> • commit: `taxonomy(problem): add T13 over-reliance`
> → approved؟

---

## 4) مجلد `inbox/` | The inbox

- أي مادة **غير مصنّفة أو ناقصة** تُحفظ أولاً في `inbox/YYYY-MM-DD-slug.md` كما هي (بدون تعديل).
- بعد التصنيف والموافقة: تُنقل إلى وجهتها، وتُحفظ النسخة الأصلية في `inbox/processed/`.
- **لا يُكتب من `inbox/` إلى `manuscript/` مباشرة أبداً** — لا بد من خطوة تأكيد.

---

## 5) منطقة التجارب الآمنة | Safe scratch zone

- التجارب والاستكشاف: `experiments/scratch/` (أو `/tmp` عند الحاجة) — لا تلمس `results/` النهائية.
- أي ملف مؤقت أُنشئه أسمّيه ببادئة `tmp_` وأحذفه بعد الانتهاء.
- القاعدة: **لا شيء يصل إلى `experiments/results/` إلا بعد موافقة** (لأنها مصادر أرقام الورقة).

---

## 6) الأثر والتتبّع | Audit trail

- كل إضافة معتمدة = **commit واحد** برسالة تبدأ بالبادئة المناسبة (الجدول أعلاه).
- يمكن التراجع عن أي إضافة: `git revert <commit>` أو بكلمة من الباحثة.
- سجل الإضافات المعتمدة (يُحدَّث مع كل إضافة):

| # | التاريخ | النوع | المكان | ملخص | Commit |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

## 7) اصطلاحات التسمية | Naming conventions

| الشيء | القاعدة | مثال |
|---|---|---|
| `citekey` | اسم المؤلف الأخير + السنة + أول كلمة دالة من العنوان (حروف صغيرة) | `huang2025survey` |
| ملف الملاحظة | `literature/notes/<citekey>.md` | `literature/notes/huang2025survey.md` |
| أكواد المشاكل التقنية | `T1`–`T12` (الجديد يبدأ من `T13`) | `T13` |
| أكواد المشاكل التنظيمية | `O1`–`O10` (الجديد `O11`) | `O11` |
| أكواد الحلول | `S1`–`S12` (الجديد `S13`) | `S13` |
| مادة الـinbox | `YYYY-MM-DD-slug.md` | `2026-10-19-hallucination-note.md` |

---

## 8) التزاماتي | My commitments

1. لا أكتب في أي مسار مقفل بدون «approved/دخّلها».
2. أصنّف كل مادة وأعرض مكانها بالضبط قبل الحفظ.
3. كل إضافة = commit موصوف + تحديث سجل الإضافات أعلاه.
4. لا أختلق مراجع أو أرقاماً — أي DOI أتحقق منه قبل إضافته.
5. أشرح المصطلح أو المفهوم بالعربي قبل إدخاله، حتى تكون المادة مفهومة لا محفوظة فقط.
