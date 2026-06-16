"""Runtime 层：capability 的真实执行层。

统一任务模型（create/poll/result/fail/timeout/cleanup）驱动 capabilities adapter。
image 为第一条真实运行链路承载层；OCR/speech/video 复用同一模式。
"""

from runtime.task_model import Task, TaskState, can_transition
from runtime.errors import RuntimeErrorCode

__all__ = ["Task", "TaskState", "can_transition", "RuntimeErrorCode"]
