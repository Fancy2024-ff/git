// 统一错误文案：把 HTTP 状态码 / 网络错误翻译成小白能处理的中文，
// 而不是裸露 "API error: xxx"。

export interface ApiErrorLike {
  status?: number
  message?: string
  detail?: any
}

const BY_STATUS: Record<number, string> = {
  401: '认证失败，请检查 API Token（前端 VITE_API_TOKEN 需与后端 DASHBOARD_API_KEY 一致）。',
  403: '没有访问权限，请确认请求路径合法。',
  404: '暂无任务数据，请先点击「启动试运行」。',
  409: '已有任务正在运行，请等待当前流水线完成后再启动。',
  413: '产物体积超出下载上限。',
  500: '后端服务异常，请查看运行 API 的终端日志。',
}

/**
 * 把任意错误对象映射成用户可读文案。
 * - 有 status：按状态码映射
 * - fetch failed / Failed to fetch / NetworkError：后端未连接
 * - 其它：回退到原始 message，但带上中文前缀
 */
export function toUserMessage(err: ApiErrorLike | null | undefined): string {
  if (!err) return '发生未知错误，请重试。'

  if (typeof err.status === 'number' && BY_STATUS[err.status]) {
    // 400 校验类错误若带 detail.message，附上后端原因
    return BY_STATUS[err.status]
  }

  const msg = (err.message || '').toLowerCase()
  if (
    msg.includes('failed to fetch') ||
    msg.includes('fetch failed') ||
    msg.includes('networkerror') ||
    msg.includes('load failed') ||
    err.status === 0
  ) {
    return '后端连接失败，请确认已启动后端：python apps/api/main.py'
  }

  if (err.status === 400) {
    const detailMsg = err.detail?.message
    return detailMsg ? `请求有误：${detailMsg}` : '请求参数有误，请检查输入。'
  }

  return err.message ? `操作失败：${err.message}` : '操作失败，请重试。'
}
