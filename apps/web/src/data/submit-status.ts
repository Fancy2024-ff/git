// 上架中心的纯逻辑：把“推荐 + 授权 + 构建 + 上传 + 审核”合并成每个平台一行可读状态。

export type ReviewStatus = 'not_submitted' | 'pending_human' | 'in_review' | 'approved' | 'rejected'
export type UploadStatus = 'not_started' | 'uploaded' | 'failed'

export interface PlatformSubmitView {
  platform_id: string
  name_cn: string
  recommended: boolean        // 当前项目是否推荐该平台
  configured: boolean         // 授权是否已配置
  missing_fields: string[]    // 缺哪些配置
  dist_exists: boolean        // 构建产物是否存在
  can_upload: boolean         // 是否可上传
  upload_status: UploadStatus
  review_status: ReviewStatus
  released: boolean
  next_owner: 'agent' | 'human'
  next_action: string
}

export interface SubmitSources {
  /** readiness.platform_readiness[] */
  platformReadiness: any[]
  /** submit-status.json.platforms[] */
  submitStatus: any[]
  /** opportunity-report.target_platforms[] */
  targetPlatforms: string[]
  /** /api/platform-auth/status -> platforms[] */
  authStatus: any[]
  /** qa-report.checks.dist_exists */
  distExists: boolean
}

const NAME_FALLBACK: Record<string, string> = {
  wechat: '微信小程序', alipay: '支付宝小程序', douyin: '抖音小程序',
  telegram: 'Telegram Mini App', reddit: 'Reddit', discord: 'Discord',
}

function mapReview(raw: string | undefined): ReviewStatus {
  switch (raw) {
    case 'in_review': return 'in_review'
    case 'approved': return 'approved'
    case 'rejected': return 'rejected'
    case 'pending_human': return 'pending_human'
    default: return 'not_submitted'
  }
}

function mapUpload(raw: string | undefined): UploadStatus {
  if (raw === 'uploaded' || raw === 'success') return 'uploaded'
  if (raw === 'failed') return 'failed'
  return 'not_started'
}

/** 合并多来源，产出每个平台的上架视图。以 readiness.platform_readiness 为主干。 */
export function buildSubmitViews(src: SubmitSources): PlatformSubmitView[] {
  const authById = new Map<string, any>()
  for (const a of src.authStatus || []) authById.set(a.platform_id, a)
  const statusById = new Map<string, any>()
  for (const s of src.submitStatus || []) statusById.set(s.platform_id, s)

  const base = (src.platformReadiness || [])
  const views: PlatformSubmitView[] = base.map((pr: any) => {
    const id = pr.platform
    const auth = authById.get(id)
    const st = statusById.get(id)
    const configured = !!(pr.configured ?? auth?.configured)
    const missing = pr.missing_fields || auth?.missing_config || []
    const upload = mapUpload(st?.upload_status)
    const review = mapReview(st?.review_status)
    const released = st?.release_status === 'released'
    const canUpload = !!(pr.can_upload ?? auth?.can_upload) && src.distExists

    return {
      platform_id: id,
      name_cn: pr.name_cn || NAME_FALLBACK[id] || id,
      recommended: (src.targetPlatforms || []).includes(id),
      configured,
      missing_fields: missing,
      dist_exists: src.distExists,
      can_upload: canUpload,
      upload_status: upload,
      review_status: review,
      released,
      next_owner: st?.next_action_owner === 'agent' ? 'agent' : 'human',
      next_action: nextActionText({ configured, canUpload, upload, review, released, missing, id }),
    }
  })
  return views
}

function nextActionText(o: {
  configured: boolean; canUpload: boolean; upload: UploadStatus;
  review: ReviewStatus; released: boolean; missing: string[]; id: string
}): string {
  if (o.released) return '已发布上线'
  if (o.review === 'approved') return '审核通过，可发布'
  if (o.review === 'in_review') return '审核中，等待平台结果'
  if (o.review === 'rejected') return '被拒，查看原因后修正重提'
  if (o.upload === 'uploaded') return '代码已上传，去平台后台提交审核（人工）'
  if (o.upload === 'failed') return '上传失败，检查配置后重试'
  if (!o.configured) {
    const fields = o.missing.length ? `（缺 ${o.missing.join(', ')}）` : ''
    return `人工：配置平台授权${fields}`
  }
  if (o.canUpload) return o.id === 'wechat' ? 'Agent：上传到微信开发版本' : 'Agent：上传到平台'
  return '人工：准备构建产物与授权'
}

/** 审核状态中文 + 色调 */
export function reviewLabel(s: ReviewStatus): { text: string; tone: string } {
  switch (s) {
    case 'in_review': return { text: '审核中', tone: 'blue' }
    case 'approved': return { text: '审核通过', tone: 'green' }
    case 'rejected': return { text: '被拒', tone: 'red' }
    case 'pending_human': return { text: '待人工提交', tone: 'orange' }
    default: return { text: '未提交', tone: 'gray' }
  }
}

export function uploadLabel(s: UploadStatus): { text: string; tone: string } {
  switch (s) {
    case 'uploaded': return { text: '已上传', tone: 'green' }
    case 'failed': return { text: '上传失败', tone: 'red' }
    default: return { text: '未上传', tone: 'gray' }
  }
}
