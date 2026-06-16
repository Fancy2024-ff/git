# image_ai 模板（复杂能力范式）
图像类小程序（证件照/抠图/头像/增强）。
页面：index → form 选图+选参数+上传+轮询 → result 图片预览+保存到相册 → profile。
能力：image.process（接口+异步任务+stub，provider missing）。
5 态：空(未选图)/选图后/处理中/成功(出图)/失败(未接入提示)。
真实处理走 utils/request.ts → /api/image/process；未配置图像 API 时如实提示，不假成功。
页面内容由 core/pipeline/runner.py:_pages_image_ai 生成。
