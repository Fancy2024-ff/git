# core/platforms — 平台规则与差异

## 职责
- 承载微信 / 支付宝 / 抖音 / Telegram 等平台的规则与差异
- 平台特定的合规细则、上架要求、能力差异

## 现状
- 平台注册表数据在 `data/platforms/platform-registry.json`
- Telegram 部署逻辑在 `core/publisher/telegram_deploy.py`（上架交付侧）
- 本目录为平台差异规则的归位点；随平台规则细化逐步填充

## 落点规则
- 平台差异规则 → 这里
- 合规检查的平台特定部分 → 这里（通用合规闸在 core/qa/compliance_qa）
