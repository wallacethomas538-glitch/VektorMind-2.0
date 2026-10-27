"""Deterministic product intelligence shared by every agent."""

from __future__ import annotations

import hashlib
import math
import random
import re
from typing import Any, Dict, List, Optional, Sequence


NICHES: Dict[str, Dict[str, Any]] = {
    "home": {
        "label": "Home & Decor",
        "audience": "apartment dwellers, gift shoppers, and wellness-minded adults 24–42",
        "pain": ["open-flame restrictions", "cluttered nightstands", "cheap-looking decor"],
        "benefits": ["instant ambiance", "safer than candles", "gift-ready unboxing"],
        "attach": ["replacement bulbs", "scented wax melts", "linen spray", "gift box"],
        "creators": ["apartment tour", "Sunday reset", "dorm room", "cozy night-in"],
        "hashtags": ["#cozyhome", "#sundayreset", "#dormsafe", "#giftguide"],
        "seasonality": "Q4 gifting spike, steady wellness demand year-round",
        "price_band": (29.0, 59.0),
        "cogs": (7.5, 14.0),
        "cac": 11.0,
        "colors": ["#1b2430", "#c4a574", "#f3efe6", "#8a9a7b"],
        "theme": "Dawn",
        "weaknesses": ["bulb burns out fast", "base feels cheap", "scent throw is weak"],
    },
    "beauty": {
        "label": "Beauty & Personal Care",
        "audience": "routine-driven women and beauty-curious men 18–35",
        "pain": ["complicated 12-step routines", "irritated skin", "products that ghost after a week"],
        "benefits": ["visible results fast", "clean-feeling formula", "travel-friendly ritual"],
        "attach": ["travel pouch", "jade roller", "refill pods", "silk scrunchie"],
        "creators": ["GRWM", "skin cycling", "dupe review", "morning routine"],
        "hashtags": ["#skintok", "#grwm", "#cleangirl", "#dupealert"],
        "seasonality": "January reset + summer glow peaks",
        "price_band": (18.0, 48.0),
        "cogs": (3.5, 9.0),
        "cac": 14.0,
        "colors": ["#2a1f24", "#e8c4c4", "#f7f1ea", "#7d5a50"],
        "theme": "Sense",
        "weaknesses": ["broke me out", "scent too strong", "tiny amount for the price"],
    },
    "fitness": {
        "label": "Fitness & Recovery",
        "audience": "home-gym regulars and comeback athletes 22–40",
        "pain": ["skipped workouts", "sore joints", "gear that looks like a toy"],
        "benefits": ["recover faster", "train at home", "looks serious on camera"],
        "attach": ["resistance bands", "sweat towel", "bottle", "carry sling"],
        "creators": ["garage gym", "mobility", "75 hard", "desk-to-deadlift"],
        "hashtags": ["#homegym", "#mobilitytok", "#trainathome", "#recovery"],
        "seasonality": "January and September resolution waves",
        "price_band": (24.0, 79.0),
        "cogs": (8.0, 22.0),
        "cac": 16.0,
        "colors": ["#101214", "#e23d28", "#f4f4f0", "#8d99ae"],
        "theme": "Refresh",
        "weaknesses": ["quality control", "instructions unclear", "smells like rubber"],
    },
    "pet": {
        "label": "Pet Lifestyle",
        "audience": "millennial pet parents who buy for the animal first",
        "pain": ["destroyed furniture", "anxious pets", "ugly plastic gear"],
        "benefits": ["calmer pet", "cleaner home", "looks designed, not pet-store"],
        "attach": ["treat pouch", "waste bags", "name tag", "travel bowl"],
        "creators": ["dog morning", "cat enrichment", "rescue glow-up"],
        "hashtags": ["#dogtok", "#catsofinstagram", "#petparent", "#rescuedog"],
        "seasonality": "holiday pet gifting + spring adoption surge",
        "price_band": (16.0, 54.0),
        "cogs": (4.0, 13.0),
        "cac": 10.0,
        "colors": ["#1c1914", "#d9a066", "#efe6d6", "#4a6741"],
        "theme": "Dawn",
        "weaknesses": ["chewed through in a day", "sizing runs small", "hard to clean"],
    },
    "kitchen": {
        "label": "Kitchen & Dining",
        "audience": "home cooks who want restaurant results without chef tools",
        "pain": ["unitaskers that clutter drawers", "uneven heat", "hard cleanup"],
        "benefits": ["one tool, many meals", "weeknight speed", "counter-worthy design"],
        "attach": ["recipe card deck", "oil brush", "storage lid", "apron"],
        "creators": ["sunday meal prep", "tiny kitchen", "what I eat in a day"],
        "hashtags": ["#kitchentok", "#mealprep", "#weeknightdinner", "#gadgetreview"],
        "seasonality": "Q4 + Super Bowl + grilling season",
        "price_band": (22.0, 69.0),
        "cogs": (6.0, 18.0),
        "cac": 12.0,
        "colors": ["#16120e", "#c45c26", "#f6efe4", "#5c6b4a"],
        "theme": "Sense",
        "weaknesses": ["nonstick peeled", "too loud", "doesn't fit in drawers"],
    },
    "tech": {
        "label": "Consumer Tech",
        "audience": "early adopters and desk-setup maximalists 20–38",
        "pain": ["cable chaos", "short battery", "plastic that yellows"],
        "benefits": ["desk-aesthetic approved", "all-day battery", "works out of the box"],
        "attach": ["carry case", "extra cable", "desk mat", "mount"],
        "creators": ["desk setup", "edc", "one week later", "vs the expensive one"],
        "hashtags": ["#desksetup", "#edc", "#techfinds", "#gadgettok"],
        "seasonality": "Prime-style event weeks + back to school",
        "price_band": (19.0, 89.0),
        "cogs": (5.5, 24.0),
        "cac": 18.0,
        "colors": ["#0d1117", "#3ee0c5", "#e8edf5", "#6c7a89"],
        "theme": "Refresh",
        "weaknesses": ["battery dies quick", "app is janky", "overheats"],
    },
    "fashion": {
        "label": "Fashion & Accessories",
        "audience": "style-fluent shoppers hunting an everyday signature piece",
        "pain": ["fast fashion that pills", "one-season trends", "sizing lottery"],
        "benefits": ["looks expensive on camera", "true-to-size", "outfits itself"],
        "attach": ["care kit", "dust bag", "extra strap", "styling guide"],
        "creators": ["fit check", "get ready with me", "quiet luxury"],
        "hashtags": ["#fitcheck", "#quietluxury", "#outfitinspo", "#capsulewardrobe"],
        "seasonality": "drop culture — new colorways every 6–8 weeks",
        "price_band": (28.0, 98.0),
        "cogs": (7.0, 22.0),
        "cac": 15.0,
        "colors": ["#14110f", "#b08d57", "#f4efe6", "#3d3229"],
        "theme": "Dawn",
        "weaknesses": ["runs small", "hardware tarnished", "looks cheaper in person"],
    },
    "outdoor": {
        "label": "Outdoor & Travel",
        "audience": "weekend hikers and carry-on-only travelers",
        "pain": ["gear that fails on trip one", "overpacked bags", "fair-weather tools"],
        "benefits": ["packs flat", "weather-proof enough", "looks field-tested"],
        "attach": ["stuff sack", "carabiner", "repair patch", "packing cube"],
        "creators": ["one bag travel", "trail day", "van life kitchen"],
        "hashtags": ["#onebag", "#trailtok", "#vanlife", "#everydaycarry"],
        "seasonality": "April–September peak, holiday travel bump",
        "price_band": (24.0, 84.0),
        "cogs": (7.0, 21.0),
        "cac": 13.0,
        "colors": ["#12160f", "#c4a35a", "#e7e2d6", "#3f5a46"],
        "theme": "Refresh",
        "weaknesses": ["zipper failed", "not as waterproof as claimed", "too bulky"],
    },
    "baby": {
        "label": "Baby & Parent",
        "audience": "first-time parents who research everything twice",
        "pain": ["unsafe-feeling products", "3 a.m. fumbles", "stuff that outgrows in weeks"],
        "benefits": ["one-handed use", "easy to sanitize", "grows with the child"],
        "attach": ["spare lid", "travel pouch", "backup bibs", "guide booklet"],
        "creators": ["newborn week", "registry must-haves", "realistic mom"],
        "hashtags": ["#newborn", "#registry", "#momtok", "#babymusthave"],
        "seasonality": "Q4 gifting + spring baby-shower season",
        "price_band": (18.0, 64.0),
        "cogs": (4.5, 16.0),
        "cac": 17.0,
        "colors": ["#1a1714", "#d7b8a3", "#f7f1ea", "#8b9a86"],
        "theme": "Sense",
        "weaknesses": ["hard to clean", "woke the baby", "broke after two washes"],
    },
    "office": {
        "label": "Work & Productivity",
        "audience": "remote workers optimizing a 10-hour desk day",
        "pain": ["afternoon crash", "ugly WFH setup", "tools that fight focus"],
        "benefits": ["noticeable comfort", "looks like a grown-up office", "quiet"],
        "attach": ["cable clips", "desk pad", "spare inserts", "carry sleeve"],
        "creators": ["desk tour", "deep work", "sunday reset office"],
        "hashtags": ["#wfhsetup", "#desksetup", "#productivity", "#deepwork"],
        "seasonality": "January productivity + back-to-office cycles",
        "price_band": (21.0, 79.0),
        "cogs": (6.0, 19.0),
        "cac": 14.0,
        "colors": ["#111318", "#6b8afd", "#eef1f6", "#8a8478"],
        "theme": "Refresh",
        "weaknesses": ["wobbles", "assembly nightmare", "cheap plastics"],
    },
}

_KEYWORD_MAP = {
    "home": (
        "candle", "lamp", "pillow", "blanket", "diffuser", "frame", "vase",
        "warmer", "lantern", "rug", "organizer", "hamper", "sconce",
    ),
    "beauty": (
        "serum", "cream", "skin", "hair", "brush", "mask", "lip", "lash",
        "toner", "oil", "mirror", "derma",
    ),
    "fitness": (
        "band", "yoga", "gym", "weight", "protein", "ab", "jump", "massage",
        "gun", "kettle", "resistance", "foam",
    ),
    "pet": ("dog", "cat", "pet", "puppy", "kitten", "leash", "litter", "chew"),
    "kitchen": (
        "pan", "knife", "blender", "air fryer", "bottle", "mug", "coffee",
        "garlic", "chop", "spatula", "cook",
    ),
    "tech": (
        "charger", "wireless", "bluetooth", "led", "camera", "stand", "hub",
        "earbuds", "tracker", "smart", "usb", "mini",
    ),
    "fashion": (
        "bag", "wallet", "jacket", "sneaker", "jewelry", "watch", "belt",
        "sunglasses", "hoodie", "ring",
    ),
    "outdoor": (
        "tent", "hike", "camp", "travel", "pack", "lantern", "waterproof",
        "bottle", "hammock", "trail",
    ),
    "baby": ("baby", "infant", "stroller", "pacifier", "diaper", "toddler", "nursing"),
    "office": ("desk", "chair", "monitor", "keyboard", "notebook", "lamp", "standup"),
}

SUPPLIERS = [
    {
        "supplier_name": "Shenzhen TechPro",
        "base_cost": 4.50,
        "rating": 4.8,
        "shipping_days": 7,
        "min_order_quantity": 10,
        "location": "Shenzhen, CN · US warehouse",
        "strength": "QC photos before ship",
        "risk": "low",
    },
    {
        "supplier_name": "Hangzhou Electronics",
        "base_cost": 5.10,
        "rating": 4.9,
        "shipping_days": 5,
        "min_order_quantity": 5,
        "location": "Hangzhou, CN · US warehouse",
        "strength": "fast restock, English PM",
        "risk": "low",
    },
    {
        "supplier_name": "US Direct Imports",
        "base_cost": 6.40,
        "rating": 4.7,
        "shipping_days": 3,
        "min_order_quantity": 1,
        "location": "Los Angeles, USA",
        "strength": "2-day domestic, easy returns",
        "risk": "low",
    },
    {
        "supplier_name": "Guangzhou Gadgets Co",
        "base_cost": 3.20,
        "rating": 4.3,
        "shipping_days": 18,
        "min_order_quantity": 50,
        "location": "Guangzhou, CN",
        "strength": "aggressive unit cost",
        "risk": "medium",
    },
    {
        "supplier_name": "Yiwu Trading Hub",
        "base_cost": 2.80,
        "rating": 3.9,
        "shipping_days": 25,
        "min_order_quantity": 100,
        "location": "Yiwu, CN",
        "strength": "lowest landed cost at volume",
        "risk": "high",
    },
    {
        "supplier_name": "Ningbo HomeWorks",
        "base_cost": 4.10,
        "rating": 4.6,
        "shipping_days": 9,
        "min_order_quantity": 20,
        "location": "Ningbo, CN · EU warehouse",
        "strength": "packaging customization",
        "risk": "low",
    },
    {
        "supplier_name": "Osaka Precision",
        "base_cost": 7.20,
        "rating": 4.95,
        "shipping_days": 8,
        "min_order_quantity": 8,
        "location": "Osaka, JP",
        "strength": "premium materials, low defect",
        "risk": "low",
    },
]

VOICES = {
    "Kore": {"tone": "warm contralto", "best_for": "cozy home and beauty", "pace": "unhurried"},
    "Puck": {"tone": "bright tenor", "best_for": "hooks and deal spots", "pace": "punchy"},
    "Charon": {"tone": "low documentary", "best_for": "tech and outdoor proof", "pace": "measured"},
    "Fenrir": {"tone": "gravel authority", "best_for": "fitness and menswear", "pace": "driven"},
    "Zephyr": {"tone": "airlight alto", "best_for": "wellness and baby", "pace": "soft"},
}


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "product"


def seed_for(*parts: Any) -> random.Random:
    payload = "|".join(str(p).lower().strip() for p in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def detect_niche(name: str, category: Optional[str] = None) -> str:
    blob = f"{name} {category or ''}".lower()
    if category:
        key = category.lower().strip()
        aliases = {
            "home & decor": "home",
            "home": "home",
            "decor": "home",
            "beauty": "beauty",
            "skincare": "beauty",
            "fitness": "fitness",
            "health": "fitness",
            "pet": "pet",
            "pets": "pet",
            "kitchen": "kitchen",
            "tech": "tech",
            "gadgets": "tech",
            "fashion": "fashion",
            "outdoor": "outdoor",
            "travel": "outdoor",
            "baby": "baby",
            "kids": "baby",
            "office": "office",
            "productivity": "office",
        }
        if key in aliases:
            return aliases[key]
        if key in NICHES:
            return key
    scores = {
        niche: sum(1 for word in words if word in blob)
        for niche, words in _KEYWORD_MAP.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "home"


def brandify(product_name: str, rng: random.Random, explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit.strip()
    stem = re.sub(r"[^A-Za-z0-9 ]+", "", product_name).split()
    head = stem[0] if stem else "Vektor"
    tails = ["Atelier", "House", "Co.", "Supply", "Studio", "Goods", "Lab", "Works"]
    return f"{head}{rng.choice(['', ' &'])} {rng.choice(tails)}".replace("  ", " ")


def charm_price(value: float) -> float:
    if value < 8:
        return round(value, 2)
    base = math.floor(value)
    return float(f"{base - 1}.99") if base > 1 else round(value, 2)


def analyze_product(
    name: str,
    category: Optional[str] = None,
    keywords: Optional[Sequence[str]] = None,
    features: Optional[Sequence[str]] = None,
    selling_price: Optional[float] = None,
    product_cost: Optional[float] = None,
) -> Dict[str, Any]:
    rng = seed_for(name, category or "")
    niche_key = detect_niche(name, category)
    niche = NICHES[niche_key]
    kws = [k.strip() for k in (keywords or []) if k and k.strip()]
    feats = [f.strip() for f in (features or []) if f and f.strip()]
    if not feats:
        feats = list(niche["benefits"][:3])
    if not kws:
        kws = [slugify(name).replace("-", " ")] + list(niche["hashtags"][:2])

    lo, hi = niche["price_band"]
    price = float(selling_price) if selling_price else round(rng.uniform(lo, hi), 2)
    price = charm_price(price)
    cogs_lo, cogs_hi = niche["cogs"]
    cost = float(product_cost) if product_cost else round(rng.uniform(cogs_lo, cogs_hi), 2)

    search_index = 42 + rng.randint(0, 55)
    competition = 28 + rng.randint(0, 60)
    trend = 35 + rng.randint(0, 60)
    opportunity = max(
        8,
        min(
            98,
            int(24 + search_index * 0.35 + trend * 0.36 - competition * 0.14),
        ),
    )

    return {
        "name": name.strip(),
        "slug": slugify(name),
        "niche": niche_key,
        "niche_label": niche["label"],
        "category": category or niche["label"],
        "audience": niche["audience"],
        "pain_points": list(niche["pain"]),
        "benefits": list(niche["benefits"]),
        "features": feats,
        "keywords": kws,
        "attach": list(niche["attach"]),
        "creators": list(niche["creators"]),
        "hashtags": list(niche["hashtags"]),
        "seasonality": niche["seasonality"],
        "colors": list(niche["colors"]),
        "theme": niche["theme"],
        "weaknesses": list(niche["weaknesses"]),
        "price": price,
        "cost": cost,
        "shipping": 5.5 if niche_key != "tech" else 4.2,
        "cac": float(niche["cac"]),
        "search_index": search_index,
        "competition": competition,
        "trend": trend,
        "opportunity": opportunity,
        "brand": brandify(name, rng),
        "seed": rng.randint(10_000, 99_999),
    }


def default_competitors(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    rng = seed_for("comp", product["name"])
    price = product["price"]
    names = [
        ("Amazon Basics", "amazon", -0.12, 0, 2),
        ("Etsy Maker Co", "etsy", 0.18, 4.99, 8),
        ("TikTok Shop #1", "tiktok", -0.04, 2.99, 9),
        ("Walmart Marketplace", "walmart", -0.08, 0, 4),
        ("Niche DTC Brand", "shopify", 0.22, 0, 5),
    ]
    out = []
    for name, platform, delta, ship, days in names:
        jitter = rng.uniform(-0.04, 0.04)
        out.append(
            {
                "competitor_name": name,
                "platform": platform,
                "price": round(max(9.99, price * (1 + delta + jitter)), 2),
                "shipping": ship,
                "delivery_days": days,
            }
        )
    return out


def default_campaigns(product: Dict[str, Any], daily_budget: float) -> List[Dict[str, Any]]:
    rng = seed_for("ads", product["name"], daily_budget)
    platforms = ["meta", "tiktok", "google"]
    split = [0.45, 0.35, 0.20]
    campaigns = []
    for i, (platform, share) in enumerate(zip(platforms, split), start=1):
        budget = round(daily_budget * share, 2)
        spent = round(budget * rng.uniform(0.72, 1.0), 2)
        roas = rng.choice([0.6, 0.9, 1.4, 2.1, 2.8, 3.6, 4.2])
        revenue = round(spent * roas, 2)
        clicks = max(12, int(spent * rng.uniform(1.4, 3.2)))
        impressions = clicks * rng.randint(28, 55)
        conversions = max(0, int(clicks * rng.uniform(0.02, 0.09)))
        campaigns.append(
            {
                "campaign_id": f"{platform[:2].upper()}-{180 + i}",
                "product_name": product["name"],
                "platform": platform,
                "daily_budget": budget,
                "spent_today": spent,
                "revenue_today": revenue,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "status": "active",
            }
        )
    return campaigns
