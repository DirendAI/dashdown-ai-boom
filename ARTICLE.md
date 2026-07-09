# I watched the AI boom happen in 150 billion PyPI downloads — and let the dashboard explain itself

*Every `pip install` leaves a line in a log. Replayed monthly since 2019, those
lines are a seismograph of the AI gold rush — and the dashboard that plots them
narrates its own charts, from static files, for $0 a view.*

---

Python is where the AI boom physically happens. The models make the headlines,
but the work — the agents, the RAG pipelines, the fine-tuning runs, the seventeen
competing frameworks — arrives on people's machines through `pip install`. PyPI
counts every one of those installs, publicly.

So I took 42 AI packages — the LLM SDKs, the agent frameworks, the vector
databases, the training and serving infrastructure — plus four boring baselines
for scale, and pulled their monthly download counts from January 2019 to June
2026. Then I did the part I actually want to tell you about: I let the dashboard
write its own analysis. Every chart on the
[live site](https://direndai.github.io/dashdown-ai-boom/) is followed by prose an
LLM generated *at build time* from the same query results the chart draws — baked
into static JSON, no server, no chat box, no per-view API bill.

Here's what the data says, section by section.

## 1. You can see ChatGPT land, to the month

Summed together, the AI cohort is a near-flat line for four years: about 600,000
downloads a month in mid-2019, creeping to 36 million by October 2022 — real
growth, but the kind you squint at. ChatGPT ships on November 30, 2022. The line
detonates. Eighteen months later the cohort does 231 million downloads a month;
by June 2026 it's **4 billion a month** — roughly 110× the pre-ChatGPT rate,
still accelerating.

The chart doesn't need an annotation arrow pointing at the inflection — but the
dashboard's explain layer draws its marks from the data anyway (the model
proposes annotations, the framework validates each one against the actual query
result before drawing it).

## 2. LangChain didn't win. Neither did OpenAI. LiteLLM is winning.

Zoom into the framework war and the famous story is there: LangChain goes from
zero (it didn't exist before October 2022) to the fastest-adopted library in
Python's recent history, ~2M monthly downloads by mid-2023, 330M by 2026. The
backlash-and-plateau narrative you read on Hacker News is only half-visible in
the data — installs keep growing — but the *lead* changes hands.

The genuinely surprising line belongs to **LiteLLM**, the do-one-thing router
that translates between provider APIs. It ends the series at **633 million
downloads a month — ahead of LangChain and ahead of the raw OpenAI SDK**.
Honesty requires the fine print: that lead is new and violently steep — 97M in
March 2026, 633M three months later — so it's some mix of a real shift in how
production LLM apps are built ("one interface to every model, get out of my
way") and a handful of very large automated pipelines pinning it. Section 4 is
about why you can't fully tell those apart. Either way, the router beating the
framework *and* the first-party SDK in raw volume was not on my 2023 bingo card.

## 3. The API economy, measured in installs

SDK downloads tell you who's *calling* models; torch/vllm/accelerate downloads
tell you who's *running* them. Both boom, but by the end of the series API-client
installs outnumber serving-infrastructure installs several times over. The
fine-tuning stack (PEFT, Accelerate) grows steadily; the serving stack (vLLM)
grows faster — but the overwhelming majority of the boom is people renting
someone else's GPUs through an HTTPS endpoint.

## 4. Most of these downloads are robots (and that's the honest headline)

Calibration: **boto3 does ~3.5 billion downloads a month.** Nobody types
`pip install boto3` three and a half billion times — that volume is CI pipelines,
Docker builds, and autoscaling fleets reinstalling the world on every deploy.

That's not a caveat to bury in a footnote; it's the right lens for the whole
dashboard. When LiteLLM and the OpenAI SDK reach the same order of magnitude as
`requests` and `numpy`, it doesn't mean hundreds of millions of humans — it means
AI packages are now baked into the *automated* software supply chain, rebuilt by
machines thousands of times a day. Download counts measure how often software
runs in production plumbing. By that honest measure, the boom is real.

## 5. Stars are applause; installs are attendance

Pair each headline repo's GitHub stars with its Python package's monthly
installs and the gap is the story. llama.cpp: 119k stars, 711k monthly installs
of its Python binding — **6 installs per star**. LangChain: 141k stars, 330M
installs — **2,347 per star**. Ollama sits in between (175k stars — more than
LangChain! — 23M installs).

Part of that is measurement (people run Ollama and llama.cpp as apps, not pip
packages — PyPI genuinely under-counts them). But part of it is the shape of
hype itself: the projects everyone stars are the ones that promise you can run
AI *yourself*; the packages machines install by the hundreds of millions are the
ones that call someone else's API.

## The part I actually built: a dashboard that narrates itself

Everything above — the whole site — is **one ~250-line Markdown file**. A section
looks like this:

````markdown
```sql framework_war
SELECT p.month, c.label AS package, p.downloads
FROM pypi_downloads p JOIN cohort c USING (package)
WHERE p.package IN ('langchain','langgraph','llama-index','openai','anthropic','litellm')
```

<LineChart data={framework_war} x="month" y="downloads" series="package" />

<Ask data={framework_war} inline>
Write two short paragraphs: the LangChain story, then the quieter, more
surprising story — who actually leads at the end of the series…
</Ask>
````

[Dashdown](https://github.com/DirendAI/dashdown) (`pip install dashdown-md`)
renders it: the SQL runs on an embedded DuckDB over ~20 KB of committed Parquet,
the chart is ECharts, and `<Ask>` sends the query result to an LLM and renders
the answer as body prose. The trick is *when*: `dashdown build` executes every
query and every Ask **once**, freezes the answers into JSON next to the chart
snapshots, and emits plain static files. GitHub Pages serves them. The reader
never triggers an LLM call, can't prompt-inject anything (there's no prompt
box), and the total AI bill for the site you're reading was a few cents of
Mistral tokens at build time. Charts additionally carry an `explain` layer that
bakes chart-anchored annotations — the model proposes marks, the framework
validates them against the actual query result, and invalid ones are dropped.

The data pipeline is deliberately boring: two Python scripts replay the git
history of two public datasets ([hugovk/top-pypi-packages](https://github.com/hugovk/top-pypi-packages)
for downloads, [EvanLi/Github-Ranking](https://github.com/EvanLi/Github-Ranking)
for stars) into two small Parquet files, which are committed. Full methodology —
including the top-N censoring and every other caveat — is on the site.

The whole thing is a ~250-line Markdown file →
**[github.com/DirendAI/dashdown-ai-boom](https://github.com/DirendAI/dashdown-ai-boom)**,
live at **[direndai.github.io/dashdown-ai-boom](https://direndai.github.io/dashdown-ai-boom/)**.
