"""utility.execute adapter —— 本地工具能力（runtime_ready 样板）。"""

from __future__ import annotations

from capabilities.base import BaseAdapter
from capabilities.utility.providers.local import LocalUtilityProvider


class UtilityAdapter(BaseAdapter):
    capability_name = "utility.execute"
    display_name = "实用工具"
    supported_operations = ["calculate", "convert", "query"]
    local_capability = True   # 本地能力，无需外部 provider → 永远 runtime_ready

    def __init__(self, provider=None):
        super().__init__(provider or LocalUtilityProvider())

    def _notes(self) -> str:
        return "本地能力，无需外部 provider，runtime_ready 样板。"
