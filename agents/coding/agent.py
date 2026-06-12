"""
Coding Agent - Dispatches PRD to the Node.js generator service and enhances output.

Flow:
1. Send PRD to generator service → get basic uni-app project scaffolding
2. Use LLM to enhance pages (better UI logic, error handling, API integration)
3. Generate supporting files (API layer, utils, constants)
4. Return the project path
"""

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from shared.models import PRDDocument
from shared.llm import get_llm
from config.settings import PROJECTS_DIR
from coding.task_dispatcher import dispatch_to_generator, GeneratorResult


def run_coding(prd: PRDDocument) -> str:
    """
    Main coding flow:
    1. Call generator service to scaffold the project
    2. Enhance with LLM-generated logic
    3. Return project path
    """
    # Step 1: Dispatch to Node.js generator
    result = dispatch_to_generator(prd)

    if not result.success:
        # Fallback: generate locally without the service
        print(f"[Coding] Generator service unavailable, using local generation")
        result = _generate_locally(prd)

    # Step 2: Enhance the generated code with LLM
    _enhance_with_llm(prd, result.project_path)

    # Step 3: Generate API layer
    _generate_api_layer(prd, result.project_path)

    print(f"[Coding] Project generated at: {result.project_path}")
    print(f"[Coding] Pages generated: {result.pages_generated}")

    return result.project_path


def _generate_locally(prd: PRDDocument) -> GeneratorResult:
    """Fallback: generate project structure locally without the Node.js service."""
    from pathlib import Path

    project_name = _sanitize_page_name(prd.app_name) or "miniapp-project"
    project_path = PROJECTS_DIR / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create basic uni-app structure
    src_dir = project_path / "src"
    pages_dir = src_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Generate index page
    index_dir = pages_dir / "index"
    index_dir.mkdir(exist_ok=True)
    _write_index_page(index_dir, prd)

    # Generate feature pages
    pages_generated = 1  # index
    for feature in prd.core_features:
        page_name = _sanitize_page_name(feature.get("name", ""))
        if not page_name:
            continue
        page_dir = pages_dir / page_name
        page_dir.mkdir(exist_ok=True)
        _write_feature_page(page_dir, page_name, feature)
        pages_generated += 1

    # manifest.json
    manifest = {
        "name": prd.app_name,
        "appid": "",
        "description": prd.summary,
        "versionName": "1.0.0",
        "versionCode": "100",
        "mp-weixin": {"appid": "", "setting": {"urlCheck": False}},
        "mp-alipay": {"appid": ""},
        "mp-toutiao": {"appid": ""},
    }
    (project_path / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # pages.json
    pages_config = _build_pages_config(prd)
    (project_path / "pages.json").write_text(
        json.dumps(pages_config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return GeneratorResult(
        success=True,
        project_path=str(project_path),
        pages_generated=pages_generated,
        platforms=[p.value for p in prd.target_platforms],
    )

def _enhance_with_llm(prd: PRDDocument, project_path: str) -> None:
    """Use LLM to enhance generated page code with better logic."""
    from pathlib import Path

    llm = get_llm(max_tokens=4096)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a senior uni-app developer. Enhance the given Vue page code for a mini-program.
Improve:
- User interaction logic (loading states, error handling, form validation)
- Proper uni.request API calls with real endpoint patterns
- Responsive layout using rpx units
- Accessibility (aria labels where applicable)

Return ONLY the complete .vue file content, no explanations.""",
        ),
        (
            "human",
            """App: {app_name}
Feature: {feature_name}
Description: {feature_desc}
API endpoint: {api_endpoint}

Current code:
```vue
{current_code}
```

Enhance this page with production-quality logic.""",
        ),
    ])

    chain = prompt | llm | StrOutputParser()
    pages_dir = Path(project_path) / "src" / "pages"

    if not pages_dir.exists():
        return

    for feature in prd.core_features:
        page_name = _sanitize_page_name(feature.get("name", ""))
        if not page_name:
            continue

        page_file = pages_dir / page_name / f"{page_name}.vue"
        if not page_file.exists():
            continue

        current_code = page_file.read_text(encoding="utf-8")

        try:
            enhanced = chain.invoke({
                "app_name": prd.app_name,
                "feature_name": feature.get("name", ""),
                "feature_desc": feature.get("description", ""),
                "api_endpoint": feature.get("api_endpoint", "/api/default"),
                "current_code": current_code,
            })

            # Only write if LLM returned valid Vue content
            if "<template>" in enhanced and "<script" in enhanced:
                page_file.write_text(enhanced, encoding="utf-8")
                print(f"[Coding] Enhanced page: {page_name}")
        except Exception as e:
            print(f"[Coding] Enhancement failed for {page_name}: {e}")


def _generate_api_layer(prd: PRDDocument, project_path: str) -> None:
    """Generate a unified API layer for the mini-program."""
    from pathlib import Path

    api_dir = Path(project_path) / "src" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    # Generate API index
    endpoints = []
    for feature in prd.core_features:
        endpoint = feature.get("api_endpoint", "")
        name = feature.get("name", "unknown").lower().replace(" ", "_")
        if endpoint:
            endpoints.append({"name": name, "path": endpoint})

    api_content = _build_api_file(endpoints)
    (api_dir / "index.ts").write_text(api_content, encoding="utf-8")

    # Generate request util
    request_content = _build_request_util()
    utils_dir = Path(project_path) / "src" / "utils"
    utils_dir.mkdir(parents=True, exist_ok=True)
    (utils_dir / "request.ts").write_text(request_content, encoding="utf-8")


def _build_api_file(endpoints: list[dict]) -> str:
    """Build the API definition file."""
    lines = [
        '/**',
        ' * Auto-generated API layer',
        ' */',
        "import { request } from '@/utils/request'",
        '',
    ]

    for ep in endpoints:
        fn_name = ep["name"].replace("-", "_")
        lines.append(f"export function {fn_name}(data: any) {{")
        lines.append(f"  return request('{ep['path']}', 'POST', data)")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def _build_request_util() -> str:
    """Build the request utility file."""
    return '''/**
 * Unified request utility for mini-program
 */

const BASE_URL = '' // Set via env or config

export interface RequestOptions {
  showLoading?: boolean
  showError?: boolean
}

export function request<T = any>(
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: any,
  options: RequestOptions = {}
): Promise<T> {
  const { showLoading = true, showError = true } = options

  if (showLoading) {
    uni.showLoading({ title: '加载中...' })
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else {
          if (showError) {
            uni.showToast({ title: '请求失败', icon: 'none' })
          }
          reject(new Error(`Request failed: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        if (showError) {
          uni.showToast({ title: '网络错误', icon: 'none' })
        }
        reject(err)
      },
      complete: () => {
        if (showLoading) {
          uni.hideLoading()
        }
      },
    })
  })
}
'''


def _write_index_page(index_dir, prd: PRDDocument) -> None:
    """Write the index/home page."""
    features_list = "\n".join([
        f'        <view class="feature-card" @click="navigateTo(\'/pages/{_sanitize_page_name(f.get("name", ""))}/{_sanitize_page_name(f.get("name", ""))}\')">'
        f'\n          <text class="feature-name">{f.get("name", "")}</text>'
        f'\n          <text class="feature-desc">{f.get("description", "")[:30]}</text>'
        f'\n        </view>'
        for f in prd.core_features
    ])

    content = f'''<template>
  <view class="container">
    <view class="hero">
      <text class="app-title">{prd.app_name}</text>
      <text class="app-desc">{prd.summary[:50]}</text>
    </view>

    <view class="features">
{features_list}
    </view>
  </view>
</template>

<script setup lang="ts">
function navigateTo(url: string) {{
  uni.navigateTo({{ url }})
}}
</script>

<style scoped>
.container {{
  padding: 32rpx;
  min-height: 100vh;
  background: #f5f5f5;
}}
.hero {{
  text-align: center;
  padding: 60rpx 0;
}}
.app-title {{
  font-size: 44rpx;
  font-weight: bold;
  color: #333;
}}
.app-desc {{
  font-size: 28rpx;
  color: #666;
  margin-top: 16rpx;
}}
.features {{
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}}
.feature-card {{
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.05);
}}
.feature-name {{
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}}
.feature-desc {{
  font-size: 26rpx;
  color: #999;
  margin-top: 8rpx;
}}
</style>
'''
    (index_dir / "index.vue").write_text(content, encoding="utf-8")


def _write_feature_page(page_dir, page_name: str, feature: dict) -> None:
    """Write a feature page."""
    feat_type = feature.get("type", "input")
    component = {
        "input": '<textarea class="input-area" v-model="inputText" placeholder="请输入内容..." />\n      <button class="action-btn" @click="handleAction" :loading="loading">开始处理</button>\n      <view v-if="result" class="result-area">{{ result }}</view>',
        "display": '<view class="display-area">\n        <image v-if="result" :src="result" mode="widthFix" />\n      </view>',
        "interaction": '<scroll-view class="chat-area" scroll-y>\n      </scroll-view>\n      <view class="input-bar">\n        <input v-model="inputText" placeholder="输入消息..." />\n        <button size="mini" @click="handleAction">发送</button>\n      </view>',
    }.get(feat_type, '<view class="default-content"><text>{{ result || "暂无内容" }}</text></view>')

    content = f'''<template>
  <view class="container">
    <view class="header">
      <text class="title">{feature.get("name", page_name)}</text>
      <text class="desc">{feature.get("description", "")}</text>
    </view>
    <view class="content">
      {component}
    </view>
  </view>
</template>

<script setup lang="ts">
import {{ ref }} from 'vue'

const loading = ref(false)
const inputText = ref('')
const result = ref('')

async function handleAction() {{
  if (!inputText.value.trim()) {{
    uni.showToast({{ title: '请输入内容', icon: 'none' }})
    return
  }}
  loading.value = true
  try {{
    const [err, res] = await uni.request({{
      url: '{feature.get("api_endpoint", "/api/" + page_name)}',
      method: 'POST',
      data: {{ input: inputText.value }}
    }})
    if (res && res.statusCode === 200) {{
      result.value = (res.data as any).result || ''
    }}
  }} catch (error) {{
    uni.showToast({{ title: '操作失败', icon: 'none' }})
  }} finally {{
    loading.value = false
  }}
}}
</script>

<style scoped>
.container {{ padding: 32rpx; min-height: 100vh; background: #f5f5f5; }}
.header {{ margin-bottom: 40rpx; }}
.title {{ font-size: 36rpx; font-weight: bold; color: #333; }}
.desc {{ font-size: 28rpx; color: #666; margin-top: 12rpx; display: block; }}
.content {{ background: #fff; border-radius: 16rpx; padding: 32rpx; }}
.input-area {{ width: 100%; min-height: 200rpx; padding: 16rpx; border: 1rpx solid #eee; border-radius: 8rpx; }}
.action-btn {{ margin-top: 24rpx; background: #4f46e5; color: #fff; }}
.result-area {{ margin-top: 24rpx; padding: 24rpx; background: #f9fafb; border-radius: 8rpx; white-space: pre-wrap; }}
</style>
'''
    (page_dir / f"{page_name}.vue").write_text(content, encoding="utf-8")


def _sanitize_page_name(name: str) -> str:
    """Sanitize a feature name into a valid directory/file name."""
    import re as _re
    # Remove anything that's not alphanumeric, Chinese, space, or dash
    name = name.lower().strip()
    # Replace spaces and special chars with dash
    name = _re.sub(r'[^a-z0-9一-鿿]', '-', name)
    # Collapse multiple dashes
    name = _re.sub(r'-+', '-', name)
    # Strip leading/trailing dashes
    name = name.strip('-')
    # Limit length
    return name[:40] if name else ""


def _build_pages_config(prd: PRDDocument) -> dict:
    """Build pages.json config."""
    pages = [{"path": "pages/index/index", "style": {"navigationBarTitleText": "首页"}}]

    for feature in prd.core_features:
        name = _sanitize_page_name(feature.get("name", ""))
        if name:
            pages.append({
                "path": f"pages/{name}/{name}",
                "style": {"navigationBarTitleText": feature.get("name", "")},
            })

    return {
        "pages": pages,
        "globalStyle": {
            "navigationBarTextStyle": "black",
            "navigationBarBackgroundColor": "#ffffff",
            "backgroundColor": "#f5f5f5",
        },
    }
