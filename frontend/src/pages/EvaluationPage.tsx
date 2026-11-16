import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Empty, Failure, Loading, n, Pane } from '../App'
import { getJSON } from '../lib/api'
type Metric = { metric: string; value: string | number; detail: string }
type Baseline = {
  method: string
  flag_count: number
  recall_30d: number
  precision_at_20: number
  negative_control_flags_30d: number
}
type Sensitivity = {
  z_cutoff: number
  rolling_window: number
  flag_count: number
  recall_30d: number
}
type Event = {
  event_id: string
  ticker: string
  event_name: string
  event_date: string
  source: string
  confidence: string
  evaluable: string | boolean
  evaluable_reason: string
}
export default function EvaluationPage() {
  const metrics = useQuery({
    queryKey: ['v2-eval-metrics'],
    queryFn: ({ signal }) => getJSON<Metric[]>('/api/evaluation/metrics', signal),
  })
  const baselines = useQuery({
    queryKey: ['v2-eval-baselines'],
    queryFn: ({ signal }) => getJSON<Baseline[]>('/api/evaluation/baselines', signal),
  })
  const sensitivity = useQuery({
    queryKey: ['v2-eval-sensitivity'],
    queryFn: ({ signal }) => getJSON<Sensitivity[]>('/api/evaluation/sensitivity', signal),
  })
  const events = useQuery({
    queryKey: ['v2-eval-events'],
    queryFn: ({ signal }) => getJSON<Event[]>('/api/evaluation/events', signal),
  })
  const get = (key: string) => metrics.data?.find((m) => m.metric === key)?.value
  const reference = baselines.data?.find((b) => b.method === 'reference_union')
  return (
    <div className="v2-page">
      <div className="v2-callout amber">
        Case-study-level evaluation. The reference detector recalls 1 of 3 eligible positive cases
        at 30 days, P@20 is 0, and it does not beat the return-only baseline. These are weak
        results.
      </div>
      {metrics.isPending && <Loading />}
      {metrics.isError && <Failure error={metrics.error} retry={() => void metrics.refetch()} />}
      <div className="v2-kpis">
        {[
          {
            label: 'RECALL / 30D',
            value: reference ? `${(reference.recall_30d * 100).toFixed(1)}%` : '—',
            sub: '1 of 3 eligible cases',
          },
          {
            label: 'EVALUABLE POSITIVES',
            value: String(get('eligible_positive_events_30d') ?? '—'),
            sub: 'Small case study set',
          },
          { label: 'FLAG LOAD', value: n(reference?.flag_count), sub: 'Reference union flags' },
          {
            label: 'PRECISION @ 20',
            value: reference ? String(reference.precision_at_20) : '—',
            sub: 'No known case in top 20',
          },
        ].map((k, i) => (
          <section className="v2-kpi" key={k.label}>
            <div>
              <span>{k.label}</span>
              <small>0{i + 1}</small>
            </div>
            <strong>{k.value}</strong>
            <p>{k.sub}</p>
          </section>
        ))}
      </div>
      <div className="v2-grid two">
        <Pane
          id="EVA-01"
          title="Baseline comparison"
          action={<span className="v2-muted">30-day recall · descriptive</span>}
        >
          {baselines.isError && (
            <Failure error={baselines.error} retry={() => void baselines.refetch()} />
          )}
          <div className="v2-baselines">
            {baselines.data?.map((b) => (
              <div key={b.method}>
                <span>{b.method.replaceAll('_', ' ')}</span>
                <div>
                  <i style={{ width: `${b.recall_30d * 100}%` }} />
                </div>
                <b>{(b.recall_30d * 100).toFixed(1)}%</b>
                <small>{n(b.flag_count)} flags</small>
              </div>
            ))}
          </div>
          <p className="v2-note">
            Reference union and return-only both hit 1 of 3. A smaller flag load can matter
            operationally; this set cannot establish comparative performance.
          </p>
        </Pane>
        <Pane id="EVA-02" title="What this does and does not prove">
          <div className="v2-prose">
            <p>
              <b>It shows:</b> how often stored flags preceded the limited labeled events under the
              stated windows and how many flags analysts would review.
            </p>
            <p>
              <b>It cannot show:</b> that a flag indicates wrongdoing, that unlabeled observations
              are true negatives, or that this detector generalizes to future cases.
            </p>
            <p>
              Event dates, supporting sources, and trading coverage require audit. Read each event
              row before drawing a conclusion.
            </p>
          </div>
        </Pane>
      </div>
      <div className="v2-grid two">
        <Pane
          id="EVA-03"
          title="Sensitivity grid"
          action={<span className="v2-muted">Precomputed parameter combinations</span>}
        >
          {sensitivity.isError && (
            <Failure error={sensitivity.error} retry={() => void sensitivity.refetch()} />
          )}
          <div className="v2-sensitivity">
            {[2.5, 3, 3.5, 4].map((z) => (
              <div key={z}>
                <b>z {z.toFixed(1)}</b>
                {[20, 40, 60, 120].map((w) => {
                  const s = sensitivity.data?.find(
                    (v) => v.z_cutoff === z && v.rolling_window === w,
                  )
                  return (
                    <div key={w} className={z === 3 && w === 60 ? 'reference' : ''}>
                      <small>{w}d</small>
                      <strong>{s ? `${Math.round(s.recall_30d * 3)}/3` : '—'}</strong>
                      <span>{n(s?.flag_count)} flags</span>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
          <p className="v2-note">
            Reference setting: z = 3.0, rolling window = 60. Cells are exploratory, not alternative
            production rules.
          </p>
        </Pane>
        <Playground />
      </div>
      <Pane id="EVA-05" title="Event audit">
        {events.isPending && <Loading />}
        {events.isError && <Failure error={events.error} retry={() => void events.refetch()} />}
        <div className="v2-table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Ticker</th>
                <th scope="col">Date</th>
                <th scope="col">Source</th>
                <th scope="col">Confidence</th>
                <th scope="col">Evaluable / reason</th>
              </tr>
            </thead>
            <tbody>
              {events.data?.map((e) => (
                <tr key={e.event_id}>
                  <td>{e.event_name}</td>
                  <td>
                    <b>{e.ticker}</b>
                  </td>
                  <td className="mono">{e.event_date || '—'}</td>
                  <td>{e.source}</td>
                  <td>{e.confidence}</td>
                  <td>
                    {String(e.evaluable)} · {e.evaluable_reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {events.data?.length === 0 && (
            <Empty text="No event audit rows in the stored evaluation." />
          )}
        </div>
      </Pane>
      <p className="v2-note">
        The event audit and aggregate metrics are displayed as supplied by the API; any source-label
        inconsistency should be resolved in the evaluation data, not hidden by the interface.
      </p>
    </div>
  )
}
function Playground() {
  const [z, setZ] = useState(3)
  const [windowSize, setWindowSize] = useState(60)
  const query = useQuery({
    queryKey: ['v2-playground', z, windowSize],
    queryFn: ({ signal }) =>
      getJSON<{
        flag_count: number
        event_hits: number
        event_denominator: number
        flags_per_ticker_year: number
      }>(`/api/playground?z=${z}&window=${windowSize}`, signal),
  })
  const reference = useQuery({
    queryKey: ['v2-playground-reference'],
    queryFn: ({ signal }) =>
      getJSON<{ flag_count: number }>('/api/playground?z=3&window=60', signal),
  })
  return (
    <Pane id="EVA-04" title="Parameter console">
      <div className="v2-controls">
        <label>
          Z cutoff
          <select value={z} onChange={(e) => setZ(Number(e.target.value))}>
            {[2.5, 3, 3.5, 4].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Rolling observations
          <select value={windowSize} onChange={(e) => setWindowSize(Number(e.target.value))}>
            {[20, 40, 60, 120].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <Failure error={query.error} retry={() => void query.refetch()} />
      ) : (
        <div className="v2-big-stat">
          {n(query.data.flag_count)}
          <span>
            precomputed flags · {query.data.event_hits}/{query.data.event_denominator} event hits
          </span>
        </div>
      )}
      <p className="v2-note">
        Difference vs reference grid:{' '}
        {query.data && reference.data
          ? `${query.data.flag_count - reference.data.flag_count >= 0 ? '+' : ''}${n(query.data.flag_count - reference.data.flag_count)} flags`
          : '—'}
        . This read-only lookup does not rerun or change the detector.
      </p>
    </Pane>
  )
}
