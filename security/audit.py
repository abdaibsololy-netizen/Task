#!/usr/bin/env python3
"""
audit.py — فحص أمني آلي لنظام منشور على الإنترنت (نطاقك أنت).

يقسّم الفحص إلى 6 محاور:
  1. TLS / HTTPS        — الشهادة، البروتوكول، HSTS، التحويل من HTTP
  2. ترويسات الأمان    — CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy...
  3. الكوكيز والجلسات  — Secure / HttpOnly / SameSite
  4. CORS               — Origin مفتوح + credentials
  5. كشف المعلومات     — مسارات حساسة، رسائل خطأ، أدوات إدارة
  6. إعدادات HTTP       — TRACE, Host header, إعادة توجيه مفتوحة, تحديد المعدل

الاستخدام:
    python security/audit.py https://example.com
    python security/audit.py https://example.com --out security/findings --timeout 12
    python security/audit.py https://example.com --skip-active     # فحص غير مؤثر فقط

المخرجات:
    security/findings/<host>_<timestamp>.json   — للآلة
    security/findings/<host>_<timestamp>.md     — للتقرير
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
except ImportError:  # pragma: no cover
    sys.exit("مطلوب requests → pip install -r security/requirements.txt")

UA = "SecAudit/1.0 (authorized self-scan, read-only)"
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

# ------------------------------------------------------------------


@dataclass
class Finding:
    id: str
    title: str
    severity: str          # critical | high | medium | low | info
    category: str
    detail: str = ""
    evidence: str = ""
    remediation: str = ""


@dataclass
class Report:
    target: str = ""
    started: str = ""
    finished: str = ""
    findings: list[Finding] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, **kw) -> None:
        self.findings.append(Finding(**kw))

    def to_json(self) -> str:
        return json.dumps(
            {
                "target": self.target,
                "started": self.started,
                "finished": self.finished,
                "facts": self.facts,
                "summary": self.summary(),
                "findings": [asdict(f) for f in self.findings],
            },
            ensure_ascii=False,
            indent=2,
        )

    def summary(self) -> dict:
        c: dict[str, int] = {}
        for f in self.findings:
            c[f.severity] = c.get(f.severity, 0) + 1
        return c

    def to_md(self) -> str:
        s = self.summary()
        lines = [
            f"# تقرير فحص أمني — {self.target}",
            "",
            f"- **البداية:** {self.started}",
            f"- **النهاية:** {self.finished}",
            f"- **عدد الملاحظات:** {len(self.findings)}",
            f"- **الملخص:** " + " | ".join(f"{k}: {v}" for k, v in sorted(s.items(), key=lambda x: SEV_ORDER.get(x[0], 9))),
            "",
            "## جدول الملاحظات",
            "",
            "| # | الخطورة | المحور | الملاحظة |",
            "|---|---------|--------|----------|",
        ]
        ordered = sorted(self.findings, key=lambda f: (SEV_ORDER.get(f.severity, 9), f.id))
        for i, f in enumerate(ordered, 1):
            lines.append(f"| {i} | {f.severity.upper()} | {f.category} | {f.title} |")
        lines.append("")
        for i, f in enumerate(ordered, 1):
            lines += [
                f"### {i}. {f.title}  `[{f.id}]`",
                f"- **الخطورة:** {f.severity}",
                f"- **المحور:** {f.category}",
            ]
            if f.detail:
                lines.append(f"- **التفسير:** {f.detail}")
            if f.evidence:
                lines.append("- **الدليل:**")
                lines.append("")
                lines.append("```")
                lines.append(f.evidence[:2000])
                lines.append("```")
                lines.append("")
            if f.remediation:
                lines.append(f"- **الإصلاح:** {f.remediation}")
            lines.append("")
        if self.facts:
            lines += ["## حقائق مُجمّعة", "", "```json", json.dumps(self.facts, ensure_ascii=False, indent=2), "```", ""]
        return "\n".join(lines)


# ------------------------------------------------------------------


class Client:
    def __init__(self, base: str, timeout: int = 10, verify: bool = True):
        self.base = base if base.endswith("/") else base + "/"
        self.timeout = timeout
        self.s = requests.Session()
        self.s.verify = verify
        self.s.headers.update({"User-Agent": UA, "Accept": "*/*"})
        self._log: list[dict] = []

    def req(self, path: str, method: str = "GET", **kw) -> requests.Response | None:
        url = urljoin(self.base, path.lstrip("/")) if path.startswith("/") else path
        try:
            r = self.s.request(method, url, timeout=self.timeout, allow_redirects=kw.pop("allow_redirects", True), **kw)
        except requests.RequestException as e:
            self._log.append({"url": url, "error": str(e)[:200]})
            return None
        self._log.append({"url": url, "status": r.status_code, "len": len(r.content)})
        return r

    def head(self, path: str = "/") -> requests.Response | None:
        return self.req(path, method="HEAD", allow_redirects=False)


# ------------------------------------------------------------------
# 1. TLS
# ------------------------------------------------------------------

def check_tls(host: str, report: Report) -> None:
    p = urlparse(host if "://" in host else f"https://{host}")
    hostname = p.hostname
    if not hostname:
        return
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ss:
                cert = ss.getpeercert()
                report.facts["tls_version"] = ss.version()
                report.facts["tls_cipher"] = (ss.cipher() or [""])[0]
                report.facts["cert_subject"] = str(cert.get("subject", ""))
                report.facts["cert_issuer"] = str(cert.get("issuer", ""))
                report.facts["cert_not_after"] = cert.get("notAfter", "")
    except Exception as e:
        report.add(
            id="TLS-001", title="فشل التحقق من TLS", severity="high", category="TLS",
            detail=f"تعذّر إكمال مصافحة TLS: {e}",
            remediation="تأكد أن_certificate صالح ومُجدَّد وأن النقطة 443 مفتوحة للعموم.",
        )
        return

    not_after = report.facts.get("cert_not_after", "")
    if not_after:
        try:
            exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days = (exp - datetime.now(timezone.utc)).days
            report.facts["cert_days_left"] = days
            if days < 0:
                report.add(id="TLS-002", title="الشهادة منتهية", severity="critical", category="TLS",
                           detail=f"انتهت الشهادة في {not_after}.", remediation="جدّد الشهادة فوراً (certbot renew).")
            elif days < 15:
                report.add(id="TLS-003", title="الشهادة قرب الانتهاء", severity="medium", category="TLS",
                           detail=f"يتبقى {days} يوماً على انتهاء الشهادة.",
                           remediation="أدر عملية التجديد التلقائي (certbot renew) وراقب فشل التجديد.")
        except ValueError:
            pass

    ver = report.facts.get("tls_version", "")
    if ver in ("TLSv1", "TLSv1.1", "SSLv3", "TLSv1.2" if False else ""):
        report.add(id="TLS-004", title=f"بروتوكول TLS قديم ({ver})", severity="high", category="TLS",
                   detail="المتصفحات الحديثة تدعم TLS 1.2+ فقط.",
                   remediation="اضبط ssl_protocols = TLSv1.2 TLSv1.3 على الخادم/الـ reverse proxy.")


# ------------------------------------------------------------------
# 2. ترويسات الأمان
# ------------------------------------------------------------------

SEC_HEADERS = {
    "strict-transport-security": ("HSTS", "medium",
        "أضف: Strict-Transport-Security: max-age=31536000; includeSubDomains"),
    "content-security-policy": ("CSP", "low",
        "أضف Content-Security-Policy صارمة (default-src 'self') لتقييد السكربتات والـ iframes"),
    "x-content-type-options": ("X-Content-Type-Options", "low",
        "أضف X-Content-Type-Options: nosniff"),
    "x-frame-options": ("X-Frame-Options / frame-ancestors", "medium",
        "أضف X-Frame-Options: DENY (أو frame-ancestors 'none' في CSP) لمنع Clickjacking"),
    "referrer-policy": ("Referrer-Policy", "info",
        "أضف Referrer-Policy: strict-origin-when-cross-origin"),
    "permissions-policy": ("Permissions-Policy", "info",
        "أضف Permissions-Policy لتقييد الكاميرا/المايكروفون/الموقع"),
}


def check_headers(r: requests.Response, report: Report) -> None:
    h = {k.lower(): v for k, v in r.headers.items()}
    report.facts["server"] = h.get("server", "")
    report.facts["powered_by"] = h.get("x-powered-by", "")
    report.facts["all_headers"] = dict(r.headers)

    if h.get("x-powered-by"):
        report.add(id="HDR-001", title="كشف التقنية عبر X-Powered-By", severity="info", category="ترويسات",
                   detail=f"الخادم يعلن: {h['x-powered-by']}", evidence=h["x-powered-by"],
                   remediation="أزل الترويسة أو اضبط expose_php=Off / server_tokens off.")

    for key, (label, sev, fix) in SEC_HEADERS.items():
        if key not in h:
            report.add(id=f"HDR-{list(SEC_HEADERS).index(key)+100:03d}", title=f"ترويسة {label} مفقودة",
                       severity=sev, category="ترويسات",
                       detail=f"الاستجابة لا تحتوي {label}.", remediation=fix)

    csp = h.get("content-security-policy", "")
    if csp and "unsafe-inline" in csp and "unsafe-eval" in csp:
        report.add(id="HDR-110", title="CSP متساهل (unsafe-inline + unsafe-eval)", severity="medium",
                   category="ترويسات", evidence=csp,
                   detail="هذهolicy تُبطل أثر CSP ضد XSS بشكل كبير.",
                   remediation="حوّل السكربتات إلى nonce/hash واحذف unsafe-eval.")
    elif csp and "unsafe-inline" in csp:
        report.add(id="HDR-111", title="CSP يسمح بـ unsafe-inline", severity="low", category="ترويسات",
                   evidence=csp, detail="XSS المضمّن يمرّ.",
                   remediation="استخدم nonce/hash بدل unsafe-inline.")

    if "server" in h and re_version(h["server"]):
        report.add(id="HDR-002", title="إصدار الخادم مكشوف", severity="info", category="ترويسات",
                   evidence=h["server"],
                   detail="رقم الإصدار يساعد المهاجم على اختيار ثغرة معروفة.",
                   remediation="server_tokens off (nginx) أو تعطيل Banner في IIS.")


def re_version(server: str) -> bool:
    import re
    return bool(re.search(r"\d+\.\d+", server or ""))


# ------------------------------------------------------------------
# 3. الكوكيز
# ------------------------------------------------------------------

def check_cookies(r: requests.Response, report: Report) -> None:
    for name, value in r.cookies.items():
        missing = []
        if not value.startswith("__Secure-") and "secure" not in value.lower():
            missing.append("Secure")
        if not value.startswith("__Host-"):
            missing.append("HttpOnly")
        if "samesite" not in value.lower():
            missing.append("SameSite")
        if missing:
            report.add(id="CKY-001", title=f"كوكي '{name}' بدون خصائص حماية", severity="medium",
                       category="كوكيز",
                       detail=f"ناقص: {', '.join(missing)} — قد يُسرق عبر XSS أو يُرسل عبر HTTP.",
                       evidence=f"Set-Cookie: {name}={value[:40]}",
                       remediation="أضف: Secure; HttpOnly; SameSite=Lax (أو Strict).")
    report.facts["cookies"] = sorted(r.cookies.keys())


# ------------------------------------------------------------------
# 4. CORS
# ------------------------------------------------------------------

def check_cors(client: Client, report: Report) -> None:
    r = client.req("/", headers={"Origin": "https://evil.example"})
    if r is None:
        return
    acao = r.headers.get("Access-Control-Allow-Origin", "")
    acac = r.headers.get("Access-Control-Allow-Credentials", "")
    report.facts["cors_origin_reflected"] = acao
    if acao == "*":
        sev = "high" if acac.lower() == "true" else "medium"
        report.add(id="CORS-001", title="CORS مفتوح على كل النطاقات", severity=sev, category="CORS",
                   detail=f"ACAO={acao} ACAC={acac or 'غير محدد'} — أي موقع يقدر يقرأ استجابات الـ API.",
                   evidence="\n".join(f"{k}: {v}" for k, v in r.headers.items() if k.lower().startswith("access-control")),
                   remediation="قيّد Origin لقائمة بيضاء صريحة، ولا تفعّل Allow-Credentials مع ACAO=*.")
    elif acao and "evil.example" in acao:
        report.add(id="CORS-002", title="CORS يعكس Origin الغريب", severity="high", category="CORS",
                   detail="الخادم يعكس أي Origin — تجاوز لسياسة CORS.",
                   evidence=f"ACAO: {acao}\nACAC: {acac}",
                   remediation="طابق Origin بقائمة بيضاء صريحة قبل الترويسة.")
    if acac.lower() == "true" and acao == "*":
        report.add(id="CORS-003", title="CORS: Origin=* مع Credentials", severity="critical", category="CORS",
                   detail="تركيبة ممنوعة في المتصفحات لكنها خطأ شائع وخطير.",
                   remediation="لا تجمع بين * و credentials.")


# ------------------------------------------------------------------
# 5. كشف المعلومات / المسارات الحساسة
# ------------------------------------------------------------------

SENSITIVE_PATHS = [
    ("/.git/HEAD", "critical", "مستودع git مكشوف — تسريب كامل للكود"),
    ("/.git/config", "critical", "إعدادات git مكشوفة (قد تحوي روابط ببيانات دخول)"),
    ("/.env", "critical", "ملف متغيرات البيئة مكشوف — مفاتيح/أسرار مباشرة"),
    ("/.env.local", "critical", "ملف env بديل مكشوف"),
    ("/.svn/entries", "high", "مستودع svn مكشوف"),
    ("/.DS_Store", "low", "ملف فهرسة نظام يكشف أسماء الملفات"),
    ("/backup.zip", "high", "أرشيف نسخة احتياطية مكشوف"),
    ("/backup.tar.gz", "high", "أرشيف نسخة احتياطية مكشوف"),
    ("/dump.sql", "critical", "نسخة قاعدة بيانات مكشوفة"),
    ("/database.sql", "critical", "نسخة قاعدة بيانات مكشوفة"),
    ("/config.json", "medium", "ملف إعدادات مكشوف"),
    ("/config.yaml", "medium", "ملف إعدادات مكشوف"),
    ("/config.php", "medium", "ملف إعدادات مكشوف"),
    ("/.htaccess", "medium", "htaccess مكشوف"),
    ("/wp-config.php.bak", "critical", "نسخة إعدادات ووردبريس مكشوفة"),
    ("/server-status", "high", "صفحة حالة Apache مكشوفة"),
    ("/server-info", "high", "صفحة معلومات Apache مكشوفة"),
    ("/phpinfo.php", "high", "phpinfo مكشوف"),
    ("/actuator", "critical", "Spring Boot Actuator مكشوف"),
    ("/actuator/env", "critical", "متغيرات بيئة التطبيق مكشوفة عبر Actuator"),
    ("/actuator/health", "info", "نقطة فحص صحة Actuator"),
    ("/actuator/heapdump", "critical", "heap dump مكشوف — يسريب ذاكرة التطبيق"),
    ("/debug/vars", "medium", "صفحة متغيرات Go مكشوفة"),
    ("/metrics", "medium", "مقاييس Prometheus مكشوفة"),
    ("/api/docs", "medium", "توثيق API مكشوف"),
    ("/swagger.json", "medium", "تعريف Swagger مكشوف"),
    ("/openapi.json", "medium", "تعريف OpenAPI مكشوف"),
    ("/graphql", "info", "نقطة GraphQL مكشوفة"),
    ("/graphiql", "info", "واجهة GraphiQL مكشوفة"),
    ("/admin", "info", "لوحة إدارة مكشوفة"),
    ("/api/health", "info", "نقطة صحة API"),
    ("/status", "info", "صفحة حالة"),
    ("/.well-known/security.txt", "info", "security.txt (مفقود/موجود)"),
    ("/robots.txt", "info", "robots.txt"),
    ("/sitemap.xml", "info", "sitemap.xml"),
]


def check_sensitive_paths(client: Client, report: Report) -> None:
    for path, sev, desc in SENSITIVE_PATHS:
        r = client.req(path, allow_redirects=False)
        if r is None:
            continue
        if r.status_code in (200, 206) and len(r.content) > 0:
            body = r.text[:300]
            interesting = r.status_code == 200 and path not in ("/robots.txt", "/sitemap.xml", "/.well-known/security.txt")
            level = sev if interesting else "info"
            if path == "/.well-known/security.txt" and r.status_code == 200:
                report.add(id="INF-100", title="security.txt موجود", severity="info", category="معلومات",
                           detail="يوفّر جهة اتصال للتبلّغ عن الثغرات.", evidence=body)
                continue
            report.add(id=f"INF-{abs(hash(path)) % 900 + 100:03d}", title=f"مسار حساس مكشوف: {path}",
                       severity=level, category="كشف معلومات", detail=desc, evidence=body)
        elif r.status_code in (301, 302, 307, 308) and path in ("/.git/HEAD", "/.env", "/actuator"):
            report.add(id=f"INF-{abs(hash(path)) % 900 + 100:03d}", title=f"إعادة توجيه من مسار حساس: {path}",
                       severity="low", category="كشف معلومات",
                       detail=f"المسار يحوّل إلى {r.headers.get('Location')} — قد يكون مجرد normalisation.",
                       evidence=f"Location: {r.headers.get('Location')}")


def check_error_disclosure(client: Client, report: Report) -> None:
    for path in ("/%00", "/..%00/", "/<script>", "/api/nonexistent-zzz-123", "/index.php?x[]=1"):
        r = client.req(path)
        if r is None:
            continue
        body = r.text
        markers = []
        for m in ("Traceback (most recent call last)", "django.core", "werkzeug", "SQLAlchemy",
                  "psycopg2", "mysql.connector", "PDOException", "java.lang.NullPointerException",
                  "at Object.<anonymous>", "Symfony\\Component", "Rails", "DEBUG = True",
                  "ORA-", "PostgreSQL", "SQLITE_", "Microsoft OLE DB Provider"):
            if m.lower() in body.lower():
                markers.append(m)
        if markers:
            report.add(id="INF-200", title="رسالة خطأ تكشف تفاصيل داخلية", severity="medium",
                       category="كشف معلومات",
                       detail=f"الاستجابة على {path} تحتوي آثاراً تقنية ({', '.join(markers[:3])}).",
                       evidence=body[:800],
                       remediation="اضبط DEBUG=False وأخفِ التفاصيل في production (صفحة خطأ عامة + تسجيل داخلي).")
            break


# ------------------------------------------------------------------
# 6. إعدادات HTTP
# ------------------------------------------------------------------

def check_http_methods(client: Client, report: Report, allow_write: bool = False) -> None:
    """TRACE/TRACK آمنة دائماً. PUT/DELETE/PATCH قد تُنشئ/تحذف بيانات — تتطلب إذناً صريحاً."""
    methods = ("TRACE", "TRACK", "PUT", "DELETE", "PATCH") if allow_write else ("TRACE", "TRACK")
    for m in methods:
        r = client.req("/", method=m, allow_redirects=False)
        if r is None:
            continue
        if r.status_code < 400:
            report.add(id="HTTP-001", title=f"الأسلوب {m} مسموح", severity="medium", category="HTTP",
                       detail=f"الخادم قبل طلب {m} على المسار الجذري (رمز {r.status_code}).",
                       evidence=f"{m} / → {r.status_code}\n" + "\n".join(f"{k}: {v}" for k, v in list(r.headers.items())[:8]),
                       remediation="السماح فقط لـ GET/POST/HEAD؛ عطّل TRACE على الويب server.")


def check_host_header(client: Client, report: Report) -> None:
    r = client.req("/", headers={"Host": "evil.example"}, allow_redirects=False)
    if r is None:
        return
    loc = r.headers.get("Location", "")
    body = r.text[:400]
    if "evil.example" in loc:
        report.add(id="HTTP-010", title="Host header injection (إعادة توجيه)", severity="high", category="HTTP",
                   detail="الخادم يحوّل إلى المضيف المُرسل — يسمح بهجمات تسميم الكاش/البريد.",
                   evidence=f"Location: {loc}", remediation="ابنِ الروابط من قائمة بيضاء للمضيفين.")
    elif "evil.example" in body:
        report.add(id="HTTP-011", title="انعكاس Host header فيBody", severity="medium", category="HTTP",
                   detail="المضيف المُرسل يظهر في محتوى الاستجابة (قد يكون XSS في قالب).",
                   evidence=body[:400], remediation="لا تنعكس قيمة Host في المخرجات.")


def check_open_redirect(client: Client, report: Report) -> None:
    params = ("redirect", "url", "next", "return", "returnUrl", "continue", "target", "dest", "goto")
    for p in params:
        for probe in ("https://evil.example/", "//evil.example/", "https:evil.example"):
            r = client.req(f"/?{p}={probe}", allow_redirects=False)
            if r is None:
                continue
            if r.status_code in (301, 302, 303, 307, 308) and "evil.example" in r.headers.get("Location", ""):
                report.add(id="HTTP-020", title="إعادة توجيه مفتوحة (Open Redirect)", severity="medium",
                           category="HTTP",
                           detail=f"المعامل ?{p}= يقود إلى موقع خارجي — يُستخدم في تصيّد OAuth/روابط_phishing.",
                           evidence=f"Location: {r.headers.get('Location')}",
                           remediation="اقبل فقط مسارات داخلية (ابدأ بـ / ولا تحتوي ://).")
                return


def check_rate_limit(client: Client, report: Report) -> None:
    codes = []
    for _ in range(8):
        r = client.req("/")
        if r is None:
            return
        codes.append(r.status_code)
        if r.status_code == 429:
            break
        time.sleep(0.4)
    report.facts["rate_limit_sample"] = codes
    if all(c == 200 for c in codes):
        report.add(id="HTTP-030", title="لا يوجد تحديد معدل (Rate limiting)", severity="low", category="HTTP",
                   detail="8 طلبات متتالية كلها نجحت بلا 429 — يسمح بـ brute-force على نقاط المصادقة.",
                   evidence=str(codes),
                   remediation="طبّق rate limiting على /login و /api (Redis/nginx limit_req) و429 بعد threshold.")


def check_http_to_https(base: str, report: Report) -> None:
    p = urlparse(base)
    if p.scheme != "https":
        report.add(id="TLS-010", title="النظام يعمل على HTTP فقط", severity="high", category="TLS",
                   detail="لا يوجد تشفير للنقل — كل بيانات وبيانات دخول تُرسل نصاً صريحاً.",
                   remediation="فعّل HTTPS وأجبِ بـ 301 إلى https، ثم فعّل HSTS.")
        return
    http_url = f"http://{p.netloc}/"
    try:
        r = requests.get(http_url, timeout=8, allow_redirects=False, headers={"User-Agent": UA})
        report.facts["http_redirect_status"] = r.status_code
        report.facts["http_redirect_location"] = r.headers.get("Location", "")
        if r.status_code in (200, 204) or "location" not in {k.lower() for k in r.headers}:
            report.add(id="TLS-011", title="نسخة HTTP متاحة بلا تحويل", severity="high", category="TLS",
                       detail=f"الطلب على {http_url} رجّع {r.status_code} بدون تحويل إلى HTTPS.",
                       evidence=f"HTTP {r.status_code}\n" + "\n".join(f"{k}: {v}" for k, v in list(r.headers.items())[:8]),
                       remediation="أضف تحويل 301 دائم إلى https في الـ reverse proxy / CDN.")
        elif not r.headers.get("Location", "").startswith("https://"):
            report.add(id="TLS-012", title="التحويل من HTTP لا يشير إلى HTTPS", severity="medium", category="TLS",
                       detail=f"Location = {r.headers.get('Location')}",
                       remediation="وجّه كل شيء إلى https.")
    except requests.RequestException:
        pass


def check_mixed_content(client: Client, report: Report) -> None:
    r = client.req("/")
    if r is None:
        return
    import re
    urls = re.findall(r'(?:src|href)\s*=\s*["\'](http://[^"\']+)', r.text, re.I)
    if urls:
        report.add(id="TLS-020", title="محتوى مختلط (Mixed content)", severity="medium", category="TLS",
                   detail="الصفحة (HTTPS) تحمّل موارد عبر HTTP — قابلة للتلاعب (MITM) وتُحجب في المتصفحات.",
                   evidence="\n".join(sorted(set(urls))[:10]),
                   remediation="استخدم https:// لكل الموارد أو protocol-relative→https.")


def check_idor(client: Client, report: Report) -> None:
    """مؤشر IDOR: هل يرد الخادم 200 بمحتوى مختلف لمعرّفات متجاورة؟"""
    pairs = [("/api/item/1", "/api/item/2"), ("/api/users/1", "/api/users/2"),
             ("/api/orders/1", "/api/orders/2"), ("/user/1", "/user/2"),
             ("/api/token/1", "/api/token/2"), ("/api/wallet/1", "/api/wallet/2"),
             ("/api/trade/1", "/api/trade/2"), ("/api/position/1", "/api/position/2")]
    for a, b in pairs:
        ra, rb = client.req(a, allow_redirects=False), client.req(b, allow_redirects=False)
        if ra is None or rb is None:
            continue
        if ra.status_code == 200 and rb.status_code == 200 and ra.text != rb.text and len(ra.text) > 20:
            report.add(id="API-001", title=f"مؤشر IDOR محتمل: {a} يرد بمحتوى مختلف", severity="medium",
                       category="API",
                       detail="معرّفان متجاوران يُرجعان 200 ببيانات مختلفة — تحقّق من أن المصادقة/الصلاحية مربوطة بالمالك.",
                       evidence=f"GET {a} → {ra.status_code} ({len(ra.text)}B)\nGET {b} → {rb.status_code} ({len(rb.text)}B)",
                       remediation="اربط كل مورد بمالكه (owner check) في طبقة التطبيق ولا تعتمد على إخفاء المعرّف.")
            return


def check_methods_auth(client: Client, report: Report) -> None:
    """نقاط المصادقة الشائعة — هل تترك منفذاً مفتوحاً؟"""
    for path in ("/api/config", "/api/settings", "/api/user", "/api/me", "/api/balance",
                 "/api/portfolio", "/api/state", "/api/trades", "/api/wallet",
                 "/admin/api", "/internal/health", "/api/admin", "/api/debug"):
        r = client.req(path, allow_redirects=False)
        if r is None:
            continue
        if r.status_code == 200 and len(r.content) > 10:
            report.add(id="API-010", title=f"نقطة API بلا مصادقة: {path}", severity="high", category="API",
                       detail="رجعت 200 بمحتوى — تحقّق منAUTH على هذه المسارات.",
                       evidence=r.text[:400],
                       remediation="أضف تحقق مصادقة/صلاحية على كل مسار تحت /api/admin و /internal.")


# ------------------------------------------------------------------
# فحص الواجهة الخلفية (backend) إن وُجدت
# ------------------------------------------------------------------

def check_stack_fingerprints(report: Report) -> None:
    h = report.facts.get("all_headers", {})
    server = str(h.get("Server", ""))
    powered = str(h.get("X-Powered-By", ""))
    blob = (server + " " + powered).lower()
    tech = []
    if "nginx" in blob: tech.append("nginx")
    if "apache" in blob: tech.append("Apache")
    if "cloudflare" in blob: tech.append("Cloudflare")
    if "vercel" in blob: tech.append("Vercel")
    if "netlify" in blob: tech.append("Netlify")
    if "express" in powered.lower(): tech.append("Express")
    if "php" in powered.lower() or "php" in blob: tech.append("PHP")
    if "iis" in blob: tech.append("IIS")
    if "django" in blob: tech.append("Django")
    report.facts["stack"] = tech


# ------------------------------------------------------------------


def run_audit(base: str, timeout: int = 10, active: bool = True, outdir: str = "security/findings",
              allow_write_methods: bool = False) -> Report:
    report = Report(target=base, started=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    client = Client(base, timeout=timeout)

    root = client.req("/")
    if root is None:
        report.add(id="NET-001", title="الموقع لا يستجيب", severity="critical", category="شبكة",
                   detail="لم يصل رد على الطلب الأساسي — تحقّق من الرابط/المنفذ/الـ firewall.",
                   remediation="تأكد أن الخادم يعمل وأن الرابط صحيح.")
    else:
        report.facts["root_status"] = root.status_code
        report.facts["root_title"] = extract_title(root.text)
        report.facts["root_final_url"] = root.url
        report.facts["body_length"] = len(root.content)
        check_headers(root, report)
        check_cookies(root, report)
        check_stack_fingerprints(report)

    check_tls(base, report)
    check_http_to_https(base, report)

    if active:
        check_cors(client, report)
        check_sensitive_paths(client, report)
        check_error_disclosure(client, report)
        check_http_methods(client, report, allow_write=allow_write_methods)
        check_host_header(client, report)
        check_open_redirect(client, report)
        check_methods_auth(client, report)
        check_idor(client, report)
        check_mixed_content(client, report)
        check_rate_limit(client, report)

    report.finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        host = urlparse(base).netloc.replace(":", "_")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = os.path.join(outdir, f"{host}_{stamp}")
        with open(stem + ".json", "w") as f:
            f.write(report.to_json())
        with open(stem + ".md", "w") as f:
            f.write(report.to_md())
        report.facts["report_files"] = [stem + ".json", stem + ".md"]
    return report


def extract_title(html: str) -> str:
    import re
    m = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    return (m.group(1).strip()[:120] if m else "")


def main() -> None:
    ap = argparse.ArgumentParser(description="فحص أمني آلي لموقعك")
    ap.add_argument("target", help="رابط الموقع، مثال: https://example.com")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--out", default="security/findings")
    ap.add_argument("--skip-active", action="store_true", help="تخطّي الفحوص النشطة (الملفات/الطرق/CORS)")
    ap.add_argument("--allow-write-methods", action="store_true",
                    help="السماح بـ PUT/DELETE/PATCH (قد تغيّر حالة الخادم — استخدم بحذر)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rep = run_audit(args.target, timeout=args.timeout, active=not args.skip_active, outdir=args.out,
                    allow_write_methods=args.allow_write_methods)
    s = rep.summary()
    if not args.quiet:
        print(f"\n=== فحص {args.target} ===")
        for sev in ("critical", "high", "medium", "low", "info"):
            if s.get(sev):
                print(f"  {sev.upper():8} {s[sev]}")
        print("\n" + rep.to_md()[:2000])
        if rep.facts.get("report_files"):
            print("\n📄 التقرير الكامل: " + ", ".join(rep.facts["report_files"]))
    else:
        print(json.dumps({"target": rep.target, "summary": rep.summary()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
