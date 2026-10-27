# Regional Russian trainer 

Corpus-informed Russian practice with a Russian/English interface. Kazakhstan is the pilot; its frequency collection was **closed at 94 distinct lemmas on 26 October 2026 by the project author**. No further Kazakhstan collection is scheduled.

## Open the trainer / Открыть тренажёр

Hosted trainer: https://regional-russian-trainer.kopako.chatgpt.site

Download `site/standalone/index.html` and open it in a browser, or use the hosted version linked above. It contains all 94 teaching targets and their measured frequencies. Choose RU / EN, practise recognition or recall, inspect evidence, and open a genuine ChatGPT conversation for the selected word. The ChatGPT hand-off includes the selected card, its evidence and an editable practice request; a copy button is available if pre-filling is unsupported. The user sends the task in ChatGPT, where the real conversation takes place. No OpenAI API key is needed. Opening the link does not automatically send the task, attach a plugin or run a corpus query.

The hosted version has its own server and per-user persistent storage. It does not inherit the author's ChatGPT/MCP connections. Choose **Connect GICR / Подключить ГИКРЯ** and authorise a separate connection on the RNC provider's domain; the trainer never asks for your RNC password. Access and refresh tokens remain server-side. Corpus requests start only after a separate Start click. The dialogue uses ChatGPT itself; the website does not call a model API. The local server below remains an alternative for collection.

On the hosted site, keep the separate progress window open. Each explicit foreground step performs at most one count; closing the window stops further steps after the current response. Saved jobs can be reopened and continued manually. This is persistent, resumable work, not an autonomous background collector. Reopening a job never starts a count by itself.

## Dialogue with ChatGPT and RNC / Диалог с ChatGPT и RNC

1. Select a word and choose **Practise in ChatGPT / Тренироваться в ChatGPT**. Review and send the prepared task in the separate ChatGPT window.
2. ChatGPT asks one question at a time, waits for the learner, and gives brief corrective feedback. It receives the card's editorial example and frequency provenance; these are not presented as new corpus quotations or proof of a distinct regional meaning.
3. For authentic corpus examples, select the connected **RNC (Test)** plugin in that ChatGPT conversation and explicitly request examples. The prepared request asks for three GICR examples from VKontakte posts for Kazakhstan, across available years. Plugin availability depends on the user's ChatGPT account and connection.
4. Opening the dialogue starts no corpus request and never resumes the closed Kazakhstan frequency run. The website also offers a copyable corpus request; the learner submits it deliberately. If RNC is unavailable, practise from the supplied card without inventing corpus evidence.

ChatGPT provides the dialogue; RNC provides corpus evidence. The RNC plugin is not a chatbot embedded in the website. New-country frequency collection remains the separate, explicit workflow below.

## Run the collector / Запустить сбор

Python 3.10 or newer; no third-party Python packages required.

```sh
python backend/server.py
```

Open `http://127.0.0.1:8765`. The default server serves only `site/standalone`, not private runtime files. Configure authorized service access in environment variables before starting:

```sh
export RNC_MCP_URL='https://YOUR-AUTHORIZED-TEST-MCP-ENDPOINT'
export RNC_MCP_TOKEN='YOUR-OWN-AUTHORIZED-TOKEN'
python backend/server.py
```

Do not put corpus credentials in HTML, Git, country files, screenshots or browser storage. The RNC endpoint is operator configuration, not a guessed runtime value. The dialogue has no API credential or model configuration. See [backend/README.md](backend/README.md) for the exact API, restart/cancellation behaviour and configuration.

Enter the exact Russian country metadata label (for example, `Финляндия`). A separate window presents the duration warning and starts only after an explicit confirmation. It displays actual examined candidates, completed counts and passing distinct lemmas. Estimated time describes the remaining candidate workload, not a promise that a particular number of words will qualify. No contexts are collected by this stage.

Before live measurements, the interface gives a pilot-based planning estimate: approximately 2.4–4.8 days for a full 24,166-candidate pass at one or two counts per candidate, using the median 8.58 seconds from 30 recent successful pilot calls. This excludes interruptions, service pauses and editorial review. It is not an estimate of the time needed to find 94 qualifying words.

## Method / Метод

* Corpus: GICR through the authorized RNC Test MCP service; `type=пост`, `country:ВКонтакте`, all available years.
* Count one exact lemma + POS at a time; one outstanding corpus call.
* Count the target country first. Skip the Russian comparison when target hits <20 or texts <10.
* Compare target and Russia frequencies per million words. Retain a pair only when target hits ≥20, target texts ≥10 and IPM ratio ≥2.
* Missing responses, errors and unconfirmed empty statistics are not zero. Stop on service errors; honour Retry-After and do not silently replay a failed count.
* Checkpoint privately before deriving results. Do not put raw job logs or intermediate tables in this repository. Final publication is an explicit action; only one final JSON per country is exported.

The frozen candidate pool is an **input lexicon**, not a Kazakhstan result or corpus ranking. It retains the existing 24,166 exact lemma/POS pairs and review order. It excludes held-out evaluation-only items. Its attribution and hash are in `backend/resources/provenance.json`.

## Data and teaching / Данные и обучение

`data/Kazakhstan_final.json` is the sole final Kazakhstan data release: 94 distinct lemmas with count provenance, denominators, ratios, teaching glosses and tasks. Corpus-query POS is preserved separately from pedagogical classification. In particular, pronouns that matched noun-labelled queries are used for annotation-literacy tasks; they are not taught as nouns or as new regional meanings.

The result is **a frequency screen among tested candidates**, not the complete Kazakhstan top94. Country labels describe profile metadata, not verified citizenship or residence. A count difference does not establish a distinct meaning. Constructed practice sentences are labelled as constructed, never presented as corpus quotations. Existing source provenance is retained. There has been no learner-outcome experiment for this release.

## Development and validation / Разработка и проверка

```sh
python -m unittest discover -s backend -p 'test_*.py' -v
python scripts/build_final_data.py --validate-only
python site/build_data.py
node --test site/worker/runtime.test.mjs
node site/test_frontend.cjs
```

The first command runs fixture-based protocol and server tests; it makes no live corpus requests. Data rebuilding requires the private source research archive and is not necessary to run the published trainer. The public final data are the application input. See source comments for the distinction between tests, live access and pedagogical validation.

The hosted Worker implementation and its independent OAuth connection are documented in [site/worker/README.md](site/worker/README.md). To rebuild the hosted artifact, configure your own Site identity using `site/.openai/hosting.example.json`, preserve Sites authentication, set `SESSION_SECRET` as a runtime secret and run `bash site/scripts/build.sh` followed by `node site/scripts/validate-artifact.mjs`. The build embeds the public final JSON and frozen candidate input; it does not need the private research archive. The hosted and local runtimes contain no model-API client. Corpus access and the separate ChatGPT conversation are independent. A successful build or deployment does not prove that a user has completed RNC authorization or sent the practice task in ChatGPT.

Original documents, private archives, credentials, intermediate results and audit reports are intentionally absent. Third-party resource attribution and any applicable source terms are preserved; no blanket licence over third-party source material is asserted.

Repository: https://github.com/kopotev/regional-russian-trainer

