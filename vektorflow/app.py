"""VEKTORFLOW-15 FastAPI application."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

from . import __version__
from .agents import (
    AGENT_ROSTER,
    KillSwitchEngaged,
    aegis_cart,
    aegis_chat,
    aegis_review,
    approve_receipt,
    arbiter,
    architect,
    bundler,
    davinci,
    echo,
    echo_presets,
    forecast,
    get_receipt,
    hawk,
    oracle,
    pivot,
    price_optimize,
    rook,
    run_mission,
    meta_model_configured,
    sentinel,
    shadow,
    smaug,
    viral,
)
from .drafts import layout_preview, mcp_registry, pollinations_ad_draft, receptionist_draft
from .intelligence import analyze_product, default_campaigns, seed_for
from .models import (
    AdCampaign,
    AdManagerRequest,
    BundleBuilderRequest,
    CartItem,
    ChatMessage,
    CompetitorShadowRequest,
    ComplianceRequest,
    CreativeRequest,
    ForecastRequest,
    KillSwitchRequest,
    LayoutPreviewRequest,
    MissionRequest,
    PollinationsAdDraftRequest,
    PriceRequest,
    PricingRequest,
    Product,
    ProfitPredictorRequest,
    ReceptionistDraftRequest,
    Review,
    SentimentPivotRequest,
    StoreBuildRequest,
    SupplierRequest,
    TTSRequest,
    ViralDetectorRequest,
)
from .persistence import PersistenceError
import vektorflow.agents as coordination_agents

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

CONFIGURED_KEY = os.getenv("VEKTORFLOW_API_KEY", "").strip()
DEMO_MODE = os.getenv("VEKTORFLOW_DEMO", "true").lower() not in {"0", "false", "no"}
API_KEY = CONFIGURED_KEY or (None if DEMO_MODE else secrets.token_urlsafe(32))

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    if DEMO_MODE or not API_KEY:
        return api_key or "demo"
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Set X-API-Key or enable VEKTORFLOW_DEMO=true.",
        )
    return api_key


app = FastAPI(
    title="VEKTORFLOW-15",
    description="Autonomous AI E-Commerce Operating System — 15 specialized agents.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def _campaigns_as_dicts(campaigns: List[AdCampaign]) -> List[dict]:
    return [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in campaigns]


@app.get("/", include_in_schema=False)
async def dashboard():
    index = STATIC / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Dashboard not built")
    return FileResponse(index)


@app.get("/health")
async def health():
    return {
        "status": "operational",
        "version": __version__,
        "features": 15,
        "demo_mode": DEMO_MODE or not API_KEY,
        "free_tier": True,
        "powered_by": "VEKTORFLOW-15",
        "license": "Apache 2.0",
        "kill_switch": coordination_agents.kill_switch_state(),
        "draft_only": True,
        "meta_served": meta_model_configured(),
        "image_served": coordination_agents.meta_model_configured(),
        "persistence": coordination_agents.persistence_status(),
    }


@app.get("/api/v1/system", tags=["Cerebrum"])
async def system_status():
    rng = seed_for("ops-feed", datetime.now(timezone.utc).strftime("%Y-%m-%d-%H"))
    feed = [
        {"agent": "Hawk", "text": "Flagged a rising Home & Decor SKU — opportunity 74.", "t": "4m"},
        {"agent": "Rook", "text": "Scaled META-181 +20%. Blended ROAS holding 2.4x.", "t": "11m"},
        {"agent": "ViralDet", "text": "TikTok velocity 412 on candle-warmer audio.", "t": "27m"},
        {"agent": "Aegis", "text": "Recovered a $45 cart. Sequence step 2 fired.", "t": "41m"},
        {"agent": "Sentinel", "text": "Cookie banner contrast check passed.", "t": "1h"},
        {"agent": "Shadow", "text": "Competitor dropped the Mini by $3. Watching.", "t": "2h"},
    ]
    rng.shuffle(feed)
    return {
        "version": __version__,
        "demo_mode": DEMO_MODE or not API_KEY,
        "agents": AGENT_ROSTER,
        "kpis": {
            "agents_online": 15,
            "open_missions": 1,
            "blended_roas": 2.41,
            "compliance": 94,
            "viral_heat": 412,
        },
        "feed": feed[:6],
        "demo_product": "Candle Warmer Lamp",
    }


@app.get("/api/v1/ops", tags=["Cerebrum"])
async def live_ops():
    product = analyze_product("Candle Warmer Lamp", "home", selling_price=44.99, product_cost=11.4)
    campaigns = default_campaigns(product, 220)
    rook_d = rook(campaigns, 2.0, 220, product["name"])
    return {
        "product": product["name"],
        "campaigns": rook_d,
        "pricing": arbiter(product["name"], product["cost"], 5.5),
        "viral": viral(product["name"]),
        "queue": [
            {"from": "Maya R.", "intent": "shipping", "preview": "Where is my warmer?", "age": "6m"},
            {"from": "Chris P.", "intent": "returns", "preview": "Bulb arrived cracked", "age": "19m"},
            {"from": "Priya S.", "intent": "product", "preview": "Will this work with soy wax?", "age": "34m"},
        ],
    }


@app.get("/api/v1/agents", tags=["Cerebrum"])
async def list_agents():
    return {"agents": AGENT_ROSTER, "count": len(AGENT_ROSTER)}


def _ensure_tools_running() -> None:
    if coordination_agents.kill_switch_state():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "kill_switch_engaged",
                "message": "Kill switch is engaged. Tools and model/provider calls are stopped.",
            },
        )


@app.post("/api/v1/mission", tags=["Cerebrum"])
async def mission(req: MissionRequest, _: str = Depends(verify_api_key)):
    payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
    try:
        return run_mission(payload)
    except KillSwitchEngaged:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "kill_switch_engaged",
                "message": "Kill switch is engaged. Tools and model/provider calls are stopped.",
            },
        ) from None


@app.get("/api/v1/kill-switch", tags=["Cerebrum"])
async def kill_switch_status(_: str = Depends(verify_api_key)):
    return {
        "kill_switch": coordination_agents.kill_switch_state(),
        "message": "Read-only status. POST engage=false to restore draft tools.",
    }


@app.post("/api/v1/kill-switch", tags=["Cerebrum"])
async def kill_switch(
    req: Optional[KillSwitchRequest] = None,
    _: str = Depends(verify_api_key),
):
    engage = True if req is None else bool(req.engage)
    state = coordination_agents.set_kill_switch(engage)
    message = (
        "Tools and model/provider calls stopped."
        if state
        else "Kill switch released. Draft-only tools restored; live actions stay blocked."
    )
    return {"ok": True, "kill_switch": state, "message": message}


@app.get("/api/v1/receipt/{mission_id}", tags=["Cerebrum"])
async def mission_receipt(mission_id: str, _: str = Depends(verify_api_key)):
    try:
        receipt = get_receipt(mission_id)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "persistence_unavailable", "persistence": exc.report},
        ) from None
    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail=f"No staged receipt exists for mission '{mission_id}'.",
        )
    return receipt


@app.post("/api/v1/receipt/{mission_id}/approve", tags=["Cerebrum"])
async def approve_mission_receipt(mission_id: str, _: str = Depends(verify_api_key)):
    """Manually approve a staged mission. Status flip only — nothing is
    published, sent, served, or executed; draft-only is preserved."""
    try:
        receipt = approve_receipt(mission_id)
    except PersistenceError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "persistence_unavailable", "persistence": exc.report},
        ) from None
    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail=f"No staged receipt exists for mission '{mission_id}'.",
        )
    return receipt


@app.post("/api/v1/ad-draft/pollinations", tags=["DaVinci"])
async def ad_draft_pollinations(
    req: PollinationsAdDraftRequest, _: str = Depends(verify_api_key)
):
    _ensure_tools_running()
    return pollinations_ad_draft(
        req.product_name,
        req.headline,
        req.features,
        req.width,
        req.height,
        req.seed,
    )


@app.post("/api/v1/receptionist/draft", tags=["Aegis"])
async def receptionist_draft_reply(
    req: ReceptionistDraftRequest, _: str = Depends(verify_api_key)
):
    _ensure_tools_running()
    return receptionist_draft(req.message, req.product_name, req.customer_name)


@app.post("/api/v1/layout/preview", tags=["Architect"])
async def layout_preview_endpoint(
    req: LayoutPreviewRequest, _: str = Depends(verify_api_key)
):
    _ensure_tools_running()
    return layout_preview(
        req.product_name,
        req.product_features,
        req.product_price,
        req.brand_name,
        req.page,
    )


@app.get("/api/v1/mcp/registry", tags=["Cerebrum"])
async def mcp_registry_endpoint(_: str = Depends(verify_api_key)):
    return mcp_registry()


@app.post("/api/v1/product-description", tags=["Hawk"])
async def product_description(product: Product, _: str = Depends(verify_api_key)):
    return hawk(product.name, product.category, product.keywords)


@app.post("/api/v1/supplier-finder", tags=["Smaug"])
async def supplier_finder(req: SupplierRequest, _: str = Depends(verify_api_key)):
    return smaug(req.product_name, req.target_selling_price, req.min_rating or 4.0, req.max_shipping_days or 21)


@app.post("/api/v1/store-builder", tags=["Architect"])
async def store_builder(req: StoreBuildRequest, _: str = Depends(verify_api_key)):
    return architect(
        req.product_name,
        req.product_features,
        req.product_price,
        req.niche,
        req.store_type or "one_product",
        req.brand_name,
    )


@app.post("/api/v1/creative-factory", tags=["DaVinci"])
async def creative_factory(req: CreativeRequest, _: str = Depends(verify_api_key)):
    return davinci(req.product_name, req.product_features, req.product_price, req.creative_type)


@app.post("/api/v1/ad-manager", tags=["Rook"])
async def ad_manager(req: AdManagerRequest, _: str = Depends(verify_api_key)):
    return rook(_campaigns_as_dicts(req.campaigns), req.target_roas or 2.0, req.total_daily_budget, req.product_name)


@app.post("/api/v1/chatbot", tags=["Aegis"])
async def chatbot(msg: ChatMessage, _: str = Depends(verify_api_key)):
    return aegis_chat(msg.message, msg.product_name)


@app.post("/api/v1/review-analyzer", tags=["Aegis"])
async def review_analyzer(review: Review, _: str = Depends(verify_api_key)):
    return aegis_review(review.review_text, review.product_name)


@app.post("/api/v1/abandoned-cart-email", tags=["Aegis"])
async def abandoned_cart_email(cart: CartItem, _: str = Depends(verify_api_key)):
    return aegis_cart(cart.product_name, cart.user_name or "Customer", cart.cart_value)


@app.post("/api/v1/dynamic-pricing", tags=["Arbiter"])
async def dynamic_pricing(req: PricingRequest, _: str = Depends(verify_api_key)):
    comps = [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in req.competitors]
    return arbiter(req.product_name, req.product_cost, req.shipping_cost, comps or None, req.demand_signal or "normal")


@app.post("/api/v1/compliance-audit", tags=["Sentinel"])
async def compliance_audit(req: ComplianceRequest, _: str = Depends(verify_api_key)):
    return sentinel(req.store_name, req.store_url, req.data_collection, req.region or "US-EU")


@app.post("/api/v1/tts/synthesize", tags=["Echo"])
async def tts_synthesize(req: TTSRequest, _: str = Depends(verify_api_key)):
    return echo(req.text, req.voice_name or "Kore", req.product_name)


@app.get("/api/v1/tts/presets", tags=["Echo"])
async def tts_presets(_: str = Depends(verify_api_key)):
    return echo_presets()


@app.post("/api/v1/viral-detector", tags=["ViralDet"])
async def viral_detector(req: ViralDetectorRequest, _: str = Depends(verify_api_key)):
    return viral(req.product_name, req.platforms)


@app.post("/api/v1/competitor-shadow", tags=["Shadow"])
async def competitor_shadow(req: CompetitorShadowRequest, _: str = Depends(verify_api_key)):
    return shadow(req.competitor_url, req.product_name)


@app.post("/api/v1/bundle-builder", tags=["Bundler"])
async def bundle_builder(req: BundleBuilderRequest, _: str = Depends(verify_api_key)):
    return bundler(req.main_product, req.budget, req.product_cost)


@app.post("/api/v1/sentiment-pivot", tags=["Pivot"])
async def sentiment_pivot(req: SentimentPivotRequest, _: str = Depends(verify_api_key)):
    return pivot(req.competitor_product_url, req.product_name)


@app.post("/api/v1/profit-predictor", tags=["Oracle"])
async def profit_predictor(req: ProfitPredictorRequest, _: str = Depends(verify_api_key)):
    return oracle(req.product_cost, req.selling_price, req.ad_budget, req.niche, req.product_name)


@app.post("/api/v1/forecast", tags=["Oracle"])
async def forecast_endpoint(req: ForecastRequest, _: str = Depends(verify_api_key)):
    return forecast(req.historical_sales, req.product_name)


@app.post("/api/v1/price-optimize", tags=["Arbiter"])
async def price_optimize_endpoint(req: PriceRequest, _: str = Depends(verify_api_key)):
    return price_optimize(req.product_id, req.current_price, req.competitor_price)
