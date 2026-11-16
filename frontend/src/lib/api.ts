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
  ouverture?: number | null
  haut?: number | null
  bas?: number | null
  volume_zscore?: number | null
  return_zscore?: number | null
  flag?: Flag | null
}
export interface Flag {
  symbole: string
  ticker_name: string
  date: string
  cloture: number | null
  volume: number | null
  daily_return: number | null
  volume_zscore: number | null
  return_zscore: number | null
  max_zscore: number
  signal: string
  signal_intensity: string
  news_nearby: boolean
  news_status: string
  matched_headline: string
  matched_news_date: string
  category: string
  priority?: number | null
  tag?: string
  co_flagged_count?: number | null
}
export interface FlagPage {
  rows: Flag[]
  total: number
  page: number
  page_size: number
  pages: number
}
export interface FlagDetail {
  flag: Flag
  news: { date: string; headline: string; url: string | null; gap_days: number }[]
  prices: { date: string; cloture: number | null }[]
  watchlist: {
    tag: string
    ai_assessment: string
    ai_reasoning: string
    ai_output_fresh: boolean
  } | null
}
export interface NewsItem {
  symbole: string
  date: string
  time: string
  headline: string
  url: string | null
  ticker_name: string
  linked_flag_date: string
}
export interface WatchResponse {
  rows: Flag[]
  total: number
  decay: {
    symbole: string
    ticker_name: string
    decline_ratio: number
    days_since_active: number
  }[]
  ai_output_fresh: boolean
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
