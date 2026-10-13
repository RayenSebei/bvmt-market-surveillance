import { useCallback, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'motion/react'
import {
  Activity,
  ArrowDownToLine,
  ArrowUpRight,
  BarChart3,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  ExternalLink,
  Focus,
  Info,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  Waves,
} from 'lucide-react'
import { Button } from './components/ui/button'
import { Hint, Panel, Metric } from './components/TerminalPrimitives'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from './components/ui/command'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './components/ui/dialog'
import { TimeChart } from './components/TimeChart'
import { SignalTable } from './components/SignalTable'
import { date, shortDate, number, score, getJSON, type Overview, type StockPoint } from './lib/api'

function exportSignals(data: Overview) {
  const csv = [
    'Observed date,Symbol,Signal,Absolute maximum z-score',
    ...data.anomalies.map((row) =>
      [row.date, row.symbol, row.signal, row.max_zscore ?? '']
        .map((value) => `"${String(value).replaceAll('"', '""')}"`)
        .join(','),
    ),
  ].join('\r\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  link.download = `bvmt-historical-signals-${data.start}-to-${data.as_of}.csv`
  link.click()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}

export default function App() {
  const [collapsed, setCollapsed] = useState(() => window.innerWidth <= 1000)
  const [commandOpen, setCommandOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [days, setDays] = useState(90)
  const [allSymbols, setAllSymbols] = useState(false)
  const [nav, setNav] = useState('overview')
  const query = useQuery({
    queryKey: ['command-center', days],
    queryFn: ({ signal }) => getJSON<Overview>(`/api/command-center?days=${days}`, signal),
  })
  const tickers = useQuery({
    queryKey: ['tickers'],
    queryFn: ({ signal }) => getJSON<{ symbole: string; name: string }[]>('/api/tickers', signal),
  })
  const stock = useQuery({
    queryKey: ['stock', selected],
    queryFn: ({ signal }) =>
      getJSON<StockPoint[]>(`/api/stock/${encodeURIComponent(selected!)}`, signal),
    enabled: !!selected,
  })
  const data = query.data
  const chartPoints = useMemo(
    () => data?.timeline.map((row) => ({ date: row.date, value: row.count })) ?? [],
    [data],
  )
  const stockPoints = useMemo(
    () =>
      stock.data
        ?.filter((row) => row.cloture !== null)
        .map((row) => ({ date: row.date, value: row.cloture! })) ?? [],
    [stock.data],
  )
  const selectSymbol = useCallback((symbol: string) => {
    setCommandOpen(false)
    setSelected(symbol)
  }, [])
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if (event.key.toLowerCase() === 'k' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault()
        setCommandOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', shortcut)
    return () => document.removeEventListener('keydown', shortcut)
  }, [])
  function navigate(id: string) {
    setNav(id)
    if (window.innerWidth <= 1000) setCollapsed(true)
    document.getElementById(id)?.scrollIntoView({ block: 'start' })
  }
  const selectedMeta = data?.symbols.find((symbol) => symbol.symbol === selected)
  const instrumentUnit = selected === 'PX1' || selected === 'TBIDX' ? 'index points' : 'TND'
  const sourceAge = data
    ? Math.max(0, Math.floor((Date.now() - Date.parse(`${data.as_of}T00:00:00Z`)) / 86400000))
    : null
  const qualityIssues = data
    ? data.quality.invalid_dates +
      data.quality.duplicate_rows +
      data.quality.missing_price_or_volume
    : 0
  return (
    <div className={`terminal ${collapsed ? 'is-collapsed' : ''}`}>
      <a className="skip-link" href="#overview">
        Skip to market overview
      </a>
      <aside className="sidebar" aria-label="Main navigation">
        <a href="#overview" className="brand">
          <span className="brand-symbol">
            <BarChart3 size={24} strokeWidth={2.6} />
          </span>
          <span className="brand-word">
            BVMT<span>SURVEILLANCE</span>
          </span>
          <span className="version">2.0</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">TN</span>
          <div>
            Tunis Exchange<small>Research workspace</small>
          </div>
          <span className="workspace-dot" />
        </div>
        <span className="nav-caption">WORKSPACE</span>
        <nav>
          {[
            { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
            { id: 'anomalies', label: 'Historical signals', icon: Radio },
            { id: 'heatmap', label: 'Market universe', icon: Focus },
            { id: 'quality', label: 'Data integrity', icon: Database },
          ].map((item) => (
            <Hint key={item.id} text={item.label}>
              <button
                className={`nav-item ${nav === item.id ? 'active' : ''}`}
                onClick={() => navigate(item.id)}
                aria-label={item.label}
                aria-current={nav === item.id ? 'location' : undefined}
              >
                <item.icon size={17} />
                <span>{item.label}</span>
                {item.id === 'overview' && <span className="nav-indicator" />}
              </button>
            </Hint>
          ))}
        </nav>
        <span className="nav-caption resources-label">RESOURCES</span>
        <button
          className="nav-item"
          onClick={() => setHelpOpen(true)}
          aria-label="Methodology and interpretation"
        >
          <CircleHelp size={17} />
          <span>Methodology</span>
        </button>
        <a
          className="nav-item"
          href="/"
          target="_blank"
          rel="noreferrer"
          aria-label="Open research dashboard"
        >
          <ExternalLink size={17} />
          <span>Research dashboard</span>
        </a>
        {!collapsed && (
          <button className="nav-item mobile-nav-close" onClick={() => setCollapsed(true)}>
            <PanelLeftClose size={17} />
            <span>Collapse navigation</span>
          </button>
        )}
        <div className="sidebar-bottom">
          <div className="archive-card">
            <div>
              <span className="status-dot" />
              HISTORICAL ENVIRONMENT
            </div>
            <p>
              Recorded market observations.
              <br />
              Built for deeper investigation.
            </p>
            <span className="archive-rule" />
          </div>
          <button className="profile" onClick={() => setHelpOpen(true)}>
            <span className="avatar">QR</span>
            <span>
              Quant Research<small>Local analytical workspace</small>
            </span>
            <ChevronRight size={14} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <Button
              variant="ghost"
              size="icon"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              onClick={() => setCollapsed((value) => !value)}
            >
              {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
            </Button>
            <span>Workspace</span>
            <ChevronRight size={12} />
            <strong>Command Center</strong>
          </div>
          <div className="topbar-actions">
            <button className="search-trigger" onClick={() => setCommandOpen(true)}>
              <Search size={14} />
              <span>Search instruments…</span>
              <kbd>Ctrl K</kbd>
            </button>
            <span className="top-divider" />
            <Hint text="This is a historical research dataset, not a live market feed.">
              <span className="environment-tag">
                <span className="status-dot" />
                HISTORICAL
              </span>
            </Hint>
          </div>
        </header>
        <main id="overview">
          <div className="page-heading">
            <div>
              <div className="page-kicker">
                <span className="tiny-cross">+</span> MARKET INTELLIGENCE <span>/</span> TUNIS, TN
              </div>
              <h1>
                Market Command Center<span className="heading-dot">.</span>
              </h1>
              <p>A sharper perspective on unusual market activity.</p>
            </div>
            <div className="heading-actions">
              <Hint text="Reload stored API data. Does not run the scraper or detection pipeline.">
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Refresh stored data"
                  disabled={query.isFetching}
                  onClick={() => {
                    void query.refetch()
                    void tickers.refetch()
                  }}
                >
                  <RefreshCw className={query.isFetching ? 'spin' : ''} size={15} />
                </Button>
              </Hint>
              <Button
                variant="outline"
                disabled={!data}
                onClick={() => data && exportSignals(data)}
              >
                <ArrowDownToLine size={14} />
                Export signals
              </Button>
            </div>
          </div>
          <div className="historical-strip">
            <div>
              <Clock3 size={14} />
              <strong>Historical snapshot</strong>
              <span className="strip-divider" />
              <span>
                Last observation <b className="mono">{data ? date(data.as_of) : '—'}</b>
              </span>
            </div>
            <span className="source-label">
              LOCAL DATASET <span>•</span> NO LIVE FEED
            </span>
          </div>
          {query.isPending && (
            <div className="loading-grid" role="status" aria-label="Loading historical market data">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <div key={i} className={`skeleton skeleton-${i}`} />
              ))}
              <span className="sr-only">Loading historical market data</span>
            </div>
          )}
          {query.isError && (
            <div className="error-box" role="alert">
              <Database size={24} />
              <h2>Historical data could not be loaded</h2>
              <p>{query.error.message}</p>
              <Button variant="outline" onClick={() => void query.refetch()}>
                Retry connection
              </Button>
              {data && <p>The last successful response remains visible below.</p>}
            </div>
          )}
          {data && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.22 }}
            >
              <div className="scope-bar">
                <span>
                  <span className="status-dot" /> OBSERVATION WINDOW{' '}
                  <span className="scope-date mono">
                    {shortDate(data.start)} — {date(data.as_of)}
                  </span>
                </span>
                <div className="segmented" aria-label="Historical observation window">
                  {[30, 90, 365].map((value) => (
                    <button
                      key={value}
                      aria-pressed={days === value}
                      onClick={() => setDays(value)}
                    >
                      {value === 365 ? '1Y' : `${value}D`}
                    </button>
                  ))}
                </div>
              </div>
              <div className="metrics-grid">
                <Metric
                  title="Monitored instruments"
                  value={number(data.metrics.symbols)}
                  subtitle="In the delivered analysis universe"
                  icon={<Focus size={17} />}
                  badge="BVMT"
                />
                <Metric
                  title="Anomalous observations"
                  value={number(data.metrics.flags)}
                  subtitle={`${data.metrics.flagged_symbols} instruments with statistical flags`}
                  icon={<Waves size={18} />}
                  badge={`${days === 365 ? '1Y' : `${days}D`} WINDOW`}
                  accent="cyan"
                />
                <Metric
                  title="High-intensity signals"
                  value={number(data.metrics.high_intensity)}
                  subtitle="Maximum absolute z-score ≥ 4.0"
                  icon={<Activity size={18} />}
                  badge="REVIEW SIGNAL"
                  accent="amber"
                />
                <Metric
                  title="Historical observations"
                  value={number(data.metrics.observations)}
                  subtitle={`Recorded since ${date(data.data_start)}`}
                  icon={<Database size={17} />}
                  badge="SOURCE ROWS"
                />
              </div>
              <div className="analytics-grid">
                <Panel
                  title="Anomaly activity"
                  eyebrow="TEMPORAL ANALYSIS"
                  className="activity-panel"
                  action={
                    <span className="panel-label">
                      <span className="legend-dot cyan" />
                      Detected signals
                    </span>
                  }
                >
                  <div className="chart-summary">
                    <strong className="mono">{number(data.metrics.flags)}</strong>
                    <span>
                      flagged observations
                      <br />
                      <small>
                        {number(data.metrics.window_observations)} source rows in window
                      </small>
                    </span>
                    <div className="chart-summary-end">
                      <span className="mono">{data.timeline.length}</span>
                      <small>recorded sessions</small>
                    </div>
                  </div>
                  <TimeChart points={chartPoints} />
                  <div className="chart-footer">
                    <span>
                      <span className="legend-dot cyan" />
                      Volume or price flag · counted once per observation
                    </span>
                    <details>
                      <summary>View data</summary>
                      <div className="chart-data-list">
                        {data.timeline.map((row) => (
                          <div key={row.date}>
                            <span>{date(row.date)}</span>
                            <b className="mono">{row.count}</b>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                </Panel>
                <Panel
                  title="Signal intensity"
                  eyebrow="DISTRIBUTION"
                  action={
                    <Hint text="Bands group stored flags by max(|volume z-score|, |return z-score|). They describe statistical extremity, not the probability of misconduct.">
                      <button className="info-button" aria-label="About signal intensity">
                        <Info size={15} />
                      </button>
                    </Hint>
                  }
                >
                  <div className="distribution-summary">
                    <span className="mono">
                      {data.metrics.flags
                        ? Math.round((data.metrics.high_intensity / data.metrics.flags) * 100)
                        : 0}
                      <small>%</small>
                    </span>
                    <div>
                      of flags have |z| ≥ 4<small>In the selected historical window</small>
                    </div>
                  </div>
                  <div className="distribution-bars">
                    {data.distribution
                      .filter((bucket) => bucket.label !== 'Unscored' || bucket.count > 0)
                      .map((bucket, index) => (
                        <div className="distribution-row" key={bucket.label}>
                          <span className="mono">{bucket.label}</span>
                          <div className="distribution-track">
                            <div
                              className={`distribution-fill band-${index}`}
                              style={{
                                width: `${(bucket.count / Math.max(1, ...data.distribution.map((b) => b.count))) * 100}%`,
                              }}
                            />
                          </div>
                          <b className="mono">{bucket.count}</b>
                        </div>
                      ))}
                  </div>
                  <div className="interpretation-note">
                    <ShieldCheck size={16} />
                    <span>
                      A signal is a starting point.
                      <br />
                      <strong>Statistical flags are not fraud findings.</strong>
                    </span>
                  </div>
                </Panel>
              </div>
              <div className="detail-grid">
                <Panel
                  id="heatmap"
                  title="Market signal map"
                  eyebrow="CROSS-SECTIONAL VIEW"
                  action={
                    <span className="panel-label mono">
                      {allSymbols ? data.symbols.length : Math.min(24, data.symbols.length)} /{' '}
                      {data.symbols.length}
                    </span>
                  }
                >
                  <div className="heatmap-subtitle">
                    Anomaly count by instrument <span>Equal-sized tiles</span>
                  </div>
                  <div className="heatmap-grid">
                    {data.symbols.slice(0, allSymbols ? undefined : 24).map((symbol) => (
                      <Hint
                        key={symbol.symbol}
                        text={`${symbol.name} · ${symbol.flags} flags · peak ${score(symbol.max_zscore)} · last recorded ${date(symbol.last_date)}. Click to inspect historical prices.`}
                      >
                        <button
                          className={`heat-tile heat-${symbol.flags === 0 ? 'zero' : symbol.flags < 4 ? 'low' : symbol.flags < 9 ? 'medium' : 'high'}`}
                          onClick={() => selectSymbol(symbol.symbol)}
                        >
                          <strong>{symbol.symbol}</strong>
                          <span className="mono">
                            {symbol.flags}
                            <small> flags</small>
                          </span>
                        </button>
                      </Hint>
                    ))}
                  </div>
                  <div className="heatmap-legend">
                    <span>
                      <i className="heat-zero" />0
                    </span>
                    <span>
                      <i className="heat-low" />
                      1–3
                    </span>
                    <span>
                      <i className="heat-medium" />
                      4–8
                    </span>
                    <span>
                      <i className="heat-high" />
                      9+
                    </span>
                    <span>flags / window</span>
                  </div>
                  <button
                    className="panel-bottom-link"
                    onClick={() => setAllSymbols((value) => !value)}
                  >
                    {allSymbols
                      ? 'Show 24 most active instruments'
                      : `Explore all ${data.symbols.length} instruments`}
                    <ArrowUpRight size={13} />
                  </button>
                </Panel>
                <Panel
                  id="anomalies"
                  title="Recent historical signals"
                  eyebrow="ANALYST REVIEW QUEUE"
                  action={<span className="count-badge mono">{data.metrics.flags}</span>}
                >
                  <SignalTable rows={data.anomalies} onSelect={selectSymbol} />
                </Panel>
              </div>
              <section id="quality" className="quality-panel">
                <div className="quality-title">
                  <ShieldCheck size={20} />
                  <div>
                    <h2>Data integrity</h2>
                    <span>Source-level checks</span>
                  </div>
                </div>
                <div className="quality-check">
                  <span>Required values</span>
                  <strong
                    className={data.quality.missing_price_or_volume ? 'text-amber' : 'text-green'}
                  >
                    {data.quality.missing_price_or_volume ? (
                      `${number(data.quality.missing_price_or_volume)} incomplete rows`
                    ) : (
                      <>
                        <Check size={12} />
                        Complete
                      </>
                    )}
                  </strong>
                </div>
                <div className="quality-check">
                  <span>Dates / duplicates</span>
                  <strong className={qualityIssues ? 'text-amber' : 'text-green'}>
                    {data.quality.invalid_dates} invalid / {data.quality.duplicate_rows} duplicate
                  </strong>
                </div>
                <div className="quality-check">
                  <span>At latest source date</span>
                  <strong>
                    {data.quality.symbols_at_as_of} / {data.metrics.symbols} instruments
                  </strong>
                </div>
                <div className="quality-check freshness">
                  <span>Historical freshness</span>
                  <strong className="text-amber">
                    <Clock3 size={12} />
                    {sourceAge} days since observation
                  </strong>
                </div>
              </section>
              {data.quality.lagging_symbols > 0 && (
                <p className="coverage-note">
                  <Info size={12} />
                  {data.quality.lagging_symbols} instruments end before the latest source date.
                  Coverage is uneven; an absent signal does not establish normal trading.
                </p>
              )}
            </motion.div>
          )}
          <footer className="page-footer">
            <span>
              <span className="footer-mark">B</span> BVMT SURVEILLANCE{' '}
              <span className="mono">/ 2.0</span>
            </span>
            <span>Independent research · Historical evidence · Human judgment</span>
            <button onClick={() => setHelpOpen(true)}>
              Methodology & limitations <ArrowUpRight size={11} />
            </button>
          </footer>
        </main>
      </div>
      <CommandDialog
        open={commandOpen}
        onOpenChange={setCommandOpen}
        title="Search market instruments"
        description="Search stored ticker symbols and inspect historical data."
      >
        <CommandInput placeholder="Search a ticker or company name…" />
        <CommandList>
          <CommandEmpty>
            {tickers.isPending
              ? 'Loading instruments…'
              : tickers.isError
                ? 'Ticker search is unavailable. Close and use Refresh stored data to retry.'
                : 'No matching instrument in the local dataset.'}
          </CommandEmpty>
          <CommandGroup heading="AVAILABLE INSTRUMENTS">
            {tickers.data?.map((ticker) => (
              <CommandItem
                key={ticker.symbole}
                value={`${ticker.symbole} ${ticker.name}`}
                onSelect={() => selectSymbol(ticker.symbole)}
              >
                <span className="command-ticker mono">{ticker.symbole}</span>
                <span>{ticker.name}</span>
                <ArrowUpRight className="ml-auto" size={13} />
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
        <div className="command-footer">
          <span>↑ ↓ to navigate</span>
          <span>↵ inspect history</span>
          <span>esc to close</span>
        </div>
      </CommandDialog>
      <Dialog
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      >
        <DialogContent className="instrument-dialog sm:max-w-3xl">
          <DialogHeader>
            <div className="eyebrow text-green">INSTRUMENT INSPECTOR / HISTORICAL</div>
            <DialogTitle className="instrument-title">
              {selected}
              <span>
                {selectedMeta?.name ||
                  tickers.data?.find((ticker) => ticker.symbole === selected)?.name}
              </span>
            </DialogTitle>
            <DialogDescription>
              Actual stored closing values · {instrumentUnit} · up to 252 recorded observations. No
              live quote.
            </DialogDescription>
          </DialogHeader>
          {stock.isPending && (
            <div
              className="skeleton stock-loading"
              role="status"
              aria-label="Loading instrument history"
            />
          )}
          {stock.isError && (
            <div className="error-box" role="alert">
              <p>{stock.error.message}</p>
              <Button variant="outline" onClick={() => void stock.refetch()}>
                Retry history
              </Button>
            </div>
          )}
          {stock.data && (
            <>
              <div className="instrument-stats">
                <div>
                  <span>Last stored close</span>
                  <strong className="mono">
                    {stockPoints.at(-1)?.value.toFixed(3) ?? 'N/A'} <small>{instrumentUnit}</small>
                  </strong>
                </div>
                <div>
                  <span>Last priced observation</span>
                  <strong className="mono">
                    {stockPoints.at(-1) ? date(stockPoints.at(-1)!.date) : 'N/A'}
                  </strong>
                </div>
                <div>
                  <span>Flags in selected window</span>
                  <strong className="mono">
                    {selectedMeta?.flags ?? 'Not in analysis universe'}
                  </strong>
                </div>
              </div>
              <TimeChart points={stockPoints} price unit={instrumentUnit} />
              <details className="price-data">
                <summary>View recorded closing values</summary>
                <div>
                  {stockPoints.map((point) => (
                    <div key={point.date}>
                      <span>{date(point.date)}</span>
                      <span className="mono">
                        {point.value.toFixed(3)} {instrumentUnit}
                      </span>
                    </div>
                  ))}
                </div>
              </details>
              <div className="inspector-notice">
                <Info size={14} />
                Gaps between recorded observations may reflect thin trading or missing coverage.
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="methodology-dialog">
          <DialogHeader>
            <DialogTitle>Evidence before conclusions.</DialogTitle>
            <DialogDescription>BVMT Surveillance / Research methodology</DialogDescription>
          </DialogHeader>
          <div className="methodology-copy">
            <p>
              This terminal presents existing statistical detector outputs. The reference detector
              uses a 60-trading-day rolling baseline, excludes the current day from that baseline,
              and applies a 3.0 z-score cutoff. Volume is transformed using log(1 + volume);
              long-gap returns are excluded by the analytical pipeline.
            </p>
            <p>
              The dashboard counts a stored observation once when either its price or volume flag is
              true. Intensity is the larger absolute z-score. It is not a misconduct probability.
            </p>
            <p>
              All window boundaries are anchored to the latest price date in the delivered analysis
              dataset. The queue is ordered by observation date, not detection time. News
              classifications and later legal outcomes are not represented as information available
              on the signal date.
            </p>
            <p>
              Coverage differs across instruments. This academic project is independent of BVMT and
              CMF. Signals require human review; they are not confirmed fraud or investment advice.
            </p>
            <a href="/" target="_blank" rel="noreferrer">
              Open the existing evaluation and research dashboard <ExternalLink size={13} />
            </a>
            <a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">
              Charts powered by TradingView Lightweight Charts™ <ExternalLink size={13} />
            </a>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
