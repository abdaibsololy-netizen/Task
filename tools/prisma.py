#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prisma.py — مخطط تدفق PRISMA 2020 من سجل الفرز | PRISMA 2020 flow from the screening log.

يقرأ literature/screening_log.csv ويطبع ملخّصاً جاهزاً للصقِه في المخطوطة،
مع فحص اتساق الأرقام (consistency check) — لأن المحكمين يتحققون من الأرقام.

    python tools/prisma.py
    python tools/prisma.py --csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent

FIELDS = ("database", "identified", "duplicates", "screened",
          "excluded_title_abstract", "fulltext_assessed", "excluded_fulltext", "included")

INT_FIELDS = FIELDS[1:]


def load(path: Path) -> List[Dict[str, int]]:
    rows: List[Dict[str, int]] = []
    if not path.exists():
        return rows
    with path.open("r", newline="", encoding="utf-8") as fh:
        for raw in csv.DictReader(fh):
            row: Dict[str, int] = {"database": (raw.get("database") or "").strip(),
                                   "notes": (raw.get("notes") or "").strip()}
            for f in INT_FIELDS:
                value = (raw.get(f) or "0").strip()
                try:
                    row[f] = int(value)
                except ValueError:
                    row[f] = 0
            rows.append(row)
    return rows


def totals(rows: List[Dict[str, int]]) -> Dict[str, int]:
    out = {f: sum(r[f] for r in rows) for f in INT_FIELDS}
    out["total_databases"] = len(rows)
    return out


def check_consistency(t: Dict[str, int]) -> List[str]:
    issues: List[str] = []
    identified, dup, screened = t["identified"], t["duplicates"], t["screened"]
    excl_ta, ft, excl_ft, included = (t["excluded_title_abstract"], t["fulltext_assessed"],
                                      t["excluded_fulltext"], t["included"])

    if identified - dup != screened:
        issues.append(f"identified - duplicates ({identified}-{dup}={identified - dup}) "
                      f"لا يساوي screened ({screened})")
    if screened - excl_ta != ft:
        issues.append(f"screened - excluded_title_abstract ({screened}-{excl_ta}={screened - excl_ta}) "
                      f"لا يساوي fulltext_assessed ({ft})")
    if ft - excl_ft != included:
        issues.append(f"fulltext_assessed - excluded_fulltext ({ft}-{excl_ft}={ft - excl_ft}) "
                      f"لا يساوي included ({included})")
    return issues


def render(t: Dict[str, int]) -> str:
    return f"""
╔══════════════════════════════════════════════════════════════════════╗
║  PRISMA 2020 — مخطط التدفق | Flow diagram                             ║
╚══════════════════════════════════════════════════════════════════════╝

IDENTIFICATION · التحديد
   Records identified from databases          : {t['identified']:>6}   ({t['total_databases']} databases)
   Records removed before screening
     - duplicates removed                     : {t['duplicates']:>6}
     - records marked ineligible/automation   : {0:>6}

SCREENING · الفرز
   Records screened (title + abstract)        : {t['screened']:>6}
   Records excluded                           : {t['excluded_title_abstract']:>6}

ELIGIBILITY · الأهلية
   Full-text records assessed                 : {t['fulltext_assessed']:>6}
   Full-text records excluded (with reasons)  : {t['excluded_fulltext']:>6}

INCLUDED · المُدرجة
   Studies included in the review             : {t['included']:>6}
   ─────────────────────────────────────────────────────────────────
   Retention rate (included / identified)     : {(t['included'] / t['identified'] * 100 if t['identified'] else 0):>5.1f}%
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="PRISMA 2020 flow summary")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--csv", action="store_true", help="اطبع الأرقام كصف CSV | print numbers as CSV")
    args = parser.parse_args(argv)

    path = args.root / "literature" / "screening_log.csv"
    rows = load(path)
    if not rows:
        print(f"❌ لا توجد بيانات في | no data in {path}")
        print("   املأ الملف من | fill it from literature/search_strings.md")
        return 1

    t = totals(rows)

    if args.csv:
        print(",".join(INT_FIELDS))
        print(",".join(str(t[f]) for f in INT_FIELDS))
        return 0

    print(render(t))

    if any("EXAMPLE" in r.get("notes", "").upper() for r in rows):
        print("=" * 74)
        print("⚠️  تحذير أمانة علمية | RESEARCH-INTEGRITY WARNING")
        print("   هذه أرقام توضيحية مبدئية (placeholder) وليست نتائج بحث حقيقية.")
        print("   استبدلها بأرقامك الفعلية قبل تضمينها في أي مخطوطة.")
        print("   These are placeholder numbers — replace them with your real")
        print("   counts before using them in a manuscript.")
        print("=" * 74)
        print()

    print("تفصيل حسب قاعدة البيانات | Per database:")
    print(f"   {'database':<22}{'ident':>7}{'dup':>7}{'scr':>7}{'exclTA':>8}{'FT':>6}{'exclFT':>8}{'incl':>6}")
    for r in rows:
        print(f"   {r['database'][:20]:<22}{r['identified']:>7}{r['duplicates']:>7}"
              f"{r['screened']:>7}{r['excluded_title_abstract']:>8}{r['fulltext_assessed']:>6}"
              f"{r['excluded_fulltext']:>8}{r['included']:>6}")
    print()

    issues = check_consistency(t)
    if issues:
        print("⚠️  فحص الاتساق | consistency check — راجع الأرقام قبل النشر:")
        for i in issues:
            print(f"   • {i}")
        return 1
    print("✅ الأرقام متسقة | numbers are consistent — جاهزة لجدول PRISMA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
