import { describe, it, expect, beforeAll } from "vitest";
import os from "os";
import path from "path";
import fs from "fs-extra";

const OUT = path.join(os.tmpdir(), "gen-test-" + process.pid);

let generateProject: (prd: any, template?: string) => Promise<any>;

beforeAll(async () => {
  process.env.GENERATOR_OUTPUT_DIR = OUT;
  await fs.emptyDir(OUT);
  ({ generateProject } = await import("../codegen/page-builder"));
});

const prd = {
  app_name: "Test App",
  summary: "a test app",
  target_platforms: ["wechat"],
  core_features: [
    { name: "翻译", type: "input" },        // Chinese-only -> must not yield empty path
    { name: "Summary", type: "display" },
  ],
};

describe("generateProject (text_ai)", () => {
  it("produces a complete buildable uni-app project", async () => {
    const res = await generateProject(prd, "text_ai");
    const p = res.project_path;
    const required = [
      "package.json",
      "vite.config.ts",
      "tsconfig.json",
      "index.html",
      "src/main.ts",
      "src/App.vue",
      "src/manifest.json",
      "src/pages.json",
      "src/pages/index/index.vue",
    ];
    for (const f of required) {
      expect(await fs.pathExists(path.join(p, f)), `missing ${f}`).toBe(true);
    }
    expect(res.template).toBe("text_ai");
    expect(res.generated_files_count).toBeGreaterThan(5);
  });

  it("writes manifest/pages under src/", async () => {
    const res = await generateProject(prd, "text_ai");
    expect(await fs.pathExists(path.join(res.project_path, "src/pages.json"))).toBe(true);
    expect(await fs.pathExists(path.join(res.project_path, "src/manifest.json"))).toBe(true);
    expect(await fs.pathExists(path.join(res.project_path, "pages.json"))).toBe(false);
  });

  it("pages.json contains index + a PRD feature page", async () => {
    const res = await generateProject(prd, "text_ai");
    const pages = (await fs.readJSON(path.join(res.project_path, "src/pages.json"))).pages;
    const paths = pages.map((p: any) => p.path);
    expect(paths).toContain("pages/index/index");
    expect(paths).toContain("pages/summary/summary");
  });

  it("Chinese feature names never produce empty paths", async () => {
    const res = await generateProject(prd, "text_ai");
    const pages = (await fs.readJSON(path.join(res.project_path, "src/pages.json"))).pages;
    for (const pg of pages) {
      expect(pg.path).toMatch(/^pages\/[^/]+\/[^/]+$/);
      expect(pg.path).not.toContain("//");
    }
    const paths = pages.map((p: any) => p.path);
    expect(paths.some((x: string) => x.startsWith("pages/feature-"))).toBe(true);
  });
});

describe("generateProject 模板归一化（6 类正式 + deprecated alias）", () => {
  it("六类正式模板都返回正式名", async () => {
    for (const t of ["text_ai", "image_ai", "ocr_scan", "speech_ai", "video_light", "utility_tool"]) {
      const res = await generateProject(prd, t);
      expect(res.template).toBe(t);
    }
  });

  it("deprecated alias 自动归一化：ai-tool/ai-chat → text_ai, ai-image → image_ai", async () => {
    expect((await generateProject(prd, "ai-tool")).template).toBe("text_ai");
    expect((await generateProject(prd, "ai-chat")).template).toBe("text_ai");
    expect((await generateProject(prd, "ai-image")).template).toBe("image_ai");
  });

  it("未知模板 fallback 到 text_ai（不再 ai-tool）", async () => {
    const res = await generateProject(prd, "nonsense");
    expect(res.template).toBe("text_ai");
    expect(res.fallback_used).toBe(true);
  });

  it("alias 不算 fallback（是已知输入）", async () => {
    const res = await generateProject(prd, "ai-tool");
    expect(res.fallback_used).toBe(false);
  });

  it("默认模板（不传）为 text_ai", async () => {
    const res = await generateProject(prd);
    expect(res.template).toBe("text_ai");
  });
});
