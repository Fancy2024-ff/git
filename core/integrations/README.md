# core/integrations — 外部服务接入

## 职责
- 所有外部服务的统一接入点：LLM、图像/视频服务、第三方 API、SDK、外部数据源
- 业务层不直接 new SDK 客户端，一律从这里出，换 provider 不改业务层

## 模块
- `llm.py` — `get_llm()` 返回配置好的 LLM 客户端

## 落点规则
- 图像/视频/LLM 接口 → 这里
- 第三方 API / SDK 封装 → 这里
- 注意：榜单抓取（appstore/googleplay）作为"机会发现"的数据采集，归在
  core/opportunity/scrapers；纯外部服务封装才放这里。
