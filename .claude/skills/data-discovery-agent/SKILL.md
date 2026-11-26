---
name: data-discovery-agent
description: >
  Reusable skill for Stack AI Rewire, Assignment: AI-Native Data Discovery. Runs the first
  stage of any AI/DS project: locate, catalog and assess the feasibility of internal and
  external data sources for a business problem, before any pipeline is built. Works for
  any use case written to the use-case contract (use_cases/<ID>_*.json + brief + internal
  estate). It sets up and checks the agent, frames the use case, runs planning and scouting,
  suggests external sources for unmet needs (Step 2b), then pauses for human review. Steps 3–5
  cover the candidate gate, the pipeline runs, the trace audit with one G7 root-cause fix, and
  the memo review, sign-off and self-check.
---

# AI-Native Data Discovery: Assignment Runner (Steps 0–5)

You are Claude, running the first steps of **Stack AI Rewire, Assignment: AI-Native Data
Discovery** in Claude Code, against the learner's copy of this repo. The repo
contains a multi-agent discovery system (`discovery_agent/`): Planner → Scout (internal catalog,
wiki, external register) → **candidate gate, where the human adds dataset links (any URL)** →
Profiler (one per source) → deterministic rules → Risk Assessor → Memo Writer, then a human review gate.

This skill gets a use case ready, checks the tooling, runs **plan + scout**, suggests external
sources for the needs that remain unmet (Step 2b), then runs the pipeline and the review (Steps 3–5).

The skill is **use-case agnostic**. UC1 (air quality and traffic) and UC2 (ice-cream sales, weather and holidays) ship with
the repo, but any business problem written to the contract below runs the same way.

## Required input
- `use_cases/<ID>_<slug>.json`: the machine-readable use case (windows, needs, grains, geography).
  Contract: `use_cases/_TEMPLATE_use_case.json`.
- `use_cases/<ID>_<slug>.md`: the business brief: problem, decisions supported, scope, out of scope.
- `internal/<ID>_<client>/catalog_export.json` + `internal/<ID>_<client>/wiki/*.md`: the client's
  internal catalog export and documentation (metadata only, never data values).
- `config/external_sources_register.json`: the external sources the client has agreements for or
  has approved, tagged with the use case id.
- **Dataset links** (any https URL): supplied by the human at the candidate gate, from their own
  search or accepted from the Step 2b suggestions. For UC1 and UC2, README.md section 4 lists links
  whose expected assessment is known.
- **The learner's search script** `scripts/web_search.py` for Step 2b. It is not provided: the learner
  generates it with Claude Code (Assignment Task 3; the prompt is in README.md, section 4, "Suggest
  sources (Step 2b)"). Claude Code's built-in `WebSearch` does not work with the gateway key, so do not
  use it. If the script is missing, fails, or returns no citations, stop at Step 2b and tell the learner
  to generate or fix it. Do not write suggestions without search results.
- `config/allowlist.json`, `config/red_flags.json`, `config/settings.json`: provided. Do not loosen
  the allowlist or the caps to make a run pass.
- Gateway credentials in the environment: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`,
  `ANTHROPIC_MODEL`. Never print, log or commit the token.

## Repo scaffold this skill produces
```
.
├── use_cases/<ID>_*.json, <ID>_*.md         <- provided, or written by you in Step 1 (new use case)
├── internal/<ID>_<client>/                  <- provided, or assembled in Step 1 (new use case)
├── outputs/<ID>/
│   ├── use_case_validation.txt              <- Step 1
│   ├── search_plan.json                     <- Step 2 (Planner)
│   ├── candidates.json                      <- Step 2 (Scout)
│   ├── trace.jsonl, transcripts/            <- Step 2 (evidence of every LLM/tool/HTTP call)
│   ├── run_summary.json                     <- Step 2 (tokens, tool calls, warnings)
│   ├── links.json                           <- Step 2 (copy of the prescribed links) and Step 2b (accepted suggestions appended): the ONE links file
└── outputs/artifacts/step0_checks.md        <- Step 0
```
Steps 3–5 produce the remaining files under `outputs/<ID>/` (`gate_decisions.json`, `records/`, `rule_flags.json`, `risk_assessment.json`, `discovery_results.json`, `feasibility_memo.md`, `signoff.json`) and `outputs/artifacts/` (`review_<ID>.md`, `check_<ID>.json`, `pytest_after.txt`, `decisions.md`).

---

## Step 0: Set up and check the tooling (no LLM calls)
1. If no environment is active: `python3 -m venv .venv && source .venv/bin/activate`, then
   `pip install -r requirements.txt`.
2. Check that the gateway variables are **set**, without printing their values:
   `python -c "import os;print({k: bool(os.environ.get(k)) for k in ['ANTHROPIC_BASE_URL','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_MODEL']})"`.
   If any is `False`, stop and tell the learner which one. Do not ask them to paste the token.
3. Run the offline tests: `python -m pytest tests/ -q`. `tests/test_tools_offline.py` and
   `tests/test_agent_loop.py` must pass. On a fresh starter repo, `tests/test_learner_gaps.py` is
   **expected to fail** (20 of 52 tests) until G1, G3, G4, G5 and G6 are implemented; once those gaps
   are closed, all 52 tests pass. If any gap tests fail on a fresh repo, report them; do not implement them here.
4. Smoke-test the tools without the LLM:
   - `python -m discovery_agent tool search_internal_catalog '{"query": "<a need from the brief>"}' --use-case <ID>`
   - `python -m discovery_agent tool inspect_dataset_link '{"url": "https://archive.ics.uci.edu/dataset/360/air+quality"}' --use-case <ID>`
   - `python -m discovery_agent tool list_external_register '{}' --use-case <ID>`
   Each must return JSON, not a traceback. A `DOMAIN_NOT_ALLOWLISTED` result is the guardrail
   working, not a bug.
5. Write `outputs/artifacts/step0_checks.md`: test results (pass/fail counts per file), the tool
   smoke results (one line each), and the model id in use. Never write the token.

## Step 1: Frame the use case against the contract
**Existing use case** (UC1 or UC2, where `use_cases/<ID>_*.json`
and `internal/<ID>_*/` already exist): check that the files exist, then do item 4 and item 5 below.
Do not rewrite a contract that someone else wrote. If item 4 fails, report the error and ask the
learner before you change any input.

**New use case** (the learner gives you a business problem): write the inputs, do not invent data.
1. Copy `use_cases/_TEMPLATE_use_case.json` to `use_cases/<ID>_<slug>.json` and fill every field:
   - `windows`: one per analysis period, with ISO dates and a purpose. Do not use a single
     open-ended window to dodge coverage checks.
   - `needs`: one row per data need, in business words, with `priority` (must/should/could),
     `min_grain` (one of `minute, 15min, 30min, hourly, daily, weekly, monthly, quarterly, annual,
     event, static`) and the `windows` it applies to. Aim for 5–12 needs. Split compound needs.
   - `as_of`: the date the discovery is valid for. It drives staleness checks.
2. Write `use_cases/<ID>_<slug>.md` with the same sections as the UC1 brief: business problem,
   decisions supported, scope, needs table, where to look, out of scope.
3. Internal estate: if the learner has a real catalog export, convert it to the
   `catalog_export.json` entry shape used in `internal/UC1_valdena_health/` (null where the catalog
   holds nothing, never a guess), and put the documentation pages in `wiki/` with the same front
   matter (`page_id`, `title`, `owner`, `last_edited`). Add the client's approved external sources
   to `config/external_sources_register.json` with the new use-case id and their real
   `agreement_status`. If the learner has no internal estate, stop and ask. Do not fabricate one.
4. Validate: `python -m discovery_agent validate-use-case <ID> | tee outputs/<ID>/use_case_validation.txt`.
   Fix every error it reports in the inputs, not in the validator.
5. Show the learner the needs table (id, name, priority, min_grain, windows) and the windows.
   **Pause** (for a human learner in an interactive session; in a non-interactive run, write the table and stop). Wait for them to confirm or change it. The needs list decides what the agents
   search for and what the rules check, so a wrong need here gives wrong verdicts later.

## Step 2: Plan and scout, then stop at the candidate gate
1. Run: `python -m discovery_agent run --use-case <ID> --stop-after scout --no-input`.
   This runs the Planner (search plan per need, including hints on what external data to link) and
   the Scout (catalog, wiki and register search), and writes `search_plan.json`, `candidates.json`, `trace.jsonl` and `transcripts/`.
2. If the run fails, read the last events in `outputs/<ID>/trace.jsonl` and the failing agent's
   transcript before changing anything. Fix the cause (credentials, model id, a prompt, a tool
   bug) and re-run. Do not raise `max_turns` or the HTTP caps as a first response.
3. Review `candidates.json` against the needs, and give the learner a table:
   need id → candidate source ids → `unmet_needs`. Then name, from the trace:
   - needs with no candidate, or only one;
   - internal entries the Scout opened but did not read the wiki backlinks for;
   - internal searches that returned nothing and were not rephrased.
4. Show the learner the `unmet_needs` and the planner's `external_data_hints`. If a need is already met
   by internal or register sources, say so. Then ask: **do you already have dataset links that fill any
   of these needs?** For UC1, name the three prescribed links in README.md section 4; UC2 has none. Ask whether
   the learner will use them. Each link needs need ids and windows. If the learner uses them, copy
   `links/UC1_example_links.json` to `outputs/<ID>/links.json` once, only if that file does not exist yet (for UC2, start from `[]`). Never copy over it: it may already hold accepted suggestions. The Chicago
   link in README.md section 4 is one the learner accepts on purpose: its refusal is the finding. Claude
   does not make that decision for the learner. **STOP and wait for the reply.**
   Only then go to Step 2b.

## Step 2b: Suggest external sources (only for needs still unmet)
1. Only after the learner has answered Step 2, item 4. Check that `scripts/web_search.py` exists in the
   learner's repo. If it does not, **STOP**: ask the learner to generate it with Claude Code, using the
   prompt in README.md ("Suggest sources (Step 2b)"), and wait for it. Do not write the script yourself.
   Once it exists, search with it for up to **five** public datasets that could fill the unmet needs:
   `python scripts/web_search.py "<query>"`. Use the planner's `external_data_hints` as starting queries.
   Each result is a lead from a search model, not a verified source. Only a URL with a citation may be
   suggested, and each one still needs checking on its publisher's page.
2. For each suggestion, show the learner: publisher, exact URL (the dataset or record page, not a search
   page), need ids, coverage **as the page states it** (quote the page; write `"not stated"` if the page
   does not say), and what still needs checking (licence, population, access). Do not download data.
3. **STOP and wait.** For each suggestion the learner decides `accept`, `reject` or `revise` (with new
   need ids or windows), with a short reason. The learner may also add links they found. Never decide,
   and never write a reason, for the learner. Silence is not acceptance.
4. Record every decision and reason in `outputs/artifacts/decisions.md` under "Source suggestions". Append each
   accepted suggestion to `outputs/<ID>/links.json` (the same file as Step 2), in the shape of
   `links/_TEMPLATE_links.json`, with the learner's reason as `note`. Never overwrite the prescribed links.
   The **learner** writes `outputs/<ID>/gate_decisions.json` (`{"decisions": [{"url", "decision": "accept" or
   "reject", "reason"}]}`), one entry for every link in `links.json`, after inspecting each link themselves.
   If the learner asks you to write it, transcribe only the reasons they have dictated, word for word, and
   say so in `decisions.md`. Never write a reason the learner did not give. The pipeline refuses to profile
   a link without one.
5. For each accepted link, check its host is on `config/allowlist.json`:
   `python -m discovery_agent tool inspect_dataset_link '{"url": "<link>"}' --use-case <ID>`.
   If a host is refused, **STOP**: the learner decides whether to add it, with a G6 justification in
   `outputs/artifacts/decisions.md`. Do not add hosts yourself, and do not try an alternate URL. The Chicago host (`catalog.data.gov`) is refused by design: record that refusal as a finding. The Eurostat host waits for G6 in Task 6; re-run the inspection after it is added.

**Then stop.** Tell the learner the candidate list and accepted links are ready for review, and give
them the command for the next stage:
`python -m discovery_agent run --use-case <ID> --from-stage profile --links-file outputs/<ID>/links.json`
(the same file as Step 2; it must hold every link the learner has decided on).
Continue with Step 3.

---

## Rules that hold in every step
- **Metadata first, then a capped sample, never the whole dataset.** Read schemas, descriptions,
  coverage and terms; `sample_data_file` may read the first part of a file. Do not download whole
  datasets or copy personal data into any output.
- **Provenance on every claim.** Every statement about a source names a tool call, URL, catalog
  field or wiki page.
- **Unknown stays unknown.** Never infer a licence, owner, refresh cadence or consent. Use null and
  list it under unknowns.
- **Guardrails are not obstacles.** A refused host, an expired vendor agreement or a restricted
  table is a finding to record, not something to work around.
- **The agents are the product.** When an output is wrong, fix the agent (prompt, tool, rule,
  validator) and re-run. Never hand-edit `candidates.json`, records or results to look right.
- **A suggestion is not a verified source.** Selecting it grants no host access and no permission to
  use the data. Keep the exact-host allowlist.

---

## Step 3: Candidate gate, allowlist, tests and the pipeline run
1. **Gate decisions (only when the use case has dataset links).** The learner writes
   `outputs/<ID>/gate_decisions.json` with one entry for every link in `outputs/<ID>/links.json`:
   `{"decisions": [{"url", "decision": "accept" or "reject", "reason"}]}`. Each `url` must match a link
   in `links.json` exactly (copy it, do not retype it). Each `reason` is at least 20 characters, in the
   learner's own words. The pipeline refuses to profile a link without one. For UC2 (no links), skip
   this file and run without `--links-file`.
2. **Allowlist.** Open `config/allowlist.json`. Every entry is an exact host (for example
   `www.dati.lombardia.it`), with no `*` and no parent domain such as `europa.eu`. Each host added under
   G6 needs a justification in `outputs/artifacts/decisions.md`. Never add `catalog.data.gov` or any host
   the learner has not accepted. A refused host is a finding, not a bug to work around.
3. **Tests.** Run `python -m pytest tests/ -q`. Before the gap work, `tests/test_learner_gaps.py`
   fails (20 of 52 tests). Once G1–G6 are done, all 52 must pass. Save the output with
   `python -m pytest tests/ -q > outputs/artifacts/pytest_after.txt`.
4. **Run the pipeline.**
   - With links: `python -m discovery_agent run --use-case <ID> --links-file outputs/<ID>/links.json --no-input`
   - Without links: `python -m discovery_agent run --use-case <ID> --no-input`
   - Targeted re-run: `python -m discovery_agent run --use-case <ID> --from-stage <stage> --stop-after <stage> --only <source_id>[,<source_id>] --no-input`.
     The stages are `plan, scout, profile, assess, memo`.

   A full UC1 run took more than 10 minutes. Run it in the background and wait for it to finish. Do
   not start a second copy while it runs.
5. **Read the run output.** Check the end of the run log and `outputs/<ID>/run_summary.json`. `warnings`
   should list only the hosts you already expect to be refused (for UC1, `catalog.data.gov`). Compare
   `http_refused` and `tool_errors` with the refusals you expect.

Practical gotchas (observed in UC1 and UC2):
- Pass `--out <dir>` to redirect pipeline outputs into a scratch folder when running a dry run or reuse check without overwriting an existing `outputs/<ID>/`.
- `run` takes `--use-case <ID>`. `check` takes the ID as a positional argument: `check UC1`.
- `--from-stage profile` reuses `candidates_final.json` and says so in the log. To run the gate again,
  pass `--link` or `--links-file`.
- `trace.jsonl` is appended by every run. `check` totals every run in it: UC1 showed 40 LLM calls
  (8 from the plan and scout run plus 32 from the full run). `run_summary.json` shows only the latest run.
  Compare per-run figures with `run_summary.json`.
- `--from-stage assess` re-assesses every record, not only the one you changed.
- `--only` takes a comma-separated list of source ids.
- Scout citations from `scripts/web_search.py` are often `vertexaisearch.cloud.google.com/grounding-api-redirect/...`
  links. Resolve them with Python `urllib.request`, because curl was blocked in the sandbox. A
  JavaScript-rendered page returns only navigation through WebFetch. The Lombardy dataset pages and the
  Eurostat table page did. Read the API endpoint or the export instead.
- A `RemoteProtocolError` from an agent (UC1 risk assessor, two retries, then success) is a transport
  failure. Re-run the stage. Do not change the prompt for it.

## Step 4: Trace audit and one G7 root-cause fix
1. **Find the failures.** Search `outputs/<ID>/trace.jsonl` for `"ok": false`, `"is_error": true`,
   `"refused"`, `"llm_retry"`, and `"kind": "submit"` with `"ok": false`. Each hit names an agent
   (`planner`, `scout`, `risk_assessor`, `memo_writer`, or `profiler__<source_id>`) and a timestamp. Find
   the matching `outputs/<ID>/transcripts/<agent>.json` and read the `tool_result` that follows.
2. **Check each record against its windows.** Open `outputs/<ID>/records/<source_id>.json`. For a
   `public_api`, compare the years in `provenance` and `unknowns` with every window in
   `use_cases/<ID>_*.json`. Each window's start and end must be probed, or listed as unknown. For a
   dataset link, `licence.found_in` must be set whenever `licence.name` is. `sample_findings` must name a
   column. Compare the memo and `discovery_results.json` for the same need: status, gap and verdict must agree.
3. **Classify the mistake before you change anything.** It is one of: a prompt instruction that is missing
   or conditional; a tool description or error message that does not state the required shape; a validator
   or schema rule that is too strict; or a rule in `discovery_agent/risk_rules.py`. Refused hosts, redirects
   off the allowlist and transport retries are not agent mistakes. Record them as findings.
4. **Make one minimal fix.** Edit the prompt, tool description, validator or rule in `discovery_agent/`.
   Never edit a file under `outputs/`. First save copies of `outputs/<ID>/records/<source_id>.json`,
   `discovery_results.json` and `feasibility_memo.md` to a folder outside the repo (for example the system
   temp folder), so the before state survives the re-run.
5. **Re-run from the affected stage.** To re-profile one source:
   `python -m discovery_agent run --use-case <ID> --from-stage profile --stop-after profile --only <source_id> --no-input`.
   Then re-assess: `python -m discovery_agent run --use-case <ID> --from-stage assess --no-input`.
   Then run `python -m pytest tests/ -q`.
6. **Check for regressions.** Re-profile one other source that uses the same agent, and confirm its record
   still meets the Step 4 checks. A prompt change that is not re-tested on a second source is not verified.
7. **Log the fix in `outputs/artifacts/decisions.md`** under the G7 headings: symptom; evidence (trace line
   and transcript line); root cause; the fix (file and the changed sentence); the re-run command; before and
   after (years probed, unknowns, the need's status and gap, the overall verdict); the decision it could
   affect; the related source or test checked.

Pitfalls (observed):
- A conditional instruction lets the agent skip a check it should always make. In UC2 the Nager profiler
  probed 2024 only, and listed 2023, 2025 and 2026 as unknowns, because the prompt said "if coverage is in
  doubt". Changing that to an always-rule gave four years, and moved N4 from `partially_met` to
  `met_with_conditions`.
- Re-assessing changes judgement flags. In UC2 the Nager flags `DQ-UNDOCUMENTED-SCHEMA`,
  `GOV-OWNER-UNKNOWN` and `GOV-PURPOSE-LIMITATION` dropped out, and `COV-GEO-MISMATCH` appeared with
  severity `minor`, while `config/red_flags.json` says `major`. Record every such change. Do not call it an
  improvement without checking it.
- A re-profile can change a grain without a reason. The UC2 Nager record moved from `daily` to `event`.
  The grain rule never compares `event`, so the check was silently turned off. Check `temporal.grain` after
  every re-profile.
- Unsourced claims. A UC2 quality note said Easter dates "match the known Easter Sunday dates by general
  knowledge". That is not a provenance entry. Check every claim in `quality_notes` against a tool call.
- Schema rejections are retried and cost turns. The planner rejected `priority_note` (UC1) and a missing
  `need_id` (UC2). Profilers sent `provenance` as a JSON string and omitted `unknowns` (UC2 Nager,
  Open-Meteo and daily sales). The scout sent `unmet_needs` as a string (UC2). Fix these in the prompt, with
  a one-line example of the required shape.
- Do not look up a `vendor_feed` in the internal catalog. UC1 AtmosData called `get_catalog_entry` and got
  `TOOL_ERROR`. The register entry is its only source.

## Step 5: Memo review, sign-off and self-check
1. **Compare the memo with the results.** Open `outputs/<ID>/feasibility_memo.md`,
   `outputs/<ID>/discovery_results.json` and `outputs/<ID>/records/`. Check that: the overall verdict and the
   number of sources per verdict match the results; each need's status and gap in the memo's coverage table
   match `need_coverage`; each source's red flags in the red-flag register match `sources[].red_flag_details`;
   the memo has its seven sections (executive summary, need coverage, source assessments, red-flag register,
   conditions and owners, recommended next steps, open questions) and the review gate; each count and date
   the memo cites matches a record. Known mismatch: the UC1 memo says "(6 sources)" for feasible with
   conditions, but the results have 7. Do not hand-edit the memo. Note the mismatch in the review, and fix
   the memo writer if it matters.
2. **Write the review.** The human writes `outputs/artifacts/review_<ID>.md`, with the ID in the exact case
   (`review_UC2.md`). The validator checks the name exactly. A lowercase `review_uc1.md` passed only because
   Windows file names are case-insensitive. The review covers: the overall verdict and whether you agree;
   each source's verdict, with the record evidence behind it; each agreement and override in `signoff.json`;
   and the decision (proceed, proceed with conditions, or stop).
3. **Write `outputs/<ID>/signoff.json`.** Start from `outputs/artifacts/_TEMPLATE_signoff.json`. The human
   fills it in. Claude does not write it for the learner. The validator enforces: `reviewer` is not empty;
   `verdict` is `proceed`, `proceed_with_conditions` or `stop`; `proceed_with_conditions` has at least one
   condition, each with `text`, `owner` and `due`; at least one `agreements` or `overrides` entry, each with
   a `reason`; `traced_conclusion.source_id` is a source in `discovery_results.json` with a record file;
   `record_field` is a dotted path that exists in that record (for example `temporal.end`); and
   `could_change_if` is at least 20 characters.
4. **Self-check.** Run `python -m discovery_agent check <ID> > outputs/artifacts/check_<ID>.json`, then read
   the file. The target is `"problems": []`. Do not change the check or the tests to reach it. The
   `trace_stats` in that file cover every run in `trace.jsonl`, so they will not equal `run_summary.json`.
   Record the difference rather than changing either file.
5. **Stop before the next use case.** Do not start another use case until the memo review, `signoff.json`
   and the check all pass. Report the check output and any problems that are still open.

The skill is complete at Step 5. Each step above names its files, commands and checks. A fresh Claude
session given a different use case (a new `use_cases/<ID>_*.json`, brief and internal estate) should be
able to follow Steps 0–5 with a comparable result. If a step only works for UC1 or UC2, or is too vague
to act on, revise it.
