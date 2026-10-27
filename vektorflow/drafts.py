"""Draft-only extensions for the hackathon demo.

Nothing in this module publishes, sends, rewrites, deploys, prices live, moves
money, or contacts an MCP server. Provider URLs are returned as drafts for a
human to review and fetch on demand.

The Pollinations image draft is organic creative. It is **not** Muse Image and
must never be labelled as Muse Image.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .agents import AGENT_ROSTER, aegis_chat, architect
from .intelligence import analyze_product, seed_for

MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1088
MIN_IMAGE_SIDE = 256


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    return text or fallback


def _safe_seed(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def pollinations_ad_draft(
    product_name: str,
    headline: Optional[str] = None,
    features: Optional[List[str]] = None,
    width: int = MAX_IMAGE_WIDTH,
    height: int = MAX_IMAGE_HEIGHT,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Return an organic Pollinations ad draft. Never Muse Image, never served."""

    name = _safe_text(product_name, "the product")
    product = analyze_product(name, features=features)
    requested_width = width
    requested_height = height
    safe_width = _clamp_int(width, MIN_IMAGE_SIDE, MAX_IMAGE_WIDTH, MAX_IMAGE_WIDTH)
    safe_height = _clamp_int(height, MIN_IMAGE_SIDE, MAX_IMAGE_HEIGHT, MAX_IMAGE_HEIGHT)
    safe_seed = _safe_seed(seed)
    if safe_seed is None:
        safe_seed = seed_for("pollinations", name, headline or "", safe_width, safe_height).randint(
            1, 2**31 - 1
        )
    line = _safe_text(headline, product["benefits"][0])
    prompt = (
        f"Organic lifestyle social ad photo for {name}. {line}. "
        f"Natural window light, real scene, no text overlay, no logos, no watermark, "
        f"clean product focus, {product['niche_label'].lower()} aesthetic."
    )
    image_url = (
        f"https://image.pollinations.ai/prompt/{quote(prompt, safe='')}"
        f"?width={safe_width}&height={safe_height}&seed={safe_seed}&nologo=true"
    )
    return {
        "agent": "DaVinci",
        "agent_id": "davinci",
        "kind": "organic_ad_draft",
        "provider": "pollinations",
        "provider_tier": "free",
        "model": "pollinations-free-tier",
        "prompt": prompt,
        "image_url": image_url,
        "requested_width": requested_width,
        "requested_height": requested_height,
        "width": safe_width,
        "height": safe_height,
        "max_width": MAX_IMAGE_WIDTH,
        "max_height": MAX_IMAGE_HEIGHT,
        "clamped": (safe_width != requested_width or safe_height != requested_height),
        "seed": safe_seed,
        "organic": True,
        "draft_only": True,
        "published": False,
        "auto_send": False,
        "provider_contacted": False,
        "fetch_mode": "client_on_demand",
        "image_served": False,
        "muse_image": False,
        "presented_as_muse_image": False,
        "disclosure": "Pollinations free-tier organic ad draft. Not Muse Image. Not published. Not served.",
        "requires_human_approval": True,
    }


def receptionist_draft(
    message: str,
    product_name: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Draft a receptionist reply through Aegis. No roster change, nothing sent."""

    base = aegis_chat(message, product_name)
    name = _safe_text(customer_name, "") or None
    return {
        "agent": base["agent"],
        "agent_id": "aegis",
        "kind": "receptionist_draft_reply",
        "role": "receptionist_draft",
        "is_new_agent": False,
        "roster_count": len(AGENT_ROSTER),
        "roster_delta": 0,
        "intent": base["intent"],
        "reply": base["reply"],
        "handoff": base["handoff"],
        "customer_name": name,
        "draft_only": True,
        "auto_send": False,
        "send_status": "not_sent",
        "provider_contacted": False,
        "requires_human_approval": True,
        "note": "Aegis receptionist draft only. No new agent was added and nothing was sent.",
    }


def layout_preview(
    product_name: str,
    product_features: Optional[List[str]] = None,
    product_price: float = 39.0,
    brand_name: Optional[str] = None,
    page: str = "home",
) -> Dict[str, Any]:
    """Return a layout preview only. No rewrite, CMS write, storefront edit, or deploy."""

    name = _safe_text(product_name, "the product")
    product = analyze_product(name, features=product_features, selling_price=product_price)
    blueprint = architect(
        name,
        product_features,
        product_price,
        product["niche"],
        "one_product",
        brand_name,
    )
    sections = [
        {
            "id": "hero",
            "name": "Hero",
            "headline": blueprint["hero_headline"],
            "subhead": blueprint["hero_subhead"],
            "cta": blueprint["cta"],
        },
        {
            "id": "proof",
            "name": "Proof strip",
            "headline": "US warehouse · 30-day returns · 2,400+ verified orders",
        },
        {
            "id": "offer",
            "name": "Offer / PDP",
            "headline": f"{name} at ${blueprint['price']:.2f}",
            "subhead": blueprint["trust"][0],
        },
        {
            "id": "faq",
            "name": "FAQ",
            "headline": blueprint["faq"][0]["q"],
            "subhead": blueprint["faq"][0]["a"],
        },
    ]
    safe_page = _safe_text(page, "home").lower()
    return {
        "agent": "Architect",
        "agent_id": "architect",
        "kind": "layout_preview",
        "page": safe_page,
        "preview_only": True,
        "draft_only": True,
        "auto_rewrite": False,
        "auto_deploy": False,
        "files_written": [],
        "cms_updated": False,
        "provider_contacted": False,
        "deployment": {
            "deployed": False,
            "target": None,
            "requires_human_approval": True,
        },
        "brand_name": blueprint["brand_name"],
        "theme": blueprint["theme"],
        "palette": blueprint["palette"],
        "sections": sections,
        "requires_human_approval": True,
        "note": "Layout preview only. No file, CMS, storefront, or deployment was modified.",
    }


MCP_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "filesystem",
        "name": "Filesystem",
        "transport": "stdio",
        "status": "registered_not_connected",
        "enabled": False,
        "verified": False,
    },
    {
        "id": "supabase",
        "name": "Supabase",
        "transport": "http",
        "status": "registered_not_connected",
        "enabled": False,
        "verified": False,
    },
    {
        "id": "github",
        "name": "GitHub",
        "transport": "http",
        "status": "registered_not_connected",
        "enabled": False,
        "verified": False,
    },
    {
        "id": "playwright",
        "name": "Playwright",
        "transport": "stdio",
        "status": "registered_not_connected",
        "enabled": False,
        "verified": False,
    },
    {
        "id": "memory",
        "name": "Memory",
        "transport": "stdio",
        "status": "registered_not_connected",
        "enabled": False,
        "verified": False,
    },
]


def mcp_registry() -> Dict[str, Any]:
    """Return local MCP registry metadata only. No MCP server is contacted."""

    return {
        "registry": [dict(item) for item in MCP_REGISTRY],
        "count": len(MCP_REGISTRY),
        "server_contacted": False,
        "network_calls": 0,
        "connections": [],
        "draft_only": True,
        "note": "Local registry metadata only. No MCP server was contacted.",
    }
