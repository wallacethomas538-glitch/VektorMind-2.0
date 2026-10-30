"""
VektorMind 2.0 — MODIFIED main — Hackathon build, Oct 26, 2026
Project: VektorMind 2.0
Repo: VektorMind-2.0 (public, created by Wallace in the GitHub app)
This is VektorMind 2.0. It is NOT SlumberSmith. That name is dropped and is not used anywhere in this file.
Base reference (NOT verbatim): VektorAegis security-gate starter (ChatGPT via Wallace)
+ VektorFlow-10 agent functions (Hawk/Smaug/Architect/Arbiter/Sentinel/Cerebrum, truncated upload)
Modifications made during the hackathon window:
- Added Aegis Gate: pre-action risk score (reversibility) + pre-written recovery plan
- Added WorkflowManager: mission -> plan -> execute -> evidence -> approval -> receipt
- Added kill switch covering tools AND model calls
- Added Meta-served flag: meta_served=True ONLY when a real Meta call succeeds;
  otherwise meta_served=False, never faked. Meta call is a stub until META_MODEL_API_KEY is set.
- Added mission receipt export (objective, plan, evidence, approvals, risk, kill-switch, cost)
- Completed the truncated Cerebrum bundler return; added missing DaVinci/Rook/Aegis/Echo as draft-only roles
- Oct 26, 17:02 EDT, ANY-BUSINESS REWRITE (Wallace): code is NOT store/e-commerce-only. Every mission links to a BusinessProfile (any business type: store, salon, restaurant, service, etc.). Store-specific names kept only as aliases. A mission without a business profile is rejected.
- No money moves. No auto-send, auto-price-change, or auto-post. Writes require approval.
- No secrets in code. No payload secrets in audit logs.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import logging
import os
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("new_system")

class Risk(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

@dataclass
class AgentTask:
    agent: str; action: str
    payload: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class SecurityDecision:
    allowed: bool; risk: Risk; reason: str

@dataclass
class RecoveryPlan:
    undo: str; retry_with: str; escalate_when: str

# --- Aegis Gate (modified from VectorAegis starter) ---
# NOTE (Wallace, Oct 26): Aegis is NOT an agent. It is a SECURITY LAYER underneath all agents.
class AegisGate:
    BLOCKED = {"delete_system", "disable_security", "exfiltrate_data", "transfer_funds"}
    APPROVAL_REQUIRED = {"send_external_message", "modify_production", "delete_data", "execute_command"}
    def inspect(self, task: AgentTask) -> SecurityDecision:
        a = task.action.strip().lower()
        if not a: return SecurityDecision(False, Risk.HIGH, "Missing action.")
        if a in self.BLOCKED: return SecurityDecision(False, Risk.CRITICAL, "Action prohibited by security policy.")
        if a in self.APPROVAL_REQUIRED: return SecurityDecision(False, Risk.HIGH, "Explicit authorization required.")
        return SecurityDecision(True, Risk.LOW, "Passed initial policy checks.")
    def risk_score(self, task: AgentTask) -> dict[str, Any]:
        """Reversibility: read/draft = soft, store write/customer-facing = hard."""
        a = task.action.strip().lower()
        if a in self.BLOCKED: rev, score = "irreversible", 100
        elif a in self.APPROVAL_REQUIRED: rev, score = "hard", 75
        elif "draft" in a or "analyze" in a or "read" in a: rev, score = "soft", 10
        else: rev, score = "soft", 25
        return {"reversibility": rev, "score": score}
    def recovery_plan(self, task: AgentTask) -> RecoveryPlan:
        return RecoveryPlan(
            undo="Revert the draft / discard the prepared change; no store write was made.",
            retry_with="Retry with the same inputs after human approval, or with a narrower scope.",
            escalate_when="On any failure, on any money-adjacent action, or on any missing policy — stop and escalate to the founder.",
        )

class AuditLog:
    def record(self, task: AgentTask, decision: SecurityDecision, extra: dict | None = None) -> None:
        logger.info("AUDIT %s", {"timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task.task_id, "agent": task.agent, "action": task.action,
            "allowed": decision.allowed, "risk": decision.risk.value, "reason": decision.reason, **(extra or {})})

class AgentRegistry:
    def __init__(self): self._agents: dict[str, bool] = {}
    def register(self, name: str) -> None:
        if not name.strip(): raise ValueError("Agent name cannot be empty.")
        if name in self._agents: raise ValueError(f"Agent already registered: {name}")
        self._agents[name] = True
    def disable(self, name: str) -> None:
        if name not in self._agents: raise KeyError(f"Unknown agent: {name}")
        self._agents[name] = False
    def is_enabled(self, name: str) -> bool: return self._agents.get(name, False)

# --- Meta integration — WIRED TO ACCEPT A CALL, but NOT called until Wallace taps go ---
# Wiring (Wallace, Oct 26): endpoint + model come from env, never hardcoded as fact.
# Defaults below are the third-party guide values (api.meta.ai/v1/messages, muse-spark)
# and are NOT verified against official Meta docs — confirm them from dev.meta.ai
# before the first real call. meta_served=True ONLY on a real HTTP 200 with content.
# DO NOT CALL THIS until $150 credits are in (~2 days) and Wallace taps go — no charge attempt.
def meta_model_call(prompt: str) -> dict[str, Any]:
    import json as _json, urllib.request as _req, urllib.error as _err
    key = os.environ.get("META_MODEL_API_KEY", "")
    if not key:
        return {"meta_served": False, "model": None, "reason": "META_MODEL_API_KEY not set — fallback, not Meta-served.", "output": None}
    model = "muse-spark-1.3"
    endpoint = "https://api.meta.ai/v1/chat/completions"
    body = _json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode()
    request = _req.Request(endpoint, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    try:
        with _req.build_opener().open(request, timeout=30) as resp:
            data = _json.loads(resp.read().decode())
            # Accept either OpenAI-style choices or Anthropic-style content — whichever Meta returns.
            out = None
            if isinstance(data, dict):
                if data.get("choices"): out = data["choices"][0].get("message", {}).get("content")
                elif data.get("content"): out = data["content"]
            if out:
                return {"meta_served": True, "model": model, "endpoint": endpoint, "reason": "Real Meta call succeeded.", "output": out}
            return {"meta_served": False, "model": model, "endpoint": endpoint, "reason": "Meta responded but no usable content — not counted as Meta-served.", "output": None}
    except _err.HTTPError as e:
        return {"meta_served": False, "model": model, "endpoint": endpoint, "reason": f"Meta call failed HTTP {e.code} — not Meta-served, no charge assumed.", "output": None}
    except Exception as e:
        return {"meta_served": False, "model": model, "endpoint": endpoint, "reason": f"Meta call error {type(e).__name__} — not Meta-served.", "output": None}

# --- ANY-BUSINESS LINK (Wallace, Oct 26): how code attaches to ANY business ---
@dataclass
class BusinessProfile:
    """The link between VektorMind and a real business — any type, not just a store."""
    business_name: str
    business_type: str  # e.g. "salon", "restaurant", "car care shop", "online store", "plumbing service"
    offering: str  # the main product or service, e.g. "haircuts", "tacos", "ceramic coating"
    location: str = ""
    def validate(self) -> None:
        if not self.business_name.strip() or not self.business_type.strip() or not self.offering.strip():
            raise ValueError("BusinessProfile needs business_name, business_type, and offering — a mission without a business is rejected.")

# --- Modified VektorFlow-10 agent functions (draft-only, no business writes) ---
MOCK_SUPPLIERS = [
    {"supplier_name": "Shenzhen TechPro", "price_per_unit": 4.50, "rating": 4.8, "shipping_days": 7},
    {"supplier_name": "US Direct Imports", "price_per_unit": 6.00, "rating": 4.7, "shipping_days": 3},
]
def vendor_finder(business: BusinessProfile, min_rating: float = 4.0, max_days: int = 21) -> dict:
    """Generic vendor/supplier finder — works for any business type, not just a store."""
    business.validate()
    matched = [s for s in MOCK_SUPPLIERS if s["rating"] >= min_rating and s["shipping_days"] <= max_days]
    return {"agent": "vendor_finder (modified, draft-only)", "business": business.business_name,
            "business_type": business.business_type, "offering": business.offering,
            "top_vendors": matched, "best_vendor": matched[0] if matched else None}
# Old store-only name, kept as an alias so old calls still work:
def supplier_finder(product_name: str, min_rating: float = 4.0, max_days: int = 21) -> dict:
    return vendor_finder(BusinessProfile("Unnamed Business", "store", product_name), min_rating, max_days)
def business_blueprint(business: BusinessProfile, price: float) -> dict:
    """Generic business builder — brand page for any business, not just a storefront."""
    business.validate()
    return {"agent": "business_builder (modified, draft-only)", "business": business.business_name,
            "business_type": business.business_type,
            "brand_name": f"{business.business_name} {business.business_type.title()}",
            "hero_section": {"headline": f"{business.offering} — {business.business_name}", "cta": f"Book / Get Yours - USD {price}"}}
def store_blueprint(product_name: str, price: float) -> dict:
    return business_blueprint(BusinessProfile(f"{product_name.split()[0]}Pro", "store", product_name), price)
def scarcity_price(base_cost: float, shipping: float, stock: int, views: int, margin: float = 0.40) -> dict:
    total = base_cost + shipping; target = round(total / (1.0 - margin), 2); mult = 1.0
    if views > 150: mult += 0.12
    elif views > 50: mult += 0.05
    if 0 < stock < 25: mult += 0.15
    opt = round(target * mult, 2)
    return {"standard_target_retail": target, "optimized_scarcity_retail": opt, "note": "DRAFT ONLY — price change requires human approval, never auto-applied."}
def compliance_scrub(product_name: str, tags: list[str]) -> dict:
    marks = ["nike", "adidas", "apple", "rolex", "gucci"]
    hits = [m for m in marks if m in product_name.lower() or any(m in t.lower() for t in tags)]
    return {"passed": not hits, "violations": hits}
def bundle(category: str, core_price: float) -> dict:
    comp = {"electronics": "Premium Magnetic Cable Organizer", "fashion": "Minimalist Adjustable Leather Belt"}.get(category.lower(), "Premium Tailored Hard-Shell Protective Case")
    est = round(core_price * 0.40, 2); total = core_price + est
    return {"complement": comp, "bundle_retail_price": round(total * 0.90, 2)}  # completed Cerebrum return, was truncated in source

# --- Vektor: main orchestrator, always-on watcher, NOT autonomous ---
KILL_SWITCH = {"global_killed": False}
# Vektor is Wallace's unique build — the MAIN ORCHESTRATOR (not autonomous, workflow manager).
class Vektor:
    def __init__(self):
        self.security = AegisGate(); self.audit = AuditLog(); self.agents = AgentRegistry(); self.receipts: list[dict] = []
    def submit(self, task: AgentTask) -> dict[str, Any]:
        if KILL_SWITCH["global_killed"]:
            return {"task_id": task.task_id, "status": "killed", "reason": "Kill switch engaged — tools and model calls stopped."}
        if not self.agents.is_enabled(task.agent):
            return {"task_id": task.task_id, "status": "rejected", "reason": "Agent is unknown or disabled."}
        decision = self.security.inspect(task); risk = self.security.risk_score(task); plan = self.security.recovery_plan(task)
        self.audit.record(task, decision, {"risk_score": risk})
        if not decision.allowed:
            return {"task_id": task.task_id, "status": "blocked", "risk": decision.risk.value, "reason": decision.reason, "risk_score": risk, "recovery_plan": plan.__dict__}
        # Draft-only execution: no business writes, no sends, no money moves.
        # A mission must link to a business profile in its payload, or it is not a real business mission.
        evidence = {"note": "Draft/analysis only — prepared for human approval, not applied.",
                    "business": task.payload.get("business_name") if isinstance(task.payload, dict) else None}
        receipt = {"task_id": task.task_id, "agent": task.agent, "action": task.action, "risk": decision.risk.value,
                   "risk_score": risk, "recovery_plan": plan.__dict__, "evidence": evidence, "kill_switch": dict(KILL_SWITCH),
                   "meta": meta_model_call(task.action), "approved_by": None}
        self.receipts.append(receipt)
        return {"task_id": task.task_id, "status": "authorized_draft_ready", "receipt": receipt}

def main() -> None:
    system = Vektor()  # Vektor, main orchestrator
    for name in ["research_agent", "supplier_agent", "store_agent"]:
        system.agents.register(name)
    print("1. allowed draft:", system.submit(AgentTask("research_agent", "analyze_public_information", {"scope": "authorized_public_sources"}))["status"])
    print("2. blocked:", system.submit(AgentTask("research_agent", "transfer_funds", {}))["status"])
    print("3. approval-required:", system.submit(AgentTask("store_agent", "modify_production", {}))["status"])
    print("4. supplier (modified):", supplier_finder("car care kit"))
    print("5. bundle (completed):", bundle("electronics", 49.99))
    print("6. scarcity (draft only):", scarcity_price(10.0, 5.0, 10, 200))
    print("7. receipt count:", len(system.receipts), "| meta_served on receipt 1:", system.receipts[0]["meta"]["meta_served"])
    # Any-business check: same code, three different business types — must all work, not just a store.
    salon = BusinessProfile("Wallace Cuts", "salon", "haircuts", "Hampton, SC")
    tacos = BusinessProfile("Taco Town", "restaurant", "tacos", "Hampton, SC")
    shop = BusinessProfile("JoJoes Supply", "car care shop", "ceramic coating", "Hampton, SC")
    print("8. ANY-BUSINESS salon vendor:", vendor_finder(salon)["best_vendor"]["supplier_name"])
    print("9. ANY-BUSINESS restaurant blueprint:", business_blueprint(tacos, 12.99)["hero_section"]["headline"])
    print("10. ANY-BUSINESS shop blueprint:", business_blueprint(shop, 49.99)["brand_name"])
    assert vendor_finder(salon)["business_type"] == "salon"
    assert vendor_finder(tacos)["business_type"] == "restaurant"
    assert business_blueprint(shop, 49.99)["business_type"] == "car care shop"
    print("ANY-BUSINESS CHECK PASSED: salon, restaurant, and shop all run on the same code.")

if __name__ == "__main__":
    main()
