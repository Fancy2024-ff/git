/**
 * Page builder - generates uni-app pages from PRD features
 */

import path from "path";
import fs from "fs-extra";

interface PRDFeature {
  name: string;
  description: string;
  type: "input" | "display" | "interaction" | "navigation";
  api_endpoint?: string;
}

interface PRD {
  app_name: string;
  summary: string;
  core_features: PRDFeature[];
  target_platforms: string[];
  monetization?: string;
}

interface GenerateResult {
  project_path: string;
  pages_generated: number;
  platforms: string[];
}

const PROJECTS_DIR = path.resolve(__dirname, "../../data/projects");
const TEMPLATES_DIR = path.resolve(__dirname, "../src/templates");

export async function generateProject(
  prd: PRD,
  template: string = "ai-tool"
): Promise<GenerateResult> {
  const projectName = prd.app_name
    .toLowerCase()
    .replace(/[^a-z0-9一-龥]/g, "-")
    .replace(/-+/g, "-");

  const projectPath = path.join(PROJECTS_DIR, projectName);

  // Copy base template
  const templatePath = path.join(TEMPLATES_DIR, template);
  if (await fs.pathExists(templatePath)) {
    await fs.copy(templatePath, projectPath, { overwrite: true });
  } else {
    // Use base template as fallback
    const basePath = path.join(TEMPLATES_DIR, "base");
    if (await fs.pathExists(basePath)) {
      await fs.copy(basePath, projectPath, { overwrite: true });
    } else {
      await fs.ensureDir(projectPath);
    }
  }

  // Generate pages directory
  const pagesDir = path.join(projectPath, "src", "pages");
  await fs.ensureDir(pagesDir);

  // Generate pages from PRD features
  let pagesGenerated = 0;
  for (const feature of prd.core_features) {
    const pageName = feature.name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "-")
      .replace(/-+/g, "-");

    const pageDir = path.join(pagesDir, pageName);
    await fs.ensureDir(pageDir);

    // Generate .vue page file
    const vueContent = generateVuePage(feature, prd.app_name);
    await fs.writeFile(path.join(pageDir, `${pageName}.vue`), vueContent, "utf-8");

    pagesGenerated++;
  }

  // Generate manifest.json for uni-app
  const manifest = generateManifest(prd);
  await fs.writeFile(
    path.join(projectPath, "manifest.json"),
    JSON.stringify(manifest, null, 2),
    "utf-8"
  );

  // === MERGE pages.json (template + PRD) ===
  const pagesJsonPath = path.join(projectPath, "pages.json");

  // Read template's pages.json if it exists (from the fs.copy step above)
  let templatePages: any[] = [];
  let templateGlobalStyle: any = {};
  let templateTabBar: any = {};
  if (await fs.pathExists(pagesJsonPath)) {
    const existing = await fs.readJSON(pagesJsonPath);
    templatePages = existing.pages || [];
    templateGlobalStyle = existing.globalStyle || {};
    templateTabBar = existing.tabBar || {};
  }

  // Generate PRD feature pages
  const prdPages = prd.core_features.map((f) => {
    const pageName = f.name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-");
    return {
      path: `pages/${pageName}/${pageName}`,
      style: { navigationBarTitleText: f.name },
    };
  });

  // Merge: template pages first, then PRD pages (skip duplicates)
  const existingPaths = new Set(templatePages.map((p: any) => p.path));
  const mergedPages = [
    ...templatePages,
    ...prdPages.filter(p => !existingPaths.has(p.path)),
  ];

  // Ensure index page exists
  if (!mergedPages.some(p => p.path.includes("index"))) {
    mergedPages.unshift({ path: "pages/index/index", style: { navigationBarTitleText: "首页" } });
  }

  const pagesConfig = {
    pages: mergedPages,
    globalStyle: templateGlobalStyle.navigationBarTextStyle
      ? templateGlobalStyle
      : { navigationBarTextStyle: "black", navigationBarBackgroundColor: "#ffffff", backgroundColor: "#f5f5f5" },
    tabBar: templateTabBar.list?.length ? templateTabBar : undefined,
  };

  await fs.writeFile(pagesJsonPath, JSON.stringify(pagesConfig, null, 2), "utf-8");

  return {
    project_path: projectPath,
    pages_generated: pagesGenerated,
    platforms: prd.target_platforms,
  };
}

function generateVuePage(feature: PRDFeature, appName: string): string {
  return `<template>
  <view class="container">
    <view class="header">
      <text class="title">${feature.name}</text>
      <text class="desc">${feature.description}</text>
    </view>

    <view class="content">
      <!-- ${feature.type} type component -->
      ${getComponentByType(feature)}
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const loading = ref(false)
const result = ref('')

async function handleAction() {
  loading.value = true
  try {
    // TODO: Call AI API endpoint
    const response = await uni.request({
      url: '${feature.api_endpoint || "/api/" + feature.name.toLowerCase()}',
      method: 'POST',
      data: {}
    })
    result.value = response.data as string
  } catch (error) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container {
  padding: 32rpx;
  min-height: 100vh;
  background: #f5f5f5;
}
.header {
  margin-bottom: 40rpx;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}
.desc {
  font-size: 28rpx;
  color: #666;
  margin-top: 12rpx;
}
.content {
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
}
</style>
`;
}

function getComponentByType(feature: PRDFeature): string {
  switch (feature.type) {
    case "input":
      return `<textarea class="input-area" placeholder="请输入内容..." />
      <button class="action-btn" @click="handleAction" :loading="loading">开始处理</button>
      <view v-if="result" class="result-area">{{ result }}</view>`;
    case "display":
      return `<view class="display-area">
        <image v-if="result" :src="result" mode="widthFix" />
      </view>`;
    case "interaction":
      return `<scroll-view class="chat-area" scroll-y>
        <!-- Chat messages here -->
      </scroll-view>
      <view class="input-bar">
        <input placeholder="输入消息..." />
        <button size="mini" @click="handleAction">发送</button>
      </view>`;
    default:
      return `<view class="default-content">
        <text>{{ result || '暂无内容' }}</text>
      </view>`;
  }
}

function generateManifest(prd: PRD): object {
  return {
    name: prd.app_name,
    appid: "",
    description: prd.summary,
    versionName: "1.0.0",
    versionCode: "100",
    "mp-weixin": {
      appid: "",
      setting: { urlCheck: false },
      usingComponents: true,
    },
    "mp-alipay": {
      appid: "",
    },
    "mp-toutiao": {
      appid: "",
    },
  };
}

function generatePagesConfig(features: PRDFeature[]): object {
  const pages = features.map((f) => {
    const pageName = f.name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "-")
      .replace(/-+/g, "-");
    return {
      path: `pages/${pageName}/${pageName}`,
      style: { navigationBarTitleText: f.name },
    };
  });

  return {
    pages: [{ path: "pages/index/index", style: { navigationBarTitleText: "首页" } }, ...pages],
    globalStyle: {
      navigationBarTextStyle: "black",
      navigationBarTitleText: "",
      navigationBarBackgroundColor: "#ffffff",
      backgroundColor: "#f5f5f5",
    },
    tabBar: {
      color: "#999",
      selectedColor: "#333",
      list: [
        { pagePath: "pages/index/index", text: "首页", iconPath: "", selectedIconPath: "" },
      ],
    },
  };
}
