"""core.generator.blueprint_builder — 页面蓝图构建（占位 / TODO）。

定位（最终架构）：
  介于 PRD（prd_builder）与代码生成（codegen）之间的一层"页面蓝图"。
  PRD 描述"做什么产品/有哪些功能"，blueprint 描述"具体生成哪些页面、每页用
  哪个组件块、路由如何编排"——把 PRD 的功能列表翻译成 codegen 可直接消费的
  结构化页面计划，让 codegen 退化为纯模板填充。

现状：
  当前 codegen.py 直接基于「base 模板 + 题材 overlay + token 注入」生成，页面
  结构由模板事实源（core/generator/src/templates）承载，蓝图层尚未独立。
  本模块先建空壳，明确职责归属，待页面动态化需求出现时再实现。

约束：
  - 唯一执行真源仍是 core/generator/codegen.py，blueprint 实现后由 codegen 调用。
  - 不得形成第二条生成主链路；Node 侧仅作 parity/兼容工具。
"""

from __future__ import annotations


def build_blueprint(prd_json: dict, template: str) -> dict:
    """TODO: 由 PRD + 选定模板产出结构化页面蓝图。

    预期返回形如：
        {
          "template": "<template>",
          "pages": [{"path": "pages/xxx/xxx", "blocks": [...], "title": "..."}],
          "routes": [...],
        }
    供 codegen 据此填充模板（而非当前的固定 4 页 + overlay）。

    现阶段未实现：codegen 仍走模板事实源 + token 注入。
    """
    raise NotImplementedError(
        "blueprint_builder 尚未实现；当前页面结构由 core/generator/src/templates "
        "模板事实源承载，codegen.py 直接消费。详见本文件 docstring。"
    )
