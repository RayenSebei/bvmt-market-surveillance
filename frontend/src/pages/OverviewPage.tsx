import { useMemo, useState } from 'react'
import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { Empty, Failure, Loading, Pane, n, type Page } from '../App'
import { getJSON, type Overview, type Flag } from '../lib/api'
import { FlagRows } from '../components/FlagRows'
import { TimeChart } from '../components/TimeChart'

export default function OverviewPage({
  overview,
  go,
  open,
}: {
  overview: UseQueryResult<Overview, Error>
  go: (p: Page) => void
  open: (symbol: string, date?: string) => void
}) {
  const [all, setAll] = useState(false)
  const radar = useQuery({
    queryKey: ['v2-radar'],
    queryFn: ({ signal }) => getJSON<Flag[]>('/api/overview/radar', signal),
  })
  const calendar = useQuery({
    queryKey: ['v2-calendar'],
    queryFn: ({ signal }) =>
      getJSON<{ date: string; count: number }[]>('/api/overview/calendar', signal),
  })
  const historical = useMemo(() => radar.data ?? [], [radar.data])
  const data = overview.data
  const noNews = historical.length
    ? Math.round((historical.filter((r) => !r.news_nearby).length / historical.length) * 100)
    : null
  const months = [...new Set(historical.map((r) => r.date.slice(0, 7)))].sort().slice(-12)
  const grid = new Map<string, number>()
  historical.forEach((r) =>
    grid.set(
      `${r.symbole}:${r.date.slice(0, 7)}`,
      (grid.get(`${r.symbole}:${r.date.slice(0, 7)}`) ?? 0) + 1,
    ),
  )
  if (overview.isPending) return <Loading />
  if (overview.isError && !data)
    return <Failure error={overview.error} retry={() => void overview.refetch()} />
  if (!data) return <Empty text="No stored market snapshot is available." />
  const today = data.timeline.find((r) => r.date === data.as_of)?.count ?? 0
  const kpis = [
    { label: 'FLAGS AT AS-OF', value: n(today), sub: 'Recorded latest date', tone: 'teal' },
    {
      label: 'FLAGS / 30D',
      value: n(data.metrics.flags),
      sub: `${n(data.metrics.window_observations)} source rows`,
      tone: 'teal',
    },
    {
      label: 'HIGH INTENSITY',
      value: n(data.metrics.high_intensity),
      sub: 'Max absolute z ≥ 4',
      tone: 'coral',
    },
    {
      label: 'NO NEARBY NEWS',
      value: noNews == null ? '—' : `${noNews}%`,
      sub: 'Across stored historical flags',
      tone: 'amber',
    },
  ]
  return (
    <div className="v2-page">
      <div className="v2-pulse-title">
        <div>
          <span className="v2-eyebrow">MARKET PULSE / OVR-00</span>
          <h2>One screen. Every signal in context.</h2>
        </div>
        <span>
          OBSERVATION WINDOW · {data.start} → {data.as_of}
        </span>
      </div>
      <div className="v2-kpis">
        {kpis.map((k, i) => (
          <section className={`v2-kpi ${k.tone}`} key={k.label}>
            <div>
              <span>{k.label}</span>
              <small>0{i + 1}</small>
            </div>
            <strong>{k.value}</strong>
            <p>{k.sub}</p>
            <svg viewBox="0 0 100 20" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 17 L12 14 L24 16 L35 8 L45 12 L57 5 L67 10 L79 3 L88 7 L100 2" />
            </svg>
          </section>
        ))}
      </div>
      <div className="v2-grid two">
        <Pane
          id="OVR-01"
          title="Flag activity"
          action={<span className="v2-muted">Recorded sessions / 30 days</span>}
        >
          <TimeChart points={data.timeline.map((r) => ({ date: r.date, value: r.count }))} />
          <p className="v2-note">
            A stored observation is counted once when either detector channel flags it.
          </p>
        </Pane>
        <Pane id="OVR-02" title="Signal composition">
          <div className="v2-distribution">
            {data.distribution.map((r) => (
              <div key={r.label}>
                <span>{r.label}</span>
                <div>
                  <i style={{ width: `${(r.count / Math.max(1, data.metrics.flags)) * 100}%` }} />
                </div>
                <b>{n(r.count)}</b>
              </div>
            ))}
          </div>
          <div className="v2-callout">Intensity is statistical extremity, not misconduct risk.</div>
        </Pane>
      </div>
      <div className="v2-grid two">
        <Pane
          id="OVR-03"
          title="Symbol × month"
          action={
            <button className="v2-link" onClick={() => setAll(!all)}>
              {all ? 'Top 12' : 'All symbols'}
            </button>
          }
        >
          {radar.isError && <Failure error={radar.error} retry={() => void radar.refetch()} />}
          <div className="v2-matrix-scroll">
            <div
              className="v2-matrix"
              style={{ gridTemplateColumns: `90px repeat(${months.length}, minmax(30px, 1fr))` }}
            >
              <span />{' '}
              {months.map((m) => (
                <b key={m}>{m.slice(2)}</b>
              ))}
              {data.symbols.slice(0, all ? undefined : 12).map((s) => (
                <div className="v2-matrix-row" key={s.symbol} style={{ display: 'contents' }}>
                  <strong>{s.symbol}</strong>
                  {months.map((m) => {
                    const count = grid.get(`${s.symbol}:${m}`) ?? 0
                    return (
                      <button
                        key={m}
                        style={{ '--heat': Math.min(count / 8, 1) } as React.CSSProperties}
                        title={`${s.symbol} / ${m}: ${count} flags`}
                        aria-label={`${s.symbol} ${m}: ${count} flags; open filtered feed`}
                        onClick={() => {
                          sessionStorage.setItem('bvmt-feed-symbol', s.symbol)
                          go('feed')
                        }}
                      >
                        {count || ''}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          </div>
          <p className="v2-note">
            Equal cells show counts, not market size. Select a cell to filter the feed by symbol.
          </p>
        </Pane>
        <Pane id="OVR-04" title="Signal radar / 2D">
          <div
            className="v2-radar"
            role="img"
            aria-label="Scatter plot of historical volume and return z-scores; select a point to inspect"
          >
            <div className="v2-axis-x">VOLUME Z →</div>
            <div className="v2-axis-y">RETURN Z →</div>
            {historical.slice(0, 400).map((r, i) => (
              <button
                key={i}
                title={`${r.symbole} · ${r.date} · volume ${r.volume_zscore} · return ${r.return_zscore}`}
                style={{
                  left: `${Math.max(4, Math.min(96, 50 + (r.volume_zscore ?? 0) * 5))}%`,
                  bottom: `${Math.max(5, Math.min(95, 50 + (r.return_zscore ?? 0) * 5))}%`,
                }}
                onClick={() => open(r.symbole, r.date)}
              />
            ))}
          </div>
          <p className="v2-note">
            Points are stored flags. Positions are capped for legibility; inspect a row for exact
            values.
          </p>
        </Pane>
      </div>
      <div className="v2-grid two">
        <Pane id="OVR-05" title="Flag calendar">
          <div className="v2-calendar">
            {calendar.data?.slice(-120).map((r) => (
              <button
                key={r.date}
                title={`${r.date}: ${r.count} flags`}
                aria-label={`${r.date}: ${r.count} flags`}
                className={r.count > 3 ? 'strong' : r.count ? 'some' : ''}
                onClick={() => {
                  sessionStorage.setItem('bvmt-feed-date', r.date)
                  go('feed')
                }}
              />
            ))}
          </div>
          <p className="v2-note">
            Last 120 recorded flag dates. Select a date to inspect the feed.
          </p>
        </Pane>
        <Pane
          id="OVR-06"
          title="Latest review prompts"
          action={
            <button className="v2-link" onClick={() => go('feed')}>
              Open full feed ↗
            </button>
          }
        >
          <FlagRows
            rows={data.anomalies.slice(0, 8).map((r) => ({
              ...r,
              max_zscore: r.max_zscore ?? 0,
              symbole: r.symbol,
              ticker_name: r.name,
              cloture: null,
              volume: null,
              daily_return: null,
              signal_intensity: '',
              news_nearby: false,
              news_status: 'See inspector',
              matched_headline: '',
              matched_news_date: '',
              category: '',
            }))}
            open={open}
          />
        </Pane>
      </div>
      <p className="v2-note">
        Universe: {n(data.metrics.symbols)} symbols · {n(data.metrics.observations)} stored
        observations since {data.data_start}. Coverage and historical news linkage vary by symbol.
      </p>
    </div>
  )
}
