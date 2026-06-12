import type { JobSummary, JobDetail, DemoResult } from '../types/job'

const BASE = 'http://localhost:8000'

async function get<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  getJobs: () => get<{ jobs: JobSummary[] }>('/api/jobs'),
  getLatestJob: () => get<JobDetail>('/api/jobs/latest'),
  getJob: (id: string) => get<JobDetail>(`/api/jobs/${id}`),
  startPipeline: (mode: string = 'demo') => post<DemoResult>('/api/demo/start', { mode }),
  getRealInputs: () => get<{ apps: any[]; exists: boolean }>('/api/real-inputs/apps'),
  saveRealInputs: (apps: any[]) => post('/api/real-inputs/apps', apps),
}
