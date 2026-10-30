/* VektorMind 2.0 — Mission Command view.
 * New work: one-sentence brief -> live /api/v1/mission -> plan, evidence,
 * Pivot replan, Aegis Gate, Wallace approval, receipt, kill-switch probe.
 * Draft-only. No Shopify, no VektorFlow15xr, no Meta/provider call.
 */
(function () {
  const $ = (sel) => document.querySelector(sel);

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function money(value) {
    const n = Number(value);
    return Number.isFinite(n) ? "$" + n.toFixed(2) : "—";
  }

  const mc = {
    killSwitch: false,
    payload: null,
    mission: null,
    busy: false,
  };

  const CACHE_KEY = "vm2-mission-command";

  function parseSentence(sentence) {
    const text = String(sentence || "").trim().replace(/\s+/g, " ").replace(/[.!?]+$/, "");
    let product = text.replace(/^(launch|sell|test|source|build|find|validate|scale|ship)\s+(a|an|the)?\s*/i, "");
    product = product.replace(/\s+(at|for|to)\s+.*$/i, "").trim();
    if (!product) product = text;
    product = product.slice(0, 160);
    const priceMatch = text.match(/\$\s*(\d+(?:\.\d{1,2})?)/);
    return {
      product,
      price: priceMatch ? Number(priceMatch[1]) : null,
      sentence: text.slice(0, 240),
    };
  }

  function currentPrice() {
    const parsed = parseSentence($("#mc-sentence").value);
    return parsed.price ?? 44.99;
  }

  function refreshPreview() {
    const parsed = parseSentence($("#mc-sentence").value);
    $("#mc-product").textContent = parsed.product || "—";
    $("#mc-price").textContent = money(parsed.price ?? 44.99);
  }

  function buildPayload() {
    const parsed = parseSentence($("#mc-sentence").value);
    return {
      product_name: parsed.product || "Unnamed product",
      category: $("#mc-category").value,
      selling_price: parsed.price ?? 44.99,
      product_cost: Number($("#mc-cost").value) || 0,
      ad_budget: Number($("#mc-budget").value) || 100,
      features: [],
      competitor_url: null,
    };
  }

  async function call(path, body) {
    const opts = body
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
      : { method: "GET" };
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch { /* non-JSON body */ }
    return { ok: res.ok, status: res.status, data };
  }

  function statusLine(kind, text) {
    return `<p class="mc-status mc-status-${kind}">${esc(text)}</p>`;
  }

  function renderPlan(coordination) {
    const plan = coordination.plan || [];
    $("#mc-plan-title").textContent =
      `${plan.length} steps · ${coordination.planner || "dynamic planning"}`;
    $("#mc-plan").innerHTML = plan.map((step) => {
      const isPivot = step.agent_id === "pivot";
      const attempts = (step.attempts || []).map((attempt) =>
        `<span class="mc-attempt ${esc(attempt.status)}">attempt ${attempt.attempt} · ${esc(attempt.status)}</span>`
      ).join("");
      return `
        <li class="mc-step ${esc(step.status)}${isPivot ? " is-pivot" : ""}">
          <span class="mc-num">${String(step.step).padStart(2, "0")}</span>
          <span class="mc-step-body">
            <b>${esc(step.agent)}</b>
            <em>${esc(step.task)}</em>
            <small>depends on: ${esc((step.depends_on || []).join(", ") || "none")} · external calls ${step.external_calls}</small>
            ${attempts ? `<span class="mc-attempts">${attempts}</span>` : ""}
            ${isPivot ? `<small class="mc-replan">replan → ${esc(step.replan?.strategy || "local_intelligence")} · provider contacted ${step.replan?.provider_contacted ? "true" : "false"}</small>` : ""}
          </span>
          <span class="tag ${esc(step.status)}">${esc(step.status)}</span>
        </li>`;
    }).join("");
  }

  function renderEvidence(coordination) {
    const evidence = coordination.evidence || [];
    $("#mc-evidence-title").textContent =
      `${evidence.length} draft reports · provider_contacted false`;
    $("#mc-evidence").innerHTML = evidence.map((item) => `
      <li class="mc-evidence-item ${esc(item.status)}">
        <span class="mc-evidence-head">
          <b>${esc(item.agent)}</b>
          <span class="tag ${esc(item.status)}">${esc(item.status)}</span>
        </span>
        <span>${esc(item.finding)}</span>
        <small>${esc(item.kind)} · external calls ${item.external_calls}</small>
      </li>`).join("");
  }

  function renderGate(coordination) {
    const gate = coordination.aegis_gate || {};
    const risk = coordination.risk || {};
    const approval = (coordination.approvals || [])[0] || {};
    $("#mc-gate").innerHTML = `
      <div class="mc-gate-row">
        <span class="tag ${gate.allowed ? "LAUNCH" : "KILL"}">${gate.allowed ? "gate passed" : "gate blocked"}</span>
        <span class="mc-mono">mode ${esc(gate.mode)} · risk ${esc(gate.risk_score)}/10</span>
      </div>
      <p>${esc(gate.recovery_plan)}</p>
      <div class="cards mc-cards">
        <div class="stat"><span>External calls</span><strong>${esc(risk.external_calls)}</strong></div>
        <div class="stat"><span>Money moved</span><strong>${risk.money_moved ? "true" : "false"}</strong></div>
        <div class="stat"><span>Reversible</span><strong>${risk.reversible ? "yes" : "no"}</strong></div>
      </div>
      <div class="mc-approval">
        <span class="mc-mono">approval</span>
        <b>${esc(approval.approver || "Wallace")}</b>
        <span class="tag maintain">${esc(approval.status || "pending")}</span>
        <p class="hint">${esc(approval.scope || "")}</p>
      </div>`;
  }

  function renderReceipt(receipt) {
    const plan = receipt.plan || [];
    const evidence = receipt.evidence || [];
    const approvals = receipt.approvals || [];
    const pending = approvals.filter((a) => a.status === "pending").length;
    const approved = receipt.status === "approved";
    $("#mc-receipt").innerHTML = `
      <div class="mc-kv"><span>mission_id</span><code>${esc(receipt.mission_id)}</code></div>
      <div class="mc-kv"><span>receipt_id</span><code>${esc(receipt.receipt_id)}</code></div>
      <div class="mc-kv"><span>status</span><b>${esc(receipt.status)}</b></div>
      <div class="mc-kv"><span>plan</span><b>${plan.length} steps</b></div>
      <div class="mc-kv"><span>evidence</span><b>${evidence.length} draft items</b></div>
      <div class="mc-kv"><span>meta_served</span><b class="${receipt.meta_served ? "bad" : "good"}">${String(receipt.meta_served)}</b></div>
      <div class="mc-kv"><span>image_served</span><b class="${receipt.image_served ? "bad" : "good"}">${String(receipt.image_served)}</b></div>
      <div class="mc-kv"><span>kill_switch</span><b>${String(receipt.kill_switch)}</b></div>
      <div class="mc-kv"><span>persistence</span><b>${esc(receipt.persistence?.status || "unconfigured")}</b></div>
      <div class="mc-kv"><span>approvals</span><b>${approved ? `approved by ${esc(receipt.approved_by || "Wallace")}` : `${pending} pending`}</b></div>
      ${approved
        ? `<p class="hint">Approved by Wallace. Drafts stay draft-only — nothing was published, sent, or served.</p>`
        : `<button class="btn primary" type="button" id="mc-approve" data-mission="${esc(receipt.mission_id)}" style="width:100%;margin-top:12px;padding:14px;font-size:16px;">Approve mission</button>
           <p class="hint">Staged for Wallace approval. Approving records your decision only — no publish, price change, send, provider call, deploy, or money move.</p>`}`;
    const approveBtn = $("#mc-approve");
    if (approveBtn) {
      approveBtn.addEventListener("click", () => approveMission(approveBtn.dataset.mission, approveBtn));
    }
  }

  async function approveMission(missionId, button) {
    if (mc.busy) return;
    mc.busy = true;
    button.disabled = true;
    button.textContent = "Approving…";
    try {
      const result = await call(`/api/v1/receipt/${encodeURIComponent(missionId)}/approve`, {});
      if (result.ok) {
        renderReceipt(result.data);
        try {
          const cached = JSON.parse(sessionStorage.getItem(CACHE_KEY) || "null");
          if (cached) {
            cached.receipt = result.data;
            sessionStorage.setItem(CACHE_KEY, JSON.stringify(cached));
          }
        } catch { /* cache is best-effort */ }
      } else {
        button.disabled = false;
        button.textContent = "Approve mission";
        $("#mc-receipt").insertAdjacentHTML("beforeend", statusLine("bad", `Approval failed · HTTP ${result.status}`));
      }
    } catch (err) {
      button.disabled = false;
      button.textContent = "Approve mission";
      $("#mc-receipt").insertAdjacentHTML("beforeend", statusLine("bad", `Approval failed · ${esc(err.message)}`));
    } finally {
      mc.busy = false;
    }
  }

  async function runMission() {
    if (mc.busy) return;
    mc.busy = true;
    const button = $("#mc-go");
    button.disabled = true;
    const payload = buildPayload();
    mc.payload = payload;

    $("#mc-plan-title").textContent = "Assembling the table…";
    $("#mc-receipt").innerHTML = '<p class="hint">Waiting for the mission to stage…</p>';
    $("#mc-gate").innerHTML = '<p class="hint">Gate evaluates after the plan executes.</p>';

    try {
      const result = await call("/api/v1/mission", payload);
      if (!result.ok) {
        const detail = result.data?.detail;
        const message = typeof detail === "string"
          ? detail
          : `${detail?.error || "mission_failed"} — ${detail?.message || result.status}`;
        $("#mc-plan-title").textContent = `Blocked · HTTP ${result.status}`;
        $("#mc-plan").innerHTML = `<li class="mc-step">${statusLine("bad", message)}</li>`;
        $("#mc-evidence").innerHTML = "";
        $("#mc-evidence-title").textContent = "No evidence";
        $("#mc-gate").innerHTML = statusLine("bad", `Aegis Gate blocked · HTTP ${result.status}`);
        $("#mc-receipt").innerHTML = statusLine("bad", "No receipt issued.");
        return;
      }

      mc.mission = result.data;
      const coordination = result.data.coordination || {};
      renderPlan(coordination);
      renderEvidence(coordination);
      renderGate(coordination);

      const receiptResult = await call(`/api/v1/receipt/${encodeURIComponent(result.data.mission_id)}`);
      if (receiptResult.ok) {
        renderReceipt(receiptResult.data);
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({
          mission: result.data,
          receipt: receiptResult.data,
        }));
      } else {
        $("#mc-receipt").innerHTML = statusLine("bad", `Receipt unavailable · HTTP ${receiptResult.status}`);
      }
    } catch (err) {
      $("#mc-plan-title").textContent = "Table fault";
      $("#mc-plan").innerHTML = `<li class="mc-step">${statusLine("bad", err.message)}</li>`;
    } finally {
      mc.busy = false;
      button.disabled = false;
    }
  }

  function paintKillSwitch() {
    const button = $("#mc-kill");
    button.textContent = `Kill switch: ${mc.killSwitch ? "ON" : "OFF"}`;
    button.classList.toggle("mc-armed", mc.killSwitch);
    button.setAttribute("aria-pressed", mc.killSwitch ? "true" : "false");
  }

  async function probeMission() {
    const result = await call("/api/v1/mission", { product_name: "kill-switch probe" });
    if (result.status === 503) {
      $("#mc-kill-msg").textContent = "Mission endpoint 503 · kill_switch_engaged";
    } else if (result.ok) {
      $("#mc-kill-msg").textContent = "Mission endpoint 200 · draft tools allowed";
    } else {
      $("#mc-kill-msg").textContent = `Mission endpoint ${result.status}`;
    }
    return result.status;
  }

  async function toggleKillSwitch() {
    const button = $("#mc-kill");
    button.disabled = true;
    try {
      const result = await call("/api/v1/kill-switch", { engage: !mc.killSwitch });
      if (!result.ok) {
        $("#mc-kill-msg").textContent = `Kill switch request failed · HTTP ${result.status}`;
        return;
      }
      mc.killSwitch = Boolean(result.data.kill_switch);
      paintKillSwitch();
      await probeMission();
    } catch (err) {
      $("#mc-kill-msg").textContent = err.message;
    } finally {
      button.disabled = false;
    }
  }

  async function loadHealth() {
    try {
      const result = await call("/health");
      if (result.ok) {
        mc.killSwitch = Boolean(result.data.kill_switch);
        paintKillSwitch();
        $("#mc-health-pill").textContent = result.data.demo_mode ? "DEMO · operational" : "LIVE KEY · operational";
        $("#mc-kill-msg").textContent = mc.killSwitch
          ? "Kill switch engaged. Draft tools blocked."
          : "Draft tools allowed.";
      } else {
        $("#mc-health-pill").textContent = `HTTP ${result.status}`;
      }
    } catch (err) {
      $("#mc-health-pill").textContent = "OFFLINE";
    }
  }

  function restoreCache() {
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (!cached) return;
    try {
      const parsed = JSON.parse(cached);
      if (!parsed?.mission?.coordination) return;
      mc.mission = parsed.mission;
      renderPlan(parsed.mission.coordination);
      renderEvidence(parsed.mission.coordination);
      renderGate(parsed.mission.coordination);
      if (parsed.receipt) renderReceipt(parsed.receipt);
    } catch { /* ignore cache */ }
  }

  function init() {
    const form = $("#mc-form");
    if (!form) return;
    refreshPreview();
    $("#mc-sentence").addEventListener("input", refreshPreview);
    $("#mc-kill").addEventListener("click", toggleKillSwitch);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runMission();
    });
    loadHealth();
    restoreCache();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
