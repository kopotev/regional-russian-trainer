# Hosted runtime

`createRuntime({html, words, candidates})` returns a Cloudflare Worker `fetch`
handler. The build embeds the released HTML, teaching words and frozen candidate
pool. The module contains no provider credentials. Test with:

```sh
node --test site/worker/runtime.test.mjs
```

Required hosted configuration:

* `.openai/hosting.json`: keep the existing `project_id`, set `r2` to `BUCKET`
  and remove the previous static-only configuration.
* `SESSION_SECRET`: fresh secret configured through the hosting control plane.
* `BUCKET`: private R2 binding, provisioned by Sites.

Sites continues to own login. Every server operation requires its trusted
`oai-authenticated-user-id` header. Private OAuth grants, request records and jobs
are stored beneath a SHA-256 namespace derived from that Site-specific identity.

`GET /api/config` supplies a signed, user-bound `csrf_token`, connection flags
and `execution_mode: "foreground_steps"`. Dialogue flags are `chat_available: false`,
`dialogue_mode: "chatgpt_handoff"` and `api_key_required: false`. Mutations require exact same-origin
`Origin`, JSON and `X-CSRF-Token`. There is no arbitrary URL or tool proxy.

## RNC connection

An explicit `POST /api/rnc/connect` registers a public OAuth client at the fixed
RNC Test service and returns `authorize_url`. The browser navigates there; the
owner enters the existing connection password on the **RNC domain**, not on the
trainer. The callback verifies owner, one-time state, expiry, issuer and PKCE
before exchanging a code. Tokens stay server-side. New grants are independent
of any existing ChatGPT plugin grant. Callback success confirms authorization,
not that a corpus count has already succeeded. `POST /api/rnc/disconnect` removes
the trainer's local authorization record; no provider credentials are shown.

## Dialogue in ChatGPT

The website has no model-API client and requires no OpenAI API key. Its dialogue
button opens ChatGPT with the selected card, provenance and an editable practice
request. A copy fallback covers clients that do not preserve pre-filled text.
The learner reviews and sends the task. Opening the link neither attaches a
plugin nor runs a corpus query.

For real corpus examples, the learner selects the connected **RNC (Test)**
plugin in that ChatGPT conversation and explicitly asks for examples. The
prepared request starts with three GICR examples for Kazakhstan VKontakte posts,
all available years. Initial dialogue uses the supplied card and does not
restart the stopped Kazakhstan frequency screen. ChatGPT conducts the dialogue;
RNC returns evidence. `POST /api/chat` remains only as an authenticated HTTP 410
`CHATGPT_HANDOFF_ONLY` response and performs no external request.

## Collection

`POST /api/jobs` creates a job but performs **no corpus request**. Supply a
country, `target_words` and an `Idempotency-Key` header. A deliberate
`POST /api/jobs/{id}/step` performs at most one `batchCount` call containing
exactly one query. `GET /api/jobs/{id}` never advances collection.

The progress window sends sequential step requests only while the user has
started or resumed work. Closing it pauses advancement after the current call;
it is not an unattended background worker. Its saved job can be reopened.
Cancellation preserves the current response. Explicit resume recovers saved
valid responses and skips unresolved attempted candidates instead of replaying
them. Only `complete` and `exhausted` jobs expose `final.csv` or `final.json`.

A user-wide conditional R2 lease prevents overlapping requests across jobs and
Worker isolates. The implementation uses documented conditional headers,
`If-None-Match: *` for initial creation and quoted `If-Match` for replacement;
R2 returns `null` on failed preconditions and provides strong consistency.

Raw requests, actual responses and timings are saved before derived count
updates. Non-2xx bodies and malformed responses remain private and are not
turned into zeros. Explicit HTTP or nested count `Retry-After` values delay
manual resume. No automatic diagnostic or failed-count retries are performed.

The screen uses target hits >=20, texts >=10 and an exact BigInt cross-product
for the IPM ratio >=2 against Russia. It retains query POS separately from
pedagogical labels and counts a lemma once. It collects no contexts.

The 18 automated tests use in-memory R2 and controlled provider responses. They
cover PKCE state binding and replay, user isolation, CSRF, exact counts,
conditional cross-isolate exclusion, cancellation, persisted-response recovery,
unconfirmed zeros, malformed responses, rate limits, exact ratios and the retired
chat route. They make no live RNC calls. Live RNC authorization and provider
availability require separate checks; fixture tests do not validate a learner's
ChatGPT conversation.

R2 contract: https://developers.cloudflare.com/r2/api/workers/workers-api-reference/
