# 🔬 AI Research Workspace — بيئة بحث أكاديمي في الذكاء الاصطناعي

> **English (EN)** — A ready-to-use research workspace for a Master's thesis on *contemporary problems of Artificial Intelligence and their solutions*, built for the goal of **publishing in an international, indexed (Scopus Q1/Q2) AI journal**.
> **العربية (AR)** — مساحة عمل بحثية جاهزة لرسالة ماجستير في *مشاكل الذكاء الاصطناعي المعاصرة وحلولها*، مبنية بهدف **النشر في مجلة عالمية مفهرسة (Scopus Q1/Q2) في الذكاء الاصطناعي**.

المستودع يغطي دورة البحث كاملة: **تحديد الموضوع → مراجعة الأدبيات المنهجية (PRISMA) → التحليل والتجارب → كتابة المخطوطة → إرسال للنشر**.
The repository covers the full research cycle: **topic definition → systematic literature review (PRISMA) → analysis & experiments → manuscript writing → journal submission**.

---

## 🗺️ خريطة المستودع | Repository map

| المسار / Path | المحتوى — عربي | Content — EN |
|---|---|---|
| `docs/00_START_HERE.md` | 🚀 ابدأ من هنا — خطواتك للأيام الأولى | Start here — your first-week plan |
| `docs/01_topic_selection.md` | 🎯 تضييق الموضوع + ١٢ فكرة بحثية جاهزة (فجوة + سؤال + منهجية) | Scoping the topic + 12 ready research ideas |
| `docs/02_research_plan.md` | 🗓️ خطة زمنية ٩ أشهر بمخرجات واضحة | 9-month plan with deliverables |
| `docs/03_methodology.md` | 🧪 اختيار المنهجية (PRISMA / Survey / Design Science) | Methodology selection guide |
| `docs/04_writing_guide.md` | ✍️ قواعد الكتابة الأكاديمية بالإنجليزية + بنك عبارات | Academic writing rules + phrase bank |
| `docs/05_publishing_guide.md` | 📤 اختيار المجلة، الإرسال، الرد على المحكمين | Journal choice, submission, rebuttal |
| `docs/06_ethics_integrity.md` | ⚖️ الأمانة العلمية وإفصاح استخدام الذكاء الاصطناعي | Research integrity & AI-use disclosure |
| `literature/` | 📚 قاعدة المصادر، التصنيف، مصفوفة المشكلة↔الحل | Source database, taxonomy, problem↔solution matrix |
| `literature/taxonomy.md` | 🧩 تصنيف المشاكل (تقنية + تنظيمية) بأكواد | Problem taxonomy with codes (T1…, O1…) |
| `literature/problem_solution_matrix.md` | 🔗 ربط كل مشكلة بالحلول والأدلة والفجوة | Problem → solutions → evidence → gap |
| `tools/` | 🛠️ سكربتات Python (إدارة المصادر، PRISMA، فحص الجودة) | Python scripts (lit manager, PRISMA, QA) |
| `experiments/` | 📊 نوتبوكات وسكربتات تحليل | Notebooks & analysis scripts |
| `manuscript/` | 📝 فصول المخطوطة (هيكل IMRaD) | Manuscript chapters (IMRaD) |
| `references/` | 🔖 ملف BibTeX | BibTeX library |
| `submission/` | 📨 قوائم المجلات، خطاب التغطية، الرد على المحكمين | Journal shortlist, cover letter, rebuttal |

---

## ⚡ التشغيل السريع | Quick start (5 min)

```bash
# 1) تثبيت بيئة Python — environment setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # أو: pip install pandas matplotlib jupyter (اختياري)

# 2) جرّب أدوات المستودع (تعمل بمكتبات Python القياسية فقط) — stdlib-only tools
python tools/litkit.py init                       # يتأكد من وجود ملفات CSV بالعناوين الصحيحة
python tools/litkit.py add --title "A Survey on Hallucination in Large Language Models" \
  --authors "Huang, Lei; Yu, Weijiang; Ma, Weitao" --year 2025 --venue "ACM TOIS" \
  --doi 10.1145/3703155 --problem T1 --solution S1,S8 --method literature_review
python tools/litkit.py stats                      # إحصاءات: سنوات، أنواع، أكواد المشاكل
python tools/litkit.py gaps                       # 🔎 أين الفجوة البحثية؟ أقل المشاكل تغطيةً
python tools/prisma.py                            # مخطط PRISMA للأرقام
python tools/validate_sources.py                  # فحص جودة جدول المصادر

# 3) شغّل الاختبارات — tests
python -m pytest tests/ -q
```

> 💡 لا حاجة لتثبيت أي مكتبة لتشغيل `tools/` و`tests/` — مكتوبة بمكتبات Python القياسية.
> No installs needed for `tools/` and `tests/` — pure standard library.

---

## 🔁 دورة العمل | The workflow loop

```
1. SCOPE      → docs/01_topic_selection.md        (اختيار الزاوية + سؤال البحث)
2. SEARCH     → literature/search_strings.md      (استعلامات Scopus/WoS/IEEE/arXiv)
3. SCREEN     → literature/screening_log.csv      (حسب PRISMA 2020)
4. EXTRACT    → literature/sources.csv            (جدول الاستخراج الموحّد)
5. SYNTHESIZE → literature/problem_solution_matrix.md
6. ANALYZE    → experiments/notebooks/
7. WRITE      → manuscript/
8. SUBMIT     → submission/
```

---

## 🤝 ملاحظات للمشرف | For the supervisor

- كل ملف CSV له **عناوين أعمدة موثّقة** داخل `literature/README.md` → النتائج قابلة للتدقيق (auditability).
- `tools/validate_sources.py` يشتغل تلقائياً في GitHub Actions على كل Push (انظر `.github/workflows/research-ci.yml`) → يمنع تراكم المصادر الناقصة.
- الأكواد (T1…T12 / O1…O10 / S1…S12) ثابتة في `literature/taxonomy.md` → تسمح بتجميع المصادر إحصائياً لاحقاً.

---

## 📄 الترخيص | License

مساحة عمل بحثية خاصة — يُنصح بإضافة `LICENSE` قبل جعل المستودع عاماً إذا كانت المخطوطة ستُنشر بوصول مفتوح (CC BY).
Research workspace — add a `LICENSE` before making the repo public if the manuscript will be open access (CC BY).
