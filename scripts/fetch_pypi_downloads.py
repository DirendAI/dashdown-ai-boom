#!/usr/bin/env python3
"""Build data/pypi_downloads.parquet from the git history of
https://github.com/hugovk/top-pypi-packages.

That repository publishes, roughly monthly since 2019, a snapshot of the
top PyPI packages by download count over the trailing 30 days. The numbers
come from the public PyPI download stats (BigQuery
`bigquery-public-data.pypi.file_downloads`, later ClickPy/ClickHouse) and
count *all* downloads — pip users, CI runners, and mirrors alike. See the
methodology page for the honesty caveats this implies.

Each monthly snapshot is treated as that month's download rate for every
cohort package that appears in it. A package missing from a snapshot was
below the top-N cutoff that month (N grew from 4,000 → 5,000 → 8,000 over
the years) and gets no row — NULL, not zero.

Usage:
    python scripts/fetch_pypi_downloads.py [--workdir /tmp/tpp]

Requires: git, duckdb (pip install duckdb). Network: github.com only.
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_URL = "https://github.com/hugovk/top-pypi-packages"
DATA_FILE = "top-pypi-packages-30-days.min.json"
FIRST_MONTH = "2019-01"

ROOT = Path(__file__).resolve().parent.parent


def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def load_cohort():
    with open(ROOT / "data" / "cohort.csv", newline="") as f:
        return {row["package"] for row in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="/tmp/top-pypi-packages")
    args = ap.parse_args()

    clone = Path(args.workdir)
    if not clone.exists():
        print(f"Cloning {REPO_URL} (history only, blobs on demand)…")
        sh(["git", "clone", "--filter=blob:none", "--no-checkout", REPO_URL, str(clone)])

    # Every "Deploy …" commit is a data refresh. The snapshot covers the
    # trailing 30 days, so a deploy on the 1st describes the *previous*
    # month: label each snapshot with (commit date − 15 days).month and
    # keep the newest commit per label.
    log = sh(["git", "log", "--format=%H %ad", "--date=short", "--grep=^Deploy"], cwd=clone)
    per_month = {}
    for line in log.splitlines():
        sha, date = line.split()
        d = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=15)
        month = d.strftime("%Y-%m")
        if month >= FIRST_MONTH and month not in per_month:
            per_month[month] = sha  # log is newest-first → first seen wins

    cohort = load_cohort()
    rows = []
    for month in sorted(per_month):
        sha = per_month[month]
        try:
            blob = sh(["git", "show", f"{sha}:{DATA_FILE}"], cwd=clone)
        except subprocess.CalledProcessError:
            print(f"  {month}: {DATA_FILE} missing at {sha[:8]}, skipped", file=sys.stderr)
            continue
        snapshot = json.loads(blob)
        hits = 0
        for r in snapshot["rows"]:
            if r["project"] in cohort:
                rows.append((f"{month}-01", r["project"], r["download_count"]))
                hits += 1
        print(f"  {month}: {hits} cohort packages in top {len(snapshot['rows'])}")

    import duckdb

    con = duckdb.connect()
    con.execute("CREATE TABLE t (month DATE, package VARCHAR, downloads BIGINT)")
    con.executemany("INSERT INTO t VALUES (?, ?, ?)", rows)
    out = ROOT / "data" / "pypi_downloads.parquet"
    con.execute(f"COPY (SELECT * FROM t ORDER BY month, package) TO '{out}' (FORMAT PARQUET)")
    print(f"Wrote {out} ({len(rows)} rows, {len(per_month)} months)")

    # cohort.csv is the hand-edited source of truth; mirror it to parquet so
    # the single parquet connector sees it. Regenerate whenever the csv changes.
    cohort_out = ROOT / "data" / "cohort.parquet"
    con.execute(
        f"COPY (SELECT * FROM read_csv('{ROOT / 'data' / 'cohort.csv'}')) "
        f"TO '{cohort_out}' (FORMAT PARQUET)"
    )
    print(f"Wrote {cohort_out}")


if __name__ == "__main__":
    main()
