import { describe, it, expect } from 'vitest'
import { appTypeName, runnableLevelLabel, feasibilityLabel, capabilityName } from '../data/appTypes'
import { capabilityOverview, type OverviewInput } from '../data/overview'

function base(over: Partial<OverviewInput> = {}): OverviewInput {
  return {
    running: false, candidate: null, opportunity: null, qa: null,
    readiness: null, pipelineReport: null, classification: null, runtime: null, ...over,
  }
}

describe('appTypes 前端镜像', () => {
  it('6 类中文名', () => {
    expect(appTypeName('text_ai')).toBe('文本 AI')
    expect(appTypeName('image_ai')).toBe('图像 AI')
    expect(appTypeName('ocr_scan')).toBe('OCR 扫描')
    expect(appTypeName(undefined)).toBe('未分类')
  })

  it('runnable_level 标签与色调', () => {
    expect(runnableLevelLabel('runtime_ready')).toEqual({ text: '可真实运行', tone: 'green' })
    expect(runnableLevelLabel('buildable').tone).toBe('orange')
    expect(runnableLevelLabel('shell_only').tone).toBe('gray')
  })

  it('feasibility 标签', () => {
    expect(feasibilityLabel('high').text).toBe('高')
    expect(feasibilityLabel('low').tone).toBe('red')
  })

  it('能力中文名', () => {
    expect(capabilityName('image.process')).toBe('图像')
    expect(capabilityName('text.generate')).toBe('文本')
  })
})

describe('capabilityOverview', () => {
  it('无分类/运行数据 → null', () => {
    expect(capabilityOverview(base())).toBeNull()
  })

  it('image_ai 缺 image.process → 暴露缺失能力', () => {
    const o = capabilityOverview(base({
      classification: { app_type: 'image_ai', miniapp_feasibility: 'medium', app_type_confidence: 0.95, required_capabilities: ['image.process'] },
      runtime: { runnable_level: 'buildable', runtime_ready: false, configured_capabilities: [], missing_capabilities: ['image.process'] },
    }))
    expect(o).not.toBeNull()
    expect(o!.appType).toBe('image_ai')
    expect(o!.runnableLevel).toBe('buildable')
    expect(o!.runtimeReady).toBe(false)
    expect(o!.missingCapabilities).toEqual(['image.process'])
  })

  it('text_ai 能力齐备 → runtime_ready', () => {
    const o = capabilityOverview(base({
      classification: { app_type: 'text_ai', miniapp_feasibility: 'high', required_capabilities: ['text.generate'] },
      runtime: { runnable_level: 'runtime_ready', runtime_ready: true, configured_capabilities: ['text.generate'], missing_capabilities: [] },
    }))
    expect(o!.runtimeReady).toBe(true)
    expect(o!.missingCapabilities).toEqual([])
  })

  it('诚实区分：工厂侧能力可执行 但 生成小程序自身不可跑', () => {
    const o = capabilityOverview(base({
      classification: { app_type: 'text_ai', required_capabilities: ['text.generate'] },
      executionReport: {
        app_type: 'text_ai',
        capability_runtime: { 'text.generate': { executable_operations: ['generate', 'chat'] } },
        app_runtime: { runnable: false, reason: '生成的小程序调用的 /api/* 尚未由真实 provider 支撑' },
      },
    }))
    expect(o!.factoryCapabilityReady).toBe(true)    // 工厂侧可执行
    expect(o!.appRuntimeRunnable).toBe(false)       // 小程序自身不可跑（不偷换）
    expect(o!.appRuntimeReason).toContain('provider')
  })
})
