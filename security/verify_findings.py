#!/usr/bin/env python3
"""
verify_findings.py — تحقّق موجّه من نتائج الجولة الأولى + قياس الأثر.

كل الخطوات **قراءة فقط** أو آمنة بطبيعتها:
  • لا يحذف/يعدّل أي سجل حقيقي
  • كتابة على معرّف غير موجود (999999999) لإثبات غياب الحماية دون إيذاء بيانات
  • محاولات دخول باسم مستخدم عشوائي (لا حساب حقيقي)

الاستخدام:
    python security/verify_findings.py http://target --out security/findings
"""
from __future__ import annotations

import argparse
import json
import os
import random
import string
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("مطلوب requests")

UA = "SecVerify/1.0 (authorized self-scan, read-only)"
FAKE_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6InRlc3QiLCJpYXQiOjE3MDAwMDAwMDB9.invalid"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", default="security/findings")
    ap.add_argument("--alerts", type=int, default=25, help="كم تنبيه نقرأ لقياس التعرّض")
    args = ap.parse_args()

    base = args.target if args.target.endswith("/") else args.target + "/"
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    out: dict = {"target": args.target, "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "checks": []}

    def chk(cid, name, sev, ok, detail, evidence="", impact=""):
        out["checks"].append({"id": cid, "name": name, "severity": sev, "vulnerable": ok,
                              "detail": detail, "evidence": evidence[:1500], "impact": impact})
        print(f"  {'🔴' if ok else '🟢'} {cid} {name} — {detail[:120]}")

    print(f"🎯 تحقّق موجّه: {base}\n")

    # ── 1) CORS على نقاط البيانات ──────────────────────────────────
    print("▶ CORS")
    for path in ("/api/alerts/1", "/api/alerts/stats/summary", "/api/alerts/mitre/navigator-layer"):
        r = s.get(urljoin(base, path.lstrip("/")), headers={"Origin": "https://evil.example"}, timeout=12)
        acao = r.headers.get("Access-Control-Allow-Origin", "")
        acac = r.headers.get("Access-Control-Allow-Credentials", "")
        out.setdefault("cors", {})[path] = {"acao": acao, "acac": acac, "status": r.status_code}
        if acao and ("evil.example" in acao or acao == "*"):
            chk("CORS-001", f"CORS مفتوح على {path}", "critical", True,
                f"ACAO={acao!r} ACAC={acac!r}",
                f"{acao}\n{acac}",
                "أي موقع يمكنه قراءة بيانات التنبيهات من متصفح الضحية (تسريب بيانات SOC).")
        else:
            chk("CORS-002", f"CORS محكوم على {path}", "info", False, f"ACAO={acao!r}")

    # ── 2) قياس كم تنبيه يُقرأ بلا مصادقة ─────────────────────────
    print("\n▶ التعرّض على بيانات التنبيهات")
    readable, total, fields, sample = 0, 0, set(), {}
    for i in range(1, args.alerts + 1):
        r = s.get(urljoin(base, f"api/alerts/{i}"), timeout=12)
        total += 1
        if r.status_code == 200:
            readable += 1
            try:
                d = r.json()
                if i == 1:
                    sample = d
                for k in (d.keys() if isinstance(d, dict) else []):
                    fields.add(k)
            except Exception:
                pass
    chk("BAC-001", "قراءة التنبيهات بلا مصادقة", "critical", readable > 0,
        f"{readable}/{total} تنبيه يُقرأ بـ 200 بدون أي توكن",
        json.dumps(sample, ensure_ascii=False)[:1200],
        f"تسريب {readable} تنبيه (بيانات SOC: أسماء الأجهزة، عناوين IP، سجلات، hashes).")
    out["alert_fields"] = sorted(fields)
    out["alerts_readable"] = readable
    out["alerts_probed"] = total

    # ── 3) الكتابة/الحذف — بمعرّف غير موجود (آمن) ─────────────────
    print("\n▶ الحماية على الكتابة والحذف")
    ghost = 999999999
    for method, path, cid, name in (("DELETE", f"/api/alerts/{ghost}", "BAC-002", "حذف تنبيه بلا مصادقة"),
                                    ("PUT", f"/api/alerts/{ghost}", "BAC-003", "تعديل تنبيه بلا مصادقة")):
        try:
            r = s.request(method, urljoin(base, path.lstrip("/")),
                          json={"severity": "low", "status": "new"} if method == "PUT" else None,
                          timeout=12)
        except requests.RequestException as e:
            chk(cid, name, "high", False, f"خطأ: {e}")
            continue
        chk(cid, name, "critical" if r.status_code in (200, 201, 204) else "info",
            r.status_code in (200, 201, 204),
            f"{method} {path} → {r.status_code} (معرّف غير موجود — لم يُمس أي سجل)",
            r.text[:400],
            "أي شخص يستطيع تعديل/حذف التنبيهات ⇒ إتلاف الأدلة وتسريب البيانات" if r.status_code < 400 else "")
        time.sleep(0.5)

    # ── 4) قياس تحديد المعدل على تسجيل الدخول ─────────────────────
    print("\n▶ مقاومة القوة Brute-force على تسجيل الدخول")
    rnd = "probe" + "".join(random.choices(string.ascii_lowercase, k=8))
    codes, msgs = [], set()
    for i in range(12):
        try:
            r = s.post(urljoin(base, "api/auth/login"),
                       json={"username": rnd, "password": "WrongProbe!123"}, timeout=12)
            codes.append(r.status_code)
            try:
                msgs.add(json.dumps(r.json())[:160])
            except Exception:
                msgs.add(r.text[:160])
        except requests.RequestException:
            break
        time.sleep(0.35)
    chk("AUTH-001", "تحديد معدل على تسجيل الدخول", "high",
        all(c == 429 for c in codes) or len(codes) < 12,
        f"12 محاولة باسم عشوائي → {codes}",
        " | ".join(sorted(msgs))[:600],
        "مهاجم يجرّب كلمات مرور بلا حدّ (brute-force) إن وُجدت حسابات ضعيفة.")
    out["login_codes"] = codes
    out["login_messages"] = sorted(msgs)

    # ── 5) كشف المستخدم (user enumeration) ────────────────────────
    print("\n▶ كشف المستخدم")
    msgs_unknown = set()
    for u in (rnd, rnd + "x", "definitely-not-a-user-zzz"):
        try:
            r = s.post(urljoin(base, "api/auth/login"), json={"username": u, "password": "WrongProbe!123"}, timeout=12)
            msgs_unknown.add(r.text[:200])
        except requests.RequestException:
            pass
        time.sleep(0.3)
    out["login_unknown_user_messages"] = sorted(msgs_unknown)
    chk("AUTH-002", "رسائل موحّدة لغياب المستخدم", "info", len(msgs_unknown) <= 1,
        f"{len(msgs_unknown)} رسالة مختلفة لأسماء مستخدمين غير موجودة",
        " | ".join(sorted(msgs_unknown))[:500],
        "يسهّل على المهاجم جمع أسماء المستخدمين الصالحة.")

    # ── 6) تسرّب آثار الأخطاء ─────────────────────────────────────
    print("\n▶ كشف المعلومات عبر الأخطاء")
    leak_markers = ("Traceback", "sqlalchemy", "psycopg2", "File \"", "pydantic_core",
                    "sqlalchemy.exc", "Internal Server Error", "Traceback (most recent call last)")
    for path, method, body in (("/api/alerts/abc", "GET", None),
                                ("/api/alerts/1/evidence?x=%00", "GET", None),
                                ("/api/auth/login", "POST", {"username": None, "password": {"a": 1}}),
                                ("/api/alerts/1", "GET", None)):
        try:
            r = s.request(method, urljoin(base, path.lstrip("/")), json=body, timeout=12)
        except requests.RequestException:
            continue
        hits = [m for m in leak_markers if m.lower() in r.text.lower()]
        if hits:
            chk("INF-001", f"تسرّب تقني في {path}", "medium", True, f"Internal Server Error" if r.status_code >= 500 else "TRACE",
                r.text[:600], "يكشف بنية النظام/المكتبة/المسارات الداخلية.")
            break
    else:
        chk("INF-002", "رسائل الأخطاء نظيفة", "info", False, "لا آثار داخلية في الأخطاء المفحوصة")

    # ── 7) هل HTTPS متاح؟ ─────────────────────────────────────────
    print("\n▶ TLS")
    host = base.split("//", 1)[1].split("/")[0]
    https_url = f"https://{host}/"
    try:
        r = s.get(https_url, timeout=12, verify=False)
        chk("TLS-001", "HTTPS متاح", "info", False, f"نجح الاتصال بـ {https_url} ({r.status_code})",
            r.text[:200], "أبقِ TLS إجبارياً (redirect + HSTS).")
    except requests.RequestException as e:
        chk("TLS-002", "لا يوجد HTTPS", "high", True, f"فشل TLS: {type(e).__name__}",
            str(e)[:300],
            "كل البيانات (بما فيها كلمات المرور والتوكنات) تُرسل نصّاً صريحاً على الشبكة.")

    # ── 8) نقاط التوثيق الإضافية ───────────────────────────────────
    print("\n▶ مسارات توثيق إضافية")
    for p in ("/docs", "/redoc", "/openapi.json", "/api/redoc"):
        try:
            r = s.get(urljoin(base, p.lstrip("/")), timeout=10)
        except requests.RequestException:
            continue
        if r.status_code == 200 and len(r.content) > 100:
            chk("DOC-001", f"مسار توثيق مكشوف: {p}", "low", True, f"{p} → 200 ({len(r.content)}B)",
                r.text[:200], "يمنح المهاجم خريطة كاملة للنظام.")

    out["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out["summary"] = {
        "vulnerable": sum(1 for c in out["checks"] if c["vulnerable"]),
        "checks": len(out["checks"]),
    }
    os.makedirs(args.out, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = os.path.join(args.out, f"verify_{host.replace(':', '_')}_{stamp}")
    with open(stem + ".json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*55}\nملاحظات مؤكدة: {out['summary']['vulnerable']} من {out['summary']['checks']} فحص")
    print(f"📄 {stem}.json")


if __name__ == "__main__":
    main()
