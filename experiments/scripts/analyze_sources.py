#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_sources.py — تحليل وصفي لجدول المصادر | Descriptive analysis of the source table.

يعمل بدون أي مكتبة خارجية؛ ويرسم الرسوم إن كانت matplotlib متاحة.
Stdlib-only; draws charts if matplotlib is installed.

    python experiments/scripts/analyze_sources.py \
        --sources literature/sources.csv --outdir experiments/results
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


def split_codes(value: str) -> List[str]:
    return [c.strip().upper() for c in re.split(r"[,\s;]+", value or "") if c.strip() and c.strip().upper() != "NA"]


def write_csv(path: Path, header: List[str], rows: List[List[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Descriptive analysis of literature/sources.csv")
    ap.add_argument("--sources", type=Path, default=REPO_ROOT / "literature" / "sources.csv")
    ap.add_argument("--outdir", type=Path, default=REPO_ROOT / "experiments" / "results")
    args = ap.parse_args(argv)

    if not args.sources.exists():
        print(f"❌ الملف غير موجود | not found: {args.sources}")
        return 1

    rows = load(args.sources)
    included = [r for r in rows if r.get("include", "").lower() == "yes"]
    print(f"📄 المصادر: {len(rows)} | المُدرجة: {len(included)}")

    outdir: Path = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    # 1) التوزيع الزمني
    years = Counter(r["year"] for r in included if r["year"])
    write_csv(outdir / "table_year_distribution.csv", ["year", "count"],
              [[y, str(c)] for y, c in sorted(years.items())])

    # 2) نوع المنشور
    types = Counter(r["type"] for r in included if r["type"])
    write_csv(outdir / "table_type_distribution.csv", ["type", "count"],
              [[t, str(c)] for t, c in sorted(types.items(), key=lambda x: -x[1])])

    # 3) أكواد المشاكل والحلول
    problems = Counter()
    solutions = Counter()
    matrix: Dict[str, Counter] = defaultdict(Counter)
    for r in included:
        pcodes = split_codes(r.get("problem_codes", ""))
        scodes = split_codes(r.get("solution_codes", ""))
        problems.update(pcodes)
        solutions.update(scodes)
        for p in pcodes:
            matrix[p].update(scodes)

    write_csv(outdir / "table_problem_coverage.csv", ["problem_code", "n_sources"],
              [[p, str(c)] for p, c in sorted(problems.items(), key=lambda x: (-x[1], x[0]))])
    write_csv(outdir / "table_solution_coverage.csv", ["solution_code", "n_sources"],
              [[s, str(c)] for s, c in sorted(solutions.items(), key=lambda x: (-x[1], x[0]))])

    all_solutions = sorted(solutions)
    header = ["problem_code"] + all_solutions + ["total"]
    body = []
    for p in sorted(problems):
        counts = [str(matrix[p].get(s, 0)) for s in all_solutions]
        body.append([p] + counts + [str(problems[p])])
    write_csv(outdir / "table_problem_solution_matrix.csv", header, body)

    # 4) تقرير نصي
    report = outdir / "analysis_report.txt"
    report.write_text(
        "Analysis of literature/sources.csv\n"
        f"sources: {len(rows)} | included: {len(included)}\n\n"
        "Year distribution:\n" + "\n".join(f"  {y}: {c}" for y, c in sorted(years.items())) + "\n\n"
        "Type distribution:\n" + "\n".join(f"  {t}: {c}" for t, c in types.most_common()) + "\n\n"
        "Problem coverage:\n" + "\n".join(f"  {p}: {c}" for p, c in problems.most_common()) + "\n\n"
        "Solution coverage:\n" + "\n".join(f"  {s}: {c}" for s, c in solutions.most_common()) + "\n",
        encoding="utf-8")

    print(f"✅ كُتبت النتائج إلى | wrote results to: {outdir}")
    for name in ("table_year_distribution.csv", "table_type_distribution.csv",
                 "table_problem_coverage.csv", "table_solution_coverage.csv",
                 "table_problem_solution_matrix.csv", "analysis_report.txt"):
        print(f"   • {name}")

    # 5) رسوم اختيارية
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("ℹ️  matplotlib غير مثبتة — تخطّي الرسوم | not installed, skipping figures")
        return 0

    figdir = outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    if years:
        fig, ax = plt.subplots(figsize=(6, 3.4), dpi=300)
        ax.bar(list(years.keys()), list(years.values()), color="#2b6cb0")
        ax.set_ylabel("Included sources")
        ax.set_title("Distribution of included sources by year")
        fig.tight_layout(); fig.savefig(figdir / "fig1_year_distribution.png"); plt.close(fig)

    if problems:
        top = problems.most_common(12)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
        ax.barh([p for p, _ in top][::-1], [c for _, c in top][::-1], color="#2f855a")
        ax.set_xlabel("Sources"); ax.set_title("Most frequently coded problems")
        fig.tight_layout(); fig.savefig(figdir / "fig2_problem_frequency.png"); plt.close(fig)

    print(f"   • figures/fig1_year_distribution.png, figures/fig2_problem_frequency.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
