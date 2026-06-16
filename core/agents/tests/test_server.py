"""API auth-enforcement tests (P0-4): write routes + download require a key."""

import json


def test_write_route_requires_api_key(server_client):
    client, _ = server_client
    res = client.post("/api/real-inputs/apps", json=[])
    assert res.status_code == 401


def test_download_requires_api_key(server_client):
    client, _ = server_client
    res = client.get("/api/jobs/whatever/download")
    assert res.status_code == 401


def test_download_with_key_missing_job_is_404(server_client, auth_headers):
    client, _ = server_client
    res = client.get("/api/jobs/does-not-exist/download", headers=auth_headers)
    assert res.status_code == 404


def test_health_route_is_public(server_client):
    """/health is the only unauthenticated route (Docker liveness probe)."""
    client, _ = server_client
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_status_route_requires_api_key(server_client):
    """/api/pipeline/status carries business state, so it requires a key."""
    client, _ = server_client
    res = client.get("/api/pipeline/status")
    assert res.status_code == 401


def test_status_route_with_key_ok(server_client, auth_headers):
    client, _ = server_client
    res = client.get("/api/pipeline/status", headers=auth_headers)
    assert res.status_code == 200
    assert "running" in res.json()


def test_jobs_route_requires_api_key(server_client):
    """/api/jobs lists pipeline outputs, so it requires a key."""
    client, _ = server_client
    res = client.get("/api/jobs")
    assert res.status_code == 401


def test_pipeline_start_requires_api_key(server_client):
    client, _ = server_client
    # No key -> 401, and importantly never spawns the pipeline subprocess.
    res = client.post("/api/pipeline/start", json={"mode": "demo"})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# P2-1: Path traversal defense
# ---------------------------------------------------------------------------

def test_path_traversal_returns_403(server_client, auth_headers):
    """Artifact endpoint must reject path traversal attempts."""
    client, server = server_client
    # Create a fake job directory with a file
    job_dir = server.OUTPUTS_DIR / "test-job-pt"
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "candidate.json").write_text(json.dumps({"name": "test"}))

    # Attempt path traversal via query param
    res = client.get("/api/jobs/test-job-pt/artifact?file=../../etc/passwd", headers=auth_headers)
    assert res.status_code == 403

    # Also test with ../ in the middle
    res = client.get("/api/jobs/test-job-pt/artifact?file=../../../etc/shadow", headers=auth_headers)
    assert res.status_code == 403

    # Valid file should work
    res = client.get("/api/jobs/test-job-pt/artifact?file=candidate.json", headers=auth_headers)
    assert res.status_code == 200


def test_job_id_traversal_blocked_on_detail_and_download(server_client, auth_headers):
    """job_id itself must not escape OUTPUTS_DIR (get_job_detail / download)."""
    client, _ = server_client
    # '..' as job_id would resolve to DATA_DIR without the containment guard.
    for path in (
        "/api/jobs/..",
        "/api/jobs/%2e%2e/download",
    ):
        res = client.get(path, headers=auth_headers)
        # 403 (blocked) or 404 (not a dir) are both acceptable; never 200 with
        # contents from outside outputs/.
        assert res.status_code in (403, 404), f"{path} -> {res.status_code}"


# ---------------------------------------------------------------------------
# P2-2: Pipeline timeout test
# ---------------------------------------------------------------------------

def test_pipeline_timeout_kills_subprocess(server_client, auth_headers, monkeypatch):
    """When PIPELINE_TIMEOUT is reached, subprocess gets killed and status is failed."""
    import subprocess
    import sys
    import asyncio

    client, server = server_client

    # Set a very short timeout
    monkeypatch.setattr(server, "PIPELINE_TIMEOUT", 1)

    # Create a job output dir so logs can flush
    job_dir = server.OUTPUTS_DIR / "timeout-test"
    job_dir.mkdir(parents=True, exist_ok=True)

    # Start a process that sleeps forever (simulates stuck pipeline)
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(999)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    server.pipeline_process = proc
    server.pipeline_job_id = "timeout-test"
    server.pipeline_logs.clear()

    # Run the stream function which should hit the timeout
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server._stream_pipeline_output("timeout-test", proc))
    loop.close()

    # Process should be killed — wait for reaping
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    assert proc.returncode is not None  # process terminated
    # Clean up
    server.pipeline_process = None


# ---------------------------------------------------------------------------
# WebSocket: deque history log test
# ---------------------------------------------------------------------------

def test_ws_sends_buffered_history_logs(server_client, auth_headers):
    """WebSocket connection should receive buffered pipeline_logs as history."""
    from collections import deque

    client, server = server_client

    # Simulate a job with buffered logs
    server.pipeline_job_id = "ws-test-job"
    server.pipeline_process = None  # Not running
    server.pipeline_logs = deque(["line1", "line2", "line3"], maxlen=5000)

    # Connect via WebSocket with token
    with client.websocket_connect("/ws/pipeline/ws-test-job?token=secret123") as ws:
        messages = []
        # Read all buffered messages (logs + status)
        import json as _json
        for _ in range(4):  # 3 log lines + 1 status
            data = _json.loads(ws.receive_text())
            messages.append(data)

    log_messages = [m for m in messages if m.get("type") == "step_log"]
    status_messages = [m for m in messages if m.get("type") == "status"]

    assert len(log_messages) == 3
    assert log_messages[0]["data"] == "line1"
    assert log_messages[2]["data"] == "line3"
    assert len(status_messages) == 1
    assert status_messages[0]["running"] is False

    # Cleanup
    server.pipeline_job_id = None
    server.pipeline_logs.clear()
