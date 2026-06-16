# text_ai 模板
文本类小程序（写作/翻译/摘要/问答）。
页面：index 首页 → form 文本输入 → result 文本结果 → profile。
能力：text.generate（真实，走中转站）。
5 态：空/输入/处理中/成功/失败。
页面内容由 core/pipeline/runner.py:_pages_text_ai 生成（保证 build 稳定）。
