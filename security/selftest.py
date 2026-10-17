#!/usr/bin/env python3
"""
selftest.py — يثبت أن أدوات الفحص تكتشف الثغرات فعلاً.

يشغّل خادماً HTTP محلياً **مصاباً عمداً** (ملفات مكشوفة، XSS، SQL error،
Open Redirect، كوكي بلا حماية، TRACE مفعّل) ثم يشغّل audit/probe عليه
ويتحقق أن كل ثغرة مُدخلة قد رُصدت.

الاستخدام:
    python security/selftest.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from audit import run_audit  # noqa: E402
from probe import Report, discover_targets, probe  # noqa: E402

GIT_HEAD = "ref: refs/heads/main\n"
ENV_FILE = "PUMPBOT_PRIVATE_KEY=5KDu...\nDB_PASSWORD=hunter2\n"


class VulnHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # noqa: D102
        pass

    # ---------- السكربت ----------
    def _send(self, code, body=b"", headers=None, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        path, _, query = self.path.partition("?")
        q = {k: unquote(v) for k, v in
             (p.split("=", 1) for p in query.split("&") if "=" in p)}

        if path == "/.git/HEAD":
            return self._send(200, GIT_HEAD.encode(), {"Server": "nginx/1.18.0"})
        if path == "/.env":
            return self._send(200, ENV_FILE.encode())
        if path == "/.DS_Store":
            return self._send(200, b"\x00\x00\x01Bud1")
        if path == "/robots.txt":
            return self._send(200, b"User-agent: *\nDisallow: /admin\n")
        if path == "/search":
            val = q.get("q", "")
            if "'" in val:
                return self._send(500, b"SQLSTATE[42S02]: Base table or view not found: pg_error")
            body = f"<html><body><h1>نتائج</h1><p>بحث عن: {val}</p></body></html>".encode()
            return self._send(200, body, {"Set-Cookie": "session=abc123; Path=/"})
        if path == "/redirect" or ("url" in q and path != "/api/item/1"):
            return self._send(302, b"", {"Location": q.get("url", "/")})
        if path == "/api/user":
            return self._send(200, b'{"name":"someone","email":"a@b.c"}')
        if path == "/api/item/1":
            return self._send(200, b'{"id":1,"secret":"alpha"}')
        if path == "/api/item/2":
            return self._send(200, b'{"id":2,"secret":"bravo"}')
        if path == "/":
            body = b"<html><head><title>Home</title></head><body><a href='/search?q=test'>s</a></body></html>"
            return self._send(200, body, {"X-Powered-By": "PHP/8.1.2",
                                          "Set-Cookie": "session=abc123; Path=/"})
        return self._send(404, b"not found")

    def do_TRACE(self):  # noqa: N802
        self._send(200, b"TRACE / HTTP/1.1\r\nX-Test: 1\r\n\r\n")

    def do_HEAD(self):  # noqa: N802
        self._send(200, b"")


def start_server() -> tuple[ThreadingHTTPServer, str]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), VulnHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def main() -> int:
    srv, base = start_server()
    print(f"🧪 خادم مصاب محلياً على {base}\n")
    failures: list[str] = []

    # ---------- audit.py ----------
    print("▶ audit.py …")
    rep = run_audit(base, timeout=5, active=True, outdir=os.path.join(HERE, "findings"))
    ids = {f.id for f in rep.findings}
    titles = " | ".join(f.title for f in rep.findings)
    expect_audit = {
        "ملف .git مكشوف": any(i.startswith("INF-") for i in ids),
        "ملف .env مكشوف": any(i.startswith("INF-") for i in ids),
        "TRACE مسموح": "HTTP-001" in ids,
        "Open Redirect": "HTTP-020" in ids,
        "HTTP بدون TLS": "TLS-010" in ids,
        "نقطة API بلا مصادقة": "API-010" in ids,
        "مؤشر IDOR": "API-001" in ids,
        "X-Powered-By": "HDR-001" in ids,
        "كوكي بلا حماية": "CKY-001" in ids,
        "ترويسات ناقصة": any(i.startswith("HDR-1") for i in ids),
    }
    for name, ok in expect_audit.items():
        print(f"  {'✅' if ok else '❌'} {name}")
        if not ok:
            failures.append(f"audit: {name}")
    print(f"  ملاحظات audit: {len(rep.findings)}")

    # ---------- probe.py ----------
    print("\n▶ probe.py …")
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": "selftest"})
    pr = Report(target=base)
    disc = discover_targets(s, base, [], [])
    print(f"  {'✅' if disc else '❌'} اكتشاف نقاط الإدخال ({len(disc)})")
    if not disc:
        failures.append("probe: discover_targets")
    probe(s, pr, f"{base}/search", "q", {"sqli", "xss"})
    probe(s, pr, f"{base}/redirect", "url", {"xss"})
    pids = {f.id for f in pr.findings}
    expect_probe = {
        "SQLi error-based": "SQLI-001" in pids,
        "XSS reflected": "XSS-001" in pids or "XSS-002" in pids,
    }
    for name, ok in expect_probe.items():
        print(f"  {'✅' if ok else '❌'} {name}")
        if not ok:
            failures.append(f"probe: {name}")
    print(f"  ملاحظات probe: {len(pr.findings)}")

    # ---------- secrets_scan.py ----------
    print("\n▶ secrets_scan.py …")
    tmp = os.path.join(HERE, "findings", "_selftest_tmp")
    os.makedirs(tmp, exist_ok=True)
    with open(os.path.join(tmp, "leak.py"), "w") as f:
        f.write('PRIVATE_KEY = "4NMwxzmYj2uvHuq8xoqhY8RXc63K3WSbuyD8KFGbXPn3Kt3dRfvvc6QeBqmzCypgMeV7Uq2Ao6xK9vBt5ZpQrWmNh"\n'
                'TG = "1234567890:AAHdG9zQ2wErTyUiOpAsDfGhJkLzXcVbNm1234"\n')
    out: list[dict] = []
    import secrets_scan
    secrets_scan.scan_repo(tmp, history=False, out=out)
    stypes = {f["type"] for f in out}
    expect_secrets = {
        "Solana key": any("Solana" in t for t in stypes),
        "Telegram token": any("Telegram" in t for t in stypes),
    }
    for name, ok in expect_secrets.items():
        print(f"  {'✅' if ok else '❌'} {name}")
        if not ok:
            failures.append(f"secrets: {name}")

    srv.shutdown()
    print("\n" + "═" * 50)
    if failures:
        print(f"❌ فشل {len(failures)} اختبار: {failures}")
        return 1
    print("✅ كل الاختبارات ناجحة — الأدوات جاهزة لفحص موقعك")
    return 0


if __name__ == "__main__":
    sys.exit(main())
