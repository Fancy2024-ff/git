"""core.runtime.config — 全局配置（单一事实源）。

所有路径、密钥、外部服务地址从这里读，不允许各模块各自 os.getenv 散落。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths — PROJECT_ROOT = repo 根（core/runtime/config.py -> parents[2]）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
APPS_DIR = DATA_DIR / "apps"
PRDS_DIR = DATA_DIR / "prds"
PROJECTS_DIR = DATA_DIR / "projects"
REPORTS_DIR = DATA_DIR / "reports"

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Data sources
QIMAI_API_KEY = os.getenv("QIMAI_API_KEY", "")  # 七麦 API
SENSORTOWER_API_KEY = os.getenv("SENSORTOWER_API_KEY", "")

# NOTE: 不再有 GENERATOR_URL / GENERATOR_API_KEY。
# miniapp 生成的唯一执行真源是 Python core/generator/codegen.py，主链路不调用
# Node generator HTTP 服务（该服务已从正式部署移除，仅作 vitest/Node 兼容工具）。

# Telegram auto-deploy
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_PROJECT_NAME = os.getenv("CLOUDFLARE_PROJECT_NAME", "miniforge-app")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

# WebApp frontend LLM (used by deployed mini-app)
WEBAPP_LLM_BASE_URL = os.getenv("WEBAPP_LLM_BASE_URL", "https://api.deepseek.com")
WEBAPP_LLM_API_KEY = os.getenv("WEBAPP_LLM_API_KEY", "")
WEBAPP_LLM_MODEL = os.getenv("WEBAPP_LLM_MODEL", "deepseek-chat")

# Mini-program platforms
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")
ALIPAY_APPID = os.getenv("ALIPAY_APPID", "")
DOUYIN_APPID = os.getenv("DOUYIN_APPID", "")
