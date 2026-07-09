---
title: The AI boom, in PyPI downloads
description: >
  Seven and a half years of Python package-install data for 42 AI packages
  (plus 4 baselines), monthly from January 2019 to June 2026. Every narrated
  paragraph on this page was written by an LLM at build time from the same
  data the charts draw — this site is static files.
icon: "📈"
---

# Watching the AI boom in 150 billion PyPI downloads

Every time someone runs `pip install`, PyPI writes it down. Add those lines up —
month by month, package by package, from January 2019 to June 2026 — and you can
watch the AI boom happen: the pre-history, the ChatGPT detonation in November
2022, the framework war, and the strange economics of a world where most
downloads aren't people at all.

The paragraphs marked with a small ✦ below were **written by an LLM at build
time**, from the same query results the charts draw. Nothing on this page talks
to a server: the analysis is baked into static JSON, the charts are baked query
snapshots, and the whole site is one Markdown file rendered by
[Dashdown](https://github.com/DirendAI/dashdown). See the
[methodology](/methodology) for sources and honest caveats.

```sql kpis
SELECT
    SUM(p.downloads)                                        AS total_downloads,
    SUM(p.downloads) FILTER (c.category <> 'baseline')     AS ai_downloads,
    MAX(p.month)                                            AS latest_month
FROM pypi_downloads p
JOIN cohort c USING (package)
```

```sql kpi_latest
SELECT SUM(p.downloads) AS ai_monthly
FROM pypi_downloads p
JOIN cohort c USING (package)
WHERE c.category <> 'baseline'
  AND p.month = (SELECT MAX(month) FROM pypi_downloads)
```

<Grid cols=3>
<Counter data={kpis} column="total_downloads" format="compact" label="Cohort downloads since 2019" />
<Counter data={kpis} column="ai_downloads" format="compact" label="…of which AI packages" />
<Counter data={kpi_latest} column="ai_monthly" format="compact" label="AI installs, latest month" />
</Grid>

## 1 · The seismograph

Forty-two AI packages — LLM SDKs, agent frameworks, vector databases, and
training/serving infrastructure — summed into one monthly line, stacked by
category. This is the whole story in a single chart; everything below is
zooming in.

```sql seismograph
SELECT
    p.month,
    CASE c.category
        WHEN 'llm_sdk'    THEN 'LLM SDKs'
        WHEN 'framework'  THEN 'Frameworks & agents'
        WHEN 'vector_rag' THEN 'Vector DBs & RAG'
        WHEN 'infra'      THEN 'Training & serving infra'
    END AS segment,
    SUM(p.downloads) AS downloads
FROM pypi_downloads p
JOIN cohort c USING (package)
WHERE c.category <> 'baseline'
GROUP BY 1, 2
ORDER BY 1, 2
```

<LineChart data={seismograph} x="month" y="downloads" series="segment" stacked
           title="Monthly PyPI downloads — AI package cohort, stacked by category"
           explain="Where is the inflection point in this time series, and how does the growth rate before it compare to after it? ChatGPT launched on 2022-11-30 — is that visible in the data?" />

<Ask data={seismograph} inline>
Narrate the overall shape of this time series in one short paragraph for a
technical reader: the near-flat years before late 2022, what happens after
ChatGPT's launch (November 30, 2022), and roughly how many times larger the
monthly download volume is at the end of the series than in October 2022. Use
concrete numbers from the data. Do not use bullet points.
</Ask>

## 2 · The framework war

LangChain was, for a moment, the fastest-adopted library in Python's history.
Then the ecosystem had second thoughts — and the raw SDKs, plus a quiet little
router called LiteLLM, kept climbing.

```sql framework_war
SELECT p.month, c.label AS package, p.downloads
FROM pypi_downloads p
JOIN cohort c USING (package)
WHERE p.package IN ('langchain', 'langgraph', 'llama-index', 'openai', 'anthropic', 'litellm')
ORDER BY p.month, package
```

<LineChart data={framework_war} x="month" y="downloads" series="package"
           title="Frameworks vs raw SDKs — monthly downloads" />

<Ask data={framework_war} inline>
This chart compares LLM orchestration frameworks (LangChain, LangGraph,
LlamaIndex) against raw provider SDKs (OpenAI, Anthropic) and the LiteLLM
router, monthly since 2019. Write two short paragraphs for a Hacker News
audience: first, the LangChain story — its explosive 2023 rise, and how its
trajectory compares to the OpenAI SDK's after 2024; second, the quieter but
more surprising story in this data — which package ends the series with the
most monthly downloads, and what its lead over the famous names suggests about
how production LLM apps are actually built. Cite concrete numbers. No bullet
points, no headings.
</Ask>

## 3 · The compute tell

SDK downloads tell you who is *calling* models. Infrastructure downloads —
PyTorch, Transformers, vLLM, Accelerate, PEFT — tell you who is *running* them.
The gap between the two is the API economy, measured in installs.

```sql compute_tell
SELECT p.month, c.label AS package, p.downloads
FROM pypi_downloads p
JOIN cohort c USING (package)
WHERE p.package IN ('torch', 'transformers', 'vllm', 'accelerate', 'peft')
ORDER BY p.month, package
```

<LineChart data={compute_tell} x="month" y="downloads" series="package"
           title="Training & serving infrastructure — monthly downloads"
           explain="Compare the trajectories of the training/fine-tuning stack (accelerate, peft) with the serving stack (vllm) and the base libraries (torch, transformers). What does the relative growth since 2023 suggest about what the ecosystem is doing with models?" />

<Ask data={compute_tell,framework_war} inline>
Comparing these two datasets — GPU-era infrastructure packages (torch,
transformers, vllm, accelerate, peft) versus API-calling packages (openai,
anthropic, litellm, langchain) — write one short paragraph on what the relative
volumes say about the shape of the AI economy: how many installs of API clients
happen for every install of serving infrastructure by the end of the series,
and whether the data supports the claim that most of the boom is people calling
someone else's GPUs rather than running their own. Use concrete numbers.
</Ask>

## 4 · Most of these downloads are robots

Time for the honest part. A PyPI "download" is an HTTP request for a package
file — from a human at a laptop, but far more often from a CI pipeline
reinstalling the world on every commit, a Docker build, a lockfile resolver, or
a cloud region warming its cache. The public stats can't cleanly separate them,
and this dataset (monthly top-N snapshots — see [methodology](/methodology))
carries no installer breakdown at all. So calibrate: here is the AI boom next
to the packages that computers install because other computers told them to.

```sql scale_check
SELECT c.label AS package,
       CASE WHEN c.category = 'baseline' THEN 'Boring baseline' ELSE 'AI cohort' END AS kind,
       p.downloads
FROM pypi_downloads p
JOIN cohort c USING (package)
WHERE p.month = (SELECT MAX(month) FROM pypi_downloads)
  AND p.package IN ('boto3', 'requests', 'numpy', 'pandas',
                    'litellm', 'openai', 'langchain', 'huggingface-hub', 'transformers', 'anthropic')
ORDER BY p.downloads DESC
```

<BarChart data={scale_check} x="package" y="downloads" series="kind" horizontal
          title="Latest month: AI packages vs infrastructure baselines"
          explain="boto3 is the AWS SDK — nobody hand-installs it 3.5 billion times a month; that volume is CI, Docker builds, and machines. Given that calibration, what do the AI packages' positions on this chart imply about how much of their volume is automated too?" />

<Ask data={scale_check} inline>
Write one short, slightly wry paragraph. boto3's ~3.5 billion monthly downloads
are overwhelmingly machines — CI pipelines, Docker builds, autoscaling fleets —
not humans typing pip install. Use that as the calibration to interpret the AI
packages on this chart: what does it mean that litellm and openai now sit in
the same order of magnitude as requests and numpy? Make the point that
download counts measure how often software is *run by machines*, which is
arguably the more honest measure of production adoption — while conceding we
cannot know how many humans are behind them. Concrete numbers, no bullets.
</Ask>

## 5 · Hype vs. usage

GitHub stars are applause; `pip install` is attendance. Some projects fill both
halls. Others — llama.cpp, Ollama, AutoGPT — are among the most-starred
repositories on Earth while their Python packages barely register next to the
boring workhorses. (Star history here covers each repo only while it sits in a
GitHub top-100 list; that's exactly the population hype is about.)

```sql stars
SELECT month, repo, cumulative_stars
FROM github_stars
WHERE repo IN ('ollama/ollama', 'ggml-org/llama.cpp', 'langchain-ai/langchain',
               'huggingface/transformers', 'vllm-project/vllm', 'Significant-Gravitas/AutoGPT')
ORDER BY month, repo
```

<LineChart data={stars} x="month" y="cumulative_stars" series="repo"
           title="Cumulative GitHub stars — the applause meter"
           explain="AutoGPT reached its star count within months of launch in 2023; transformers took years to earn a similar count. What do the different slopes here say about how attention worked before and after ChatGPT?" />

```sql hype_gap
SELECT g.repo,
       g.cumulative_stars                              AS stars,
       p.downloads                                     AS monthly_installs,
       ROUND(p.downloads * 1.0 / g.cumulative_stars)   AS installs_per_star
FROM (
    SELECT repo, cumulative_stars,
           ROW_NUMBER() OVER (PARTITION BY repo ORDER BY month DESC) AS rn
    FROM github_stars
) g
JOIN (VALUES ('ollama/ollama', 'ollama'),
             ('ggml-org/llama.cpp', 'llama-cpp-python'),
             ('langchain-ai/langchain', 'langchain'),
             ('huggingface/transformers', 'transformers'),
             ('vllm-project/vllm', 'vllm')) AS m(repo, package) ON g.repo = m.repo
JOIN pypi_downloads p
  ON p.package = m.package
 AND p.month = (SELECT MAX(month) FROM pypi_downloads)
WHERE g.rn = 1
ORDER BY installs_per_star DESC
```

<Table data={hype_gap} title="Stars vs installs, latest month"
       format="stars=number, monthly_installs=number, installs_per_star=number" decimals=0 />

<Ask data={hype_gap,stars} inline>
This table pairs each repo's GitHub stars with its Python package's monthly
PyPI downloads (latest month), plus installs-per-star. Write one short
paragraph on the gap: llama.cpp and Ollama are two of the most-starred projects
in the world, yet their Python bindings are dwarfed by langchain and
transformers installs. Offer the honest explanations — people run Ollama and
llama.cpp as apps or binaries, not via pip, so PyPI under-counts them; and
stars measure enthusiasm while installs measure automation. Note which project
has the most extreme stars-to-installs imbalance, with numbers.
</Ask>

## 6 · The AI's read on the data

Questions you're probably asking → each answered once, at build time, by the
model reading the actual query results. These are pinned by the author; there
is no prompt box, no server, and no per-view LLM cost — what you read is a
frozen JSON file.

<Ask data={seismograph} label="When did the boom actually start?"
     ask="Pinpoint the takeoff as precisely as this monthly data allows. Was November 2022 (ChatGPT) the ignition, or was growth already underway — and was there a second, later acceleration? Answer in 3-4 sentences with numbers." />

<Ask data={seismograph} label="Which category is winning?"
     ask="Rank the four AI categories by monthly downloads at the end of the series, and name the category that grew fastest over the final 18 months. One short paragraph, concrete numbers." />

<Ask data={framework_war} label="Did LangChain win?"
     ask="Answer the question 'did LangChain win?' in 3-4 sentences, using its trajectory versus langgraph, the raw openai SDK, and litellm. Note its rise, whether it plateaued, and who actually leads at the end of the series." />

<Ask data={compute_tell} label="Is anyone actually training models?"
     ask="Using accelerate and peft (fine-tuning) versus vllm (serving) versus torch (everything), answer in 3-4 sentences: does this install data suggest the ecosystem shifted from training/fine-tuning toward inference/serving, and when?" />

<Ask data={hype_gap} label="Which project is most hyped relative to its installs?"
     ask="Using installs-per-star as the measure, name the most over-hyped and most under-hyped projects in this table (lowest and highest installs per star), give the numbers, and offer one honest caveat about why PyPI installs under-count some of these projects. 3-4 sentences." />

<Ask data={kpis,kpi_latest} label="How big is this, really?"
     ask="Put the totals in perspective in 2-3 sentences: the cohort's downloads since 2019, the AI share of it, and the AI packages' latest monthly rate. If the latest monthly rate held, how long would it take the AI packages alone to log another 150 billion downloads?" />

---

**Fine print.** Downloads count all traffic the public stats count — humans,
CI, containers, and some mirrors; monthly figures for a package appear only
while it ranks in the public top-N snapshot (so early, tiny months are absent,
not zero). Sources, scripts, and every caveat: [methodology](/methodology).
Built with [Dashdown](https://github.com/DirendAI/dashdown) — the page you're
reading is one Markdown file.
