const BASE_URL = ''

export interface RequestOptions {
  showLoading?: boolean
}

export function request<T = any>(
  url: string,
  method: 'GET' | 'POST' = 'GET',
  data?: any,
  options: RequestOptions = {}
): Promise<T> {
  const { showLoading = true } = options

  if (showLoading) uni.showLoading({ title: '加载中...' })

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          uni.showToast({ title: '请求失败', icon: 'none' })
          reject(new Error(`HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
      complete: () => { if (showLoading) uni.hideLoading() },
    })
  })
}
