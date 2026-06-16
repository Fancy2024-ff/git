# 交付检查清单（可直接用于审查 PR / 改动）

> 每次开发前过 A 段，合入前过 B 段。任一「否」都要先解决或显式标记技术债。

## A. 开发前检查

- [ ] **这个需求属于哪一层？** 能明确指到 apps/api · apps/web · apps/worker · core/<某层>。
- [ ] **应该放在哪个目录？** 已对照 `placement-rules.md` 的 17 类场景确定落点。
- [ ] **是否已有同类模块？** 已查 registry / 已有 adapter / 已有 step / 已有 data 模块，不重造轮子。
- [ ] **是否会破坏架构边界？** 不会把业务塞进 runner.py / main.py / 大组件；不会跨层直调。
- [ ] **是否会引入写死逻辑？** 路径/平台/模板/provider/步骤都走 registry/config/单一事实源。
- [ ] **是否需要下层支持？** 判断是否要新增/复用 classification / capability / platform / runtime 层；
      若依赖的目标目录尚未建立，已决定「按 migration-principles 暂存并标技术债」还是「顺手抽离」。

## B. 开发后检查（合入前）

- [ ] **测试**：新增/更新了对应测试（后端 pytest / 前端 vitest / generator vitest），且本地跑过全绿。
- [ ] **artifact / report / 状态字段**：若产出新数据，已定义 schema、写入 `data/outputs/{jobId}/`、
      字段归入 core/domain 方向，且 API 能读到、前端能展示。
- [ ] **API / 前端**：若涉及对外行为，API 路由与前端展示已同步更新，无遗漏。
- [ ] **大文件红线**：没有把逻辑塞进 runner.py / main.py / 大 Vue 组件；新逻辑在独立模块。
- [ ] **结构债**：没有继续制造结构债；若有不得已的过渡，已在改动说明里显式标记技术债。
- [ ] **状态诚实**：正确区分并如实表达全局状态，绝不一律 passed——
      - `shell_only`（仅骨架）
      - `buildable`（可构建/可提交，但能力未接入）
      - `runtime_ready`（能力齐备可真实运行）
      - `upload_ready`（平台授权齐备可自动上传）
      - `review_ready`（满足提交审核条件）
- [ ] **无写死**：没有写死 路径 / 平台 / 模板 / provider / 步骤。
- [ ] **能力诚实**：未接入的能力为 `provider_missing`，runnable_level 已相应降级，前端/报告未假成功。

## 审查者一句话否决项

出现以下任一，直接打回：
1. 新业务大段进了 runner.py / main.py / 大组件。
2. 平台 if-else 进了 pipeline / api。
3. app 分类 / 可行性在 classification 之外又判了一遍。
4. 能力未接入却返回成功 / 前端显示假 passed。
5. 写死了 路径 / 平台 / 模板 / provider / 步骤。
6. 无测试。
