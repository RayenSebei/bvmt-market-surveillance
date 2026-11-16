import { useMemo, useRef, useState } from 'react'
import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Empty, Failure, Loading, Pane, n, type Page } from '../App'
import { getJSON, type Overview, type Flag } from '../lib/api'
import { FlagRows } from '../components/FlagRows'
import { TimeChart } from '../components/TimeChart'
import { KpiValue, Sparkline } from '../components/KpiValue'
gsap.registerPlugin(useGSAP, ScrollTrigger)

export default function OverviewPage({
  overview,
  go,
  open,
}: {
  overview: UseQueryResult<Overview, Error>
  go: (p: Page) => void
  open: (symbol: string, date?: string) => void
}) {
  const pageRef = useRef<HTMLDivElement>(null)
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
  useGSAP(
    () => {
      if (!data || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
      const strip = pageRef.current?.querySelector<HTMLElement>('.v2-kpis')
      if (!strip) return
      gsap
        .timeline({ defaults: { ease: 'power2.out', duration: 0.24 } })
        .from('.v2-kpi', { y: 12, opacity: 0, stagger: 0.04 })
        .from('.v2-pane', { y: 10, opacity: 0, stagger: 0.035 }, '-=0.12')
      gsap.to(strip, {
        scale: 0.96,
        transformOrigin: 'top center',
        ease: 'none',
        scrollTrigger: {
          trigger: strip,
          start: 'top 104px',
          end: '+=130',
          scrub: true,
        },
      })
    },
    { scope: pageRef, dependencies: [data?.as_of], revertOnUpdate: true },
  )
  const currentFlags = historical.filter(
    (r) => r.date >= (data?.start ?? '') && r.date <= (data?.as_of ?? ''),
  )
  const previousStart = data
    ? new Date(Date.parse(`${data.start}T00:00:00Z`) - 30 * 86400000).toISOString().slice(0, 10)
    : ''
  const previousFlags = historical.filter(
    (r) => r.date >= previousStart && r.date < (data?.start ?? ''),
  )
  const noNews = currentFlags.length
    ? Math.round((currentFlags.filter((r) => !r.news_nearby).length / currentFlags.length) * 100)
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
  const previousSession = data.timeline.filter((r) => r.date < data.as_of).at(-1)?.count ?? null
  const previousNoNewsPct = previousFlags.length
    ? Math.round((previousFlags.filter((r) => !r.news_nearby).length / previousFlags.length) * 100)
    : null
  const delta = (value: number | null, prior: number | null, unit = '') =>
    value == null || prior == null
      ? 'Previous period unavailable'
      : `${value - prior >= 0 ? '+' : ''}${n(value - prior)}${unit} vs previous period`
  const flagDays = data.timeline.map((r) => r.count)
  const highDays = data.timeline.map(
    (d) => currentFlags.filter((r) => r.date === d.date && r.max_zscore >= 4).length,
  )
  const noNewsDays = data.timeline.map(
    (d) => currentFlags.filter((r) => r.date === d.date && !r.news_nearby).length,
  )
  const kpis = [
    {
      label: 'FLAGS AT AS-OF',
      value: today,
      suffix: '',
      sub: delta(today, previousSession),
      tone: 'teal',
      trend: flagDays,
    },
    {
      label: 'FLAGS / 30D',
      value: data.metrics.flags,
      suffix: '',
      sub: radar.data ? delta(data.metrics.flags, previousFlags.length) : 'Previous period loading',
      tone: 'teal',
      trend: flagDays,
    },
    {
      label: 'HIGH INTENSITY',
      value: data.metrics.high_intensity,
      suffix: '',
      sub: radar.data
        ? delta(data.metrics.high_intensity, previousFlags.filter((r) => r.max_zscore >= 4).length)
        : 'Previous period loading',
      tone: 'coral',
      trend: highDays,
    },
    {
      label: 'NO NEARBY NEWS',
      value: noNews,
      suffix: '%',
      sub: delta(noNews, previousNoNewsPct, ' pp'),
      tone: 'amber',
      trend: noNewsDays,
    },
  ]
  return (
    <div className="v2-page v2-overview" ref={pageRef}>
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
            <KpiValue value={k.value} suffix={k.suffix} />
            <p>{k.sub}</p>
            <Sparkline
              values={k.trend}
              label={`${k.label} across ${k.trend.length} recorded sessions; latest ${k.trend.at(-1) ?? 0}`}
            />
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
            role="group"
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
