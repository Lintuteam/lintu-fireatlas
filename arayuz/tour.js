/* Lintu: maskotla adım adım kullanım turu. Her adım bir öğeyi vurgular, gerekirse sekme değiştirir.
   Metinler i18n'den (tour.s1 … tour.s11). İlk açılışta bir kez kendiliğinden başlar. */
"use strict";
const TOUR = (() => {
  const STEPS = [
    { sel: null, corner: true, k: "tour.a1", pose: "lintu_selam" },
    { sel: "#solStrip", k: "tour.a2", pose: "lintu_sun" },
    { sel: ".cards", k: "tour.a3", pose: "lintu_goster" },
    { sel: "#sciModeBtn", k: "tour.a4", pose: "lintu_fikir" },
    { sel: ".filters", k: "tour.a5", pose: "lintu_goster" },
    { sel: "#matrix, .matwrap", tab: "cal", k: "tour.a6", pose: "lintu_sun" },
    { sel: "#calDetail, #rankList, #matNote", tab: "cal", k: "tour.a6b", pose: "lintu_fikir" },
    { sel: "#ftSeg", tab: "map", k: "tour.a7", pose: "lintu_goster" },
    { sel: "#mcCard, #map", tab: "map", k: "tour.a8", pose: "lintu_fikir" },
    { sel: "#topList", tab: "map", k: "tour.a9", pose: "lintu_sun" },
    { sel: "#jumpModeBtn", tab: "map", k: "tour.a9b", pose: "lintu_dusun" },
    { sel: "#jumpChart", tab: "join", k: "tour.a10", pose: "lintu_dusun" },
    { sel: "#sciLevel, #t-sci", tab: "sci", k: "tour.a10b", pose: "lintu_fikir" },
    { sel: ".tools", k: "tour.a11", pose: "lintu_selam" }
  ];
  let LIST = STEPS;  const KEY = "lintuTurGoruldu";
  let i = 0, ov = null, hole = null, box = null, txt = null, nEl = null, prevB = null, nextB = null, closeB = null, target = null, lastFocus = null;

  function build() {
    if (ov) return;
    ov = document.createElement("div"); ov.className = "tour"; ov.hidden = true;
    ov.innerHTML = `<div class="tour-hole"></div>
      <div class="tour-box" role="dialog" aria-modal="true" aria-labelledby="tourTxt">
        <img src="img/lintu.png" class="tour-bird" alt="Lintu">
        <div class="tour-bubble"><p id="tourTxt" aria-live="polite"></p>
          <div class="tour-nav"><span class="tour-n mono"></span><span class="sp"></span>
            <button type="button" class="tour-prev"></button><button type="button" class="tour-next"></button><button type="button" class="tour-close" aria-label="close">✕</button></div>
          <div class="tour-dots" aria-hidden="true"></div>
        </div>
      </div>`;
    document.body.appendChild(ov);
    hole = ov.querySelector(".tour-hole"); box = ov.querySelector(".tour-box"); txt = ov.querySelector("#tourTxt"); nEl = ov.querySelector(".tour-n");
    prevB = ov.querySelector(".tour-prev"); nextB = ov.querySelector(".tour-next"); closeB = ov.querySelector(".tour-close");
    prevB.onclick = () => go(i - 1); nextB.onclick = () => (i < LIST.length - 1 ? go(i + 1) : close()); closeB.onclick = close;
    ov.addEventListener("keydown", e => { if (e.key === "Escape") close(); if (e.key === "ArrowRight") nextB.click(); if (e.key === "ArrowLeft" && i > 0) go(i - 1); if (e.key === "Tab") trap(e); });
    window.addEventListener("resize", place); window.addEventListener("scroll", place, true);
    // köşedeki kalıcı Lintu düğmesi: turu yeniden açar
    const fab = document.createElement("button"); fab.type = "button"; fab.className = "lintu-fab"; fab.id = "lintuFab";
    fab.innerHTML = `<img src="img/lintu_bas.png" alt=""><span data-i18n="tour.ask">${esc(t("tour.ask"))}</span>`;
    fab.onclick = () => start(0); document.body.appendChild(fab);
  }
  function trap(e) { const f = [...box.querySelectorAll("button")]; const a = f[0], z = f[f.length - 1]; if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); } else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); } }
  function vis(x) { if (!x || !x.isConnected) return false; const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(x).visibility !== "hidden"; }
  function find(sel) { if (!sel) return null; try { return [...document.querySelectorAll(sel)].find(vis) || null; } catch (e) { return null; } }
  function place() {
    if (!ov || ov.hidden) return;
    const W = innerWidth, H = innerHeight, s = LIST[i] || {};
    if (target && !vis(target)) target = find(s.sel);
    ov.classList.toggle("nodim", !target && !!s.corner);
    if (!target) {
      hole.style.cssText = `left:${W / 2}px;top:${H / 2}px;width:0;height:0`;
      if (s.corner) { box.className = "tour-box bottom left"; box.style.cssText = ""; }
      else { box.className = "tour-box center"; box.style.cssText = ""; }
      return;
    }
    const r = target.getBoundingClientRect(), p = 8;
    const top = Math.max(4, r.top - p), left = Math.max(4, r.left - p), bot = Math.min(H - 4, r.bottom + p), right = Math.min(W - 4, r.right + p);
    hole.style.cssText = `left:${left}px;top:${top}px;width:${Math.max(0, right - left)}px;height:${Math.max(0, bot - top)}px`;
    // balonu hedefi en az örten köşeye koy (4 köşe denenir)
    box.style.cssText = ""; const bw = box.offsetWidth || 400, bh = box.offsetHeight || 200, m = 14;
    const cands = [["bottom", "right", W - m - bw, H - m - bh], ["bottom", "left", m, H - m - bh], ["top", "right", W - m - bw, m], ["top", "left", m, m]];
    let best = cands[0], bo = Infinity;
    for (const c of cands) { const ox = Math.max(0, Math.min(r.right, c[2] + bw) - Math.max(r.left, c[2])), oy = Math.max(0, Math.min(r.bottom, c[3] + bh) - Math.max(r.top, c[3])), o = ox * oy; if (o < bo - 1) { bo = o; best = c; } }
    box.className = "tour-box " + best[0] + " " + best[1];
  }
  let tok = 0;
  async function go(n) {
    i = Math.max(0, Math.min(LIST.length - 1, n)); const my = ++tok;
    const s = LIST[i];
    txt.textContent = s.text || t(s.k);
    nEl.textContent = `${i + 1} / ${LIST.length}`;
    prevB.textContent = t("tour.prev"); prevB.disabled = i === 0;
    nextB.textContent = i === LIST.length - 1 ? t("tour.done") : t("tour.next");
    closeB.title = t("tour.close"); closeB.setAttribute("aria-label", t("tour.close"));
    ov.querySelector(".tour-bird").src = `img/${s.pose || "lintu"}.png`;
    ov.querySelector(".tour-dots").innerHTML = LIST.map((_, k) => `<i class="${k === i ? "on" : ""}"></i>`).join("");
    box.classList.remove("pop"); void box.offsetWidth; box.classList.add("pop");
    target = null; place(); nextB.focus({ preventScroll: true });
    if (s.tab && window.APP && APP.S && APP.S.tab !== s.tab) { try { APP.showTab(s.tab); } catch (e) { /* sekme yok */ } }
    if (s.pre) { try { await s.pre(); } catch (e) { /* adım hazırlığı başarısız */ } }
    if (my !== tok) return;
    // hedef görünür olana kadar bekle (sekme/panel açılışı, async çizim)
    for (let k = 0; k < 20 && !(target = find(s.sel)) && s.sel; k++) { await new Promise(r => setTimeout(r, 60)); if (my !== tok) return; }
    if (my !== tok) return;
    if (target) {
      const r0 = target.getBoundingClientRect();
      if (r0.height > innerHeight * 0.8) target.scrollIntoView({ behavior: "auto", block: "start" }); else target.scrollIntoView({ behavior: "auto", block: "center" });
      target.classList.add("tour-target"); document.querySelectorAll(".tour-target").forEach(x => { if (x !== target) x.classList.remove("tour-target"); });
    } else document.querySelectorAll(".tour-target").forEach(x => x.classList.remove("tour-target"));
    place(); setTimeout(() => { if (my === tok) place(); }, 250);
  }
  function start(n, list) {
    LIST = list || STEPS; build(); lastFocus = document.activeElement; ov.hidden = false; document.body.classList.add("touring");
    const fab = document.getElementById("lintuFab"); if (fab) fab.hidden = true;
    go(n || 0);
  }
  function close() {
    if (!ov) return; ov.hidden = true; document.body.classList.remove("touring"); document.querySelectorAll(".tour-target").forEach(x => x.classList.remove("tour-target"));
    const fab = document.getElementById("lintuFab"); if (fab) fab.hidden = false;
    try { localStorage.setItem(KEY, "1"); } catch (e) { /* depolama kapalı olabilir */ }
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function autoStart() {
    build();
    let seen = false; try { seen = localStorage.getItem(KEY) === "1"; } catch (e) { seen = false; }
    if (!seen) setTimeout(() => start(0), 500);
  }
  document.addEventListener("DOMContentLoaded", () => { const b = document.getElementById("tourBtn"); if (b) b.addEventListener("click", () => start(0)); });
  async function startSci() { // bilimsel tur: "Nasıl çalışıyor?" sekmesindeki adımlar
    const c = await SCI.content();
    const L = c.steps.map((st, k) => ({ tab: "sci", sel: ".scistep h2", text: st.tour, pose: st.pose, pre: () => SCI.go(k) }));
    start(0, L);
  }
  return { start, startSci, close, autoStart, steps: STEPS.length };
})();
window.TOUR = TOUR;
