---
name: miniapp-factory-architecture-guardrails
description: "Mini App Factory 最终版目标架构守门规则。当需要给本项目新增功能、判断代码/模块/平台逻辑/provider 逻辑该放在哪、重构目录边界、接入新平台或新能力类型、避免把逻辑继续堆进 runner.py / main.py / Vue 组件、或让项目朝最终版 7x24 工厂架构演进时，必须先使用此技能。"
---

# Mini App Factory 架构守门规则

这是本项目**最终版目标架构 v1.0** 的守门规则。它不是参考文档，是约束：
后续所有新增功能、重构、平台接入、能力接入、自动化补齐，**都必须先经过这套规则判断落位**。

## 这个 Skill 是什么

- 它定义了本项目的**目标架构蓝图**（已冻结，除非用户明确批准改架构，否则不变）。
- 它**不要求每次改动都全量迁移旧代码**。旧代码可暂存。
- 但它要求：**新增代码必须按目标结构落位，不允许继续制造结构债。**
- 它的核心目标：阻止项目退化成「一个大 runner.py + 若干大页面」，让项目持续朝 7x24 自动化工厂架构演进。

## 绝对红线（违反即拒绝该写法）

1. 不允许把大段新业务逻辑塞进 `core/pipeline/runner.py`、`apps/api/main.py`、或某个大 Vue 组件。
2. 不允许写死路径 / 平台 / 模板 / provider / 步骤——必须走 registry / config / 单一事实源。
3. 不允许制造假状态、假成功。能力未接入必须如实表达 `provider_missing` / 降级 `runnable_level`。
4. 不允许在多处重复 app 分类、平台差异、provider 调用逻辑——必须收敛到对应层。

## 使用此 Skill 时，动手前必须先回答四问

1. **这是哪一层？**（apps/api · apps/web · apps/worker · core/* 的某一层）
2. **应该放在哪个目录？**（对照 `references/placement-rules.md`）
3. **是否已有可复用模块？**（先查 registry / 已有 adapter / 已有 step，不要重造）
4. **是否需要新增 artifact / 状态字段 / API / 测试？**（对照 `references/delivery-checklist.md`）

回答不清楚就先读 references，不要凭感觉落位。

## 导航（细节都在 references，不要塞进本文件）

- 目标架构权威说明（每一层职责、为什么分开、绝不能放错的逻辑、模板矩阵、全局状态）
  → `references/target-architecture.md`
- 新增功能放哪的具体规则表（17 类场景 + 可过渡 vs 不可恶化）
  → `references/placement-rules.md`
- 每次开发前/后的检查清单（可直接拿来审查 PR/改动）
  → `references/delivery-checklist.md`
- 现状结构 → 目标结构的迁移原则（何时暂存、何时必须抽离、何时记技术债）
  → `references/migration-principles.md`

## 一句话准则

**新增功能先判层、再落位、不写死、不假状态、不堆大文件；旧代码可暂存但新代码必须朝目标架构靠拢。**
