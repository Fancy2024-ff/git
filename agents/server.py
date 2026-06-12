"""
FastAPI backend for the MiniApp Factory dashboard.
Exposes REST API + WebSocket for the Vue 3 frontend.
"""

import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure agents/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import DATA_DIR, PRDS_DIR, PROJECTS_DIR, APPS_DIR, REPORTS_DIR
from shared.models import ProjectStatus
from shared.database import _load_db, list_projects, get_project

app = FastAPI(title="MiniApp Factory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State ---
pipeline_process: Optional[subprocess.Popen] = None
pipeline_logs: list[str] = []
connected_clients: list[WebSocket] = []


# === MODELS ===

class PipelineStartRequest(BaseModel):
    category: str = "ai"
    limit: int = 50
    evaluate: bool = True


class SourceConfig(BaseModel):
    qimai_api_key: str = ""
    sensortower_api_key: str = ""
    wechat_appid: str = ""
    alipay_appid: str = ""
    douyin_appid: str = ""


# === ROUTES: Overview ===

@app.get("/api/overview")
def get_overview():
    """Dashboard overview stats."""
    db = _load_db()
    projects = db.get("projects", {})

    total = len(projects)
    by_status = {}
    for p in projects.values():
        status = p.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    # Count PRDs
    prd_count = len(list(PRDS_DIR.glob("*.json"))) if PRDS_DIR.exists() else 0

    # Count generated projects
    project_dirs = len(list(PROJECTS_DIR.iterdir())) if PROJECTS_DIR.exists() else 0

    return {
        "total_projects": total,
        "by_status": by_status,
        "prd_count": prd_count,
        "generated_projects": project_dirs,
        "pipeline_running": pipeline_process is not None and pipeline_process.poll() is None,
    }


# === ROUTES: Opportunities ===

@app.get("/api/opportunities")
def get_opportunities():
    """List all discovered opportunities from the database."""
    db = _load_db()
    projects = db.get("projects", {})

    opportunities = []
    for pid, p in projects.items():
        opp = p.get("opportunity")
        if opp:
            opportunities.append({
                "id": pid,
                "app_name": opp.get("app", {}).get("name", ""),
                "category": opp.get("app", {}).get("category", ""),
                "downloads": opp.get("app", {}).get("downloads", 0),
                "rating": opp.get("app", {}).get("rating", 0),
                "gap_score": opp.get("gap_score", 0),
                "missing_platforms": opp.get("missing_platforms", []),
                "competition_level": opp.get("competition_level", ""),
                "estimated_difficulty": opp.get("estimated_difficulty", ""),
                "reason": opp.get("reason", ""),
                "features": opp.get("app", {}).get("features", []),
                "description": opp.get("app", {}).get("description", ""),
                "status": p.get("status", "discovered"),
            })

    opportunities.sort(key=lambda x: x["gap_score"], reverse=True)
    return {"opportunities": opportunities, "total": len(opportunities)}


# === ROUTES: Projects ===

@app.get("/api/projects")
def get_projects():
    """List all projects."""
    db = _load_db()
    projects = []
    for pid, p in db.get("projects", {}).items():
        projects.append({
            "id": pid,
            "app_name": p.get("app_name", ""),
            "status": p.get("status", ""),
            "project_path": p.get("project_path", ""),
            "target_platforms": p.get("target_platforms", []),
            "created_at": p.get("created_at", ""),
            "updated_at": p.get("updated_at", ""),
        })
    return {"projects": projects}


@app.get("/api/projects/{project_id}")
def get_project_detail(project_id: str):
    """Get project detail including file tree."""
    db = _load_db()
    p = db.get("projects", {}).get(project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    result = dict(p)

    # Build file tree if project path exists
    project_path = Path(p.get("project_path", ""))
    if project_path.exists():
        files = []
        for f in sorted(project_path.rglob("*")):
            if f.is_file():
                files.append({
                    "path": str(f.relative_to(project_path)),
                    "size": f.stat().st_size,
                    "ext": f.suffix,
                })
        result["files"] = files
    else:
        result["files"] = []

    return result


@app.get("/api/projects/{project_id}/file")
def get_project_file(project_id: str, path: str):
    """Read a specific file from a project."""
    db = _load_db()
    p = db.get("projects", {}).get(project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    project_path = Path(p.get("project_path", ""))
    file_path = project_path / path

    # Security: ensure file is within project directory
    try:
        file_path.resolve().relative_to(project_path.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied")

    if not file_path.exists():
        raise HTTPException(404, "File not found")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content, "size": file_path.stat().st_size}


# === ROUTES: Jobs (from data/outputs/) ===

OUTPUTS_DIR = DATA_DIR / "outputs"


@app.get("/api/jobs")
def list_jobs():
    """List all demo pipeline jobs from data/outputs/, sorted by mtime (newest first)."""
    if not OUTPUTS_DIR.exists():
        return {"jobs": []}
    jobs = []
    dirs = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for d in dirs:
        job = {"id": d.name, "path": str(d)}
        qa_file = d / "qa-report.json"
        if qa_file.exists():
            qa = json.loads(qa_file.read_text(encoding="utf-8-sig"))
            job["qa_passed"] = qa.get("passed", False)
            job["build_verified"] = qa.get("checks", {}).get("build_verified", False)
        cand_file = d / "candidate.json"
        if cand_file.exists():
            cand = json.loads(cand_file.read_text(encoding="utf-8-sig"))
            job["app_name"] = cand.get("name_cn", cand.get("name", ""))
            job["app_name_en"] = cand.get("name", "")
        artifacts = [f.name for f in d.iterdir() if f.is_file()]
        job["artifacts"] = artifacts
        job["has_miniapp"] = (d / "generated" / "miniapp").exists()
        jobs.append(job)
    return {"jobs": jobs}


@app.get("/api/jobs/latest")
def get_latest_job():
    """Get the most recent job by mtime."""
    if not OUTPUTS_DIR.exists():
        raise HTTPException(404, "No jobs found")
    dirs = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir()]
    if not dirs:
        raise HTTPException(404, "No jobs found")
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return get_job(dirs[0].name)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Get a specific job's details."""
    job_dir = OUTPUTS_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(404, "Job not found")

    result = {"id": job_id, "path": str(job_dir), "artifacts": {}}

    # Read all JSON/MD artifacts
    for f in job_dir.iterdir():
        if f.is_file():
            if f.suffix == ".json":
                try:
                    result["artifacts"][f.name] = json.loads(f.read_text(encoding="utf-8-sig"))
                except Exception:
                    result["artifacts"][f.name] = {"error": "parse failed"}
            elif f.suffix == ".md":
                result["artifacts"][f.name] = f.read_text(encoding="utf-8-sig")

    # Miniapp file list
    miniapp_dir = job_dir / "generated" / "miniapp"
    if miniapp_dir.exists():
        result["miniapp_files"] = [
            str(f.relative_to(miniapp_dir)) for f in miniapp_dir.rglob("*") if f.is_file() and "node_modules" not in str(f)
        ]
        result["miniapp_path"] = str(miniapp_dir)
    return result


@app.get("/api/jobs/{job_id}/artifact")
def get_job_artifact(job_id: str, file: str):
    """Read a specific artifact file from a job."""
    job_dir = OUTPUTS_DIR / job_id
    file_path = job_dir / file
    # Security check
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


# === ROUTES: Demo Start ===

class DemoStartRequest(BaseModel):
    mode: str = "demo"


@app.post("/api/demo/start")
async def start_demo(req: DemoStartRequest = DemoStartRequest()):
    """Start the pipeline and return job info when complete."""
    global pipeline_process, pipeline_logs

    if pipeline_process and pipeline_process.poll() is None:
        raise HTTPException(409, "Pipeline already running")

    pipeline_logs = []
    scripts_dir = Path(__file__).parent.parent / "scripts"
    python_exe = sys.executable

    cmd = [python_exe, "-X", "utf8", str(scripts_dir / "run_demo_pipeline.py"), "--mode", req.mode]

    pipeline_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).parent.parent),
        env={**dict(__import__("os").environ), "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
    )

    # Wait for completion (demo is fast, < 1s)
    stdout, _ = pipeline_process.communicate(timeout=30)
    pipeline_logs = stdout.strip().split("\n") if stdout else []
    exit_code = pipeline_process.returncode
    pipeline_process = None

    # Find the new job ID from output
    job_id = None
    for line in pipeline_logs:
        if "Job ID:" in line:
            job_id = line.split("Job ID:")[-1].strip()
            break

    return {
        "success": exit_code == 0,
        "job_id": job_id,
        "exit_code": exit_code,
        "log_lines": len(pipeline_logs),
        "logs": pipeline_logs[-20:],
    }


# === ROUTES: PRD ===

@app.get("/api/prds")
def list_prds():
    """List all generated PRDs."""
    if not PRDS_DIR.exists():
        return {"prds": []}

    prds = []
    for f in sorted(PRDS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            prds.append({
                "filename": f.name,
                "app_name": data.get("app_name", f.stem),
                "summary": data.get("summary", "")[:100],
                "features_count": len(data.get("core_features", [])),
                "feasibility_score": data.get("feasibility_score", 0),
                "created_at": data.get("created_at", ""),
            })
        except (json.JSONDecodeError, Exception):
            continue

    return {"prds": prds}


@app.get("/api/prds/{filename}")
def get_prd_detail(filename: str):
    """Get full PRD content."""
    filepath = PRDS_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "PRD not found")

    data = json.loads(filepath.read_text(encoding="utf-8"))
    return data


# === ROUTES: Pipeline Control ===

@app.get("/api/pipeline/status")
def pipeline_status():
    """Get current pipeline status."""
    running = pipeline_process is not None and pipeline_process.poll() is None
    return {
        "running": running,
        "logs": pipeline_logs[-100:],  # Last 100 lines
        "log_count": len(pipeline_logs),
    }


@app.post("/api/pipeline/start")
async def start_pipeline(req: PipelineStartRequest):
    """Start the pipeline in a background process."""
    global pipeline_process, pipeline_logs

    if pipeline_process and pipeline_process.poll() is None:
        raise HTTPException(409, "Pipeline already running")

    pipeline_logs = []
    scripts_dir = Path(__file__).parent.parent / "scripts"
    venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"

    cmd = [
        str(venv_python), "-X", "utf8",
        str(scripts_dir / "test_full_pipeline.py"),
    ]

    pipeline_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(Path(__file__).parent.parent),
        env={**dict(__import__("os").environ), "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
    )

    # Start reading output in background
    asyncio.get_event_loop().create_task(_read_pipeline_output())

    return {"message": "Pipeline started", "pid": pipeline_process.pid}


@app.post("/api/pipeline/stop")
def stop_pipeline():
    """Stop the running pipeline."""
    global pipeline_process
    if pipeline_process and pipeline_process.poll() is None:
        pipeline_process.terminate()
        pipeline_process = None
        return {"message": "Pipeline stopped"}
    return {"message": "No pipeline running"}


async def _read_pipeline_output():
    """Read pipeline stdout and broadcast to WebSocket clients."""
    global pipeline_process
    if not pipeline_process:
        return

    loop = asyncio.get_event_loop()
    while pipeline_process and pipeline_process.poll() is None:
        line = await loop.run_in_executor(None, pipeline_process.stdout.readline)
        if line:
            line = line.rstrip()
            pipeline_logs.append(line)
            # Broadcast to connected WebSocket clients
            for ws in connected_clients[:]:
                try:
                    await ws.send_text(json.dumps({"type": "log", "data": line}))
                except Exception:
                    connected_clients.remove(ws)


# === ROUTES: Data Sources ===

@app.get("/api/sources")
def get_sources():
    """Get configured data source info."""
    from config.settings import QIMAI_API_KEY, SENSORTOWER_API_KEY, WECHAT_APPID, ALIPAY_APPID, DOUYIN_APPID
    return {
        "qimai": {"configured": bool(QIMAI_API_KEY), "key_preview": QIMAI_API_KEY[:8] + "..." if QIMAI_API_KEY else ""},
        "sensortower": {"configured": bool(SENSORTOWER_API_KEY), "key_preview": SENSORTOWER_API_KEY[:8] + "..." if SENSORTOWER_API_KEY else ""},
        "wechat": {"configured": bool(WECHAT_APPID), "appid": WECHAT_APPID},
        "alipay": {"configured": bool(ALIPAY_APPID), "appid": ALIPAY_APPID},
        "douyin": {"configured": bool(DOUYIN_APPID), "appid": DOUYIN_APPID},
    }


# === WebSocket ===

@app.websocket("/ws/pipeline")
async def websocket_pipeline(ws: WebSocket):
    """WebSocket for real-time pipeline logs."""
    await ws.accept()
    connected_clients.append(ws)

    # Send existing logs
    for log in pipeline_logs[-50:]:
        await ws.send_text(json.dumps({"type": "log", "data": log}))

    # Send current status
    running = pipeline_process is not None and pipeline_process.poll() is None
    await ws.send_text(json.dumps({"type": "status", "running": running}))

    try:
        while True:
            await ws.receive_text()  # Keep alive
    except WebSocketDisconnect:
        connected_clients.remove(ws)


# === ROUTES: Real Inputs ===

REAL_INPUTS_DIR = DATA_DIR / "real_inputs"


@app.get("/api/real-inputs/apps")
def get_real_inputs():
    """Get imported real apps."""
    apps_file = REAL_INPUTS_DIR / "apps.json"
    if not apps_file.exists():
        return {"apps": [], "exists": False}
    apps = json.loads(apps_file.read_text(encoding="utf-8-sig"))
    return {"apps": apps, "exists": True}


@app.post("/api/real-inputs/apps")
async def save_real_inputs(request):
    """Save real app data."""
    from starlette.requests import Request
    body = await request.body()
    data = json.loads(body)
    apps = data if isinstance(data, list) else data.get("apps", [])
    REAL_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (REAL_INPUTS_DIR / "apps.json").write_text(
        json.dumps(apps, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"saved": len(apps)}


# === Run ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
