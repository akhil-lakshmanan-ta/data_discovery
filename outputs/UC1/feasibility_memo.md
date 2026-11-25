
# UC1 Feasibility Memo: Air quality and traffic (Valdena Civic Health Office)

As of 2026-10-15. Draft from discovery outputs. No pipeline or model is proposed here.

## 1. Executive summary

Overall verdict: **feasible with conditions.** All three must needs (N1 air quality, N2 traffic, N3 temperature and humidity) are met only with conditions. None is met cleanly today.

Facts that drive the verdict:

1. **Prototype (2004-03-10 to 2005-04-04) can start now, on public data.** The UCI 360 file (`link.uci_360`) is the only candidate that covers the whole prototype window with NO2 reference, temperature and humidity. It has heavy -200 sentinel coding, a licence conflict (CC BY 4.0 versus "research purposes only"), and single-site representativeness. It is for method building only.
2. **Production (2024-01-01 to 2025-12-31) depends on the city's own data, which is not yet accessible.** The station feed (`internal.airq.station_readings`) and the traffic counts (`internal.traffic.hourly_counts`) both have open access requests or untested access. The clinic table (`internal.clinic.resp_visits_daily`) is limited by policy to daily district counts.
3. **Two production-window breaks sit inside the window.** Traffic counter replacement on 2024-03-18 changed how counts are recorded, and the wiki says not to compare across it without adjustment. Station VR-03 stopped reporting on 2024-06-30, and the catalog still lists the network as active.
4. **Temperature and humidity for production rest on a model, not on station data.** Open-Meteo returned hourly values at probe level, but it is reanalysis. Its licence is mixed and its location point is not confirmed. The only station-grade vendor feed (`vendor.atmosdata_pro`) is not usable: the agreement expired, the key was revoked and there is no licence.
5. **Two sources are out.** The Chicago link (`link.data_open_air_chicago_hour_aggre_d4970b`) is on a non-allowlisted host, has no licence, and covers the wrong geography. The AtmosData feed is blocked by its contract status. Neither is needed to meet a must need.

## 2. Need coverage

| Need id | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations (NO2, PM2.5) | must | met with conditions | Production: `internal.airq.station_readings`. Prototype: `link.uci_360`; `link.lombardia_nicp_bhqi_eba0c8` (unverified for prototype) | Production access pending. VR-03 closed from 2024-06-30 and the catalog conflicts with the wiki. UCI has -200 sentinels and a licence conflict. ARPA Lombardia has no evidenced coverage for 2004-2005 and no pollutant mapping. |
| N2 | Hourly vehicle traffic near monitoring stations | must | met with conditions | `internal.traffic.hourly_counts` | Counter break on 2024-03-18 is unadjusted. Counter proximity to stations is undocumented. Time zone is not stated. Access is untested. |
| N3 | Hourly temperature and humidity | must | met with conditions | `api.open_meteo_archive` (both windows); `link.uci_360` (prototype only) | Open-Meteo is model reanalysis, not station data. Its point and licence are unconfirmed. No station-grade production source is available. |
| N4 | Daily respiratory clinic visits by district | should | met with conditions | `internal.clinic.resp_visits_daily` | Purpose fit for a live warning is not confirmed. District code system, small-cell suppression and district-to-station mapping are missing. |
| N5 | Patient-level clinic visit records | could | unmet | none | No candidate provides it. The clinic data policy allows only daily district counts. |
| N6 | National yearly context: PM2.5 deaths | could | partially met | `link.europa_sdg_11_52_099aa6` | Only 2005 falls in the prototype window. 2004 is absent. No production-window years (data ends 2023). Licence unknown. |

## 3. Source assessments

Verdicts are: feasible with conditions (6 sources), then not feasible (2 sources). No source is feasible without conditions.

### internal.airq.station_readings
- **What it is:** Hourly NO2 and PM2.5 from the city's own stations, keyed by station code and UTC hour. Owned by the Environment Monitoring Unit. Catalog shows about 4.2 million rows, coverage from 2023-01-01 with no end date, and hourly refresh (last refreshed 2026-10-14).
- **Verdict:** Feasible with conditions. Only source for N1 in production.
- **Key flags:**
  - ACC-RESTRICTED (major): authentication required, internal classification. No access request record or approval found in the wiki or catalog.
  - GOV-CATALOG-WIKI-CONFLICT (major): the wiki (last edited 2024-07-01) says VR-03 (Via Roma) was switched off on 2024-06-30. The catalog still says active.
- **Conditions:** Environment Monitoring Unit approves access and confirms warehouse reachability. Confirm VR-03 status and choose how to handle the gap (exclude or impute). Confirm the PM2.5 method, validation flags and per-station coverage. Catalog status to be corrected.
- **Cannot serve the prototype window.**

### internal.traffic.hourly_counts
- **What it is:** Hourly vehicle counts per road counter (counter_id, local timestamp, vehicles). Owned by the Mobility Office, stewarded by Luca Ferri. About 15 million rows, coverage from 2021-01-01, open-ended, hourly refresh (catalog metadata dated 2026-10-12).
- **Verdict:** Feasible with conditions. Only source for N2.
- **Key flags:**
  - GOV-CATALOG-WIKI-CONFLICT (major): the wiki (last edited 2024-04-02) says counts are per direction before 2024-03-18 and combined after. It says not to compare across the change without adjustment. The catalog does not mention this.
  - INT-NO-JOIN-KEY (major): no coordinates, station mapping or sensor metadata. Proximity to stations is not established.
  - DQ-DST-ARTEFACTS (minor): timestamps are "local time (zone not stated)". No DST handling documented. Join to UTC air data unverified.
- **Conditions:** Mobility Office documents the counter-break handling and updates the catalog. Provide counter coordinates or a counter-to-station mapping. Data lead confirms time zone and DST and converts to UTC. Mobility Office tests access and completeness for 2024-2025, since access was not tested.

### api.open_meteo_archive
- **What it is:** Open-Meteo Historical Weather API, reanalysis. Hourly temperature_2m and relative_humidity_2m in UTC. Probed at 45.46, 9.19; the grid point returned was 45.448154, 9.169279 (Milan area, elevation 138 m). Both probe windows (2004-03-10 to 2004-03-12 and 2024-01-01 to 2024-01-02) returned data. Coverage confirmed at probe level only. Last-modified date on the licence page is unverified.
- **Verdict:** Feasible with conditions. Only production source for N3.
- **Key flags:**
  - LIC-MIXED (major): the API data is listed as CC BY 4.0. The underlying Copernicus C3S reanalysis has its own licence, which was not read. Commercial-use position unknown.
  - COV-GEO-MISMATCH (major): the probe point is in the Milan area. Valdena is not located in any source read.
  - LIC-ATTRIBUTION (minor): attribution "Weather data by Open-Meteo.com" is required.
  - FRS-METADATA-DATE-MISLEADING (minor): licence page shows "Last modified: 24 Nov 2026", after the as-of date.
- **Conditions:** Legal confirms C3S terms and commercial-use position before production use. Client confirms the Valdena point and records it in decisions.md. Data engineering runs full-range missing-value checks on both windows. Attribution goes into outputs; Legal signs off for production under the open-data links policy.
- **Refresh cadence and owner are unknown.**

### link.uci_360
- **What it is:** UCI 360 Air Quality. Single-site, hourly, multisensor data from an unnamed Italian road-level site. Pairs five sensor responses with reference CO, NMHC, benzene, NOx and NO2, plus T, RH and AH. Whole-file sample: 9,357 rows, 2004-03-10 to 2005-04-04. No traffic data.
- **Verdict:** Feasible with conditions. Prototype only.
- **Key flags:**
  - GOV-PURPOSE-LIMITATION (major): notes say "exclusively for research purposes. Commercial purposes are fully excluded." This conflicts with the CC BY 4.0 licence on the same page. Not resolved in any source.
  - DQ-METADATA-CONTRADICTION (major): metadata says no missing values, but notes say missing values are tagged -200. The sample confirms -200.
  - DQ-SENTINEL-VALUES (major): NMHC(GT) about 90% of rows; CO(GT) about 17%; NOx(GT) and NO2(GT) about 17% each.
  - INT-REPRESENTATIVENESS (major): one site, no station id, coordinates or district.
  - FRS-STALE (major, kept): data ends 2005-04-04. Acceptable for method build. Not acceptable for production.
  - LIC-ATTRIBUTION (minor): citation required (De Vito et al., 2008; DOI 10.24432/C59K5F).
- **Conditions:** Legal resolves the CC BY vs research-only conflict. Use is limited to research and method building. It must not feed a production clinical or commercial warning. Set -200 to null. Use for method build only, not to generalise to city stations. Keep the citation.

### link.lombardia_nicp_bhqi_eba0c8
- **What it is:** ARPA Lombardia fixed-station sensor readings, published on the Regione Lombardia open data portal (dataset nicp-bhqi). Export has one row per sensor per timestamp: sensor id, timestamp, value, validity code, operator id. No pollutant, station or coordinate columns. Licence CC0 1.0 per the record.
- **Verdict:** Feasible with conditions. Possible prototype candidate for N1, but not yet counted.
- **Key flags:**
  - DQ-SENTINEL-VALUES (major): the sample has value -9999 in about 4.5% of rows, with status "NA" on the same rows.
  - DQ-UNDOCUMENTED-SCHEMA (major): Italian headers only. No unit, pollutant or sensor map. No data dictionary read.
  - FRS-METADATA-DATE-MISLEADING (minor): dateModified 2026-11-24 is after the as-of date. Datepublished 2017-11-20.
- **Conditions:** Obtain the full dataset description and dictionary. Establish historical coverage, and confirm whether any of it overlaps 2004-03-10 to 2005-04-04. This is currently unverified. Remove sentinel rows. Legal sign-off needed for production use. Current policy places it in prototyping and context only.

### internal.clinic.resp_visits_daily
- **What it is:** Respiratory clinic visit counts by day and district (visit_date, district, visit_count). Owned by Clinical Analytics, stewarded by Chiara Conti. About 40,000 rows. Coverage from 2022-01-01, open-ended, daily refresh (last refreshed 2026-10-14). Declared aggregated, with no patient identifiers.
- **Verdict:** Feasible with conditions. Only source for N4. Production window is inside coverage.
- **Key flags:**
  - ACC-RESTRICTED (major): authentication required, internal. Request goes to Clinical Analytics.
  - GOV-PURPOSE-LIMITATION (major): the wiki clinic data policy (owner Data Protection Office, last edited 2025-02-01) allows only this daily district count table for this purpose. Whether a live patient-warning use falls within the surveillance purpose is not confirmed.
  - INT-JOIN-KEY-MISMATCH (major): district coding is undocumented (string). District of residence does not map to station or counter ids.
- **Conditions:** Data Protection Office confirms the purpose and whether further sign-off is needed. Clinical Analytics documents the district code system, small-cell suppression and zero-day handling. Data lead with GIS builds a district-to-station/counter mapping before any joint analysis.

### link.europa_sdg_11_52_099aa6
- **What it is:** Eurostat sdg_11_52, annual premature deaths attributed to PM2.5, Italy only (national aggregate). 36 cells: 18 years by number and rate. Coverage 2005-01-01 to 2023-12-31. Last updated 2025-12-09 per API metadata.
- **Verdict:** Feasible with conditions. N6 is a could-need, so the blocker below does not reject the source.
- **Key flags:**
  - LIC-UNKNOWN (blocker): no licence in the API response. The copyright page redirects to EU Login and shows no licence text.
  - COV-PARTIAL-WINDOW (major): prototype window 0.24 covered (2005 only). Production window 0.00 covered.
- **Conditions:** Legal confirms the reuse licence before any use. Production use needs Legal sign-off. Accept it as national annual context only. Data lead confirms the 2006 gap in the time index and the rate denominator if used.

### link.data_open_air_chicago_hour_aggre_d4970b
- **What it is:** A link to a US open-data record "Open Air Chicago hour aggregations". Described as hourly air sensor data from a US city.
- **Verdict:** Not feasible.
- **Key flags:**
  - ACC-UNREACHABLE (blocker): the host catalog.data.gov returned DOMAIN_NOT_ALLOWLISTED. No metadata, schema, coverage or licence could be read.
  - LIC-UNKNOWN (blocker): no licence readable.
  - COV-GEO-MISMATCH (major): Chicago, US, not Italy.
- **Note:** The guardrail is respected. No alternate route was tried. The prototype N1 need does not depend on it.

### vendor.atmosdata_pro
- **What it is:** AtmosData Pro station-grade weather feed, listed as a candidate for N3 (production). No data read or requested. No schema, grain, spatial coverage or period documented.
- **Verdict:** Not feasible.
- **Key flags:**
  - LIC-AGREEMENT-NOT-ACTIVE (blocker): contract AD-2021-114 ran 2022-01-01 to 2025-12-31. Renewal waiting on Procurement. No signed renewal on file.
  - ACC-UNREACHABLE (blocker): API key revoked 2026-01-01. Not probed, per vendor-feed rule.
  - LIC-UNKNOWN (blocker): terms and docs URLs null.
  - ACC-RESTRICTED (major): approved purposes empty.
- **Note:** Not needed for a must need, since Open-Meteo covers N3 at probe level. Revisit only if Procurement renews with full terms.

## 4. Red-flag register

| Source id | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.airq.station_readings | ACC-RESTRICTED | major | Auth required, internal. Request to Environment Monitoring Unit. No request or approval on record. | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Catalog "active". Wiki: VR-03 off from 2024-06-30. | judgement |
| internal.traffic.hourly_counts | GOV-CATALOG-WIKI-CONFLICT | major | Counter break 2024-03-18 in wiki; not in catalog. Do not compare without adjustment. | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | No coordinates or station mapping. Proximity undocumented. | judgement |
| internal.traffic.hourly_counts | DQ-DST-ARTEFACTS | minor | Local time, zone not stated. No DST handling. | judgement |
| api.open_meteo_archive | LIC-MIXED | major | CC BY 4.0 for API; C3S reanalysis licence not read. Commercial use unknown. | rule |
| api.open_meteo_archive | COV-GEO-MISMATCH | major | Probe point grid is Milan area. Valdena not located. | judgement |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | Attribution text and citation required. | rule |
| api.open_meteo_archive | FRS-METADATA-DATE-MISLEADING | minor | Licence page dated 2026-11-24, after as-of date. | judgement |
| link.uci_360 | GOV-PURPOSE-LIMITATION | major | "Research purposes only" vs CC BY 4.0 on the same page. | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Declared no missing values; notes say -200 tags. Sample confirms -200. | rule |
| link.uci_360 | DQ-SENTINEL-VALUES | major | -200 in NMHC(GT) ~90%, CO/NOx/NO2(GT) ~17%. | judgement |
| link.uci_360 | INT-REPRESENTATIVENESS | major | Single unnamed road-level site. | judgement |
| link.uci_360 | FRS-STALE | major | Ends 2005-04-04. Kept for prototype only. | rule |
| link.uci_360 | LIC-ATTRIBUTION | minor | Citation required. | rule |
| link.lombardia_nicp_bhqi_eba0c8 | DQ-SENTINEL-VALUES | major | -9999 in ~4.5% of sample rows. | judgement |
| link.lombardia_nicp_bhqi_eba0c8 | DQ-UNDOCUMENTED-SCHEMA | major | No pollutant, station or unit columns. No dictionary. | judgement |
| link.lombardia_nicp_bhqi_eba0c8 | FRS-METADATA-DATE-MISLEADING | minor | dateModified after as-of date. | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | Auth required. Request to Clinical Analytics. | rule |
| internal.clinic.resp_visits_daily | GOV-PURPOSE-LIMITATION | major | Policy permits daily district counts for surveillance. Live warning use unconfirmed. | judgement |
| internal.clinic.resp_visits_daily | INT-JOIN-KEY-MISMATCH | major | District code undocumented. No mapping to stations or counters. | judgement |
| link.europa_sdg_11_52_099aa6 | LIC-UNKNOWN | blocker | No licence in response. Copyright page gives no text. | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Prototype 0.24 covered; production 0.00. | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | DOMAIN_NOT_ALLOWLISTED. | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence readable. | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | US geography. | judgement |
| vendor.atmosdata_pro | LIC-AGREEMENT-NOT-ACTIVE | blocker | Contract expired 2025-12-31. No signed renewal. | rule |
| vendor.atmosdata_pro | ACC-UNREACHABLE | blocker | Key revoked 2026-01-01. Not probed. | rule |
| vendor.atmosdata_pro | LIC-UNKNOWN | blocker | No terms or docs on file. | rule |
| vendor.atmosdata_pro | ACC-RESTRICTED | major | No approved purposes. | rule |

## 5. Conditions and owners

Owners are as named in the source assessments. The discovery output does not name resolvers in its structured fields.

| Condition | Source(s) | Who can resolve | Blocking which need |
|---|---|---|---|
| Approve access; confirm warehouse reachability | internal.airq.station_readings | Environment Monitoring Unit | N1 (production) |
| Resolve VR-03 status and gap handling; correct catalog status | internal.airq.station_readings | Environment Monitoring Unit with data lead; catalog steward | N1 (production) |
| Confirm PM2.5 method, validation flags, per-station coverage | internal.airq.station_readings | Environment Monitoring Unit | N1 (production) |
| Document counter-break adjustment; update catalog | internal.traffic.hourly_counts | Mobility Office | N2 |
| Provide counter coordinates or station mapping | internal.traffic.hourly_counts | Mobility Office | N2 |
| Confirm time zone and DST; convert to UTC | internal.traffic.hourly_counts | Data lead | N2 |
| Test access and completeness for 2024-2025 | internal.traffic.hourly_counts | Mobility Office | N2 |
| Confirm C3S licence and commercial-use position | api.open_meteo_archive | Legal | N3 (production) |
| Confirm Valdena coordinates; record in decisions.md | api.open_meteo_archive | Civic Health Office / data lead | N3 |
| Full-range missing-value checks | api.open_meteo_archive | Data engineering | N3 |
| Attribution text in outputs; Legal sign-off for production | api.open_meteo_archive | Legal | N3 (production) |
| Resolve CC BY vs research-only conflict | link.uci_360 | Legal | N1 (prototype) |
| Set -200 to null; accept single-site limits | link.uci_360 | Data lead; project lead | N1 (prototype) |
| Obtain dataset description and dictionary; confirm prototype coverage | link.lombardia_nicp_bhqi_eba0c8 | Data lead | N1 (prototype, currently unverified) |
| Remove sentinel and NA rows; Legal sign-off for production | link.lombardia_nicp_bhqi_eba0c8 | Data lead; Legal | N1 (prototype) |
| Confirm live warning use within surveillance purpose; any further DPO sign-off | internal.clinic.resp_visits_daily | Data Protection Office | N4 |
| Document district codes, small-cell suppression, zero-day handling | internal.clinic.resp_visits_daily | Clinical Analytics (Chiara Conti) | N4 |
| Build district-to-station/counter mapping | internal.clinic.resp_visits_daily | Data lead with GIS support | N4 (joint analysis) |
| Approve clinic access request | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Confirm Eurostat reuse licence | link.europa_sdg_11_52_099aa6 | Legal | N6 |
| Confirm 2006 gap and rate denominator | link.europa_sdg_11_52_099aa6 | Data lead | N6 |
| Renewed agreement, terms, new key, schema | vendor.atmosdata_pro | Procurement | None (not needed) |

## 6. Recommended next steps

1. **Raise access requests now.** Environment Monitoring Unit (station readings, N1 production). Mobility Office (traffic counts, N2, including 2024-2025 test). Clinical Analytics (daily district counts, N4). Track each as a dated request, since no request record exists for the first one.
2. **Ask Legal to clear three licences before any use.** Open-Meteo and the C3S reanalysis (N3, production). The UCI CC BY vs research-only conflict (N1 prototype). The Eurostat reuse licence (N6).
3. **Ask the Data Protection Office** whether a live patient-warning use falls within the clinic data policy's surveillance purpose.
4. **Decide the Valdena location.** Confirm coordinates for the Open-Meteo point. The probe used a Milan-area point. Record the decision and rationale in decisions.md. Confirm whether that point should be re-probed.
5. **Decide on the prototype data.** Proceed with UCI 360 for method building only, with research-only use and no production service. Keep ARPA Lombardia out of the prototype until its coverage and sensor map are confirmed.
6. **Decide on the VR-03 and counter-break treatment rules** before profiling production data. Both breaks fall inside the production window (2024-03-18 and 2024-06-30).
7. **Profile first once the gate is passed, in this order:** (a) traffic counts around 2024-03-18, to check the break and time zone; (b) station readings for 2024-2025, with VR-03 flagged; (c) Open-Meteo for both windows, for missing values and the probe point; (d) UCI for -200 handling and time coverage; (e) clinic daily counts for district code and suppression checks.
8. **Do not pursue** the Chicago link or the AtmosData feed further. Both are outside the guardrails or contractually closed.

## 7. Open questions for the human reviewer

1. Which Valdena coordinates should be used for Open-Meteo? The probe point is Milan area, and the brief says the register default is Lisbon, which is not the client's location. Has decisions.md been updated?
2. Does a live patient-warning model fall within the clinic data policy's surveillance purpose, or does the Data Protection Office need to sign off separately?
3. Can Legal say whether UCI 360 may be used for method building, given its CC BY 4.0 licence and its "research purposes only" note?
4. Can Legal confirm the C3S licence terms and commercial-use position for Open-Meteo-derived series?
5. Can Legal confirm the Eurostat reuse licence? Is the Eurostat series needed at all, given its national-only scope and a licence that is unknown?
6. Is VR-03 permanently closed? Should it be excluded or imputed in the production window?
7. Should the production model use a station-based temperature and humidity source? If so, who will renew or replace the AtmosData agreement?
8. Are the 2024-03-18 counter change and the undocumented counter-to-station proximity acceptable for the N2 need, or must the Mobility Office supply coordinates first?
9. Does the ARPA Lombardia dataset cover 2004-2005 at all? Its historical coverage is unknown from any source read.
10. Who approves the client's clinic request, and does Clinical Analytics accept district counts only?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-24T20:16:42Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- link.europa_sdg_11_52_099aa6: LIC-UNKNOWN

**Open questions:**

1. Which Valdena coordinates should be used for Open-Meteo? The probe used a Milan-area point. The brief says the register default is Lisbon, which is not the client's location. Has decisions.md been updated?
2. Does a live patient-warning model fall within the clinic data policy's surveillance purpose, or does the Data Protection Office need to sign off separately?
3. Can Legal say whether UCI 360 may be used for method building, given its CC BY 4.0 licence and its 'research purposes only' note?
4. Can Legal confirm the C3S licence terms and commercial-use position for Open-Meteo-derived series?
5. Can Legal confirm the Eurostat reuse licence, and is the national-only Eurostat series needed at all?
6. Is VR-03 permanently closed? Should it be excluded or imputed in the production window?
7. Should production temperature and humidity come from a station-grade source? If so, who will renew or replace the AtmosData agreement?
8. Are the 2024-03-18 counter change and the undocumented counter-to-station proximity acceptable for N2, or must the Mobility Office supply coordinates first?
9. Does the ARPA Lombardia dataset cover 2004-2005 at all? Its historical coverage is unknown from any source read.
10. Who approves the clinic access request, and does Clinical Analytics accept district counts only?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
