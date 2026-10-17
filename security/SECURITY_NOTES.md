# 📋 ملاحظات المراجعة الأمنية — كود PumpBot (مراجعة يدوية)

> مراجعة يدوية لكود `bot/` و`data/` و`.github/workflows/`.
> التاريخ: 2026-10-17 · الحالة: ملاحظات مفتوحة — لم يُطبّق أي إصلاح بعد.

---

## 🔴 عالية الخطورة

### S-01 — المستودع **عام** (public) وبيانات التداول مكشوفة
- **أين:** `https://github.com/abdaibsololy-netizen/Task` (تم التحقق: `isPrivate: false`)
- **الوصف:** الكود كامل + `master_wallet_data.txt` + `master_wallet_analysis.csv` + تحليل الاستراتيجية
  (`analysis/*.md`) منشورة للجميع. هذا يعني:
  - أي شخص يعرف **محفظة المتداول المستهدف** (`2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb`)
    والمنطق الذي يتبعه → يستطيع **التسابق أمامك** (front-run) على الصفقات المنسوخة.
  - قواعد الدخول/الخروج كاملة (MCap 2–8K، وعمر 18–72h، لقطات 1.9/3.5/4.0) → يمكن لناسخ
    بناء بوت منافس بنفس الشروط بدقة.
  - المنهجية كلها (كيف تستخرج قواعد المتداول من بياناته) قابلة للتكرار على أي محفظة أخرى.
- **الأثر:** خسارة مالية مباشرة من تكرار صفقاتك + تسريب أصولك الفكرية.
- **الإصلاح المقترح:**
  1. اجعل المستودع **private** فوراً (Settings → Danger zone → Change visibility).
  2. أو: انقل الكود إلى مستودع خاص، واترك في العام فقط التقرير/المنهجية بلا مفاتيح.
  3. دوّر `HELIUS_API_KEY` / `PUMPBOT_PRIVATE_KEY` إن وُضع أيٌّ منها في الملف سابقاً.
  4. بيانات المحفظة (`master_wallet_*`) — احذفها من التاريخ العام أو استخدم حساباً وهمياً.

### S-02 — مفتاح التوقيع في **query string** (تسريب في السجلات)
- **أين:** `bot/executor.py:73` → `s.post(self.trade_api + "?api-key=" + key, ...)`
- **الوصف:** `PUMPBOT_PRIVATE_KEY` (مفتاح محفظتك) يُرسل كـ **جزء من الرابط** لا كترويسة.
  الروابط تُسجَّل في: سجلات الوصول (access logs)، الـ proxies، الـ CDN،قد تُرسل في `Referer` عند أي إعادة توجيه، وتظهر في `ps`/history عند فشل الطلب.
- **الأثر:** تسريب مفتاح المحفظة = **سحب كاملAssets** من أي شخص يقرأ السجل.
- **الإصلاح:** أرسل المفتاح في ترويسة:
  ```python
  headers={"x-api-key": key}          # PumpPortal يدعم الترويسة
  # أو على الأقل: لا تطبع استجابة الخادم في bot.log
  ```
  وأضف قناعاً على أي طباعة: `text[:200]` → استبدل `key` بـ `***` قبل الطباعة.

### S-03 — مفتاح Helius داخل رابط WebSocket
- **أين:** `bot/copytrade.py:27` → `HELIUS_WS = "wss://atlas-mainnet.helius-rpc.com/?api-key={key}"`
- **الوصف:** نفس المشكلة — الرابط كامل（التي تحوي المفتاح) قد يُسجَّل في سجلات الوسيط/الـ proxy.
- **الأثر:** تسريب مفتاح RPC (Allowlist Spec) → overuse ومصاريف.
- **الإصلاح:** استخدم ترويسة `x-api-key` إن دعمها Helius، وإلا دوّر المفتاح دورياً
  وحدّد سقفاً للاستخدام.

---

## 🟠 متوسطة الخطورة

### S-04 — ملفات الحالة والمقاييس غير مستثناة في `.gitignore`
- **أين:** `.gitignore` (يتجاهل `bot_state.json` فقط) مقابل `bot/config.yaml` → `alpha_state.json`،
  `copy_state.json`، و`bot/.alert_state.json`.
- **الوصف:** عند التشغيل محلياً تُنشأ هذه الملفات (المراكز، الأرباح،PnL) وبصلاحيات افتراضية
  `0644` (قابلة للقراءة من أي مستخدم على الجهاز) — وقد تُرفع بالغلط إلى Git.
- **الإصلاح:**
  ```gitignore
  *state.json
  .alert_state.json
  *.log
  ```
  وفي `bot/portfolio.py` أنشئ الملف بـ `os.open(..., 0o600)`.

### S-05 — نموّ الذاكرة بلا حدّ في وضع 24/7
- **أين:** `bot/alpha.py` → `self.windows` (دكت لكل mint) و`self.meta_cache` و`self.activity`،
  و`bot/family.py:55` → `self.members` (لا يُ prune أبداً).
- **الوصف:** البوت مصمَّم للتشغيل continuous على VPS. كل عملة جديدة تُخزَّن مؤقتاً للأبد
  (dict لا يُمسح). بعد أيام من التشغيل تستهلك الذاكرة مئات الميغابايت حتى gigs.
- **الأثر:** استهلاك موارد/DoS على الخادم → توقف البوت في أسوأ لحظة (أثناء صفقة مفتوحة).
- **الإصلاح:** أضف purge دوري (كل N دقيقة) يحذف mints الأقدم من 6 ساعات من
  `windows`/`activity`/`meta_cache`، و`members` من `family`.

### S-06 — `MODE=live` لا يعمل في وضع alpha (خلل أمان تشغيلي)
- **أين:** `bot/main.py` + `bot/alpha.py:57` (`self.live = cfg.get("mode") == "live"`)
  مقابل `bot/copytrade.py:66` (`os.environ.get("MODE", ...)`).
- **الوصف:** `bot/README.md` يشرح `MODE=live python main.py` للتداول الحقيقي، لكن في وضع
  **alpha** هذا الأمر **لا يفعل شيئاً** (يبقى paper) — بينما في وضع copy يشغّل التداول الحقيقي.
 vice-versa: `mode: live` في `config.yaml` يشغّل التداول الحقيقي في alpha **فوراً** بلا تأكيد.
- **الأثر:** التداول حقيقي غير مقصود (خسارة مباشرة) أو — الأخطر — ظنّك أنك تختبر
  live وأنت paper (أو العكس).
- **الإصلاح:** وحّد مصدر التفعيل في مكان واحد + **تأكيد صريح**:
  ```python
  if mode == "live" and os.environ.get("I_UNDERSTAND_LIVE") != "1":
      raise SystemExit("❌ وضع LIVE يحتاج I_UNDERSTAND_LIVE=1")
  ```
  وسجّل في السجل: "LIVE MODE" + عنوان المحفظة عند التشغيل.

### S-07 — HTML injection في تنبيهات تيليجرام
- **أين:** `bot/alert_loop.py` → `build_message()` تبني رسالة بـ `parse_mode: HTML` وتُدخل
  `p['sym']` (رمز العملة القادم من API خارجي) بدون تهريب.
- **الوصف:** رمز يحوي `<b>` أو `<a href="https://evil">` يُدرج HTML خاماً — رسالة تصيّد/رابط مزيف في التنبيه الرسمي.
- **الإصلاح:** `html.escape(p['sym'])` قبل الإدراج، أو بدّل `parse_mode` إلى `None` (نص عادي).

### S-08 — `actions/*` مثبّتة بـ major version فقط (supply chain)
- **أين:** `.github/workflows/alerts.yml` → `actions/checkout@v4`, `actions/setup-python@v5`,
  `actions/cache@v4`.
- **الوصف:** تثبيت بـ tag تاريخي ممكن التعديل عليه (delegated tag) → خطر supply-chain.
- **الإصلاح:** ثبّت بـ **SHA كامل** (`uses: actions/checkout@<40-char-sha> # v4.2.2`).

---

## 🟡 منخفضة الخطورة / تحصين

| # | الملاحظة | المكان | المقترح |
|---|---|---|---|
| S-09 | `urllib.request.urlopen` على روابط خارجية بلا تحقق من المخطّط | `bot/alert_loop.py:46,162`، `data/collect_wallet.py:29,42`، `data/shadow_collector.py:33` | تأكد أن الرابط يبدأ بـ `https://` (bandit B310) |
| S-10 | استجابات API الخام تُطبع في السجل | `bot/executor.py:80-82` | لا تطبع body الخادم كاملاً؛ سجّل code فقط |
| S-11 | `Portfolio.load()` لا تتحقق من صحة ملف الحالة | `bot/portfolio.py:26-33` | `try/except` + تحقق من الحقول (ملف قابل للتعديل خارجياً) |
| S-12 | لا يوجد `timeout` موحّد لكل الطلبات | `bot/scanner.py` (محدد ✅)، `data/*` | تأكد أن كل طلب شبكة له timeout |
| S-13 | `bandit`: 5 ملاحظات B310 (كلها false-positive — روابط ثابتة) | `bot/`, `data/` | أضف `# nosec B310` مع تعليق يوضّح السبب |
| S-14 | `assert` في سكربتات الإنتاج (يزول مع `-O`) | `data/collect_wallet.py:247` | استبدلها برمي `RuntimeError` |

---

## ✅ أشياء سليمة (لا تغيّرها)

- `yaml.safe_load` في `bot/main.py` ✅ (لا `yaml.load` غير آمن)
- لا أسرار مسرّبة في الملفات ولا في تاريخ git (تحقّق: `security/secrets_scan.py`) ✅
- `Portfolio.save()` كتابة ذرّية (`tmp` + `os.replace`) ✅
- `permissions: contents: read` في الـ workflow ✅
- لا `pull_request_target` ولا `workflow_dispatch` بمكتبة غير موثوقة ✅
- الأسرار عبر متغيرات البيئة وGitHub Secrets فقط ✅
- `bandit`: صفر ملاحظات High على `bot/` و`data/` (بعد استثناء الـ venv) ✅

---

## 🎯 ترتيب المعالجة المقترح

1. **اليوم:** اجعل المستودع private (S-01) + انقل المفتاح من query string إلى ترويسة (S-02)
2. **اليوم:** أضف `*state.json` إلى `.gitignore` (S-04)
3. **خلال أيام:** purge للذاكرة (S-05) + توحيد تفعيل live مع تأكيد (S-06)
4. **خلال أسبوع:** تهريب HTML (S-07) + تثبيت actions بـ SHA (S-08)
