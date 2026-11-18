# BVMT Market Surveillance presentation

An eight-slide, five-minute interactive keynote built as a separate React application. It reads no live market feed and never runs the research pipeline. The factual snapshot and caveats are documented in [`docs/fact-sheet.md`](docs/fact-sheet.md). Two alternative visual concepts and the selected outline are in [`docs/concepts.md`](docs/concepts.md).

## Run locally

Node 22.12+ or 24 is recommended.

```powershell
cd presentation
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://127.0.0.1:5173/#1`.

To build and preview the deployable static site:

```powershell
npm run build
npm run preview
```

`vercel.json` sets the Vite build command and `dist` output directory. Set the Vercel project root to `presentation/`. The static presentation requires no backend. Its local demo link points to `http://127.0.0.1:5000/terminal` only when that service responds; otherwise it shows an unavailable state. Run Flask and build `frontend/` as described in the repository root README to enable the demo.

## Present

- Right arrow, Space, or Page Down: next slide. Left arrow or Page Up: previous slide.
- Click the footer arrows to navigate. The hash (`#1` through `#8`) is a deep link.
- Click the fullscreen control for projector mode.
- Click **Notes**, or press `N`, to open the 5-minute script, rehearsal timer, and jury Q&A. Press Escape to close it.
- Slide 6 switches between captured views of the real Flask dashboard and React Market Command Center.
- Open `?print#1` to display all eight slides in a print layout, then use the browser's Print / Save as PDF command. For example: `http://127.0.0.1:5173/?print#1`.

The app respects the operating system's reduced-motion preference. Slide screenshots captured at 1440×900 are in `verification/`.

## Reuse for another hackathon

1. Replace the verified figures and sources in `docs/fact-sheet.md` before changing slide copy. Keep a separate note for assumptions and unresolved evidence.
2. Edit the eight slide functions in `src/main.tsx`. The navigation array determines order; update `titles` and `notes` at the same time.
3. Replace `public/terminal.png` and `public/dashboard.png` with actual captures of the new project, or remove the product screen tabs if none exist. Do not label illustrations as screenshots.
4. Set colors and typography in `src/styles.css`. Keep result caveats legible on the same slide as the metrics.
5. Update the spoken script and jury answers in `src/notes.ts`, then check that the allocated seconds total 300.
6. Run `npm run build`, inspect every slide at 1440×900 and on a narrow viewport, and rehearse with the timer.

The source project remains untouched. The only content copied into this directory is two real application screenshots captured from the local running dashboards.
