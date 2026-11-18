# BVMT Surveillance Terminal v2

The React application at `/terminal` now has seven lazy-loaded views: Overview, Anomaly Feed, Stock Detail, News, Watchlist, Pipeline and Evaluation. It uses the existing read-only Flask API. Statistical flags are prompts for human review, not findings of misconduct.

## V2 structure and tokens

- `src/App.tsx`: navigation, historical ticker tape, status bar, theme, URL state, Ctrl+K search and inspector dialog.
- `src/pages/`: one lazy-loaded module per view.
- `src/components/Inspector.tsx`: price, z-score, and dated news context.
- `src/components/StockChart.tsx`: lazy-loaded candlesticks and comparison normalized to 100.
- `src/components/FlagRows.tsx`: paged review tables.
- `src/terminal.css`: responsive v2 tokens and pane layout.

Dark colors: background `#101923`, pane `#17232e`, border `#2b3b49`, text `#e7eef1`, teal `#6dd6bf`, amber `#e8b966`, coral `#e18f86`. Inter is the UI font, IBM Plex Mono is the data font. Light theme is persisted under `bvmt-theme-v2`. The 250 ms entrance and drawer motion is removed under reduced motion.

Watchlist statuses and saved filter views stay in localStorage. URL query parameters carry page, ticker, range and feed filters. The detector console reads precomputed sensitivity cells; it does not rerun detection. The tape is historical, based on each symbol's last two stored closes.

The evaluation remains a small case study: 30-day recall 1/3, P@20 0, and no improvement over the return-only baseline. The event audit exposes source-label limitations.

The Market Command Center is a React/TypeScript application using Vite, Tailwind 4, shadcn/ui, TradingView Lightweight Charts 5, TanStack Query/Table, Motion, and Lucide. Fonts are bundled locally. The Flask API and original research dashboard remain available.

## Local development

From the repository root, install Python dependencies in a virtual environment and start Flask:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

In a separate terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://127.0.0.1:5173`). Vite proxies `/api` to Flask. Node 22.12+ or 24 is recommended for Vite 7.

## Built application

```powershell
cd frontend
npm run build
```

Flask serves the resulting `frontend/dist` at `/terminal`, including the bundled assets. No frontend development server is required to view the built application. The existing research dashboard stays at `/`. Without a frontend build, `/terminal` returns a clear unavailable response and the existing dashboard is unaffected.

## Checks

```powershell
npm run build
npm run format:check
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Browser verification evidence is documented in `../docs/FRONTEND_VERIFICATION.md`. Screenshots are stored locally in `frontend/verification/` and intentionally excluded from Git along with downloaded CSVs and browser logs.

## Architecture

- `src/main.tsx`: query client, reduced-motion policy, tooltip provider, local fonts.
- `src/App.tsx`: application shell, Command Center composition, command search, inspector, and methodology dialog.
- `src/components/TerminalPrimitives.tsx`: reusable panel, metric, and tooltip vocabulary.
- `src/components/TimeChart.tsx`: responsive Lightweight Charts lifecycle, crosshair readout, zoom/pan and fit control.
- `src/components/SignalTable.tsx`: typed TanStack table with filtering, sorting, and pagination.
- `src/components/ui/`: shadcn primitives generated after discovery through shadcn MCP; local styling and accessible dialog composition.
- `src/lib/api.ts`: typed read-only API contracts, abortable requests, date/number formatting.
- `src/styles.css`: theme tokens, terminal layouts, component treatments, breakpoints and reduced-motion rules.
- `../src/dashboard.py`: presentation-only historical aggregates. It does not run the detector or write source data.

## API semantics

`GET /api/command-center?days=30|90|365` anchors the window to the latest valid date in `_all_tickers_full.csv`; both endpoints of the selected calendar-day window are inclusive. A stored observation is counted once when either price or volume is flagged. Future flags and invalid dates cannot enter that window. Empty or missing required datasets return an explicit error rather than healthy-looking zero metrics.

The activity chart fills zero only on dates with recorded source observations, not invented exchange sessions. The Market Map has 83 company-share tiles: it excludes PX1 (TUNINDEX) and TBIDX (Tunisian Bond Index) from the stored 85-series analysis universe because indices are not companies. The heatmap uses equal-sized tiles, ordered by flag count and then symbol. It is not market capitalization or return performance. The table lists stored flags by observation date; the repository does not provide a detection timestamp. Intensity bands describe `max(abs(volume_zscore), abs(return_zscore))`, not fraud risk.

Search reads `/api/tickers`. The inspector reads `/api/stock/<symbol>` and labels each instrument's own latest priced date. This endpoint returns up to 252 stored observations, which may end before the aggregate snapshot. PX1 and TBIDX are displayed in index points; equity closes use TND. Retrospective news/legal classifications are not shown as contemporaneous evidence. Refresh only repeats GET requests; it does not trigger scraping or analytical recomputation.

## Next pages

This terminal is an optional Command Center view. Dedicated instrument research, anomaly investigation, news/context, watchlist/triage, evaluation/model validation, and pipeline/data-management remain available in the existing dashboard.

See `../docs/DESIGN_SYSTEM.md` for the reusable visual and interaction rules.
