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

describe("generateProject (ai-tool)", () => {
  it("produces a complete buildable uni-app project", async () => {
    const res = await generateProject(prd, "ai-tool");
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
    expect(res.template).toBe("ai-tool");
    expect(res.generated_files_count).toBeGreaterThan(5);
  });

  it("writes manifest/pages under src/", async () => {
    const res = await generateProject(prd, "ai-tool");
    expect(await fs.pathExists(path.join(res.project_path, "src/pages.json"))).toBe(true);
    expect(await fs.pathExists(path.join(res.project_path, "src/manifest.json"))).toBe(true);
    // NOT at project root
    expect(await fs.pathExists(path.join(res.project_path, "pages.json"))).toBe(false);
  });

  it("pages.json contains index + a PRD feature page", async () => {
    const res = await generateProject(prd, "ai-tool");
    const pages = (await fs.readJSON(path.join(res.project_path, "src/pages.json"))).pages;
    const paths = pages.map((p: any) => p.path);
    expect(paths).toContain("pages/index/index");
    // English feature page
    expect(paths).toContain("pages/summary/summary");
  });

  it("Chinese feature names never produce empty paths", async () => {
    const res = await generateProject(prd, "ai-tool");
    const pages = (await fs.readJSON(path.join(res.project_path, "src/pages.json"))).pages;
    for (const pg of pages) {
      expect(pg.path).toMatch(/^pages\/[^/]+\/[^/]+$/);
      expect(pg.path).not.toContain("//");
    }
    // The Chinese feature collapses to a stable fallback name, not empty.
    const paths = pages.map((p: any) => p.path);
    expect(paths.some((x: string) => x.startsWith("pages/feature-"))).toBe(true);
  });

  it("falls back to ai-tool for an unknown template", async () => {
    const res = await generateProject(prd, "nonsense");
    expect(res.template).toBe("ai-tool");
    expect(res.fallback_used).toBe(true);
  });
});
