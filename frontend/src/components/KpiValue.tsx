import { useRef } from 'react'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'

export function KpiValue({ value, suffix = '' }: { value: number | null; suffix?: string }) {
  const valueRef = useRef<HTMLElement>(null)
  useGSAP(
    () => {
      const target = valueRef.current
      if (!target) return
      const format = (n: number) =>
        `${new Intl.NumberFormat('en-GB').format(Math.round(n))}${suffix}`
      if (value == null) {
        target.textContent = '—'
        return
      }
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        target.textContent = format(value)
        return
      }
      const counter = { value: 0 }
      gsap.to(counter, {
        value,
        duration: 0.65,
        ease: 'power2.out',
        onUpdate: () => {
          target.textContent = format(counter.value)
        },
        onComplete: () => {
          target.textContent = format(value)
        },
      })
    },
    { scope: valueRef, dependencies: [value, suffix], revertOnUpdate: true },
  )
  return (
    <strong ref={valueRef} className="v2-kpi-value">
      {value == null ? '—' : `${new Intl.NumberFormat('en-GB').format(value)}${suffix}`}
    </strong>
  )
}

export function Sparkline({ values, label }: { values: number[]; label: string }) {
  const max = Math.max(1, ...values)
  const path = values
    .map(
      (v, i) =>
        `${i ? 'L' : 'M'}${(i / Math.max(1, values.length - 1)) * 100} ${19 - (v / max) * 17}`,
    )
    .join(' ')
  return (
    <svg
      className="v2-sparkline"
      viewBox="0 0 100 20"
      preserveAspectRatio="none"
      role="img"
      aria-label={label}
    >
      <path d={path} />
    </svg>
  )
}
