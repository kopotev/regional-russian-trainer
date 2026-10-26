# Country collector and optional AI tutor

This server runs on **127.0.0.1 only**. A static HTML file or public GitHub page cannot secretly use the author's ChatGPT or RNC account. Live collection needs an authorized RNC MCP connection configured by the operator. API tutoring needs a separately billed OpenAI API key; a ChatGPT subscription is not an API credential. Without it, the trainer's Open in ChatGPT route opens a real conversation in ChatGPT instead. No simulated model responses are returned.

## Start

Python 3.10 or later; no third-party Python dependencies.

```sh
python3 backend/server.py
```

Open `http://127.0.0.1:8765`. The public frontend is served from `site/standalone` by default. Never point `--static` at a research archive, credentials directory, or the entire working checkout. The local `runtime` directory contains private state and full source responses. Do not add it to Git.

Configure environment variables in the operator's shell or deployment secret manager, never in HTML or committed files:

| Variable | Purpose |
| --- | --- |
| `RNC_MCP_URL` | Authorized **HTTPS** Streamable HTTP MCP endpoint for RNC Test |
| `RNC_MCP_TOKEN` | Bearer access token if that endpoint requires it; obtain through its supported authentication flow |
| `RNC_MCP_TOOL` | Exact server tool name; default `batchCount` |
| `OPENAI_API_KEY` | Optional server-side OpenAI API credential |
| `OPENAI_MODEL` | Optional model identifier available to this API project; required alongside the key |
| `COLLECTOR_DATA_DIR` | Private writable job directory; default `runtime` |
| `CANDIDATE_POOL` | Optional replacement frozen CSV with `lemma,pos`; default bundled `backend/resources/candidates.csv` |
| `GITHUB_TOKEN` | Optional fine-grained token with Contents write access only to the intended public repository |
| `GITHUB_REPOSITORY` | Optional fixed `owner/repository` for explicit final-data publication |

PowerShell uses `$env:RNC_MCP_URL = 'https://your-authorized-endpoint/mcp'`, then `python backend/server.py`. Credentials are operator supplied. No credentials are bundled. The server does not implement an OAuth browser login or refresh tokens: an expired bearer token stops the current job, and the operator must renew it through the service's documented flow. Do not copy another user's ChatGPT connection token.

## What the collector does

1. A deliberate click submits an exact Russian country label from `country:ВКонтакте`, such as `Финляндия`. Labels are not silently translated. `Россия` is the reference and is not accepted as a target. Unsupported country labels are left to the corpus to reject; unconfirmed empty statistics never become zeros.
2. The server freezes all 24,166 bundled lemma–POS pairs in their existing review order, records the exact SHA-256, and creates a durable job. This vocabulary is a candidate pool, not a list of confirmed regionalisms. Its origins are recorded in `resources/provenance.json`; no held-out control words are added.
3. One worker issues **one** `batchCount` count query at a time. GICR, type `пост`, all available years, target country first. It asks for no contexts, concordances, frequency lists, or complete corpus jobs.
4. Target counts below 20 hits or 10 texts are rejected without a Russian query. Otherwise the matching Russian count is obtained. Supplied IPM is checked against the subcorpus denominator; acceptance uses exact integer arithmetic for the ratio ≥ 2. Confirmed Russian zero is allowed; an inferred zero is not.
5. One lemma contributes at most one word, even with several POS. It stops at the selected distinct-word target, user cancellation, pool exhaustion, or the first API/data/storage error. The default target for **new** country jobs is 94. Kazakhstan's previous collection has been stopped by the user; this service does not resume that legacy run.
6. Every full source response and timing record is saved before validation and state update. Atomic fsync + replacement protects job JSON. The server process holds an OS file lease for its runtime directory. A restart marks an unfinished job `interrupted`, rather than silently resending a count.
7. Resume requires an explicit click, rechecks the unchanged candidate pool, reuses valid saved counts, and skips previously attempted unresolved endpoints. It never retries an API error automatically. Such skipped candidates are incomplete, not negatives. Explicit numeric or HTTP-date Retry-After deadlines are respected before resume.
8. Final CSV is available after target completion or pool exhaustion. It labels every result as a **frequency screen**, with semantic status unverified. A lower-than-requested count at exhaustion is reported honestly.

Closing the progress popup does not cancel a job; cancelling waits for the current request to finish and save. Closing the Python server interrupts processing. Keep it running for a long collection. Running jobs are private to this local operator; this is not a multi-user Internet server. Do not expose it through a public tunnel without adding proper per-user authentication, authorization, quotas, TLS and durable worker infrastructure.

## Time and progress

Progress reports actual candidate count, requested/completed count calls, completed comparisons and distinct qualifying words. `queue_progress` refers to the frozen **queue examined**, not to the probability of finding a regional word. Until observations exist the ETA is unknown. Subsequently it gives a rough interval for checking the **remaining entire queue**, derived from the last 30 actual service durations and one to two calls per candidate. It never predicts when 94 words will be found: the target may be unreachable. On the original pilot, call latency and intermittent errors made collection take hours; no completion-time guarantee is appropriate.

## Browser API

First `GET /api/session` (alias `/api/config`) establishes an HttpOnly, SameSite=Strict cookie and returns:

```json
{"csrf_token":"session token", "collector_available":false, "chat_available":false, "country_label_note":"..."}
```

All POSTs require same-origin `Origin`, `Content-Type: application/json`, the cookie, and `X-CSRF-Token`. No CORS or arbitrary remote URLs are accepted from the browser. API responses are private/no-store.

| Request | Body/result |
| --- | --- |
| `POST /api/jobs` | `{country:"Финляндия", target_words:94}`; add a random `Idempotency-Key` header (8–100 ASCII alphanumeric/underscore/hyphen characters); returns 201 + job |
| `GET /api/jobs` | Existing local jobs |
| `GET /api/jobs/{id}` | Current job state; poll every few seconds |
| `POST /api/jobs/{id}/cancel` | `{}`; save then stop |
| `POST /api/jobs/{id}/resume` | `{}`; deliberate continuation after interruption/error |
| `GET /api/jobs/{id}/final.csv` | Final frequency data; 400 before finalization |
| `POST /api/jobs/{id}/publish` | `{}`; optional explicit GitHub publication of final frequency data only |
| `POST /api/chat` | `{messages:[{role:"user",content:"..."}], card:{lemma,pos,definition,meaning,semantic_status,country,example,source}}` |

Job statuses: `queued`, `running`, `cancelling`, `cancelled`, `paused_error`, `interrupted`, `complete`, `exhausted`. A job includes `id`, `country`, `reference_country`, `target_words`, `pool_size`, `processed_candidates`, `completed_comparisons`, `requests_completed`, `requests_attempted`, `qualified_words`, `error`, `queue_progress`, `eta`, `final_csv_url`, `publish_available`, and `published_url`. Only complete/exhausted jobs have an export URL. Counts are actual, not animated estimates.

Errors use non-2xx status and `{error:{code,message,retry_after}}`. Treat provider errors as errors even when the remote MCP envelope has `isError:false`; the nested count's `ok` value is checked. Do not automatically resubmit a failed write or duplicate a job. If GitHub publication is uncertain, inspect the repository before manually resolving `publish_state` in private job state; the server blocks repeat publication while uncertainty remains.

Chat returns `{reply,model,response_id,provider}`. It sends genuine user/assistant turns to `https://api.openai.com/v1/responses`, with `store:false`, bounded history and a source-aware Russian tutoring instruction. It does not collect corpus contexts or attribute invented examples to GICR. See the [official text generation documentation](https://developers.openai.com/api/docs/guides/text). The model may still be wrong: frequency differences do not establish special meanings, and generated exercises remain labelled as generated.

## Public country data

Publication is an explicit separate action after a job has finalized. It writes exactly one `data/country-<stable-country-hash>/frequency_screened.json` file to the configured repository. It includes selected words, aggregate counts, denominators, IPM, screen criteria and source-pool fingerprint. It excludes private raw paths, response archives, progress logs, audits and credentials. It does **not** label unreviewed words as ready teaching cards. The Contents API updates an existing country file using its current SHA; a failed/uncertain write is not silently retried.

## Verification

```sh
python3 backend/test_server.py
```

Tests use local fixtures and a local HTTP server; they make no RNC, OpenAI, or GitHub network calls. A passing fixture test does not demonstrate that an operator's OAuth token, API model access, billing or remote deployment is configured. The release should describe those live checks separately.
