# -*- coding: utf-8 -*-
"""
اختبارات أدوات المستودع | Tests for the research tooling.

تشغيل | Run:
    python -m pytest tests/ -q
أو بدون pytest | or without pytest:
    python tests/test_tools.py
"""
from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import litkit  # noqa: E402
import prisma  # noqa: E402
import validate_sources  # noqa: E402


# --------------------------------------------------------------------------- #
#  مساعدات | Helpers
# --------------------------------------------------------------------------- #

def make_repo(tmp: Path) -> Path:
    """ينشئ هيكل مستودع مصغّر داخل مجلد مؤقت | build a mini repo in a temp dir."""
    (tmp / "literature" / "notes").mkdir(parents=True, exist_ok=True)
    (tmp / "references").mkdir(parents=True, exist_ok=True)
    return tmp


def run(args, root: Path):
    return subprocess.run(
        [sys.executable, str(TOOLS / "litkit.py"), "--root", str(root), *args],
        capture_output=True, text=True,
    )


# --------------------------------------------------------------------------- #
#  اختبارات litkit
# --------------------------------------------------------------------------- #

def test_init_creates_csv_files_with_headers():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        assert litkit.main(["--root", str(root), "init"]) == 0
        src = root / "literature" / "sources.csv"
        scr = root / "literature" / "screening_log.csv"
        assert src.exists() and scr.exists()
        with src.open(encoding="utf-8") as fh:
            assert list(csv.DictReader(fh).fieldnames) == list(litkit.FIELDS)
        with scr.open(encoding="utf-8") as fh:
            assert list(csv.DictReader(fh).fieldnames) == list(litkit.SCREENING_FIELDS)


def test_add_then_duplicate_detection_by_doi():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        base = ["add", "--title", "Hallucination in Enterprise RAG Systems",
                "--authors", "Doe, Jane", "--year", "2026", "--venue", "ACM TOIS",
                "--doi", "10.1145/1234567", "--problem", "T1", "--solution", "S1",
                "--method", "experiment"]
        assert litkit.main(["--root", str(root), *base]) == 0
        res = run(base, root)  # نفس الـDOI مرة ثانية
        assert res.returncode == 2
        assert "duplicate" in res.stdout.lower() or "مكر" in res.stdout


def test_add_detects_duplicate_by_title_even_with_new_doi():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        litkit.main(["--root", str(root), "add", "--title", "AI Governance in Banks",
                     "--authors", "Smith, Ali", "--year", "2025", "--venue", "IJIM",
                     "--doi", "10.1/a", "--problem", "O2", "--solution", "S7", "--method", "slr"])
        res = run(["add", "--title", "AI Governance in Banks", "--authors", "Smith, Ali",
                   "--year", "2025", "--venue", "IJIM", "--doi", "10.1/b",
                   "--problem", "O2", "--solution", "S7", "--method", "slr"], root)
        assert res.returncode == 2


def test_citekey_generation():
    key = litkit.make_citekey("Huang, Lei; Yu, Weijiang", "2025",
                              "A Survey on Hallucination in Large Language Models")
    assert key == "huang2025survey", key


def test_stats_and_gaps_run_on_seeded_data():
    """يتأكد أن أوامر العرض تعمل على بيانات المستودع الفعلية."""
    assert litkit.main(["--root", str(ROOT), "stats"]) == 0
    assert litkit.main(["--root", str(ROOT), "gaps"]) == 0


def test_gaps_flags_uncovered_problem_codes():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        litkit.main(["--root", str(root), "add", "--title", "Prompt injection defenses",
                     "--authors", "A, B", "--year", "2026", "--venue", "IEEE",
                     "--doi", "10.1/c", "--problem", "T4", "--solution", "S6", "--method", "benchmark"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            litkit.main(["--root", str(root), "gaps"])
        out = buf.getvalue()
        assert "T4" in out
        assert "zero coverage" in out          # بقية الأكواد بلا تغطية
        assert "T10" in out                    # مثال على كود غير مغطّى


def test_search_finds_row():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        litkit.main(["--root", str(root), "add", "--title", "Energy cost of LLM inference",
                     "--authors", "B, C", "--year", "2026", "--venue", "Elsevier",
                     "--doi", "10.1/d", "--problem", "T7", "--solution", "S9", "--method", "experiment"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            litkit.main(["--root", str(root), "search", "energy"])
        assert "Energy cost" in buf.getvalue()


def test_dedupe_apply_removes_duplicates():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        path = root / "literature" / "sources.csv"
        rows = litkit.read_csv(path, litkit.FIELDS)
        row = {f: "" for f in litkit.FIELDS}
        row.update({"id": "1", "citekey": "a2025test", "title": "Same Paper", "year": "2025",
                    "venue": "V", "type": "journal", "doi": "10.1/dup", "include": "yes"})
        rows.append(row)
        dup = dict(row); dup["id"] = "2"; dup["citekey"] = "a2025testb"
        rows.append(dup)
        litkit.write_csv(path, litkit.FIELDS, rows)
        assert litkit.main(["--root", str(root), "dedupe", "--apply"]) == 0
        assert len(litkit.read_csv(path, litkit.FIELDS)) == 1


def test_export_bib_writes_entries_for_included_rows():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        litkit.main(["--root", str(root), "init"])
        litkit.main(["--root", str(root), "add", "--title", "RAG for Enterprise QA",
                     "--authors", "Doe, Jane; Roe, Ann", "--year", "2026",
                     "--venue", "Journal of Things", "--doi", "10.1/e",
                     "--problem", "T1", "--solution", "S1", "--method", "case_study"])
        litkit.main(["--root", str(root), "add", "--title", "Excluded paper",
                     "--authors", "X, Y", "--year", "2026", "--venue", "V",
                     "--doi", "10.1/f", "--problem", "T2", "--solution", "S4",
                     "--method", "position", "--include", "no"])
        litkit.main(["--root", str(root), "export-bib"])
        bib = (root / "references" / "references_auto.bib").read_text(encoding="utf-8")
        assert "@article{doe2026enterprise" in bib
        assert "Doe, Jane and Roe, Ann" in bib
        assert "Excluded paper" not in bib


# --------------------------------------------------------------------------- #
#  اختبارات prisma
# --------------------------------------------------------------------------- #

def test_prisma_totals_and_consistency():
    rows = [
        {"database": "Scopus", "identified": 100, "duplicates": 20, "screened": 80,
         "excluded_title_abstract": 50, "fulltext_assessed": 30, "excluded_fulltext": 18, "included": 12},
        {"database": "IEEE", "identified": 60, "duplicates": 10, "screened": 50,
         "excluded_title_abstract": 35, "fulltext_assessed": 15, "excluded_fulltext": 7, "included": 8},
    ]
    t = prisma.totals(rows)
    assert t["identified"] == 160
    assert t["duplicates"] == 30
    assert t["screened"] == 130
    assert t["included"] == 20
    assert prisma.check_consistency(t) == []


def test_prisma_detects_inconsistent_numbers():
    # خطأان مقصودان: 100-10 != 95 (التحديد/الفرز) و 55-15 != 35 (الأهلية/الإدراج)
    t = {"identified": 100, "duplicates": 10, "screened": 95,
         "excluded_title_abstract": 40, "fulltext_assessed": 55,
         "excluded_fulltext": 15, "included": 35}
    issues = prisma.check_consistency(t)
    assert len(issues) == 2, issues


def test_prisma_runs_on_repo_screening_log():
    assert prisma.main(["--root", str(ROOT)]) in (0, 1)  # 1 = عدم اتساق الأرقام التجريبية


def test_prisma_csv_output():
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        prisma.main(["--root", str(ROOT), "--csv"])
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("identified")


# --------------------------------------------------------------------------- #
#  اختبارات validate_sources
# --------------------------------------------------------------------------- #

def _write_sources(tmp: Path, rows):
    path = tmp / "literature" / "sources.csv"
    litkit.write_csv(path, validate_sources.FIELDS, rows)
    return path


def _blank_row(**kw):
    row = {f: "" for f in validate_sources.FIELDS}
    row.update({"type": "journal", "include": "yes", "venue_rank": "na"})
    row.update(kw)
    return row


def test_validate_accepts_clean_table():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        path = _write_sources(root, [_blank_row(
            id="1", citekey="doe2026rag", title="RAG in Practice", authors="Doe, Jane",
            year="2026", venue="J", doi="10.1000/xyz123", problem_codes="T1",
            solution_codes="S1", method="experiment", contribution="tool",
            evidence_strength="high", status="extracted")])
        errors, warnings, n = validate_sources.validate(path)
        assert errors == [], errors
        assert n == 1


def test_validate_flags_missing_required_fields():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        path = _write_sources(root, [_blank_row(id="1", citekey="x", title="No authors",
                                                year="2026", venue="J")])
        errors, _, _ = validate_sources.validate(path)
        assert any("authors" in e for e in errors)


def test_validate_flags_bad_doi_and_unknown_codes():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        path = _write_sources(root, [_blank_row(
            id="1", citekey="x2026bad", title="Bad codes", authors="A, B", year="2026",
            venue="J", doi="not-a-doi", problem_codes="T99", solution_codes="S77",
            method="experiment")])
        errors, _, _ = validate_sources.validate(path)
        assert any("DOI" in e for e in errors)
        assert any("T99" in e for e in errors)
        assert any("S77" in e for e in errors)


def test_validate_flags_duplicate_citekey_and_year_range():
    with tempfile.TemporaryDirectory() as td:
        root = make_repo(Path(td))
        path = _write_sources(root, [
            _blank_row(id="1", citekey="dup2026x", title="One", authors="A, B",
                       year="1899", venue="J", doi="10.1/a", problem_codes="T1",
                       solution_codes="S1", method="slr"),
            _blank_row(id="2", citekey="dup2026x", title="Two", authors="C, D",
                       year="2026", venue="J", doi="10.1/b", problem_codes="T1",
                       solution_codes="S1", method="slr"),
        ])
        errors, _, _ = validate_sources.validate(path)
        assert any("citekey" in e and "مكر" in e or "duplicate citekey" in e for e in errors)
        assert any("1899" in e for e in errors)


def test_validate_repo_sources_csv_has_no_errors():
    """جدول المستودع الفعلي يجب أن يمرّ بلا أخطاء (التحذيرات مسموحة)."""
    errors, warnings, n = validate_sources.validate(ROOT / "literature" / "sources.csv")
    assert errors == [], errors
    assert n >= 5


# --------------------------------------------------------------------------- #

if __name__ == "__main__":  # تشغيل بدون pytest
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{'✅ all tests passed' if not failures else f'❌ {failures} failing'}")
    sys.exit(1 if failures else 0)
