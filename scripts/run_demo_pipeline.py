"""DEPRECATED: pipeline moved to core/pipeline/runner.py

This shim keeps `python scripts/run_demo_pipeline.py` and the API's
subprocess call working during migration. It forwards all CLI args to
core/pipeline/runner.py unchanged.
"""

import sys
import runpy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "core" / "pipeline" / "runner.py"

# Execute the real runner as __main__, preserving sys.argv (argparse works)
runpy.run_path(str(RUNNER), run_name="__main__")
