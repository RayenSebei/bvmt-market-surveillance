import { type UseQueryResult } from '@tanstack/react-query'
import { Failure, Loading, n, Pane } from '../App'
import { type Overview } from '../lib/api'
export default function PipelinePage({ overview }: { overview: UseQueryResult<Overview, Error> }) {
  if (overview.isPending) return <Loading />
  if (overview.isError)
    return <Failure error={overview.error} retry={() => void overview.refetch()} />
  const d = overview.data!
  return (
    <div className="v2-page">
      <div className="v2-grid two">
        <Pane id="PIP-01" title="Source coverage">
          <div className="v2-big-stat">
            {n(d.metrics.observations)}
            <span>stored observations</span>
          </div>
          <div className="v2-facts">
            <div>
              <span>Universe</span>
              <b>{n(d.metrics.symbols)} symbols</b>
            </div>
            <div>
              <span>First recorded</span>
              <b>{d.data_start}</b>
            </div>
            <div>
              <span>Latest recorded</span>
              <b>{d.as_of}</b>
            </div>
            <div>
              <span>Symbols at latest date</span>
              <b>{n(d.quality.symbols_at_as_of)}</b>
            </div>
            <div>
              <span>Lagging symbols</span>
              <b>{n(d.quality.lagging_symbols)}</b>
            </div>
          </div>
        </Pane>
        <Pane id="PIP-02" title="Integrity checks">
          <div className="v2-facts">
            <div>
              <span>Invalid dates</span>
              <b>{n(d.quality.invalid_dates)}</b>
            </div>
            <div>
              <span>Duplicate rows</span>
              <b>{n(d.quality.duplicate_rows)}</b>
            </div>
            <div>
              <span>Missing price or volume</span>
              <b>{n(d.quality.missing_price_or_volume)}</b>
            </div>
          </div>
          <p className="v2-note">
            This is a read-only view of stored files. Refresh repeats API requests; it does not
            rerun scraping or the detector.
          </p>
        </Pane>
      </div>
      <Pane id="PIP-03" title="Coverage by symbol">
        <div className="v2-table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Symbol</th>
                <th scope="col">Name</th>
                <th scope="col">Latest date</th>
                <th scope="col">Flags in window</th>
                <th scope="col">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {d.symbols.map((s) => (
                <tr key={s.symbol}>
                  <td>
                    <b>{s.symbol}</b>
                  </td>
                  <td>{s.name}</td>
                  <td className="mono">{s.last_date}</td>
                  <td className="mono">{n(s.flags)}</td>
                  <td>
                    <span className={s.last_date === d.as_of ? 'v2-chip' : 'v2-chip amber'}>
                      {s.last_date === d.as_of ? 'At as-of' : 'Lagging'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Pane>
    </div>
  )
}
