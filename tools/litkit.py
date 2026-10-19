#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
litkit.py — مدير أدبيات خفيف لمشروع بحث الماجستير | Lightweight literature manager.

يعمل بمكتبات Python القياسية فقط (no third-party dependencies).
Stdlib-only — no pip install required.

أمثلة | Examples
---------------
    python tools/litkit.py init
    python tools/litkit.py add --title "..." --authors "Doe, Jane" --year 2026 \
        --venue "ACM TOIS" --doi 10.1145/xxxx --problem T1 --solution S1 --method experiment
    python tools/litkit.py search hallucination
    python tools/litkit.py stats
    python tools/litkit.py gaps
    python tools/litkit.py dedupe --apply
    python tools/litkit.py export-bib

كل الأوامر تقبل `--root PATH` لاستخدام مجلد آخر (مفيد للاختبارات).
All commands accept `--root PATH` (used by the test-suite).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence

# --------------------------------------------------------------------------- #
#  الثوابت | Constants
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parent.parent

FIELDS: Sequence[str] = (
    "id", "citekey", "title", "authors", "year", "venue", "type", "doi", "url",
    "problem_codes", "solution_codes", "method", "contribution", "venue_rank",
    "evidence_strength", "include", "status", "quality_score", "notes",
)

SCREENING_FIELDS: Sequence[str] = (
    "database", "identified", "duplicates", "screened",
    "excluded_title_abstract", "fulltext_assessed", "excluded_fulltext", "included",
)

VALID_TYPES = {"journal", "conference", "preprint", "book", "report", "standard"}
VALID_METHODS = {"slr", "survey_empirical", "case_study", "experiment",
                 "benchmark", "position", "design_science"}
VALID_CONTRIB = {"taxonomy", "framework", "empirical_evidence", "tool", "review"}
VALID_RANK = {"Q1", "Q2", "Q3", "Q4", "na"}
VALID_EVIDENCE = {"high", "medium", "low"}
VALID_INCLUDE = {"yes", "no"}
VALID_STATUS = {"to_read", "reading", "extracted", "cited", "excluded"}

# الأكواد الرسمية من literature/taxonomy.md
PROBLEM_CODES = {f"T{i}" for i in range(1, 13)} | {f"O{i}" for i in range(1, 11)}
SOLUTION_CODES = {f"S{i}" for i in range(1, 13)}

PROBLEM_LABELS = {
    "T1": "Hallucination / factual inaccuracy",
    "T2": "Bias & fairness",
    "T3": "Privacy & data leakage",
    "T4": "Security (injection, jailbreak, poisoning)",
    "T5": "Transparency & explainability",
    "T6": "Robustness & reliability",
    "T7": "Cost, compute & energy",
    "T8": "Data quality & governance",
    "T9": "Evaluation & benchmarking",
    "T10": "IP & copyright",
    "T11": "Accountability & auditability",
    "T12": "Agentic AI risks",
    "O1": "Adoption & readiness",
    "O2": "Governance & policy",
    "O3": "Trust & acceptance",
    "O4": "Skills & AI literacy",
    "O5": "ROI & value measurement",
    "O6": "Change management & job displacement",
    "O7": "Regulatory compliance",
    "O8": "Legacy systems integration",
    "O9": "Vendor lock-in",
    "O10": "Environmental sustainability",
}
SOLUTION_LABELS = {
    "S1": "Retrieval grounding / RAG",
    "S2": "Human-in-the-loop",
    "S3": "Fine-tuning & alignment",
    "S4": "Explainability tooling",
    "S5": "Privacy-preserving techniques",
    "S6": "Guardrails & red-teaming",
    "S7": "Governance frameworks",
    "S8": "Benchmarks & evaluation",
    "S9": "MLOps & monitoring",
    "S10": "Training & AI literacy",
    "S11": "Prompt engineering",
    "S12": "Agentic orchestration & verification",
}

STOPWORDS = {"with", "from", "that", "this", "into", "over", "under", "using",
             "based", "their", "your", "when", "what", "where", "which", "while"}

BIB_TEMPLATES = {
    "journal": "@article{{{key},\n  author    = {{{authors}}},\n  title     = {{{title}}},\n"
               "  journal   = {{{venue}}},\n  year      = {{{year}}},\n  doi       = {{{doi}}}\n}}\n",
    "conference": "@inproceedings{{{key},\n  author    = {{{authors}}},\n  title     = {{{title}}},\n"
                  "  booktitle = {{{venue}}},\n  year      = {{{year}}},\n  doi       = {{{doi}}}\n}}\n",
    "preprint": "@misc{{{key},\n  author       = {{{authors}}},\n  title        = {{{title}}},\n"
                "  year         = {{{year}}},\n  howpublished = {{{venue}}},\n  doi          = {{{doi}}}\n}}\n",
    "book": "@book{{{key},\n  author    = {{{authors}}},\n  title     = {{{title}}},\n"
            "  publisher = {{{venue}}},\n  year      = {{{year}}},\n  doi       = {{{doi}}}\n}}\n",
    "report": "@techreport{{{key},\n  author      = {{{authors}}},\n  title       = {{{title}}},\n"
              "  institution = {{{venue}}},\n  year        = {{{year}}},\n  doi         = {{{doi}}}\n}}\n",
    "standard": "@misc{{{key},\n  author       = {{{authors}}},\n  title        = {{{title}}},\n"
                "  year         = {{{year}}},\n  howpublished = {{{venue}}},\n  note         = {{Standard}}\n}}\n",
}


# --------------------------------------------------------------------------- #
#  مساعدات | Helpers
# --------------------------------------------------------------------------- #

def sources_path(root: Path) -> Path:
    return root / "literature" / "sources.csv"


def screening_path(root: Path) -> Path:
    return root / "literature" / "screening_log.csv"


def bib_path(root: Path) -> Path:
    return root / "references" / "references_auto.bib"


def read_csv(path: Path, fields: Sequence[str]) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for raw in reader:
            rows.append({f: (raw.get(f) or "").strip() for f in fields})
        return rows


def write_csv(path: Path, fields: Sequence[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields))
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in fields})


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.rstrip(".")


def make_citekey(authors: str, year: str, title: str) -> str:
    first = authors.split(";")[0].split(",")[0].strip() if authors else ""
    last = "".join(ch for ch in first.lower() if ch.isalnum()) or "anon"
    word = ""
    for token in re.sub(r"[^a-z0-9 ]", " ", title.lower()).split():
        if len(token) > 3 and token not in STOPWORDS:
            word = token
            break
    return f"{last}{year}{word}"


def split_codes(value: str) -> List[str]:
    if not value:
        return []
    return [c.strip().upper() for c in re.split(r"[,\s;]+", value) if c.strip()]


def next_id(rows: List[Dict[str, str]]) -> int:
    ids = [int(r["id"]) for r in rows if r.get("id", "").isdigit()]
    return (max(ids) + 1) if ids else 1


# --------------------------------------------------------------------------- #
#  الأوامر | Commands
# --------------------------------------------------------------------------- #

def cmd_init(args: argparse.Namespace) -> int:
    root: Path = args.root
    sp, sc = sources_path(root), screening_path(root)
    created = []

    if not sp.exists():
        write_csv(sp, FIELDS, [])
        created.append(str(sp.relative_to(root)))
    if not sc.exists():
        write_csv(sc, SCREENING_FIELDS, [])
        created.append(str(sc.relative_to(root)))
    (root / "literature" / "notes").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(parents=True, exist_ok=True)

    if created:
        print("✅ تم إنشاء | created: " + ", ".join(created))
    else:
        print("ℹ️  الملفات موجودة already present:", sp.name, "/", sc.name)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    root: Path = args.root
    path = sources_path(root)
    if not path.exists():
        print("❌ لم يتم تهيئة المشروع. شغّل: python tools/litkit.py init")
        return 1

    rows = read_csv(path, FIELDS)

    doi = normalize_doi(args.doi or "")
    title_key = normalize_title(args.title)

    for row in rows:
        if doi and normalize_doi(row.get("doi", "")) == doi:
            print(f"⚠️  مكرّر (duplicate DOI) — already present: id={row['id']} {row['citekey']}")
            return 2
        if title_key and normalize_title(row.get("title", "")) == title_key:
            print(f"⚠️  مكرّر (duplicate title) — already present: id={row['id']} {row['citekey']}")
            return 2

    key = make_citekey(args.authors or "", args.year or "", args.title)
    if any(r["citekey"] == key for r in rows):
        key = f"{key}b"

    row = {f: "" for f in FIELDS}
    row.update({
        "id": str(next_id(rows)),
        "citekey": key,
        "title": args.title.strip(),
        "authors": (args.authors or "").strip(),
        "year": (args.year or "").strip(),
        "venue": (args.venue or "").strip(),
        "type": (args.type or "journal").strip(),
        "doi": (args.doi or "").strip(),
        "url": (args.url or "").strip(),
        "problem_codes": (args.problem or "").strip().upper(),
        "solution_codes": (args.solution or "").strip().upper(),
        "method": (args.method or "").strip(),
        "contribution": (args.contribution or "").strip(),
        "venue_rank": (args.rank or "na").strip(),
        "evidence_strength": (args.evidence or "").strip(),
        "include": (args.include or "yes").strip(),
        "status": (args.status or "to_read").strip(),
        "quality_score": (args.quality or "").strip(),
        "notes": (args.notes or "").strip(),
    })
    rows.append(row)
    write_csv(path, FIELDS, rows)
    print(f"✅ أُضيف | added  id={row['id']}  citekey={key}  ({row['title'][:60]}...)")
    print(f"   إجمالي المصادر | total sources: {len(rows)}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows = read_csv(sources_path(root), FIELDS)
    query = args.query.lower()
    hits = [r for r in rows if any(query in (r[f] or "").lower() for f in FIELDS)]
    if not hits:
        print(f"🔍 لا نتائج لـ | no results for: {args.query}")
        return 0
    print(f"🔍 {len(hits)} نتيجة | result(s) for '{args.query}':\n")
    for r in hits:
        print(f"  [{r['id']:>3}] {r['citekey']:<28} {r['year']:<5} {r['problem_codes']:<10} {r['title'][:70]}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows = read_csv(sources_path(root), FIELDS)
    if not rows:
        print("لا توجد مصادر بعد — أضف بـ: python tools/litkit.py add ...")
        return 0

    def tally(extractor) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for r in rows:
            for value in extractor(r):
                if value:
                    counts[value] = counts.get(value, 0) + 1
        return counts

    print(f"📊 إجمالي المصادر | total sources: {len(rows)}\n")

    sections = [
        ("السنة | Year", tally(lambda r: [r["year"]])),
        ("النوع | Type", tally(lambda r: [r["type"]])),
        ("المنهجية | Method", tally(lambda r: [r["method"]])),
        ("تصنيف المنشور | Rank", tally(lambda r: [r["venue_rank"]])),
        ("مُدرَج؟ | Include", tally(lambda r: [r["include"]])),
        ("الحالة | Status", tally(lambda r: [r["status"]])),
        ("قوة الدليل | Evidence", tally(lambda r: [r["evidence_strength"]])),
    ]
    for label, counts in sections:
        print(f"— {label}")
        if not counts:
            print("   (فارغ | empty)")
        for key in sorted(counts, key=lambda k: (-counts[k], k)):
            print(f"   {key or '(blank)':<20} {counts[key]:>4}")
        print()

    print("— أكواد المشاكل | Problem codes")
    probs = tally(lambda r: split_codes(r["problem_codes"]))
    for code in sorted(probs, key=lambda c: (-probs[c], c)):
        label = PROBLEM_LABELS.get(code, "")
        print(f"   {code:<5} {probs[code]:>3}  {label}")
    print()
    print("— أكواد الحلول | Solution codes")
    sols = tally(lambda r: split_codes(r["solution_codes"]))
    for code in sorted(sols, key=lambda c: (-sols[c], c)):
        label = SOLUTION_LABELS.get(code, "")
        print(f"   {code:<5} {sols[code]:>3}  {label}")
    return 0


def cmd_gaps(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows = read_csv(sources_path(root), FIELDS)
    included = [r for r in rows if r.get("include", "").lower() == "yes"]
    if not included:
        print("لا توجد مصادر مُدرَجة (include=yes) بعد.")
        return 0

    prob_counts: Dict[str, int] = {}
    prob_solutions: Dict[str, set] = {}
    sol_counts: Dict[str, int] = {}
    for r in included:
        codes = [c for c in split_codes(r["problem_codes"]) if c != "NA"]
        sols = [c for c in split_codes(r["solution_codes"]) if c != "NA"]
        for c in codes:
            prob_counts[c] = prob_counts.get(c, 0) + 1
            prob_solutions.setdefault(c, set()).update(sols)
        for s in sols:
            sol_counts[s] = sol_counts.get(s, 0) + 1

    print(f"🔎 تحليل الفجوات على {len(included)} مصدراً مُدرَجاً | gap analysis over {len(included)} included sources\n")
    print("المشاكل الأقل تغطيةً (مرشحة لتكون فجوة بحثية) | Least-covered problems (gap candidates):")
    print("-" * 78)
    ordered = sorted(PROBLEM_CODES, key=lambda c: (prob_counts.get(c, 0), c))
    for code in ordered:
        n = prob_counts.get(code, 0)
        sols = prob_solutions.get(code, set())
        bar = "█" * min(n, 30)
        flag = "  ⚠️ GAP" if n <= 1 else ""
        print(f"  {code:<4} n={n:<4} {bar:<30} {PROBLEM_LABELS.get(code, '')[:34]}  {flag}")
    print()
    print("الحلول الأقل استخداماً | Least-used solution families:")
    print("-" * 78)
    for code in sorted(SOLUTION_CODES, key=lambda c: (sol_counts.get(c, 0), c)):
        n = sol_counts.get(code, 0)
        print(f"  {code:<4} n={n:<4} {SOLUTION_LABELS.get(code, '')}")
    print()
    uncovered = [c for c in sorted(PROBLEM_CODES) if prob_counts.get(c, 0) == 0]
    if uncovered:
        print("🚩 مشاكل بلا أي مصدر | problems with zero coverage: " + ", ".join(uncovered))
    print("\n💡 نصيحة: أي مشكلة بـ n<=1 أو حل بلا تقييم = فجوة قابلة للنشر (بعد التحقق اليدوي).")
    return 0


def cmd_dedupe(args: argparse.Namespace) -> int:
    root: Path = args.root
    path = sources_path(root)
    rows = read_csv(path, FIELDS)
    seen_doi: Dict[str, Dict[str, str]] = {}
    seen_title: Dict[str, Dict[str, str]] = {}
    duplicates: List[Dict[str, str]] = []

    for r in rows:
        doi = normalize_doi(r.get("doi", ""))
        tkey = normalize_title(r.get("title", ""))
        if doi and doi in seen_doi:
            duplicates.append(r)
        elif tkey and tkey in seen_title:
            duplicates.append(r)
        else:
            if doi:
                seen_doi[doi] = r
            if tkey:
                seen_title[tkey] = r

    if not duplicates:
        print("✅ لا توجد مصادر مكرّرة | no duplicates found")
        return 0

    print(f"⚠️  وجدت {len(duplicates)} مصدراً مكرراً | found {len(duplicates)} duplicate(s):")
    for r in duplicates:
        print(f"   id={r['id']} {r['citekey']} :: {r['title'][:60]}")

    if args.apply:
        dup_ids = {r["id"] for r in duplicates}
        kept = [r for r in rows if r["id"] not in dup_ids]
        write_csv(path, FIELDS, kept)
        print(f"🧹 حُذفت | removed {len(dup_ids)};   المتبقي | remaining: {len(kept)}")
    else:
        print("   (شغّل بـ --apply للحذف | run with --apply to remove)")
    return 0


def cmd_export_bib(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows = read_csv(sources_path(root), FIELDS)
    selected = [r for r in rows if r.get("include", "").lower() == "yes"]
    out = Path(args.out) if args.out else bib_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)

    chunks = [
        "% Auto-generated by tools/litkit.py — لا تعدّله يدوياً | do not edit by hand.\n"
        "% Source of truth: literature/sources.csv\n\n"
    ]
    for r in selected:
        etype = r["type"] if r["type"] in BIB_TEMPLATES else "misc"
        authors = " and ".join(a.strip() for a in r["authors"].split(";") if a.strip())
        chunk = BIB_TEMPLATES[etype].format(
            key=r["citekey"], authors=authors, title=r["title"],
            venue=r["venue"], year=r["year"], doi=r["doi"] or r["url"],
        )
        chunks.append(chunk)

    out.write_text("\n".join(chunks), encoding="utf-8")
    print(f"📚 صُدّر {len(selected)} مدخلاً إلى | exported {len(selected)} entries to: {out}")
    return 0


# --------------------------------------------------------------------------- #
#  الواجهة | CLI
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="litkit",
        description="مدير أدبيات لمشروع بحث الذكاء الاصطناعي | literature manager for the AI research project",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT,
                        help="مجلد المستودع (للاختبارات) | repository root (for tests)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="تهيئة ملفات CSV | create CSV files").set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="إضافة مصدر | add a source")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--authors", default="")
    p_add.add_argument("--year", default="")
    p_add.add_argument("--venue", default="")
    p_add.add_argument("--type", default="journal", choices=sorted(VALID_TYPES))
    p_add.add_argument("--doi", default="")
    p_add.add_argument("--url", default="")
    p_add.add_argument("--problem", default="", help="أكواد المشاكل مثل: T1,O3")
    p_add.add_argument("--solution", default="", help="أكواد الحلول مثل: S1,S8")
    p_add.add_argument("--method", default="", choices=sorted(VALID_METHODS))
    p_add.add_argument("--contribution", default="", choices=sorted(VALID_CONTRIB))
    p_add.add_argument("--rank", default="na", choices=sorted(VALID_RANK))
    p_add.add_argument("--evidence", default="", choices=sorted(VALID_EVIDENCE))
    p_add.add_argument("--include", default="yes", choices=sorted(VALID_INCLUDE))
    p_add.add_argument("--status", default="to_read", choices=sorted(VALID_STATUS))
    p_add.add_argument("--quality", default="")
    p_add.add_argument("--notes", default="")
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="بحث نصي | full-text search")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    sub.add_parser("stats", help="إحصاءات | statistics").set_defaults(func=cmd_stats)
    sub.add_parser("gaps", help="تحليل الفجوات | gap analysis").set_defaults(func=cmd_gaps)

    p_dedupe = sub.add_parser("dedupe", help="كشف التكرار | find duplicates")
    p_dedupe.add_argument("--apply", action="store_true")
    p_dedupe.set_defaults(func=cmd_dedupe)

    p_bib = sub.add_parser("export-bib", help="تصدير BibTeX | export BibTeX")
    p_bib.add_argument("--out", default=None)
    p_bib.set_defaults(func=cmd_export_bib)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.root = Path(args.root)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
