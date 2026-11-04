"""VEKTORFLOW-15 FastAPI application."""

from __future__ import annotations

import asyncio
import os
import secrets
import socket
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

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
    approve_image_generation,
    chat_with_spark,
    approve_receipt,
    arbiter,
    architect,
    bundler,
    davinci,
    echo,
    echo_presets,
    forecast,
    get_generated_images,
    get_staged_image_request,
    get_latest_receipt,
    get_receipt,
    hawk,
    oracle,
    pivot,
    price_optimize,
    rook,
    run_mission,
    meta_model_configured,
    meta_api_base_url,
    sentinel,
    stage_image_generation,
    shadow,
    smaug,
    viral,
)
from .drafts import layout_preview, mcp_registry, pollinations_ad_draft, receptionist_draft
from .intelligence import analyze_product, default_campaigns
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
    ImageGenerateRequest,
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


@app.get("/api/v1/meta-diagnostics", tags=["Cerebrum"])
async def meta_diagnostics():
    """Draft-only network diagnostics; never includes credentials or response bodies."""
    base = meta_api_base_url()
    host = urlparse(base).hostname
    addresses = []
    dns_error = None
    tcp_connected = False
    tcp_error = None
    probe_status = None
    probe_headers = {}
    if host:
        try:
            addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
        except OSError as exc:
            dns_error = type(exc).__name__
        try:
            with socket.create_connection((host, 443), timeout=5):
                tcp_connected = True
        except OSError as exc:
            tcp_error = type(exc).__name__
    try:
        probe = urllib_request.Request(f"{base}/v1/chat/completions", method="HEAD")
        with urllib_request.urlopen(probe, timeout=5) as response:
            probe_status = response.status
            probe_headers = dict(response.headers.items())
    except HTTPError as exc:
        probe_status = exc.code
        probe_headers = dict(exc.headers.items()) if exc.headers else {}
    except (URLError, TimeoutError, OSError) as exc:
        probe_status = None
        probe_headers = {"error_type": type(exc).__name__}
    return {
        "host": host,
        "resolved_ips": addresses,
        "dns_error": dns_error,
        "tcp_connect": tcp_connected,
        "tcp_error": tcp_error,
        "probe": {"method": "HEAD", "url": f"{base}/v1/chat/completions", "status": probe_status, "headers": probe_headers},
        "proxy_configured": bool(os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")),
    }


@app.get("/api/v1/system", tags=["Cerebrum"])
async def system_status():
    return {
        "version": __version__,
        "demo_mode": DEMO_MODE or not API_KEY,
        "agents": AGENT_ROSTER,
        "kpis": {
            "agents_online": 15,
            "open_missions": 0,
            "blended_roas": 0,
            "compliance": 0,
            "viral_heat": 0,
        },
        "feed": [],
        "demo_product": None,
    }


@app.get("/api/v1/ops", tags=["Cerebrum"])
async def live_ops():
    """Live Ops reads the latest staged mission in this session.

    No canned demo product, no fake support queue. If no mission has been
    staged yet, returns an explicit empty state instead of invented data.
    """
    receipt = get_latest_receipt()
    if receipt is None:
        return {
            "live": False,
            "empty": True,
            "product": None,
            "campaigns": None,
            "pricing": None,
            "viral": None,
            "queue": [],
            "message": "No mission staged yet in this session. Run a mission and Live Ops will read it.",
        }
    objective = receipt.get("objective") or {}
    name = objective.get("product") or "Unnamed product"
    category = objective.get("category") or "general"
    price = float(objective.get("target_price") or 44.99)
    cost = objective.get("product_cost_input")
    budget = float(objective.get("ad_budget") or 100)
    product = analyze_product(name, category, selling_price=price, product_cost=cost)
    campaigns = default_campaigns(product, budget)
    rook_d = rook(campaigns, 2.0, budget, product["name"])
    return {
        "live": True,
        "empty": False,
        "mission_id": receipt.get("mission_id"),
        "product": product["name"],
        "campaigns": rook_d,
        "pricing": arbiter(product["name"], product["cost"], 5.5),
        "viral": viral(product["name"]),
        "queue": [],
        "queue_note": "No live support feed connected. Support items appear here when a real feed is wired.",
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


@app.post("/api/v1/images/generate", tags=["DaVinci"])
async def images_generate(req: ImageGenerateRequest, _: str = Depends(verify_api_key)):
    """Stage an image request. Aegis-scored; nothing is generated until approved."""
    _ensure_tools_running()
    return stage_image_generation(req.prompt)


@app.post("/api/v1/images/generate/{request_id}/approve", tags=["DaVinci"])
async def images_generate_approve(request_id: str, _: str = Depends(verify_api_key)):
    """Owner approval: run the staged prompt through Muse Image and return the image."""
    _ensure_tools_running()
    # The Meta call blocks (urllib, up to ~30s): keep it off the event loop
    # so the dashboard stays responsive while an image generates.
    result = await asyncio.to_thread(approve_image_generation, request_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("reason"))
    return result


@app.post("/api/v1/chat", tags=["Muse Spark"])
async def chat_turn(payload: Dict[str, Any], _: str = Depends(verify_api_key)):
    """Live conversation with Muse Spark. Each message is a real Meta call."""
    _ensure_tools_running()
    message = str(payload.get("message") or "").strip()[:2000]
    if not message:
        raise HTTPException(status_code=422, detail="message is required")
    raw_history = payload.get("history") or []
    turns = []
    for m in raw_history[-20:]:
        if isinstance(m, dict) and str(m.get("content") or "").strip():
            turns.append({"role": "assistant" if m.get("role") == "assistant" else "user",
                          "content": str(m.get("content"))[:2000]})
    turns.append({"role": "user", "content": message})
    result = await asyncio.to_thread(chat_with_spark, turns)
    return result


@app.get("/api/v1/images/generate/{request_id}", tags=["DaVinci"])
async def images_generate_status(request_id: str, _: str = Depends(verify_api_key)):
    """Recover a staged image request's state (e.g. after a panel reload)."""
    record = get_staged_image_request(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No staged image request '{request_id}'.")
    return record


@app.get("/api/v1/images/history", tags=["DaVinci"])
async def images_history(_: str = Depends(verify_api_key)):
    """Session gallery: every image generated through the approve flow, newest first."""
    return {"images": get_generated_images(), "count": len(get_generated_images())}


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
