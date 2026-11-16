import { useState } from 'react'
import { type Flag } from '../lib/api'
import { Empty, n } from '../App'
export function FlagRows({
  rows,
  open,
  priority = false,
}: {
  rows: Flag[]
  open: (symbol: string, date?: string) => void
  priority?: boolean
}) {
  const [page, setPage] = useState(0)
  const visible = rows.slice(page * 50, (page + 1) * 50)
  return (
    <>
      <div className="v2-table-scroll">
        <table>
          <thead>
            <tr>
              {priority && <th scope="col">Rank</th>}
              <th scope="col">Observed</th>
              <th scope="col">Symbol</th>
              <th scope="col">Signal</th>
              <th scope="col">Max |z|</th>
              <th scope="col">News context</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((r, i) => (
              <tr key={`${r.symbole}-${r.date}-${i}`}>
                {priority && <td>{n(r.priority ?? i + 1)}</td>}
                <td className="mono">{r.date}</td>
                <td>
                  <b>{r.symbole}</b>
                  <small>{r.ticker_name}</small>
                </td>
                <td>{r.signal}</td>
                <td className="mono">{r.max_zscore?.toFixed(2) ?? '—'}</td>
                <td>
                  <span className={r.news_nearby ? 'v2-chip' : 'v2-chip amber'}>
                    {r.news_status}
                  </span>
                </td>
                <td>
                  <button className="v2-row-action" onClick={() => open(r.symbole, r.date)}>
                    Inspect ↗
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <Empty text="No flags match this view. Adjust the filters or range." />}
      </div>
      {rows.length > 50 && (
        <div className="v2-pagination">
          <button disabled={page === 0} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span>
            {page + 1} / {Math.ceil(rows.length / 50)}
          </span>
          <button disabled={(page + 1) * 50 >= rows.length} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </>
  )
}
