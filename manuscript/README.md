# 📝 المخطوطة | Manuscript

> **تُكتب بالإنجليزية** للنشر الدولي — الشرح العربي بين `{ ... }` موجّه لك أنت، **احذفه قبل الإرسال**.
> The manuscript is written in **English**; Arabic notes in `{ ... }` are guidance for you — **delete before submission**.

---

## الملفات | Files

| # | الملف | المحتوى | عدد الكلمات المستهدف |
|---|---|---|---|
| 0 | `00_abstract.md` | الملخص + الكلمات المفتاحية | ١٥٠–٢٥٠ |
| 1 | `01_introduction.md` | المقدمة (قمع مقلوب) | ٨٠٠–١٢٠٠ |
| 2 | `02_related_work.md` | الأدبيات السابقة والفجوة | ١٢٠٠–٢٠٠٠ |
| 3 | `03_problem_taxonomy.md` | تصنيف المشاكل (T#/O#) | ٨٠٠–١٢٠٠ |
| 4 | `04_solution_landscape.md` | مشهد الحلول (S#) | ١٢٠٠–١٨٠٠ |
| 5 | `05_methodology.md` | المنهجية (PRISMA) | ١٠٠٠–١٥٠٠ |
| 6 | `06_results.md` | النتائج (جداول/أشكال) | ١٢٠٠–١٨٠٠ |
| 7 | `07_discussion.md` | المناقشة + الآثار + الأجندة | ١٢٠٠–١٨٠٠ |
| 8 | `08_conclusion.md` | الخاتمة والحدود | ٥٠٠–٨٠٠ |

---

## قواعد التعامل مع الملفات | House rules

1. **اكتب بالإنجليزية داخل الأقسام**، واحذف الملاحظات العربية عند تجهيز النسخة النهائية.
2. كل ادّعاء يحتاج مرجعاً: `@citekey` (BibTeX) — والمفتاح يجب أن يكون موجوداً في `references/`.
3. الأرقام تأتي من `experiments/results/` — لا تكتب رقماً من ذاكرتك.
4. ابدأ كل قسم بجملة **أنت** تربط المصادر (ليس باقتباس).
5. راجع `docs/04_writing_guide.md` لبنك العبارات الأكاديمية.

---

## سير العمل | Workflow

```
مسودة أولية (write ugly)  →  مراجعة المشرف  →  تحسين الحجة  →
تنسيق حسب المجلة  →  تحويل إلى LaTeX (Pandoc)  →  submission/
```

**تحويل إلى LaTeX | Convert to LaTeX:**
```bash
pandoc manuscript/*.md -f markdown -s \
  --bibliography=references/references.bib \
  --citeproc -o submission/manuscript.tex
```

---

## تتبّع الحالة | Status tracker

| القسم | الحالة | آخر تحديث |
|---|---|---|
| Abstract | 🟥 مسودة | |
| Introduction | 🟥 مسودة | |
| Related work | ⬜ لم يبدأ | |
| Problem taxonomy | ⬜ لم يبدأ | |
| Solution landscape | ⬜ لم يبدأ | |
| Methodology | ⬜ لم يبدأ | |
| Results | ⬜ لم يبدأ | |
| Discussion | ⬜ لم يبدأ | |
| Conclusion | ⬜ لم يبدأ | |

🟥 مسودة · 🟧 قيد المراجعة · 🟨 جاهز للمشرف · 🟩 معتمد
