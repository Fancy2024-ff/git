"""text 能力的输入/输出 schema（轻量约定，便于 provider 对齐）。"""

# operation 入参约定
GENERATE_INPUT = {"prompt": "str", "max_tokens": "int?"}
CHAT_INPUT = {"messages": "list[{role,content}] | prompt:str", "max_tokens": "int?"}

# 统一输出 data 形状
OUTPUT = {"text": "str"}
