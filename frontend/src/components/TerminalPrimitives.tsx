import type { ReactNode } from 'react'
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip'

/** Shared terminal vocabulary for this page and future research views. */
export function Hint({ children, text }: { children: ReactNode; text: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent className="max-w-72">{text}</TooltipContent>
    </Tooltip>
  )
}

export function Panel({
  title,
  eyebrow,
  action,
  children,
  className = '',
  id,
}: {
  title: string
  eyebrow?: string
  action?: ReactNode
  children: ReactNode
  className?: string
  id?: string
}) {
  return (
    <section id={id} className={`panel ${className}`}>
      <div className="panel-heading">
        <div>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}

export function Metric({
  title,
  value,
  subtitle,
  icon,
  badge,
  accent = 'green',
}: {
  title: string
  value: string
  subtitle: string
  icon: ReactNode
  badge: string
  accent?: 'green' | 'cyan' | 'amber'
}) {
  return (
    <section className={`metric-card accent-${accent}`}>
      <div className="metric-top">
        <span>{title}</span>
        {icon}
      </div>
      <div className="metric-value-row">
        <strong className="mono">{value}</strong>
        <span>{badge}</span>
      </div>
      <p>{subtitle}</p>
      <div className="metric-accent" />
    </section>
  )
}
