# AI-Native Data Discovery — Assignment Walkthrough

## 1. Setup & Tooling (`Step 0` & `scripts/web_search.py`)
- Configured the local Python 3.11 environment and verified gateway environment variables (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` using `claude-haiku-5-5`) without logging credentials.
- Built `scripts/web_search.py` to query grounded web search for Step 2b dataset discovery and return structured citations, resolving Google grounding redirect URLs via Python `urllib.request` where sandboxed `curl` or JS-rendered pages returned incomplete HTML.
- Verified offline tool behavior (`search_internal_catalog`, `inspect_dataset_link`, `list_external_register`) before running live LLM stages.

## 2. Closing the Learner Gaps (`G1`–`G6`)
- **G1 (`extract_licence`):** Implemented extraction across JSON-LD metadata, licence links, and body text sentences, ignoring `"Unknown"` JSON-LD placeholders when a concrete licence link (such as `CC BY 4.0`) appears elsewhere on the page.
- **G3 (`jsonstat_summary`):** Updated JSON-stat parsing to count only non-null cells in list- and dict-form `value` payloads, calculating `missing_cells = expected_cells - value_count` and raising `MISSING_CELLS` when gaps are present.
- **G4 (Temporal & grain rules):** Implemented deterministic checks comparing source coverage windows and temporal grain against each need's `min_grain` and target windows.
- **G5 (Verdict calibration):** Added 8 numbered calibration rules in `discovery_agent/prompts/risk_assessor.md` aligning `blocker`, `major`, and `minor` flag severities with `must`/`should`/`could` need priorities, window types (`prototype` vs. `production`), and rule vs. judgement flag origins.
- **G6 (`config/allowlist.json`):** Added exact hosts `ec.europa.eu` (Eurostat `sdg_11_52`) and `www.dati.lombardia.it` (accepted Step 2b Lombardy air-sensor dataset), while deliberately keeping `catalog.data.gov` off the allowlist so the out-of-scope Chicago link produces the expected `DOMAIN_NOT_ALLOWLISTED` guardrail finding.
- After implementing `G1`–`G6`, all **52/52** offline tests in `tests/` passed (`outputs/artifacts/pytest_after.txt`).

## 3. Use Case 1 (`UC1` — Valdena Civic Health Office)
- **Step 2b source suggestions:** Searched for Italian air-quality datasets to supplement `N1`, accepting `https://www.dati.lombardia.it/Ambiente/Dati-sensori-aria/nicp-bhqi` (ARPA Lombardia / Regione Lombardia air sensors, `CC0 1.0` in JSON-LD) and rejecting `https://www.dati.lombardia.it/d/ib47-atvt` (static station metadata without pollutant concentration readings). Recorded both decisions in `outputs/artifacts/decisions.md` and `outputs/UC1/gate_decisions.json`.
- **Pipeline outcome (`feasible_with_conditions`):**
  - Historical prototype modeling (`N1`) is viable using `link.uci_360` (2004–2005 hourly Italian sensor data, subject to `-200` sentinel handling and single-site limits) and `link.lombardia_nicp_bhqi_eba0c8` (subject to schema and coverage verification).
  - External register weather (`api.open_meteo_archive`) and holiday (`api.nager_public_holidays`) APIs support context/modelling needs (`N3`, `N4`, `N5`) once location and licence conditions are cleared, while `link.europa_sdg_11_52_099aa6` covers annual mortality context (`N6`, `could` need).
  - Two sources were rated `not_feasible`: `link.data_open_air_chicago_hour_aggre_d4970b` (blocked off-allowlist and outside Italy) and `vendor.atmosdata_pro` (expired vendor contract and revoked API key).
- **Human gate (`proceed_with_conditions`):** Signed off in `outputs/UC1/signoff.json` and `outputs/artifacts/review_UC1.md` with explicit conditions on production data sourcing, Legal sign-off, and `-200` sentinel cleaning. `python -m discovery_agent check UC1` passed with `"problems": []`.

## 4. Use Case 2 (`UC2` — Valdena Gelato Shop) & `G7` Root-Cause Fix
- **Assumptions & setup:** Updated `config/external_sources_register.json` default coordinates for `api.open_meteo_archive` from Lisbon to Milan (`45.46, 9.19`) as a documented northern Italy location assumption in `outputs/artifacts/decisions.md`. UC2 required no external dataset links.
- **G7 agent failure found & fixed:**
  - **Symptom & root cause:** In the initial UC2 run, `profiler__api.nager_public_holidays` probed only `2024` and left `2023`, `2025`, and `2026` unprobed (`N4` rated `partially_met`) because `discovery_agent/prompts/profiler.md` line 7 instructed the profiler to probe window ends only `"if coverage is in doubt"`.
  - **Fix & verification:** Changed `discovery_agent/prompts/profiler.md` line 7 so `public_api` profilers always probe the start and end of every target window (and every calendar year touched by year-based endpoints). Re-running `profile` on `api.nager_public_holidays` and `assess` probed all four target years (`2023`–`2026`, HTTP 200) and moved `N4` from `partially_met` to `met_with_conditions` with all 52 tests passing.
- **Pipeline outcome (`not_feasible` / `stop`):**
  - Must-need `N2` (product-code mapping across the 2024 `"L"` code change) is `unmet`: `wiki/product_codes_2024.md` confirms no mapping table exists, `internal.sales.products` holds current codes only without effective dates, and product names are not unique.
  - `internal.sales.daily_by_product` (`N1`) also has confidential/untested access, undocumented VAT/timezone rules, and a `2024-02-05` to `2024-03-10` till migration gap (`wiki/till_migration_2024.md`) that must be treated as missing rather than zero.
  - In `outputs/UC2/signoff.json` (`verdict: "stop"`) and `outputs/artifacts/review_UC2.md`, I overruled treating `api.nager_public_holidays` as `feasible_with_conditions` for production due to its unresolved `LIC-UNKNOWN` blocker and unverified Easter/2026 holiday dates. `python -m discovery_agent check UC2` passed with `"problems": []`.

## 5. What Worked vs. What Needed Care
- **What worked well:** Separating deterministic Python rule checks (`risk_rules.py`, `validation.py`) from LLM reasoning kept schema validation, allowlist guardrails, and window/grain checks reproducible across runs.
- **Friction & edge cases observed:**
  - Re-profiling and re-assessing a single source (`api.nager_public_holidays`) caused non-rule judgement flags to shift across runs (`DQ-UNDOCUMENTED-SCHEMA`, `GOV-OWNER-UNKNOWN`, and `GOV-PURPOSE-LIMITATION` dropped; `COV-GEO-MISMATCH` appeared as `minor` despite `major` in `config/red_flags.json`) and shifted `temporal.grain` from `daily` to `event`. Checking records against `discovery_results.json` during human review caught these nuances.
  - Agents occasionally triggered schema validation retries on first submission (e.g., omitting `unknowns` or passing JSON strings) before self-correcting on retry; transport retries (`RemoteProtocolError`) also occurred once during UC1 assessment and succeeded without prompt edits.
  - JavaScript-rendered open-data portals (Lombardy and Eurostat) only returned page navigation via HTML fetch, requiring direct inspection of their JSON/JSON-stat endpoints.

## 6. Skill Extension & Fresh-Session Reuse Check (`SKILL.md`)
- Extended `skills/data-discovery-agent/SKILL.md` and `.claude/skills/data-discovery-agent/SKILL.md` with concrete **Steps 3–5** (candidate gate, allowlist/test checks, pipeline commands, trace audit & G7 root-cause fix workflow, and human memo review/sign-off/self-check).
- Tested the updated skill in a brand-new Claude Code session on `UC2` (Steps 0–2b) using `--out` to write to a scratch directory without modifying validated outputs. The fresh session verified the environment, validated the UC2 contract, ran `plan` and `scout` (7 LLM calls, 0 tool errors), surfaced the `N2` product-code mapping gap, and stopped cleanly at the candidate gate. Based on its feedback, I added two final clarifications to `SKILL.md` (noting that all 52 tests pass once `G1`–`G6` are complete, and documenting `--out <dir>` for scratch reuse checks).