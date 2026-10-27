"""Request and response contracts for the 15-agent operating system."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    category: Optional[str] = "general"
    keywords: Optional[List[str]] = []


class SupplierRequest(BaseModel):
    product_name: str
    target_selling_price: Optional[float] = None
    min_rating: Optional[float] = 4.0
    max_shipping_days: Optional[int] = 21


class StoreBuildRequest(BaseModel):
    product_name: str
    product_features: List[str] = []
    product_price: float = 39.0
    niche: Optional[str] = "general"
    store_type: Optional[str] = "one_product"
    brand_name: Optional[str] = None


class CreativeRequest(BaseModel):
    product_name: str
    product_features: List[str] = []
    product_price: float = 39.0
    creative_type: str = "all"


class AdCampaign(BaseModel):
    campaign_id: str
    product_name: str
    platform: str
    daily_budget: float
    spent_today: float
    revenue_today: float
    impressions: int
    clicks: int
    conversions: int
    status: str = "active"


class AdManagerRequest(BaseModel):
    target_roas: Optional[float] = 2.0
    total_daily_budget: float = 500.0
    campaigns: List[AdCampaign] = []
    product_name: Optional[str] = None


class ChatMessage(BaseModel):
    message: str
    product_name: Optional[str] = None


class Review(BaseModel):
    review_text: str
    product_name: Optional[str] = None


class CartItem(BaseModel):
    product_name: str
    user_name: Optional[str] = "Customer"
    cart_value: Optional[float] = None


class CompetitorPrice(BaseModel):
    competitor_name: str
    platform: str
    price: float
    shipping: float = 0
    delivery_days: int = 7


class PricingRequest(BaseModel):
    product_name: str
    product_cost: float
    shipping_cost: float = 0
    competitors: List[CompetitorPrice] = []
    demand_signal: Optional[str] = "normal"


class ComplianceRequest(BaseModel):
    store_name: str
    store_url: str
    data_collection: Optional[List[str]] = ["email", "shipping_address"]
    region: Optional[str] = "US-EU"


class TTSRequest(BaseModel):
    text: str
    voice_name: Optional[str] = "Kore"
    product_name: Optional[str] = None


class ViralDetectorRequest(BaseModel):
    product_name: str
    platforms: Optional[List[str]] = ["tiktok", "instagram", "youtube"]


class CompetitorShadowRequest(BaseModel):
    competitor_url: str
    product_name: Optional[str] = None


class BundleBuilderRequest(BaseModel):
    main_product: str
    budget: float = 45.0
    product_cost: Optional[float] = None


class SentimentPivotRequest(BaseModel):
    competitor_product_url: str
    product_name: Optional[str] = None


class ProfitPredictorRequest(BaseModel):
    product_cost: float
    selling_price: float
    ad_budget: float
    niche: str = "general"
    product_name: Optional[str] = None


class ForecastRequest(BaseModel):
    historical_sales: List[int]
    product_name: Optional[str] = None


class PriceRequest(BaseModel):
    product_id: str
    current_price: float
    competitor_price: Optional[float] = None


class MissionRequest(BaseModel):
    product_name: str
    category: Optional[str] = None
    keywords: Optional[List[str]] = []
    features: Optional[List[str]] = []
    selling_price: float = 39.0
    product_cost: Optional[float] = None
    shipping_cost: float = 5.5
    ad_budget: float = 100.0
    brand_name: Optional[str] = None
    store_name: Optional[str] = None
    store_url: Optional[str] = None
    platforms: Optional[List[str]] = ["tiktok", "instagram", "meta"]
    competitor_url: Optional[str] = None
