# 🛠️ أدوات المستودع | Tools

> كل الأدوات **بدون أي مكتبة خارجية** (Python القياسية فقط) — تعمل مباشرة على Python 3.9+.
> All tools are **stdlib-only** (Python 3.9+). No pip install needed.

---

## `litkit.py` — مدير الأدبيات | literature manager

| الأمر Command | الوظيفة What it does |
|---|---|
| `init` | ينشئ `literature/sources.csv` و`screening_log.csv` بالعناوين الصحيحة |
| `add` | يضيف مصدراً، يولّد `id` و`citekey`، ويرفض التكرار (بالـDOI أو العنوان) |
| `search QUERY` | بحث نصي في كل الحقول |
| `stats` | إحصاءات: سنة، نوع، منهجية، تصنيف، حالة، أكواد |
| `gaps` | 🔎 **أهم أمر**: ترتيب المشاكل بالتغطية لاكتشاف الفجوة البحثية |
| `dedupe [--apply]` | كشف/حذف المكرّر |
| `export-bib [--out]` | تصدير BibTeX → `references/references_auto.bib` |

```bash
python tools/litkit.py add --title "..." --authors "Doe, Jane; Smith, Ali" \
  --year 2026 --venue "Expert Systems with Applications" --doi 10.1016/j.eswa.2026.1 \
  --problem T1,T5 --solution S1,S4 --method experiment --rank Q1 --evidence high
```

**أكواد الخروج | Exit codes:** `0` نجاح · `1` خطأ عام · `2` مصدر مكرّر

---

## `prisma.py` — مخطط PRISMA 2020

```bash
python tools/prisma.py           # مخطط نصي + تفصيل لكل قاعدة + فحص اتساق
python tools/prisma.py --csv     # الأرقام فقط (للنسخ إلى جدول)
```

يفحص أن: `identified − duplicates = screened`، و`screened − excluded = fulltext`،
و`fulltext − excluded = included`. **أي عدم اتساق = سبب رفض شائع.**

---

## `validate_sources.py` — فحص الجودة | QA

```bash
python tools/validate_sources.py            # التحذيرات لا تفشل الأمر
python tools/validate_sources.py --strict   # التحذيرات = أخطاء (يستخدمه الـCI)
```

يفحص: الحقول الإلزامية، صحة السنة، صيغة DOI، تكرار `id`/`citekey`/`DOI`/العنوان،
وصحة قيم التعداد (type, method, contribution, rank, evidence, include, status) وأكواد `T#/O#/S#`.

---

## إضافة أداة جديدة | Adding a tool

1. أنشئ `tools/mytool.py` بمكتبات قياسية فقط (إن أمكن).
2. أضف `--root` لتحديد مجلد المستودع (يستخدمه الاختبار).
3. أضف اختباراً في `tests/test_tools.py`.
4. ثبّت أي مكتبة جديدة في `requirements.txt`.
