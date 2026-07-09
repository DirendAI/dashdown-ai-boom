---
title: Methodology
description: Where the numbers come from, how they were aggregated, and every caveat that matters.
icon: "🔬"
width: s
---

# Methodology & honest caveats

## Sources

Two public datasets, both replayed from git history so every number is real and
reproducible without credentials:

- **PyPI downloads** — [hugovk/top-pypi-packages](https://github.com/hugovk/top-pypi-packages),
  which has published a monthly snapshot of the top PyPI packages by
  trailing-30-day download count since early 2019. The counts originate from
  PyPI's public download statistics (the
  [`bigquery-public-data.pypi.file_downloads`](https://console.cloud.google.com/marketplace/product/gcp-public-data-pypi/pypi)
  dataset, later [ClickPy](https://clickpy.clickhouse.com/)/ClickHouse).
  `scripts/fetch_pypi_downloads.py` walks the repo's history, takes one
  snapshot per month, and keeps the 46 cohort packages
  (`data/cohort.csv`).
- **GitHub stars** — [EvanLi/Github-Ranking](https://github.com/EvanLi/Github-Ranking),
  which commits a daily CSV of every GitHub top-100 list (overall and per
  language) with star counts, since late 2018. `scripts/fetch_github_stars.py`
  takes the first snapshot of each month.

`scripts/clickhouse_queries.sql` contains the canonical full-resolution
queries against the [ClickHouse public playground](https://play.clickhouse.com)
for anyone who wants exact per-month counts for every package (including the
installer breakdown this page had to do without).

## The caveats, in decreasing order of importance

1. **Downloads are not humans.** A PyPI download is an HTTP request — CI
   pipelines, Docker builds, dependency resolvers, and autoscaling fleets
   dominate the totals. boto3's ~3.5&nbsp;billion downloads a month are the
   proof: nobody types `pip install boto3` three and a half billion times. The
   full ClickHouse/BigQuery data can split traffic by installer and exclude
   mirror clients (`bandersnatch`, `devpi`); the top-N snapshots used here
   cannot, so treat every absolute number as *machine activity*, and trends —
   which are the story — as directionally solid.
2. **Top-N censoring.** A package appears in a monthly snapshot only if it
   ranked in the public top-N that month (N grew from ~4,000 in 2019 to 15,000
   today). Small early months are therefore *missing*, not zero — lines start
   when a package first cracks the list. This clips the tails of young
   packages and slightly flatters their apparent takeoff steepness.
3. **Snapshot timing.** Each monthly figure is a trailing-30-day window
   captured near the start of the following month, labeled with the month it
   mostly covers. A few months in 2019–2020 have no snapshot and are simply
   absent — which also means cumulative totals (like the headline counter) sum
   only the sampled months. Read them as floors, not exact censuses.
4. **Star coverage.** Star history covers a repo only while it sits in a
   GitHub top-100 list (overall or per-language). That's exactly the
   population "hype" is about, but it means series begin when a repo becomes
   famous, and `openai/openai-python`-sized repos drift in and out.
5. **PyPI under-counts local AI.** Ollama and llama.cpp are used mostly as
   standalone apps/binaries, so their Python bindings understate their real
   adoption. Section 5 says this out loud rather than pretending the chart is
   the whole truth.
6. **Package renames.** The cohort maps both old and new names where relevant
   (`pinecone-client` → `pinecone`); repo renames are handled in the star
   script (`ggerganov/llama.cpp` → `ggml-org/llama.cpp`).

## The AI commentary

Every ✦-marked paragraph and every card in section 6 was generated **once, at
build time** by `mistral-medium-latest` reading the same (capped) query results
the charts render, via Dashdown's [`<Ask>`](https://github.com/DirendAI/dashdown)
component. The questions are pinned by the author; readers cannot prompt the
model, no LLM is called when you view the page, and the answers are ordinary
static JSON files in the build output. If the site was built without an API
key, those blocks show a muted notice instead — nothing else changes.

## Reproduce it

```bash
pip install 'dashdown-md[mistral,pdf]'
python scripts/fetch_pypi_downloads.py     # rebuild data/pypi_downloads.parquet
python scripts/fetch_github_stars.py       # rebuild data/github_stars.parquet
dashdown serve .                           # live dev server
MISTRAL_API_KEY=… dashdown build . --out dist   # static site, answers baked
```
