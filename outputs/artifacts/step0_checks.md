# Step 0 checks

Model id in use: `claude-haiku-5-5` (from `ANTHROPIC_MODEL`)
Gateway variables: `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL` all set (values not recorded).
Python: 3.11.3, existing `.venv`, `requirements.txt` installed.

## Offline tests (`python -m pytest <file> -q`)

| File | Result |
|---|---|
| `tests/test_tools_offline.py` | 24 passed, 0 failed |
| `tests/test_agent_loop.py` | 7 passed, 0 failed |
| `tests/test_learner_gaps.py` | 1 passed, 20 failed (expected until G1, G3, G4, G5, G6 are implemented) |

Failing gap tests by gap:
- G1 (terms and licence extraction): 9 failures (UCI page, Zenodo JSON-LD, Kaggle unknown licence, JSON-LD variants, text and links variants)
- G3 (Eurostat response and list values): 2 failures
- G4 (window coverage, grain, metadata contradiction, evaluate skipped rules): 7 failures
- G5 (calibration rules): 1 failure
- G6 (`ec.europa.eu` allowlisted): 1 failure

## Tool smoke tests (UC1)

- `search_internal_catalog` ("air quality PM2.5 monitoring"): returns JSON with hits, including `airq.station_readings` (catalog) and the station network wiki page.
- `inspect_dataset_link` (UCI `archive.ics.uci.edu/dataset/360/air+quality`): returns JSON with `link_type: uci_dataset_page`, `canonical_ref: uci:360`, and metadata.
- `list_external_register` (UC1): returns JSON; includes `policy.open_data_links` (open-data policy for analyst-supplied links).

No tracebacks. No `DOMAIN_NOT_ALLOWLISTED` result in these three calls.
