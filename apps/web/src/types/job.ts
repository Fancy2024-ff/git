export interface JobSummary {
  id: string
  path: string
  app_name?: string
  app_name_en?: string
  qa_passed?: boolean
  build_verified?: boolean
  artifacts?: string[]
  has_miniapp?: boolean
}

export interface JobDetail {
  id: string
  path: string
  artifacts: Record<string, any>
  miniapp_files?: string[]
  miniapp_path?: string
}

export interface PipelineStep {
  step?: string
  name: string
  capability?: string
  status: string
  artifact?: string
  duration_ms?: number
  started_at?: string
  finished_at?: string
  error?: string
  user_message?: string
}

export type PipelineMode = 'demo' | 'real' | 'live'

export interface DemoResult {
  success: boolean
  job_id: string | null
  exit_code: number
  log_lines: number
  logs: string[]
}
