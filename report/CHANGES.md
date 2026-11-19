# Report update record

The original PDFs are preserved byte for byte in `report/original/`. The
editable LaTeX sources under `report/short/`, `report/long/`, and
`report/common/` were not edited. The new source trees and PDFs are under
`report/stage13_updated/` and `report/stage30_updated/`. Both cover pages
render pixel-identically to the originals, including the internship period
1 July 2026 to 1 August 2026. The company-supervisor continuation sentence
was added to the normal chapters, without assigning later work to those dates.

## Short report (14 pages; original 13)

- Replaced the old dashboard workflow with the final React, TypeScript, and
  Tailwind Terminal served through Flask at `/`; described all seven views,
  the signal inspector, keyboard and reduced-motion behavior, and the
  83-company Market Map. The map uses 20-session average traded value, not
  market capitalization; PX1 and TBIDX are index series.
- Replaced old dashboard captures with final Terminal Anomaly Feed,
  Watchlist, Overview/Market Map, Inspector, and Evaluation captures.
- Corrected the description of 85 market symbols to 85 stored series:
  83 company shares plus PX1 and TBIDX.
- Kept the frozen reference detector formula, 60 prior valid observations,
  floors 0.10/0.01, 10-day return-gap rule, and 1,414 flags.
- Replaced the old three-event-only evaluation with the expanded sourced
  register, four development and one held-out eligible positives, Wilson
  intervals, six candidates, baselines, random-placement comparison,
  workload, source audit, correlated controls, quality checks, and the
  decision to retain `reference_v1`. The original one-of-three result is
  retained as a separate reproduction check.
- Added the code's Wilson, median/MAD robust score, exact-date excess-return,
  and one-sided permutation formulas. Added an abstract, abbreviation key,
  list of figures, and list of tables. The extra front-matter material added
  one physical page; the obsolete dashboard figure and old three-event table
  were cut to limit growth.
- Updated the conclusion and references. No news-classifier agreement or
  accuracy is claimed.

## Long report (32 pages; original 33)

- Updated the abstract and introduction to distinguish the final project
  from the earlier dashboard, and corrected the old statement that only
  three positives had source and coverage. Six positives have sources and
  five have primary-window coverage; one is held out. TINV, CGF, and UBCI
  retain unsupported original claims/dates, while TSI has a source but no
  listed trading series.
- Corrected the market-universe wording to 85 series, including two indices,
  and updated the pipeline diagram to the React Terminal.
- Replaced the seven old dashboard screenshots and interface prose with
  final Terminal figures for Overview/Market Map, Inspector, Anomaly Feed,
  Stock Detail, News, Watchlist, Pipeline, and Evaluation. Removed old
  endpoint timing numbers because they were not remeasured.
- Rewrote the evaluation chapter around the protocol committed before
  candidate code, 18 added sourced rows, development/held-out split, Wilson
  intervals, six candidates and baselines, permutation p-value, flags per
  week, quality and corporate-action checks, and the retain-reference
  decision. Kept the original detector result of 1,414 flags and one of
  three original positive events.
- Corrected UADH to a 25 March 2026 suspension; Syphax to a 19 December
  public announcement with the 11 December ruling in notes; ADWYA to an
  exploratory suspension with reason undisclosed. PGH and LNDOR share a
  notice and are reported with both separate and collapsed control counts.
- Updated the conclusion, limitations, references, parameter/output/page
  registers, and all 28 event rows. Replaced the old 109-test statement
  with 117 passing tests; documented build, format, responsive, and SPA
  verification. Removed the seven-page template implementation, obsolete
  timing table, three-event-only baseline table, and sensitivity grid table
  to keep the original 33-page length.

## Verification limits

- The supervisor's agreement to continue the project is stated by the
  report owner; no independent company document was supplied.
- CODELOGIC's service profile and internship narrative were retained from
  the original reports; they were not independently reconfirmed here.
- Historical endpoint latency figures were removed rather than repeated.
- The news-classifier human labeling study is unfinished. No accuracy or
  agreement value can be verified or cited.
- The public-event register is small and not a representative sample;
  the held-out positive count is one. Performance claims remain limited
  to the defined screening case studies.

## Readability and count corrections

- Cropped each final Terminal figure to the relevant pane. The Stock Detail,
  News, Watchlist, Pipeline, and Evaluation source captures were retaken in
  Playwright at 135% browser zoom only after all market-tape prices loaded. Both updated
  report asset trees use these captures; the originals were untouched.
- Replaced the long report's floating screenshot blocks with bounded in-flow
  figures, each no taller than 35% of text height, to prevent sparse float pages.
- Corrected the positive-source count: seven positive CSV rows have dated URLs.
  The evaluation metric counts six because it requires `include_headline=true`,
  excluding sourced but unlisted TSI. Five are primary-window eligible.
- Verified the 1,414 reference flag rows directly: 1,399 company shares, 15 PX1,
  zero TBIDX. Added this distinction to abstracts and results text.
- Added the simple volume-spike workload and control comparison after Table 6.1;
  defined Phase 2, `reference_v1`, and `robust_z3` at first use; clarified the
  prototype dashboard was later replaced.
- Replaced the final event register longtable with a one-page tabular
  register to avoid the longtable page-split glue warning. Final compile and visual verification are recorded separately.

Final layout check: the short PDF is 14 pages; the long PDF is 32 pages. The long report lost one page because cropped, in-flow figures and a shorter checklist removed the sparse figure page and orphan line; no substantive report section was cut in this revision. The Stock Detail figure shows the full chart axis, and the Market Map and inspector figures show legible detail crops. Both final LaTeX logs have no overfull boxes, broken references, or infinite-glue warnings.
