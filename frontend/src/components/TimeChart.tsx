import { useEffect, useRef, useState } from 'react'
import { AreaSeries, ColorType, createChart, type IChartApi, type Time } from 'lightweight-charts'
import { Maximize2 } from 'lucide-react'
import { Button } from './ui/button'

export interface ChartPoint {
  date: string
  value: number
}
export function TimeChart({
  points,
  unit = 'signals',
  price = false,
}: {
  points: ChartPoint[]
  unit?: string
  price?: boolean
}) {
  const element = useRef<HTMLDivElement>(null)
  const chart = useRef<IChartApi | null>(null)
  const [hover, setHover] = useState('')
  useEffect(() => {
    if (!element.current || !points.length) return
    const instance = createChart(element.current, {
      autoSize: true,
      localization: { locale: 'en-GB' },
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8393a8',
        fontFamily: 'IBM Plex Mono',
        fontSize: 10,
        attributionLogo: true,
      },
      grid: { vertLines: { color: '#182332' }, horzLines: { color: '#182332' } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.15, bottom: 0.08 } },
      timeScale: {
        borderVisible: false,
        timeVisible: false,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      crosshair: {
        vertLine: { color: '#55d8d0', labelBackgroundColor: '#163c44' },
        horzLine: { color: '#43616c', labelBackgroundColor: '#163c44' },
      },
      handleScroll: {
        mouseWheel: false,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
    })
    const series = instance.addSeries(AreaSeries, {
      lineColor: price ? '#42e6b1' : '#4dd6d1',
      topColor: price ? '#27ce941f' : '#4dd6d129',
      bottomColor: '#4dd6d100',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      priceFormat: { type: 'price', precision: price ? 3 : 0, minMove: price ? 0.001 : 1 },
    })
    const unique = [
      ...new Map(
        points
          .filter((p) => /^\d{4}-\d{2}-\d{2}$/.test(p.date) && Number.isFinite(p.value))
          .map((p) => [p.date, p]),
      ).values(),
    ].sort((a, b) => a.date.localeCompare(b.date))
    series.setData(unique.map((p) => ({ time: p.date as Time, value: p.value })))
    instance.timeScale().fitContent()
    instance.subscribeCrosshairMove((param) => {
      const point = param.seriesData.get(series)
      if (!param.time || !point || !('value' in point)) {
        setHover('')
        return
      }
      const time =
        typeof param.time === 'object'
          ? `${param.time.year}-${String(param.time.month).padStart(2, '0')}-${String(param.time.day).padStart(2, '0')}`
          : String(param.time)
      setHover(`${time}  ·  ${point.value.toFixed(price ? 3 : 0)} ${unit}`)
    })
    chart.current = instance
    return () => {
      chart.current = null
      instance.remove()
    }
  }, [points, price, unit])
  return (
    <div className="chart-wrap">
      <div className="chart-toolbar">
        <span className="chart-readout mono">
          {hover ||
            (price
              ? `Historical closing value · ${unit}`
              : 'Flagged observations / recorded session')}
        </span>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Fit chart to data"
          onClick={() => chart.current?.timeScale().fitContent()}
        >
          <Maximize2 size={13} />
        </Button>
      </div>
      {points.length ? (
        <div
          className="time-chart"
          ref={element}
          role="img"
          aria-label={
            price
              ? 'Interactive historical closing price chart'
              : 'Interactive historical anomaly count chart'
          }
        />
      ) : (
        <div className="empty">No observations in this window.</div>
      )}
    </div>
  )
}
