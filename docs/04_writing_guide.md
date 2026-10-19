# ✍️ دليل الكتابة الأكاديمية | Academic Writing Guide

> المحتوى الفعلي للمخطوطة يُكتب **بالإنجليزية**، والشرح هنا **عربي**.
> The manuscript is written in **English**; the guidance here is **Arabic**.

---

## 1) بنية الورقة | Paper structure (IMRaD)

| القسم Section | عدد الكلمات Words | وظيفته Function |
|---|---|---|
| Title | ١٠–١٥ كلمة | دقيق + يحتوي كلمات البحث |
| Abstract | ١٥٠–٢٥٠ | خلفية → فجوة → هدف → منهج → أهم نتيجة → أثر |
| Keywords | ٥–٧ | لا تكرّر كلمات العنوان |
| 1. Introduction | ٨٠٠–١٢٠٠ | قمْع مقلوب: عام ← خاص ← الفجوة ← السؤال ← المساهمة |
| 2. Related work | ١٢٠٠–٢٠٠٠ | **توليف نقدي** لا سرد أوراق |
| 3. Method | ١٠٠٠–١٥٠٠ | قابل للتكرار ١٠٠٪ |
| 4. Results | ١٢٠٠–١٨٠٠ | نتائج فقط — بلا تفسير |
| 5. Discussion | ١٢٠٠–١٨٠٠ | ماذا تعني النتائج + مقارنة بالأدبيات + نظرية |
| 6. Conclusion | ٥٠٠–٨٠٠ | إجابة السؤال + حدود + أبحاث مستقبلية |

---

## 2) معادلة المقدمة | Introduction funnel (٤ فقرات)

```
¶1  السياق العام وأهميته (٢–٣ جمل + أرقام/مراجع)
¶2  ما نعرفه حالياً (أهم اتجاهين أو ثلاثة)
¶3  الفجوة ⚠️ — جملة صريحة: "However, ... remains underexplored."
    ادعمها بأرقامك: "Only X of the Y reviewed studies addressed ..."
¶4  السؤال + المنهج + المساهمة (٣ نقاط مرقّمة bullets) + خريطة الورقة
```

**Contribution statement — اكتبها قبل أي شيء آخر** (٣ نقاط تبدأ بـفعل):
> *This study (1) proposes a unified taxonomy ...; (2) systematically compares ...; (3) identifies ... as an underexplored gap.*

---

## 3) بنك عبارات | Academic phrase bank

| الوظيفة Function | عبارة مقترحة Suggested wording |
|---|---|
| فجوة Gap | `... has received limited attention in the literature.` / `To the best of our knowledge, no study has ...` |
| هدف Aim | `This paper aims to ...` / `The present study sets out to ...` |
| منهج Method | `We conducted a systematic literature review following PRISMA 2020 guidelines.` |
| نتيجة Result | `Our analysis indicates that ...` / `The findings reveal a marked concentration of ...` |
| مقارنة Contrast | `In contrast to X, who found ..., our results suggest ...` |
| احتراز Hedging | `This may suggest ...` / `It is plausible that ...` / `The evidence points to ...` |
| حدود Limitation | `A key limitation is that ...; consequently, our findings should be interpreted with caution regarding ...` |
| أثر Implication | `For practitioners, ...` / `From a policy perspective, ...` |

> **الاحتراز Hedging مهم:** لا تكتب *"proves"* أو *"always"*. الأكاديمية = دقة + تواضع ادّعائي.

---

## 4) أخطاء لغوية شائعة (للكتّاب بالعربية) | Common errors for Arabic-native writers

| ❌ خطأ | ✅ صحيح | القاعدة Rule |
|---|---|---|
| `The study aim to...` | `The study aims to ...` | توافق الفاعل |
| `In the other hand` | `On the other hand` | collocation |
| `According to Smith (2020), he said...` | `Smith (2020) argues that ...` | تجنّب التكرار |
| `AI are changing` | `AI is changing` | AI اسم غير معدود |
| `This paper will discuss` | `This paper discusses` | لا تستخدم المستقبل للوصف |
| `Researches show` | `Research shows` / `Studies show` | research غير معدود |
| جملة من ٦٠ كلمة | ١٥–٢٥ كلمة | جملة = فكرة واحدة |
| `very important` | `critical` / `pivotal` | تجنّب المبالغات العامة |

**نصائح سريعة:**
- استخدم المبني للمعلوم أكثر: *We coded, We compared* (أوضح وأقصر).
- زمن الأفعال: المضارع للحقائق الثابتة (*the literature shows*)، الماضي لما فعلته أنت (*we screened 1,240 records*).
- كل فقرة تبدأ بجملة موضوعية (topic sentence) وتنتهي بربط للتي بعدها.

---

## 5) الاقتباس والمراجع | Citation hygiene

- **لا تقتبس مرجعاً لم تقرأه.** (الأدوات التوليدية تختلق مراجع — تحقّق من كل DOI.)
- اقتبس **المرجع الأصلي** لا المرجع الذي نقله.
- لا تكدّس ١٠ مراجع في جملة واحدة؛ اختر أقواها ٢–٣.
- كل `citekey` في المتن يجب أن يوجد في `references/references.bib` (يفحصه `validate_sources.py` لاحقاً).
- صيغة APA 7 أم IEEE؟ **حسب المجلة** — وحّدها من البداية ولا تخلط.

---

## 6) روتين كتابة فعّال | Writing routine

1. اكتب المسودة **بدون تعديل** (write ugly first).
2. عدّل في جولة منفصلة: البنية → الحجة → الوضوح → اللغة.
3. اقرأ فقرتك بصوت عالٍ — الجملة التي تتعثّر فيها تحتاج إعادة كتابة.
4. راجع بعد ٢٤ ساعة؛ ثم سلّمها للمشرف.
5. احتفظ بكل نسخة: `manuscript/` تحت Git = تاريخ كامل لكل تعديل.

---

## 7) أدوات مساعدة | Tools

| الحاجة | أداة مجانية |
|---|---|
| قواعد لغوية | LanguageTool / Grammarly |
| إعادة صياغة | DeepL Write |
| تدقيق التشابه | Turnitin / iThenticate (عبر جامعتك) |
| إدارة المراجع | Zotero + BibTeX → `references/references.bib` |
| تحويل Markdown → LaTeX | Pandoc |
