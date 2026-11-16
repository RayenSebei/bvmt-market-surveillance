import { lazy, Suspense, useMemo, useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { Empty, Failure, Loading, Pane } from '../App'
import { getJSON, type StockPoint } from '../lib/api'
const StockChart = lazy(() => import('../components/StockChart'))
export default function StockPage({
  ticker,
  setTicker,
  range,
  setRange,
  tickers,
  open,
}: {
  ticker: string
  setTicker: (s: string) => void
  range: string
  setRange: (s: string) => void
  tickers: { symbole: string; name: string }[]
  open: (symbol: string, date?: string) => void
}) {
  const [compare, setCompare] = useState<string[]>([])
  const query = useQuery({
    queryKey: ['v2-stock', ticker, range],
    queryFn: ({ signal }) =>
      getJSON<StockPoint[]>(`/api/stock/${encodeURIComponent(ticker)}?range=${range}`, signal),
  })
  const others = useQueries({
    queries: compare.map((symbol) => ({
      queryKey: ['v2-stock', symbol, range],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        getJSON<StockPoint[]>(`/api/stock/${encodeURIComponent(symbol)}?range=${range}`, signal),
    })),
  })
  const normalized = useMemo(
    () =>
      [
        { symbol: ticker, points: query.data ?? [] },
        ...compare.map((symbol, i) => ({ symbol, points: others[i]?.data ?? [] })),
      ].map((series) => {
        const valid = series.points.filter((p) => p.cloture != null)
        const first = valid[0]?.cloture || 1
        return {
          symbol: series.symbol,
          points: valid.map((p) => ({ date: p.date, value: (p.cloture! / first) * 100 })),
        }
      }),
    [ticker, query.data, compare, others],
  )
  const addCompare = (symbol: string) => {
    if (symbol !== ticker && !compare.includes(symbol)) setCompare([...compare, symbol].slice(0, 2))
  }
  return (
    <div className="v2-page">
      <Pane id="STK-01" title="Instrument research">
        <div className="v2-controls">
          <label>
            Instrument
            <select value={ticker} onChange={(e) => setTicker(e.target.value)}>
              {tickers.map((t) => (
                <option key={t.symbole} value={t.symbole}>
                  {t.symbole} · {t.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Range
            <select value={range} onChange={(e) => setRange(e.target.value)}>
              {['3M', '6M', '1Y', 'ALL'].map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <label>
            Compare · up to 3 total
            <select value="" onChange={(e) => addCompare(e.target.value)}>
              <option value="">Add instrument</option>
              {tickers
                .filter((t) => t.symbole !== ticker && !compare.includes(t.symbole))
                .map((t) => (
                  <option key={t.symbole} value={t.symbole}>
                    {t.symbole}
                  </option>
                ))}
            </select>
          </label>
          {compare.map((s) => (
            <button
              className="v2-chip"
              key={s}
              onClick={() => setCompare(compare.filter((v) => v !== s))}
            >
              {s} ×
            </button>
          ))}
        </div>
        {query.isPending && <Loading />}
        {query.isError && <Failure error={query.error} retry={() => void query.refetch()} />}
        {query.data && (
          <>
            <Suspense fallback={<Loading />}>
              <StockChart
                points={query.data}
                symbol={ticker}
                normalized={normalized}
                compare={compare.length > 0}
              />
            </Suspense>
            <p className="v2-note">
              Comparison starts at 100 at each instrument's first available observation in the
              selected range. Gaps and dates may differ. Markers reflect stored flags.
            </p>
          </>
        )}
      </Pane>
      <div className="v2-grid two">
        <Pane id="STK-02" title="Stored flag observations">
          {query.data?.filter((p) => p.flag).length ? (
            <div className="v2-event-list">
              {query.data
                .filter((p) => p.flag)
                .slice(-30)
                .reverse()
                .map((p) => (
                  <button key={p.date} onClick={() => open(ticker, p.date)}>
                    <time>{p.date}</time>
                    <span>{p.flag?.signal}</span>
                    <b>|z| {p.flag?.max_zscore.toFixed(2)}</b>
                  </button>
                ))}
            </div>
          ) : (
            <Empty text="No stored flags in this selected range." />
          )}
        </Pane>
        <Pane id="STK-03" title="Detector channels">
          <div className="v2-facts">
            <div>
              <span>Latest close</span>
              <b>{query.data?.at(-1)?.cloture?.toFixed(3) ?? '—'}</b>
            </div>
            <div>
              <span>Latest volume z</span>
              <b>{query.data?.at(-1)?.volume_zscore?.toFixed(2) ?? '—'}</b>
            </div>
            <div>
              <span>Latest return z</span>
              <b>{query.data?.at(-1)?.return_zscore?.toFixed(2) ?? '—'}</b>
            </div>
          </div>
        </Pane>
      </div>
    </div>
  )
}
