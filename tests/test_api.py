from fastapi.testclient import TestClient

from vektorflow.app import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "operational"
    assert body["features"] == 15


def test_dashboard_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "VEKTORFLOW" in res.text


def test_system_roster():
    res = client.get("/api/v1/system")
    assert res.status_code == 200
    body = res.json()
    assert len(body["agents"]) == 15
    assert body["kpis"]["agents_online"] == 15


def test_hawk():
    res = client.post(
        "/api/v1/product-description",
        json={"name": "Candle Warmer Lamp", "category": "home", "keywords": ["cozy", "halogen"]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["agent"] == "Hawk"
    assert "Candle Warmer" in body["description"]
    assert body["scores"]["opportunity"] >= 1


def test_smaug():
    res = client.post(
        "/api/v1/supplier-finder",
        json={"product_name": "Candle Warmer Lamp", "target_selling_price": 45},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["suppliers_found"] >= 1
    assert body["top_suppliers"][0]["landed_cost"] > 0


def test_mission_pipeline():
    res = client.post(
        "/api/v1/mission",
        json={
            "product_name": "Candle Warmer Lamp",
            "category": "home",
            "selling_price": 44.99,
            "product_cost": 11.4,
            "ad_budget": 100,
            "features": ["halogen", "dimmable"],
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["agent"] == "Cerebrum"
    assert body["verdict"] in {"LAUNCH", "ITERATE", "KILL"}
    agents = body["agents"]
    for key in (
        "hawk",
        "smaug",
        "architect",
        "davinci",
        "rook",
        "aegis",
        "arbiter",
        "sentinel",
        "echo",
        "viral",
        "shadow",
        "bundler",
        "pivot",
        "oracle",
        "cerebrum",
    ):
        assert key in agents


def test_oracle_and_rook():
    oracle = client.post(
        "/api/v1/profit-predictor",
        json={"product_cost": 11.4, "selling_price": 44.99, "ad_budget": 80, "niche": "home"},
    )
    assert oracle.status_code == 200
    assert "series" in oracle.json()

    rook = client.post(
        "/api/v1/ad-manager",
        json={
            "target_roas": 2.0,
            "total_daily_budget": 200,
            "product_name": "Candle Warmer Lamp",
            "campaigns": [],
        },
    )
    assert rook.status_code == 200
    assert rook.json()["campaign_actions"]


def test_thin_offer_is_killed():
    res = client.post(
        "/api/v1/mission",
        json={
            "product_name": "Cheap Plastic Gadget",
            "selling_price": 9.99,
            "product_cost": 8.5,
            "ad_budget": 250,
        },
    )
    assert res.status_code == 200
    assert res.json()["verdict"] == "KILL"


def test_deterministic():
    a = client.post("/api/v1/product-description", json={"name": "Desk Mat Pro", "category": "office"})
    b = client.post("/api/v1/product-description", json={"name": "Desk Mat Pro", "category": "office"})
    assert a.json()["scores"] == b.json()["scores"]
