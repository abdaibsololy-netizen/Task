# 📚 إدارة الأدبيات | Literature Management

## الملفات | Files

| الملف File | الوظيفة Purpose |
|---|---|
| `taxonomy.md` | الأكواد الرسمية للمشاكل (T#/O#) والحلول (S#) — المرجع الوحيد للترميز |
| `search_strings.md` | استعلامات البحث لكل قاعدة بيانات (قابلة للتكرار = شرط النشر) |
| `screening_log.csv` | أعداد الفرز حسب PRISMA → `tools/prisma.py` — ⚠️ **الأرقام الحالية توضيحية (EXAMPLE)**، استبدلها بأرقامك الحقيقية قبل النشر |
| `sources.csv` | **جدول الاستخراج الرئيسي** — كل مصدر وكل حقل |
| `notes/*.md` | ملاحظة لكل ورقة مهمة (من القالب) |
| `templates/paper_note.md` | قالب الملاحظة |
| `problem_solution_matrix.md` | التوليف: مشكلة → حلول → أدلة → فجوة |

---

## حقول `sources.csv` | Schema

| العمود Column | إلزامي؟ | الوصف Description |
|---|---|---|
| `id` | تلقائي | رقم تسلسلي (auto) |
| `citekey` | تلقائي | `lastnameYEARfirstword` — يجب أن يطابق BibTeX |
| `title` | ✅ | العنوان الكامل |
| `authors` | ✅ | `Last, First; Last, First` |
| `year` | ✅ | سنة النشر |
| `venue` | ✅ | المجلة/المؤتمر |
| `type` | ✅ | `journal/conference/preprint/book/report/standard` |
| `doi` | ✅ | `10.xxxx/yyyy` (بدون https) |
| `url` | ⬜ | رابط مباشر |
| `problem_codes` | ✅ | من `taxonomy.md` — مفصولة بفاصلة |
| `solution_codes` | ✅ | من `taxonomy.md` |
| `method` | ✅ | `slr/survey_empirical/case_study/experiment/benchmark/position/design_science` |
| `contribution` | ⬜ | `taxonomy/framework/empirical_evidence/tool/review` |
| `venue_rank` | ⬜ | `Q1/Q2/Q3/Q4/na` |
| `evidence_strength` | ⬜ | `high/medium/low` |
| `include` | ✅ | `yes/no` |
| `status` | ⬜ | `to_read/reading/extracted/cited/excluded` |
| `quality_score` | ⬜ | ٠–٥ (تقييمك للجودة) |
| `notes` | ⬜ | ملاحظة قصيرة |

> شغّل `python tools/validate_sources.py` للتحقق من الاكتمال — يفشل الـCI إن نقص حقل إلزامي.

---

## الأوامر | Commands

```bash
# إضافة مصدر (يولّد id + citekey ويمنع التكرار بالـDOI/العنوان)
python tools/litkit.py add --title "..." --authors "..." --year 2026 \
  --venue "..." --doi 10.xxxx/yyyy --problem T1,O3 --solution S1,S8 --method slr

# بحث نصي في كل الحقول
python tools/litkit.py search "hallucination"

# إحصاءات (سنوات، أنواع، أكواد، حالة الإدراج)
python tools/litkit.py stats

# تحليل الفجوات 🔎
python tools/litkit.py gaps

# تصدير BibTeX → references/references_auto.bib
python tools/litkit.py export-bib
```

---

## سير عمل الفرز | Screening workflow

```
Search (search_strings.md)
   ↓  سجّل الأعداد في screening_log.csv
Deduplicate  (tools/litkit.py dedupe)
   ↓
Title/Abstract screening  → sources.csv (include=no للأسباب)
   ↓
Full-text screening       → literature/notes/*.md
   ↓
Extraction & coding       → sources.csv مكتمل
   ↓
Synthesis                 → problem_solution_matrix.md
```

**قاعدة ذهبية:** سجّل **سبب الاستبعاد** لكل ورقة مستبعدة في عمود `notes` — المحكمون يطلبون هذا الجدول غالباً كملحق.
