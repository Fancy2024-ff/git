/**
 * Mini-program code generator service
 * Receives PRD from the coding agent and generates uni-app projects
 */

import express from "express";
import { generateProject } from "./codegen/page-builder";

const app = express();
app.use(express.json({ limit: "10mb" }));

const PORT = process.env.PORT || 3100;

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "miniapp-generator" });
});

// Generate a new mini-program project from PRD
app.post("/generate", async (req, res) => {
  try {
    const { prd, template = "ai-tool" } = req.body;

    if (!prd) {
      res.status(400).json({ error: "PRD document is required" });
      return;
    }

    const result = await generateProject(prd, template);
    res.json({ success: true, ...result });
  } catch (error: any) {
    console.error("Generation failed:", error);
    res.status(500).json({ error: error.message });
  }
});

// List available templates
app.get("/templates", (_req, res) => {
  res.json({
    templates: [
      { name: "base", description: "空白基础模板" },
      { name: "ai-tool", description: "AI 工具类 (文字/翻译/摘要)" },
      { name: "ai-chat", description: "AI 对话类 (聊天助手)" },
      { name: "ai-image", description: "AI 图片类 (生成/编辑/风格)" },
    ],
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Generator service running on http://localhost:${PORT}`);
});
