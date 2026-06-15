"""DEPRECATED: API server moved to apps/api/main.py

This shim keeps `python agents/server.py` and `uvicorn server:app` working
during the migration. Update your scripts to use apps/api/main.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

# Re-export the FastAPI app from the new location
from main import app  # noqa: E402,F401

if __name__ == "__main__":
    print("[DEPRECATED] agents/server.py moved to apps/api/main.py")
    print("Run instead:  cd apps/api && python main.py")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
