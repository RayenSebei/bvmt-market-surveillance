# BVMT Surveillance Terminal 2.0

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

The activity chart fills zero only on dates with recorded source observations, not invented exchange sessions. The heatmap uses equal-sized tiles, ordered by flag count and then symbol. It is not market capitalization or return performance. The table lists stored flags by observation date; the repository does not provide a detection timestamp. Intensity bands describe `max(abs(volume_zscore), abs(return_zscore))`, not fraud risk.

Search reads `/api/tickers`. The inspector reads `/api/stock/<symbol>` and labels each instrument's own latest priced date. This endpoint returns up to 252 stored observations, which may end before the aggregate snapshot. PX1 and TBIDX are displayed in index points; equity closes use TND. Retrospective news/legal classifications are not shown as contemporaneous evidence. Refresh only repeats GET requests; it does not trigger scraping or analytical recomputation.

## Next pages

This terminal is an optional Command Center view. Dedicated instrument research, anomaly investigation, news/context, watchlist/triage, evaluation/model validation, and pipeline/data-management remain available in the existing dashboard.

See `../docs/DESIGN_SYSTEM.md` for the reusable visual and interaction rules.
