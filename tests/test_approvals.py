"""Manual approval of staged mission receipts.

POST /api/v1/receipt/{mission_id}/approve flips pending approvals to
approved. It must never publish, send, serve, or execute anything —
draft-only is preserved and the Aegis Gate is untouched.
"""

from fastapi.testclient import TestClient

from vektorflow.app import app
import vektorflow.agents as agents

client = TestClient(app)

MISSION_PAYLOAD = {
    "product_name": "Candle Warmer Lamp",
    "category": "home",
    "selling_price": 44.99,
    "product_cost": 11.4,
    "ad_budget": 100,
}


def _new_mission():
    response = client.post("/api/v1/mission", json=MISSION_PAYLOAD)
    assert response.status_code == 200, response.text
    return response.json()


def _approve(mission_id):
    return client.post(f"/api/v1/receipt/{mission_id}/approve")


def test_approve_happy_path_flips_pending_to_approved():
    mission_id = _new_mission()["mission_id"]

    before = client.get(f"/api/v1/receipt/{mission_id}").json()
    assert before["status"] == "staged_for_approval"
    assert all(a["status"] == "pending" for a in before["approvals"])
    assert before["approved_by"] is None

    response = _approve(mission_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["status"] == "approved"
    assert body["approved_by"] == "Wallace"
    assert body["approved_at"]
    assert all(a["status"] == "approved" for a in body["approvals"])
    assert all(a["decided_at"] for a in body["approvals"])
    assert body["receipt"]["status"] == "approved"
    approval_stage = next(e for e in body["trace"] if e["stage"] == "approval")
    assert approval_stage["status"] == "approved"


def test_approve_unknown_mission_returns_404():
    response = _approve("VF-00000-deadbeef00")
    assert response.status_code == 404


def test_approve_is_idempotent():
    mission_id = _new_mission()["mission_id"]

    first = _approve(mission_id)
    assert first.status_code == 200
    first_body = first.json()

    second = _approve(mission_id)
    assert second.status_code == 200
    second_body = second.json()

    assert second_body["status"] == "approved"
    assert all(a["status"] == "approved" for a in second_body["approvals"])
    # Same decision stands; no duplicate or escalated state.
    assert second_body["approved_by"] == "Wallace"


def test_approve_preserves_draft_only_and_changes_nothing_else():
    mission_id = _new_mission()["mission_id"]
    before = client.get(f"/api/v1/receipt/{mission_id}").json()

    body = _approve(mission_id).json()

    # Draft-only invariant: approval records a decision, executes nothing.
    assert body["draft_only"] is True
    assert body["kill_switch"] is False
    # Plan and evidence untouched.
    assert len(body["plan"]) == len(before["plan"])
    assert len(body["evidence"]) == len(before["evidence"])
    # Aegis Gate untouched.
    assert body["aegis_gate"] == before["aegis_gate"]
    assert body["aegis_gate"]["mode"] == "draft_only"
    # Blocked actions still blocked.
    assert "publish_live" in body["risk"]["blocked_actions"]


def test_approve_survives_persistence_outage():
    mission_id = _new_mission()["mission_id"]

    original = agents.persistence.save_mission

    def boom(receipt):
        raise agents.persistence.PersistenceError("down", report={"status": "error"})

    agents.persistence.save_mission = boom
    try:
        response = _approve(mission_id)
    finally:
        agents.persistence.save_mission = original

    # Memory holds the truth; the approval still lands.
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "approved"
