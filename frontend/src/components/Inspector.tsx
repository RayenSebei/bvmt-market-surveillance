import { useQuery } from '@tanstack/react-query'
import { Copy, ExternalLink, X } from 'lucide-react'
import { getJSON, type FlagDetail, type StockPoint } from '../lib/api'
import { Empty, Failure, Loading, Pane } from '../App'
import { TimeChart } from './TimeChart'
import { DialogClose, DialogDescription, DialogTitle } from './ui/dialog'

export function Inspector({ symbol, date }: { symbol: string; date?: string }) {
  const stock = useQuery({
    queryKey: ['inspector-stock', symbol],
    queryFn: ({ signal }) =>
      getJSON<StockPoint[]>(`/api/stock/${encodeURIComponent(symbol)}?range=1Y`, signal),
  })
  const chosen = date || stock.data?.filter((p) => p.flag).at(-1)?.date
  const detail = useQuery({
    queryKey: ['inspector-detail', symbol, chosen],
    queryFn: ({ signal }) =>
      getJSON<FlagDetail>(`/api/anomaly/${encodeURIComponent(symbol)}/${chosen}`, signal),
    enabled: !!chosen,
  })
  const flag = detail.data?.flag
  const summary = flag
    ? `${flag.symbole} on ${flag.date}: ${flag.signal} statistical flag; volume z ${flag.volume_zscore ?? 'N/A'}, return z ${flag.return_zscore ?? 'N/A'}. ${flag.news_status}. Review required.`
    : ''
  return (
    <div className="v2-inspector-shell">
      <header className="v2-inspector-header">
        <div>
          <span className="v2-pane-id">SIG / SIGNAL INSPECTOR</span>
          <DialogTitle>{symbol}</DialogTitle>
          <DialogDescription>
            {chosen || 'Selecting stored flag'} · {flag?.signal || 'Statistical signal'}
          </DialogDescription>
          <p>Stored price and statistical context. Human review required.</p>
        </div>
        <DialogClose className="v2-inspector-close" aria-label="Close signal inspector">
          <X size={20} aria-hidden="true" />
        </DialogClose>
      </header>
      <div className="v2-inspector-body">
        <div className="v2-inspector">
          {stock.isPending && <Loading />}
          {stock.isError && <Failure error={stock.error} retry={() => void stock.refetch()} />}
          {stock.data && (
            <Pane
              id="SIG-01"
              title="Price context"
              action={<span className="v2-muted">Drag to zoom · stored closes</span>}
            >
              <TimeChart
                points={stock.data
                  .filter((p) => p.cloture != null)
                  .map((p) => ({ date: p.date, value: p.cloture! }))}
                price
                unit={symbol === 'PX1' || symbol === 'TBIDX' ? 'points' : 'TND'}
              />
              <p className="v2-note">
                Flag date: {chosen || 'No stored flag in this range'}. The chart may include
                observations recorded later.
              </p>
            </Pane>
          )}
          {detail.isPending && chosen && <Loading />}
          {detail.isError && <Failure error={detail.error} retry={() => void detail.refetch()} />}
          {flag ? (
            <>
              <div className="v2-z-pair">
                <div>
                  <span>VOLUME Z</span>
                  <strong>{flag.volume_zscore?.toFixed(2) ?? '—'}</strong>
                </div>
                <div>
                  <span>RETURN Z</span>
                  <strong>{flag.return_zscore?.toFixed(2) ?? '—'}</strong>
                </div>
              </div>
              <Pane id="SIG-02" title="Why was this flagged?">
                <p className="v2-prose">
                  A rolling z-score compares the observation with its trailing window. The reference
                  screening rule uses a 60-observation window and a 3.0 absolute z cutoff for volume
                  or return. A flag indicates statistical extremity under that rule. It does not
                  identify a cause.
                </p>
                <button
                  className="v2-small-button"
                  onClick={() => void navigator.clipboard.writeText(summary)}
                >
                  <Copy size={14} /> Copy summary
                </button>
              </Pane>
              <Pane id="SIG-03" title="Nearby news / ±7 days">
                {detail.data?.news.length ? (
                  <div className="v2-event-list">
                    {detail.data.news.map((item, i) => (
                      <div key={i}>
                        <time>{item.date}</time>
                        <span className={item.gap_days <= 0 ? 'v2-chip' : 'v2-chip amber'}>
                          {item.gap_days <= 0 ? 'Available by flag date' : 'Later context'}
                        </span>
                        <p>{item.headline}</p>
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noreferrer">
                            Source <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty text="No ilboursa news match within seven calendar days. This alone is not suspicious." />
                )}
              </Pane>
              <p className="v2-note">
                Peer co-flags:{' '}
                {detail.data?.watchlist
                  ? 'See the watchlist context for this observation.'
                  : 'Not available for this observation.'}
              </p>
            </>
          ) : (
            !chosen &&
            !stock.isPending && (
              <Empty text="No stored flag in this instrument range. Choose a flagged row from the feed to inspect it." />
            )
          )}
        </div>
      </div>
    </div>
  )
}
