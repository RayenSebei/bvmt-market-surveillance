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
type KnownRate = {
  k: number
  known_event_nearby_flags: number
  wilson_low: number
  wilson_high: number
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
type Phase2Row = {
  method: string
  split: string
  hits: number
  events: number
  wilson_low: number
  wilson_high: number
  flags: number
  flags_per_week: number
  negative_control_flags: number
  negative_control_flags_collapsed: number
  permutation_p: number
}
type Phase2Verdict = {
  selected_candidate: string
  held_out_positives: number
  adopt_candidate: boolean
  market_wide_tagged: number
  market_wide_total: number
}
export default function EvaluationPage() {
  const phase2 = useQuery({
    queryKey: ['phase2-comparison'],
    queryFn: ({ signal }) => getJSON<Phase2Row[]>('/api/evaluation/phase2/comparison', signal),
  })
  const verdict = useQuery({
    queryKey: ['phase2-verdict'],
    queryFn: ({ signal }) => getJSON<Phase2Verdict>('/api/evaluation/phase2/verdict', signal),
  })
  const metrics = useQuery({
    queryKey: ['v2-eval-metrics'],
    queryFn: ({ signal }) => getJSON<Metric[]>('/api/evaluation/metrics', signal),
  })
  const baselines = useQuery({
    queryKey: ['v2-eval-baselines'],
    queryFn: ({ signal }) => getJSON<Baseline[]>('/api/evaluation/baselines', signal),
  })
  const knownRates = useQuery({
    queryKey: ['v2-known-event-rates'],
    queryFn: ({ signal }) => getJSON<KnownRate[]>('/api/evaluation/precision', signal),
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
  const at20 = knownRates.data?.find((row) => row.k === 20)
  const denominator = Number(get('eligible_positive_events_30d') ?? 0)
  const expandedReference = phase2.data?.find(
    (row) => row.method === 'reference_v1' && row.split === 'held_out',
  )
  const pct = (value: number) => `${(100 * value).toFixed(1)}%`
  const wilson = (k: number, total: number) => {
    if (!total) return '—'
    const z = 1.959963984540054
    const p = k / total
    const base = 1 + (z * z) / total
    const center = (p + (z * z) / (2 * total)) / base
    const half = (z * Math.sqrt((p * (1 - p)) / total + (z * z) / (4 * total * total))) / base
    return `${pct(Math.max(0, center - half))}–${pct(Math.min(1, center + half))}`
  }
  return (
    <div className="v2-page">
      <div className="v2-callout amber">
        Phase 2 keeps reference_v1. The selected {verdict.data?.selected_candidate ?? 'candidate'}
        {expandedReference &&
          ` and reference_v1 each hit ${expandedReference.hits} of ${expandedReference.events} held-out positive events`}
        . The held-out set is too small to establish improvement.
      </div>
      <Pane
        id="EVA-P2"
        title="Frozen-split method comparison"
        action={<span className="v2-muted">Primary window −30/+5 calendar days</span>}
      >
        {phase2.isPending && <Loading />}
        {phase2.isError && <Failure error={phase2.error} retry={() => void phase2.refetch()} />}
        <div className="v2-table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Method</th>
                <th scope="col">Split</th>
                <th scope="col">Hits / events · 95% Wilson</th>
                <th scope="col">Flags / week</th>
                <th scope="col">Negative-control flags</th>
                <th scope="col">Controls, shared notice collapsed</th>
                <th scope="col">Random p</th>
              </tr>
            </thead>
            <tbody>
              {phase2.data?.map((row) => (
                <tr key={`${row.method}-${row.split}`}>
                  <td>
                    <b>{row.method.replaceAll('_', ' ')}</b>
                  </td>
                  <td>{row.split === 'held_out' ? 'Held out' : 'Development'}</td>
                  <td>
                    {row.hits} of {row.events} · {pct(row.wilson_low)}–{pct(row.wilson_high)}
                  </td>
                  <td>
                    {row.flags_per_week.toFixed(2)} <small>({n(row.flags)} total)</small>
                  </td>
                  <td>{row.negative_control_flags}</td>
                  <td>{row.negative_control_flags_collapsed}</td>
                  <td>{row.permutation_p.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="v2-note">
          Six candidate detectors were tried. Same-count random placements use 1,000 seeds.
          Intervals describe uncertainty in this small sourced event set; they are not accuracy
          estimates. ADWYA is exploratory and excluded from control counts. The collapsed count
          treats the shared PGH/Land'Or notice as one control cluster.
        </p>
      </Pane>
      <div className="v2-grid two">
        <Pane id="EVA-REVIEW" title="Top-flag review summary">
          <div className="v2-prose">
            <p>
              Among the 20 highest ranked reference flags: six have likely corporate-action context,
              two have suspected data glitches, three show thin-trading artifacts, and nine remain
              unexplained in stored material.
            </p>
            <p>
              {verdict.data?.market_wide_tagged ?? '—'} of {verdict.data?.market_wide_total ?? '—'}{' '}
              stock flags meet the predeclared market-wide tag threshold. Review classes are
              provisional and do not establish wrongdoing.
            </p>
          </div>
        </Pane>
        <Pane id="EVA-LIMIT" title="What this does and does not prove">
          <div className="v2-prose">
            <p>
              It shows dated flags near a small set of sourced events, with workload, negative
              controls, and a fixed held-out split.
            </p>
            <p>
              It cannot establish wrongdoing, estimate accuracy for all market days, or prove that
              no nearby ilboursa headline is suspicious. ilboursa is the sole stored news source.
              Human review is required.
            </p>
          </div>
        </Pane>
      </div>
      {metrics.isPending && <Loading />}
      {metrics.isError && <Failure error={metrics.error} retry={() => void metrics.refetch()} />}
      <div className="v2-kpis">
        {[
          {
            label: 'RECALL / 30D',
            value: denominator ? `${get('recall_30d_hits')} of ${denominator}` : '—',
            sub: denominator
              ? `95% Wilson ${pct(Number(get('recall_30d_wilson_low')))}–${pct(Number(get('recall_30d_wilson_high')))}; original 1 of 3`
              : '—',
          },
          {
            label: 'EVALUABLE POSITIVES',
            value: String(get('eligible_positive_events_30d') ?? '—'),
            sub: 'Small sourced case study set',
          },
          { label: 'FLAG LOAD', value: n(reference?.flag_count), sub: 'Reference union flags' },
          {
            label: 'KNOWN-EVENT @ 20',
            value: at20 ? `${at20.known_event_nearby_flags} of ${at20.k}` : '—',
            sub: at20 ? `95% Wilson ${pct(at20.wilson_low)}–${pct(at20.wilson_high)}` : '—',
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
                <b>
                  {b.method.startsWith('random_')
                    ? `mean ${(b.recall_30d * denominator).toFixed(2)} of ${denominator}`
                    : `${Math.round(b.recall_30d * denominator)} of ${denominator}`}
                </b>
                {!b.method.startsWith('random_') && (
                  <small>
                    95% Wilson {wilson(Math.round(b.recall_30d * denominator), denominator)}
                  </small>
                )}
                <small>{n(b.flag_count)} flags</small>
              </div>
            ))}
          </div>
          <p className="v2-note">
            Reference and return-only results are descriptive on the expanded sourced set. A smaller
            flag load can matter operationally; this set cannot establish comparative performance.
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
                      <strong>
                        {s && get('eligible_positive_events_30d')
                          ? `${Math.round(s.recall_30d * Number(get('eligible_positive_events_30d')))}/${get('eligible_positive_events_30d')}`
                          : '—'}
                      </strong>
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
