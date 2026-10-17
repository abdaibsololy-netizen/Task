#!/usr/bin/env python3
"""
secrets_scan.py — البحث عن أسرار مسرّبة داخل المستودع أو داخل موقعك المنشور.

الاستخدام:
    python security/secrets_scan.py                      # المستودع كله (ملفات + تاريخ git)
    python security/secrets_scan.py --path bot --no-history
    python security/secrets_scan.py --url https://example.com   #_site: HTML + JS bundles_

أنواع الأسرار المدعومة:
  Solana keypair (base58 / JSON array) | Telegram bot token | Helius / RPC keys
  AWS | GitHub tokens | Private keys (PEM) | Stripe | Slack | Discord webhook
  Google API key | Infura / Alchemy | JWT | generic api_key/secret/token assignments
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    pass

# (اسم، regex، خطورة، توصية)
PATTERNS: list[tuple[str, str, str, str]] = [
    ("Solana private key (base58)", r"\b[1-9A-HJ-NP-Za-km-z]{85,90}\b", "critical",
     "المفتاح يجب أن يكون في متغير بيئة فقط — إن كان حقيقياً فاقلبه فوراً (لا يمكن استرجاع funds من نفس المفتاح)."),
    ("Solana JSON keypair", r"\[\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*[\"\d,\s]{40,}\]", "critical",
     "احذف الملف من تاريخ git (git filter-repo / BFG) وأعد توليد المفتاح."),
    ("PEM private key", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", "critical",
     "أزله فوراً من المستودع واعتبره مكشوفاً."),
    ("Telegram bot token", r"\b\d{8,10}:[A-Za-z0-9_-]{35,}\b", "critical",
     "ألغِ التوكن من @BotFather وأعد إصداره (revoke)."),
    ("AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", "critical",
     "عطّل المفتاح من IAM فوراً ( deactivate ) وأصدر مفتاحاً جديداً."),
    ("AWS secret", r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})", "critical",
     "ألغِ المفتاح من IAM فوراً."),
    ("GitHub token", r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b", "critical",
     "ألغِ التوكن من GitHub Settings → Developer settings وأعد إصداره."),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "critical", "ألغِ التوكن من Slack app settings."),
    ("Slack webhook", r"https://hooks\.slack\.com/services/T[A-Za-z0-9_/]{20,}", "high",
     "ألغِ الـ webhook وأعد إنشاءه."),
    ("Discord webhook", r"https://discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_-]{20,}", "high",
     "احذف الـ webhook وأنشئ واحداً جديداً."),
    ("Stripe secret key", r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}\b", "critical", "ألغِ المفتاح من Stripe Dashboard."),
    ("Google API key", r"\bAIza[0-9A-Za-z_-]{35}\b", "high", "قيّد المفتاح بـ API restrictions ثم أعد توليده."),
    ("Infura/Alchemy key", r"\b(?:https://[a-z0-9-]+\.(?:infura\.io|gateway\.alchemy\.com)/v[0-9]/[A-Za-z0-9]{20,})\b", "high",
     "أنشئ project جديداً وقيّد المفتاح."),
    ("Helius API key", r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "medium",
     "تحقّق إن كان UUID هو مفتاح Helius — دوّره من helius.dev."),
    ("JWT", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "high",
     "إن كان توكن جلسة فعّالاً فأي شخص يستطيع استخدامه."),
    ("Generic secret assignment", r"(?i)\b(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key|passwd|password)\b\s*[=:]\s*['\"]([^'\"\s]{12,})['\"]", "high",
     "انقل القيمة إلى متغير بيئة أو GitHub Secrets ولا تضعها في الكود."),
    ("Basic auth in URL", r"https?://[^\s:/@]+:[^\s:/@]+@[^\s/]+", "high",
     "المستخدم:كلمة المرور داخل الرابط تُسجَّل في السجلات|Referer — انقلها للترويسة."),
]

# ملفات لا تفحص (ثنائيات/حزم/بيانات ضخمة)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
             ".mypy_cache", ".pytest_cache", ".ruff_cache", "security/findings"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar", ".ico",
            ".woff", ".woff2", ".ttf", ".eot", ".so", ".pyc", ".mp4", ".mp3", ".webp"}
MAX_BYTES = 3_000_000

# نصائح التعديل (Markdown/JSON/CSV) — نخفّض الضجيج
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".htm", ".css", ".scss", ".json",
            ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".sh", ".bash", ".zsh",
            ".md", ".txt", ".csv", ".php", ".rb", ".go", ".rs", ".java", ".sql", ".vue", ".svelte",
            ".xml", ".htaccess", ".gitignore", ".gitconfig", ""}

# كلمات تُستعمل كـ placeholders شائعة — نتجاهلها لتفادي الإيجابيات الكاذبة.
# (مقصود: لا تحذف كلمات مثل "fake"/"dummy" لأنها قد ترد داخل أسرار حقيقية)
FALSE_POSITIVE_HINTS = ("example", "xxxxxxx", "your-", "changeme", "placeholder",
                         "redacted", "<your", "xxxxx")


def is_noise(text: str) -> bool:
    low = text.lower()
    return any(h in low for h in FALSE_POSITIVE_HINTS)


def scan_text(text: str, where: str, out: list[dict], allow_noise: bool = False) -> None:
    for name, pat, sev, fix in PATTERNS:
        for m in re.finditer(pat, text):
            val = m.group(0)
            if not allow_noise and is_noise(val):
                continue
            masked = val[:6] + "…" + val[-4:] if len(val) > 14 else val[:3] + "…"
            out.append({
                "type": name, "severity": sev, "where": where,
                "match_preview": masked, "line": text[:m.start()].count("\n") + 1,
                "remediation": fix,
            })


def scan_repo(root: str = ".", history: bool = True, out: list[dict] | None = None) -> None:
    out = out if out is not None else []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".venv")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
                data = open(p, "rb").read()
            except OSError:
                continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            if ext not in TEXT_EXT and not fn.startswith("."):
                continue
            before = len(out)
            scan_text(text, p, out)
            if len(out) > before:
                out[-1]["source"] = "working tree"

    if history:
        try:
            log = subprocess.run(
                ["git", "-C", root, "log", "-p", "--all", "--no-color"],
                capture_output=True, text=True, timeout=120).stdout
            before = len(out)
            scan_text(log, "git history (git log -p --all)", out)
            if len(out) > before:
                for x in out[before:]:
                    x["source"] = "git history"
        except (subprocess.SubprocessError, OSError) as e:
            out.append({"type": "history scan error", "severity": "info", "where": str(e),
                        "match_preview": "", "line": 0, "remediation": "", "source": "git history"})


def scan_site(base: str, timeout: int = 12, max_pages: int = 25) -> list[dict]:
    out: list[dict] = []
    try:
        import requests
    except ImportError:
        return out
    s = requests.Session()
    s.headers.update({"User-Agent": "SecSecretScan/1.0 (authorized self-scan)"})
    seen: set[str] = set()
    queue = [base]
    pages = 0
    while queue and pages < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        pages += 1
        try:
            r = s.get(url, timeout=timeout, allow_redirects=True)
        except Exception:
            continue
        if r is None or r.status_code >= 400:
            continue
        ctype = r.headers.get("Content-Type", "")
        text = r.text
        scan_text(text, f"{url} [{ctype}]", out, allow_noise=False)
        if "html" in ctype:
            for m in re.finditer(r'(?:src|href)\s*=\s*["\']([^"\']+\.js[^"\']*)', text, re.I):
                js = urljoin(url, m.group(1))
                if js not in seen:
                    queue.append(js)
            for m in re.finditer(r'(?:src|href)\s*=\s*["\']([^"\']+\.html?[^"\']*)', text, re.I):
                h = urljoin(url, m.group(1))
                if h not in seen and len(queue) + len(seen) < max_pages * 3:
                    queue.append(h)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="مسح الأسرار المسرّبة")
    ap.add_argument("--path", default=".", help="مسار المستودع")
    ap.add_argument("--url", help="فحص أسرار مسرّبة في الموقع المنشور")
    ap.add_argument("--no-history", action="store_true", help="تخطّي تاريخ git")
    ap.add_argument("--out", default="security/findings")
    args = ap.parse_args()

    findings: list[dict] = []
    if args.url:
        print(f"🔎 فحص الموقع {args.url} …")
        findings += scan_site(args.url if args.url.endswith("/") else args.url + "/")
    else:
        print(f"🔎 فحص المستودع {args.path} …")
        scan_repo(args.path, history=not args.no_history, out=findings)

    # تقرير
    by_type: dict[str, int] = {}
    for f in findings:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1

    print("\n=== النتيجة ===")
    if not findings:
        print("✅ لم يُعثر على أسرار مسرّبة.")
    else:
        for f in findings:
            print(f"  [{f['severity'].upper():8}] {f['type']} — {f['where']} (سطر {f['line']})")
        print("\n— الإصلاح المقترح —")
        for t in sorted(set(f["type"] for f in findings)):
            fix = next(f["remediation"] for f in findings if f["type"] == t)
            print(f"  • {t}: {fix}")

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = os.path.join(args.out, f"secrets_{stamp}")
        with open(stem + ".json", "w") as f:
            json.dump({"target": args.url or args.path, "count": len(findings),
                       "by_type": by_type, "findings": findings}, f, ensure_ascii=False, indent=2)
        print(f"\n📄 {stem}.json")


if __name__ == "__main__":
    main()
