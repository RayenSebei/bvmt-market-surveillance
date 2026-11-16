import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Empty, exportCSV, Failure, Loading, Pane } from '../App'
import { FlagRows } from '../components/FlagRows'
import { getJSON, type FlagPage } from '../lib/api'
const params = new URLSearchParams(location.search)
export default function FeedPage({ open }: { open: (symbol: string, date?: string) => void }) {
  const [symbol, setSymbol] = useState(
    () => params.get('filter') || sessionStorage.getItem('bvmt-feed-symbol') || '',
  )
  const [date, setDate] = useState(() => sessionStorage.getItem('bvmt-feed-date') || '')
  const [signal, setSignal] = useState(() => params.get('signal') || '')
  const [news, setNews] = useState(() => params.get('news') || '')
  const [page, setPage] = useState(1)
  const [views, setViews] = useState<Record<string, string>>(
    () => JSON.parse(localStorage.getItem('bvmt-views-v2') || '{}') as Record<string, string>,
  )
  useEffect(() => {
    const u = new URL(location.href)
    for (const [k, v] of Object.entries({ filter: symbol, signal, news }))
      v ? u.searchParams.set(k, v) : u.searchParams.delete(k)
    history.replaceState(null, '', u)
  }, [symbol, signal, news])
  const query = useQuery({
    queryKey: ['v2-feed', symbol, date, signal, news, page],
    queryFn: ({ signal: abort }) =>
      getJSON<FlagPage>(
        `/api/anomalies/search?page=${page}&page_size=100&sort=date&ticker=${encodeURIComponent(symbol)}&date_from=${date}&date_to=${date}&signal=${signal}&status=${news}`,
        abort,
      ),
  })
  const save = () => {
    const name = prompt('Name this local filter view')
    if (!name) return
    const next = { ...views, [name]: JSON.stringify({ symbol, date, signal, news }) }
    setViews(next)
    localStorage.setItem('bvmt-views-v2', JSON.stringify(next))
  }
  return (
    <div className="v2-page">
      <Pane
        id="FED-01"
        title="Filter the review queue"
        action={<span className="v2-muted">{query.data?.total ?? '—'} matching observations</span>}
      >
        <div className="v2-controls">
          <label>
            Instrument
            <input
              value={symbol}
              onChange={(e) => {
                setSymbol(e.target.value)
                setPage(1)
              }}
              placeholder="Symbol or name"
            />
          </label>
          <label>
            Observed date
            <input
              type="date"
              value={date}
              onChange={(e) => {
                setDate(e.target.value)
                setPage(1)
              }}
            />
          </label>
          <label>
            Signal
            <select
              value={signal}
              onChange={(e) => {
                setSignal(e.target.value)
                setPage(1)
              }}
            >
              <option value="">All channels</option>
              <option value="volume">Volume</option>
              <option value="price">Return</option>
            </select>
          </label>
          <label>
            Local news
            <select
              value={news}
              onChange={(e) => {
                setNews(e.target.value)
                setPage(1)
              }}
            >
              <option value="">Any</option>
              <option value="nearby">Nearby match</option>
              <option value="none">No match</option>
            </select>
          </label>
          <button className="v2-small-button" onClick={save}>
            Save view
          </button>
          <select
            aria-label="Saved local filter views"
            onChange={(e) => {
              const v = views[e.target.value]
              if (v) {
                const state = JSON.parse(v) as {
                  symbol: string
                  date: string
                  signal: string
                  news: string
                }
                setSymbol(state.symbol)
                setDate(state.date)
                setSignal(state.signal)
                setNews(state.news)
              }
            }}
          >
            <option value="">Saved views</option>
            {Object.keys(views).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </div>
        <p className="v2-note">
          Saved views stay in this browser. URL filters can be shared; local saved views do not
          travel with the URL.
        </p>
      </Pane>
      <Pane
        id="FED-02"
        title="Stored flags"
        action={
          <button
            className="v2-small-button"
            disabled={!query.data?.rows.length}
            onClick={() => exportCSV(query.data?.rows ?? [], 'bvmt-filtered-feed')}
          >
            Export visible page CSV
          </button>
        }
      >
        {query.isPending && <Loading />}
        {query.isError && <Failure error={query.error} retry={() => void query.refetch()} />}
        {query.data && (
          <>
            <FlagRows rows={query.data.rows} open={open} />
            <div className="v2-pagination">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span>
                {page} / {query.data.pages || 1}
              </span>
              <button disabled={page >= query.data.pages} onClick={() => setPage(page + 1)}>
                Next
              </button>
            </div>
            {!query.data.total && (
              <Empty text="Try clearing the instrument, date, or news filter." />
            )}
          </>
        )}
      </Pane>
    </div>
  )
}
