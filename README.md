# VektorMind 2.0

## Proposed GitHub description (one line)
VektorMind 2.0 — upgrade of VektorFlow's 15-agent coordination layer to Muse Spark dynamic planning + Muse Image ad creatives, for solo-seller store operations, with every ad and action staged for owner approval.

## What this is
A solo seller types one sentence, and a 15-agent team runs the play — in draft only, staged for the owner's approval. Nothing is published, sent, priced live, or moved for money without the owner's tap.

Live demo: https://vektormind-2-0.onrender.com/
Live mission receipt (example, verified Oct 27): VF-52983-ac7a6516f6 — staged_for_approval, plan 15 steps, evidence 15 draft items, Pivot replanned, Aegis Gate passed (risk 2), meta_served false, image_served false.

## The submitted pitch, in plain terms
Upgrade VektorFlow's coordination layer — the system that breaks missions into subtasks, assigns them across 15 specialist agents, and synthesizes their outputs — to run on Muse Spark's agentic reasoning. Today that orchestration is hand-coded state machines; with Muse Spark, VektorMind dynamically plans multi-step store operations (for example: "find trending car-care products, price them competitively, generate ads, and stage them for my approval"), adapting in real time when subtasks fail or new information arrives. Muse Image auto-generates product ad creatives directly in the agent pipeline — from product sourcing to staged ad, with the owner approving before anything publishes.

**Honesty label:** Muse Spark and Muse Image are integration targets in this build. Until a real, owner-approved call returns HTTP 200, the demo labels their outputs as staged targets, not live Meta results. No live Meta generation call has been made as of Oct 27, 2026.

## How a mission runs (live, draft-only)
1. One sentence in — Mission Command dashboard.
2. Dynamic 15-step plan — Hawk, Smaug, Architect, DaVinci, Rook, Aegis, Arbiter, Sentinel, Echo, Cerebrum, ViralDet, Shadow, Bundler, Pivot, Oracle.
3. Draft evidence — 15 draft items, no external calls, no provider calls.
4. Pivot replan, visible — when an external source is not contacted in draft-only mode, Pivot fails that attempt, then replans with local intelligence.
5. Aegis Gate — generic security gate, risk score, blocked actions: publish_live, price_live, money_move, send_external_message, call_provider, deploy_live.
6. Staged for Wallace approval — approval pending, approver Wallace, final tap.
7. Receipt — mission_id, plan, evidence, meta_served, image_served, kill_switch state.

Kill switch: ON blocks missions with 503, OFF allows them with 200. Tested locally Oct 27 (32 tests passed) and live on the dashboard.

## What is new vs. not new (hackathon honesty)
**New in the Oct 26–Nov 4 window:**
- Muse Spark dynamic planning layer (planner label in the mission receipt; live Meta call pending credits + owner approval)
- Mission loop: objective → 15-step plan → evidence → Aegis Gate → owner approval pending → receipt
- Mission Command dashboard: one-sentence brief, plan, evidence, Pivot replan, Aegis Gate, approval, receipt, kill-switch control
- Boot overlay fix, Python 3.14 dependency fix, new Render service VektorMind-2.0, new Supabase project Hackathon 2026

**Not new — reused, not claimed as new work:**
- VektorFlow-15 code base (cloned, pre-existing): FastAPI app, 15-agent roster, Cerebrum Command shell, mission loop structure
- 15-agent concept, Store Playbook, draft-only extensions structure
- Oct 26 5-agent / any-business rebuild: reference only, not the submission
- VektorFlow15xr backend, Render service, and Supabase: frozen backup only, not touched, not wired to this build
- VektorAegis (separate project, Codeberg): not named, credited, or used in this submission; the gate in this code is the generic Aegis Gate

## Stack and accounts (new accounts only)
- GitHub: wallacethomas538-glitch/VektorMind-2.0 (public)
- Render: VektorMind-2.0 (new service, Free plan, Oregon)
- Supabase: Hackathon 2026 (new project, ca-central-1) — Render env HACKATHON_SUPABASE_URL / HACKATHON_SUPABASE_KEY only; generic SUPABASE_URL / SUPABASE_ANON_KEY are ignored by the code, anon is not used
- No Shopify live store, API, products, orders, or writes in this build
- No VektorFlow15xr calls, no Meta generation calls yet

## Status as of Oct 27, 2026
- Main: 6d9b054, Render deploy live, /health 200, persistence ready (Supabase)
- Live mission VF-52983-ac7a6516f6 verified via /api/v1/receipt
- Meta $150 credits: not yet in dev.meta.ai Billing — recheck Oct 28, claim deadline Nov 4, 9:00 PM ET
- Demo video (3 minutes): not recorded yet — must show a user interacting with a working mission, new work only
- Submission: via Cerebral Valley, due Nov 4, 2026, 9:00 PM ET

## Quick start (for judges)
1. Open https://vektormind-2-0.onrender.com/ — wait ~2 seconds for the boot screen to clear.
2. On Mission Command, type one sentence, for example: "Launch a dorm-safe candle warmer lamp at $44.99 for solo sellers"
3. Submit, watch the 15-step plan, draft evidence, Pivot replan, Aegis Gate, and the receipt staged for approval.
4. Check the receipt: https://vektormind-2-0.onrender.com/api/v1/receipt/VF-52983-ac7a6516f6
5. Check health: https://vektormind-2-0.onrender.com/health
