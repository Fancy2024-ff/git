/**
 * Mini-program code generator — Node parity/compat tool (NOT a production service).
 *
 * The single source of truth for code generation is the Python core/generator/codegen.py,
 * which the pipeline calls directly. This Express wrapper exists only so the TypeScript
 * page-builder can be exercised by vitest and kept in parity with the Python generator.
 * It is intentionally excluded from the production deployment (docker-compose api + web only).
 */

import crypto from "crypto";
import express from "express";
import { generateProject } from "./codegen/page-builder";

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
    const template = body.template ?? "ai-tool";

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
  if (GENERATOR_API_KEY) {
    console.log(`🔒 Auth enabled (GENERATOR_API_KEY set)`);
  } else {
    console.log(`⚠️  Auth disabled (no GENERATOR_API_KEY)`);
  }
});
