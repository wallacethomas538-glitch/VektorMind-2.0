const state = {
  agents: [],
  mission: null,
  view: "command",
  agent: null,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : { method: "GET" };
  const res = await fetch(path, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

function money(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "—";
  return (v < 0 ? "-" : "") + "$" + Math.abs(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}
function money2(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "—";
  return "$" + v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function show(view) {
  state.view = view;
  $$(".view").forEach((el) => el.classList.toggle("is-on", el.id === `view-${view}`));
  $$(".top-nav button").forEach((btn) => btn.classList.toggle("is-on", btn.dataset.nav === view));
  if (view !== "agent") {
    $$(".roster li").forEach((li) => li.classList.remove("is-on"));
  }
}

function go(view) {
  show(view);
  if (view === "ops") loadOps();
  if (view === "dossier" && state.mission) renderDossier(state.mission);
}

function boot() {
  const seen = sessionStorage.getItem("vf-booted");
  const overlay = $("#boot");
  if (seen) {
    overlay.hidden = true;
    return;
  }
  overlay.hidden = false;
  const lines = [
    "Linking Hawk… product desk live",
    "Smaug opening supplier books",
    "Architect drafting the floor",
    "DaVinci warming the studio",
    "Rook taking the buy desk",
    "Aegis on the door",
    "Arbiter reading the tape",
    "Sentinel sealing the vault",
    "Echo at the booth",
    "ViralDet watching the spike",
    "Shadow inside the other store",
    "Bundler stacking the kit",
    "Pivot lifting one-star copy",
    "Oracle looking 30 days out",
    "Cerebrum has the table",
  ];
  let i = 0;
  const tick = () => {
    $("#boot-line").textContent = lines[Math.min(i, lines.length - 1)];
    $("#boot-fill").style.width = `${((i + 1) / lines.length) * 100}%`;
    i += 1;
    if (i < lines.length) setTimeout(tick, 90);
    else {
      sessionStorage.setItem("vf-booted", "1");
      setTimeout(() => { overlay.hidden = true; }, 280);
    }
  };
  tick();
}

function renderRoster() {
  const roster = $("#roster");
  const grid = $("#agent-grid");
  roster.innerHTML = state.agents.map((a) => `
    <li data-agent="${a.id}">
      <span class="g">${a.glyph}</span>
      <span><b>${esc(a.name)}</b><em>${esc(a.role)}</em></span>
      <span class="dot" title="online"></span>
    </li>`).join("");
  grid.innerHTML = state.agents.map((a) => `
    <article class="agent-tile" data-agent="${a.id}">
      <div>
        <div class="g">${a.glyph} · ONLINE</div>
        <h3>${esc(a.name)}</h3>
      </div>
      <p>${esc(a.role)}</p>
    </article>`).join("");
  $$("[data-agent]").forEach((el) => {
    el.addEventListener("click", () => openAgent(el.dataset.agent));
  });
}

function renderKpis(sys) {
  const k = sys.kpis || {};
  $("#kpi-panel").innerHTML = [
    ["Agents online", k.agents_online ?? 15],
    ["Open missions", k.open_missions ?? 1],
    ["Blended ROAS", (k.blended_roas ?? 0).toFixed(2) + "x"],
    ["Compliance", (k.compliance ?? 0) + "/100"],
  ].map(([l, v]) => `<div class="kpi"><span>${l}</span><strong>${v}</strong></div>`).join("");

  $("#feed").innerHTML = (sys.feed || []).map((f) =>
    `<li><b>${esc(f.agent)}</b><span>${esc(f.text)}</span><time>${esc(f.t)}</time></li>`
  ).join("");

  const items = (sys.feed || []).map((f) => `${f.agent} — ${f.text}`);
  items.push("VEKTORFLOW-15 · Apache 2.0 · Fifteen agents, one decision");
  $("#ticker").innerHTML = `<span>${items.concat(items).map(esc).join("</span><span>")}</span>`;
  if (sys.demo_mode) $("#mode-pill").textContent = "DEMO";
  else $("#mode-pill").textContent = "SECURE";
}

function openAgent(id) {
  const agent = state.agents.find((a) => a.id === id);
  if (!agent) return;
  state.agent = agent;
  show("agent");
  $$(".roster li").forEach((li) => li.classList.toggle("is-on", li.dataset.agent === id));
  $("#agent-station").innerHTML = workstation(agent);
  bindNav($("#agent-station"));
  const form = $("#agent-form");
  if (form) form.addEventListener("submit", (e) => runWorkstation(e, agent));
}

function workstation(agent) {
  const commonName = `<label>Product name<input name="product_name" value="Candle Warmer Lamp" required /></label>`;
  const forms = {
    hawk: `${commonName}<label>Category<input name="category" value="home" /></label><label>Keywords<input name="keywords" value="cozy, halogen, dorm-safe" /></label>`,
    smaug: `${commonName}<label>Target price<input name="target_selling_price" type="number" step="0.01" value="44.99" /></label>`,
    architect: `${commonName}<label>Features<input name="product_features" value="halogen, dimmable" /></label><label>Price<input name="product_price" type="number" step="0.01" value="44.99" /></label>`,
    davinci: `${commonName}<label>Features<input name="product_features" value="halogen, dimmable" /></label><label>Price<input name="product_price" type="number" step="0.01" value="44.99" /></label>`,
    rook: `${commonName}<label>Daily budget<input name="total_daily_budget" type="number" value="200" /></label><p class="hint">Leave campaigns empty and Rook will read the live book.</p>`,
    aegis: `<label>Customer message<textarea name="message" rows="3">Where is my order?</textarea></label>${commonName}`,
    arbiter: `${commonName}<label>Unit cost<input name="product_cost" type="number" step="0.01" value="11.40" /></label><label>Shipping<input name="shipping_cost" type="number" step="0.01" value="5.50" /></label>`,
    sentinel: `<label>Store name<input name="store_name" value="Glow House" /></label><label>Store URL<input name="store_url" value="glowhouse.store" /></label>`,
    echo: `<label>Script<textarea name="text" rows="4">Your dorm says no open flames. This lamp didn't get the memo — it just skipped the fire.</textarea></label><label>Voice<select name="voice_name"><option>Kore</option><option>Puck</option><option>Charon</option><option>Fenrir</option><option>Zephyr</option></select></label>`,
    cerebrum: `<p class="hint">Cerebrum only speaks after a full mission. Launch from the brief, or load the sample.</p>`,
    viral: `${commonName}`,
    shadow: `<label>Competitor URL<input name="competitor_url" value="https://glowhaus.co" /></label>${commonName}`,
    bundler: `<label>Main product<input name="main_product" value="Candle Warmer Lamp" /></label><label>Budget<input name="budget" type="number" value="45" /></label>`,
    pivot: `<label>Competitor product URL<input name="competitor_product_url" value="https://glowhaus.co/lamp" /></label>${commonName}`,
    oracle: `${commonName}<div class="row3"><label>Cost<input name="product_cost" type="number" step="0.01" value="11.40" /></label><label>Price<input name="selling_price" type="number" step="0.01" value="44.99" /></label><label>Ad budget<input name="ad_budget" type="number" value="100" /></label></div><label>Niche<input name="niche" value="home" /></label>`,
  };
  const extra = agent.id === "cerebrum"
    ? `<button class="btn primary" type="button" data-nav="mission">Open mission brief</button>`
    : `<button class="btn primary" type="submit">Run ${esc(agent.name)}</button>`;
  return `
    <div class="station panel">
      <p class="eyebrow">${agent.glyph} · ${esc(agent.role)}</p>
      <h2>${esc(agent.name)}</h2>
      <p class="quote">“${esc(agent.quote)}”</p>
      <form id="agent-form" class="form">${forms[agent.id] || commonName}${extra}</form>
      <div id="agent-result"></div>
    </div>`;
}

function splitList(v) {
  return String(v || "").split(",").map((s) => s.trim()).filter(Boolean);
}

async function runWorkstation(e, agent) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const g = (k) => fd.get(k);
  const num = (k) => Number(g(k));
  const box = $("#agent-result");
  box.innerHTML = `<p class="hint">${agent.name} is on it…</p>`;
  const map = {
    hawk: ["/api/v1/product-description", { name: g("product_name"), category: g("category"), keywords: splitList(g("keywords")) }],
    smaug: ["/api/v1/supplier-finder", { product_name: g("product_name"), target_selling_price: num("target_selling_price") }],
    architect: ["/api/v1/store-builder", { product_name: g("product_name"), product_features: splitList(g("product_features")), product_price: num("product_price") }],
    davinci: ["/api/v1/creative-factory", { product_name: g("product_name"), product_features: splitList(g("product_features")), product_price: num("product_price"), creative_type: "all" }],
    rook: ["/api/v1/ad-manager", { target_roas: 2, total_daily_budget: num("total_daily_budget"), product_name: g("product_name"), campaigns: [] }],
    aegis: ["/api/v1/chatbot", { message: g("message"), product_name: g("product_name") }],
    arbiter: ["/api/v1/dynamic-pricing", { product_name: g("product_name"), product_cost: num("product_cost"), shipping_cost: num("shipping_cost"), competitors: [] }],
    sentinel: ["/api/v1/compliance-audit", { store_name: g("store_name"), store_url: g("store_url") }],
    echo: ["/api/v1/tts/synthesize", { text: g("text"), voice_name: g("voice_name") }],
    viral: ["/api/v1/viral-detector", { product_name: g("product_name") }],
    shadow: ["/api/v1/competitor-shadow", { competitor_url: g("competitor_url"), product_name: g("product_name") }],
    bundler: ["/api/v1/bundle-builder", { main_product: g("main_product"), budget: num("budget") }],
    pivot: ["/api/v1/sentiment-pivot", { competitor_product_url: g("competitor_product_url"), product_name: g("product_name") }],
    oracle: ["/api/v1/profit-predictor", { product_cost: num("product_cost"), selling_price: num("selling_price"), ad_budget: num("ad_budget"), niche: g("niche"), product_name: g("product_name") }],
  };
  const spec = map[agent.id];
  if (!spec) return;
  try {
    const data = await api(spec[0], spec[1]);
    box.innerHTML = renderAgent(agent.id, data);
    if (agent.id === "oracle") drawSeries(data.series);
  } catch (err) {
    box.innerHTML = `<p class="hint">${esc(err.message)}</p>`;
  }
}

function renderAgent(id, d) {
  if (!d) return "";
  const cards = (items) => `<div class="cards">${items.map(([l, v]) => `<div class="stat"><span>${esc(l)}</span><strong>${v}</strong></div>`).join("")}</div>`;
  const note = d.briefing ? `<p class="lede">${esc(d.briefing)}</p>` : "";
  switch (id) {
    case "hawk":
      return note + cards([
        ["Opportunity", d.scores?.opportunity],
        ["Trend", d.scores?.trend],
        ["Competition", d.scores?.competition],
        ["Verdict", `<span class="tag ${d.verdict}">${esc(d.verdict)}</span>`],
      ]) + `<div class="panel" style="margin-top:12px"><h3>${esc(d.seo_title)}</h3><p>${esc(d.description)}</p><ul>${(d.bullets||[]).map(b=>`<li>${esc(b)}</li>`).join("")}</ul></div>`;
    case "smaug":
      return note + `<div class="table-wrap"><table><thead><tr><th>Supplier</th><th>Tier</th><th>Landed</th><th>Margin</th><th>Ship</th><th>Risk</th></tr></thead><tbody>${
        (d.top_suppliers||[]).map(s=>`<tr><td>${esc(s.supplier_name)}<br><small>${esc(s.location)}</small></td><td>${esc(s.tier)}</td><td>${money2(s.landed_cost)}</td><td>${s.margin}%</td><td>${s.shipping_days}d</td><td>${esc(s.risk)}</td></tr>`).join("")
      }</tbody></table></div><p class="hint" style="margin-top:12px">${esc(d.negotiation_script||"")}</p>`;
    case "architect":
      return note + cards([["Brand", esc(d.brand_name)],["Theme", esc(d.theme)],["Price", money2(d.price)],["Blueprint", d.blueprint_score]]) +
        `<div class="panel" style="margin-top:12px"><h3>${esc(d.hero_headline)}</h3><p>${esc(d.hero_subhead)}</p><div class="swatches">${Object.values(d.palette||{}).map(c=>`<span class="swatch" style="background:${c}" title="${c}"></span>`).join("")}</div></div>`;
    case "davinci":
      return note + `<div class="hooks">${(d.hook_variations||[]).map(h=>`<div class="hook"><small>${esc(h.hook_type)} · ${esc(h.platform)} · ${esc(h.estimated_hook_rate)}</small><div>${esc(h.hook_text)}</div></div>`).join("")}</div><pre class="script">${esc((d.video_script||[]).join("\n"))}</pre>`;
    case "rook":
      return note + cards([["Blended ROAS", (d.blended_roas??0).toFixed(2)+"x"],["Spend", money(d.spend_today)],["Revenue", money(d.revenue_today)],["Reallocated", money(d.reallocated_budget)]]) +
        `<div class="table-wrap"><table><thead><tr><th>Campaign</th><th>ROAS</th><th>Action</th><th>New budget</th><th>Why</th></tr></thead><tbody>${
          (d.campaign_actions||[]).map(a=>`<tr><td>${esc(a.campaign_id)} · ${esc(a.platform)}</td><td>${a.roas}x</td><td><span class="tag ${a.action}">${esc(a.action)}</span></td><td>${money2(a.new_budget)}</td><td>${esc(a.reason)}</td></tr>`).join("")
        }</tbody></table></div><p class="quote">${esc(d.rook_quote||"")}</p>`;
    case "aegis":
      if (d.chat) {
        return renderAgent("aegis", d.chat) + renderAgent("aegis", d.review) + renderAgent("aegis", d.cart);
      }
      if (d.sequence) {
        return note + `<div class="hooks">${d.sequence.map(s=>`<div class="hook"><small>T+${s.hour}h</small><div><b>${esc(s.subject)}</b><br>${esc(s.preview)}</div></div>`).join("")}</div>`;
      }
      if (d.sentiment) {
        return `<p><span class="tag ${d.sentiment}">${esc(d.sentiment)}</span> ${(d.confidence*100).toFixed(0)}% · ${esc((d.themes||[]).join(", "))}</p><p>${esc(d.suggested_reply)}</p>`;
      }
      return `<p><span class="tag">${esc(d.intent||"reply")}</span></p><p>${esc(d.reply)}</p>`;
    case "arbiter":
      return note + cards([["Suggested", money2(d.suggested_price)],["Floor", money2(d.floor_price)],["Premium", money2(d.premium_price)],["Gross margin", (d.unit_economics?.gross_margin_pct??"—")+"%"]]) +
        `<p>${esc(d.rationale||"")}</p>`;
    case "sentinel":
      return note + cards([["Score", d.compliance_score],["Status", esc(d.status)],["Region", esc(d.region)]]) +
        `<ul>${(d.checklist||[]).map(c=>`<li>${esc(c.item)} — <small>${esc(c.status)}</small></li>`).join("")}</ul><p class="hint">${esc(d.policy_excerpt||"")}</p>`;
    case "echo":
      return note + cards([["Voice", esc(d.voice)],["Seconds", d.estimated_seconds],["Words", d.word_count]]) + `<p>${esc(d.text)}</p><p class="hint">${esc(d.note)}</p>`;
    case "viral":
      return note + cards([["Velocity", d.total_velocity],["Action", `<span class="tag ${String(d.action).replace(/\s+/g,"").replace("LAUNCHNOW","SURGING")}">${esc(d.action)}</span>`]]) +
        `<div class="hooks">${Object.entries(d.signals||{}).map(([k,v])=>`<div class="hook"><small>${esc(k)}</small><div>${v.velocity} · <span class="tag ${v.trending}">${esc(v.trending)}</span> · ${esc(v.format)}</div></div>`).join("")}</div>`;
    case "shadow":
      return note + `<p>${esc(d.positioning)}</p><ul>${(d.actions||[]).map(a=>`<li>${esc(a)}</li>`).join("")}</ul>`;
    case "bundler":
      return note + `<div class="cards">${(d.bundles||[]).map(b=>`<div class="stat"><span>${esc(b.name)}</span><strong>${money2(b.price)}</strong><p>${esc((b.includes||[]).join(" · "))}<br>${b.margin_pct}% margin · +${b.aov_lift}% AOV</p></div>`).join("")}</div><p>${esc(d.play||"")}</p>`;
    case "pivot":
      return note + `<p>${esc(d.positioning)}</p><div class="hooks">${(d.matrix||[]).map(a=>`<div class="hook"><small>${esc(a.weakness)}</small><div><b>${esc(a.headline)}</b><br>${esc(a.body)}</div></div>`).join("")}</div>`;
    case "oracle":
      return note + cards([
        ["Conservative 30d", money(d.conservative_30day)],
        ["Base 30d", money(d.base_30day)],
        ["Optimistic 30d", money(d.optimistic_30day)],
        ["Break-even", "Day " + d.break_even_day],
      ]) + `<canvas class="chart" id="oracle-chart" width="720" height="180"></canvas>`;
    case "cerebrum":
      return note + cards([["Verdict", `<span class="tag ${d.verdict}">${esc(d.verdict)}</span>`],["Conviction", d.conviction]]) +
        `<p>${esc(d.posture||"")}</p><ul>${(d.priorities||[]).map(p=>`<li>${esc(p)}</li>`).join("")}</ul>`;
    default:
      return `<pre class="script">${esc(JSON.stringify(d, null, 2))}</pre>`;
  }
}

function drawSeries(series) {
  const canvas = $("#oracle-chart");
  if (!canvas || !series?.length) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const vals = series.map((p) => p.profit);
  const min = Math.min(0, ...vals);
  const max = Math.max(0, ...vals);
  const span = max - min || 1;
  const x = (i) => 16 + (i / (vals.length - 1)) * (w - 32);
  const y = (v) => h - 16 - ((v - min) / span) * (h - 32);
  ctx.strokeStyle = "#232b38";
  ctx.beginPath();
  ctx.moveTo(16, y(0));
  ctx.lineTo(w - 16, y(0));
  ctx.stroke();
  ctx.beginPath();
  vals.forEach((v, i) => (i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v))));
  ctx.strokeStyle = "#3ee0c5";
  ctx.lineWidth = 2;
  ctx.stroke();
  const last = vals[vals.length - 1];
  ctx.fillStyle = last >= 0 ? "#3ee0c5" : "#ff6b7a";
  ctx.beginPath();
  ctx.arc(x(vals.length - 1), y(last), 3.5, 0, Math.PI * 2);
  ctx.fill();
}

function renderDossier(mission) {
  const wrap = $("#dossier");
  if (!mission) {
    wrap.className = "dossier empty";
    wrap.innerHTML = `<div class="empty-state"><p class="eyebrow">Dossier</p><h2>No mission on the table</h2><p>Launch a product or load the sample Candle Warmer Lamp read.</p><button class="btn primary" data-nav="mission">Launch</button></div>`;
    bindNav(wrap);
    return;
  }
  wrap.className = "dossier";
  const p = mission.product || {};
  const agents = mission.agents || {};
  const tabs = Object.keys(agents);
  wrap.innerHTML = `
    <div class="verdict">
      <p class="eyebrow">${esc(mission.mission_id)} · ${esc(p.niche_label || p.niche || "")}</p>
      <h1>${esc(mission.verdict)} the ${esc(p.name || "offer")}</h1>
      <p class="lede">${esc(mission.briefing)}</p>
      <div class="cards" style="margin-top:16px">
        <div class="stat"><span>Conviction</span><strong>${mission.conviction}</strong></div>
        <div class="stat"><span>Price</span><strong>${money2(p.price)}</strong></div>
        <div class="stat"><span>Opportunity</span><strong>${p.opportunity}</strong></div>
        <div class="stat"><span>30-day base</span><strong>${money(agents.oracle?.base_30day)}</strong></div>
      </div>
    </div>
    <div class="dossier-head">
      <div>
        <p class="eyebrow">Agent reports</p>
        <h2>Full table read</h2>
      </div>
      <div>
        <button class="btn ghost tiny" id="dl-json">Export JSON</button>
        <button class="btn ghost tiny" onclick="window.print()">Print</button>
      </div>
    </div>
    <div class="tabs" id="dos-tabs">${tabs.map((t,i)=>`<button data-tab="${t}" class="${i===0?"is-on":""}">${esc(agents[t].agent || t)}</button>`).join("")}</div>
    <div class="report panel" id="dos-report">${renderAgent(tabs[0], agents[tabs[0]])}</div>
  `;
  if (tabs[0] === "oracle") drawSeries(agents.oracle.series);
  $$("#dos-tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      $$("#dos-tabs button").forEach((b) => b.classList.remove("is-on"));
      btn.classList.add("is-on");
      const key = btn.dataset.tab;
      $("#dos-report").innerHTML = renderAgent(key, agents[key]);
      if (key === "oracle") drawSeries(agents[key].series);
    });
  });
  $("#dl-json")?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(mission, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${mission.mission_id || "vektorflow"}-dossier.json`;
    a.click();
  });
}

async function runMission(payload) {
  const list = $("#exec-list");
  const order = state.agents.length ? state.agents : [];
  list.innerHTML = order.map((a) =>
    `<li data-ex="${a.id}"><span class="mark"></span><span class="who">${a.name}</span><span>Queued</span></li>`
  ).join("");
  $("#exec-title").textContent = "Cerebrum assembling";
  $("#exec-sub").textContent = "The table is waking in order. Do not touch the brief.";
  $("#mission-go").disabled = true;
  try {
    const data = await api("/api/v1/mission", payload);
    state.mission = data;
    sessionStorage.setItem("vf-mission", JSON.stringify(data));
    const keys = ["hawk","smaug","architect","davinci","rook","aegis","arbiter","sentinel","echo","cerebrum","viral","shadow","bundler","pivot","oracle"];
    for (let i = 0; i < keys.length; i++) {
      await wait(140);
      const row = list.querySelector(`[data-ex="${keys[i]}"]`);
      if (!row) continue;
      row.classList.add("on");
      const agentData = data.agents?.[keys[i]];
      row.lastElementChild.textContent = agentData?.briefing || "Reported.";
    }
    $("#exec-title").textContent = `${data.verdict} · conviction ${data.conviction}`;
    $("#exec-sub").textContent = data.briefing;
    renderDossier(data);
    await wait(400);
    go("dossier");
  } catch (err) {
    $("#exec-title").textContent = "Table fault";
    $("#exec-sub").textContent = err.message;
  } finally {
    $("#mission-go").disabled = false;
  }
}

function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function loadSample() {
  await runMission({
    product_name: "Candle Warmer Lamp",
    category: "home",
    features: ["halogen", "dimmable", "dorm-safe"],
    keywords: ["cozy", "halogen"],
    selling_price: 44.99,
    product_cost: 11.4,
    ad_budget: 100,
    competitor_url: "https://glowhaus.co",
  });
}

async function loadOps() {
  const board = $("#ops-board");
  board.innerHTML = `<p class="hint">Reading the floor…</p>`;
  try {
    const data = await api("/api/v1/ops");
    board.innerHTML = `
      <div class="panel">
        <p class="eyebrow">Rook</p>
        <h3>Campaign book · ${esc(data.product)}</h3>
        ${renderAgent("rook", data.campaigns)}
      </div>
      <div class="ops-grid">
        <div class="panel">
          <p class="eyebrow">Arbiter</p>
          <h3>Price tape</h3>
          ${renderAgent("arbiter", data.pricing)}
        </div>
        <div class="panel">
          <p class="eyebrow">Aegis</p>
          <h3>Support queue</h3>
          <ul class="queue">${(data.queue||[]).map(q=>`<li><b>${esc(q.from)}</b> · <span class="tag">${esc(q.intent)}</span><br>${esc(q.preview)}<br><small>${esc(q.age)}</small></li>`).join("")}</ul>
        </div>
      </div>
      <div class="panel">
        <p class="eyebrow">ViralDet</p>
        <h3>Heat</h3>
        ${renderAgent("viral", data.viral)}
      </div>`;
  } catch (err) {
    board.innerHTML = `<p class="hint">${esc(err.message)}</p>`;
  }
}

function bindNav(root = document) {
  $$("[data-nav]", root).forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      go(el.dataset.nav);
    });
  });
}

function clock() {
  const el = $("#clock");
  const tick = () => {
    el.textContent = new Date().toISOString().slice(11, 19) + " UTC";
  };
  tick();
  setInterval(tick, 1000);
}

async function init() {
  boot();
  clock();
  bindNav();
  $("#btn-sample")?.addEventListener("click", loadSample);
  $("#ops-refresh")?.addEventListener("click", loadOps);
  $("#mission-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    runMission({
      product_name: fd.get("product_name"),
      category: fd.get("category"),
      brand_name: fd.get("brand_name") || null,
      features: splitList(fd.get("features")),
      selling_price: Number(fd.get("selling_price")),
      product_cost: Number(fd.get("product_cost")),
      ad_budget: Number(fd.get("ad_budget")),
      competitor_url: fd.get("competitor_url"),
    });
  });
  try {
    const sys = await api("/api/v1/system");
    state.agents = sys.agents || [];
    renderRoster();
    renderKpis(sys);
    $("#exec-list").innerHTML = state.agents.map((a) =>
      `<li data-ex="${a.id}"><span class="mark"></span><span class="who">${a.name}</span><span>Standing by</span></li>`
    ).join("");
  } catch (err) {
    $("#kpi-panel").innerHTML = `<div class="kpi"><span>System</span><strong>Offline</strong></div>`;
  }
  const cached = sessionStorage.getItem("vf-mission");
  if (cached) {
    try {
      state.mission = JSON.parse(cached);
      renderDossier(state.mission);
    } catch { /* ignore */ }
  }
}

init();
