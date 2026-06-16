"""Global configuration for miniapp-factory agents."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
# This file lives at core/agents/config/settings.py.
# Repo root = settings.py / config / agents / core → 4 levels up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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
# 是否启用 LLM 增强（目前仅作用于第 2 步需求分析）。默认 false：保证 demo 离线稳定。
# true 时第 2 步会调用 LLM 生成 ai-demand-analysis.json；失败自动 fallback 到规则分析。
USE_LLM = os.getenv("USE_LLM", "false").strip().lower() in ("1", "true", "yes", "on")

# Data sources
QIMAI_API_KEY = os.getenv("QIMAI_API_KEY", "")  # 七麦 API
SENSORTOWER_API_KEY = os.getenv("SENSORTOWER_API_KEY", "")

# Generator service
GENERATOR_URL = os.getenv("GENERATOR_URL", "http://localhost:3100")

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
