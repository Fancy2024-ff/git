import type { JobSummary, JobDetail } from '../types/job'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
const API_KEY = import.meta.env.VITE_API_TOKEN || ''

async function get<T = any>(path: string): Promise<T> {
  const headers: Record<string, string> = {}
  if (API_KEY) headers['X-API-Key'] = API_KEY
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T = any>(path: string, body?: any): Promise<T> {
  const headers: Record<string, string> = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (API_KEY) headers['X-API-Key'] = API_KEY
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export interface PipelineStartResult {
  accepted: boolean
  job_id: string
  mode: string
}

export const api = {
  getJobs: () => get<{ jobs: JobSummary[] }>('/api/jobs'),
  getLatestJob: () => get<JobDetail>('/api/jobs/latest'),
  getJob: (id: string) => get<JobDetail>(`/api/jobs/${id}`),
  startPipeline: (mode: string = 'demo') => post<PipelineStartResult>('/api/pipeline/start', { mode }),
  stopPipeline: () => post('/api/pipeline/stop'),
  getPipelineStatus: () => get<{ running: boolean; job_id: string | null; log_lines: number }>('/api/pipeline/status'),
  getRealInputs: () => get<{ apps: any[]; exists: boolean }>('/api/real-inputs/apps'),
  saveRealInputs: (apps: any[]) => post('/api/real-inputs/apps', apps),
  getPlatforms: () => get<{ platforms: any[]; total: number }>('/api/platforms'),
  getPlatformAuth: () => get<{ platforms: any[] }>('/api/platform-auth/status'),
  uploadWechat: () => post<{ upload_passed: boolean; reason: string }>('/api/platforms/wechat/upload'),
}

export function connectPipelineWS(jobId: string, onMessage: (data: any) => void): { disconnect: () => void } {
  let ws: WebSocket | null = null
  let retryCount = 0
  let stopped = false

  function connect() {
    if (stopped) return
    const tokenParam = API_KEY ? `?token=${API_KEY}` : ''
    ws = new WebSocket(`${WS_BASE}/ws/pipeline/${jobId}${tokenParam}`)
    ws.onopen = () => { retryCount = 0 }
    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {
      if (stopped) return
      const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)
      retryCount++
      setTimeout(connect, delay)
    }
  }

  connect()

  return {
    disconnect() {
      stopped = true
      if (ws) { ws.close(); ws = null }
    }
  }
}
