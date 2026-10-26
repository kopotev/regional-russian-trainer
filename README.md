# Regional Russian trainer / Русский язык по странам

Corpus-informed Russian practice with a Russian/English interface. Kazakhstan is the pilot; its frequency collection was **closed at 94 distinct lemmas on 26 October 2026 by the project author**. No further Kazakhstan collection is scheduled.

## Open the trainer / Открыть тренажёр

Hosted trainer: https://regional-russian-trainer.kopako.chatgpt.site

Download `site/dist/index.html` and open it in a browser, or use the hosted version linked below. It contains all 94 teaching targets and their measured frequencies. Choose RU / EN, practise recognition or recall, inspect evidence, and open a genuine ChatGPT conversation for the selected word. The ChatGPT hand-off includes the evidence and an editable prompt; a copy button is available if pre-filling is unsupported. The conversation takes place in the user's ChatGPT account and is not a simulated chatbot.

The public static version does not inherit the author's ChatGPT/MCP connections. Embedded API dialogue and new-country collection require the separately configured local server below. It never reports an unconfigured service as a successful collection.

## Run the collector / Запустить сбор

Python 3.10 or newer; no third-party Python packages required.

```sh
python backend/server.py
```

Open `http://127.0.0.1:8765`. The default server serves only `site/dist`, not private runtime files. Configure authorized service access in environment variables before starting:

```sh
export RNC_MCP_URL='https://YOUR-AUTHORIZED-TEST-MCP-ENDPOINT'
export RNC_MCP_TOKEN='YOUR-OWN-AUTHORIZED-TOKEN'
export OPENAI_API_KEY='YOUR-OWN-API-KEY'
export OPENAI_MODEL='YOUR-AVAILABLE-RESPONSES-MODEL'
python backend/server.py
```

Do not put keys in HTML, Git, country files, screenshots or browser storage. ChatGPT subscription access is separate from API credentials. Model and endpoint are operator configuration, not guessed runtime values. See [backend/README.md](backend/README.md) for the exact API, restart/cancellation behaviour and configuration.

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
```

The first command runs fixture-based protocol and server tests; it makes no live corpus requests. Data rebuilding requires the private source research archive and is not necessary to run the published trainer. The public final data are the application input. See source comments for the distinction between tests, live access and pedagogical validation.

Original documents, private archives, credentials, intermediate results and audit reports are intentionally absent. Third-party resource attribution and any applicable source terms are preserved; no blanket licence over third-party source material is asserted.

Repository: https://github.com/kopotev/regional-russian-trainer

