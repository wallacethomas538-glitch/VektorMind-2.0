from vektorflow.agents import aegis_chat, aegis_review, arbiter, hawk, oracle, smaug
from vektorflow.intelligence import analyze_product, detect_niche


def test_niche_detection():
    assert detect_niche("Candle Warmer Lamp") == "home"
    assert detect_niche("Serum Glow Drops", "beauty") == "beauty"
    assert detect_niche("Desk Mat Pro", "office") == "office"


def test_analysis_is_stable():
    a = analyze_product("Candle Warmer Lamp", "home", selling_price=44.99)
    b = analyze_product("Candle Warmer Lamp", "home", selling_price=44.99)
    assert a["opportunity"] == b["opportunity"]
    assert a["slug"] == "candle-warmer-lamp"


def test_aegis_intents():
    assert aegis_chat("Where is my order?")["intent"] == "shipping"
    assert aegis_chat("I want a refund, it arrived broken")["intent"] == "returns"
    assert aegis_review("I love this, great quality")["sentiment"] == "POSITIVE"
    assert aegis_review("It broke and feels cheap")["sentiment"] == "NEGATIVE"


def test_oracle_has_series():
    out = oracle(11.4, 44.99, 100, "home", "Candle Warmer Lamp")
    assert len(out["series"]) == 30
    assert out["recommendation"] in {"LAUNCH", "ITERATE", "THIN"}


def test_smaug_and_arbiter():
    s = smaug("Candle Warmer Lamp", 45)
    assert s["suppliers_found"] >= 1
    a = arbiter("Candle Warmer Lamp", 11.4, 5.5)
    assert a["suggested_price"] >= a["floor_price"] or a["floor_price"] > 0


def test_hawk_copy():
    h = hawk("Resistance Band Set", "fitness", ["home gym"])
    assert h["agent"] == "Hawk"
    assert "Resistance" in h["seo_title"] or "Band" in h["description"]
