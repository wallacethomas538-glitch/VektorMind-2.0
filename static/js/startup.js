/* VektorMind 2.0 — Flow V startup.
 * Plays the exact Flow V startup video once (731245344_1793131062986620.mp4),
 * loops its hum independently, then reveals V Hub. The video is not a backdrop:
 * it is removed after startup, and V Hub itself is the look from then on.
 * The mute control lives in the top bar and only affects the hum.
 */
(function () {
  "use strict";

  const hub = document.getElementById("vhub");
  const startup = document.getElementById("vhub-startup");
  const video = document.getElementById("vhub-startup-video");
  const hum = document.getElementById("vhub-hum");
  const toggles = Array.from(document.querySelectorAll("[data-hum-toggle]"));
  const MUTE_KEY = "vhub-hum-muted";
  const FALLBACK_MS = 8600;

  let muted = false;
  try { muted = localStorage.getItem(MUTE_KEY) === "1"; } catch { /* storage unavailable */ }
  let finished = false;

  function renderToggles() {
    toggles.forEach((button) => {
      button.textContent = muted ? "Hum off" : "Hum on";
      button.classList.toggle("is-muted", muted);
      button.setAttribute("aria-pressed", muted ? "true" : "false");
      button.setAttribute("aria-label", muted ? "Bring the hum back" : "Mute the hum");
      button.title = muted ? "Bring the hum back" : "Mute the hum";
    });
  }

  function playHum() {
    if (!hum || muted) return;
    const attempt = hum.play();
    if (attempt && typeof attempt.catch === "function") attempt.catch(() => { /* needs a gesture */ });
  }

  function setMuted(next) {
    muted = next;
    try { localStorage.setItem(MUTE_KEY, muted ? "1" : "0"); } catch { /* storage unavailable */ }
    if (hum) {
      if (muted) hum.pause();
      else playHum();
    }
    renderToggles();
  }

  toggles.forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      setMuted(!muted);
    });
  });

  renderToggles();
  playHum();

  ["pointerdown", "keydown", "touchstart"].forEach((name) => {
    window.addEventListener(name, playHum, { once: true, passive: true });
  });

  function finishStartup(instant) {
    if (finished) return;
    finished = true;
    if (!startup) {
      if (hub) hub.classList.remove("is-starting");
      return;
    }
    if (instant) {
      if (hub) hub.classList.remove("is-starting");
      startup.hidden = true;
      if (video) video.pause();
      return;
    }
    startup.classList.add("is-done");
    window.setTimeout(() => {
      if (hub) hub.classList.remove("is-starting");
      startup.hidden = true;
      if (video) video.pause();
    }, 950);
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    finishStartup(true);
    return;
  }

  if (!video) {
    finishStartup(true);
    return;
  }

  video.addEventListener("ended", () => finishStartup(), { once: true });
  video.addEventListener("error", () => finishStartup(true), { once: true });

  const attempt = video.play();
  if (attempt && typeof attempt.catch === "function") {
    attempt.catch(() => { /* keep the fallback timer */ });
  }
  window.setTimeout(finishStartup, FALLBACK_MS);
})();
