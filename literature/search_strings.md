# 🔎 استعلامات البحث | Search Strings

> **شرط أساسي للنشر:** يجب أن تكون استراتيجية البحث **قابلة للتكرار** — انسخ هذه الاستعلامات حرفياً وسجّل تاريخ التنفيذ وعدد النتائج في `screening_log.csv`.
> Publishing requirement: the search must be **reproducible** — copy these verbatim, log execution date + hit counts.

---

## 1) مفردات البحث | Concept blocks

| الرمز | المفهوم | المصطلحات |
|---|---|---|
| **A** | الذكاء الاصطناعي | `"artificial intelligence"` OR `"AI"` OR `"machine learning"` OR `"large language model*"` OR `LLM*` OR `"generative AI"` OR `"genAI"` OR `"foundation model*"` |
| **B** | المشاكل | `challenge*` OR `problem*` OR `risk*` OR `barrier*` OR `limitation*` OR `failure` OR `hallucination*` OR `bias` OR `"privacy"` OR `"security"` OR `"explainab*"` OR `"trust"` |
| **C** | الحلول | `solution*` OR `mitigation*` OR `framework*` OR `governance` OR `"retrieval-augmented"` OR `RAG` OR `"human-in-the-loop"` OR `guardrail*` OR `benchmark*` OR `"best practice*"` |
| **D** | السياق التنظيمي | `organi?ation*` OR `enterprise*` OR `adoption` OR `implementation` OR `"information system*"` |

**الاستعلام الأساسي | Master query:** `A AND B AND C`
**نسخة تنظيمية | IS-oriented:** `A AND B AND (C OR D)`

---

## 2) استعلامات جاهزة لكل قاعدة | Per-database queries

### Scopus
```
TITLE-ABS-KEY ( ( "artificial intelligence" OR "machine learning" OR
"large language model*" OR "generative ai" OR "foundation model*" )
AND ( challenge* OR problem* OR risk* OR barrier* OR hallucination* OR bias )
AND ( mitigation* OR solution* OR framework OR governance OR
"retrieval-augmented" OR guardrail* ) )
AND PUBYEAR > 2022 AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

### Web of Science
```
TS=(("artificial intelligence" OR "large language model*" OR "generative AI")
AND (challenge* OR risk* OR hallucination* OR barrier*)
AND (mitigation* OR solution* OR framework OR governance))
AND PY=(2023-2026) AND LA=(English)
```

### IEEE Xplore
```
("Abstract":("large language model" OR "generative AI")
 AND "Abstract":(challenge* OR hallucination* OR risk*)
 AND "Abstract":(mitigation* OR framework OR governance))
Filters: 2023–2026, Journals + Conferences
```

### ACM Digital Library
```
[[Abstract: "large language model"] OR [Abstract: "generative AI"]]
AND [[Abstract: "challenge"] OR [Abstract: "hallucination"]]
AND [[Abstract: "mitigation"] OR [Abstract: "governance"]]
Publication Year: 2023–2026
```

### arXiv (للمواد الحديثة — سجّلها كـ`preprint`)
```
http://export.arxiv.org/api/query?search_query=abs:%22hallucination%22+AND+abs:%22large+language+model%22&start=0&max_results=200&sortBy=submittedDate&sortOrder=descending
```

### Google Scholar (للبحث المتشعب backward/forward)
استخدم Publish or Perish أو الإشعارات الشهرية، وسجّل أول ٢٠٠ نتيجة مرتبة بالصلة.

---

## 3) سجل التنفيذ | Execution log (انسخه إلى `screening_log.csv`)

| قاعدة البيانات Database | التاريخ Date | الاستعلام Query ID | عدد النتائج Hits |
|---|---|---|---|
| Scopus | | Master | |
| Web of Science | | Master | |
| IEEE Xplore | | Master | |
| ACM DL | | Master | |
| arXiv | | Master | |
| **الإجمالي قبل إزالة التكرار** | | | |

---

## 4) تنبيهات | Alerts

فعّل إشعاراً أسبوعياً حتى لا يفوتك جديد المجال أثناء الكتابة:
- Scopus / WoS: Saved search → Alert
- Google Scholar: `scholar.google.com` → Follow + Alerts
- arXiv: RSS للفئات `cs.AI`, `cs.CL`, `cs.LG`
- أضف كل جديد مباشرة: `python tools/litkit.py add --status to_read ...`
