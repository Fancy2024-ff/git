"""core.runtime.context — Job 运行上下文。

职责：承载一次 pipeline run 的 job_id / 输出目录 / 模式 / 计时等运行时状态，
供各 step 传递。轻量数据类，不含业务规则。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


@dataclass
class JobContext:
    """一次流水线运行的上下文。"""

    job_id: str
    output_dir: Path
    mode: str = "demo"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    meta: dict = field(default_factory=dict)

    @property
    def generated_dir(self) -> Path:
        return self.output_dir / "generated"

    @property
    def miniapp_dir(self) -> Path:
        return self.output_dir / "generated" / "miniapp"

    def artifact_path(self, name: str) -> Path:
        return self.output_dir / name
