import { describe, it, expect } from 'vitest'
import { upsertStepStarted, applyStepFinished } from '../data/pipeline-events'
import { resolveCopy, hasDeliverable, canViewDetail } from '../data/deliverables'
import { buildSubmitViews, reviewLabel, uploadLabel } from '../data/submit-status'
import { toUserMessage } from '../data/error-messages'

describe('pipeline step upsert', () => {
  it('重复 step_started 不重复新增', () => {
    let steps = upsertStepStarted([], { step: 'market_input', name: '读取市场数据', agent: 'MarketInputAgent' })
    steps = upsertStepStarted(steps, { step: 'market_input', name: '读取市场数据', agent: 'MarketInputAgent' })
    expect(steps).toHaveLength(1)
    expect(steps[0].name).toBe('读取市场数据')
  })

  it('不同 step 追加', () => {
    let steps = upsertStepStarted([], { step: 'market_input', name: '读取市场数据', agent: 'A' })
    steps = upsertStepStarted(steps, { step: 'gap_check', name: '覆盖检查', agent: 'B' })
    expect(steps).toHaveLength(2)
  })

  it('step_finished 更新对应步骤状态', () => {
    let steps = upsertStepStarted([], { step: 'gap_check', name: '覆盖检查', agent: 'B' })
    steps = applyStepFinished(steps, { step: 'gap_check', artifact: 'gap-check.json' })
    expect(steps[0].status).toBe('passed')
    expect(steps[0].artifact).toBe('gap-check.json')
  })

  it('step_finished success=false → failed', () => {
    let steps = upsertStepStarted([], { step: 'build_qa', name: '构建', agent: 'QA' })
    steps = applyStepFinished(steps, { step: 'build_qa', success: false, error: '构建失败' })
    expect(steps[0].status).toBe('failed')
    expect(steps[0].error).toBe('构建失败')
  })
})

describe('deliverable resolver', () => {
  const job = {
    path: 'D:/out/job1',
    miniapp_path: 'D:/out/job1/generated/miniapp',
    artifacts: {
      'qa-report.json': { checks: { dist_exists: true, dist_path: 'D:/out/job1/.../mp-weixin' } },
      'submit-status.json': { platforms: [] },
      'prd.md': '# PRD\n内容',
    },
  }

  it('miniapp 复制 miniapp_path', () => {
    expect(resolveCopy(job, 'miniapp')).toEqual({ mode: 'path', value: 'D:/out/job1/generated/miniapp' })
  })
  it('dist 复制 dist_path', () => {
    expect(resolveCopy(job, 'dist').value).toBe('D:/out/job1/.../mp-weixin')
  })
  it('publish-package 复制 job.path/publish-package', () => {
    expect(resolveCopy(job, 'publish-package').value).toBe('D:/out/job1/publish-package')
  })
  it('md 复制内容', () => {
    const r = resolveCopy(job, 'prd.md')
    expect(r.mode).toBe('content')
    expect(r.value).toContain('# PRD')
  })
  it('hasDeliverable / canViewDetail', () => {
    expect(hasDeliverable(job, 'miniapp')).toBe(true)
    expect(hasDeliverable(job, 'dist')).toBe(true)
    expect(canViewDetail(job, 'prd.md')).toBe(true)
    expect(canViewDetail(job, 'miniapp')).toBe(false)
  })
})

describe('submit status mapper', () => {
  it('未配置 → 提示缺字段，不可上传', () => {
    const views = buildSubmitViews({
      platformReadiness: [{ platform: 'wechat', name_cn: '微信小程序', configured: false, can_upload: false, missing_fields: ['appid', 'private_key_path'] }],
      submitStatus: [{ platform_id: 'wechat', upload_status: 'not_started', review_status: 'not_submitted' }],
      targetPlatforms: ['wechat'],
      authStatus: [],
      distExists: true,
    })
    const w = views[0]
    expect(w.configured).toBe(false)
    expect(w.can_upload).toBe(false)
    expect(w.missing_fields).toContain('appid')
    expect(w.next_action).toContain('配置')
    expect(w.recommended).toBe(true)
  })

  it('配置好 + dist 存在 → 可上传', () => {
    const views = buildSubmitViews({
      platformReadiness: [{ platform: 'wechat', name_cn: '微信小程序', configured: true, can_upload: true, missing_fields: [] }],
      submitStatus: [{ platform_id: 'wechat', upload_status: 'not_started', review_status: 'not_submitted' }],
      targetPlatforms: ['wechat'], authStatus: [], distExists: true,
    })
    expect(views[0].can_upload).toBe(true)
    expect(views[0].next_action).toContain('上传到微信开发版本')
  })

  it('已上传 → 待人工提交审核', () => {
    const views = buildSubmitViews({
      platformReadiness: [{ platform: 'wechat', name_cn: '微信小程序', configured: true, can_upload: true }],
      submitStatus: [{ platform_id: 'wechat', upload_status: 'uploaded', review_status: 'not_submitted' }],
      targetPlatforms: ['wechat'], authStatus: [], distExists: true,
    })
    expect(views[0].upload_status).toBe('uploaded')
    expect(views[0].next_action).toContain('提交审核')
  })

  it('labels', () => {
    expect(reviewLabel('in_review').text).toBe('审核中')
    expect(uploadLabel('uploaded').text).toBe('已上传')
  })
})

describe('error message mapper', () => {
  it('401', () => expect(toUserMessage({ status: 401 })).toContain('认证失败'))
  it('409', () => expect(toUserMessage({ status: 409 })).toContain('正在运行'))
  it('404', () => expect(toUserMessage({ status: 404 })).toContain('启动试运行'))
  it('500', () => expect(toUserMessage({ status: 500 })).toContain('后端服务异常'))
  it('fetch failed', () => expect(toUserMessage({ message: 'Failed to fetch' })).toContain('后端连接失败'))
  it('400 带 detail', () => expect(toUserMessage({ status: 400, detail: { message: 'bad field' } })).toContain('bad field'))
})
