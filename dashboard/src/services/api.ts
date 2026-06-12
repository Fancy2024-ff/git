import type { JobSummary, JobDetail, DemoResult } from '../types/job'

const BASE = 'http://localhost:8000'

async function get<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  getJobs: () => get<{ jobs: JobSummary[] }>('/api/jobs'),
  getLatestJob: () => get<JobDetail>('/api/jobs/latest'),
  getJob: (id: string) => get<JobDetail>(`/api/jobs/${id}`),
  startDemo: () => post<DemoResult>('/api/demo/start'),
}
