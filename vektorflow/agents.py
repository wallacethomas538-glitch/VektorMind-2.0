"""The 15 specialized VEKTORFLOW agents."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .intelligence import (
    SUPPLIERS,
    VOICES,
    analyze_product,
    brandify,
    charm_price,
    default_campaigns,
    default_competitors,
    seed_for,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp(agent: str, extra: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "agent": agent,
        "powered_by": "VEKTORFLOW-15",
        "generated_at": _now(),
    }
    payload.update(extra)
    return payload


def hawk(name: str, category: Optional[str] = None, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    p = analyze_product(name, category, keywords)
    bullets = [
        f"{p['features'][0].rstrip('.').capitalize()} — built for {p['audience'].split(',')[0]}",
        f"Solves {p['pain_points'][0]} without looking like a gadget from a clearance bin",
        f"{p['benefits'][1].capitalize()} in the first evening you use it",
        f"Gift-ready: {p['seasonality'].split(',')[0].lower()}",
    ]
    description = (
        f"Meet the {p['name']} — the {p['niche_label'].lower()} piece {p['audience'].split(',')[0]} "
        f"actually keep on the counter. It takes on {p['pain_points'][0]} and replaces it with "
        f"{p['benefits'][0]}. {' '.join(p['keywords'][:3]).strip()}."
    )
    seo_title = f"{p['name']} | {p['benefits'][0].title()} for {p['niche_label']}"
    return _stamp(
        "Hawk",
        {
            "product": p["name"],
            "niche": p["niche_label"],
            "seo_title": seo_title[:70],
            "description": description,
            "bullets": bullets,
            "audience": p["audience"],
            "keywords": p["keywords"],
            "scores": {
                "search": p["search_index"],
                "competition": p["competition"],
                "trend": p["trend"],
                "opportunity": p["opportunity"],
            },
            "verdict": "SCOUT" if p["opportunity"] >= 55 else "WATCH",
            "briefing": (
                f"Opportunity {p['opportunity']}/100 in {p['niche_label']}. "
                f"Trend is {'heating' if p['trend'] >= 55 else 'stable'}; "
                f"competition is {'crowded' if p['competition'] >= 65 else 'beatable'}."
            ),
        },
    )


def smaug(
    product_name: str,
    target_selling_price: Optional[float] = None,
    min_rating: float = 4.0,
    max_shipping_days: int = 21,
) -> Dict[str, Any]:
    p = analyze_product(product_name, selling_price=target_selling_price)
    rng = seed_for("smaug", product_name)
    price = target_selling_price or p["price"]
    matched = []
    for raw in SUPPLIERS:
        unit = round(raw["base_cost"] * rng.uniform(0.85, 1.25) * (p["cost"] / 8.0), 2)
        unit = max(1.4, unit)
        if raw["rating"] < min_rating or raw["shipping_days"] > max_shipping_days:
            continue
        landed = round(unit + (2.1 if "US" in raw["location"] else 1.15), 2)
        net = price * 0.71 - landed
        margin = round((net / price) * 100, 1) if price else 0
        if raw["rating"] >= 4.7 and raw["shipping_days"] <= 7:
            tier = "Gold"
        elif raw["rating"] >= 4.3:
            tier = "Silver"
        else:
            tier = "Bronze"
        matched.append(
            {
                "supplier_name": raw["supplier_name"],
                "price_per_unit": unit,
                "landed_cost": landed,
                "rating": raw["rating"],
                "shipping_days": raw["shipping_days"],
                "min_order_quantity": raw["min_order_quantity"],
                "location": raw["location"],
                "tier": tier,
                "margin": margin,
                "strength": raw["strength"],
                "risk": raw["risk"],
                "first_po": raw["min_order_quantity"] * unit,
                "negotiation": (
                    f"Open at ${max(1.1, unit * 0.88):.2f} on a {raw['min_order_quantity'] * 2}-unit trial. "
                    f"Trade volume for a second QC photo set and polybag branding."
                ),
            }
        )
    matched.sort(key=lambda s: (0 if s["tier"] == "Gold" else 1, -s["margin"]))
    pick = matched[0] if matched else None
    return _stamp(
        "Smaug",
        {
            "product": product_name,
            "target_price": price,
            "suppliers_found": len(matched),
            "top_suppliers": matched[:5],
            "recommended": pick["supplier_name"] if pick else None,
            "negotiation_script": pick["negotiation"] if pick else "Widen rating or shipping filters.",
            "briefing": (
                f"{len(matched)} suppliers cleared the gate. "
                + (
                    f"Lead with {pick['supplier_name']} at ${pick['landed_cost']:.2f} landed, {pick['margin']}% margin."
                    if pick
                    else "No supplier met the constraints."
                )
            ),
        },
    )


def architect(
    product_name: str,
    product_features: Optional[List[str]] = None,
    product_price: float = 39.0,
    niche: Optional[str] = None,
    store_type: str = "one_product",
    brand_name: Optional[str] = None,
) -> Dict[str, Any]:
    p = analyze_product(product_name, niche, features=product_features, selling_price=product_price)
    rng = seed_for("arch", product_name)
    brand = brandify(product_name, rng, brand_name)
    pages = [
        {"page": "Home", "job": "Hero proof + single CTA + 3 objection crushers"},
        {"page": "Shop", "job": f"{store_type.replace('_', ' ').title()} PDP with bundle toggle"},
        {"page": "Story", "job": f"Why {brand} exists, told in 90 words"},
        {"page": "FAQ / Shipping", "job": "Delivery windows, returns, dorm/apartment rules"},
        {"page": "Reviews", "job": "UGC grid + objection-handling quotes"},
    ]
    faq = [
        {"q": f"Is the {p['name']} actually worth ${p['price']:.2f}?", "a": f"Compared with {p['pain_points'][0]}, yes — it pays for itself the first month you stop replacing the cheap version."},
        {"q": "How fast does it ship?", "a": "US warehouse orders leave in 24h and typically land in 3–5 days. Overseas backup stock is 12–18."},
        {"q": "What's the return policy?", "a": "30 days. Photograph the issue, we send a prepaid label. No scavenger hunt."},
        {"q": f"Will it help with {p['pain_points'][1]}?", "a": f"That's the job. {p['benefits'][0].capitalize()} is the default outcome, not a maybe."},
    ]
    return _stamp(
        "Architect",
        {
            "brand_name": brand,
            "product": p["name"],
            "store_type": store_type,
            "theme": p["theme"],
            "palette": {
                "ink": p["colors"][0],
                "accent": p["colors"][1],
                "paper": p["colors"][2],
                "sage": p["colors"][3],
            },
            "hero_headline": f"{p['benefits'][0].capitalize()} — without {p['pain_points'][0]}",
            "hero_subhead": f"The {p['name']} for {p['audience'].split(',')[0]}. Designed to live out, not in a closet.",
            "price": p["price"],
            "cta": "Get yours — ships tomorrow",
            "pages": pages,
            "faq": faq,
            "trust": ["30-day returns", "US warehouse", "2,400+ verified orders", "Secure checkout"],
            "upsells": p["attach"][:3],
            "blueprint_score": 78 + (p["opportunity"] % 18),
            "briefing": f"{brand} is a {store_type.replace('_', ' ')} store on the {p['theme']} system. Hero writes the benefit, not the SKU.",
        },
    )


def davinci(
    product_name: str,
    product_features: Optional[List[str]] = None,
    product_price: float = 39.0,
    creative_type: str = "all",
) -> Dict[str, Any]:
    p = analyze_product(product_name, features=product_features, selling_price=product_price)
    hooks = [
        {"hook_type": "curiosity", "hook_text": f"Nobody tells you this about {p['name'].lower()}s…", "platform": "tiktok", "estimated_hook_rate": "High"},
        {"hook_type": "problem", "hook_text": f"If {p['pain_points'][0]} is ruining your {p['niche_label'].lower()}, watch this.", "platform": "meta", "estimated_hook_rate": "High"},
        {"hook_type": "social_proof", "hook_text": f"12,400 people switched to the {p['name']} this month. Here's why.", "platform": "meta", "estimated_hook_rate": "Medium"},
        {"hook_type": "shock", "hook_text": f"Stop buying the ${int(p['price'] * 2)} version. This ${p['price']:.0f} one does the same job.", "platform": "tiktok", "estimated_hook_rate": "High"},
        {"hook_type": "deal", "hook_text": f"{p['name']} restocked. The bundle disappears Sunday.", "platform": "stories", "estimated_hook_rate": "Medium"},
    ]
    script = [
        f"0–2s  HOOK  {hooks[1]['hook_text']}",
        f"2–6s  PAIN  Show {p['pain_points'][0]} in a real room, no stock footage.",
        f"6–11s DEMO  Hands on the {p['name']}. One feature: {p['features'][0]}.",
        f"11–14s PROOF Overlay a 1-line review. Cut to unboxing.",
        f"14–18s CTA  '{p['name']} — ${p['price']:.2f}. Link in bio, ships tomorrow.'",
    ]
    headlines = [
        f"The {p['niche_label']} upgrade that doesn't look like a gadget",
        f"{p['benefits'][0].capitalize()}. Tonight.",
        f"Built for {p['audience'].split(',')[0]}",
    ]
    return _stamp(
        "DaVinci",
        {
            "product": p["name"],
            "creative_type": creative_type,
            "hook_variations": hooks,
            "video_script": script,
            "headlines": headlines,
            "primary_text": (
                f"Most {p['niche_label'].lower()} products photograph well and live in a drawer. "
                f"The {p['name']} is the opposite — {p['benefits'][0]} the first night, "
                f"and it doesn't punish you for {p['pain_points'][0]}."
            ),
            "ugc_prompt": f"Film a 15s Sunday-reset using the {p['name']}. Natural window light. End on the price.",
            "hashtags": p["hashtags"],
            "briefing": "Five hooks, one 18-second script, three headlines. Shoot the problem hook first.",
        },
    )


def rook(
    campaigns: List[Dict[str, Any]],
    target_roas: float = 2.0,
    total_daily_budget: float = 500.0,
    product_name: Optional[str] = None,
) -> Dict[str, Any]:
    if not campaigns:
        product = analyze_product(product_name or "Candle Warmer Lamp")
        campaigns = default_campaigns(product, total_daily_budget)
    actions = []
    spend = 0.0
    revenue = 0.0
    for c in campaigns:
        spent = float(c.get("spent_today") or 0)
        rev = float(c.get("revenue_today") or 0)
        budget = float(c.get("daily_budget") or 0)
        spend += spent
        revenue += rev
        roas = round(rev / spent, 2) if spent else 0.0
        ctr = round((c.get("clicks") or 0) / max(c.get("impressions") or 1, 1) * 100, 2)
        cpa = round(spent / c["conversions"], 2) if c.get("conversions") else None
        if roas >= max(3.0, target_roas + 1):
            action, new_budget, why = "scale", round(budget * 1.5, 2), "ROAS cleared 3x — press the winner"
        elif roas >= target_roas:
            action, new_budget, why = "scale", round(budget * 1.2, 2), "Above target, scale in 20% steps"
        elif roas < 1.0 and spent > budget * 0.6:
            action, new_budget, why = "kill", 0.0, "Below breakeven after meaningful spend"
        else:
            action, new_budget, why = "maintain", budget, "Inside the learning band — do not touch"
        actions.append(
            {
                "campaign_id": c.get("campaign_id"),
                "platform": c.get("platform"),
                "product_name": c.get("product_name"),
                "roas": roas,
                "ctr": ctr,
                "cpa": cpa,
                "action": action,
                "new_budget": new_budget,
                "reason": why,
                "spent_today": spent,
                "revenue_today": rev,
            }
        )
    blended = round(revenue / spend, 2) if spend else 0.0
    quote = (
        "No mercy. Data doesn't lie."
        if any(a["action"] == "kill" for a in actions)
        else "Winners get oxygen. Losers get silence."
    )
    return _stamp(
        "Rook",
        {
            "target_roas": target_roas,
            "blended_roas": blended,
            "spend_today": round(spend, 2),
            "revenue_today": round(revenue, 2),
            "campaign_actions": actions,
            "reallocated_budget": round(sum(a["new_budget"] for a in actions), 2),
            "rook_quote": quote,
            "briefing": f"Blended ROAS {blended:.2f}x on ${spend:.0f}. {sum(1 for a in actions if a['action']=='kill')} killed, {sum(1 for a in actions if a['action']=='scale')} scaled.",
        },
    )


def aegis_chat(message: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    text = message.lower()
    product = product_name or "your order"
    if any(w in text for w in ("refund", "return", "broken", "damaged", "cracked")):
        intent, reply = "returns", "Sorry — that’s on us. Photograph the issue, I’ll send a prepaid label and a replacement goes out before the return even lands. 30-day window, no scavenger hunt."
    elif any(w in text for w in ("where", "track", "shipping", "arrive", "delivery")):
        intent, reply = "shipping", f"Your {product} leaves the US warehouse within 24h. Most customers see a scan the same afternoon and a doorstep in 3–5 days. Drop your order number and I’ll pull the exact scan."
    elif any(w in text for w in ("discount", "coupon", "code", "sale")):
        intent, reply = "promo", "I can apply WELCOME10 on this chat — 10% off if you check out in the next hour. Want me to send the cart link?"
    elif any(w in text for w in ("how", "work", "use", "setup")):
        intent, reply = "product", f"Setup is two minutes. Unbox, place the {product} on a stable surface, and you’re done — no app required. I’ll email the one-page guide."
    else:
        intent, reply = "general", f"I’m here. Tell me whether this is about shipping, a return, or how the {product} works and I’ll handle it in one reply."
    return _stamp("Aegis", {"intent": intent, "reply": reply, "handoff": intent in {"returns"}, "briefing": f"Classified as {intent}."})


def aegis_review(review_text: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    text = review_text.lower()
    pos = ("love", "great", "amazing", "perfect", "works", "beautiful", "fast", "quality", "recommend")
    neg = ("broke", "cheap", "slow", "hate", "scam", "refund", "worst", "damaged", "late", "flimsy")
    p_hits = [w for w in pos if w in text]
    n_hits = [w for w in neg if w in text]
    score = (len(p_hits) - len(n_hits) * 1.4)
    if score >= 1:
        sentiment, conf = "POSITIVE", 0.72 + min(0.23, len(p_hits) * 0.06)
    elif score <= -1:
        sentiment, conf = "NEGATIVE", 0.7 + min(0.25, len(n_hits) * 0.06)
    else:
        sentiment, conf = "NEUTRAL", 0.58
    themes = []
    if any(w in text for w in ("ship", "late", "arrive", "delivery")):
        themes.append("shipping")
    if any(w in text for w in ("quality", "broke", "flimsy", "cheap", "solid")):
        themes.append("build")
    if any(w in text for w in ("value", "price", "expensive", "worth")):
        themes.append("value")
    if not themes:
        themes = ["overall"]
    reply = {
        "POSITIVE": "Thank you — notes like this are why we obsess over the unboxing. Mind if we quote you?",
        "NEGATIVE": "This isn’t the standard. I’m escalating to Aegis and we’ll make it right today — replacement or refund, your call.",
        "NEUTRAL": "Appreciate the honest note. If anything’s missing from the experience, reply here and I’ll fix it.",
    }[sentiment]
    return _stamp(
        "Aegis",
        {
            "sentiment": sentiment,
            "confidence": round(conf, 2),
            "themes": themes,
            "signals": {"positive": p_hits, "negative": n_hits},
            "suggested_reply": reply,
            "product": product_name,
            "briefing": f"{sentiment.title()} ({conf:.0%}) · themes: {', '.join(themes)}",
        },
    )


def aegis_cart(product_name: str, user_name: str = "Customer", cart_value: Optional[float] = None) -> Dict[str, Any]:
    p = analyze_product(product_name, selling_price=cart_value)
    value = cart_value or p["price"]
    sequence = [
        {
            "hour": 1,
            "subject": f"{user_name.split()[0]}, your {product_name} is still in the bag",
            "preview": "I held the US-warehouse unit. It ships tomorrow if you want it.",
        },
        {
            "hour": 22,
            "subject": f"A 10% nudge for the {product_name}",
            "preview": f"COMEBACK10 takes it to ${value * 0.9:.2f}. Expires tonight.",
        },
        {
            "hour": 70,
            "subject": "Last call — then it goes back to the floor",
            "preview": f"People buy the {product_name} for {p['benefits'][0]}. Don’t overthink it.",
        },
    ]
    return _stamp(
        "Aegis",
        {
            "product": product_name,
            "user_name": user_name,
            "cart_value": value,
            "email_subject": sequence[0]["subject"],
            "email_body": (
                f"Hey {user_name.split()[0]},\n\n"
                f"You were one click from the {product_name}. I checked — the US warehouse still has your unit, "
                f"and it can leave tomorrow. {p['benefits'][0].capitalize()} the first night.\n\n"
                f"Finish the order →\n— Aegis, {p.get('brand', 'the shop')}"
            ),
            "sequence": sequence,
            "expected_recovery": "12–18% of abandoned carts",
            "briefing": "3-email drip: hold, discount, last call.",
        },
    )


def arbiter(
    product_name: str,
    product_cost: float,
    shipping_cost: float = 0,
    competitors: Optional[List[Dict[str, Any]]] = None,
    demand_signal: str = "normal",
) -> Dict[str, Any]:
    p = analyze_product(product_name, product_cost=product_cost)
    comps = competitors or default_competitors(p)
    landed = product_cost + shipping_cost
    floor = charm_price(landed / 0.42)
    landed_prices = [c["price"] + c.get("shipping", 0) for c in comps]
    mid = sum(landed_prices) / len(landed_prices)
    low, high = min(landed_prices), max(landed_prices)
    demand = {"low": -0.06, "normal": 0.0, "high": 0.07, "viral": 0.12}.get(demand_signal, 0.0)
    suggested = charm_price(max(floor, mid * (1 + demand) * 0.97))
    return _stamp(
        "Arbiter",
        {
            "product": product_name,
            "floor_price": floor,
            "suggested_price": suggested,
            "premium_price": charm_price(suggested * 1.18),
            "unit_economics": {
                "cogs": product_cost,
                "shipping": shipping_cost,
                "landed": round(landed, 2),
                "gross_margin_pct": round(((suggested - landed) / suggested) * 100, 1),
            },
            "market": {"low": round(low, 2), "mid": round(mid, 2), "high": round(high, 2)},
            "competitors": comps,
            "demand_signal": demand_signal,
            "rationale": (
                f"Floor is ${floor:.2f} to hold a 58% gross. Market midpoint is ${mid:.2f}. "
                f"Demand '{demand_signal}' shifts us to ${suggested:.2f} — under the premium cluster, above race-to-bottom."
            ),
            "briefing": f"Price at ${suggested:.2f}. Floor ${floor:.2f}. Do not go below it.",
        },
    )


def sentinel(
    store_name: str,
    store_url: str,
    data_collection: Optional[List[str]] = None,
    region: str = "US-EU",
) -> Dict[str, Any]:
    collected = data_collection or ["email", "shipping_address"]
    flags = []
    score = 94
    if "payment" in collected or "card" in collected:
        flags.append("Never store raw card data — use the processor’s vault.")
        score -= 6
    if "email" in collected and "sms" in collected:
        flags.append("Dual-channel marketing needs a separate, unticked consent.")
        score -= 4
    if "eu" in region.lower() and "ip" in collected:
        flags.append("IP + device fingerprint is personal data under GDPR.")
        score -= 5
    checklist = [
        {"item": "Privacy policy linked in footer and checkout", "status": "required"},
        {"item": "Cookie banner with reject-all equal prominence", "status": "required" if "eu" in region.lower() else "recommended"},
        {"item": "CCPA Do-Not-Sell link for California traffic", "status": "required"},
        {"item": "Plain-language returns + shipping times", "status": "required"},
        {"item": "Data processing addendum with email vendor", "status": "recommended"},
        {"item": f"Retention limit published for: {', '.join(collected)}", "status": "required"},
    ]
    policy = (
        f"{store_name} ({store_url}) collects {', '.join(collected)} to fulfill orders and, only with consent, "
        f"to send product updates. We do not sell personal information. EU visitors may request access, correction, "
        f"or deletion at privacy@{store_url.replace('https://', '').replace('http://', '').split('/')[0]}. "
        f"California residents may opt out via the Do Not Sell link."
    )
    return _stamp(
        "Sentinel",
        {
            "store": store_name,
            "store_url": store_url,
            "region": region,
            "compliance_score": max(60, score),
            "status": "Compliant" if score >= 85 else "Needs work",
            "data_collection": collected,
            "flags": flags or ["No critical gaps in the declared collection set."],
            "checklist": checklist,
            "policy_excerpt": policy,
            "briefing": f"Score {max(60, score)}/100 for {store_name}. {len(flags)} flag(s).",
        },
    )


def echo(text: str, voice_name: str = "Kore", product_name: Optional[str] = None) -> Dict[str, Any]:
    voice = VOICES.get(voice_name, VOICES["Kore"])
    words = len(re.findall(r"\w+", text))
    seconds = round(max(3.0, words / 2.4), 1)
    cleaned = re.sub(r"\s+", " ", text).strip()
    if seconds > 20:
        note = "Trim to 15–18s for paid social. Front-load the hook."
    elif seconds < 8:
        note = "Short enough for a bumper. Pair with a hard visual in frame one."
    else:
        note = "Right inside the sweet spot for Reels and TikTok."
    return _stamp(
        "Echo",
        {
            "voice": voice_name,
            "voice_profile": voice,
            "text": cleaned,
            "text_preview": cleaned[:140] + ("…" if len(cleaned) > 140 else ""),
            "word_count": words,
            "estimated_seconds": seconds,
            "note": note,
            "ssml_hint": f'<speak><prosody rate="{voice["pace"]}">{cleaned}</prosody></speak>',
            "product": product_name,
            "briefing": f"{voice_name} · {seconds}s · {note}",
        },
    )


def echo_presets() -> Dict[str, Any]:
    return _stamp(
        "Echo",
        {
            "presets": [
                {"id": "cozy_warmth", "voice": "Kore", "pitch": -1, "rate": "unhurried"},
                {"id": "dynamic_pitch", "voice": "Puck", "pitch": 2, "rate": "punchy"},
                {"id": "mellow_serene", "voice": "Zephyr", "pitch": -2, "rate": "soft"},
                {"id": "field_report", "voice": "Charon", "pitch": -3, "rate": "measured"},
                {"id": "drive", "voice": "Fenrir", "pitch": -1, "rate": "driven"},
            ],
            "voices": VOICES,
        },
    )


def cerebrum(dossier: Dict[str, Any]) -> Dict[str, Any]:
    hawk_s = dossier.get("hawk", {}).get("scores", {})
    oracle = dossier.get("oracle", {})
    smaug = dossier.get("smaug", {})
    rook_d = dossier.get("rook", {})
    sentinel_d = dossier.get("sentinel", {})
    opp = hawk_s.get("opportunity", 50)
    rec = oracle.get("recommendation", "ITERATE")
    margin = (smaug.get("top_suppliers") or [{}])[0].get("margin", 0)
    rec_weight = {"LAUNCH": 80, "ITERATE": 44, "THIN": 16}.get(rec, 44)
    score = int(
        max(
            5,
            min(99, opp * 0.34 + rec_weight * 0.40 + min(max(margin, 0), 55) * 0.26),
        )
    )
    if rec == "LAUNCH" and score >= 58:
        verdict = "LAUNCH"
        posture = "Green-light a 14-day test. Cap spend at the planned daily budget until Rook sees 2.0x."
    elif rec == "THIN" or score < 42:
        verdict = "KILL"
        posture = "Do not buy traffic. Rebuild offer, price, or supplier before another dollar."
    else:
        verdict = "ITERATE"
        posture = "Fix the weakest agent note, then run a $30/day creative test — not a full launch."
    priorities = [
        dossier.get("hawk", {}).get("briefing"),
        dossier.get("smaug", {}).get("briefing"),
        dossier.get("rook", {}).get("briefing"),
        dossier.get("oracle", {}).get("briefing"),
    ]
    return _stamp(
        "Cerebrum",
        {
            "verdict": verdict,
            "conviction": score,
            "posture": posture,
            "priorities": [p for p in priorities if p][:4],
            "compliance": sentinel_d.get("compliance_score"),
            "blended_roas": rook_d.get("blended_roas"),
            "quote": "Fifteen minds. One decision.",
            "briefing": f"{verdict} · conviction {score}. {posture}",
        },
    )


def viral(product_name: str, platforms: Optional[List[str]] = None) -> Dict[str, Any]:
    p = analyze_product(product_name)
    rng = seed_for("viral", product_name)
    plats = platforms or ["tiktok", "instagram", "youtube"]
    signals = {}
    total = 0
    for plat in plats:
        velocity = rng.randint(40, 520)
        total += velocity
        if velocity > 360:
            state = "SURGING"
        elif velocity > 180:
            state = "RISING"
        else:
            state = "QUIET"
        signals[plat] = {
            "velocity": velocity,
            "trending": state,
            "format": p["creators"][0],
            "sample_sound": rng.choice(["original audio", "trending stitch", "voiceover"]),
        }
    if total > 700:
        action = "LAUNCH NOW"
    elif total > 380:
        action = "ACCELERATE"
    else:
        action = "MONITOR"
    return _stamp(
        "ViralDet",
        {
            "product": product_name,
            "signals": signals,
            "total_velocity": total,
            "action": action,
            "hashtags": p["hashtags"],
            "creator_fits": p["creators"],
            "window": "48–72 hours if SURGING, else a 7-day watch",
            "briefing": f"{action} · velocity {total} across {', '.join(plats)}.",
        },
    )


def shadow(competitor_url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    host = urlparse(competitor_url if "://" in competitor_url else f"https://{competitor_url}").netloc or competitor_url
    host = host.replace("www.", "")
    p = analyze_product(product_name or host.split(".")[0].replace("-", " "))
    rng = seed_for("shadow", host)
    bestsellers = [
        {"name": f"{p['name']} — Core", "price": p["price"], "reviews": 400 + rng.randint(0, 1800)},
        {"name": f"{p['name']} Mini", "price": charm_price(p["price"] * 0.72), "reviews": 120 + rng.randint(0, 400)},
        {"name": f"{p['attach'][0].title()} Add-on", "price": charm_price(p["price"] * 0.28), "reviews": 80 + rng.randint(0, 220)},
    ]
    hooks = [
        f"We fixed {p['weaknesses'][0]}",
        f"The ${int(p['price'] * 2)} look for ${p['price']:.0f}",
        f"Seen on {p['creators'][0]}",
        "Ships from the US — not a 3-week wait",
    ]
    return _stamp(
        "Shadow",
        {
            "competitor": host,
            "competitor_url": competitor_url,
            "positioning": f"Premium-looking {p['niche_label'].lower()} at mid-market prices",
            "intel": {
                "best_sellers": bestsellers,
                "ad_hooks": hooks,
                "avg_review": round(3.9 + rng.random() * 0.8, 2),
                "traffic_mix": {"paid": 0.46, "organic": 0.33, "social": 0.21},
                "weak_spot": p["weaknesses"][0],
            },
            "actions": [
                f"Counter-hook their '{hooks[0]}' with a side-by-side demo",
                "Undercut the Mini by 5% and win the comparison table",
                "Run US-warehouse as the primary trust badge — they hide shipping times",
            ],
            "briefing": f"{host} leans on '{hooks[0]}'. Their exposed flank is {p['weaknesses'][0]}.",
        },
    )


def bundler(main_product: str, budget: float = 45.0, product_cost: Optional[float] = None) -> Dict[str, Any]:
    p = analyze_product(main_product, selling_price=budget, product_cost=product_cost)
    cost = product_cost or p["cost"]
    tiers = [
        {
            "name": f"Starter {p['name']}",
            "includes": [p["name"]],
            "price": charm_price(budget),
            "cost": round(cost, 2),
        },
        {
            "name": f"{p['name']} Kit",
            "includes": [p["name"], p["attach"][0], p["attach"][1]],
            "price": charm_price(budget * 1.35),
            "cost": round(cost + 3.4, 2),
        },
        {
            "name": f"Deluxe {p['name']} Bundle",
            "includes": [p["name"], *p["attach"][:3]],
            "price": charm_price(budget * 1.8),
            "cost": round(cost + 6.1, 2),
        },
    ]
    for t in tiers:
        t["margin_pct"] = round(((t["price"] - t["cost"]) / t["price"]) * 100, 1)
        t["aov_lift"] = round(((t["price"] / budget) - 1) * 100, 1)
    return _stamp(
        "Bundler",
        {
            "product": main_product,
            "bundles": tiers,
            "recommended": tiers[1]["name"],
            "play": "Default the PDP to the Kit. Let the Deluxe sit as the anchor. Starter exists so nobody bounces.",
            "briefing": f"Kit lifts AOV {tiers[1]['aov_lift']}% at {tiers[1]['margin_pct']}% margin. Make it the default.",
        },
    )


def pivot(competitor_product_url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    host = competitor_product_url
    p = analyze_product(product_name or "Hero product")
    angles = [
        {"weakness": p["weaknesses"][0], "headline": f"Tired of {p['weaknesses'][0]}?", "body": f"We rebuilt the {p['name']} around the #1 complaint on {host}."},
        {"weakness": p["weaknesses"][1], "headline": f"Hate {p['weaknesses'][1]}?", "body": "Say it in the first two seconds. Then show the fix in-hand."},
        {"weakness": p["weaknesses"][2], "headline": f"If '{p['weaknesses'][2]}' showed up in your last order…", "body": "This is the positioning. Their one-star is your brief."},
    ]
    return _stamp(
        "Pivot",
        {
            "source": competitor_product_url,
            "product": p["name"],
            "weaknesses": p["weaknesses"],
            "ad_angles": [a["headline"] for a in angles],
            "matrix": angles,
            "positioning": f"The {p['name']} for people who already bought the cheap one and regretted it.",
            "briefing": f"Lead with '{p['weaknesses'][0]}' — it is the loudest review cluster.",
        },
    )


def oracle(
    product_cost: float,
    selling_price: float,
    ad_budget: float,
    niche: str = "general",
    product_name: Optional[str] = None,
) -> Dict[str, Any]:
    p = analyze_product(product_name or "Offer", category=niche, selling_price=selling_price, product_cost=product_cost)
    contribution = selling_price - product_cost - 1.1  # fees
    cac = p["cac"]
    daily_orders_base = max(1.0, ad_budget / max(cac, 6))
    def scenario(mult: float) -> Dict[str, Any]:
        orders = daily_orders_base * mult
        rev = orders * selling_price
        ad = ad_budget
        cogs = orders * product_cost
        fees = orders * 1.1
        profit = rev - ad - cogs - fees
        return {
            "daily_orders": round(orders, 1),
            "daily_revenue": round(rev, 2),
            "daily_profit": round(profit, 2),
            "day30_profit": round(profit * 30, 2),
            "day30_revenue": round(rev * 30, 2),
        }

    conservative = scenario(0.7)
    base = scenario(1.0)
    optimistic = scenario(1.45)
    be_orders = ad_budget / max(contribution, 0.5)
    be_day = int(min(30, max(1, round(be_orders / max(daily_orders_base, 0.1)))))
    if contribution > product_cost * 1.6 and base["day30_profit"] > ad_budget * 8:
        rec = "LAUNCH"
    elif base["day30_profit"] > 0:
        rec = "ITERATE"
    else:
        rec = "THIN"
    series = []
    running = 0.0
    rng = seed_for("oracle", product_name or "", selling_price, ad_budget)
    for d in range(1, 31):
        noise = rng.uniform(0.82, 1.18)
        running += base["daily_profit"] * noise
        series.append({"day": d, "profit": round(running, 2)})
    return _stamp(
        "Oracle",
        {
            "product": p["name"],
            "niche": p["niche_label"],
            "inputs": {
                "product_cost": product_cost,
                "selling_price": selling_price,
                "ad_budget": ad_budget,
                "contribution": round(contribution, 2),
                "assumed_cac": cac,
            },
            "conservative_30day": conservative["day30_profit"],
            "base_30day": base["day30_profit"],
            "optimistic_30day": optimistic["day30_profit"],
            "scenarios": {"conservative": conservative, "base": base, "optimistic": optimistic},
            "break_even_day": be_day,
            "recommendation": rec,
            "series": series,
            "briefing": f"{rec}: 30-day base ${base['day30_profit']:.0f}. Break-even around day {be_day}.",
        },
    )


def forecast(historical_sales: List[int], product_name: Optional[str] = None) -> Dict[str, Any]:
    window = historical_sales[-7:] if historical_sales else [0]
    avg = sum(window) / max(len(window), 1)
    rng = seed_for("fc", tuple(historical_sales[-14:]), product_name or "")
    nxt = []
    for i in range(7):
        seasonal = 1 + 0.08 * (1 if i in (4, 5) else -0.15)
        nxt.append(max(0, int(round(avg * seasonal * rng.uniform(0.9, 1.12)))))
    return _stamp(
        "Oracle",
        {
            "product": product_name,
            "trailing_avg": round(avg, 2),
            "next_7_days": nxt,
            "next_7_total": sum(nxt),
            "briefing": f"Next 7 days ~ {sum(nxt)} units (avg {avg:.1f}/day).",
        },
    )


def price_optimize(product_id: str, current_price: float, competitor_price: Optional[float] = None) -> Dict[str, Any]:
    if competitor_price:
        rec = charm_price(competitor_price * 0.97)
        why = "Sit a hair under the named competitor without looking cheap."
    else:
        rec = charm_price(current_price)
        why = "No competitor feed — hold charm pricing and wait for Arbiter."
    return _stamp(
        "Arbiter",
        {
            "product_id": product_id,
            "current_price": current_price,
            "recommended_price": rec,
            "rationale": why,
            "briefing": f"Move {product_id} to ${rec:.2f}.",
        },
    )


def run_mission(req: Dict[str, Any]) -> Dict[str, Any]:
    name = req["product_name"]
    features = req.get("features") or []
    keywords = req.get("keywords") or []
    price = float(req.get("selling_price") or 39)
    cost = req.get("product_cost")
    p = analyze_product(name, req.get("category"), keywords, features, price, cost)
    cost = float(cost if cost is not None else p["cost"])
    ship = float(req.get("shipping_cost") or p["shipping"])
    budget = float(req.get("ad_budget") or 100)
    brand = req.get("brand_name")
    store = req.get("store_name") or brandify(name, seed_for("store", name), brand)
    url = req.get("store_url") or f"{p['slug']}.store"
    platforms = req.get("platforms") or ["tiktok", "instagram", "meta"]
    competitor = req.get("competitor_url") or "https://competitor.store"

    hawk_d = hawk(name, req.get("category"), keywords)
    smaug_d = smaug(name, price)
    arch_d = architect(name, features, price, req.get("category"), "one_product", brand)
    davinci_d = davinci(name, features, price)
    campaigns = default_campaigns(p, budget)
    rook_d = rook(campaigns, 2.0, budget, name)
    aegis_d = {
        "chat": aegis_chat(f"Where is my {name}?", name),
        "review": aegis_review(f"Love the {name}, great quality and fast shipping", name),
        "cart": aegis_cart(name, "Jordan", price),
    }
    arbiter_d = arbiter(name, cost, ship, None, "normal")
    sentinel_d = sentinel(store, url)
    script = davinci_d["video_script"][0].split("  ", 1)[-1] if davinci_d.get("video_script") else f"Meet the {name}."
    echo_d = echo(f"{arch_d['hero_headline']}. {script}", "Kore", name)
    viral_d = viral(name, platforms)
    shadow_d = shadow(competitor, name)
    bundler_d = bundler(name, price, cost)
    pivot_d = pivot(competitor, name)
    oracle_d = oracle(cost, price, budget, p["niche"], name)
    dossier = {
        "hawk": hawk_d,
        "smaug": smaug_d,
        "architect": arch_d,
        "davinci": davinci_d,
        "rook": rook_d,
        "aegis": aegis_d,
        "arbiter": arbiter_d,
        "sentinel": sentinel_d,
        "echo": echo_d,
        "viral": viral_d,
        "shadow": shadow_d,
        "bundler": bundler_d,
        "pivot": pivot_d,
        "oracle": oracle_d,
    }
    cerebrum_d = cerebrum({**dossier, "oracle": oracle_d, "hawk": hawk_d, "smaug": smaug_d, "rook": rook_d, "sentinel": sentinel_d})
    dossier["cerebrum"] = cerebrum_d
    return _stamp(
        "Cerebrum",
        {
            "mission_id": f"VF-{p['seed']}",
            "product": p,
            "verdict": cerebrum_d["verdict"],
            "conviction": cerebrum_d["conviction"],
            "agents": dossier,
            "briefing": cerebrum_d["briefing"],
        },
    )


AGENT_ROSTER = [
    {"id": "hawk", "name": "Hawk", "glyph": "01", "role": "Product scout", "quote": "I see the product before the market does.", "endpoint": "/api/v1/product-description"},
    {"id": "smaug", "name": "Smaug", "glyph": "02", "role": "Supplier whisperer", "quote": "Every supplier has a number. I find it.", "endpoint": "/api/v1/supplier-finder"},
    {"id": "architect", "name": "Architect", "glyph": "03", "role": "Store builder", "quote": "A store is a machine for converting attention into orders.", "endpoint": "/api/v1/store-builder"},
    {"id": "davinci", "name": "DaVinci", "glyph": "04", "role": "Creative factory", "quote": "The hook is the product. The product is the proof.", "endpoint": "/api/v1/creative-factory"},
    {"id": "rook", "name": "Rook", "glyph": "05", "role": "Media buyer", "quote": "No mercy. Data doesn't lie.", "endpoint": "/api/v1/ad-manager"},
    {"id": "aegis", "name": "Aegis", "glyph": "06", "role": "Support sorcerer", "quote": "A saved customer is cheaper than a new one.", "endpoint": "/api/v1/chatbot"},
    {"id": "arbiter", "name": "Arbiter", "glyph": "07", "role": "Dynamic pricing", "quote": "Price is a story. I write the ending.", "endpoint": "/api/v1/dynamic-pricing"},
    {"id": "sentinel", "name": "Sentinel", "glyph": "08", "role": "Compliance", "quote": "If it isn't compliant, it isn't a business.", "endpoint": "/api/v1/compliance-audit"},
    {"id": "echo", "name": "Echo", "glyph": "09", "role": "Voice synthesis", "quote": "Voice is the shortest path to trust.", "endpoint": "/api/v1/tts/synthesize"},
    {"id": "cerebrum", "name": "Cerebrum", "glyph": "10", "role": "Central command", "quote": "Fifteen minds. One decision.", "endpoint": "/api/v1/mission"},
    {"id": "viral", "name": "ViralDet", "glyph": "11", "role": "Viral detector", "quote": "Virality is a velocity, not a vibe.", "endpoint": "/api/v1/viral-detector"},
    {"id": "shadow", "name": "Shadow", "glyph": "12", "role": "Competitor intel", "quote": "Your competitor already ran the test. I stole the answers.", "endpoint": "/api/v1/competitor-shadow"},
    {"id": "bundler", "name": "Bundler", "glyph": "13", "role": "Bundle builder", "quote": "The second item is where margin lives.", "endpoint": "/api/v1/bundle-builder"},
    {"id": "pivot", "name": "Pivot", "glyph": "14", "role": "Sentiment pivot", "quote": "Their one-star review is your headline.", "endpoint": "/api/v1/sentiment-pivot"},
    {"id": "oracle", "name": "Oracle", "glyph": "15", "role": "Profit predictor", "quote": "Thirty days from now is already visible.", "endpoint": "/api/v1/profit-predictor"},
]
