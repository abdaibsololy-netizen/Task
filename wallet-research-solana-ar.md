# دراسة أداء التداول والربح والخسارة لمحفظة Solana

**تاريخ اللقطة:** 8 أكتوبر 2026 (UTC)
**الشبكة:** Solana Mainnet
**عنوان المحفظة:** `2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb`

> **الخلاصة المباشرة:** واجهة Vybe لحساب PnL التاريخي تسجل للمحفظة ربحًا محققًا **+$2,835.64**، وربحًا/خسارة غير محققة **−$115.84**؛ مجموع الحقلين حسابيًا **+$2,719.80**. هذا تقدير أداء تداول من مزوّد بيانات، وليس رصيد المحفظة أو كشفًا نقديًا مدققًا. سجلّها يغلب عليه تدوير صفقات صغيرة على ميم كوينات حديثة من Pump.fun، مع دخول متكرر قرب $115–$121 وبيع على دفعة أو دفعات. توجد مراكز مفتوحة وتسعيرات ناقصة، لذا لا يصح اعتبار الربح غير المحقق نقدًا مضمونًا.

## 1. أرقام الأداء التي أرجعها Vybe

طلبتُ سجل `resolution=Full` لمحفظة العنوان أعلاه. هذه قيم الملخص كما أعادها endpoint وقت الفحص، مع التقريب إلى السنت:

| المقياس | القيمة | ملاحظة |
|---|---:|---|
| PnL محقق تاريخيًا | **+$2,835.64** | من المراكز التي صنّفها المزوّد كمحققة |
| PnL غير محقق | **−$115.84** | يتضمن صف Wrapped SOL المفتوح؛ بعض توكنات الميم المفتوحة لا يملك المزوّد لها سعرًا (`null`) |
| مجموع الحقلين حسابيًا | **+$2,719.80** | ليس ربحًا نقديًا قابلًا للسحب ولا قيمة المحفظة الحالية |
| عدد الأصول في الملخص | **35** | صفوف التفصيل تشمل Wrapped SOL؛ بقية الصفوف 34 مِنتًا بأسماء/رموز ميم، وعناوينها تنتهي بـ`pump` |
| عدد الصفقات المبلغ عنه | **91** | كما ورد في الملخص |
| حجم التداول المبلغ عنه | **$22,716.13** | حجم إجمالي وفق المزوّد؛ لا يُعاد جمع أحجام صف Wrapped SOL مع بقية التوكنات كأنها صفقات مستقلة |
| متوسط حجم الصفقة | **$249.63** | كما ورد في الملخص |
| نسبة الفوز المعلنة | **84.62%** | غير مؤكدة حسابيًا: الملخص يسجل 77 رابحة وواحدة خاسرة من أصل 91؛ تبقى 13 غير مفسرة ضمن الحقول المنشورة |
| أفضل مِنت حسب PnL المحقق | **AORP: +$281.88** | المِنت `G7UJP…pump`، وليس كل توكن يحمل الرمز AORP إن وُجد غيره |
| أسوأ مِنت حسب PnL المحقق | **ATFS: −$2.88** | المِنت `HE2k…pump`; يوجد مِنت آخر بالرمز نفسه ربح +$1.89 |

**تنبيه قراءة:** جمع الربح المحقق وغير المحقق يعطي +$2,719.80 حسابيًا، لكنه لا يثبت صافي ما كسبه صاحب المحفظة من كل مصادر الأموال. وثائق Vybe تقول إن مقاييس PnL مشتقة من أسواق «موثّقة/مفلترة»؛ لذلك يمكن أن تختلف عن إعادة بناء كل تحويل على السلسلة، كما أن الأسعار غير المتاحة والمراكز المفتوحة تؤثر في الإجمالي. وتغير تقدير PnL غير المحقق بنحو $6 خلال قراءات متقاربة في الجلسة نفسها، وهو مقياس متحرك.

### نتيجة آخر سبعة أيام في بيانات Vybe

السلسلة اليومية التي أعادتها الواجهة للأيام 1–7 أكتوبر 2026 موجبة في كل يوم، ومجموعها **+$997.12**:

| اليوم (UTC) | PnL اليومي |
|---|---:|
| 1 أكتوبر | +$249.07 |
| 2 أكتوبر | +$63.10 |
| 3 أكتوبر | +$80.82 |
| 4 أكتوبر | +$369.04 |
| 5 أكتوبر | +$128.83 |
| 6 أكتوبر | +$94.32 |
| 7 أكتوبر | +$11.93 |
| **المجموع** | **+$997.12** |

## 2. تفصيل كل مِنت تداولته المحفظة

الأرقام التالية هي أحجام الشراء والبيع وPnL لكل صف كما أرجعته واجهة Vybe، مقربة إلى سنت. **العنوان الكامل للمِنت قابل للنقر لفتح صفحة Solscan**. الرموز متكررة بين مِنتات مختلفة؛ لذلك يجب مطابقة العنوان، لا الرمز وحده. بيانات الشراء والبيع أحجام بالدولار كما حسبها المزوّد، وليست بالضرورة كشفًا صافيًا بعد كل الرسوم.

### مِنتات الميم التي تحقق لها PnL محقق (28 مغلقًا + مركز XRPN جرى بيع جزء منه)

| الرمز/اسم المِنت كما ظهر | عنوان المِنت | شراء USD | بيع USD (عدد عمليات البيع) | PnL محقق USD | الحالة |
|---|---|---:|---:|---:|---|
| AORP — American Oil Relief Program | [`G7UJPfu4Xh4Lv5H1ETmwn1Q9uMScw3GSFgBqzKppump`](https://solscan.io/token/G7UJPfu4Xh4Lv5H1ETmwn1Q9uMScw3GSFgBqzKppump) | $117.45 | $399.33 (2) | **+$281.88** | مغلق |
| SARP | [`GGMm5EmstNMQh4tvR127joSzBDa5UeE4FkVYZZmtpump`](https://solscan.io/token/GGMm5EmstNMQh4tvR127joSzBDa5UeE4FkVYZZmtpump) | $119.31 | $395.64 (2) | **+$276.33** | مغلق |
| SARP — Strategic American Protocol | [`6WbiJtjXoNpLH6GhSvDX4HqRUN3ShQgxsk56Synpump`](https://solscan.io/token/6WbiJtjXoNpLH6GhSvDX4HqRUN3ShQgxsk56Synpump) | $118.26 | $384.60 (3) | **+$266.34** | مغلق |
| WOTF — World Oil Trust Fund | [`6DWHBW3R5NE2LUShJRbvDyi9GZ8Hz4EFFRgcfP3apump`](https://solscan.io/token/6DWHBW3R5NE2LUShJRbvDyi9GZ8Hz4EFFRgcfP3apump) | $120.02 | $326.89 (3) | **+$206.87** | مغلق |
| GOIF | [`qTyZGgDKVH1fZNhBAnGcUgtyVbVrWZ3uNeuCgJ4pump`](https://solscan.io/token/qTyZGgDKVH1fZNhBAnGcUgtyVbVrWZ3uNeuCgJ4pump) | $121.02 | $308.28 (2) | **+$187.26** | مغلق |
| DOTF | [`tY5KSvxu3iBMwVZzVpYqrVbxAVbAXMKTJ7SxW6Wpump`](https://solscan.io/token/tY5KSvxu3iBMwVZzVpYqrVbxAVbAXMKTJ7SxW6Wpump) | $119.34 | $296.62 (2) | **+$177.28** | مغلق |
| GOIF — Global Oil Institution Fund | [`waW5EVqWFtDVpwoudzYQxCoP8DCFUz91trdyg2Zpump`](https://solscan.io/token/waW5EVqWFtDVpwoudzYQxCoP8DCFUz91trdyg2Zpump) | $116.49 | $292.05 (2) | **+$175.56** | مغلق |
| XRPN — EVERNORTHXRP | [`iTbVzEXiw7eC9ftbv5eNVCQUrY64AQLHCfgW4DGpump`](https://solscan.io/token/iTbVzEXiw7eC9ftbv5eNVCQUrY64AQLHCfgW4DGpump) | $120.05 | $226.25 (2) | **+$136.21** | مفتوح جزئيًا؛ بقيت كمية من المركز |
| UDR | [`5iURQEWL4NcbqhXRnhssfCzhAnghWbEGUoTWiWhpump`](https://solscan.io/token/5iURQEWL4NcbqhXRnhssfCzhAnghWbEGUoTWiWhpump) | $178.10 | $307.92 (1) | **+$129.82** | مغلق |
| NTDA — National Trump Digital Accounts | [`76R3Mbb3w66VQg7u7tQHoCMqq6QofD59bncoZKnpump`](https://solscan.io/token/76R3Mbb3w66VQg7u7tQHoCMqq6QofD59bncoZKnpump) | $116.21 | $234.08 (2) | **+$117.87** | مغلق |
| VSOF | [`CnrPtHUeeM6QtHjkEArLF68B2pf2TvhJfSvShaQpump`](https://solscan.io/token/CnrPtHUeeM6QtHjkEArLF68B2pf2TvhJfSvShaQpump) | $116.67 | $234.51 (3) | **+$117.84** | مغلق |
| WSOS — World Strategic Oil Supply | [`tCHCHiqVVcsL69ab94xGHV8zdpKyFYNiz92Behjpump`](https://solscan.io/token/tCHCHiqVVcsL69ab94xGHV8zdpKyFYNiz92Behjpump) | $116.11 | $231.25 (2) | **+$115.13** | مغلق |
| AROS | [`GC9GWsd9mQhj4GWpUQBxw7peBEimGjgpUrGgkWBpump`](https://solscan.io/token/GC9GWsd9mQhj4GWpUQBxw7peBEimGjgpUrGgkWBpump) | $116.71 | $227.88 (1) | **+$111.18** | مغلق |
| NTDA | [`fSK8y3f3Hz1mTeSYap6FeqhZ8ResekAAuhZYddnpump`](https://solscan.io/token/fSK8y3f3Hz1mTeSYap6FeqhZ8ResekAAuhZYddnpump) | $118.84 | $205.47 (1) | **+$86.63** | مغلق |
| VSOF — Vanguard Strategic Oil Fund | [`nktiJ91NxzY8Dq1JB6YvZq97bpCiELxrRgBzwKupump`](https://solscan.io/token/nktiJ91NxzY8Dq1JB6YvZq97bpCiELxrRgBzwKupump) | $116.13 | $199.53 (1) | **+$83.40** | مغلق |
| VSOF | [`6BfTBNYJcZW9AnxRQ7aAx4Luf2K4BpmWpR7FWTPZpump`](https://solscan.io/token/6BfTBNYJcZW9AnxRQ7aAx4Luf2K4BpmWpR7FWTPZpump) | $116.67 | $196.12 (2) | **+$79.45** | مغلق |
| DOTF | [`4cYJ8eGZaKMF1iuoUXskhfTHSi6VxL7Jq7xaTJHbpump`](https://solscan.io/token/4cYJ8eGZaKMF1iuoUXskhfTHSi6VxL7Jq7xaTJHbpump) | $116.56 | $180.62 (1) | **+$64.06** | مغلق |
| AROS | [`1Atst4LcMEYfAXACbCaBpdk166CU8eopNkjyD8jpump`](https://solscan.io/token/1Atst4LcMEYfAXACbCaBpdk166CU8eopNkjyD8jpump) | $120.49 | $171.51 (1) | **+$51.02** | مغلق |
| USDF — United States Dividend Fund | [`tYLAYuNEJbuvDzuERBHSHAeVFZTgkkSLPwrRwHzpump`](https://solscan.io/token/tYLAYuNEJbuvDzuERBHSHAeVFZTgkkSLPwrRwHzpump) | $175.33 | $209.24 (1) | **+$33.91** | مغلق |
| GOIF | [`apy9dR4PyLzqAs6eZHKDLsLRE1qbc6GHaGsgaNTpump`](https://solscan.io/token/apy9dR4PyLzqAs6eZHKDLsLRE1qbc6GHaGsgaNTpump) | $119.56 | $147.69 (1) | **+$28.13** | مغلق |
| GOIF | [`FsJAn2icHwMM68bB67ccZfog4czywSioTgiHrDVSpump`](https://solscan.io/token/FsJAn2icHwMM68bB67ccZfog4czywSioTgiHrDVSpump) | $118.98 | $139.64 (1) | **+$20.66** | مغلق |
| SARP | [`Ph1ie3e4aMXCEVCjTcTzkyVhTRC7k9kpkq5MKSUpump`](https://solscan.io/token/Ph1ie3e4aMXCEVCjTcTzkyVhTRC7k9kpkq5MKSUpump) | $115.44 | $134.60 (1) | **+$19.16** | مغلق |
| DOTF — Digital Oil Trust Fund | [`RvkFYybWAGhgcsmvkQvFdUgqnVREbcSQhHFUW6Ypump`](https://solscan.io/token/RvkFYybWAGhgcsmvkQvFdUgqnVREbcSQhHFUW6Ypump) | $114.97 | $130.44 (1) | **+$15.47** | مغلق |
| UDR | [`PUXx1iSexu15p8FLG4FoFyRpyVtARFEf6CYbUzopump`](https://solscan.io/token/PUXx1iSexu15p8FLG4FoFyRpyVtARFEf6CYbUzopump) | $116.08 | $128.61 (1) | **+$12.53** | مغلق |
| DOTF | [`GkNBBV3TstnLb4Fxj1bmToza8ikx5UReSBw3LEWmpump`](https://solscan.io/token/GkNBBV3TstnLb4Fxj1bmToza8ikx5UReSBw3LEWmpump) | $114.43 | $126.48 (1) | **+$12.05** | مغلق |
| DOTF | [`SH6SfUf5pPbdq9h7RjnsoGjNvP3onox7P5tKJGEpump`](https://solscan.io/token/SH6SfUf5pPbdq9h7RjnsoGjNvP3onox7P5tKJGEpump) | $120.14 | $132.19 (1) | **+$12.04** | مغلق |
| ELPEPE | [`6bcjVdK2k9AS3cH4wEzc5x61myRLLAEkTSxwzVygpump`](https://solscan.io/token/6bcjVdK2k9AS3cH4wEzc5x61myRLLAEkTSxwzVygpump) | $117.86 | $126.62 (1) | **+$8.76** | مغلق |
| ATFS — American Trust Fund System | [`rtyCb78V7G3yEX3zqFRGn94Zy6nJYx5rKQrhDZ5pump`](https://solscan.io/token/rtyCb78V7G3yEX3zqFRGn94Zy6nJYx5rKQrhDZ5pump) | $114.86 | $116.75 (1) | **+$1.89** | مغلق |
| ATFS — American Trust Fund System | [`HE2kCYoqisUpFCjVa6QDat8Aqrn4DWkxaRbF7CPpump`](https://solscan.io/token/HE2kCYoqisUpFCjVa6QDat8Aqrn4DWkxaRbF7CPpump) | $119.21 | $116.33 (1) | **−$2.88** | مغلق — أسوأ نتيجة محققة في القائمة |

الأرقام في الجدول مقربة إلى السنت، لذا قد يختلف مجموع الصفوف المعروضة بسنت عن القيمة الدقيقة في الملخص. من المراكز الـ28 المغلقة في ميم كوينات، يظهر **27 ربحًا محققًا وواحدًا خاسرًا**. ويوجد مركز XRPN إضافي رُبح منه جزء محقق (+$136.21) لكنه ما زال مفتوحًا جزئيًا. هذه هي قراءة صفوف الأصول، وليست بديلًا عن إحصائية win rate الإجمالية التي لم تتطابق حقولها تمامًا.

### المراكز المفتوحة حاليًا بحسب سجل التوكنات

تعرض Solscan **6 أرصدة توكن** بالمحفظة، وتُظهر في الملخص 72.66M من أحد أرصدة XRPN. يسجل Vybe ستة مراكز ميم مفتوحة: XRPN جزئيًا، وخمسة مراكز لم تُسجل لها مبيعات بعد؛ تساوي العدد قرينة، لا تحقق مستقلًا من كل مِنت. العمود الأخير أدناه مجرد ضرب للكمية المتبقية في سعر أول زوج PumpSwap رجعه DexScreener وقت الفحص؛ **قيمة نظرية لا تضمن إمكان البيع بهذا السعر**.

| الرمز | المِنت | المتبقي حسب سجل الشراء/البيع | PnL غير المحقق في Vybe | قيمة سعرية تقريبية من DexScreener / سيولة الزوج |
|---|---|---:|---:|---:|
| XRPN — المِنت `iTbVz…` (جزئي) | [`iTbVzEXiw7eC9ftbv5eNVCQUrY64AQLHCfgW4DGpump`](https://solscan.io/token/iTbVzEXiw7eC9ftbv5eNVCQUrY64AQLHCfgW4DGpump) | 12.75M | غير متاح (`null`) | ~$78 / سيولة ~$4,998 |
| GOIF — `Bm7…` | [`Bm7Uxam9efqL8gu9CX5kZ3A7t5nj2v2titSC7nnpump`](https://solscan.io/token/Bm7Uxam9efqL8gu9CX5kZ3A7t5nj2v2titSC7nnpump) | 46.58M | +$43.82 | ~$161 / سيولة ~$3,325 |
| GOIF — Global Oil Institution Fund (`nZbP…`) | [`nZbPjCn4GJcLxrdHWRnMhPt875EyHSNTzhFmD6Dpump`](https://solscan.io/token/nZbPjCn4GJcLxrdHWRnMhPt875EyHSNTzhFmD6Dpump) | 48.66M | غير متاح (`null`) | ~$180 / سيولة ~$3,597 |
| AROS — American Reserved Oil Supply (`VEnb…`) | [`VEnbFNs7yCnN4aeNRXkgL25cBXg96nWVfHiQBN1pump`](https://solscan.io/token/VEnbFNs7yCnN4aeNRXkgL25cBXg96nWVfHiQBN1pump) | 51.42M | غير متاح (`null`) | ~$200 / سيولة ~$3,655 |
| XRPN — EVERNORTHXRP (`mHinvys…`) | [`mHinvysGkV4YPfj1PYxHGgyc4S7LCDwVki4r1Phpump`](https://solscan.io/token/mHinvysGkV4YPfj1PYxHGgyc4S7LCDwVki4r1Phpump) | 72.66M | +$77.69 | ~$249 / سيولة ~$3,266 |
| SARP — المِنت الأحدث (`W7Ljd…`) | [`W7LjdSHiGM6nE376hFUHpGMVGLuj1nokhy8v2r5pump`](https://solscan.io/token/W7LjdSHiGM6nE376hFUHpGMVGLuj1nokhy8v2r5pump) | 50.47M | +$91.03 | ~$199 / سيولة ~$3,638* |
| **المجموع التقريبي للقيمة السعرية** |  |  |  | **~$1,067** |

- الـ`null` ليست صفرًا؛ تعني أن Vybe لم يرجع تقييمًا غير محقق لهذا الصف. سعر DexScreener التقريبي يملأ فراغ السعر فقط ولا يحول PnL إلى ربح محقق.
- كفحص ورقي منفصل فقط: إذا وُزعت تكلفة XRPN الجزئي تناسبيًا على الكمية المتبقية، فتكون تكلفة الوحدات الست المفتوحة نحو `$661.07` مقابل سعر معلن إجمالي يقارب `$1,066.68`؛ فرق نظري **+$405.61**. هذا ليس رقم Vybe ولا أضيفه إلى الإجمالي الأساسي، لأن السعر من مجمعات ضحلة ولا يضمن تصفية الرصيد بهذا السعر.
- للمِنت SARP الأحدث `W7Ljd…` رجّع DexScreener زوج PumpSwap بسعر يقارب `$0.000003937`، كما رجّع زوج Pump.fun آخر بسعر مختلف جدًا (نحو `$0.00004806`) من دون سيولة معروضة في ذلك الصف. هذا اختلاف جوهري في التسعير/الأزواج؛ لذلك لا أستخدمه لحساب الربح الأساسي.
- تقديرات السيولة لقطة لحظية، والسيولة في هذه الأزواج بضعة آلاف من الدولارات فقط. بيع الرصيد كاملًا قد يسبب انزلاقًا سعريًا، لذا **قيمة ~$1,067 ليست بالضرورة حصيلة بيع قابلة للتحقق**.

### صف Wrapped SOL الذي يغيّر قراءة غير المحقق

يسجل Vybe صفًا مستقلًا لـ`wSOL` (العنوان القياسي `So111…11112`): مشتريات `$8,064.32` على 57 عملية، ومبيعات `$4,162.35` على 34 عملية، PnL محقق `+$9.80` وغير محقق **−$328.38**. هذا أصل المقابل/التسعير المستخدم في صفقات SOL، وليس واحدًا من ميم كوينات `pump`. لا تعرض Solscan رصيد wSOL منفصلًا ضمن ملخص الحساب؛ لذلك يجب مطابقة هذا الصف مع أرصدة SOL والتحويلات قبل تفسير خسارته على أنها مركز مستقل. هذا الصف هو السبب الأكبر في أن رقم Vybe غير المحقق الإجمالي سالب رغم ظهور مكاسب غير محققة في بعض التوكنات المفتوحة.

## 3. أسلوب التداول الذي تكشفه الصفقات

1. **دخول صغير ومتكرر:** أغلب مشتريات ميم كوين واحدة لكل مِنت، بقيمة تقارب **$114–$121** (نحو 1.0–1.1 SOL عند السعر وقتها). توجد استثناءات أكبر، مثل UDR بنحو $178 وUSDF بنحو $175 وXRPN بنحو $172.
2. **تدوير بين مِنتات كثيرة بدل الاحتفاظ بتوكن واحد:** السجل يعرض 34 مِنتًا بأسماء ميم/روايات مثل AORP وWOTF وGOIF وDOTF وSARP وAROS وNTDA وVSOF وWSOS. الأسماء والرموز تسميات للتوكنات وليست إثباتًا لارتباط رسمي بالنفط أو الحكومة أو أي مؤسسة.
3. **خروج مجزأ أحيانًا:** لكل ميم كوين غالبًا عملية شراء واحدة، ثم عملية بيع واحدة إلى ثلاث عمليات. أمثلة واضحة: AORP بيعان، وStrategic American Protocol ثلاث مبيعات، وWOTF ثلاث مبيعات. هذا يتوافق مع جني أرباح على دفعات.
4. **صفقات قصيرة نسبيًا في العينة:** SARP `GGMm…` بين أول شراء وآخر بيع قرابة ساعتين و45 دقيقة، وGOIF `qTy…` قرابة 8 ساعات، وAORP قرابة 38.6 ساعة. هذه أمثلة من مراكز رابحة وليست متوسط مدة محسوبًا لكل الصفقات.
5. **الانطباع العام:** النمط أقرب إلى تدوير/زخم قصير الأجل في ميم كوينات منخفضة القيمة السوقية منه إلى استثمار طويل الأجل قائم على أصول أساسية. تكرار أحجام دخول متقاربة قد يشبه قواعد تداول آلية أو تنفيذًا منضبطًا، لكنه **لا يثبت** أن المحفظة بوت.
6. **تركّز الربح:** أفضل ثلاثة مِنتات حققت مجتمعة نحو **$824.55**، وأفضل سبعة نحو **$1,571.52** (قرابة **55.4%** من الربح المحقق في الملخص). لذلك تعتمد نسبة معتبرة من النتيجة على عدد قليل من الصفقات الرابحة الكبيرة؛ لا يكفي عرض win rate وحده لوصف المخاطرة.

## 4. الرصيد والتحويلات: لا تخلطها مع PnL

- أحدث صفحة Solscan التي فُحصت تعرض **14.205940312 SOL** بقيمة **$1,549.01** عند سعر SOL المعروض **$109.04**، و**6 أرصدة توكن**. الرقم الدولاري الظاهر يساوي قيمة SOL المعروضة؛ صفحة الحساب لا تسعّر أرصدة التوكن الستة كلها في هذا الإجمالي. وتعرض الصفحة مالك الحساب `System Program` و`isOnCurve=True`، ما يتوافق مع حساب محفظة عادي لا برنامج/عقد ذكي؛ لكنه لا يكشف هوية صاحبه.
- في **30 سبتمبر 2026** استقبل العنوان تحويلين ظاهرين من الوسيط `CyrKL8GZ9J1qtfF3oJniSimqe5w6ajEJFwahqo37Xygb`: `0.001265524 SOL` و`0.028646294 SOL`، أي **0.029911818 SOL** في هذين التحويلين. يوسم Orb مصدر الوسيط بأنه Binance Hot Wallet 2؛ هذا تصنيف مستكشف، وليس إثبات هوية المالك.
- في **8 أكتوبر 2026 عند 14:08:42 UTC** خرج **8 SOL** إلى عنوان صنّفه Orb بأنه Binance Deposit (`Gmea…`). هذا تحويل إلى جهة موسومة من المستكشف، ولا يجوز احتسابه وحده كربح أو بيع.
- بعد التحويل ظهرت مشتريات/مبيعات أخرى، ومنها شراء أحدث مِنت SARP `W7Ljd…`: نحو **50.47 مليون توكن**؛ Vybe يسجل شراءً بنحو **$108.05**، وسجل المعاملة/Orb يعرض شراءً يقارب **0.9876 SOL**. رصيد SOL الحالي انخفض لاحقًا إلى 14.20594 SOL.
- لا تكفي التحويلات المذكورة وحدها لتحديد رأس المال الابتدائي أو صافي الإيداعات والسحوبات طوال عمر المحفظة. لذا لا أحسب منها ROI ولا أصف +$2,719.80 بأنه ربح المحفظة النقدي الكلي.

## 5. تقييم المخاطر النوعي للتوكنات

- صفحات Solscan المفحوصة لعينة من المراكز (AORP وSARP وWOTF وATFS) تصنفها **Meme** و**Pump.fun**؛ وتُظهر في هذه العينة ما بين 130 و315 حاملًا تقريبًا. هذا وصف للعينة وقت اللقطة، لا تدقيق أمني لكل المِنتات الـ34.
- أزواج DexScreener التي فُحصت تعرض سيولة تقريبية في حدود **$2.6K–$7.9K** لبعض الصفقات/الأرصدة الحالية؛ مثل AORP نحو $5.7K، WOTF نحو $7.9K، SARP `GGMm…` نحو $3.3K، وATFS الخاسر نحو $2.9K. هذه سيولة ضحلة نسبيًا مقارنة ببيع بمئات الدولارات، وتزيد مخاطر الانزلاق وصعوبة الخروج بالسعر النظري.
- الرمز الواحد قد يشير إلى مِنتات مختلفة: هناك عدة مِنتات باسم SARP وGOIF وDOTF وATFS وغيرها. يجب اعتماد عنوان المِنت في الجداول، لا الرمز أو الاسم فقط.
- لم أجد في البيانات المفحوصة ما يثبت أن عنوان المحفظة احتيالي، ولا ما يحدد هوية مالكه. نمط ميم كوينات حديثة وسيولة محدودة يعني **مخاطر سوق مرتفعة**، لكنه ليس وحده دليلًا على نصب أو غسل أموال.

## 6. منهجية وحدود الثقة

- PnL وعمليات الشراء/البيع لكل مِنت مأخوذة من واجهة Vybe التجريبية بطلب `resolution=Full`. وثائق Vybe تشرح أن حقولها تشمل PnL محققًا وغير محققًا، حجم التداول، وعدد الصفقات، وتقول إن بياناتها مشتقة من أسواق موثقة/مفلترة.
- الملخص يعرض تناقضًا داخليًا: `77` رابحة + `1` خاسرة لا تساوي `91` صفقة، رغم أن نسبة `84.615%` تساوي حسابيًا `77/91`. لذلك تُذكر نسبة الفوز كقيمة **يعلنها المزوّد** لا كمعدل تم التحقق منه مستقلًا.
- بعض أرصدة التوكن المفتوحة بلا PnL غير محقق (`null`). تسعيرات DexScreener في التقرير مجرد تقدير لحظي من زوج تداول محدد، وقد لا تعكس سعر تنفيذ الكمية كاملة. ويوجد اختلاف واضح بين زوجين للـSARP الأحدث.
- `PnL التداول`، و`قيمة المحفظة الحالية`، و`صافي النقد بعد الإيداع والسحب والرسوم` ثلاثة مقاييس مختلفة. تقرير نهائي محاسبي يحتاج سجلًا كاملًا للمعاملات، وأسعار تنفيذ كل مبادلة، والرسوم، والتحويلات الخارجية، وتحققًا من أرصدة التوكنات وأسعار بيعها الفعلية.

## 7. هل النسخ بـ$10 أو$50 ممكن؟

### محاكاة رجعية، لا توقع للمستقبل

أعدتُ حساب 28 مِنت ميم **مغلقة بالكامل** فقط، واستبعدتُ مركز XRPN الجزئي والمراكز المفتوحة وصف wSOL. اشترت المحفظة هذه المراكز بأحجام مجمعة تقارب `$3,411.24`، وسجلت لها PnL محققًا يقارب `$2,689.63`.

| افتراض نسخ كل مركز بنفس نقطة دخول وخروج المحفظة | إجمالي المبلغ الاسمي على 28 مركزًا | PnL رجعي افتراضي | المتوسط لكل مركز |
|---|---:|---:|---:|
| `$10` لكل مِنت | $280 | **+$223.13** | +$7.97 |
| `$50` لكل مِنت | $1,400 | **+$1,115.67** | +$39.85 |

في هذا السجل المغلق فقط، 27 من 28 مركزًا كانت موجبة وواحد سالب. مثال: AORP حقق نحو +240% من مبلغ دخوله، ما يعادل نظريًا +$24 على دخول $10 أو +$120 على $50؛ أما ATFS الخاسر فكان نحو −2.4%، أي −$0.24 أو −$1.21. **هذه أرقام hindsight مشروطة بأن تشتري وتبيع بنفس سعره تقريبًا**؛ لا تشمل تأخر النسخ، اختلاف السعر، أثر الصفقة على المجمع، تعثر المعاملة، ولا تثبت أن الصفقة التالية ستربح. الميم كوين قد يهبط أكثر أو يفقد السيولة، وعندها يمكن أن تخسر كامل $10 أو $50.

### تقدير أثر $10 و$50 على السيولة الحالية

استخدمت بيانات DexScreener من 8 أكتوبر وسعر SOL المعروض `$109.04`. الجدول يقدّر **انزلاق متوسط التنفيذ مقابل السعر الحالي** في نموذج مجمع ثابت مبسط، باستخدام احتياطي SOL في جهة واحدة من المجمع (`quote reserve`) لا رقم السيولة الإجمالي ذي الجهتين. التقريب هو `حجم الصفقة ÷ (احتياطي جهة SOL + حجم الصفقة)` قبل رسوم المجمع/المسار وأي حركة سعر أخرى؛ ليس عرض تنفيذ حيًا، وقد تكون حركة السعر بعد الصفقة أكبر من النسبة المعروضة.

| مجمع التوكن | احتياطي SOL المقابل بالدولار | أثر تقريبي لصفقة $10 | أثر تقريبي لصفقة $50 |
|---|---:|---:|---:|
| XRPN `iTbVz…` المفتوح جزئيًا | ~$1,547 | ~0.64% | ~3.13% |
| GOIF `Bm7…` المفتوح | ~$666 | ~1.48% | ~6.99% |
| GOIF `nZbP…` المفتوح | ~$792 | ~1.25% | ~5.94% |
| AROS `VEnb…` المفتوح | ~$764 | ~1.29% | ~6.14% |
| XRPN `mHinvys…` المفتوح | ~$603 | ~1.63% | ~7.66% |
| SARP `W7Ljd…` المفتوح — زوج PumpSwap | ~$875 | ~1.13% | ~5.40% |
| ATFS `HE2k…` — صفقة خاسرة سابقة | ~$497 | ~1.97% | ~9.13% |
| UDR `5iUR…` — صفقة رابحة سابقة | ~$294 | ~3.29% | ~14.55% |

**قراءة عملية:** في الأزواج المفتوحة الستة التي فُحصت، $10 أصغر بكثير من الاحتياطي المقدر، وقد يكون أثره أقل من نحو 1–2% في اللقطة الحالية؛ أما $50 فقد يسبب نحو 3–8% أثرًا نظريًا فيها. وفي الأزواج الأضعف مثل UDR/ATFS يصل التقدير إلى نحو 9–15% لصفقة $50. إذا هبط التوكن أو خرجت السيولة، تصبح الأرقام أسوأ. كما أن حجم تداول 24 ساعة كان شبه معدوم لبعض الأزواج (مثل SARP `GGMm…` نحو `$1.74`، وDOTF نحو `$17.75`، وUDR نحو `$5.97`)؛ وجود احتياطي في المجمع لا يعني أن السعر المعروض حديث أو أن البيع سيُنفذ بلا انزلاق.

### ماذا لو اشتريت بعد دخوله وارتفاع السعر؟

نعم، شراءه يرفع السعر اللحظي في مجمع AMM عادةً، لكن مقدار الارتفاع تحدده احتياطيات المجمع لا القيمة السوقية وحدها. كتمرين تقريبي، شراء نموذجي منه بنحو `$117` مقابل احتياطي quote-side حالي `$603–$1,547` يعطي ارتفاعًا نظريًا في السعر اللحظي بعد المبادلة بنحو **16%–43%** في نموذج constant-product مبسط. وفي احتياطيات أضعف مثل UDR (~$294) وATFS (~$497)، يصل السيناريو النظري إلى نحو **96%** و**53%**. هذه ليست قياسات تاريخية عند لحظة دخوله؛ استخدمت احتياطيات اللقطة الحالية بدل الاحتياطي الفعلي وقت كل معاملة. ولو افترضنا أن هذه الاحتياطيات كانت قبل دخوله ثم أضفنا شراءه، فشراء ناسخ بـ$50 بعده قد يضيف انزلاق تنفيذ متوسطًا آخر بنحو **2.9%–6.5%** في نطاق المجمعات المفتوحة، ونحو **7.5%–10.8%** في UDR/ATFS الأضعف، قبل الرسوم؛ هذا فوق أنك بدأت بسعر أعلى.

لترجمة «الدخول بعد ارتفاع» إلى أرقام: متوسط العائد البسيط للمراكز الـ28 المغلقة في العينة نحو **+79.69%** إذا دخلتَ عند سعره نفسه. إذا دخلت بعد ارتفاع السعر عن دخوله، وافترضنا فقط لأجل السيناريو أن الخروج اللاحق ظل عند سعر البيع التاريخي نفسه، تصبح النتيجة التقريبية:

| سعر دخولك أعلى من سعره | العائد النظري بعد إعادة الحساب | ربح/خسارة على $10 | ربح/خسارة على $50 |
|---:|---:|---:|---:|
| 0% (سعر مماثل) | +79.69% | +$7.97 | +$39.85 |
| +16% | +54.91% | +$5.49 | +$27.45 |
| +43% | +25.66% | +$2.57 | +$12.83 |
| +53% | +17.44% | +$1.74 | +$8.72 |
| +80% | −0.17% تقريبًا | −$0.02 | −$0.09 |
| +100% (السعر تضاعف قبل دخولك) | −10.15% | −$1.02 | −$5.08 |

هذه **ليست أرباحًا متوقعة**: هي متوسط مراكز ناجحة/خاسرة أُغلقت تاريخيًا، وتفترض أن صفقتك ستخرج عند نفس سعر خروجه؛ وهذا افتراض متفائل إذا انتظرتَ حتى ظهور بيعه على السلسلة. لا تشمل تأخر النسخ أو الانزلاق والرسوم، وقد تحصل على سعر أسوأ بعد أن يكون بيعه قد حرّك المجمع. وتُظهر ببساطة أن الارتفاع الذي يساعد صاحب الصفقة قد يستهلك معظم أفضلية الناسخ إذا انتظر طويلًا؛ عند دخول متأخر بنحو 80% تكون الأفضلية التاريخية المتوسطة قد اختفت تقريبًا قبل التكاليف.

### منطقة الدخول والقاع الظاهر في عينة تاريخية

بحساب **حجم الشراء بالدولار ÷ عدد التوكنات التي استلمها** عبر 34 مِنت ميم في بيانات Vybe، تراوحت أسعار الدخول الضمنية بين **$0.0000021409 و$0.0000025605**؛ الوسيط نحو **$0.0000023313**. وبافتراض معروض قريب من مليار توكن — كما في صفحات Solscan التي تحققت منها — فهذا يعادل تقريبًا منطقة FDV من **$2.14K إلى $2.56K** (وسيط ~$2.33K). هذه **منطقة دخول تاريخية متكررة**، وليست مستوى دعم مضمونًا أو قاعًا مستقبليًا.

في ستة أمثلة، قارنت سعر دخوله بأدنى سعر في شمعة الدقيقة التي وقعت عند/حول عملية الشراء:

| المِنت | متوسط سعر دخول المحفظة | أدنى سعر في شمعة الدقيقة حول الدخول | الفرق التقريبي |
|---|---:|---:|---:|
| [AORP `G7UJP…`](https://solscan.io/token/G7UJPfu4Xh4Lv5H1ETmwn1Q9uMScw3GSFgBqzKppump) | $0.000002349 | $0.000002222 | +5.7% |
| [SARP — Strategic American Protocol `6Wbi…`](https://solscan.io/token/6WbiJtjXoNpLH6GhSvDX4HqRUN3ShQgxsk56Synpump) | $0.000002307 | $0.000002307 | نحو 0% |
| [WOTF `6DWH…`](https://solscan.io/token/6DWHBW3R5NE2LUShJRbvDyi9GZ8Hz4EFFRgcfP3apump) | $0.000002553 | $0.000002172 | +17.5% |
| [ATFS `HE2k…`](https://solscan.io/token/HE2kCYoqisUpFCjVa6QDat8Aqrn4DWkxaRbF7CPpump) | $0.000002472 | $0.000002225 | +11.1% |
| [GOIF `qTy…`](https://solscan.io/token/qTyZGgDKVH1fZNhBAnGcUgtyVbVrWZ3uNeuCgJ4pump) | $0.000002560 | $0.000002235 | +14.6% |
| [DOTF `tY5…`](https://solscan.io/token/tY5KSvxu3iBMwVZzVpYqrVbxAVbAXMKTJ7SxW6Wpump) | $0.000002332 | $0.000002329 | +0.1% |

هذا يوحي أن بعض دخولاته كانت قريبة من قيعان **مسجلة على الرسم**، لكن أدنى سعر داخل شمعة الدقيقة قد يكون حدث قبل صفقة المحفظة أو بعدها، ولا يثبت أنه كان معروفًا وقت الدخول. كما أن مصدر الشموع أظهر قفزات سعرية شاذة، لذلك لا أتعامل مع تلك القيعان كدعم قابل للاعتماد. أحدث SARP `W7Ljd…` مثال إضافي على عدم تطابق سعر الصفقة مع إحدى الشموع، ما يمنع اعتماد السعر اللحظي كـ«قاع دقيق».

### هل يشتري فعلًا «بعد الانهيار»؟ وهل يمكن نسخه في اللحظة نفسها؟

- أمثلة معاملات فعلية تؤكد أن دخوله متكرر قرب **0.9876 SOL** عبر Bloom Router إلى Pump.fun AMM: اشترى AORP بنحو 49.99M توكن، وSARP `6Wbi…` بنحو 51.27M، وATFS الخاسر بنحو 48.23M. هذا يثبت حجم دخوله وطريق التنفيذ في هذه الأمثلة، لا سبب اختياره للتوقيت.
- شموع GeckoTerminal حول بعض هذه المشتريات تُظهر قفزات/انهيارات سعرية لحظية هائلة وغير متسقة مع سعر المبادلة المحسوب من المعاملة؛ قد تكون انهيارًا حقيقيًا، أو خللًا في سلسلة السعر/انتقالًا بين مجمعات. لذلك **لا أستطيع إثبات أن لديه استراتيجية موثوقة لشراء القاع بعد الانهيار**، ولا أوصي باعتبار الشمعة وحدها إشارة دخول.
- لا يمكن تنفيذ نسخة مطابقة تمامًا: المعاملة تصبح مرئية بعد إدراجها/تأكيدها، وقد يتحرك السعر قبل أن تنفذ أنت. كذلك يبيع المحفظة بعض المراكز على دفعتين أو ثلاث؛ إذا لم تراقب كل بيع قد تبقى داخل التوكن بعد خروجه.

**الجواب المباشر:** من ناحية حجم السيولة في اللقطة الحالية، دخول **$10 لكل تجربة** أيسر من $50، لكن ليس مضمون الخروج ولا يحمي من انهيار كامل. **$50 ليس مبلغًا ضخمًا بالنسبة لبعض المجمعات، لكنه كبير بما يكفي لإحداث انزلاق ملحوظ في الأزواج الأضعف**. قبل أي مبادلة، افحص عرض البيع الفعلي للكمية التي ستملكها وحدّ الانزلاق؛ إذا كان العرض سيئًا أو لا يوجد مسار بيع واضح فتجاوز الصفقة. لا تنسخ المحفظة آليًا أو تمنح موقعًا/بوتًا مفتاحك الخاص.

## 8. هل نستطيع معرفة نوع أوامر الخروج؟ وكيف تبني نسخة أسرع؟

### ما تثبته البيانات عن هذه المحفظة — وما لا تثبته

- معاملة AORP المفحوصة على Orb تظهر مبادلة نحو `0.987654 SOL` مقابل `49.99M` توكن عبر **Bloom Router** إلى **Pump.fun AMM / PumpSwap**. هذا يثبت استعمال مسار Bloom في تلك المعاملة؛ لا يثبت وحده أن صاحب الحساب يستخدم واجهة Bloom نفسها أو خاصية Copy Trading تحديدًا، إذ يمكن أن يرسل تداولًا يدويًا أو عبر API.
- في تجميع Vybe السابق: من 28 مِنت ميم مغلقًا، صُنّف 27 موجبًا ومِنت واحد خاسرًا (`−$2.88` على شراء `$119.21`، نحو `−2.4%`). وفي عدد من المراكز المغلقة ظهرت عمليتا بيع أو ثلاث للمِنت؛ وهذا يثبت الخروج على دفعات في تلك الحالات، لا سبب البيع. وهناك أيضًا خمسة مِنتات لم تسجل لها مبيعات، ومركز XRPN مفتوح جزئيًا.
- هذا **يتوافق** مع جني أرباح على دفعات، لكنه لا يميّز بين Take Profit ثابت، أو Trailing Stop، أو Stop Loss، أو Follow Sells، أو بيع يدوي. ملخص PnL لا يعرض إعدادات صاحب المحفظة ولا سبب إطلاق كل بيع؛ والمراكز المفتوحة تجعل الحكم من العينة المغلقة وحدها منحازًا. لذلك لا أستطيع تأكيد أنه يستخدم Stop Loss أو Trailing أو حتى أن مبيعاته الآلية هي سبب الأرباح.

Bloom نفسها توثّق في Copy Trading خيارات `Buy Exact / Buy % / Buy Fixed` و`Follow Sells`، كما توثّق Auto Orders تشمل Take Profit وStop Loss وTrailing ووقت خروج وخروجًا عند بيع المطوّر. وجود هذه الإمكانات مع مرور إحدى صفقاته عبر Bloom يجعل استخدامها **ممكنًا ومعقولًا، لا مثبتًا**. صفحة الرسوم الرسمية تذكر 1% على كل شراء وبيع، و0.9% عند التسجيل عبر إحالة؛ تحقّق من السعر الفعلي/الكاشباك في حسابك قبل حساب نقطة التعادل.

### أقرب نسخة جاهزة الآن: Bloom Copy Trading

إذا أردت تقليد حركة المحفظة بأقل وقت تطوير، استخدم مهمة Copy Trading الرسمية وأدخل عنوانها. كإعداد أولي للنسخ، لا كتوصية استثمارية:

1. فعّل `Follow Sells` كي تبيع النسبة التي يبيعها الهدف، و`Buy Tokens Once` و`Sell Only Copied Buys` لتفادي تكرار الدخول أو بيع رصيد لم تشتره هذه المهمة.
2. أظهر سجلها دخولًا نموذجيًا قريبًا من `0.9876 SOL` (نحو `$117` في اللقطة). `Buy Exact` سيحاول محاكاة ذلك المبلغ؛ إن كان أكبر من ميزانيتك استخدم `Buy Fixed` أو نسبة أقل من 100%، وضع حدًا أقصى لكل صفقة وعدد المراكز.
3. اضبط `Max Slot Diff` منخفضًا حتى تتجاوز الإشارة إذا تأخر النسخ كثيرًا؛ هذا يقلل النسخ المتأخر لكنه قد يجعل البوت يفوّت صفقات. استخدم فلاتر الحد الأعلى/الأدنى لشراء الهدف والقيمة السوقية وعمر التوكن.
4. لنسخة أقرب إلى سلوكه، ابدأ بـ`Follow Sells` من دون TP/SL/Trailing مستقل. إضافة هذه المخارج قد تبيعك قبل الهدف أو بعده، وبالتالي لن تكون نسخة مطابقة. إذا أضفت حد خسارة كشبكة أمان، اعتبره قرارًا يغيّر الاستراتيجية لا معلومة مستنتجة عن الهدف.

Bloom API الرسمي يتيح إرسال Swap وإرفاق أوامر خروج، لكنه في التوثيق العام يشرح واجهات Swap/Deploy/Wallets ولا يعرض واجهة عامة لإنشاء مهمة Copy ومراقبة عنوان هدف؛ لذلك حتى مع API ستحتاج إلى بناء مستمع معاملاتك. المفتاح Bearer مرتبط بحساب Bloom، ومحافظ التنفيذ يجب أن تكون ضمنه. انتبه إلى `auto_orders`: إغفالها أو إرسال `null` يطبق استراتيجية Spot المحفوظة، و`[]` يعطّل أوامر الخروج، والمصفوفة المخصصة تستخدم أوامرك وحدها؛ حدّد السلوك صراحةً حتى لا ترث إعدادًا لم تقصده. كما أن الوثائق تنشر حدود طلبات (60/دقيقة، 1,200/ساعة، 10,000/أسبوع)، لذا راقب حدّ الاستخدام وأعد المحاولة بتدرّج. ويمكن استعماله كطبقة تنفيذ، لكن المرور عبر طلب API خارجي لا يضمن أن يكون أسرع من Copy Trading المدمج في Bloom.

### بنية بوت مخصص — ابدأ بقياس السرعة قبل مطاردة الميلي ثانية

1. **استقبال الإشارة:** Yellowstone gRPC / LaserStream مع فلتر عنوان الهدف، وبـ`processed` لأسرع تنبيه؛ سجّل التوقيع والـslot، ثم صالح النتيجة عند `confirmed` وتعامل مع إعادة الاتصال والتكرار. `processed` أسرع لكنه ليس نهائيًا، فلا تُرسل شراءً ثانيًا لمجرد غموض التأكيد.
2. **فكّ المعاملة:** لا تراقب شموع الدقيقة ولا تبحث فقط عن تعليمة Pump.fun مباشرة. صفقة العينة تمر عبر Bloom Router وبداخلها PumpSwap؛ فكّ التعليمات الخارجية والداخلية، وتأكد من نجاح المعاملة (`meta.err`)، واستعمل فروق أرصدة SOL والتوكن قبل/بعدها لتحديد المِنت والاتجاه والكمية الفعلية. وقّع **معاملة جديدة لمحفظتك**؛ لا يمكن إعادة بث توقيع الهدف ليصبح صفقتك.
3. **بوابة المخاطر قبل التنفيذ:** حد أقصى SOL لكل صفقة ولكل توكن، سقف انزلاق/أثر سعري، حد أدنى للسيولة ومسار بيع، عدد أقصى للمراكز، قائمة منع، منع التكرار، وقاطع يومي يوقف التداول. افحص ناتج البيع المتوقع لكمية محفظتك؛ Stop Loss لا يضمن سعرًا أو حتى إمكان البيع إذا اختفت السيولة أو تعذّر المسار.
4. **التنفيذ:** للنسخة الأولى استخدم Bloom API أو Jupiter Swap لبناء المسار وإرسال الصفقة؛ قد يمنح بناء تعليمات Pump.fun/PumpSwap مباشرة وتوقيعها محليًا تحكمًا أكبر وربما يقلل بعض الرحلات الشبكية، لكن لا تفترض أنه أسرع قبل القياس. اجعل متابعة البيع بنسبة من **رصيدك أنت قبل الصفقة**، لا كمية توكنات الهدف حرفيًا، لأن حجم التنفيذ والانزلاق والرسوم يختلفان.
5. **القياس:** خزّن أوقات اكتشاف الإشارة، انتهاء فكّها، إرسال معاملتك، الـslot، سعر تنفيذك وسعر الهدف والرسوم. قارن `slot gap` وسعر التنفيذ الفعلي قبل تغيير مزوّد البيانات أو دفع تكاليف بنية أسرع. سرعة اللغة وحدها لن تعوّض تأخر مزوّد البيانات أو بناء الصفقة أو إرسالها.

**مهم بتاريخ هذا التقرير (8 أكتوبر 2026):** توثيق Jito أعلن موعد إيقاف ShredStream في **5 سبتمبر 2026** وأوصى بالانتقال إلى DoubleZero Edge؛ الموعد المعلن قد مضى، فلا تبدأ مشروعًا جديدًا من شروحات قديمة تفترض أن Jito ShredStream متاح. DoubleZero Edge مسار بيانات shreds وليس وحده خدمة توقيع/إرسال Swap. Yellowstone/LaserStream أسهل كبداية؛ قِس زمن مسار أوروبي من بيئة تشغيلك قبل شراء بنية مخصّصة. وإيقاف ShredStream لا يعني تلقائيًا إيقاف واجهة Jito لإرسال المعاملات؛ هما مساران مختلفان.

حتى مع أسرع بث، لن تحصل تلقائيًا على سعر الهدف: أنت ترى معاملته بعد أن أُرسلت/عولجت وتبني صفقة أخرى بعدها. وهذا مهم جدًا هنا؛ تقدير التقرير السابق لشراء قريب من `$117` مقابل احتياطيات المجمعات الحالية أعطى أثرًا نظريًا يقارب `16%–43%` في بعض المجمعات المفتوحة و`53%–96%` في أمثلة أضعف. ليست هذه قياسات تاريخية أو سعر تنفيذ مضمونًا، لكنها توضح لماذا قد يرفع النسخ سعر دخولك ويحوّل «السرعة» إلى مطاردة أعلى سعر.

**الأمان:** ابدأ بمراقبة/محاكاة بلا توقيع، ثم بمحفظة تشغيل منفصلة ومحدودة التمويل إذا قررت التجربة. لا تضع مفتاحًا خاصًا أو API key في Git أو واجهة المتصفح؛ تعامل مع Bloom API key كبيانات تداول حساسة، واحفظه في مدير أسرار. لا يمكن استنتاج إعدادات الهدف الخاصة أو ضمان نسخ ربحه.

## المصادر

1. [Solscan — الحساب والرصيد الحالي](https://solscan.io/account/2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb)
2. [Vybe — PnL المحفظة، كامل التاريخ](https://solana-trader-pnl-api.vybenetwork.com/api/wallets/2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb/pnl?resolution=Full&limit=1000)
3. [توثيق Vybe — Wallet PnL API ومنهج الحقول](https://docs.vybenetwork.com/docs/fetch-wallet-pnls)
4. [Orb — سجل المحفظة](https://orbmarkets.io/address/2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb/history)
5. [Orb — معاملة تحويل 8 SOL إلى العنوان الموسوم Binance Deposit](https://orbmarkets.io/tx/4614PqCFjJ8StathzjzyPvsMLW8Eocc5Nmvsz11zcBwYJxxid3VbZZTZyEKc1HrYVKYD3ns1UyibZoysxDsojbY4)
6. [Orb — تحويل شراء SARP الأحدث](https://orbmarkets.io/tx/3t1fuBpf76s3RF8g1Fdm8wES34WQWvqoMKiXbvBJZqySYmBcW7g4ZJGZq82SSBwVSnzxJ6EK2soj5cJbjLLu97Tn)
7. [Solscan — صفحة توكن AORP](https://solscan.io/token/G7UJPfu4Xh4Lv5H1ETmwn1Q9uMScw3GSFgBqzKppump)؛ [DexScreener API — AORP](https://api.dexscreener.com/latest/dex/tokens/G7UJPfu4Xh4Lv5H1ETmwn1Q9uMScw3GSFgBqzKppump)
8. [Solscan — صفحة SARP `GGMm…`](https://solscan.io/token/GGMm5EmstNMQh4tvR127joSzBDa5UeE4FkVYZZmtpump)؛ [DexScreener API — SARP `GGMm…`](https://api.dexscreener.com/latest/dex/tokens/GGMm5EmstNMQh4tvR127joSzBDa5UeE4FkVYZZmtpump)
9. [Solscan — صفحة WOTF](https://solscan.io/token/6DWHBW3R5NE2LUShJRbvDyi9GZ8Hz4EFFRgcfP3apump)؛ [DexScreener API — WOTF](https://api.dexscreener.com/latest/dex/tokens/6DWHBW3R5NE2LUShJRbvDyi9GZ8Hz4EFFRgcfP3apump)
10. [Solscan — صفحة مِنت ATFS الخاسر](https://solscan.io/token/HE2kCYoqisUpFCjVa6QDat8Aqrn4DWkxaRbF7CPpump)؛ [DexScreener API — ATFS](https://api.dexscreener.com/latest/dex/tokens/HE2kCYoqisUpFCjVa6QDat8Aqrn4DWkxaRbF7CPpump)
11. [DexScreener API — أزواج المراكز المفتوحة XRPN `iTbVz…`](https://api.dexscreener.com/latest/dex/tokens/iTbVzEXiw7eC9ftbv5eNVCQUrY64AQLHCfgW4DGpump)، [GOIF `Bm7…`](https://api.dexscreener.com/latest/dex/tokens/Bm7Uxam9efqL8gu9CX5kZ3A7t5nj2v2titSC7nnpump)، [GOIF `nZbP…`](https://api.dexscreener.com/latest/dex/tokens/nZbPjCn4GJcLxrdHWRnMhPt875EyHSNTzhFmD6Dpump)، [AROS `VEnb…`](https://api.dexscreener.com/latest/dex/tokens/VEnbFNs7yCnN4aeNRXkgL25cBXg96nWVfHiQBN1pump)، [XRPN `mHinvys…`](https://api.dexscreener.com/latest/dex/tokens/mHinvysGkV4YPfj1PYxHGgyc4S7LCDwVki4r1Phpump)، [SARP `W7Ljd…`](https://api.dexscreener.com/latest/dex/tokens/W7LjdSHiGM6nE376hFUHpGMVGLuj1nokhy8v2r5pump)
12. [Solana Explorer — الحساب](https://explorer.solana.com/address/2dV2AzutJpBMDGzW2VS2LEFnVoqHxEGKq5J1UWnKC2Vb?cluster=mainnet-beta)
13. [DexScreener API — UDR `5iUR…`](https://api.dexscreener.com/latest/dex/tokens/5iURQEWL4NcbqhXRnhssfCzhAnghWbEGUoTWiWhpump) و[DOTF `tY5…`](https://api.dexscreener.com/latest/dex/tokens/tY5KSvxu3iBMwVZzVpYqrVbxAVbAXMKTJ7SxW6Wpump) — أسعار/احتياطيات أزواج وقت الفحص.
14. معاملات الدخول التي استُخدمت لعينة النسخ: [شراء AORP](https://orbmarkets.io/tx/41wz7Poe7QBxHd8CQbEVbBGqpeXFVodUGH7qJizA9inqw5JGL8awDVcqfgby1FuGt9zyfgG3HDpVgkGpp9sCuNVt)، [شراء SARP `6Wbi…`](https://orbmarkets.io/tx/67GTFqS6X1SgKdEnupmeP494sgxHMKvDp9v5FYRrS9ZyYsC87prATw4zpWfmDG6q9FsYuuNdV3RjPV5i18AxDGrb)، [شراء ATFS الخاسر](https://orbmarkets.io/tx/4NAJQsr6eJX9frMtKFHBUaedg53nKYC58yMpkKnZNzeYx5efPcJjtpmGQn41xVm1aaARhscmros4dmZrPjQR5A8f).
15. [GeckoTerminal — شموع الدقيقة لـAORP حول الدخول](https://api.geckoterminal.com/api/v2/networks/solana/pools/8sKzmW8r2hQH8wuBCcAB8WHWvRHmJk8hqprme1novPxw/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1790901999&currency=usd&token=base)، [SARP `6Wbi…`](https://api.geckoterminal.com/api/v2/networks/solana/pools/9Z1cRcyxQCLMBLaSACAimrBv5ZA2nhBHESbjxviLTbgg/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1791057341&currency=usd&token=base)، [ATFS](https://api.geckoterminal.com/api/v2/networks/solana/pools/EXQ4omc4xKw6wb2X9mD1NCxrMixxviBqCFo2mUjbhkGT/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1791244489&currency=usd&token=base)، [WOTF](https://api.geckoterminal.com/api/v2/networks/solana/pools/FhXq6akCDx47spG5XGqd2CFJGGgGRQpdNBpjiUpSNVQ3/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1791136721&currency=usd&token=base)، [GOIF `qTy…`](https://api.geckoterminal.com/api/v2/networks/solana/pools/ANcPJyoPyos5hoGioj6UvkzA4RpU5FRNTb626xSMX6dB/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1790946676&currency=usd&token=base)، و[DOTF `tY5…`](https://api.geckoterminal.com/api/v2/networks/solana/pools/FKajTTeLMZ59oxNhrNf9YTbG8GkAgwe2ELDEbQ2iM7mp/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1791209004&currency=usd&token=base). هذه لقطات تاريخية أتعامل معها بتحفظ بسبب قفزات سعر غير متسقة.
16. [GeckoTerminal — شموع الدقيقة لأحدث SARP `W7Ljd…`](https://api.geckoterminal.com/api/v2/networks/solana/pools/AdvA19rgGhN1ZUNHP7nQPxZ29x1P263g2FHnQdyPHVYi/ohlcv/minute?aggregate=1&limit=30&before_timestamp=1791473508&currency=usd&token=base) — تُظهر تعارضًا مع سعر الدخول المحسوب من بيانات المبادلة.
17. [Orb — معاملة شراء AORP `41wz…`](https://orbmarkets.io/tx/41wz7Poe7QBxHd8CQbEVbBGqpeXFVodUGH7qJizA9inqw5JGL8awDVcqfgby1FuGt9zyfgG3HDpVgkGpp9sCuNVt) — تعرض مسار Bloom Router إلى Pump.fun AMM وكمية SOL/التوكن في المثال.
18. [Bloom — Copy Trading على Solana](https://docs.bloombot.app/solana/solana-bot/copy)، [إعدادات مهمة النسخ في Manager](https://docs.bloombot.app/manager/pages/tasks/solana/copy-trade)، و[Copy Presets](https://docs.bloombot.app/solana/solana-bot/settings/presets/copy-presets) — Buy Exact/Fixed، Follow Sells، Buy Tokens Once، وحدّ فرق الـslots.
19. [Bloom — الأسئلة الشائعة](https://docs.bloombot.app/solana/miscellaneous/faqs)، [صفحة الرسوم](https://docs.bloombot.app/grow-with-bloom/fees-structure)، و[الموقع الرسمي](https://www.bloombot.app/) — Auto Orders وTP/SL/Trailing ورسوم/خصومات المنصة المعلنة.
20. [Bloom API — المقدمة](https://dev.bloombot.app/introduction) و[مرجع Swap](https://dev.bloombot.app/api-reference/swap) و[Auto-orders](https://dev.bloombot.app/concepts/auto-orders) — واجهات التنفيذ وخيارات TP/SL/Trailing وحدود الطلبات.
21. [Helius — Yellowstone gRPC](https://www.helius.dev/docs/grpc) و[Transaction Monitoring](https://www.helius.dev/docs/grpc/transaction-monitoring) — بث المعاملات والالتزام `processed/confirmed`.
22. [Jito — إعلان Sunset لـShredStream](https://docs.jito.wtf/lowlatencytxnfeed/) و[إرسال المعاملات عبر Block Engine](https://docs.jito.wtf/lowlatencytxnsend/) — واجهتا استقبال البيانات وإرسال المعاملات منفصلتان.
23. [Jupiter — Trigger API V2](https://developers.jup.ag/docs/trigger) — أوامر OCO لوقف الخسارة/جني الربح وTrailing Stop؛ و[Solana — توقيع الإنتاج وإدارة المفاتيح](https://solana.com/docs/core/transactions/signing-in-production) — إرشادات عدم تضمين المفاتيح في الكود أو Git.
24. [DoubleZero Edge](https://doublezero.xyz/dz-edge) — خدمة توصيل بيانات Solana الخام (shreds)، منفصلة عن إنشاء المعاملات وتوقيعها وإرسالها.
---

**تنبيه:** هذه دراسة بيانات عامة على السلسلة وليست نصيحة استثمارية أو تقريرًا جنائيًا. الأسعار والسيولة وأسماء العناوين قد تتغير أو تكون غير دقيقة؛ تحقق من عنوان المِنت والمعاملة مباشرة قبل أي قرار.
