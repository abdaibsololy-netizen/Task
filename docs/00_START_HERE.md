# 🚀 ابدأ من هنا | Start Here

> **الهدف Goal:** تحويل "موضوع عام عن الذكاء الاصطناعي" إلى **ورقة بحثية قابلة للنشر** خلال فصل دراسي أو فصلين.
> Turn a general "AI" interest into a **publishable paper** within one or two semesters.

---

## 1️⃣ الأسبوع الأول | Week 1 — قرّر الزاوية (Decide the angle)

الذكاء الاصطناعي واسع جداً — لا تكتب عن "الذكاء الاصطناعي" بشكل عام؛ كل المجالات الرصينة ترفض هذا.
"AI" alone is too broad — good journals reject unfocused manuscripts.

**افتح `01_topic_selection.md` واختر واحدة من ١٢ فكرة، أو املأ ورقة القرار.**
Open `01_topic_selection.md`, pick one of 12 ideas, or fill the decision worksheet.

القاعدة الذهبية | Golden rule:
```
موضوع ضيق  +  سؤال بحثي واضح  +  فجوة مثبتة بالأدبيات  +  منهجية قابلة للتنفيذ
Narrow topic + clear research question + evidence-backed gap + feasible method
```

---

## 2️⃣ الأسبوع ٢–٤ | Weeks 2–4 — ابنِ قاعدة الأدبيات (Build the literature base)

```bash
# سجّل كل ورقة تمر عليها — حتى لو استبعدتها لاحقاً
python tools/litkit.py add --title "..." --authors "..." --year 2026 \
  --venue "..." --doi 10.xxxx/yyy --problem T1 --solution S1 --method survey
python tools/litkit.py stats       # شوف التوزيع
python tools/litkit.py gaps        # 🔎 وين الفجوة اللي ما أحد غطاها؟
```

- استعلامات البحث الجاهزة: `literature/search_strings.md`
- سجل الفرز (PRISMA): `literature/screening_log.csv` ثم `python tools/prisma.py`
- ملاحظة لكل ورقة مقبولة: انسخ `literature/templates/paper_note.md` إلى `literature/notes/`

**الهدف الكمّي | Targets:** ٦٠–١٢٠ ورقة مُفرَزة، ٣٠–٦٠ ورقة مستخرجة، ٢٠–٤٠ مرجعاً في الورقة النهائية.

---

## 3️⃣ الشهر ٢ | Month 2 — ثبّت المنهجية (Lock the methodology)

`docs/03_methodology.md` يشرح ثلاثة مسارات ويخبرك أيهم يناسب فكرتك:
1. **مراجعة منهجية SLR (PRISMA 2020)** — الأسرع والأكثر قابلية للنشر لطالب ماجستير.
2. **دراسة ميدانية (Survey/SEM)** — تحتاج عينة وموافقة أخلاقية.
3. **Design Science /Artifact** — تبني أداة أو إطار حل وتقيّمه.

---

## 4️⃣ الشهر ٣+ | Month 3+ — التحليل والكتابة (Analyze & write)

- التحليل الببليومتري: `experiments/notebooks/00_bibliometric_starter.ipynb`
- الكتابة: `manuscript/` كل فصل فيه **هيكل إنجليزي جاهز + شرح عربي** تحت كل عنوان.
- دليل الكتابة وبنك العبارات الأكاديمية: `docs/04_writing_guide.md`

---

## 5️⃣ قبل الإرسال | Before submission

`docs/05_publishing_guide.md` + `submission/checklist.md` — ولا تنسَ `docs/06_ethics_integrity.md` (إفصاح استخدام أدوات الذكاء الاصطناعي في الكتابة شرط في أغلب المجلات الآن).

---

## 🧭 خريطة سريعة للملفات التي ستعدّلها أنت | Files YOU will edit

| الملف | متى تعدّله |
|---|---|
| `docs/01_topic_selection.md` | الأسبوع ١ |
| `literature/search_strings.md` | الأسبوع ٢ |
| `literature/screening_log.csv` | الأسبوع ٢–٤ |
| `literature/sources.csv` | طوال فترة الفرز والاستخراج |
| `literature/problem_solution_matrix.md` | الشهر ٢–٣ |
| `literature/notes/*.md` | كل ورقة مهمة |
| `manuscript/*.md` | الشهر ٣+ |
| `submission/journal_shortlist.md` | قبل الإرسال |

---

## ❓أسئلة شائعة | FAQ

**س: هل أستطيع استخدام ChatGPT/أدوات الذكاء الاصطناعي في الكتابة؟**
Yes, but: (1) تحقّق من كل مرجع بنفسك؛ (2) أفصح عن الاستخدام في قسم *Declaration of Generative AI*؛ (3) لا تجعل أداةً مؤلفاً. راجع `docs/06_ethics_integrity.md`.

**س: كم مصدر أحتاج؟**
25–40 مرجعاً في ورقة مراجعة منهجية قصيرة، و40–80 في ورقة كاملة؛ المهم **الانتقاء المنهجي** لا العدد.

**س: المجلة تطلب LaTeX — ماذا أفعل؟**
حوّل المخطوطة لاحقاً؛ اكتب الآن في Markdown (سهل المراجعة مع المشرف)، ثم استخدم Pandoc:
`pandoc manuscript/*.md -o draft.tex --bibliography=references/references.bib`
