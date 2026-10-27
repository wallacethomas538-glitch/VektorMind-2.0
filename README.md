# VEKTORFLOW-15

**Autonomous AI e-commerce operating system — 15 specialized agents, one launch decision.**

Cerebrum Command is a working command center. Brief a product and the table runs scout, supply, store, creative, media, support, price, compliance, voice, virality, competitor intel, bundles, positioning, and a 30-day P&L — then Cerebrum issues **LAUNCH**, **ITERATE**, or **KILL**.

Same product, same numbers. The read is deterministic.

## Reused vs. new (Mission Command dashboard branch)

This branch (`opencode/mission-command-dashboard`) is an upgrade of the existing
Cerebrum Command dashboard. It does **not** claim the pre-existing board as new work.

**Reused from main `5bace1d` (pre-existing, not new):**

- Cerebrum Command shell: layout, left agent rail, top nav, ticker, boot overlay, `static/css/app.css`, `static/js/app.js`.
- All 15 agents and the mission loop in `vektorflow/agents.py`, plus `/api/v1/mission`, `/api/v1/receipt/{mission_id}`, `/api/v1/kill-switch`, and `/health` in `vektorflow/app.py`.
- Draft-only extensions, persistence layer, Supabase migration, and existing tests.
- The Launch, Live Ops, and Dossier views.

**New in this branch:**

- `static/js/mission_command.js` — one-sentence mission brief driving the live mission API, then rendering the dynamic 15-step plan, draft evidence, the visible Pivot failed/replanned attempts, the Aegis Gate, the pending Wallace approval, and the receipt (`mission_id`, `plan`, `evidence`, `meta_served`, `image_served`).
- Mission Command view in `static/index.html` (title/header rebrand to **VektorMind 2.0 — Mission Command**), with the Cerebrum layout retained.
- Kill-switch ON/OFF control in the UI that probes `/api/v1/mission` for `503` when engaged and `200` when released.
- Mission Command styles appended to `static/css/app.css`, plus the dashboard assertion update in `tests/test_api.py`.
- This README section.

No Shopify integration, no VektorFlow15xr call, no Meta call. Draft-only.

## The table

| # | Agent | Desk |
|---|-------|------|
| 01 | Hawk | Product scout, SEO copy, opportunity score |
| 02 | Smaug | Supplier match, landed cost, negotiation script |
| 03 | Architect | Brand, palette, store blueprint, FAQ |
| 04 | DaVinci | Hooks, 18s script, headlines, UGC prompt |
| 05 | Rook | Scale / maintain / kill on ROAS |
| 06 | Aegis | Support intents, review tone, abandoned-cart drip |
| 07 | Arbiter | Floor, charm price, competitor tape |
| 08 | Sentinel | GDPR/CCPA score, policy excerpt, checklist |
| 09 | Echo | Voice casting and runtime for ad reads |
| 10 | Cerebrum | Assembles the table. One verdict. |
| 11 | ViralDet | Platform velocity and launch window |
| 12 | Shadow | Competitor hooks, weak spot, counter-moves |
| 13 | Bundler | Starter / Kit / Deluxe with AOV lift |
| 14 | Pivot | One-star reviews turned into ad angles |
| 15 | Oracle | Conservative / base / optimistic 30-day P&L |

Built for solo-seller store operations. Draft-only by default.

## Quick start

```bash
python -m pip install -r requirements.txt
python -m vektorflow
```

Open [http://localhost:8000](http://localhost:8000). Demo mode is on by default.

```bash
# lock mutating endpoints in production
export VEKTORFLOW_DEMO=false
export VEKTORFLOW_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

Interactive API: [http://localhost:8000/docs](http://localhost:8000/docs)

```bash
pytest
```

```bash
docker build -t vektorflow-15 .
docker run -p 8000:8000 vektorflow-15
```

## How a mission works

1. Open **Launch** and brief the product (name, category, price, cost, daily ad budget).
2. Cerebrum wakes the table in order. Each agent files a one-line finding.
3. The **dossier** is the full read — verdict, conviction, and every desk report.
4. **Live Ops** is today’s floor: Rook’s book, Arbiter’s tape, Aegis’s queue, ViralDet’s heat.

Individual desks are on the left rail if you only need one agent.

## Mission receipts

Every mission returns an objective, the dynamic 15-step plan, draft evidence, the
Aegis Gate decision, pending Wallace approval, risk, and a receipt. A visible Pivot
replan follows the blocked external-sentiment lookup.

```bash
curl -s localhost:8000/api/v1/receipt/<mission_id>
```

A real mission returns its own staged receipt. An unknown id returns `404`.

## Draft-only extensions

- `POST /api/v1/ad-draft/pollinations` — organic Pollinations draft, max 1024x1088. Not Muse Image, never served.
- `POST /api/v1/receptionist/draft` — Aegis receptionist draft. No new agent, never sent.
- `POST /api/v1/layout/preview` — preview only. No rewrite, CMS write, or deploy.
- `GET /api/v1/mcp/registry` — local metadata only. No MCP server contacted.
- `GET|POST /api/v1/kill-switch` — stop or restore draft tools.

`meta_served` and `image_served` stay `false` until credits land and Wallace
second-approves an exact call.

## Persistence (Hackathon 2026 only)

Receipts persist only to the new Hackathon 2026 Supabase project, using:

```bash
HACKATHON_SUPABASE_URL=
HACKATHON_SUPABASE_KEY=
```

Generic `SUPABASE_URL` / `SUPABASE_KEY` are ignored on purpose. The schema is in
`supabase/migrations/20261027_hackathon_2026.sql` with RLS enabled. Leave the
variables blank to keep receipts in process memory only.

## Security

- `VEKTORFLOW_DEMO=true` (default) keeps the command center usable without a key.
- With demo off, mutating `/api/v1/*` routes require `X-API-Key`.
- `/`, `/health`, `/docs`, and `/static` stay public so the board can load.

## License

Apache 2.0. Copyright 2026 Wallace J Thomas III — VEKTORFLOW.
