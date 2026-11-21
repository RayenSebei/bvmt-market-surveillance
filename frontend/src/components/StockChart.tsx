import { useEffect, useRef } from 'react'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineSeries,
  createSeriesMarkers,
  type Time,
} from 'lightweight-charts'
import { type StockPoint } from '../lib/api'
export default function StockChart({
  points,
  symbol,
  normalized,
  compare,
}: {
  points: StockPoint[]
  symbol: string
  normalized: { symbol: string; points: { date: string; value: number }[] }[]
  compare: boolean
}) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!ref.current) return
    const chart = createChart(ref.current, {
      autoSize: true,
      height: 340,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8c9eac',
        fontFamily: 'IBM Plex Mono',
      },
      grid: { vertLines: { color: '#253341' }, horzLines: { color: '#253341' } },
      timeScale: { borderVisible: false },
      rightPriceScale: { borderVisible: false },
      handleScroll: { pressedMouseMove: true, mouseWheel: true },
    })
    if (compare) {
      normalized.forEach((s, i) => {
        const series = chart.addSeries(LineSeries, {
          color: ['#55cbb5', '#e3b269', '#d88983'][i],
          lineWidth: 2,
          priceLineVisible: false,
        })
        series.setData(s.points.map((p) => ({ time: p.date as Time, value: p.value })))
      })
    } else {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: '#55cbb5',
        downColor: '#d88983',
        borderVisible: false,
        wickUpColor: '#55cbb5',
        wickDownColor: '#d88983',
      })
      series.setData(
        points
          .filter(
            (p) => p.ouverture != null && p.haut != null && p.bas != null && p.cloture != null,
          )
          .map((p) => ({
            time: p.date as Time,
            open: p.ouverture!,
            high: p.haut!,
            low: p.bas!,
            close: p.cloture!,
          })),
      )
      createSeriesMarkers(
        series,
        points
          .filter((p) => p.flag)
          .map((p) => ({
            time: p.date as Time,
            position: 'aboveBar' as const,
            color: '#e3b269',
            shape: 'circle' as const,
            text: 'F',
          })),
      )
    }
    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [points, normalized, compare])
  return (
    <div
      ref={ref}
      className="v2-stock-chart"
      role="img"
      aria-label={
        compare
          ? `Normalized closing values from 100 for ${normalized.map((s) => s.symbol).join(', ')}. ${normalized.map((s) => `${s.symbol}: ${s.points.length} points, latest ${s.points.at(-1)?.value.toFixed(2) ?? 'unavailable'}`).join('; ')}.`
          : `Candlestick history for ${symbol}, ${points.length} observations from ${points[0]?.date ?? 'unknown'} to ${points.at(-1)?.date ?? 'unknown'}, with ${points.filter((p) => p.flag).length} stored flag markers.`
      }
    />
  )
}
