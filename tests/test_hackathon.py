from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
import json

from vektorflow.app import app
import vektorflow.agents as agents

client = TestClient(app)

MISSION_PAYLOAD = {
    "product_name": "Candle Warmer Lamp",
    "category": "home",
    "selling_price": 44.99,
    "product_cost": 11.4,
    "ad_budget": 100,
    "features": ["halogen", "dimmable"],
    "competitor_url": "https://competitor.store/warmer",
}


def _new_mission():
    response = client.post("/api/v1/mission", json=MISSION_PAYLOAD)
    assert response.status_code == 200, response.text
    return response.json()


def test_mission_loop_is_staged_with_visible_pivot_replan():
    body = _new_mission()
    coordination = body["coordination"]

    assert body["mission_id"].startswith("VF-")
    assert len(coordination["plan"]) == 15
    assert [step["agent_id"] for step in coordination["plan"]][-1] == "oracle"

    pivot_step = next(step for step in coordination["plan"] if step["agent_id"] == "pivot")
    assert pivot_step["status"] == "replanned"
    assert pivot_step["replan_on_failure"] is True
    assert pivot_step["attempts"][0]["status"] == "failed"
    assert pivot_step["attempts"][1]["status"] == "completed"
    assert pivot_step["replan"]["provider_contacted"] is False

    assert any(
        event["agent"] == "Pivot" and event["status"] == "failed"
        for event in coordination["events"]
    )
    assert any(
        event["agent"] == "Pivot" and event["status"] == "replanned"
        for event in coordination["events"]
    )

    stages = [entry["stage"] for entry in coordination["trace"]]
    assert stages == [
        "objective",
        "plan",
        "agents",
        "evidence",
        "aegis_gate",
        "approval",
        "receipt",
    ]

    assert len(coordination["evidence"]) == 15
    assert coordination["approvals"][0]["approver"] == "Wallace"
    assert coordination["approvals"][0]["status"] == "pending"
    assert coordination["aegis_gate"]["allowed"] is True
    assert coordination["aegis_gate"]["mode"] == "draft_only"
    assert coordination["risk"]["external_calls"] == 0
    assert coordination["risk"]["money_moved"] is False

    assert coordination["meta_served"] is False
    assert coordination["image_served"] is False
    assert body["meta_served"] is False
    assert body["image_served"] is False
    assert body["draft_only"] is True
    assert body["agents"]["davinci"]["muse_image"]["generated"] is False
    assert body["agents"]["davinci"]["muse_image"]["image_served"] is False
    assert body["persistence"]["status"] == "unconfigured"
    assert body["persistence"]["stored"] is False


def test_muse_spark_live_planner_call_is_mocked(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "draft plan from Muse Spark"}}]}).encode()

    seen = {}
    def fake_urlopen(request, timeout):
        seen.setdefault("requests", []).append({"url": request.full_url, "timeout": timeout, "body": json.loads(request.data)})
        if request.full_url.endswith("/images/generations"):
            return type("ImageResponse", (), {"__enter__": lambda s: s, "__exit__": lambda s, *a: False,
                "read": lambda s: json.dumps({"data": [{"url": "https://cdn.example.test/draft.png"}]}).encode()})()
        return FakeResponse()

    monkeypatch.setenv("META_MODEL_API_KEY", "test-only-key")
    monkeypatch.setattr(agents.urllib_request, "urlopen", fake_urlopen)
    body = _new_mission()

    assert seen["requests"][0]["url"] == "https://api.meta.ai/v1/chat/completions"
    assert seen["requests"][0]["body"]["model"] == "muse-spark-1.3"
    assert "test-only-key" not in json.dumps(body)
    assert body["meta_served"] is True
    assert body["coordination"]["muse_spark"]["output"] == "draft plan from Muse Spark"
    assert body["coordination"]["draft_only"] is True


def test_muse_spark_failure_stays_staged(monkeypatch):
    monkeypatch.setenv("META_MODEL_API_KEY", "test-only-key")
    def failed_urlopen(*args, **kwargs):
        raise TimeoutError("test failure")
    monkeypatch.setattr(agents.urllib_request, "urlopen", failed_urlopen)
    body = _new_mission()

    assert body["meta_served"] is False
    assert body["coordination"]["planner"] == "Muse Spark dynamic planning (staged)"
    assert body["coordination"]["muse_spark"]["status"] == "staged"
    assert "failed" in body["coordination"]["muse_spark"]["reason"]


def test_muse_image_missing_key_stays_staged(monkeypatch):
    monkeypatch.delenv("META_MODEL_API_KEY", raising=False)
    body = _new_mission()

    image = body["coordination"]["muse_image"]
    assert image["status"] == "staged"
    assert image["image_served"] is False
    assert image["reason"] == "META_MODEL_API_KEY is not configured."
    assert body["image_served"] is False


def test_muse_image_success_is_draft_only_and_mocked(monkeypatch):
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"data": [{"url": "https://cdn.example.test/draft.png"}]}).encode()

    seen = {}
    def fake_urlopen(request, timeout):
        seen.update({"url": request.full_url, "body": json.loads(request.data)})
        if request.full_url.endswith("/chat/completions"):
            return type("SparkResponse", (), {"__enter__": lambda s: s, "__exit__": lambda s, *a: False,
                "read": lambda s: json.dumps({"choices": [{"message": {"content": "draft plan"}}]}).encode()})()
        return FakeResponse()

    monkeypatch.setenv("META_MODEL_API_KEY", "test-only-key")
    monkeypatch.setattr(agents.urllib_request, "urlopen", fake_urlopen)
    body = _new_mission()

    assert seen["url"] == "https://api.meta.ai/v1/images/generations"
    assert seen["body"]["model"] == "muse-image-1.0"
    assert body["image_served"] is True
    assert body["coordination"]["muse_image"]["status"] == "staged_for_approval"
    assert body["coordination"]["draft_only"] is True


def test_muse_image_failure_is_plainly_staged(monkeypatch):
    monkeypatch.setenv("META_MODEL_API_KEY", "test-only-key")
    monkeypatch.setattr(agents.urllib_request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("test failure")))
    body = _new_mission()

    image = body["coordination"]["muse_image"]
    assert image["status"] == "staged"
    assert image["image_served"] is False
    assert "Muse Image API call failed" in image["reason"]


def test_each_mission_gets_its_own_receipt():
    first = _new_mission()
    second = _new_mission()
    assert first["mission_id"] != second["mission_id"]

    one = client.get(f"/api/v1/receipt/{first['mission_id']}")
    two = client.get(f"/api/v1/receipt/{second['mission_id']}")
    assert one.status_code == 200
    assert two.status_code == 200
    assert one.json()["plan"] == first["coordination"]["plan"]
    assert two.json()["plan"] == second["coordination"]["plan"]
    assert one.json()["receipt_id"] != two.json()["receipt_id"]


def test_receipt_returns_actual_mission_and_fake_returns_404():
    body = _new_mission()
    mission_id = body["mission_id"]

    response = client.get(f"/api/v1/receipt/{mission_id}")
    assert response.status_code == 200
    receipt = response.json()

    assert receipt["mission_id"] == mission_id
    assert receipt["status"] == "staged_for_approval"
    assert receipt["plan"] == body["coordination"]["plan"]
    assert receipt["evidence"] == body["coordination"]["evidence"]
    assert receipt["approvals"] == body["coordination"]["approvals"]
    assert receipt["risk"]["external_calls"] == 0
    assert receipt["kill_switch"] is False
    assert receipt["meta_served"] is False
    assert receipt["image_served"] is False

    missing = client.get("/api/v1/receipt/VF-DOES-NOT-EXIST-0000000000")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "No staged receipt exists for mission 'VF-DOES-NOT-EXIST-0000000000'."


def test_kill_switch_on_and_off():
    assert client.get("/api/v1/kill-switch").json()["kill_switch"] is False

    on = client.post("/api/v1/kill-switch", json={"engage": True})
    assert on.status_code == 200
    assert on.json()["kill_switch"] is True
    assert client.get("/health").json()["kill_switch"] is True

    blocked_mission = client.post("/api/v1/mission", json=MISSION_PAYLOAD)
    assert blocked_mission.status_code == 503
    assert blocked_mission.json()["detail"]["error"] == "kill_switch_engaged"

    blocked_draft = client.post(
        "/api/v1/ad-draft/pollinations",
        json={"product_name": "Candle Warmer Lamp"},
    )
    assert blocked_draft.status_code == 503

    off = client.post("/api/v1/kill-switch", json={"engage": False})
    assert off.status_code == 200
    assert off.json()["kill_switch"] is False
    assert client.post("/api/v1/mission", json=MISSION_PAYLOAD).status_code == 200


def test_pollinations_draft_is_organic_clamped_and_not_muse_image():
    response = client.post(
        "/api/v1/ad-draft/pollinations",
        json={
            "product_name": "Candle Warmer Lamp",
            "headline": "Instant ambiance, safer than candles",
            "width": 2048,
            "height": 4096,
        },
    )
    assert response.status_code == 200
    draft = response.json()

    assert draft["provider"] == "pollinations"
    assert draft["width"] == 1024
    assert draft["height"] == 1088
    assert draft["clamped"] is True
    assert draft["organic"] is True
    assert draft["draft_only"] is True
    assert draft["provider_contacted"] is False
    assert draft["image_served"] is False
    assert draft["muse_image"] is False
    assert draft["presented_as_muse_image"] is False
    assert draft["auto_send"] is False
    assert "Muse Image" in draft["disclosure"]

    parsed = urlparse(draft["image_url"])
    assert parsed.hostname == "image.pollinations.ai"
    query = parse_qs(parsed.query)
    assert query["width"] == ["1024"]
    assert query["height"] == ["1088"]


def test_pollinations_draft_enforces_minimum_size():
    draft = client.post(
        "/api/v1/ad-draft/pollinations",
        json={"product_name": "Desk Mat Pro", "width": 10, "height": 10},
    ).json()
    assert draft["width"] == 256
    assert draft["height"] == 256


def test_receptionist_draft_does_not_add_an_agent_or_send():
    response = client.post(
        "/api/v1/receptionist/draft",
        json={
            "message": "Where is my order?",
            "product_name": "Candle Warmer Lamp",
            "customer_name": "Maya R.",
        },
    )
    assert response.status_code == 200
    draft = response.json()

    assert draft["agent"] == "Aegis"
    assert draft["is_new_agent"] is False
    assert draft["roster_delta"] == 0
    assert draft["roster_count"] == 15
    assert draft["auto_send"] is False
    assert draft["send_status"] == "not_sent"
    assert draft["intent"] == "shipping"


def test_layout_preview_never_rewrites_or_deploys():
    response = client.post(
        "/api/v1/layout/preview",
        json={"product_name": "Candle Warmer Lamp", "product_price": 44.99},
    )
    assert response.status_code == 200
    preview = response.json()

    assert preview["preview_only"] is True
    assert preview["auto_rewrite"] is False
    assert preview["auto_deploy"] is False
    assert preview["deployment"]["deployed"] is False
    assert preview["files_written"] == []
    assert preview["cms_updated"] is False
    assert len(preview["sections"]) >= 4


def test_mcp_registry_contacts_nothing():
    registry = client.get("/api/v1/mcp/registry").json()

    assert registry["count"] == len(registry["registry"])
    assert registry["server_contacted"] is False
    assert registry["network_calls"] == 0
    assert registry["connections"] == []
    assert all(item["enabled"] is False for item in registry["registry"])
    assert all(item["status"] == "registered_not_connected" for item in registry["registry"])


def test_draft_endpoints_respect_kill_switch():
    client.post("/api/v1/kill-switch", json={"engage": True})
    endpoints = [
        ("/api/v1/receptionist/draft", {"message": "Hello"}),
        ("/api/v1/layout/preview", {"product_name": "Candle Warmer Lamp"}),
    ]
    for path, payload in endpoints:
        response = client.post(path, json=payload)
        assert response.status_code == 503, path
    client.post("/api/v1/kill-switch", json={"engage": False})
