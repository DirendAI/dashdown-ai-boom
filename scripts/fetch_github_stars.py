#!/usr/bin/env python3
"""Build data/github_stars.parquet from the git history of
https://github.com/EvanLi/Github-Ranking.

That repository commits a daily CSV of the top-100 GitHub repos (overall
and per language) with their star counts. Replaying its history gives a
real monthly star series for any repo *while it is in a top-100 list* —
which the AI headline repos all are. A repo absent from a month's snapshot
simply wasn't top-100 yet; it gets no row (NULL, not zero).

Usage:
    python scripts/fetch_github_stars.py [--workdir /tmp/gh-ranking]

Requires: git, duckdb. Network: github.com only.
"""

import argparse
import csv
import io
import subprocess
from datetime import datetime
from pathlib import Path

REPO_URL = "https://github.com/EvanLi/Github-Ranking"
FIRST_MONTH = "2019-01"

# Repos whose star history we chart, keyed by every name they have had.
STAR_REPOS = {
    "langchain-ai/langchain": "langchain-ai/langchain",
    "hwchase17/langchain": "langchain-ai/langchain",
    "run-llama/llama_index": "run-llama/llama_index",
    "jerryjliu/llama_index": "run-llama/llama_index",
    "huggingface/transformers": "huggingface/transformers",
    "vllm-project/vllm": "vllm-project/vllm",
    "ggml-org/llama.cpp": "ggml-org/llama.cpp",
    "ggerganov/llama.cpp": "ggml-org/llama.cpp",
    "ollama/ollama": "ollama/ollama",
    "jmorganca/ollama": "ollama/ollama",
    "openai/openai-python": "openai/openai-python",
    "pytorch/pytorch": "pytorch/pytorch",
    "AUTOMATIC1111/stable-diffusion-webui": "AUTOMATIC1111/stable-diffusion-webui",
    "Significant-Gravitas/AutoGPT": "Significant-Gravitas/AutoGPT",
    "Significant-Gravitas/Auto-GPT": "Significant-Gravitas/AutoGPT",
    "Torantulino/Auto-GPT": "Significant-Gravitas/AutoGPT",
}

ROOT = Path(__file__).resolve().parent.parent


def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="/tmp/gh-ranking")
    args = ap.parse_args()

    clone = Path(args.workdir)
    if not clone.exists():
        print(f"Cloning {REPO_URL} (history only, blobs on demand)…")
        sh(["git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch",
            REPO_URL, str(clone)])

    # One snapshot per month: the first daily CSV committed in that month.
    log = sh(["git", "log", "--reverse", "--format=%H %ad", "--date=short"], cwd=clone)
    per_month = {}
    for line in log.splitlines():
        sha, date = line.split()
        month = date[:7]
        if month >= FIRST_MONTH and month not in per_month:
            per_month[month] = (sha, date)

    rows = []
    for month in sorted(per_month):
        sha, date = per_month[month]
        # The daily file is named after its date; fall back to listing.
        names = [f"Data/github-ranking-{date}.csv"]
        try:
            listing = sh(["git", "ls-tree", "--name-only", sha, "Data/"], cwd=clone)
            names += sorted(n for n in listing.splitlines() if n.endswith(".csv"))
        except subprocess.CalledProcessError:
            pass
        blob = None
        for name in names:
            try:
                blob = sh(["git", "show", f"{sha}:{name}"], cwd=clone)
                break
            except subprocess.CalledProcessError:
                continue
        if blob is None:
            continue
        best = {}
        for r in csv.DictReader(io.StringIO(blob)):
            url = (r.get("repo_url") or "").removeprefix("https://github.com/")
            repo = STAR_REPOS.get(url)
            if repo:
                stars = int(r["stars"])
                best[repo] = max(best.get(repo, 0), stars)
        for repo, stars in best.items():
            rows.append((f"{month}-01", repo, stars))
        print(f"  {month}: {len(best)} tracked repos in top-100 lists")

    import duckdb

    con = duckdb.connect()
    con.execute("CREATE TABLE t (month DATE, repo VARCHAR, cumulative_stars BIGINT)")
    con.executemany("INSERT INTO t VALUES (?, ?, ?)", rows)
    out = ROOT / "data" / "github_stars.parquet"
    con.execute(
        "COPY (SELECT month, repo, cumulative_stars, "
        "cumulative_stars - lag(cumulative_stars) OVER (PARTITION BY repo ORDER BY month) AS new_stars "
        f"FROM t ORDER BY month, repo) TO '{out}' (FORMAT PARQUET)"
    )
    print(f"Wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
