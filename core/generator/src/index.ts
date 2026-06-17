/**
 * Mini-program code generator service
 * Receives PRD from the coding agent and generates uni-app projects
 */

import crypto from "crypto";
import express from "express";
import { generateProject } from "./codegen/page-builder";
import {
  listOfficialTemplates,
  listDeprecatedAliases,
  getDefaultTemplate,
} from "./codegen/template-registry";

const app = express();
app.use(express.json({ limit: "10mb" }));

const PORT = process.env.PORT || 3100;
const GENERATOR_API_KEY = process.env.GENERATOR_API_KEY || "";
const NODE_ENV = process.env.NODE_ENV || "development";

// In production, refuse to start without an API key
if (NODE_ENV === "production" && !GENERATOR_API_KEY) {
  console.error(
    "❌ FATAL: NODE_ENV=production requires GENERATOR_API_KEY to be set. Refusing to start.",
  );
  process.exit(1);
}

/**
 * Constant-time string comparison to prevent timing attacks.
 * Uses HMAC-SHA256 so length differences don't leak information.
 */
function safeEqual(a: string, b: string): boolean {
  const hashA = crypto.createHmac("sha256", "key").update(a).digest();
  const hashB = crypto.createHmac("sha256", "key").update(b).digest();
  return crypto.timingSafeEqual(hashA, hashB);
}

// Auth middleware: Bearer token validation (skips /health)
function authMiddleware(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction,
): void {
  if (!GENERATOR_API_KEY) {
    // No key configured = auth disabled (dev mode)
    next();
    return;
  }
  const authHeader = req.headers.authorization || "";
  const token = authHeader.startsWith("Bearer ")
    ? authHeader.slice(7)
    : "";
  if (!safeEqual(token, GENERATOR_API_KEY)) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  next();
}

// Health check (no auth required)
app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "miniapp-generator" });
});

// Apply auth to all routes below
app.use(authMiddleware);

// Generate a new mini-program project from PRD.
// Accepts either { prd: {...}, template } or a bare PRD object as the body.
app.post("/generate", async (req, res) => {
  try {
    const body = req.body || {};
    const prd = body.prd ?? body;
    const template = body.template ?? getDefaultTemplate();

    if (!prd || !prd.app_name || !Array.isArray(prd.core_features)) {
      res.status(400).json({
        error: "PRD with app_name and core_features[] is required",
      });
      return;
    }

    const result = await generateProject(prd, template);
    res.json({ success: true, ...result });
  } catch (error: any) {
    console.error("Generation failed:", error);
    res.status(500).json({ error: error.message });
  }
});

// List available templates（正式 6 类 + base 底座；旧三类仅作 deprecated alias）
app.get("/templates", (_req, res) => {
  const descriptions: Record<string, string> = {
    text_ai: "文本 AI（写作/翻译/摘要/对话）",
    image_ai: "图像 AI（抠图/证件照/头像/增强）",
    ocr_scan: "OCR 扫描识别（文档/票据/表格）",
    speech_ai: "语音 AI（配音/TTS/语音转写）",
    video_light: "轻视频（摘要/封面/脚本）",
    utility_tool: "实用工具（计算/转换/查询）",
  };
  res.json({
    templates: [
      { name: "base", description: "公共底座（始终先复制，保证可构建）" },
      ...listOfficialTemplates().map((name) => ({ name, description: descriptions[name] || name })),
    ],
    deprecated_aliases: listDeprecatedAliases(),
    default_template: getDefaultTemplate(),
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Generator service running on http://localhost:${PORT}`);
  if (GENERATOR_API_KEY) {
    console.log(`🔒 Auth enabled (GENERATOR_API_KEY set)`);
  } else {
    console.log(`⚠️  Auth disabled (no GENERATOR_API_KEY)`);
  }
});
