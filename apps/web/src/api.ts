import axios from 'axios'

export type Watchpoint = { id: string; name: string; latitude: number; longitude: number; timezone: string; tags: string[] }
export type WeatherPoint = { time: string; temperature_c: number | null; wind_speed_ms: number | null; precipitation_mm: number | null; cloud_cover_pct: number | null; shortwave_radiation_wm2: number | null; quality_flag: string }

const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '' })

export async function getWatchpoints() {
  return (await client.get<Watchpoint[]>('/api/v1/watchpoints')).data
}

export async function getForecast(watchpointId: string) {
  return (await client.get<{ watchpoint: Watchpoint; points: WeatherPoint[]; model: string; source: string }>('/api/v1/weather/forecast', { params: { watchpoint_id: watchpointId } })).data
}

export async function getQualitySummary() {
  return (await client.get<{ sources: { name: string; status: string; freshness_minutes: number; coverage_percent: number }[] }>('/api/v1/quality/summary')).data
}
