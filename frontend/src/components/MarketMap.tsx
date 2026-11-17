import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { Maximize2, Minimize2 } from 'lucide-react'
import { getJSON } from '../lib/api'
import { Failure, Loading } from '../App'
import '../market-map.css'

type Timeframe = '1D' | '1W' | '1M' | 'YTD'
type ColorBy = 'Daily change' | 'Max |z|' | 'Flag intensity'
type SizeBy = 'Traded value' | 'Flag count' | 'Equal'
type SymbolRow = {
  symbol: string
  name: string
  last_date: string
  close: number | null
  change_pct: number | null
  avg_traded_value_20d: number | null
  traded_on_asof: boolean
  flags_30d: number
  max_abs_z_30d: number | null
}
type Response = { as_of: string; symbols: SymbolRow[] }
type Tile = { row: SymbolRow; x: number; y: number; w: number; h: number }

const fmt = (value: number | null, digits = 2) =>
  value == null
    ? '—'
    : new Intl.NumberFormat('en-GB', { maximumFractionDigits: digits }).format(value)
const pct = (value: number | null) =>
  value == null ? 'no trade' : `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`

// Squarified layout: order by weight, then add a row while its worst aspect ratio improves.
function squarify(
  rows: SymbolRow[],
  weight: (row: SymbolRow) => number,
  width: number,
  height: number,
): Tile[] {
  const ordered = rows
    .map((row) => ({ row, value: Math.max(weight(row), 0.0001) }))
    .sort((a, b) => b.value - a.value)
  const total = ordered.reduce((sum, item) => sum + item.value, 0)
  const items = ordered.map((item) => ({ ...item, area: (item.value / total) * width * height }))
  const result: Tile[] = []
  let x = 0,
    y = 0,
    w = width,
    h = height
  const worst = (line: typeof items) => {
    const sum = line.reduce((n, item) => n + item.area, 0)
    const min = Math.min(...line.map((item) => item.area))
    const max = Math.max(...line.map((item) => item.area))
    const side = Math.min(w, h)
    return Math.max((side * side * max) / (sum * sum), (sum * sum) / (side * side * min))
  }
  const place = (line: typeof items) => {
    const area = line.reduce((n, item) => n + item.area, 0)
    if (w < h) {
      const rowH = area / w
      let cursor = x
      line.forEach((item) => {
        const tileW = item.area / rowH
        result.push({ row: item.row, x: cursor, y, w: tileW, h: rowH })
        cursor += tileW
      })
      y += rowH
      h -= rowH
    } else {
      const colW = area / h
      let cursor = y
      line.forEach((item) => {
        const tileH = item.area / colW
        result.push({ row: item.row, x, y: cursor, w: colW, h: tileH })
        cursor += tileH
      })
      x += colW
      w -= colW
    }
  }
  let line: typeof items = []
  for (const item of items) {
    if (line.length && worst([...line, item]) > worst(line)) {
      place(line)
      line = []
    }
    line.push(item)
  }
  if (line.length) place(line)
  return result
}

function percentile95(values: number[]) {
  if (!values.length) return 1
  const sorted = values.slice().sort((a, b) => a - b)
  const rank = (sorted.length - 1) * 0.95
  const low = Math.floor(rank),
    high = Math.ceil(rank)
  return Math.max(0.01, sorted[low] + (sorted[high] - sorted[low]) * (rank - low))
}

export default function MarketMap({ open }: { open: (symbol: string) => void }) {
  const [tf, setTf] = useState<Timeframe>('1D')
  const [colorBy, setColorBy] = useState<ColorBy>('Daily change')
  const [sizeBy, setSizeBy] = useState<SizeBy>('Traded value')
  const [search, setSearch] = useState('')
  const [fullscreen, setFullscreen] = useState(false)
  const [active, setActive] = useState(0)
  const [dimensions, setDimensions] = useState({ width: 900, height: 260 })
  const surface = useRef<HTMLDivElement>(null)
  const tilesRef = useRef<HTMLDivElement>(null)
  const previous = useRef(new Map<string, { x: number; y: number }>())
  const query = useQuery({
    queryKey: ['market-map', tf],
    queryFn: ({ signal }) => getJSON<Response>(`/api/heatmap?tf=${tf}`, signal),
    staleTime: 15 * 60 * 1000,
  })
  const rows = query.data?.symbols ?? []
  useEffect(() => {
    if (!surface.current) return
    const observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width
      setDimensions({
        width,
        height: fullscreen ? Math.max(300, innerHeight - 280) : 260,
      })
    })
    observer.observe(surface.current)
    return () => observer.disconnect()
  }, [fullscreen])
  const ordered = useMemo(
    () => rows.slice().sort((a, b) => a.symbol.localeCompare(b.symbol)),
    [rows],
  )
  const size = (row: SymbolRow) =>
    sizeBy === 'Equal'
      ? 1
      : sizeBy === 'Flag count'
        ? Math.max(row.flags_30d, 0.2)
        : Math.max(row.avg_traded_value_20d ?? 0, 1)
  const tiles = useMemo(
    () => squarify(rows, size, dimensions.width, dimensions.height),
    [rows, sizeBy, dimensions],
  )
  const metric = (row: SymbolRow) =>
    colorBy === 'Daily change'
      ? row.change_pct
      : colorBy === 'Max |z|'
        ? row.max_abs_z_30d
        : row.flags_30d
  // The scale is symmetric and clamps at the 95th percentile of absolute, available values.
  const clamp = percentile95(
    rows
      .filter((row) => row.traded_on_asof)
      .map(metric)
      .filter((v): v is number => v != null)
      .map(Math.abs),
  )
  const positive = colorBy !== 'Daily change'
  const color = (row: SymbolRow) => {
    if (!row.traded_on_asof) return '#38454e'
    const value = metric(row)
    if (value == null || value === 0) return '#34434b'
    const strength = Math.min(Math.abs(value) / clamp, 1)
    const alpha = (0.22 + strength * 0.62).toFixed(3)
    return value < 0 && !positive ? `rgba(225,143,134,${alpha})` : `rgba(109,214,191,${alpha})`
  }
  const summary = (list: SymbolRow[]) => list.map((r) => r.symbol).join(', ') || 'none'
  const gainers = rows
    .filter((r) => r.traded_on_asof && r.change_pct != null)
    .sort((a, b) => b.change_pct! - a.change_pct!)
    .slice(0, 5)
  const losers = rows
    .filter((r) => r.traded_on_asof && r.change_pct != null)
    .sort((a, b) => a.change_pct! - b.change_pct!)
    .slice(0, 5)
  const flagged = rows
    .filter((r) => r.flags_30d > 0)
    .sort((a, b) => b.flags_30d - a.flags_30d)
    .slice(0, 5)
  const move = (index: number, direction: number) => {
    const next = (index + direction + ordered.length) % ordered.length
    setActive(next)
    surface.current
      ?.querySelector<HTMLButtonElement>(`[data-symbol="${ordered[next].symbol}"]`)
      ?.focus()
  }
  useGSAP(
    () => {
      if (
        !rows.length ||
        matchMedia('(prefers-reduced-motion: reduce)').matches ||
        !tilesRef.current
      )
        return
      gsap.from(tilesRef.current.querySelectorAll('.market-tile'), {
        scale: 0.96,
        opacity: 0,
        duration: 0.35,
        stagger: { each: 0.006, amount: 0.25 },
        ease: 'power2.out',
      })
    },
    { scope: tilesRef, dependencies: [query.data?.as_of, tf], revertOnUpdate: true },
  )
  useLayoutEffect(() => {
    if (!tilesRef.current) return
    const next = new Map<string, { x: number; y: number }>()
    tiles.forEach((tile) => {
      next.set(tile.row.symbol, { x: tile.x, y: tile.y })
      const old = previous.current.get(tile.row.symbol)
      const element = tilesRef.current?.querySelector<HTMLElement>(
        `[data-symbol="${tile.row.symbol}"]`,
      )
      if (old && element && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
        gsap.fromTo(
          element,
          { x: old.x - tile.x, y: old.y - tile.y },
          { x: 0, y: 0, duration: 0.35, ease: 'power2.out', overwrite: true },
        )
      }
    })
    previous.current = next
  }, [tiles])
  if (query.isPending) return <Loading />
  if (query.isError) return <Failure error={query.error} retry={() => void query.refetch()} />
  return (
    <section className={`market-map ${fullscreen ? 'fullscreen' : ''}`} aria-label="Market Map">
      <div className="market-map-head">
        <div>
          <h2>Market Map</h2>
          <strong>Data as of {query.data.as_of}</strong>
          <span>
            {sizeBy === 'Traded value'
              ? 'Size: avg traded value (20d)'
              : sizeBy === 'Flag count'
                ? 'Size: flag count (30d)'
                : 'Size: equal'}
          </span>
        </div>
      </div>
      <div className="market-controls">
        <label>
          Timeframe{' '}
          <select value={tf} onChange={(e) => setTf(e.target.value as Timeframe)}>
            {(['1D', '1W', '1M', 'YTD'] as const).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Color by{' '}
          <select value={colorBy} onChange={(e) => setColorBy(e.target.value as ColorBy)}>
            {(['Daily change', 'Max |z|', 'Flag intensity'] as const).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Size by{' '}
          <select value={sizeBy} onChange={(e) => setSizeBy(e.target.value as SizeBy)}>
            {(['Traded value', 'Flag count', 'Equal'] as const).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label>
          Find ticker{' '}
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value.toUpperCase())}
            placeholder="e.g. BIAT"
          />
        </label>
        <button
          className="market-fullscreen"
          onClick={() => setFullscreen(!fullscreen)}
          aria-label={fullscreen ? 'Exit fullscreen' : 'Fullscreen map'}
        >
          {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>
      <div
        className="market-legend"
        aria-label={`${colorBy} scale clamped at 95th percentile of absolute values: ${fmt(clamp)}${colorBy === 'Daily change' ? '%' : ''}`}
      >
        <span>{colorBy === 'Daily change' ? `−${fmt(clamp)}%` : '0'}</span>
        <i className={positive ? 'positive' : ''} />
        <span>0</span>
        {!positive && (
          <>
            <i className="positive" />
            <span>+{fmt(clamp)}%</span>
          </>
        )}
        {positive && (
          <span>
            +{fmt(clamp)}
            {colorBy === 'Max |z|' ? 'σ' : ' flags'}
          </span>
        )}
        <small>95th percentile clamp · amber outline = flagged · grey = no trade</small>
      </div>
      <p className="sr-only">
        Top five gainers: {summary(gainers)}. Top five losers: {summary(losers)}. Top five flagged:{' '}
        {summary(flagged)}.
      </p>
      <div className="market-surface" ref={surface}>
        <div
          className="market-tiles"
          ref={tilesRef}
          style={{ height: dimensions.height }}
          role="group"
          aria-label={`${rows.length} BVMT symbols; use arrow keys to move between tiles`}
        >
          {tiles.map(({ row, x, y, w, h }) => {
            const area = w * h
            const detail = `${row.name} (${row.symbol}). Close ${fmt(row.close, 3)}. Change ${pct(row.change_pct)}. Average traded value over 20 sessions ${fmt(row.avg_traded_value_20d)}. Last trade ${row.last_date}. ${row.flags_30d} flags in 30 days. Max absolute z ${fmt(row.max_abs_z_30d)}.`
            return (
              <button
                key={row.symbol}
                data-symbol={row.symbol}
                className={`market-tile ${row.flags_30d ? 'flagged' : ''} ${row.max_abs_z_30d != null && row.max_abs_z_30d >= 4 ? 'intense' : ''} ${search && !row.symbol.includes(search) ? 'dimmed' : ''}`}
                style={{
                  left: x + 0.5,
                  top: y + 0.5,
                  width: Math.max(0, w - 1),
                  height: Math.max(0, h - 1),
                  background: color(row),
                }}
                tabIndex={ordered[active]?.symbol === row.symbol ? 0 : -1}
                aria-label={detail}
                title={detail}
                onFocus={() => setActive(ordered.findIndex((item) => item.symbol === row.symbol))}
                onKeyDown={(e) => {
                  if (['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'].includes(e.key)) {
                    e.preventDefault()
                    move(
                      ordered.findIndex((item) => item.symbol === row.symbol),
                      e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : -1,
                    )
                  }
                }}
                onClick={() => open(row.symbol)}
              >
                {area > 2600 && (
                  <>
                    <b>{row.symbol}</b>
                    {area > 4600 && <span>{pct(row.change_pct)}</span>}
                  </>
                )}
                <span className="market-tooltip" aria-hidden="true">
                  {row.name} · {row.symbol}
                  <br />
                  Close {fmt(row.close, 3)} · {pct(row.change_pct)}
                  <br />
                  Traded value {fmt(row.avg_traded_value_20d)}
                  <br />
                  Last trade {row.last_date}
                  <br />
                  {row.flags_30d} flags / 30d · Max |z| {fmt(row.max_abs_z_30d)}
                </span>
              </button>
            )
          })}
        </div>
        <div className="market-list">
          {rows
            .slice()
            .sort((a, b) => size(b) - size(a))
            .map((row) => (
              <button
                key={row.symbol}
                className={search && !row.symbol.includes(search) ? 'dimmed' : ''}
                style={{ borderLeft: `3px solid ${color(row)}` }}
                onClick={() => open(row.symbol)}
              >
                <b>{row.symbol}</b>
                <span>{row.name}</span>
                <strong>{pct(row.change_pct)}</strong>
                {row.flags_30d > 0 && <em>◉ {row.flags_30d}</em>}
              </button>
            ))}
        </div>
      </div>
      <p className="market-note">
        Screening for human review, not a verdict. No sector data is available; this is a flat map.
      </p>
    </section>
  )
}
