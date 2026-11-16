import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Empty, Failure, Loading, Pane } from '../App'
import { getJSON, type NewsItem } from '../lib/api'
export default function NewsPage({ open }: { open: (symbol: string, date?: string) => void }) {
  const [ticker, setTicker] = useState('')
  const query = useQuery({
    queryKey: ['v2-news', ticker],
    queryFn: ({ signal }) =>
      getJSON<NewsItem[]>(
        `/api/news/recent?limit=100&ticker=${encodeURIComponent(ticker)}`,
        signal,
      ),
  })
  return (
    <div className="v2-page">
      <Pane
        id="NWS-01"
        title="Market news archive"
        action={<span className="v2-muted">Local historical news · sources may be incomplete</span>}
      >
        <div className="v2-controls">
          <label>
            Filter ticker
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. BIAT"
            />
          </label>
        </div>
        {query.isPending && <Loading />}
        {query.isError && <Failure error={query.error} retry={() => void query.refetch()} />}
        {query.data && (
          <div className="v2-news-list">
            {query.data.map((item, i) => (
              <article key={i}>
                <div>
                  <time>
                    {item.date} {item.time}
                  </time>
                  <span className="v2-chip">{item.symbole}</span>
                  {item.linked_flag_date && (
                    <button
                      className="v2-link"
                      onClick={() => open(item.symbole, item.linked_flag_date)}
                    >
                      Related flag · {item.linked_flag_date} ↗
                    </button>
                  )}
                </div>
                <h3>{item.headline}</h3>
                {item.url && (
                  <a href={item.url} rel="noreferrer" target="_blank">
                    Open source ↗
                  </a>
                )}
              </article>
            ))}
            {!query.data.length && <Empty text="No local news items match this ticker." />}
          </div>
        )}
      </Pane>
      <p className="v2-note">
        A news match may be later context, not information available on a flag date. Check the
        inspector timeline before interpreting it.
      </p>
    </div>
  )
}
