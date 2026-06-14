"""Shared pytest fixtures for the agents test suite."""

import importlib
import sys
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))


@pytest.fixture
def server_client(monkeypatch, tmp_path):
    """Return (TestClient, server_module) with auth enabled and isolated data dirs.

    The real DATA_DIR is never touched: REAL_INPUTS_DIR / OUTPUTS_DIR are
    redirected to a tmp path after import.
    """
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DASHBOARD_API_KEY", "secret123")

    # Import fresh so module-level env reads (DASHBOARD_API_KEY) take effect.
    sys.modules.pop("server", None)
    import server
    importlib.reload(server)

    server.REAL_INPUTS_DIR = tmp_path / "real_inputs"
    server.OUTPUTS_DIR = tmp_path / "outputs"
    server.REAL_INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    server.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    from fastapi.testclient import TestClient

    yield TestClient(server.app), server

    # Teardown: reset global state
    server.pipeline_process = None
    server.pipeline_job_id = None
    server.pipeline_logs.clear()
    server.ws_clients.clear()


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "secret123"}
