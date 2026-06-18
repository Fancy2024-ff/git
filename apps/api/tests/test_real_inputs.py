"""apps.api.main 真实输入校验 + 归一化回归。"""

import json


def test_missing_required_fields_is_400(server_client, auth_headers):
    client, _ = server_client
    res = client.post(
        "/api/real-inputs/apps",
        headers=auth_headers,
        json=[{"name": "A", "source": "App Store", "category": "Productivity"}],
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["message"] == "Validation failed"
    assert detail["errors"][0]["index"] == 0


def test_normalizes_missing_cn_fields(server_client, auth_headers):
    client, server = server_client
    payload = [{
        "name": "Cool App",
        "source": "App Store",
        "category": "Productivity",
        "description": "Does cool things",
        "features": ["feat one", "feat two"],
    }]
    res = client.post("/api/real-inputs/apps", headers=auth_headers, json=payload)
    assert res.status_code == 200
    assert res.json()["saved"] == 1

    saved = json.loads((server.REAL_INPUTS_DIR / "apps.json").read_text(encoding="utf-8"))
    app = saved[0]
    assert app["name_cn"] == "Cool App"
    assert app["features_cn"] == ["feat one", "feat two"]
    assert app["description_cn"] == "Does cool things"
    assert app["downloads"] == 0
    assert app["review_count"] == 0
    assert app["monetization"] == "unknown"


def test_empty_list_is_400(server_client, auth_headers):
    client, _ = server_client
    res = client.post("/api/real-inputs/apps", headers=auth_headers, json=[])
    assert res.status_code == 400


def test_model_cross_fills_from_cn_only(server_client):
    _, server = server_client
    model = server.RealAppInput(
        name="X", source="App Store", category="Tools",
        description_cn="中文描述", features_cn=["功能一"],
    )
    assert model.description == "中文描述"
    assert model.features == ["功能一"]
    assert model.name_cn == "X"


def test_save_requires_api_key(server_client):
    client, _ = server_client
    res = client.post("/api/real-inputs/apps", json=[])
    assert res.status_code == 401
