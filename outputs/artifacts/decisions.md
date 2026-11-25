# Decisions log

## Source suggestions (Step 2b)
One row per suggestion you accepted, rejected or revised, with your reason. Use the page's own wording for the reason.

| Suggestion (publisher, URL) | Need, window | Decision | Reason |
|---|---|---|---|
| Regione Lombardia open data / ARPA Lombardia, [https://www.dati.lombardia.it/Ambiente/Dati-sensori-aria/nicp-bhqi](https://www.dati.lombardia.it/Ambiente/Dati-sensori-aria/nicp-bhqi) | N1, prototype | accept | Official ARPA Lombardia / Regione Lombardia air-sensor dataset returned by search citation; coverage dates, pollutant grain (hourly vs daily PM2.5), and CC0 terms need verification through the profiler once www.dati.lombardia.it is allowlisted in G6. |
| Regione Lombardia open data, [https://www.dati.lombardia.it/d/ib47-atvt](https://www.dati.lombardia.it/d/ib47-atvt) | N1, prototype | reject | Static station/sensor metadata table without pollutant concentration readings (N1), and not returned directly as a search citation URL. |

Inspected through the workflow (at least one accepted extra source): `link.lombardia_nicp_bhqi_eba0c8` (`https://www.dati.lombardia.it/Ambiente/Dati-sensori-aria/nicp-bhqi`) — accepted in Step 2b, allowlisted under `www.dati.lombardia.it` in G6, and profiled through the UC1 workflow as `feasible_with_conditions` (`CC0 1.0` in JSON-LD; prototype `N1` candidate pending data-dictionary and `2004–2005` coverage verification).

## G1 and G3: one edge case in each function
- **G1, `extract_licence`**: a JSON-LD licence that says `"Unknown"` (the Kaggle fixture: `{"name": "Unknown", "url": ""}`). The code treats "Unknown" as no licence, so `licence_name` is None, but it does not stop there. It keeps looking at licence links and licence sentences, and returns the JSON-LD hit (`found_in: "json-ld"`, snippet = the JSON value) only when nothing else in the page names a licence. Effect on the `licence` field: a page that says "Unknown" in its metadata but links to CC BY 4.0 in its body gets `CC BY 4.0`, not a false LIC-UNKNOWN blocker. A page with no licence anywhere still gets LIC-UNKNOWN.
- **G3, `jsonstat_summary`**: a `null` inside a list-form `value` array. The code counts only non-null values, so the `null` is a missing cell, not a value. Effect on the summary: `value_count` excludes it, `missing_cells` is `expected_cells - value_count` (1 in the test case), and `MISSING_CELLS` is raised. The same rule applies to dict-form values, where absent keys are missing cells.

## G4–G5: feasible for one need or window, not another
- **Source and the rule or calibration decision:** `link.uci_360` (UCI Air Quality, serving `N1` across `prototype` and `production`) and `link.europa_sdg_11_52_099aa6` (Eurostat `sdg_11_52`, serving `N6` as a `could` need), evaluated under temporal/grain rules (G4) and the 8 numbered verdict calibration rules in `prompts/risk_assessor.md` (G5).
- **Feasible for (need, window), and why:** `link.uci_360` is `feasible_with_conditions` for `N1` in the `prototype` window (`2004-03-10` to `2005-04-04`, hourly data) because it covers that historical window for method building once `-200` sentinels are handled and single-site scope is accounted for. `link.europa_sdg_11_52_099aa6` is `feasible_with_conditions` for `N6` (`could` need) as annual national PM2.5 mortality context across `2005` and `2007–2023` per rule 2 (`could` needs with a blocker do not automatically force `not_feasible`).
- **Not feasible for (need, window), and why:** `link.uci_360` is not usable for the `production` window (`2024-01-01` to `2025-12-31`) because its data ends on `2005-04-04` (`FRS-STALE`), is single-site, and carries a `CC BY 4.0` vs research-only conflict. `link.europa_sdg_11_52_099aa6` has `0.00` coverage in the production window and misses `2004` in the prototype window.
- **Reason for each red flag you dismissed:** No red flag was dismissed without justification: `LIC-UNKNOWN` on `link.europa_sdg_11_52_099aa6` does not block `UC1` because `N6` is a `could` need; `ACC-UNREACHABLE` on `link.data_open_air_chicago_hour_aggre_d4970b` reflects the intentional `catalog.data.gov` allowlist refusal; and `FRS-STALE` on `link.uci_360` is accepted only for historical prototype work, not production.

## G6: Allowlist changes

- **Added `ec.europa.eu`:** Exact host required to fetch and inspect the prescribed Eurostat `sdg_11_52` JSON-stat API endpoint for annual PM2.5 premature deaths in Italy (`N6`).
- **Added `www.dati.lombardia.it`:** Exact host required to inspect the accepted Step 2b Regione Lombardia / ARPA Lombardia air-sensor dataset (`nicp-bhqi`) for Italian air-quality monitoring (`N1`).
- **Excluded `catalog.data.gov`:** Kept off the allowlist because the Chicago link covers a US city outside UC1's Italian geographic scope, and keeping it blocked preserves the expected `DOMAIN_NOT_ALLOWLISTED` guardrail finding.
- **Excluded rejected Step 2b dataset (`dati.lombardia.it/d/ib47-atvt`):** Rejected during Step 2b because it contains only static station/sensor metadata without pollutant concentration readings (`N1`).


## G5: Verdict calibration
- **What you changed in `prompts/risk_assessor.md`, and the reasoning behind each rule:** Replaced the `LEARNER TODO (G5)` note with 8 numbered calibration rules under `## Verdict calibration` using `blocker`, `major`, and `minor` severities from `config/red_flags.json`, `must`/`should`/`could` priorities, `prototype` vs `production` windows, and rule vs judgement flag origins. Rules 1–2 keep `could`-need blockers from over-penalising non-essential sources while keeping `must`-need blockers strict unless a named owner/allowlist action clears them; rules 3–4 separate major/minor flags from `not_feasible` verdicts; rules 5–7 handle `FRS-STALE`, `COV-PARTIAL-WINDOW`, and `COV-GRAIN-MISMATCH` by window and need priority; rule 8 caps judgement flags at moving a verdict one step (never alone to `not_feasible`) and ignores dismissed rule flags.
- **Verdicts that changed after you re-ran `--from-stage assess` (source: before → after, why):** The `UC1` `profile` -> `assess` -> `memo` run produced `discovery_results.json` and `feasibility_memo.md` directly with the 8 calibration rules active (`overall_verdict: feasible_with_conditions`; 7 sources `feasible_with_conditions` and 2 sources `not_feasible`: `link.data_open_air_chicago_hour_aggre_d4970b` and `vendor.atmosdata_pro`); no separate prior pre-G5 `UC1` assessment baseline was saved to compare a before-to-after diff.

## G7 — Agent failure fixed

- **Symptom:** In UC2, the profiler for `api.nager_public_holidays` only probed calendar year `2024` even though UC2's target windows (`history`: `2023-06-01` to `2025-05-31`, `recent`: `2025-06-01` to `2026-03-31`) span four calendar years (`2023`, `2024`, `2025`, `2026`). As a result, `N4` was reported as `partially_met` with `"2023, 2025, 2026 not probed"`.
- **Evidence:** `outputs/UC2/trace.jsonl` line 67 showed only one successful `call_public_api` call (`year=2024, country=IT`), and `outputs/UC2/transcripts/profiler__api.nager_public_holidays.json` (near line 255) explicitly noted `"Only the 2024 IT call was made; 2023, 2025 and 2026 coverage not probed."`
- **Root cause:** `discovery_agent/prompts/profiler.md` line 7 instructed the profiler to probe both ends of needed windows only `"if coverage is in doubt"`. Because the profiler assumed coverage was not in doubt after `2024` succeeded, it skipped the remaining target years.
- **Fix:** Updated line 7 of `discovery_agent/prompts/profiler.md` so that for every `public_api` candidate, the profiler always probes the start and end of each target window (and for year-based endpoints, every calendar year touched by a target window) even when coverage looks complete, recording each probed year in `provenance` and any unprobed year in `unknowns`.
- **Re-run commands:**
  - `python -m discovery_agent run --use-case UC2 --from-stage profile --stop-after profile --only api.nager_public_holidays --no-input`
  - `python -m discovery_agent run --use-case UC2 --from-stage assess --no-input`
- **Measured before / after:**
  - Years probed (`api.nager_public_holidays`): `1` (`2024`, trace line 67) -> `4` (`2023`, `2024`, `2025`, `2026`, trace lines 92–98; all HTTP 200).
  - Record unknowns: `"Coverage for years other than 2024 (2023, 2025, 2026 not probed)"` removed.
  - `N4` status in `outputs/UC2/discovery_results.json`: `partially_met` -> `met_with_conditions` (gap no longer cites unprobed years; `feasibility_memo.md` updated to `"Probes for 2023 to 2026 returned HTTP 200."`).
  - Overall UC2 verdict: unchanged (`not_feasible`, because must-need `N2` remains unmet).
- **Project decision affected:** Confirms `api.nager_public_holidays` actually serves all four target years for `N4`, narrowing the remaining decision to clearing `LIC-UNKNOWN` (or substituting an official Italian holiday calendar) rather than treating multi-year API coverage as an open risk.
- **Regression check:** Ran `python -m pytest tests/ -q` (`52 passed in 1.66s`). Also noted during review that the re-run shifted `temporal.grain` from `daily` to `event` and changed non-rule judgement flags on Nager (`DQ-UNDOCUMENTED-SCHEMA`, `GOV-OWNER-UNKNOWN`, `GOV-PURPOSE-LIMITATION` dropped; `COV-GEO-MISMATCH` added as `minor`), which I kept in mind during the UC2 memo review.

## Other decisions
- **Open-Meteo coordinates (`config/external_sources_register.json`):** Changed `api.open_meteo_archive` `default_query` coordinates from Lisbon (`latitude: "38.72"`, `longitude: "-9.14"`) to **Milan, northern Italy (`latitude: "45.46"`, `longitude: "9.19"`)**. Both `UC1` (Valdena Civic Health Office) and `UC2` (Valdena Gelato Shop) are fictional clients located in northern Italy (`geography.primary: ["IT"]`) without a named municipality in the internal catalog or wiki; Milan is the primary metropolitan hub in northern Italy and provides representative regional weather reanalysis coverage for both use cases.
