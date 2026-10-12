# BVMT Market Surveillance — independent repository audit and Codex implementation brief

**Reviewed snapshot:** user-uploaded `bvmt-market-surveillance-master (2).zip`, dated October 7, 2026.  This review covers the uploaded snapshot, not unverified changes made after it.

**Goal:** a defensible academic statistical screening tool and a high-quality, responsive analyst dashboard. **Never** represent statistical anomalies or AI assessments as confirmed fraud, misconduct, or calibrated fraud risk. Retain clear non-affiliation disclosures.

## Verified baseline

- 85 symbols; 61,812 price observations dated 2021-06-17 to 2026-06-17.
- 1,454 anomaly flags; 556 classified `EXPLAINED`, 898 `UNEXPLAINED`.
- The project documents only 3 source-backed positive events and 2 evaluable 30-day cases. Its reference method does not exceed the return-only baseline on event recall and precision. Do not inflate this evidence.
- 23 non-Flask tests passed locally; compilation and dashboard JavaScript syntax checks passed. The full suite could not be executed in the review environment because Flask and Flask-CORS were not installed and the environment could not reach PyPI. Do **not** claim full-suite verification from this review.

## Prioritized audit tickets

### P0 — Security and analytical validity

**BVMT-01: Minimum-history mismatch** (`src/detection/anomaly_detector.py:46-49, 76-78, 103-112`). The detector advertises a 60-trading-observation baseline, but `.rolling(60, min_periods=20)` permits z-scores after 20 prior observations. In the saved output, 97 flags occur within the first 60 observations of their symbols, starting at observation 22. Either require 60 valid prior observations for both signals and document implications for the number of signals, or rename it to an explicit warm-up design. Add synthetic unit tests with 20/59/60/61 prior observations and gaps.

**BVMT-02: Look-ahead in news interpretation** (`src/validation/classify_anomalies.py:85-119`). Matching within +/- 7 days is fine for *retrospective association*, but `EXPLAINED` suggests contemporary explanatory evidence. Of 556 records so labeled, 178 match news dated *after* the price/volume signal. Split `news_available_as_of_flag` (<= flag timestamp) from `post_event_news_context`, preserve matched date and gap, and use neutral labels such as `NEWS_MATCH_FOUND`/`NO_LOCAL_MATCH`. Do not equate absence of local news with suspicious activity. Add timestamp and publication-date availability coverage where possible.

**BVMT-03: Silent OHLC mutation** (`src/detection/anomaly_detector.py:64-66`; `src/evaluation/full_universe.py:40-61`). 58 source rows have closing price outside reported intraday high/low; maximum departure is ~0.7 TND. The current unconditional clamp changes four individual date/symbol flag decisions versus computing with raw closing prices (total flags remain 1,454). Establish provenance, allow an explicit correction policy with a quality log, and segregate material issues for review. Avoid overwriting raw CSVs. Rerun evaluation following any detector change.

**BVMT-04: Unprotected computational endpoint** (`app.py:46-49, 95-119, 149-156, 498-500`; `scraper/run_pipeline.py:16-26`). `POST /api/scrape` requires no authorization, starts subprocess work and is reachable even though the UI declares scraping unavailable. The Flask server binds `0.0.0.0` and enables broad CORS. Disable trigger by default and bind loopback in local development. If an execution API is truly needed, add authentication, authorization, CSRF safeguards where applicable, rate limiting, a job lock, explicit mode and audit trail. Use `sys.executable`, log stderr, and distinguish *analysis* from *scrape* accurately.

**BVMT-04b: Evaluation outputs can become stale** (`run_all.py:11-21, 40-47`; `src/evaluation/full_universe.py:203-215`). The default `run_all.py` does not call evaluation, baseline or sensitivity generation. Following data or detector changes, the dashboard may read updated anomaly flags alongside old evaluation metrics. Add a reproducible evaluation stage or an explicit, timestamped stale-results state; track hashes of input data/config and generated output metadata, and test the dependency chain.

**BVMT-05: Input validation and URL safety** (`app.py:372-376`; `templates/dashboard.html:248-250`). Validate requested ticker strictly against known tickers/`^[A-Z0-9]+$` before constructing paths; check that news external URLs are HTTP(S) before inserting as links. Keep HTML escaping and add validation at the API boundary.

### P1 — Dashboard correctness, usefulness, trust

**BVMT-06: Unusable severity filters and missing records** (`app.py:236-252`; `templates/dashboard.html:241-245`). API always takes top 50 out of 1,454, and all 50 score `High` by its `max_zscore >= 4` rule; Medium and Low filters cannot show results. Return paginated results with filters, dates, symbol, score type, classification, sort, total count; do not frontload `.head(50)` before filtering. Add deterministic tie-breaks, CSV export, and tests. A statistical severity band is not a validated fraud-risk probability: rename the UI concept to *signal intensity* or *anomaly strength*.

**BVMT-07: Date-axis gaps** (`app.py:292-319`; `templates/dashboard.html:252-257,269-278`). Timeline emits only days with nonzero flags; sampled 90-calendar-day interval has 49 flag-dates. SVG equally spaces these, misrepresenting the horizontal time scale. Stock chart uses equally spaced trading observations even across long inactivity gaps. Use time-scaled chart components, preserve explicit dates, include zero-flag trading dates when meaningful, and show non-trading or missing-data periods.

**BVMT-08: Staleness and fabricated fallback time** (`app.py:182-185, 230`; dashboard footer). Observations end 2026-06-17. `last_scrape` falls back to `datetime.now()`, creating a misleading impression of recency. Define `data_as_of`, `news_as_of`, `pipeline_last_run_at`, `dashboard_checked_at` independently and show a historical-data badge. A snapshot is not a live exchange feed.

**BVMT-09: Key investigative outputs not exposed** (`app.py` APIs; `bvmt_data/watchlist_refined.csv`, `watchlist_ai_assessed.csv`). Dashboard's anomaly feed focuses on raw top-50 z-score flags but does not present the refined 17-case review queue or optional AI draft assessments as a dedicated analyst workspace. Add a sortable case queue with details, priority, human-review state, annotations and evidence pointers. Never allow AI text to overwrite human conclusions.

**BVMT-10: API performance & design** (`app.py:69-92`, multiple endpoints). Repeated CSV loading per request, no pagination/caching/versioning, broad exception-to-empty handling obscures broken files. Introduce a read-only service layer with schema validation, cache/mtime invalidation, structured HTTP errors, typed API schemas, and response sizes suitable for scaling. Preserve compatibility until replacement UI is tested.

**BVMT-11: Frontend accessibility/maintainability** (`templates/dashboard.html`). A single-file UI has inline CSS/JS, basic SVG charts, no analyst navigation sidebar, no cross-filtering/drilldowns, minimal loading states, and no data export. Add keyboard navigation, accessible charts and tables, visible focus, reduced-motion preference, responsive layouts, component separation, loading/empty/error states and automated browser tests.

**BVMT-12: Test/CI coverage** (`tests/test_api.py:22-35`). Most endpoint checks only assert HTTP 200, so incorrect payloads can pass. Add schema/value tests, boundary cases, malicious-input tests, no-unauthorized-job tests, pure detector property tests, frozen fixture/golden data tests, and browser E2E. Set up GitHub Actions for pytest, Ruff, type checks and frontend checks; pin lockfiles.

### Methodological caution

- Source-backed case sample is tiny. Keep recall and event-matching claims expressly descriptive. Counts in an event window that includes up to five days after an event are not by themselves proof of pre-event early warning.
- Incomplete event labels make `precision@k` against known cases a *known-case hit rate*, not population precision. Label it clearly in UI and report.
- Evaluate corporate actions, rights issues, splits, dividend adjustments, thin liquidity, skipped trading days, symbol survivorship and missing announcement timestamps before raising fraud-related claims.
- An AI model's triage output is a draft and should include model version, data as-of, source evidence, reviewer controls, and an explicit 'not a legal finding' label.

## Recommended architecture

**Preserve the working statistical backend.** Modularize Flask into services/blueprints and typed read-only API endpoints; keep existing data and analysis unchanged until regression tests cover them. Create a new isolated `frontend/` with React + TypeScript + Vite, Tailwind and shadcn/ui. Use TradingView Lightweight Charts for OHLCV/volume and Recharts for aggregate visualizations, TanStack Table for filtering/virtualization, Lucide icons, Motion for restrained transitions. Do not migrate to Next.js or add a database without a concrete requirement. For a small portfolio project, Flask + Vite is easier to manage.

### Design direction — 'Institutional surveillance workstation'

- Dark midnight/navy shell with clear typographic hierarchy, desaturated surfaces, teal/blue accents for neutral information, amber for review and red for extreme statistical outliers; avoid neon overload and fake live tickers.
- Persistent collapsible left nav, ticker/command palette, top search, light/dark switch, historical-data timestamp. Four KPI cards: universe coverage, flags in selected period, items awaiting review, data freshness.
- **Market Overview**: interactive time-series of flag activity, sector/symbol heatmap, signal composition, data-quality indicators, top review queue (not random top 50).
- **Signal Explorer**: paginated/filterable signals with column chooser, saved filters, score breakdown and a clickable analyst drawer.
- **Stock Lab**: date-scaled candlestick + volume, anomaly markers, selectable z-score tracks, news and corporate-action timeline, comparisons with TUNINDEX, raw vs normalized view where justified by available data.
- **Case Workbench**: human-controlled status (new/reviewing/escalated/closed), investigation notes, evidence, related alerts, AI draft rationale, exportable case pack. Use SQLite/PostgreSQL only if persistently storing analyst notes/cases.
- **Research & Validation**: event coverage and denominator drilldowns, baseline vs reference, 2-D sensitivity matrix, labeled-event provenance, caveats prominent.
- **Data & Pipeline**: as-of stamps, per-source coverage, data-quality quarantine, execution logs (read-only by default), lineage of processed outputs.

## Codex execution brief — paste into Codex

> Act as a senior market surveillance engineer, Python quantitative researcher, application-security reviewer and product designer. First review `README.md`, `docs/REPORT.md`, `run_all.py`, `app.py`, `templates/dashboard.html`, detector/classifier/evaluation modules and all tests. The uploaded audit tickets BVMT-01 through BVMT-12 are hypotheses to validate in the current checkout; use repository reality as the source of truth, and report deviations. **Do not silently run scraper/network collection, execute live Groq requests, alter protected raw CSVs, delete outputs, or deploy**. Do not suggest or implement fraud-verdict features.
>
> Work in small phases with readable commits and before/after tests. Phase 1: fix analytical correctness, unauthorized execution surfaces, news-time terminology and data-quality reporting; add regression tests and rerun evaluation after any detector change, with a table of changed metrics and flags. Phase 2: implement robust server-side filtered/paginated APIs and expose refined/AI-human-triage data; make all timestamps honest. Phase 3: create a new React + TypeScript dashboard alongside the existing Flask app, using an institutional-grade design system and the six analyst views. Phase 4: use browser automation to test every navigation, filter, chart, responsive breakpoint, empty/error state and keyboard interaction. Phase 5: add automated CI checks, update docs/screenshots and provide an audit-trail changelog.
>
> Before editing, propose a file-by-file plan and request confirmation for major architecture decisions. Do not claim 'fixed' without evidence: show exact tests run, pass/fail results, sample API responses, screenshots and remaining risks. Never fabricate live data, source attributions or performance claims. Keep normal project usage operational.

## Acceptance checks

- [ ] No unauthorized pipeline run reachable via public dashboard/API.
- [ ] Historical data and news dates clearly distinguished from current time.
- [ ] User can find all 1,454 historical flags using paging and filters; rebaseline and update this count if detection changes.
- [ ] News from after an anomaly is never displayed as information available on the anomaly date.
- [ ] Correct 60-observation history policy and data-quality treatment covered by tests.
- [ ] Raw CSV files preserved byte-for-byte unless user specifically authorizes changes.
- [ ] Case workbench shows the 17 stored refined cases, clearly labeling AI output as draft.
- [ ] Mobile and desktop screenshots, keyboard and axe-based a11y testing, no console errors, end-to-end test results.
- [ ] Updated evaluation and baseline comparison with tiny-sample limitations intact.
- [ ] No fake 'live' feed, 'fraud detected' verdict or guaranteed confidence/risk score.

## Suggested Codex capabilities

1. **Playwright MCP** — real browser interaction and screenshot-based test feedback: `codex mcp add playwright npx "@playwright/mcp@latest"`.
2. **Chrome DevTools MCP** — browser console, network and performance trace: `codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest` (or use MCP config if CLI syntax differs).
3. **shadcn MCP** — component registry and composable UI blocks, appropriate *after* creating React frontend: `~/.codex/config.toml` with `[mcp_servers.shadcn]`, `command="npx"`, `args=["shadcn@latest","mcp"]`.
4. **Context7 Codex plugin** — fresh library docs and skill: `codex plugin marketplace add upstash/context7` then `codex plugin add context7@context7-marketplace`; authenticate via OAuth.

MCP servers and Codex plugins are distinct from ordinary npm UI libraries. Install only sources you trust. On native Windows, an MCP `npx` executable may need `npx.cmd` or `cmd /c`; follow the specific server's Windows instructions and confirm tools are listed in Codex before relying on them.
