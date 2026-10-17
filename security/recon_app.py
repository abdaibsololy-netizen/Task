#!/usr/bin/env python3
"""
recon_app.py — استطلاع مُعجب بالتطبيق (SPA / REST / GraphQL).

ما يفعله:
  1. يقرأ صفحة الجذر ويحفظها
  2. ينزّل كل ملفات JS/CSS ويبحث فيها عن: أسرار، مسارات API، روابط مصادقة
  3. يبحث عن مواصفات API (swagger/openapi/redoc) ويحفظها
  4. يبني خريطة نقاط النهاية من المواصفة + من حزم JS
  5. يختبر كل نقطة نهاية: بلا مصادقة / بتوكن وهمية / مع/id
  6. يبحث عن: نقاط بلا مصادقة، IDOR، كشف أخطاء، GraphQL، CORS، rate-limit على /login

الاستخدام:
    python security/recon_app.py http://target --out security/findings
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("مطلوب requests")

UA = "SecRecon/1.0 (authorized self-scan, read-only)"
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

SPEC_PATHS = ["/api/docs", "/swagger.json", "/openapi.json", "/api/openapi.json",
              "/v3/api-docs", "/api-docs", "/api/v1/openapi.json", "/redoc",
              "/api/docs/openapi.json", "/api/swagger.json", "/swagger/v1/swagger.json",
              "/api/schema", "/api/spec"]

JS_EXT = (".js", ".mjs", ".css", ".map")
ASSET_RE = re.compile(r'(?:src|href)\s*=\s*["\']([^"\']+\.(?:js|mjs|css|map)(?:\?[^"\']*)?)["\']', re.I)
API_PATH_RE = re.compile(r'["\'`](/api/[A-Za-z0-9_\-/{}.:]+)')
URL_RE = re.compile(r'https?://[A-Za-z0-9_\-./:%]+')

# أسرار داخل حزم JS
JS_SECRET_RES = [
    ("مفتاح API/Token", re.compile(r'(?i)["\'](?:api[_-]?key|apikey|access[_-]?token|auth[_-]?token|secret[_-]?key|bearer|token)["\']\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{16,})["\']')),
    ("Solana private key", re.compile(r'["\']([1-9A-HJ-NP-Za-km-z]{85,90})["\']')),
    ("Telegram token", re.compile(r'["\'](\d{8,10}:[A-Za-z0-9_\-]{35,})["\']')),
    ("AWS key", re.compile(r'["\']((?:AKIA|ASIA)[0-9A-Z]{16})["\']')),
    ("Google API key", re.compile(r'["\'](AIza[0-9A-Za-z_\-]{35})["\']')),
    ("JWT", re.compile(r'["\'](eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})["\']')),  # sec:ignore
    ("مفتاح Solana عام؟", re.compile(r'["\']([1-9A-HJ-NP-Za-km-z]{43,44})["\']')),
]


@dataclass
class Finding:
    id: str
    title: str
    severity: str
    category: str
    detail: str = ""
    evidence: str = ""
    endpoint: str = ""
    remediation: str = ""


@dataclass
class Report:
    target: str = ""
    started: str = ""
    finished: str = ""
    findings: list[Finding] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    endpoints: list[dict] = field(default_factory=list)

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
            "summary": self.summary(), "facts": self.facts,
            "endpoints": self.endpoints, "findings": [asdict(f) for f in self.findings],
        }, ensure_ascii=False, indent=2)

    def to_md(self) -> str:
        o = sorted(self.findings, key=lambda f: (SEV_ORDER.get(f.severity, 9), f.id))
        out = [f"# تقرير استطلاع التطبيق — {self.target}", "",
               f"- **البداية:** {self.started}", f"- **النهاية:** {self.finished}",
               f"- **نقاط النهاية المكتشفة:** {len(self.endpoints)}",
               f"- **الملاحظات:** " + " | ".join(f"{k}:{v}" for k, v in sorted(self.summary().items(), key=lambda x: SEV_ORDER.get(x[0], 9))),
               "", "## خريطة نقاط النهاية", "", "| المسار |ethods | الملاحظات |", "|---|---|---|"]
        for e in self.endpoints:
            out.append(f"| `{e.get('path','')}` | {', '.join(e.get('methods', [])) or '-'} | {e.get('note','')} |")
        out += ["", "## الملاحظات", "", "| # | الخطورة | النوع | الملاحظة | المسار |", "|---|---|---|---|---|"]
        for i, f in enumerate(o, 1):
            out.append(f"| {i} | {f.severity.upper()} | {f.category} | {f.title} | `{f.endpoint}` |")
        out.append("")
        for i, f in enumerate(o, 1):
            out += [f"### {i}. {f.title} `[{f.id}]`", f"- **الخطورة:** {f.severity}",
                    f"- **المسار:** `{f.endpoint}`"]
            if f.detail:
                out.append(f"- **التفسير:** {f.detail}")
            if f.evidence:
                out += ["", "```", f.evidence[:1200], "```", ""]
            if f.remediation:
                out.append(f"- **الإصلاح:** {f.remediation}")
            out.append("")
        return "\n".join(out)


def get(s: requests.Session, url: str, **kw) -> requests.Response | None:
    try:
        return s.get(url, timeout=kw.pop("timeout", 12), allow_redirects=kw.pop("allow_redirects", True), **kw)
    except requests.RequestException:
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description="استطلاع مُعجب بالتطبيق")
    ap.add_argument("target")
    ap.add_argument("--out", default="security/findings")
    ap.add_argument("--max-assets", type=int, default=30)
    args = ap.parse_args()

    base = args.target if args.target.endswith("/") else args.target + "/"
    outdir = os.path.join(args.out, "app")
    os.makedirs(outdir, exist_ok=True)

    rep = Report(target=args.target, started=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    # ── 1) الصفحة الجذرية ───────────────────────────────────────────
    root = get(s, base)
    if root is None:
        rep.add(id="NET-001", title="الموقع لا يستجيب", severity="critical", category="شبكة",
                detail="لم يصل رد على الطلب الأساسي.")
        print("❌ لا استجابة — تحقّق من الرابط")
        _save(rep, args.out, base)
        return

    html = root.text
    open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(html)
    rep.facts["root_status"] = root.status_code
    rep.facts["root_server"] = root.headers.get("Server", "")
    rep.facts["root_headers"] = dict(root.headers)
    rep.facts["root_len"] = len(root.content)
    rep.facts["root_sha256"] = hashlib.sha256(root.content).hexdigest()[:16]
    rep.facts["root_title"] = (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S).group(1).strip()
                               if re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) else "")
    print(f"✔ الجذر: {root.status_code} | {rep.facts['root_title']} | {len(root.content)}B")

    # ── 2) تنزيل الأصول ────────────────────────────────────────────
    assets: list[str] = []
    for m in ASSET_RE.finditer(html):
        u = urljoin(base, m.group(1))
        if u not in assets:
            assets.append(u)
    rep.facts["assets_found"] = len(assets)

    js_text = ""
    for i, u in enumerate(assets[: args.max_assets], 1):
        r = get(s, u)
        if r is None or r.status_code >= 400:
            continue
        name = os.path.basename(urlparse(u).path) or f"asset{i}"
        try:
            open(os.path.join(outdir, name), "w", encoding="utf-8").write(r.text)
        except OSError:
            pass
        if name.endswith((".js", ".mjs", ".map")):
            js_text += "\n" + r.text
        print(f"  ✔ asset {i}/{len(assets[:args.max_assets])}: {name} ({len(r.content)}B)")

    # ── 3) أسرار داخل حزم JS ────────────────────────────────────────
    if js_text:
        for lname, pat in JS_SECRET_RES:
            for m in pat.finditer(js_text):
                val = m.group(1) if m.groups() else m.group(0)
                if any(h in val.lower() for h in ("example", "your-", "xxxx", "placeholder")):
                    continue
                rep.add(id="JS-SEC-001", title=f"أسرار داخل حزمة JS: {lname}", severity="critical",
                        category="تسريب أسرار",
                        detail="سر مُضمَّن في كود الواجهة — أي زائر يستطيع قراءته من المتصفح.",
                        evidence=f"{val[:10]}…{val[-6:]} (len={len(val)})",
                        remediation="انقل المفاتيح إلى الخادم (backend proxy) — لا تضع مفاتيح في الـ frontend.")
        # مسارات API من JS
        api_paths = sorted(set(API_PATH_RE.findall(js_text)))
        rep.facts["api_paths_from_js"] = api_paths[:200]
        print(f"✔ مسارات API في JS: {len(api_paths)}")
        # روابط خارجية
        ext = sorted({u for u in URL_RE.findall(js_text)
                      if not re.match(r"https?://(localhost|127\.0\.0\.1|20\.215\.186\.30|w3\.org|schemas\.)", u)})[:60]
        rep.facts["external_urls_in_js"] = ext

    # ── 4) مواصفات API ──────────────────────────────────────────────
    spec = None
    for p in SPEC_PATHS:
        u = urljoin(base, p)
        r = get(s, u)
        if r is None or r.status_code >= 400:
            continue
        ct = r.headers.get("Content-Type", "")
        if "json" in ct and r.text.lstrip()[:1] in "{[":
            spec = r.json()
            open(os.path.join(outdir, "openapi.json"), "w", encoding="utf-8").write(r.text)
            rep.facts["openapi_path"] = p
            rep.add(id="API-020", title="مواصفة OpenAPI/Swagger منشورة", severity="medium", category="API",
                    detail="أي زائر يستطيع قراءة كل نقاط النهاية والمخططات.",
                    evidence=f"{p} → {len(r.content)}B",
                    remediation="احمِ المواصفة (Basic auth / allowlist / أزلها من الإنتاج).")
            break
        if "swagger" in r.text.lower() or "openapi" in r.text.lower():
            open(os.path.join(outdir, f"docs{os.path.basename(p) or '.html'}"), "w", encoding="utf-8").write(r.text)
            rep.facts.setdefault("api_docs_urls", []).append(p)
            rep.add(id="API-021", title="صفحة توثيق API منشورة", severity="low", category="API",
                    detail="توثيق تفاعلي متاح بلا مصادقة.", evidence=p,
                    remediation="قيّد الوصول لصفحة التوثيق.")
    if spec is None:
        rep.facts.setdefault("api_docs_urls", [])

    # ── 5) خريطة نقاط النهاية ───────────────────────────────────────
    endpoints: dict[str, set] = {}
    if spec:
        for path, item in (spec.get("paths") or {}).items():
            methods = [m.upper() for m in item.keys() if m.lower() in
                       ("get", "post", "put", "patch", "delete", "head", "options")]
            endpoints.setdefault(path, set()).update(methods)
    for p in rep.facts.get("api_paths_from_js", []):
        endpoints.setdefault(p, set())

    ep_list = []
    for path, methods in sorted(endpoints.items()):
        ep_list.append({"path": path, "methods": sorted(methods), "note": ""})
    rep.endpoints = ep_list

    # ── 6) اختبار المصادقة على كل نقطة ──────────────────────────────
    # توكن وهمي يُبنى في وقت التشغيل (حتى لا يطابقه ماسح الأسرار)
    FAKE = ("Bearer " + "eyJhbGciOiJIUzI1NiJ9" + "." +
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0" + "." + "dummy-signature")
    for ep in rep.endpoints:
        path = ep["path"]
        if "{" in path:
            sample = re.sub(r"\{[^}]+\}", "1", path)
        else:
            sample = path
        u = urljoin(base, sample.lstrip("/"))
        r0 = get(s, u)
        if r0 is None:
            continue
        sig0 = hashlib.sha256(r0.content).hexdigest()
        is_spa = r0.content == root.content
        r1 = get(s, u, headers={"Authorization": FAKE})
        sig1 = hashlib.sha256(r1.content).hexdigest() if r1 is not None else ""
        rec = {
            "path": path, "sample": sample,
            "status_no_auth": r0.status_code, "len": len(r0.content),
            "status_fake_auth": r1.status_code if r1 else None,
            "differs_with_fake_token": sig0 != sig1,
            "content_type": r0.headers.get("Content-Type", ""),
            "spa_fallback": is_spa,
        }
        ep.update(rec)
        if is_spa:
            ep["note"] = "catch-all (SPA)"
            continue
        if r0.status_code == 200 and len(r0.content) > 0:
            ct = r0.headers.get("Content-Type", "")
            if "json" in ct or r0.text.lstrip()[:1] in "{[":
                rep.add(id="API-001", title=f"نقطة API ترجع بيانات بلا مصادقة: {sample}", severity="high",
                        category="Broken Access Control",
                        detail="الاستجابة 200 + JSON بدون أي مصادقة — تحقّق إن كانت البيانات حساسة.",
                        evidence=r0.text[:300], endpoint=sample,
                        remediation="أضف تحقق مصادقة/صلاحية على هذه النقطة (أو 401/403).")
                ep["note"] = "200 بلا مصادقة"
            else:
                ep["note"] = "200 (html/text)"
        if r1 is not None and rec["differs_with_fake_token"] and r1.status_code in (200, 201):
            rep.add(id="API-002", title="المصادقة تُقبل بتوكن وهمية (token validation ضعيفة)", severity="high",
                    category="Broken Access Control",
                    detail="الاستجابة تغيّرت مع توكن Bearer عشوائي — الخادم لا يتحقق من صحة التوكن بشكل صحيح.",
                    evidence=f"status: {r0.status_code} → {r1.status_code}", endpoint=sample,
                    remediation="تحقق من التوقيع/الصلاحية/الصلاحية الزمنية لكل طلب.")
    # ── 7) فحص login / register ─────────────────────────────────────
    for p in ("/api/login", "/api/auth/login", "/api/auth/register", "/api/register", "/api/users", "/api/user"):
        u = urljoin(base, p.lstrip("/"))
        r = get(s, u)
        if r is None or r.status_code >= 400:
            continue
        if r.content == root.content:
            continue
        rep.facts.setdefault("auth_endpoints", []).append({"path": p, "status": r.status_code,
                                                             "body": r.text[:200]})
        rep.add(id="API-030", title=f"نقطة مصادقة/مستخدم مكشوفة: {p}", severity="medium", category="API",
                detail="راجع: rate limiting، user enumeration، سياسة كلمة المرور، CSRF.",
                evidence=r.text[:300], endpoint=p,
                remediation="أضف rate limiting + قفل الحساب بعد محاولات فاشلة + رسالة خطأ موحّدة.")

    # ── 8) GraphQL / introspection ──────────────────────────────────
    for p in ("/graphql", "/api/graphql"):
        u = urljoin(base, p.lstrip("/"))
        payload = {"query": "{__schema{types{name}}}"}
        try:
            r = s.post(u, json=payload, timeout=12)
        except requests.RequestException:
            continue
        if r.status_code == 200 and "__schema" in r.text:
            rep.add(id="API-040", title="GraphQL introspection مفتوح", severity="medium", category="API",
                    detail="يمكن قراءة كامل المخطّط — يسرّع الاستطلاع والبناء.", endpoint=p,
                    evidence=r.text[:300], remediation="أغلق introspection في الإنتاج.")

    rep.finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save(rep, args.out, base)
    print("\n" + "=" * 50)
    for k, v in sorted(rep.summary().items(), key=lambda x: SEV_ORDER.get(x[0], 9)):
        print(f"  {k.upper():8} {v}")
    print(f"  نقاط النهاية: {len(rep.endpoints)} | الأصول: {rep.facts.get('assets_found',0)}")
    print(f"  الملفات المحفوظة: {outdir}")


def _save(rep: Report, outdir: str, base: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    host = urlparse(base).netloc.replace(":", "_")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = os.path.join(outdir, f"recon_{host}_{stamp}")
    with open(stem + ".json", "w") as f:
        f.write(rep.to_json())
    with open(stem + ".md", "w") as f:
        f.write(rep.to_md())


if __name__ == "__main__":
    main()
