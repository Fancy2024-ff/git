"""Global configuration for miniapp-factory agents."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
APPS_DIR = DATA_DIR / "apps"
PRDS_DIR = DATA_DIR / "prds"
PROJECTS_DIR = DATA_DIR / "projects"
REPORTS_DIR = DATA_DIR / "reports"

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# Data sources
QIMAI_API_KEY = os.getenv("QIMAI_API_KEY", "")  # 七麦 API
SENSORTOWER_API_KEY = os.getenv("SENSORTOWER_API_KEY", "")

# Generator service
GENERATOR_URL = os.getenv("GENERATOR_URL", "http://localhost:3100")

# Mini-program platforms
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")
ALIPAY_APPID = os.getenv("ALIPAY_APPID", "")
DOUYIN_APPID = os.getenv("DOUYIN_APPID", "")
