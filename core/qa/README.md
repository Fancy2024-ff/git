# core/qa — 交付质量验证

## 职责
分三类质量闸：
- **engineering qa**（`engineering_qa.py`）— 工程可构建性：文件结构、编码（三层乱码检测）、JSON 合法性、真跑 npm install + build:mp-weixin、断言真实 dist 产物（app.js/app.json/app.wxss + 页面 js）
- **growth qa**（`growth_qa.py`）— 裂变交付：growth-plan / share-strategy / viral-score 产物齐全且含分享钩子、激励、裂变回环
- **compliance qa**（`compliance_qa.py`）— 合规交付：隐私政策、用户协议、审核备注齐全

## 入口
- `run_engineering_qa(miniapp_dir, output_dir) -> dict`
- `run_growth_qa(output_dir) -> dict`
- `run_compliance_qa(miniapp_dir, output_dir) -> dict`

## 落点规则
- 工程 build 检查 → engineering_qa
- 裂变位检查 / 分享检查 → growth_qa
- 合规检查 → compliance_qa（平台差异细则在 core/platforms）
