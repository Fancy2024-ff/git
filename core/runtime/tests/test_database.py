"""core.runtime.database 测试：save/get/list（隔离 DB 文件 + 锁）。"""

import pytest

from core.shared.models import MiniAppProject, ProjectStatus


@pytest.fixture
def db(monkeypatch, tmp_path):
    from core.runtime import database
    from filelock import FileLock

    db_file = tmp_path / "pipeline_state.json"
    monkeypatch.setattr(database, "DB_FILE", db_file)
    monkeypatch.setattr(database, "DB_LOCK", FileLock(str(db_file) + ".lock", timeout=10))
    return database


def test_save_and_get_roundtrip(db):
    project = MiniAppProject(id="p1", app_name="Test App")
    db.save_project(project)

    loaded = db.get_project("p1")
    assert loaded is not None
    assert loaded.id == "p1"
    assert loaded.app_name == "Test App"


def test_get_missing_returns_none(db):
    assert db.get_project("nope") is None


def test_list_and_status_filter(db):
    db.save_project(MiniAppProject(id="a", app_name="A", status=ProjectStatus.DISCOVERED))
    db.save_project(MiniAppProject(id="b", app_name="B", status=ProjectStatus.CODE_READY))

    assert len(db.list_projects()) == 2
    ready = db.list_projects(status=ProjectStatus.CODE_READY)
    assert [p.id for p in ready] == ["b"]


def test_save_updates_existing(db):
    db.save_project(MiniAppProject(id="x", app_name="Old"))
    db.save_project(MiniAppProject(id="x", app_name="New"))
    assert db.get_project("x").app_name == "New"
    assert len(db.list_projects()) == 1
