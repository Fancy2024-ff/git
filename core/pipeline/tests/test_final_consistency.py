"""最终一致性回归：运行时协议字段 + 部署口径。

锁定：
  1. pipeline 步骤事件/报告以 step/capability 为唯一正式字段。
  2. 部署口径与 codegen 真源一致：compose 不再起 Node generator 服务，
     不再强制 GENERATOR_API_KEY / GENERATOR_URL。
"""

from pathlib import Path

import importlib.util
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_runner():
    spec = importlib.util.spec_from_file_location("runner_proto_test", PROJECT_ROOT / "core" / "pipeline" / "runner.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_step_report_entry_uses_step_capability_protocol(tmp_path, monkeypatch):
    runner = _load_runner()
    # 隔离报告输出目录与状态
    monkeypatch.setattr(runner, "_pipeline_output_dir", tmp_path)
    monkeypatch.setattr(runner, "_pipeline_steps", [])
    runner.step_start("market_input", "读取市场数据", "MarketInput")
    entry = runner._pipeline_steps[-1]
    assert entry["step"] == "market_input"
    assert entry["capability"] == "MarketInput"
    assert "agent" not in entry
    # 报告文件已落盘且只使用 capability 协议字段
    import json
    report = json.loads((tmp_path / "pipeline-report.json").read_text(encoding="utf-8"))
    assert report["steps"][0]["capability"] == "MarketInput"
    assert "agent" not in report["steps"][0]


def test_no_agent_suffix_capability_names_in_runner():
    """runner 不再输出/展示 agent 协议字段，也无 *_agent 业务函数。"""
    src = (PROJECT_ROOT / "core" / "pipeline" / "runner.py").read_text(encoding="utf-8")
    assert '"agent"' not in src
    assert "AGENTS" not in src
    for bad in ('"MarketInputAgent"', '"CodegenAgent"', '"QACheckAgent"',
                "def codegen_agent", "def qa_check_agent", "def market_input_agent"):
        assert bad not in src, f"residual agent token: {bad}"


def test_compose_has_no_generator_service():
    """部署口径：compose 不再起 Node generator 服务，不再强制 GENERATOR_* 。"""
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    # 不再有 generator 服务定义 / 依赖 / 端口
    assert "Dockerfile.generator" not in compose
    assert "generator:" not in compose
    assert "GENERATOR_API_KEY" not in compose
    assert "GENERATOR_URL" not in compose


def test_runtime_config_has_no_generator_url():
    cfg = (PROJECT_ROOT / "core" / "runtime" / "config.py").read_text(encoding="utf-8")
    assert "GENERATOR_URL =" not in cfg


def test_compose_mounts_canonical_input_path_with_healthcheck():
    """部署口径与 canonical 输入路径一致 + healthcheck 语义完整。"""
    import yaml
    compose = yaml.safe_load((PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    api = compose["services"]["api"]
    # canonical 输入路径已挂载（与 apps/api/main.py 的 _real_inputs_file 一致）
    vols = api.get("volumes", [])
    assert any("/app/data/inputs/real" in v for v in vols), f"canonical input mount missing: {vols}"
    # 不再挂载 legacy real_inputs（避免双口径）
    assert not any("real_inputs" in v for v in vols), f"legacy mount should be gone: {vols}"
    # api 有真实 healthcheck，dashboard 的 service_healthy 才有意义
    assert "healthcheck" in api and api["healthcheck"].get("test"), "api healthcheck missing"
    dash = compose["services"]["dashboard"]
    assert dash["depends_on"]["api"]["condition"] == "service_healthy"


def test_api_and_runner_use_only_canonical_real_input_path():
    """real 模式只读 data/inputs/real/apps.json，不保留 data/real_inputs fallback。"""
    runner = (PROJECT_ROOT / "core" / "pipeline" / "runner.py").read_text(encoding="utf-8")
    api = (PROJECT_ROOT / "apps" / "api" / "main.py").read_text(encoding="utf-8")
    assert "data/inputs/real/apps.json" in runner
    assert "data/real_inputs" not in runner
    assert "LEGACY_REAL_INPUTS_DIR" not in runner
    assert "LEGACY_REAL_INPUTS_DIR" not in api
    assert "data/real_inputs" not in api


def test_step_capability_map_doc_exists_and_agent_map_renamed():
    """文件名收口：AGENT_MAP.md 已重命名为 STEP_CAPABILITY_MAP.md。"""
    arch = PROJECT_ROOT / "docs" / "architecture"
    assert (arch / "STEP_CAPABILITY_MAP.md").exists()
    assert not (arch / "AGENT_MAP.md").exists()
