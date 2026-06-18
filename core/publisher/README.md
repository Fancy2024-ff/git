# core/publisher — 上架与交付

## 职责
- 上架材料生成（listing materials、publish package）
- 上传流程、提交状态
- 平台部署（Telegram WebApp 自动部署等）

## 模块
- `telegram_deploy.py` — Telegram WebApp 构建 + Cloudflare Pages 部署 + Bot 配置
- `templates/telegram-webapp/` — Telegram WebApp 模板

## 落点规则
- 上架 listing / publish package / 上传 / 提交状态 → 这里
- 平台差异规则 → core/platforms（这里只做交付动作）
- 外部部署服务（Cloudflare/Bot API）→ 经 core/integrations 收口（后续）
