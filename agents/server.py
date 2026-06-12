"""
MiniApp Factory – FastAPI backend (production).
Zero duplicate routes. Each path+method defined exactly once.
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from config.settings import DATA_DIR

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
OUTPUTS_DIR = DATA_DIR / "outputs"
PLATFORMS_DIR = DATA_DIR / "platforms"
PLATFORM_AUTH_DIR = DATA_DIR / "platform-auth"
REAL_INPUTS_DIR = DATA_DIR / "real_inputs"

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="MiniApp Factory API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
pipeline_process: Optional[subprocess.Popen] = None
pipeline_job_id: Optional[str] = None
pipeline_logs: list[str] = []
connected_ws_clients: list[WebSocket] = []

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_job_id() -> str:
    """YYYYMMDD-XXXXXX (date + 6 random hex chars)."""
    import secrets
    return datetime.now().strftime("%Y%m%d") + "-" + secrets.token_hex(3)


def _read_json(path: Path):
    """Read JSON with BOM-safe encoding."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


async def _broadcast(msg: dict):
    """Send JSON message to all connected WebSocket clients."""
    text = json.dumps(msg, ensure_ascii=False)
    for ws in connected_ws_clients[:]:
        try:
            await ws.send_text(text)
        except Exception:
            if ws in connected_ws_clients:
                connected_ws_clients.remove(ws)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PipelineStartRequest(BaseModel):
    mode: str = "demo"


# ---------------------------------------------------------------------------
# SECTION: Pipeline
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/start")
async def pipeline_start(req: PipelineStartRequest = PipelineStartRequest()):
    """Start pipeline in background, return immediately."""
    global pipeline_process, pipeline_job_id, pipeline_logs

    if pipeline_process and pipeline_process.poll() is None:
        raise HTTPException(409, "Pipeline already running")

    # Validate real mode has data
    if req.mode == "real":
        apps_file = REAL_INPUTS_DIR / "apps.json"
        if not apps_file.exists():
            raise HTTPException(400, "No real input data: apps.json missing. Import apps first.")
        apps = _read_json(apps_file)
        if not apps:
            raise HTTPException(400, "apps.json is empty. Import at least one app for real mode.")

    # Generate job_id BEFORE starting
    job_id = _generate_job_id()
    pipeline_job_id = job_id
    pipeline_logs = []

    python_exe = sys.executable
    cmd = [
        python_exe, "-X", "utf8",
        str(SCRIPTS_DIR / "run_demo_pipeline.py"),
        "--mode", req.mode,
        "--job-id", job_id,
    ]

    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}

    pipeline_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).parent.parent),
        env=env,
    )

    asyncio.get_event_loop().create_task(_stream_pipeline_output(job_id))

    return {"accepted": True, "job_id": job_id, "mode": req.mode}

async def _stream_pipeline_output(job_id: str):
    """Read pipeline stdout line by line, broadcast via WebSocket."""
    global pipeline_process

    loop = asyncio.get_event_loop()

    while pipeline_process and pipeline_process.poll() is None:
        line = await loop.run_in_executor(None, pipeline_process.stdout.readline)
        if not line:
            break
        line = line.rstrip()
        pipeline_logs.append(line)
        await _broadcast({"type": "log", "data": line, "job_id": job_id})

    # Pipeline finished
    exit_code = pipeline_process.returncode if pipeline_process else -1
    success = exit_code == 0
    await _broadcast({"type": "pipeline_finished", "job_id": job_id, "success": success})
    # Clear process reference
    # Note: keep pipeline_logs and pipeline_job_id for status queries


@app.get("/api/pipeline/status")
def pipeline_status():
    """Current pipeline status."""
    running = pipeline_process is not None and pipeline_process.poll() is None
    return {
        "running": running,
        "job_id": pipeline_job_id,
        "log_lines": len(pipeline_logs),
    }


@app.post("/api/pipeline/stop")
def pipeline_stop():
    """Kill running pipeline."""
    global pipeline_process
    if pipeline_process and pipeline_process.poll() is None:
        pipeline_process.terminate()
        pipeline_process = None
        return {"stopped": True, "job_id": pipeline_job_id}
    raise HTTPException(409, "No pipeline running")


# ---------------------------------------------------------------------------
# SECTION: WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/pipeline")
async def ws_pipeline(ws: WebSocket):
    """Global WebSocket for pipeline log streaming."""
    await ws.accept()
    connected_ws_clients.append(ws)

    # Send buffered logs
    for line in pipeline_logs[-100:]:
        await ws.send_text(json.dumps({"type": "log", "data": line, "job_id": pipeline_job_id}))

    # Send current status
    running = pipeline_process is not None and pipeline_process.poll() is None
    await ws.send_text(json.dumps({"type": "status", "running": running, "job_id": pipeline_job_id}))

    try:
        while True:
            await ws.receive_text()  # keep-alive
    except (WebSocketDisconnect, Exception):
        if ws in connected_ws_clients:
            connected_ws_clients.remove(ws)


# ---------------------------------------------------------------------------
# SECTION: Jobs CRUD (from OUTPUTS_DIR)
# ---------------------------------------------------------------------------

@app.get("/api/jobs")
def list_jobs():
    """List all pipeline jobs, sorted newest first."""
    if not OUTPUTS_DIR.exists():
        return {"jobs": []}
    jobs = []
    dirs = sorted(
        [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for d in dirs:
        job: dict = {"id": d.name, "path": str(d)}
        # QA report
        qa_file = d / "qa-report.json"
        if qa_file.exists():
            qa = _read_json(qa_file)
            job["qa_passed"] = qa.get("passed", False)
            job["build_verified"] = qa.get("checks", {}).get("build_verified", False)
        # Candidate info
        cand_file = d / "candidate.json"
        if cand_file.exists():
            cand = _read_json(cand_file)
            job["app_name"] = cand.get("name_cn", cand.get("name", ""))
            job["app_name_en"] = cand.get("name", "")
        # Artifacts list
        job["artifacts"] = [f.name for f in d.iterdir() if f.is_file()]
        job["has_miniapp"] = (d / "generated" / "miniapp").exists()
        jobs.append(job)
    return {"jobs": jobs}


@app.get("/api/jobs/latest")
def get_latest_job():
    """Most recent job by modification time."""
    if not OUTPUTS_DIR.exists():
        raise HTTPException(404, "No jobs found")
    dirs = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()]
    if not dirs:
        raise HTTPException(404, "No jobs found")
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return get_job_detail(dirs[0].name)


@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: str):
    """Full details for a specific job."""
    job_dir = OUTPUTS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    result: dict = {"id": job_id, "path": str(job_dir), "artifacts": {}}

    for f in job_dir.iterdir():
        if f.is_file():
            if f.suffix == ".json":
                try:
                    result["artifacts"][f.name] = _read_json(f)
                except Exception:
                    result["artifacts"][f.name] = {"error": "parse failed"}
            elif f.suffix == ".md":
                result["artifacts"][f.name] = f.read_text(encoding="utf-8-sig")

    # Miniapp file tree
    miniapp_dir = job_dir / "generated" / "miniapp"
    if miniapp_dir.exists():
        result["miniapp_files"] = [
            str(f.relative_to(miniapp_dir))
            for f in miniapp_dir.rglob("*")
            if f.is_file() and "node_modules" not in str(f)
        ]
        result["miniapp_path"] = str(miniapp_dir)

    return result


@app.get("/api/jobs/{job_id}/artifact")
def get_job_artifact(job_id: str, file: str):
    """Read a specific artifact file from a job."""
    job_dir = OUTPUTS_DIR / job_id
    file_path = job_dir / file

    # Security: path must resolve within job_dir
    try:
        file_path.resolve().relative_to(job_dir.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")

    if not file_path.exists():
        raise HTTPException(404, f"Artifact not found: {file}")

    content = file_path.read_text(encoding="utf-8-sig")
    if file_path.suffix == ".json":
        return json.loads(content)
    return {"content": content}


# ---------------------------------------------------------------------------
# SECTION: Platforms
# ---------------------------------------------------------------------------

@app.get("/api/platforms")
def get_platforms():
    """Read platform registry."""
    reg_file = PLATFORMS_DIR / "platform-registry.json"
    if not reg_file.exists():
        return {"platforms": []}
    platforms = _read_json(reg_file)
    return {"platforms": platforms, "total": len(platforms)}


# ---------------------------------------------------------------------------
# SECTION: Platform Auth
# ---------------------------------------------------------------------------

@app.get("/api/platform-auth/status")
def get_platform_auth_status():
    """Check auth config status for each platform (never exposes secrets)."""
    platform_configs = {
        "wechat": {"name": "微信小程序", "required": ["appid", "private_key_path"]},
        "telegram": {"name": "Telegram Mini Apps", "required": ["bot_token", "webapp_url"]},
        "discord": {"name": "Discord Activities", "required": ["application_id", "activity_url"]},
    }

    platforms_status = []
    for plat_id, meta in platform_configs.items():
        config_file = PLATFORM_AUTH_DIR / f"{plat_id}.json"
        configured = False
        can_upload = False
        can_submit = False
        missing: list[str] = meta["required"][:]

        if config_file.exists():
            try:
                config = _read_json(config_file)
                missing = [f for f in meta["required"] if not config.get(f)]
                configured = len(missing) == 0
                can_upload = configured and config.get("upload_enabled", False)
                can_submit = configured and config.get("submit_review_enabled", False)
            except Exception:
                missing = meta["required"][:]

        platforms_status.append({
            "platform_id": plat_id,
            "platform_name": meta["name"],
            "configured": configured,
            "can_upload": can_upload,
            "can_submit_review": can_submit,
            "missing_config": missing,
        })

    return {"platforms": platforms_status}


@app.post("/api/platforms/wechat/upload")
def wechat_upload():
    """Attempt WeChat upload – fails gracefully if not configured."""
    config_file = PLATFORM_AUTH_DIR / "wechat.json"
    if not config_file.exists():
        return {"upload_passed": False, "reason": "wechat.json not found in platform-auth"}

    try:
        config = _read_json(config_file)
    except Exception as e:
        return {"upload_passed": False, "reason": f"config parse error: {e}"}

    if not config.get("appid") or not config.get("private_key_path"):
        return {"upload_passed": False, "reason": "appid or private_key_path missing"}

    if not config.get("upload_enabled"):
        return {"upload_passed": False, "reason": "upload_enabled is false"}

    import shutil
    if not shutil.which("npx"):
        return {"upload_passed": False, "reason": "npx not found on PATH"}

    return {
        "upload_passed": False,
        "reason": "miniprogram-ci integration pending",
        "config_valid": True,
    }


# ---------------------------------------------------------------------------
# SECTION: Real Inputs
# ---------------------------------------------------------------------------

@app.get("/api/real-inputs/apps")
def get_real_inputs():
    """Get imported real app list."""
    apps_file = REAL_INPUTS_DIR / "apps.json"
    if not apps_file.exists():
        return {"apps": [], "exists": False}
    apps = _read_json(apps_file)
    return {"apps": apps, "exists": True}


@app.post("/api/real-inputs/apps")
async def save_real_inputs(request: Request):
    """Save real app data."""
    body = await request.body()
    data = json.loads(body)
    apps = data if isinstance(data, list) else data.get("apps", [])
    REAL_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (REAL_INPUTS_DIR / "apps.json").write_text(
        json.dumps(apps, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"saved": len(apps)}


# ---------------------------------------------------------------------------
# SECTION: Overview
# ---------------------------------------------------------------------------

@app.get("/api/overview")
def get_overview():
    """Dashboard stats."""
    # Count jobs
    job_count = 0
    if OUTPUTS_DIR.exists():
        job_count = sum(1 for d in OUTPUTS_DIR.iterdir() if d.is_dir())

    # Count real inputs
    apps_file = REAL_INPUTS_DIR / "apps.json"
    real_apps_count = 0
    if apps_file.exists():
        try:
            real_apps_count = len(_read_json(apps_file))
        except Exception:
            pass

    # Platform auth status
    platforms_configured = 0
    for name in ("wechat", "telegram", "discord"):
        cf = PLATFORM_AUTH_DIR / f"{name}.json"
        if cf.exists():
            try:
                c = _read_json(cf)
                if c.get("appid") or c.get("bot_token") or c.get("application_id"):
                    platforms_configured += 1
            except Exception:
                pass

    running = pipeline_process is not None and pipeline_process.poll() is None

    return {
        "total_jobs": job_count,
        "real_apps_imported": real_apps_count,
        "platforms_configured": platforms_configured,
        "pipeline_running": running,
        "current_job_id": pipeline_job_id if running else None,
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


