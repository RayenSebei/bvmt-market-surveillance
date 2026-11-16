import { lazy, Suspense, useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Bell,
  BookOpen,
  ChartCandlestick,
  ChartNoAxesCombined,
  Database,
  Menu,
  Moon,
  Newspaper,
  Search,
  Sun,
} from 'lucide-react'
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
import { getJSON, type Overview, type StockPoint, type Flag } from './lib/api'
import { Inspector } from './components/Inspector'
import './terminal.css'

const OverviewPage = lazy(() => import('./pages/OverviewPage'))
const FeedPage = lazy(() => import('./pages/FeedPage'))
const StockPage = lazy(() => import('./pages/StockPage'))
const NewsPage = lazy(() => import('./pages/NewsPage'))
const WatchlistPage = lazy(() => import('./pages/WatchlistPage'))
const PipelinePage = lazy(() => import('./pages/PipelinePage'))
const EvaluationPage = lazy(() => import('./pages/EvaluationPage'))
export type Page = 'overview' | 'feed' | 'stock' | 'news' | 'watchlist' | 'pipeline' | 'evaluation'
const pages = [
  { id: 'overview', label: 'Overview', icon: ChartNoAxesCombined },
  { id: 'feed', label: 'Anomaly Feed', icon: Activity },
  { id: 'stock', label: 'Stock Detail', icon: ChartCandlestick },
  { id: 'news', label: 'News', icon: Newspaper },
  { id: 'watchlist', label: 'Watchlist', icon: Bell },
  { id: 'pipeline', label: 'Pipeline', icon: Database },
  { id: 'evaluation', label: 'Evaluation', icon: BookOpen },
] as const
const initial = new URLSearchParams(location.search)
const validPage = (value: string | null): Page =>
  pages.find((p) => p.id === value)?.id ?? 'overview'
export const n = (value: number | null | undefined) =>
  value == null ? '—' : new Intl.NumberFormat('en-GB').format(value)
export function exportCSV(rows: Flag[], name = 'bvmt-flags') {
  const fields: (keyof Flag)[] = [
    'date',
    'symbole',
    'ticker_name',
    'signal',
    'max_zscore',
    'volume_zscore',
    'return_zscore',
    'news_status',
  ]
  const csv = [
    fields.join(','),
    ...rows.map((r) =>
      fields.map((key) => `"${String(r[key] ?? '').replaceAll('"', '""')}"`).join(','),
    ),
  ].join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `${name}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
export function Pane({
  id,
  title,
  children,
  action,
  className = '',
}: {
  id: string
  title: string
  children: React.ReactNode
  action?: React.ReactNode
  className?: string
}) {
  return (
    <section className={`v2-pane ${className}`}>
      <header className="v2-pane-head">
        <div>
          <span className="v2-pane-id">{id}</span>
          <h2>{title}</h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  )
}
export function Loading() {
  return (
    <div className="v2-loading" role="status" aria-label="Loading stored data">
      <div />
      <div />
      <div />
    </div>
  )
}
export function Failure({ error, retry }: { error: Error; retry: () => void }) {
  return (
    <div className="v2-failure" role="alert">
      <strong>Stored data unavailable</strong>
      <p>{error.message}</p>
      <button onClick={retry}>Retry request</button>
    </div>
  )
}
export function Empty({ text }: { text: string }) {
  return <div className="v2-empty">{text}</div>
}
export default function App() {
  const [page, setPage] = useState<Page>(() => validPage(initial.get('view')))
  const [ticker, setTicker] = useState(() => initial.get('ticker') || 'BIAT')
  const [range, setRange] = useState(() => initial.get('range') || '1Y')
  const [selected, setSelected] = useState<{ symbol: string; date?: string } | null>(null)
  const [command, setCommand] = useState(false)
  const [rail, setRail] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('bvmt-theme-v2') || 'dark')
  const overview = useQuery({
    queryKey: ['v2-overview'],
    queryFn: ({ signal }) => getJSON<Overview>('/api/command-center?days=30', signal),
  })
  const tickers = useQuery({
    queryKey: ['v2-tickers'],
    queryFn: ({ signal }) => getJSON<{ symbole: string; name: string }[]>('/api/tickers', signal),
  })
  const stock = useQuery({
    queryKey: [
      'v2-tape',
      overview.data?.symbols
        ?.slice(0, 8)
        .map((s) => s.symbol)
        .join(','),
    ],
    queryFn: async ({ signal }) =>
      Promise.all(
        (overview.data?.symbols ?? []).slice(0, 8).map(async (s) => ({
          symbol: s.symbol,
          flags: s.flags,
          points: await getJSON<StockPoint[]>(
            `/api/stock/${encodeURIComponent(s.symbol)}?range=3M`,
            signal,
          ).catch(() => [] as StockPoint[]),
        })),
      ),
    enabled: !!overview.data,
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('bvmt-theme-v2', theme)
  }, [theme])
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    params.set('view', page)
    params.set('ticker', ticker)
    params.set('range', range)
    history.replaceState(null, '', `${location.pathname}?${params}`)
  }, [page, ticker, range])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setCommand(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  const open = (symbol: string, date?: string) => {
    setSelected({ symbol, date })
    setCommand(false)
  }
  const go = (p: Page) => {
    setPage(p)
    setRail(false)
    window.scrollTo({ top: 0 })
  }
  const tape =
    stock.data?.map((s) => {
      const valid = s.points.filter((p) => p.cloture != null)
      const last = valid.at(-1)?.cloture ?? null
      const prev = valid.at(-2)?.cloture ?? null
      return { ...s, last, change: last != null && prev ? (last / prev - 1) * 100 : null }
    }) ?? []
  return (
    <div className={`v2-app ${rail ? 'rail-open' : ''}`}>
      <a className="v2-skip" href="#workspace">
        Skip to workspace
      </a>
      <aside className="v2-rail" aria-label="Primary navigation">
        <div className="v2-brand">
          <span>
            B<span className="v2-brand-slash">/</span>
          </span>
          <div>
            BVMT<small>SURVEILLANCE</small>
          </div>
          <b>V2</b>
        </div>
        <nav>
          {pages.map((p, i) => (
            <button
              key={p.id}
              aria-label={p.label}
              aria-current={page === p.id ? 'page' : undefined}
              className={page === p.id ? 'active' : ''}
              onClick={() => go(p.id)}
            >
              <p.icon size={18} strokeWidth={1.8} />
              <span>{p.label}</span>
              <em>{String(i + 1).padStart(2, '0')}</em>
            </button>
          ))}
        </nav>
        <div className="v2-rail-foot">
          <span>RESEARCH TERMINAL</span>
          <small>Stored BVMT observations</small>
        </div>
      </aside>
      <div className="v2-body">
        <header className="v2-top">
          <button className="v2-menu" aria-label="Toggle navigation" onClick={() => setRail(!rail)}>
            <Menu size={18} />
          </button>
          <div className="v2-top-title">
            BVMT <span>/</span> {pages.find((p) => p.id === page)?.label}
          </div>
          <div className="v2-top-actions">
            <button className="v2-search" onClick={() => setCommand(true)}>
              <Search size={15} /> <span>Search instrument</span>
              <kbd>Ctrl K</kbd>
            </button>
            <button
              className="v2-icon"
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>
        <div className="v2-tape" aria-label="Stored ticker tape">
          <div className="v2-tape-label">
            MARKET TAPE <span>HISTORICAL</span>
          </div>
          <div className="v2-tape-viewport">
            <div className="v2-tape-track">
              {[...tape, ...tape].map((s, i) => (
                <button
                  key={`${s.symbol}-${i}`}
                  onClick={() => {
                    setTicker(s.symbol)
                    go('stock')
                  }}
                >
                  <b>{s.symbol}</b>
                  <span>{s.last?.toFixed(3) ?? '—'}</span>
                  <span className={s.change != null && s.change < 0 ? 'down' : 'up'}>
                    {s.change == null ? '—' : `${s.change >= 0 ? '+' : ''}${s.change.toFixed(2)}%`}
                  </span>
                  <small>{s.flags} flags</small>
                </button>
              ))}
            </div>
          </div>
        </div>
        <main id="workspace" className="v2-workspace">
          <div className="v2-heading">
            <div>
              <span className="v2-eyebrow">TUNIS EXCHANGE / HISTORICAL SCREENING</span>
              <h1>{pages.find((p) => p.id === page)?.label}</h1>
              <p>Statistical signals and market context for analyst review.</p>
            </div>
            <div className="v2-heading-right">
              <span className="v2-asof">
                DATA AS OF <strong>{overview.data?.as_of || '—'}</strong>
              </span>
              <button className="v2-small-button" onClick={() => void overview.refetch()}>
                Refresh stored data
              </button>
            </div>
          </div>
          <Suspense fallback={<Loading />}>
            {page === 'overview' ? (
              <OverviewPage overview={overview} go={go} open={open} />
            ) : page === 'feed' ? (
              <FeedPage open={open} />
            ) : page === 'stock' ? (
              <StockPage
                ticker={ticker}
                setTicker={setTicker}
                range={range}
                setRange={setRange}
                tickers={tickers.data ?? []}
                open={open}
              />
            ) : page === 'news' ? (
              <NewsPage open={open} />
            ) : page === 'watchlist' ? (
              <WatchlistPage open={open} />
            ) : page === 'pipeline' ? (
              <PipelinePage overview={overview} />
            ) : (
              <EvaluationPage />
            )}
          </Suspense>
        </main>
        <footer className="v2-status">
          <span>
            <i className={overview.isError ? 'offline' : ''} /> API{' '}
            {overview.isError ? 'UNAVAILABLE' : overview.isPending ? 'CONNECTING' : 'READ ONLY'}
          </span>
          <span>AS OF {overview.data?.as_of || '—'}</span>
          <span>{n(overview.data?.quality.symbols_at_as_of)} SYMBOLS AT DATE</span>
          <span>{n(overview.data?.quality.lagging_symbols)} LAGGING</span>
          <span className="v2-disclaimer">
            Statistical flags are review prompts, not findings of misconduct.
          </span>
          <span className="v2-hints">CTRL K SEARCH · ESC CLOSE</span>
        </footer>
      </div>
      <nav className="v2-mobile-nav" aria-label="Mobile navigation">
        {pages.map((p) => (
          <button
            key={p.id}
            aria-label={p.label}
            aria-current={page === p.id ? 'page' : undefined}
            onClick={() => go(p.id)}
          >
            <p.icon size={19} />
            <span>{p.label.split(' ')[0]}</span>
          </button>
        ))}
      </nav>
      <CommandDialog
        open={command}
        onOpenChange={setCommand}
        title="Search instruments"
        description="Choose a stored instrument"
      >
        <CommandInput placeholder="Symbol or company" />
        <CommandList>
          <CommandEmpty>No matching symbol.</CommandEmpty>
          <CommandGroup heading="Instruments">
            {tickers.data?.map((t) => (
              <CommandItem
                key={t.symbole}
                value={`${t.symbole} ${t.name}`}
                onSelect={() => {
                  setTicker(t.symbole)
                  open(t.symbole)
                }}
              >
                {t.symbole} <span className="v2-command-name">{t.name}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
      <Dialog
        open={!!selected}
        onOpenChange={(value) => {
          if (!value) setSelected(null)
        }}
      >
        <DialogContent className="v2-drawer">
          <DialogHeader>
            <DialogTitle>
              {selected?.symbol} <span>/ SIGNAL INSPECTOR</span>
            </DialogTitle>
            <DialogDescription>
              Stored price and statistical context. Human review required.
            </DialogDescription>
          </DialogHeader>
          {selected && <Inspector symbol={selected.symbol} date={selected.date} />}
        </DialogContent>
      </Dialog>
    </div>
  )
}
