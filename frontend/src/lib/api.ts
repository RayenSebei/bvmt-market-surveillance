export interface Anomaly {
  symbol: string
  name: string
  date: string
  signal: string
  max_zscore: number | null
  volume_zscore: number | null
  return_zscore: number | null
}
export interface MarketSymbol {
  symbol: string
  name: string
  last_date: string
  flags: number
  max_zscore: number | null
}
export interface Overview {
  as_of: string
  start: string
  data_start: string
  days: number
  metrics: {
    symbols: number
    observations: number
    window_observations: number
    flags: number
    flagged_symbols: number
    high_intensity: number
  }
  quality: {
    invalid_dates: number
    duplicate_rows: number
    missing_price_or_volume: number
    symbols_at_as_of: number
    lagging_symbols: number
  }
  symbols: MarketSymbol[]
  timeline: { date: string; count: number }[]
  anomalies: Anomaly[]
  distribution: { label: string; count: number }[]
}
export interface StockPoint {
  date: string
  cloture: number | null
  volume: number | null
  anomaly: boolean
}
export async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.error || `Request failed (${response.status})`)
  }
  return response.json()
}
export const number = (value: number) => new Intl.NumberFormat('en-GB').format(value)
export const date = (value: string) =>
  new Date(`${value}T12:00:00Z`).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
export const shortDate = (value: string) =>
  new Date(`${value}T12:00:00Z`).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    timeZone: 'UTC',
  })
export const score = (value: number | null) => (value === null ? 'N/A' : `${value.toFixed(2)}σ`)
