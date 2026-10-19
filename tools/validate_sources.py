#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_sources.py — فحص جودة جدول المصادر | QA checks for literature/sources.csv

يفحص: العناوين، الحقول الإلزامية، صحة السنة، صيغة DOI، تكرار المفاتيح،
وصحة أكواد التصنيف (T#/O#/S# من literature/taxonomy.md).

    python tools/validate_sources.py            # خروج 1 إن وُجد خطأ | exit 1 on errors
    python tools/validate_sources.py --strict   # اعتبر التحذيرات أخطاء | warnings = errors
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

FIELDS = ("id", "citekey", "title", "authors", "year", "venue", "type", "doi", "url",
          "problem_codes", "solution_codes", "method", "contribution", "venue_rank",
          "evidence_strength", "include", "status", "quality_score", "notes")

REQUIRED = ("title", "authors", "year", "venue", "type")
VALID_TYPES = {"journal", "conference", "preprint", "book", "report", "standard"}
VALID_METHODS = {"slr", "survey_empirical", "case_study", "experiment",
                 "benchmark", "position", "design_science"}
VALID_CONTRIB = {"taxonomy", "framework", "empirical_evidence", "tool", "review"}
VALID_RANK = {"Q1", "Q2", "Q3", "Q4", "na"}
VALID_EVIDENCE = {"high", "medium", "low"}
VALID_INCLUDE = {"yes", "no"}
VALID_STATUS = {"to_read", "reading", "extracted", "cited", "excluded"}
PROBLEM_CODES = {f"T{i}" for i in range(1, 13)} | {f"O{i}" for i in range(1, 11)}
SOLUTION_CODES = {f"S{i}" for i in range(1, 13)}

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
CITEKEY_RE = re.compile(r"^[a-z0-9]+$")


def split_codes(value: str) -> List[str]:
    return [c.strip().upper() for c in re.split(r"[,\s;]+", value or "") if c.strip()]


def validate(path: Path) -> Tuple[List[str], List[str], int]:
    errors: List[str] = []
    warnings: List[str] = []

    if not path.exists():
        return [f"الملف غير موجود | file not found: {path}"], warnings, 0

    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = [h.strip() for h in (reader.fieldnames or [])]
        rows = [{f: (r.get(f) or "").strip() for f in FIELDS} for r in reader]

    if header != list(FIELDS):
        errors.append("ترويسة الأعمدة غير مطابقة للمخطط | header mismatch.\n"
                      f"   المتوقع | expected: {list(FIELDS)}\n"
                      f"   الموجود | found   : {header}")

    if not rows:
        warnings.append("الجدول فارغ | table is empty")
        return errors, warnings, 0

    seen_ids: Dict[str, int] = {}
    seen_keys: Dict[str, int] = {}
    seen_dois: Dict[str, int] = {}
    seen_titles: Dict[str, int] = {}

    for idx, row in enumerate(rows, start=2):  # start=2 -> رقم السطر في الملف
        where = f"row {idx} ({row.get('citekey') or row.get('title', '')[:30]})"

        for field in REQUIRED:
            if not row.get(field):
                errors.append(f"{where}: الحقل الإلزامي فارغ | missing required field: '{field}'")

        year = row.get("year", "")
        if year:
            if not year.isdigit():
                errors.append(f"{where}: السنة ليست رقماً | year is not numeric: '{year}'")
            elif not (1990 <= int(year) <= 2035):
                errors.append(f"{where}: سنة خارج النطاق | year out of range: {year}")

        if row.get("type") and row["type"] not in VALID_TYPES:
            errors.append(f"{where}: نوع غير صالح | invalid type: '{row['type']}'")
        if row.get("method") and row["method"] not in VALID_METHODS:
            errors.append(f"{where}: منهجية غير صالحة | invalid method: '{row['method']}'")
        if row.get("contribution") and row["contribution"] not in VALID_CONTRIB:
            errors.append(f"{where}: مساهمة غير صالحة | invalid contribution: '{row['contribution']}'")
        if row.get("venue_rank") and row["venue_rank"] not in VALID_RANK:
            errors.append(f"{where}: تصنيف غير صالح | invalid venue_rank: '{row['venue_rank']}'")
        if row.get("evidence_strength") and row["evidence_strength"] not in VALID_EVIDENCE:
            errors.append(f"{where}: قوة الدليل غير صالحة | invalid evidence_strength: '{row['evidence_strength']}'")
        if row.get("include") and row["include"] not in VALID_INCLUDE:
            errors.append(f"{where}: قيمة include غير صالحة | invalid include: '{row['include']}'")
        if row.get("status") and row["status"] not in VALID_STATUS:
            errors.append(f"{where}: حالة غير صالحة | invalid status: '{row['status']}'")

        doi = row.get("doi", "")
        if doi:
            if not DOI_RE.match(doi):
                errors.append(f"{where}: صيغة DOI غير صحيحة | bad DOI format: '{doi}'")
            key = doi.lower().rstrip(".")
            if key in seen_dois:
                errors.append(f"{where}: DOI مكرّر | duplicate DOI with row {seen_dois[key]}")
            else:
                seen_dois[key] = idx
        else:
            warnings.append(f"{where}: لا يوجد DOI | no DOI")

        citekey = row.get("citekey", "")
        if citekey:
            if not CITEKEY_RE.match(citekey):
                warnings.append(f"{where}: citekey يُفضَّل أن يكون ascii صغير | prefer lowercase ascii: '{citekey}'")
            if citekey in seen_keys:
                errors.append(f"{where}: citekey مكرّر | duplicate citekey with row {seen_keys[citekey]}")
            else:
                seen_keys[citekey] = idx

        rid = row.get("id", "")
        if rid:
            if rid in seen_ids:
                errors.append(f"{where}: id مكرّر | duplicate id with row {seen_ids[rid]}")
            else:
                seen_ids[rid] = idx

        title_key = re.sub(r"[^a-z0-9]+", " ", row.get("title", "").lower()).strip()
        if title_key:
            if title_key in seen_titles:
                errors.append(f"{where}: عنوان مكرّر | duplicate title with row {seen_titles[title_key]}")
            else:
                seen_titles[title_key] = idx

        for code in split_codes(row.get("problem_codes", "")):
            if code != "NA" and code not in PROBLEM_CODES:
                errors.append(f"{where}: كود مشكلة غير معروف | unknown problem code: '{code}'")
        for code in split_codes(row.get("solution_codes", "")):
            if code != "NA" and code not in SOLUTION_CODES:
                errors.append(f"{where}: كود حل غير معروف | unknown solution code: '{code}'")

        if not split_codes(row.get("problem_codes", "")):
            warnings.append(f"{where}: بلا أكواد مشاكل | no problem codes")
        if not split_codes(row.get("solution_codes", "")):
            warnings.append(f"{where}: بلا أكواد حلول | no solution codes")
        if not row.get("method"):
            warnings.append(f"{where}: المنهجية غير محددة | method not set")

    return errors, warnings, len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate literature/sources.csv")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--strict", action="store_true", help="التحذيرات تُعامل كأخطاء | treat warnings as errors")
    args = parser.parse_args(argv)

    path = args.root / "literature" / "sources.csv"
    errors, warnings, n = validate(path)

    print(f"🔍 فحص | validating {path}  ({n} صفاً | rows)")

    for w in warnings:
        print(f"   ⚠️  {w}")
    for e in errors:
        print(f"   ❌ {e}")

    if not errors and not warnings:
        print("✅ لا أخطاء ولا تحذيرات | clean")
        return 0
    if errors:
        print(f"\n❌ {len(errors)} خطأً | error(s);  {len(warnings)} تحذيراً | warning(s)")
        return 1
    print(f"\n⚠️  لا أخطاء، لكن {len(warnings)} تحذيراً | no errors, {len(warnings)} warning(s)")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
