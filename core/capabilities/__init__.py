"""能力层（Capability Factory）：全项目唯一的能力抽象层。

6 类能力：text / image / vision / speech / video / utility。
统一抽象：base.BaseAdapter + schemas.CapabilityResult/CapabilitySpec + status.CapabilityStatus。
单一事实源：app_types（App 类型）+ registry（能力注册表）。
"""

from capabilities.status import CapabilityStatus, RunnableLevel
from capabilities.schemas import CapabilityResult, CapabilitySpec
from capabilities.base import BaseAdapter, BaseProvider

__all__ = [
    "CapabilityStatus", "RunnableLevel",
    "CapabilityResult", "CapabilitySpec",
    "BaseAdapter", "BaseProvider",
]
