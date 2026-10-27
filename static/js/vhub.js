/* VektorMind 2.0 — V Hub.
 * A glowing faceted V, a purple/blue particle spiral, a perspective floor grid,
 * rings, and six tech panels orbiting in 3D. Everything is drawn live in
 * HTML/CSS/JS — no reference video plays behind it and there is no backdrop.
 * Push a panel once: the orbit swings it to the front, stops, and the section
 * swings up. Push the header again or tap close to swing back down and resume
 * the rotating hub. Only one section is open at a time. Draft-only; status is
 * read from the API.
 */
(function () {
  "use strict";

  const hub = document.getElementById("vhub");
  if (!hub) return;

  const stage = document.getElementById("vhub-stage");
  const panels = Array.from(document.querySelectorAll(".vhub-panel"));
  const section = document.getElementById("vhub-section");
  const sectionHead = document.getElementById("vhub-section-head");
  const sectionEyebrow = document.getElementById("vhub-section-eyebrow");
  const sectionTitle = document.getElementById("vhub-section-title");
  const sectionBody = document.getElementById("vhub-section-body");
  const closeButton = document.getElementById("vhub-close");
  const statusPill = document.getElementById("vhub-status-pill");
  const particleCanvas = document.getElementById("vhub-particles");

  const TAU = Math.PI * 2;
  const STEP = TAU / panels.length;
  const FRONT = Math.PI / 2;
  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const SPEED = REDUCED ? 0 : 0.16;
  const AIM_MS = 480;
  const RECEIPT_KEY = "vhub-receipt-ids";

  const META = {
    agents: { eyebrow: "Table of 15", title: "Agents", load: loadAgents },
    llm: { eyebrow: "Provider gate", title: "LLM / Muse Spark", load: loadLlm },
    missions: { eyebrow: "Draft-only", title: "Missions", load: loadMissions },
    ops: { eyebrow: "Floor read", title: "Live Ops", load: loadOps },
    receipts: { eyebrow: "Staged approvals", title: "Receipts", load: loadReceipts },
    kill: { eyebrow: "Aegis Gate", title: "Kill Switch", load: loadKill },
  };

  let angle = -Math.PI / 2;
  let mode = "spin";
  let active = null;
  let pending = null;
  let aimFrom = 0;
  let aimTarget = 0;
  let aimStart = 0;
  let rafId = null;
  let lastTs = 0;

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function money(value) {
    const n = Number(value);
    return Number.isFinite(n) ? "$" + n.toFixed(2) : "—";
  }

  function card(label, value, kind) {
    return `<div class="vhub-status ${kind || ""}"><span>${esc(label)}</span><b>${value}</b></div>`;
  }

  function loading(text) {
    return `<p class="hint">${esc(text)}</p>`;
  }

  function errorBlock(result) {
    const detail = result && (result.error || `Request failed · HTTP ${result.status}`);
    return `<div class="vhub-note-card"><p class="eyebrow">Unavailable</p><p>${esc(detail)}</p><p class="hint">Check the API, then push this panel again.</p></div>`;
  }

  async function request(path, body) {
    const opts = body === undefined
      ? { method: "GET" }
      : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    try {
      const res = await fetch(path, opts);
      let data = null;
      try { data = await res.json(); } catch { /* non-JSON body */ }
      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      return { ok: false, status: 0, data: null, error: err.message };
    }
  }

  function parseSentence(sentence) {
    const text = String(sentence || "").trim().replace(/\s+/g, " ").replace(/[.!?]+$/, "");
    let product = text.replace(/^(launch|sell|test|source|build|find|validate|scale|ship)\s+(a|an|the)?\s*/i, "");
    product = product.replace(/\s+(at|for|to)\s+.*$/i, "").trim();
    if (!product) product = text;
    const priceMatch = text.match(/\$\s*(\d+(?:\.\d{1,2})?)/);
    return {
      product: product.slice(0, 160),
      price: priceMatch ? Number(priceMatch[1]) : null,
    };
  }

  function rememberReceipt(id) {
    if (!id) return;
    try {
      const list = JSON.parse(sessionStorage.getItem(RECEIPT_KEY) || "[]");
      if (!list.includes(id)) {
        list.unshift(id);
        sessionStorage.setItem(RECEIPT_KEY, JSON.stringify(list.slice(0, 20)));
      }
    } catch { /* ignore storage */ }
  }

  function knownMissionIds() {
    const ids = new Set();
    try {
      JSON.parse(sessionStorage.getItem(RECEIPT_KEY) || "[]").forEach((id) => { if (id) ids.add(id); });
    } catch { /* ignore */ }
    for (const key of ["vm2-mission-command", "vf-mission"]) {
      try {
        const raw = sessionStorage.getItem(key);
        if (!raw) continue;
        const parsed = JSON.parse(raw);
        const id = parsed?.mission?.mission_id || parsed?.mission_id || parsed?.receipt?.mission_id;
        if (id) ids.add(id);
      } catch { /* ignore */ }
    }
    return Array.from(ids);
  }

  /* ---------- particle spiral ---------- */

  const particles = [];
  let particleCtx = null;
  let particleW = 0;
  let particleH = 0;

  function setupParticles() {
    if (!particleCanvas) return;
    particleCtx = particleCanvas.getContext("2d");
    if (!particleCtx) return;
    const count = window.innerWidth < 700 ? 170 : 320;
    particles.length = 0;
    for (let i = 0; i < count; i += 1) {
      const arm = i % 3;
      const spread = Math.pow(Math.random(), 0.62);
      particles.push({
        arm,
        radius: 0.07 + spread * 0.5 + Math.random() * 0.03,
        angle: arm * (TAU / 3) + spread * 3.6 + Math.random() * 0.3,
        speed: 0.1 + Math.random() * 0.34,
        size: 0.45 + Math.random() * 1.7,
        depth: Math.random(),
        hue: Math.random() < 0.72 ? 258 : 190,
      });
    }
    resizeParticles();
  }

  function resizeParticles() {
    if (!particleCanvas || !particleCtx) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.75);
    particleW = hub.clientWidth || window.innerWidth;
    particleH = hub.clientHeight || window.innerHeight;
    particleCanvas.width = Math.max(1, Math.round(particleW * dpr));
    particleCanvas.height = Math.max(1, Math.round(particleH * dpr));
    particleCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawParticles(ts) {
    if (!particleCtx) return;
    const ctx = particleCtx;
    if (!particleW || !particleH) resizeParticles();
    ctx.clearRect(0, 0, particleW, particleH);
    const cx = particleW * 0.5;
    const cy = particleH * 0.46;
    const maxRadius = Math.min(particleW, particleH) * (particleW < 700 ? 0.62 : 0.54);
    const time = (ts || 0) / 1000;

    ctx.globalCompositeOperation = "lighter";
    for (let i = 0; i < particles.length; i += 1) {
      const p = particles[i];
      const spin = REDUCED ? 0 : time * p.speed;
      const a = p.angle + spin;
      const radius = p.radius * maxRadius;
      const x = cx + Math.cos(a) * radius;
      const y = cy + Math.sin(a) * radius * 0.74;
      const tailA = a - 0.05 - p.depth * 0.07;
      const tx = cx + Math.cos(tailA) * radius * 0.94;
      const ty = cy + Math.sin(tailA) * radius * 0.74;
      const fade = (0.12 + p.depth * 0.66) * (1 - p.radius * 0.9);
      const alpha = Math.max(0, Math.min(0.82, fade));

      ctx.strokeStyle = "hsla(" + p.hue + ", 100%, 78%, " + (alpha * 0.7).toFixed(3) + ")";
      ctx.lineWidth = p.size * 0.55;
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(x, y);
      ctx.stroke();

      ctx.fillStyle = "hsla(" + p.hue + ", 100%, 88%, " + alpha.toFixed(3) + ")";
      ctx.beginPath();
      ctx.arc(x, y, p.size * 0.55, 0, TAU);
      ctx.fill();
    }
    ctx.globalCompositeOperation = "source-over";
  }

  /* ---------- orbit ---------- */

  function layout() {
    const w = stage.clientWidth || window.innerWidth;
    const h = stage.clientHeight || window.innerHeight;
    const radius = Math.min(w, h) * (w < 700 ? 0.37 : 0.34);
    const radiusY = radius * 0.82;
    panels.forEach((el, index) => {
      const a = angle + index * STEP;
      const x = Math.cos(a) * radius;
      const y = Math.sin(a) * radiusY;
      const depth = (Math.sin(a) + 1) / 2;
      const z = (depth - 0.5) * 110;
      const rotY = Math.cos(a) * -26;
      const rotX = 4 + depth * 5;
      const scale = 0.82 + depth * 0.2;
      el.style.transform = `translate(-50%, -50%) translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, ${z.toFixed(2)}px) rotateY(${rotY.toFixed(2)}deg) rotateX(${rotX.toFixed(2)}deg) scale(${scale.toFixed(3)})`;
      el.style.zIndex = String(10 + Math.round(depth * 90));
      if (!el.classList.contains("is-active")) {
        el.style.opacity = (0.55 + depth * 0.45).toFixed(3);
      }
    });
  }

  function aimAngleFor(index) {
    let target = FRONT - index * STEP;
    while (target - angle > Math.PI) target -= TAU;
    while (target - angle < -Math.PI) target += TAU;
    return target;
  }

  function tick(ts) {
    if (!lastTs) lastTs = ts;
    const dt = Math.min((ts - lastTs) / 1000, 0.05);
    lastTs = ts;

    if (mode === "aiming") {
      const progress = Math.min(1, (ts - aimStart) / AIM_MS);
      const eased = 1 - Math.pow(1 - progress, 3);
      angle = aimFrom + (aimTarget - aimFrom) * eased;
      if (progress >= 1) {
        const id = pending;
        pending = null;
        openPanel(id);
      }
    } else if (mode === "spin") {
      angle += SPEED * dt;
    }

    layout();
    drawParticles(ts);
    rafId = requestAnimationFrame(tick);
  }

  function startLoop() {
    if (rafId === null) {
      lastTs = 0;
      rafId = requestAnimationFrame(tick);
    }
  }

  function stopLoop() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  }

  function setPressed(id) {
    panels.forEach((el) => {
      const on = el.dataset.panel === id;
      el.classList.toggle("is-active", on);
      el.setAttribute("aria-expanded", on ? "true" : "false");
      el.style.opacity = on ? "1" : "";
    });
  }

  /* ---------- panel / section ---------- */

  function onPanelPush(el) {
    if (mode !== "spin") return;
    const index = panels.indexOf(el);
    const meta = META[el.dataset.panel];
    if (!meta) return;
    pending = el.dataset.panel;
    aimFrom = angle;
    aimTarget = aimAngleFor(index);
    aimStart = performance.now();
    mode = "aiming";
    setPressed(pending);
  }

  function openPanel(id) {
    const meta = META[id];
    if (!meta) {
      mode = "spin";
      return;
    }
    mode = "open";
    active = id;
    setPressed(id);
    sectionEyebrow.textContent = meta.eyebrow;
    sectionTitle.textContent = meta.title;
    sectionBody.innerHTML = loading("Opening…");
    section.hidden = false;
    void section.offsetWidth;
    section.classList.add("is-open");
    document.body.classList.add("vhub-section-open");
    meta.load(sectionBody);
  }

  function closePanel(immediate) {
    if (section.hidden && mode !== "open") {
      mode = "spin";
      return;
    }
    const was = active;
    active = null;
    mode = "closing";
    section.classList.remove("is-open");
    document.body.classList.remove("vhub-section-open");
    panels.forEach((el) => {
      el.classList.remove("is-active");
      el.setAttribute("aria-expanded", "false");
      el.style.opacity = "";
    });

    const finish = () => {
      section.hidden = true;
      sectionBody.innerHTML = "";
      mode = "spin";
      lastTs = 0;
      if (was) {
        const el = panels.find((panel) => panel.dataset.panel === was);
        if (el && immediate !== true) el.focus({ preventScroll: true });
      }
    };

    if (immediate === true) finish();
    else setTimeout(finish, 540);
  }

  function goToPanel(id) {
    const el = panels.find((panel) => panel.dataset.panel === id);
    if (!el) return;
    if (mode === "open") {
      closePanel();
      setTimeout(() => goToPanel(id), 560);
      return;
    }
    if (mode === "closing" || mode === "aiming") {
      setTimeout(() => goToPanel(id), 560);
      return;
    }
    startLoop();
    pending = id;
    aimFrom = angle;
    aimTarget = aimAngleFor(panels.indexOf(el));
    aimStart = performance.now();
    mode = "aiming";
    setPressed(id);
  }

  function showClassic(view) {
    closePanel(true);
    hub.hidden = true;
    document.body.classList.remove("vhub-open");
    document.body.classList.remove("vhub-section-open");
    stopLoop();
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    const target = view || "mission-command";
    if (typeof window.go === "function") {
      try { window.go(target); } catch { /* classic nav best effort */ }
    }
  }

  function openHub() {
    if (mode === "open" || mode === "closing") closePanel(true);
    hub.hidden = false;
    document.body.classList.add("vhub-open");
    resizeParticles();
    startLoop();
    refreshStatusPill();
  }

  async function refreshStatusPill() {
    if (!statusPill) return;
    const result = await request("/health");
    if (!result.ok) {
      statusPill.textContent = result.status ? `HTTP ${result.status}` : "OFFLINE";
      return;
    }
    const health = result.data || {};
    statusPill.textContent = health.kill_switch
      ? "KILL SWITCH ON"
      : (health.demo_mode ? "DEMO · operational" : "LIVE KEY · operational");
  }

  /* ---------- sections ---------- */

  async function loadAgents(root) {
    root.innerHTML = loading("Reading the table of 15…");
    const result = await request("/api/v1/agents");
    if (!result.ok || !result.data) {
      root.innerHTML = errorBlock(result);
      return;
    }
    const agents = result.data.agents || [];
    root.innerHTML = `
      <div class="vhub-status-grid">
        ${card("agents", String(agents.length), "")}
        ${card("mode", "draft-only", "good")}
        ${card("provider calls", "0", "")}
      </div>
      <div class="vhub-agent-grid">${agents.map((agent) => `
        <article class="vhub-agent">
          <span class="vhub-agent-glyph">${esc(agent.glyph)}</span>
          <div>
            <b>${esc(agent.name)}</b>
            <span>${esc(agent.role)}</span>
            <small>${esc(agent.quote)}</small>
          </div>
        </article>`).join("")}
      </div>
      <p class="hint">Fifteen specialists. Every report is a draft for Wallace approval. No publish, send, or money move.</p>`;
  }

  async function loadLlm(root) {
    root.innerHTML = loading("Reading /health…");
    const result = await request("/health");
    if (!result.ok || !result.data) {
      root.innerHTML = errorBlock(result);
      return;
    }
    const health = result.data || {};
    const metaServed = health.meta_served === true;
    const imageServed = health.image_served === true;
    const kill = health.kill_switch === true;
    root.innerHTML = `
      <div class="vhub-status-grid">
        ${card("meta_served", String(metaServed), metaServed ? "bad" : "good")}
        ${card("image_served", String(imageServed), imageServed ? "bad" : "good")}
        ${card("provider calls", "none", "warn")}
        ${card("demo_mode", String(Boolean(health.demo_mode)), "warn")}
        ${card("draft_only", String(Boolean(health.draft_only)), "good")}
        ${card("kill_switch", String(kill), kill ? "bad" : "good")}
      </div>
      <div class="vhub-note-card">
        <p class="eyebrow">Real status only</p>
        <p>Meta and Muse Image stay <b>false</b> until real provider HTTP 200 content, credits, a key, and Wallace approval. Nothing here is simulated or shown as live.</p>
        <p class="hint">Values above come from <code>/health</code>. No Meta or model call is made by V Hub.</p>
      </div>
      <div class="vhub-note-card">
        <p class="eyebrow">Muse Image creative slot</p>
        <p><b>staged, not generated yet</b></p>
        <p class="hint">The V core scene is drawn live in HTML/CSS as a visual nod to the Flow V look. No video plays here. It is not Muse Image and not an ad creative.</p>
      </div>
      <div class="vhub-links">
        <button class="btn primary" type="button" data-vhub-goto="missions">Run a draft-only mission</button>
        <button class="btn ghost" type="button" data-vhub-goto="kill">Open kill switch</button>
      </div>`;
  }

  async function loadMissions(root) {
    root.innerHTML = `
      <form id="vhub-mission-form" class="form vhub-form">
        <label>Mission sentence
          <input name="sentence" required maxlength="240" value="Launch a dorm-safe candle warmer lamp at $44.99 for solo sellers" />
        </label>
        <div class="row">
          <label>Category
            <select name="category">
              <option value="home">Home &amp; Decor</option>
              <option value="beauty">Beauty</option>
              <option value="fitness">Fitness</option>
              <option value="pet">Pet</option>
              <option value="kitchen">Kitchen</option>
              <option value="tech">Tech</option>
              <option value="fashion">Fashion</option>
              <option value="outdoor">Outdoor</option>
              <option value="baby">Baby</option>
              <option value="office">Office</option>
            </select>
          </label>
          <label>Daily ad budget
            <input name="ad_budget" type="number" min="0" step="1" value="100" />
          </label>
          <label>Unit cost
            <input name="product_cost" type="number" min="0" step="0.01" value="11.40" />
          </label>
        </div>
        <button class="btn primary" type="submit">Run mission</button>
        <p class="hint">Draft-only. No Shopify, no Meta or provider call. Nothing is published, sent, or served.</p>
      </form>
      <div id="vhub-mission-result"></div>`;

    const form = root.querySelector("#vhub-mission-form");
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runHubMission(form, root.querySelector("#vhub-mission-result"), form.querySelector('button[type="submit"]'));
    });
  }

  async function runHubMission(form, out, button) {
    const data = new FormData(form);
    const parsed = parseSentence(data.get("sentence"));
    const payload = {
      product_name: parsed.product || "Unnamed product",
      category: data.get("category"),
      selling_price: parsed.price ?? 44.99,
      product_cost: Number(data.get("product_cost")) || 0,
      ad_budget: Number(data.get("ad_budget")) || 100,
      features: [],
      competitor_url: null,
    };

    button.disabled = true;
    out.innerHTML = loading("Assembling the table…");
    const result = await request("/api/v1/mission", payload);
    button.disabled = false;
    if (!result.ok || !result.data) {
      out.innerHTML = errorBlock(result);
      return;
    }

    const dossier = result.data;
    const coordination = dossier.coordination || {};
    const plan = coordination.plan || [];
    const evidence = coordination.evidence || [];
    const receipt = coordination.receipt || {};
    rememberReceipt(dossier.mission_id);

    out.innerHTML = `
      <div class="vhub-status-grid">
        ${card("mission_id", `<code>${esc(dossier.mission_id || "—")}</code>`, "")}
        ${card("status", esc(coordination.status || "staged_for_approval"), "good")}
        ${card("plan steps", String(plan.length), "")}
        ${card("draft evidence", String(evidence.length), "")}
        ${card("meta_served", String(dossier.meta_served === true), dossier.meta_served ? "bad" : "good")}
        ${card("image_served", String(dossier.image_served === true), dossier.image_served ? "bad" : "good")}
      </div>
      <div class="vhub-note-card">
        <p class="eyebrow">Receipt</p>
        <p><b>${esc(receipt.status || "staged_for_approval")}</b> · ${esc(receipt.id || "issued")}</p>
        <p class="hint">Staged for Wallace approval. No publish, price change, send, provider call, deploy, or money move.</p>
      </div>
      <div class="vhub-links">
        <button class="btn primary" type="button" data-vhub-goto="receipts">Read receipt</button>
        <button class="btn ghost" type="button" data-vhub-goto="ops">Open Live Ops</button>
        <button class="btn ghost" type="button" data-vhub-classic>Open full Mission Command</button>
      </div>`;
  }

  async function loadOps(root) {
    root.innerHTML = loading("Reading the floor…");
    const result = await request("/api/v1/ops");
    if (!result.ok || !result.data) {
      root.innerHTML = errorBlock(result);
      return;
    }
    const ops = result.data;
    const campaigns = ops.campaigns || {};
    const pricing = ops.pricing || {};
    const viral = ops.viral || {};
    root.innerHTML = `
      <div class="vhub-status-grid">
        ${card("product", esc(ops.product || "—"), "")}
        ${card("blended ROAS", Number(campaigns.blended_roas || 0).toFixed(2) + "x", "")}
        ${card("spend", money(campaigns.spend_today), "")}
        ${card("revenue", money(campaigns.revenue_today), "")}
        ${card("suggested price", money(pricing.suggested_price), "")}
        ${card("viral velocity", String(viral.total_velocity ?? "—"), "")}
      </div>
      <div class="vhub-note-card">
        <p class="eyebrow">Support queue</p>
        <ul class="queue">${(ops.queue || []).map((item) => `
          <li><b>${esc(item.from)}</b> · <span class="tag">${esc(item.intent)}</span><br>${esc(item.preview)}<br><small>${esc(item.age)}</small></li>`).join("") || "<li>No queue items.</li>"}
        </ul>
      </div>
      <p class="hint">Draft read only. No campaign budget changed, no price applied, no message sent.</p>
      <div class="vhub-links">
        <button class="btn ghost" type="button" data-vhub-classic="ops">Open classic Live Ops</button>
      </div>`;
  }

  async function loadReceipts(root) {
    root.innerHTML = `
      <div class="vhub-note-card">
        <p class="eyebrow">Read a receipt</p>
        <form id="vhub-receipt-form" class="form vhub-form">
          <label>Mission ID
            <input name="mission_id" placeholder="paste a staged mission_id" required />
          </label>
          <button class="btn primary" type="submit">Read receipt</button>
        </form>
      </div>
      <div id="vhub-receipt-list"></div>`;

    const list = root.querySelector("#vhub-receipt-list");
    root.querySelector("#vhub-receipt-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const id = String(new FormData(event.target).get("mission_id") || "").trim();
      if (!id) return;
      rememberReceipt(id);
      await renderReceiptList(list);
    });
    await renderReceiptList(list);
  }

  async function renderReceiptList(list) {
    const ids = knownMissionIds();
    if (!ids.length) {
      list.innerHTML = `
        <div class="vhub-note-card">
          <p class="eyebrow">No receipts yet</p>
          <p>Run a draft-only mission to stage one for Wallace approval.</p>
          <div class="vhub-links">
            <button class="btn primary" type="button" data-vhub-goto="missions">Run a mission</button>
          </div>
        </div>`;
      return;
    }

    list.innerHTML = loading("Reading staged receipts…");
    const results = await Promise.all(ids.slice(0, 12).map(async (id) => ({
      id,
      result: await request(`/api/v1/receipt/${encodeURIComponent(id)}`),
    })));

    list.innerHTML = results.map(({ id, result }) => {
      if (!result.ok || !result.data) {
        return `<div class="vhub-receipt">
          <div class="vhub-receipt-top"><code>${esc(id)}</code><span class="tag kill">${result.status === 404 ? "not found" : "HTTP " + result.status}</span></div>
          <small>Receipt not available from this server session. Run the mission again, or paste a current mission_id.</small>
        </div>`;
      }
      const receipt = result.data;
      const plan = receipt.plan || [];
      const evidence = receipt.evidence || [];
      const approval = (receipt.approvals || [])[0] || {};
      return `<div class="vhub-receipt">
        <div class="vhub-receipt-top"><code>${esc(receipt.receipt_id || id)}</code><span class="tag LAUNCH">${esc(receipt.status || "staged")}</span></div>
        <div class="vhub-status-grid">
          ${card("plan", plan.length + " steps", "")}
          ${card("evidence", evidence.length + " items", "")}
          ${card("meta_served", String(receipt.meta_served === true), receipt.meta_served ? "bad" : "good")}
          ${card("image_served", String(receipt.image_served === true), receipt.image_served ? "bad" : "good")}
          ${card("kill_switch", String(receipt.kill_switch === true), receipt.kill_switch ? "bad" : "good")}
          ${card("approval", esc(approval.status || "pending"), "warn")}
        </div>
        <small>Staged for Wallace approval. No publish, price change, send, provider call, deploy, or money move.</small>
      </div>`;
    }).join("");
  }

  async function loadKill(root) {
    root.innerHTML = loading("Reading Aegis Gate…");
    const result = await request("/health");
    if (!result.ok || !result.data) {
      root.innerHTML = errorBlock(result);
      return;
    }
    renderKillPanel(root, result.data.kill_switch === true);
  }

  function renderKillPanel(root, engaged) {
    root.innerHTML = `
      <div class="vhub-kill ${engaged ? "is-on" : ""}">
        <div>
          <p class="eyebrow">Kill switch</p>
          <h3>${engaged ? "ENGAGED" : "OFF"}</h3>
          <p class="hint">${engaged
            ? "Tools and model/provider calls are stopped. Release to restore draft-only tools; live actions remain blocked."
            : "Draft tools allowed. Live actions stay blocked."}</p>
        </div>
        <button class="vhub-kill-btn ${engaged ? "is-on" : ""}" id="vhub-kill-toggle" type="button">${engaged ? "Release draft tools" : "Engage kill switch"}</button>
      </div>
      <div class="vhub-note-card">
        <p class="eyebrow">Real state</p>
        <p>Current state is read from <code>/health</code> and changed with <code>POST /api/v1/kill-switch</code>. No simulated status is shown.</p>
      </div>`;

    const button = root.querySelector("#vhub-kill-toggle");
    button.addEventListener("click", async () => {
      button.disabled = true;
      const result = await request("/api/v1/kill-switch", { engage: !engaged });
      button.disabled = false;
      if (!result.ok || !result.data) {
        button.insertAdjacentHTML("afterend", `<p class="hint">Kill switch request failed · HTTP ${result.status}</p>`);
        return;
      }
      renderKillPanel(root, result.data.kill_switch === true);
      refreshStatusPill();
    });
  }

  /* ---------- wiring ---------- */

  panels.forEach((el) => {
    el.setAttribute("aria-expanded", "false");
    el.addEventListener("click", () => onPanelPush(el));
  });

  sectionHead.addEventListener("click", (event) => {
    if (event.target.closest("#vhub-close")) return;
    closePanel();
  });
  closeButton.addEventListener("click", (event) => {
    event.stopPropagation();
    closePanel();
  });
  section.addEventListener("click", (event) => {
    if (event.target === section) closePanel();
  });

  sectionBody.addEventListener("click", (event) => {
    const goto = event.target.closest("[data-vhub-goto]");
    if (goto) {
      event.preventDefault();
      goToPanel(goto.dataset.vhubGoto);
      return;
    }
    const classic = event.target.closest("[data-vhub-classic]");
    if (classic) {
      event.preventDefault();
      showClassic(classic.getAttribute("data-vhub-classic") || "mission-command");
    }
  });

  document.getElementById("nav-vhub")?.addEventListener("click", (event) => {
    event.preventDefault();
    openHub();
  });
  document.getElementById("vhub-classic")?.addEventListener("click", (event) => {
    event.preventDefault();
    showClassic("mission-command");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && mode === "open") closePanel();
  });

  window.addEventListener("resize", () => {
    resizeParticles();
    layout();
  });

  document.body.classList.add("vhub-open");
  setupParticles();
  layout();
  startLoop();
  refreshStatusPill();
})();
