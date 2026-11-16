import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Empty, Failure, Loading, Pane, n } from '../App'
import { getJSON, type WatchResponse } from '../lib/api'
type Status = 'Unreviewed' | 'Reviewed' | 'Dismissed'
export default function WatchlistPage({ open }: { open: (symbol: string, date?: string) => void }) {
  const query = useQuery({
    queryKey: ['v2-watchlist'],
    queryFn: ({ signal }) => getJSON<WatchResponse>('/api/watchlist', signal),
  })
  const [statuses, setStatuses] = useState<Record<string, Status>>(
    () =>
      JSON.parse(localStorage.getItem('bvmt-review-status-v2') || '{}') as Record<string, Status>,
  )
  const [active, setActive] = useState(0)
  const [queuePage, setQueuePage] = useState(0)
  const setStatus = (key: string, status: Status) => {
    const next = { ...statuses, [key]: status }
    setStatuses(next)
    localStorage.setItem('bvmt-review-status-v2', JSON.stringify(next))
  }
  const totalRows = query.data?.rows ?? []
  const rows = totalRows.slice(queuePage * 100, (queuePage + 1) * 100)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLSelectElement ||
        e.target instanceof HTMLTextAreaElement ||
        document.querySelector('[role="dialog"]')
      )
        return
      if (e.key === 'j') setActive((i) => Math.min(rows.length - 1, i + 1))
      if (e.key === 'k') setActive((i) => Math.max(0, i - 1))
      if (e.key === 'Enter' && rows[active]) open(rows[active].symbole, rows[active].date)
      if (e.key === 'e' && rows[active])
        setStatus(`${rows[active].symbole}:${rows[active].date}`, 'Reviewed')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [rows, active, open, statuses])
  return (
    <div className="v2-page">
      <div className="v2-callout">
        Review statuses are local-only notes in this browser. They do not change the API or the
        underlying watchlist.
      </div>
      <Pane
        id="QUE-01"
        title="Prioritized review queue"
        action={
          <span className="v2-muted">
            {n(query.data?.total)} rows · J/K move · Enter inspect · E reviewed
          </span>
        }
      >
        {query.isPending && <Loading />}
        {query.isError && <Failure error={query.error} retry={() => void query.refetch()} />}
        {query.data && (
          <div className="v2-table-scroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">Observed</th>
                  <th scope="col">Instrument</th>
                  <th scope="col">Context</th>
                  <th scope="col">Local review status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const key = `${r.symbole}:${r.date}`
                  return (
                    <tr
                      key={key}
                      className={i === active ? 'selected' : ''}
                      onClick={() => setActive(i)}
                    >
                      <td className="mono">{n(r.priority ?? i + 1)}</td>
                      <td className="mono">{r.date}</td>
                      <td>
                        <b>{r.symbole}</b>
                        <small>{r.ticker_name}</small>
                      </td>
                      <td>{r.tag || r.signal}</td>
                      <td>
                        <select
                          aria-label={`Local review status for ${r.symbole} ${r.date}`}
                          value={statuses[key] || 'Unreviewed'}
                          onChange={(e) => setStatus(key, e.target.value as Status)}
                        >
                          <option>Unreviewed</option>
                          <option>Reviewed</option>
                          <option>Dismissed</option>
                        </select>
                      </td>
                      <td>
                        <button className="v2-row-action" onClick={() => open(r.symbole, r.date)}>
                          Inspect ↗
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {!rows.length && <Empty text="The stored review queue is empty." />}
          </div>
        )}
        {totalRows.length > 100 && (
          <div className="v2-pagination">
            <button
              disabled={queuePage === 0}
              onClick={() => {
                setQueuePage(queuePage - 1)
                setActive(0)
              }}
            >
              Previous
            </button>
            <span>
              {queuePage + 1} / {Math.ceil(totalRows.length / 100)}
            </span>
            <button
              disabled={(queuePage + 1) * 100 >= totalRows.length}
              onClick={() => {
                setQueuePage(queuePage + 1)
                setActive(0)
              }}
            >
              Next
            </button>
          </div>
        )}
      </Pane>
      <Pane id="QUE-02" title="Volume decay context">
        <div className="v2-decay">
          {query.data?.decay.slice(0, 20).map((r) => (
            <div key={r.symbole}>
              <b>{r.symbole}</b>
              <span>{r.ticker_name}</span>
              <strong>
                {r.decline_ratio == null ? '—' : `${(r.decline_ratio * 100).toFixed(1)}%`}
              </strong>
            </div>
          ))}
        </div>
      </Pane>
    </div>
  )
}
