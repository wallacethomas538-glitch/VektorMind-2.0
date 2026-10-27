import json

import httpx
import pytest

from vektorflow import persistence


def _receipt(mission_id="VF-123-abc"):
    return {
        "mission_id": mission_id,
        "receipt_id": f"receipt-{mission_id}",
        "status": "staged_for_approval",
        "objective": {"goal": "stage drafts"},
        "plan": [{"step": 1, "agent_id": "hawk", "status": "completed"}],
        "evidence": [{"agent_id": "hawk", "status": "completed"}],
        "approvals": [
            {
                "approver": "Wallace",
                "role": "final tap",
                "status": "pending",
                "scope": "review drafts",
                "requested_at": "2026-10-27T00:00:00Z",
            }
        ],
        "risk": {"score": 2},
        "kill_switch": False,
        "meta_served": False,
        "image_served": False,
        "receipt": {"id": f"receipt-{mission_id}", "status": "staged_for_approval", "issued_at": "2026-10-27T00:00:00Z"},
    }


def test_generic_supabase_env_is_ignored(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://old-project.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "old-key")

    status = persistence.configuration_status()
    assert status["state"] == "unconfigured"
    assert status["reads_generic_supabase_env"] is False

    report = persistence.save_mission(_receipt())
    assert report["stored"] is False
    assert report["backend"] == "in-memory"
    assert report["status"] == "unconfigured"


def test_partial_configuration_does_not_call_out(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://hackathon.supabase.co")
    status = persistence.configuration_status()
    assert status["state"] == "incomplete"

    report = persistence.save_mission(_receipt())
    assert report["stored"] is False
    assert report["status"] == "incomplete"


def test_non_supabase_or_http_url_is_rejected(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "http://hackathon.supabase.co")
    monkeypatch.setenv("HACKATHON_SUPABASE_KEY", "test-key")
    assert persistence.configuration_status()["state"] == "invalid_url"

    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://example.com")
    assert persistence.configuration_status()["state"] == "invalid_url"


def test_save_and_fetch_use_only_the_hackathon_project(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://hackathon2026.supabase.co")
    monkeypatch.setenv("HACKATHON_SUPABASE_KEY", "hackathon-key")

    receipt = _receipt()
    calls = []
    stored_rows = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(
            {
                "host": request.url.host,
                "path": request.url.path,
                "method": request.method,
                "params": dict(request.url.params),
                "apikey": request.headers.get("apikey"),
                "authorization": request.headers.get("authorization"),
            }
        )
        if request.method == "POST":
            stored_rows.append((request.url.path.rsplit("/", 1)[-1], json.loads(request.content)))
            return httpx.Response(201, json=[])
        if request.url.path.endswith("/mission_receipts"):
            return httpx.Response(200, json=[{"receipt": receipt}])
        if request.url.path.endswith("/missions"):
            return httpx.Response(200, json=[{"id": receipt["mission_id"]}])
        return httpx.Response(200, json=[])

    client = httpx.Client(transport=httpx.MockTransport(handler))

    report = persistence.save_mission(receipt, client=client)
    assert report["stored"] is True
    assert report["status"] == "stored"
    assert report["project"] == "hackathon-2026"
    assert [step["table"] for step in report["steps"]] == [
        "missions",
        "mission_receipts",
        "approvals",
    ]
    assert report["steps"][2]["rows"] == 1

    tables = [table for table, _ in stored_rows]
    assert tables == ["missions", "mission_receipts", "approvals"]
    receipt_row = stored_rows[1][1]
    assert receipt_row["mission_id"] == receipt["mission_id"]
    assert receipt_row["meta_served"] is False
    assert receipt_row["image_served"] is False
    approval_row = stored_rows[2][1]
    assert approval_row["approver"] == "Wallace"
    assert approval_row["status"] == "pending"

    fetched = persistence.fetch_receipt(receipt["mission_id"], client=client)
    assert fetched == receipt

    assert calls
    assert all(call["host"] == "hackathon2026.supabase.co" for call in calls)
    assert all(call["apikey"] == "hackathon-key" for call in calls)
    assert all(call["authorization"] == "Bearer hackathon-key" for call in calls)


def test_fetch_unknown_mission_returns_none(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://hackathon2026.supabase.co")
    monkeypatch.setenv("HACKATHON_SUPABASE_KEY", "hackathon-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert persistence.fetch_receipt("VF-FAKE", client=client) is None


def test_existing_mission_without_receipt_is_an_error(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://hackathon2026.supabase.co")
    monkeypatch.setenv("HACKATHON_SUPABASE_KEY", "hackathon-key")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/mission_receipts"):
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[{"id": "VF-REAL"}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(persistence.PersistenceError) as excinfo:
        persistence.fetch_receipt("VF-REAL", client=client)
    assert excinfo.value.report["status"] == "error"
    assert "hackathon-key" not in str(excinfo.value.report)


def test_http_failure_is_sanitized(monkeypatch):
    monkeypatch.setenv("HACKATHON_SUPABASE_URL", "https://hackathon2026.supabase.co")
    monkeypatch.setenv("HACKATHON_SUPABASE_KEY", "hackathon-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "secret-ish"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(persistence.PersistenceError) as excinfo:
        persistence.save_mission(_receipt(), client=client)
    assert excinfo.value.report["http_status"] == 401
    assert "hackathon-key" not in str(excinfo.value.report)
    assert "secret-ish" not in str(excinfo.value.report)
