你现在接手 repo-review，继续在已有重构成果上工作，不要重新猜方向。

项目路径：
C:\Users\Administrator\Documents\小程序上架工厂\repo-review

当前分支：
refactor/core-capability-domains

你必须先做：
1. 进入项目目录
2. git status --short
3. git log --oneline -4
4. 确认工作树是否 clean
5. 读取关键文件，不要凭记忆：
   - core/pipeline/runner.py
   - core/generator/codegen.py
   - core/opportunity/viral_score.py
   - core/opportunity/scoring.py
   - core/opportunity/classifier.py
   - core/growth/planner.py
   - core/growth/share_strategy.py
   - core/qa/engineering_qa.py
   - core/qa/growth_qa.py
   - core/qa/compliance_qa.py
   - apps/api/main.py
   - apps/web/src/components/DecisionOverview.vue
   - apps/web/src/components/FactoryConsole.vue
   - apps/web/src/components/DeliverablesPanel.vue

架构约束：
- 最终架构是 capability-domain，不是 agents
- apps/ 放应用，core/ 按能力域拆分
- core/pipeline/runner.py 只做编排，不放业务正文
- core/generator/codegen.py 是唯一生产 codegen 执行真源
- 运行时协议只使用 step/capability，不输出 agent 字段
- 正式真实输入路径是 data/inputs/real/apps.json
- 不保留 data/real_inputs fallback
- 正式部署不依赖 generator service
- docker-compose 不恢复 generator service
- 不恢复旧 agents 架构
- 不恢复旧总线式 runner
- 不把 D:\daily work\miniapp-factory 当主线
- 不凭历史记忆描述目录

当前已完成：
- capability-domain 架构已收口
- 旧 agents/generator/dashboard/scripts 已退出主线
- 5 套传播型模板已真实构建通过：
  - avatar-viral
  - sticker-viral
  - pet-talk-viral
  - funny-video-viral
  - blessing-video-viral
- Viral Score 已进入候选选择和 opportunity score
- 每次生成强制产出 growth-plan.md / share-strategy.md
- 三层 QA 已落地：EngineeringQA / GrowthQA / ComplianceQA
- 前端已展示机会、传播、模板、增长和 QA 摘要
- 已有 4 个本地 commit：
  - arch: collapse to capability-domain runtime
  - generator: add viral template factory and canonical codegen
  - growth-qa: add viral decision, growth docs, three-layer QA
  - web-docs: expose artifacts and align documentation

真实边界：
- 当前是规则版 v1
- 当前小程序模板是可构建骨架，不是真实 AI 后端
- 当前上架是提交准备包，不是一键审核通过
- 不能把这些边界包装成已经完成商业闭环

执行规则：
- 不要大范围重构已经收口的架构
- 不要引入新服务，除非明确必要
- 不要引入真实密钥
- 不要提交 data/outputs、node_modules、dist、.npm-cache、platform-auth 私密配置
- 每轮改完必须给出测试命令和结果
- 如果需要 commit，先列出 git status 和将提交文件分类，等我确认