-- Canonical full-resolution queries for this dashboard's aggregates.
--
-- These run against the ClickHouse public playground (https://play.clickhouse.com,
-- user `play`, no auth) which hosts the complete PyPI download log and GitHub
-- events history. They are the "full-fat" way to regenerate data/ — exact
-- per-month counts for every cohort package, with installer detail.
--
-- The committed aggregates were instead derived from two public GitHub datasets
-- (see fetch_pypi_downloads.py / fetch_github_stars.py), because this repo was
-- built in an environment whose network policy allows github.com but not
-- play.clickhouse.com. Same underlying source (the public PyPI stats), coarser
-- resolution (top-N monthly snapshots). If you have open network, prefer these.
--
-- Run e.g.:
--   curl 'https://play.clickhouse.com/?user=play' --data-binary @- < query.sql

-- 1) data/pypi_downloads.parquet — monthly downloads per cohort package.
--    (pypi table: one row per download; check SHOW TABLES / DESCRIBE first.)
SELECT
    toStartOfMonth(date)  AS month,
    project               AS package,
    count()               AS downloads
FROM pypi.pypi_downloads_per_day_by_version_by_installer_by_type_by_country -- or `pypi.pypi`
WHERE project IN (
    'openai','anthropic','cohere','mistralai','google-generativeai','google-genai',
    'groq','together','ollama',
    'langchain','langchain-core','langgraph','llama-index','haystack-ai','dspy-ai',
    'crewai','pyautogen','semantic-kernel','litellm','instructor','langsmith',
    'pydantic-ai','openai-agents',
    'chromadb','pinecone-client','pinecone','qdrant-client','weaviate-client',
    'faiss-cpu','lancedb',
    'torch','transformers','accelerate','vllm','peft','datasets',
    'sentence-transformers','tokenizers','tiktoken','safetensors','huggingface-hub',
    'llama-cpp-python',
    'requests','boto3','numpy','pandas'
)
  AND date >= '2019-01-01'
  AND installer NOT IN ('bandersnatch', 'devpi')   -- exclude mirror traffic
GROUP BY month, package
ORDER BY month, package;

-- 2) data/installer_share.parquet — cohort downloads split by installer.
SELECT
    project   AS package,
    installer,
    count()   AS downloads
FROM pypi.pypi_downloads_per_day_by_version_by_installer_by_type_by_country
WHERE project IN (/* cohort list above */ 'openai')
GROUP BY package, installer
ORDER BY package, downloads DESC;

-- 3) data/github_stars.parquet — monthly new/cumulative stars per repo.
SELECT
    toStartOfMonth(created_at) AS month,
    repo_name                  AS repo,
    count()                    AS new_stars,
    sum(count()) OVER (PARTITION BY repo ORDER BY month) AS cumulative_stars
FROM github_events
WHERE event_type = 'WatchEvent'
  AND repo_name IN (
    'langchain-ai/langchain','run-llama/llama_index','huggingface/transformers',
    'vllm-project/vllm','ggml-org/llama.cpp','ollama/ollama','openai/openai-python',
    'pytorch/pytorch','AUTOMATIC1111/stable-diffusion-webui','Significant-Gravitas/AutoGPT'
  )
  AND created_at >= '2019-01-01'
GROUP BY month, repo
ORDER BY month, repo;
