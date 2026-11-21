import { useRef, useState } from 'react'
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
  const [scrollTop, setScrollTop] = useState(0)
  const [active, setActive] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)
  const virtual = rows.length > 200
  const rowHeight = 62
  const start = virtual ? Math.max(0, Math.floor(scrollTop / rowHeight) - 5) : 0
  const end = virtual ? Math.min(rows.length, start + 19) : rows.length
  const visible = rows.slice(start, end)
  const move = (index: number) => {
    const next = Math.max(0, Math.min(rows.length - 1, index))
    setActive(next)
    if (virtual && scrollRef.current)
      scrollRef.current.scrollTop = Math.max(0, (next - 4) * rowHeight)
  }
  return (
    <>
      <div
        ref={scrollRef}
        className={virtual ? 'v2-table-scroll v2-virtual-table' : 'v2-table-scroll'}
        onScroll={(event) => setScrollTop(event.currentTarget.scrollTop)}
        tabIndex={rows.length ? 0 : undefined}
        aria-label="Flag rows. Use J and K to move, Enter to inspect."
        onKeyDown={(event) => {
          if (event.key === 'j' || event.key === 'ArrowDown') {
            event.preventDefault()
            move(active + 1)
          }
          if (event.key === 'k' || event.key === 'ArrowUp') {
            event.preventDefault()
            move(active - 1)
          }
          if (event.key === 'Enter' && rows[active]) {
            event.preventDefault()
            open(rows[active].symbole, rows[active].date)
          }
        }}
      >
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
            {virtual && start > 0 && (
              <tr aria-hidden="true" className="v2-spacer">
                <td colSpan={priority ? 7 : 6} style={{ height: start * rowHeight }} />
              </tr>
            )}
            {visible.map((r, i) => (
              <tr
                key={`${r.symbole}-${r.date}-${start + i}`}
                className={active === start + i ? 'selected' : ''}
                aria-selected={active === start + i}
              >
                {priority && <td>{n(r.priority ?? start + i + 1)}</td>}
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
            {virtual && end < rows.length && (
              <tr aria-hidden="true" className="v2-spacer">
                <td
                  colSpan={priority ? 7 : 6}
                  style={{ height: (rows.length - end) * rowHeight }}
                />
              </tr>
            )}
          </tbody>
        </table>
        {!rows.length && <Empty text="No flags match this view. Adjust the filters or range." />}
      </div>
      {virtual && (
        <p className="v2-note">
          {rows.length} rows in this API page; visible rows are rendered as you scroll.
        </p>
      )}
    </>
  )
}
