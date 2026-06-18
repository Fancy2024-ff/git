# core/shared — 跨域共享

## 职责
只放 truly shared 的内容：schema、types、constants、纯工具函数。
不放任何域专属业务逻辑。

## 模块
- `models.py` — 跨域 pydantic 模型与枚举（AppInfo / GapOpportunity / PRDDocument /
  MiniAppProject / AppSource / MiniProgramPlatform / ProjectStatus）

## 落点规则
- 公共 schema / types / constants → 这里
- 只被单一域使用的模型 → 放进那个域，不要放这里
