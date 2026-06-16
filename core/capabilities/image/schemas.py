"""image 能力的输入/输出 schema + 异步任务状态约定。"""

# operation 入参：image_ref 为图片引用（临时路径/URL/上传 id）
PROCESS_INPUT = {"image_ref": "str", "operation": "str", "params": "dict?"}

# 异步任务状态（create_task → poll_task）
TASK_PENDING = "pending"
TASK_PROCESSING = "processing"
TASK_SUCCEEDED = "succeeded"
TASK_FAILED = "failed"

# poll_task 成功输出
TASK_RESULT = {"task_id": "str", "status": "str", "result_url": "str"}
