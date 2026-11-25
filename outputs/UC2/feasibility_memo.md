
# UC2 Data Feasibility Memo: Ice-cream sales, weather and holidays

Client: Valdena Gelato Shop (fictional, northern Italy)
As-of date: 2026-10-15
Status: discovery only. No pipeline or profiling has been started.

## 1. Executive summary

**Verdict: not feasible as it stands. Must need N2 (mapping of product codes across the April 2024 code change) is unmet, and no candidate source provides that mapping.**

Facts that drive the verdict:

1. **N2 is unmet.** The wiki (product_codes_2024, last edited 2024-04-02) says that from 2024-04-01 codes ending in "L" were replaced by new codes and that no mapping table exists. The product list (internal.sales.products) holds current codes only, with no effective dates. Without a mapping, the history window cannot be joined on product_code.
2. **The other two must needs are reachable, but only with conditions.** N1 (daily sales by product) comes from the restricted till table, internal.sales.daily_by_product. Access is not yet granted. N3 (daily maximum temperature) comes from the Open-Meteo archive, api.open_meteo_archive. Its licence is mixed and the shop location is not confirmed.
3. **Known sales gap.** The wiki (till_migration_2024) records no sales rows from 2024-02-05 to 2024-03-10. These days must be treated as missing, not zero.
4. **No source is rated not feasible.** All five assessed sources are feasible with conditions. The overall not-feasible verdict rests on N2 being unmet, not on any single source failing.
5. **Should needs are covered but not verified.** N4 (holidays, api.nager_public_holidays) has an unknown data licence. N5 (shop calendar, internal.store.calendar) has not been profiled. Neither is a must need, so neither blocks the verdict on its own.

## 2. Need coverage

| Need ID | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met with conditions | internal.sales.daily_by_product | Restricted access, not yet granted. 2024-02-05 to 2024-03-10 must be treated as missing. Net/gross and sale_date timezone undefined. |
| N2 | Mapping of product codes before and after the 2024 code change | must | **unmet** | internal.sales.products (partial, name-side reference only) | No mapping exists. Retired pre-2024 codes are not in any candidate. Name matching is ambiguous because some names are not unique. |
| N3 | Daily maximum temperature | must | met with conditions | api.open_meteo_archive | Modelled grid-cell data, not the shop's location. Location unconfirmed. Mixed upstream licences need Legal sign-off. Full daily coverage only probed at window edges. |
| N4 | Public holidays in Italy | should | met with conditions | api.nager_public_holidays | National holidays only. Data licence unknown. Easter dates not checked against an official source. |
| N5 | Shop opening days and local events | should | met with conditions | internal.store.calendar | Not profiled. is_open rules undocumented. Access not confirmed. Catalog row count (~1,500) is below the ~1,744 calendar days to 2026-10-10. |

## 3. Source assessments

Order: feasible, then with conditions, then not feasible. No source is rated feasible without conditions, and none is rated not feasible.

### internal.sales.daily_by_product: feasible with conditions
- **What it is (catalog):** Till-system table of units sold and revenue (EUR) per product_code per day. Owner Retail Operations. Catalog states daily grain, coverage from 2022-01-01 (no end date), daily refresh (last 2026-10-14), about 310,000 rows. The row count is unverified. Nothing was sampled.
- **Key flags:**
  - ACC-RESTRICTED (major): auth_required=true, classification confidential, access by request to Retail Operations. Grant status unknown and untested.
  - INT-JOIN-KEY-MISMATCH (major): the 2024 code change breaks the join on product_code (wiki product_codes_2024).
  - DQ-METADATA-CONTRADICTION (minor, judgement): the 2024 till gap is documented in the wiki (till_migration_2024). It is a condition, not a rule flag.
- **Conditions:** Access grant. Treat 2024-02-05 to 2024-03-10 as missing. Confirm whether units_sold and revenue_eur are net of refunds, voids and discounts, and the sale_date cut-off timezone. Build or obtain a code mapping (N2).

### internal.sales.products: feasible with conditions (supporting reference only)
- **What it is (catalog):** Reference list of current product codes, names and categories, about 64 rows, static, owned by Retail Operations. Last metadata update 2025-03-31.
- **Key flags:** INT-JOIN-KEY-MISMATCH (major, judgement). It has no pre-2024 codes and no effective dates.
- **Conditions:** Use only as the name-side reference for a manual mapping. Obtain the retired-code list from Retail Operations. Confirm the table is reachable (not probed) and whether it is shop-specific (geography not documented).
- **Note:** This source does not meet N2 on its own. N2 stays unmet.

### internal.store.calendar: feasible with conditions
- **What it is (catalog):** Daily operational calendar, one row per calendar_date, an is_open flag and free-text event_name. Owner Store Operations. Coverage from 2022-01-01, weekly refresh (last 2026-10-10). Not profiled. No wiki page documents it.
- **Key flags:** DQ-UNDOCUMENTED-SCHEMA (major, judgement). One-line column descriptions only. No population rules for is_open. event_name has no controlled vocabulary.
- **Conditions:** Profile the table to confirm one row per day from 2022. Document how is_open is populated and how the outage days are marked. Confirm access and that coverage reaches 2026-03-31. The weekly refresh may lag the as-of date.

### api.open_meteo_archive: feasible with conditions
- **What it is (catalog and record):** Open-Meteo historical reanalysis API, daily temperature_2m_max (°C) for one latitude/longitude point. Modelled values on a grid cell, not station observations. Owner not stated.
- **Probes:** Confirmed data for 2023-06-01 to 2023-06-03, 2025-06-01 to 2025-06-03 and 2026-03-29 to 2026-03-31. Probe point 45.46, 9.19, snapped to 45.448154, 9.169279 (elevation 138 m).
- **Key flags:**
  - LIC-MIXED (major, rule): upstream sources carry their own terms (Copernicus C3S, DWD CC BY, UK Met Office CC BY-SA). Commercial use of the combined data is not stated.
  - COV-GEO-MISMATCH (major, judgement): the probe point is an unconfirmed assumption. The shop's city is not named in any internal source.
  - LIC-ATTRIBUTION (minor, rule): CC BY 4.0 as stated by provider. Attribution text: "Weather data by Open-Meteo.com, with a link to https://open-meteo.com/".
- **Conditions:** Legal sign-off on commercial use and mixed licences. Shop management confirms the location, and the chosen grid point is recorded in decisions.md. Confirm full daily coverage for 2023-06-01 to 2026-03-31. Set timezone=Europe/Rome in every call. Drop hourly parameters. Agree how reanalysis differs from station data (not validated).

### api.nager_public_holidays: feasible with conditions
- **What it is (catalog and record):** REST API (v3) listing public holidays for one country and year (IT). Returns date, names, fixed and global flags, counties and type. Probes for 2023 to 2026 returned HTTP 200. National holidays only. Regional and patron-saint days are not represented. Owner not stated.
- **Key flags:**
  - LIC-UNKNOWN (blocker for production, rule): licence name null, commercial use unknown. The only licence found is MIT, which covers the software. Register agreement status is "not_required_open_data".
  - COV-GEO-MISMATCH (minor, judgement): national only. Local holidays are handled under N5.
- **Conditions:** Legal or the publisher establishes the data licence before production use. Verify Easter-linked dates (2023-04-09, 2024-03-31, 2025-04-20, 2026-04-05) and the national list against an official Italian source. Explain the 14th record in the 2026 response (not inspected). Confirm v3 is the endpoint used. v4 is not registered or assessed.

## 4. Red-flag register

| Source ID | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.sales.daily_by_product | ACC-RESTRICTED | major | auth_required=true; confidential; request to Retail Operations; grant status unknown | rule |
| internal.sales.daily_by_product | INT-JOIN-KEY-MISMATCH | major | 2024 code change; no mapping table (wiki product_codes_2024) | judgement |
| internal.sales.daily_by_product | DQ-METADATA-CONTRADICTION | minor | 2024-02-05 to 2024-03-10 no rows (wiki till_migration_2024); recorded as condition | judgement |
| internal.sales.products | INT-JOIN-KEY-MISMATCH | major | current codes only; no effective dates; retired codes not present | judgement |
| internal.store.calendar | DQ-UNDOCUMENTED-SCHEMA | major | one-line descriptions; no is_open population rules; no wiki page | judgement |
| api.open_meteo_archive | LIC-MIXED | major | mixed_sources=true; upstream licences; commercial use not stated | rule |
| api.open_meteo_archive | COV-GEO-MISMATCH | major | assumed point 45.448154, 9.169279; shop location unconfirmed | judgement |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0; attribution text required | rule |
| api.nager_public_holidays | LIC-UNKNOWN | blocker (production) | licence name null; commercial use unknown; only MIT software licence found | rule |
| api.nager_public_holidays | COV-GEO-MISMATCH | minor | national holidays only | judgement |

Rule warnings: none.

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve | Blocking which need |
|---|---|---|---|
| Build or obtain a pre-2024 to post-2024 product code mapping, including retired codes and names | internal.sales.daily_by_product; internal.sales.products | Retail Operations | N2 (must); N1 history use on product_code |
| Grant warehouse SQL access to analytics | internal.sales.daily_by_product | Retail Operations | N1 (must) |
| Confirm net/gross treatment (refunds, voids, discounts) and sale_date timezone | internal.sales.daily_by_product | Retail Operations | N1 (must), in its definition |
| Treat 2024-02-05 to 2024-03-10 as missing, not zero | internal.sales.daily_by_product | Analytics team, agreed with Retail Operations | N1 (must) |
| Confirm shop location and record grid point in decisions.md | api.open_meteo_archive | Valdena shop management | N3 (must) |
| Legal sign-off on mixed upstream licences and commercial use; attribution shown | api.open_meteo_archive | Legal | N3 (must) |
| Confirm full daily coverage 2023-06-01 to 2026-03-31; set timezone Europe/Rome | api.open_meteo_archive | Analytics team | N3 (must) |
| Establish holiday data licence before production use | api.nager_public_holidays | Legal or publisher | N4 (should); production use |
| Verify Easter and national holiday dates against an official source; explain 2026 14th record; confirm v3 | api.nager_public_holidays | Analytics team | N4 (should) |
| Profile table; document is_open rules and outage marking; confirm access and coverage to 2026-03-31 | internal.store.calendar | Analytics team; Store Operations | N5 (should) |
| Confirm the products table is reachable and shop-specific | internal.sales.products | Retail Operations | N2 (partial support) |

## 6. Recommended next steps

1. **Raise an access request** to Retail Operations for warehouse SQL on internal.sales.daily_by_product, and record the outcome.
2. **Ask Retail Operations for the retired pre-2024 product code list** with names, and whether a mapping exists or can be built. Treat this as the gate for N2. If it is produced, it becomes a new source and must be assessed separately.
3. **Ask Retail Operations to define** net/gross treatment and the sale_date timezone.
4. **Decide the shop location** for N3 and record it in decisions.md. The probe point (45.46, 9.19) is an assumption and must be confirmed or replaced.
5. **Ask Legal** for sign-off on Open-Meteo mixed licences and commercial use, and on the Nager data licence. Note the Open-Meteo attribution text as a required output.
6. **Ask Store Operations** for documentation of is_open and outage-day marking, and for confirmation of access and coverage to 2026-03-31.
7. **Decision for the owner:** whether to proceed with N1 and N3 on the history window without N2 (for example, aggregate-level analysis that does not need product-level joins), or to hold until the mapping exists. This decision is not made in this memo.
8. **Once the gate is passed**, profile in this order: (a) sales daily coverage, row counts and the 2024 gap; (b) calendar one-row-per-day check; (c) Open-Meteo coverage across the full window; (d) holiday list against an official source.

## 7. Open questions for the human reviewer

1. Does Retail Operations hold a retired-code mapping for the April 2024 change, or can one be built? Without it, N2 stays unmet and the verdict stands.
2. Which city or location is the shop in? Only coordinates are recorded, and no internal source names the city. Who will confirm them?
3. Will the owner accept a product-level analysis that excludes the pre-2024 history if N2 cannot be met?
4. Has Legal been asked to sign off on the Open-Meteo mixed licences and the Nager data licence? If yes, what is the outcome?
5. Is access to internal.sales.daily_by_product and internal.store.calendar already granted to the analytics team? The discovery did not test it.
6. Are units_sold and revenue_eur net or gross of refunds, voids and discounts? Does sale_date use local time?
7. Does the register's "production approved" status for Open-Meteo already cover commercial use, or is it still pending Legal?

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-25T10:21:26Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- api.nager_public_holidays: LIC-UNKNOWN

**Open questions:**

1. Does Retail Operations hold a retired-code mapping for the April 2024 product code change, or can one be built? Without it, N2 stays unmet and the not-feasible verdict stands.
2. Which city or location is the shop in? Only coordinates (45.46, 9.19, snapped to 45.448154, 9.169279) are recorded, and no internal source names the city. Who confirms them?
3. Will the owner accept a product-level analysis that excludes the pre-2024 history if N2 cannot be met?
4. Has Legal been asked to sign off on the Open-Meteo mixed upstream licences and commercial use, and on the Nager holiday data licence? What was the outcome?
5. Is access to internal.sales.daily_by_product and internal.store.calendar already granted to the analytics team? The discovery did not test it.
6. Are units_sold and revenue_eur net or gross of refunds, voids and discounts? Does sale_date use local time, and what is the cut-off?
7. Does the register's 'production approved' status for Open-Meteo already cover commercial use, or is it still pending Legal?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
