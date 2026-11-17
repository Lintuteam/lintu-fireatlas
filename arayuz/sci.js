// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* "Nasıl çalışıyor?" sekmesi: bilimsel anlatım. İçerik i18n/sci_{dil}.json'dan gelir (adım başlığı, Lintu pozu,
   sade anlatım, formüller, sayılar = metrics.json anahtarları, ilgili ekran). Gerçek yangın doğrulama tablosu
   data/gercek_dogrulama.json'dan. Lintu bilim turu bu adımları sırayla vurgular. */
"use strict";
const SCI = (() => {
  const C = {}; let VAL = null, step = 0;
  async function load(lang) {
    if (!C[lang]) { try { C[lang] = await getJSON(`i18n/sci_${lang}.json?v=2.5.3`); } catch (e) { C[lang] = lang === "tr" ? null : await load("tr"); } }
    return C[lang];
  }
  async function loadVal() { if (VAL === null) { try { VAL = await getJSON("data/gercek_dogrulama.json?v=2.5.3"); } catch (e) { VAL = false; } } return VAL; }
  const UNIT_EN = { "yüzde puan": "pp", "%": "%", "MW": "MW" };
  const unitTxt = u => { if (!u || ["adet", "oran", "nokta", "olay", "tespit"].includes(u)) return ""; return " " + esc(S.lang === "en" ? (UNIT_EN[u] || u) : u); };
  const MATCH_EN = { "eşleşiyor": "match", "kısmen": "partial", "bulunamadı": "not found" };
  function num(k, d) { // metrics.json değeri + etiket rozeti
    const m = metric(k); if (!m) return `<span class="dim">${esc(k)}?</span>`;
    const v = Array.isArray(m.value) ? m.value.map(x => fmtN(x, d === undefined ? 1 : d)).join(" … ") : fmtN(m.value, d === undefined ? (Math.abs(m.value) < 10 ? 2 : 0) : d);
    return `<b class="mono">${esc(v)}${unitTxt(m.unit)}</b> ${badge(m.etiket)}`;
  }
  const fillNums = s => esc(s).replace(/\{m:([a-z0-9_]+)(?:\|(\d))?\}/gi, (_, k, d) => num(k, d === undefined ? undefined : +d));
  // Matematik yazımı: *i* italik, _{alt}, ^{üst}, _{a}^{b} üst üste, [[pay~~payda]] kesir. Girdi önce kaçışlanır.
  function mathHTML(src) {
    let h = esc(src);
    h = h.replace(/\[\[(.+?)~~(.+?)\]\]/g, '<span class="frac"><span class="fn">$1</span><span class="fd">$2</span></span>');
    h = h.replace(/\*(.+?)\*/g, "<i>$1</i>");
    h = h.replace(/_\{([^{}]*)\}\^\{([^{}]*)\}/g, '<span class="ss"><sup>$2</sup><sub>$1</sub></span>');
    h = h.replace(/_\{([^{}]*)\}/g, "<sub>$1</sub>").replace(/\^\{([^{}]*)\}/g, "<sup>$1</sup>");
    h = h.replace(/Σ/g, '<span class="sigma">Σ</span>');
    return h;
  }
  // Sembol adı: A_yangın → A + alt indis (tablo için)
  const symHTML = x => esc(x).replace(/^(\S+?)_(\S+(?: \S+)?)$/, (m, a, b) => `<i>${a}</i><sub>${b}</sub>`).replace(/^([^<\s]+)$/, "<i>$1</i>");
  const LV_KEY = "sciLevel";
  let LV = "basic";
  try { LV = localStorage.getItem(LV_KEY) === "expert" ? "expert" : "basic"; } catch (e) { LV = "basic"; }
  function setLevel(v) { LV = v; try { localStorage.setItem(LV_KEY, v); } catch (e) { } render(); }
  function eqBlock(b, c) {
    const u = c.ui || {}, ex = LV === "expert";
    let h = `<figure class="formula ${ex ? "" : "basic"}">`;
    if (ex) h += `<div class="fx" role="math">${mathHTML(b.formula)}</div>${b.caption ? `<figcaption>${fillNums(b.caption)}</figcaption>` : ""}`;
    h += `<dl class="eqinfo">`;
    if (b.what) h += `<div class="eq-what"><dt>${esc(u.what || "")}</dt><dd>${fillNums(b.what)}</dd></div>`;
    if (ex && b.syms) h += `<div class="eq-syms"><dt>${esc(u.syms || "")}</dt><dd><table class="symt"><thead><tr><th scope="col">${esc(u.sym || "")}</th><th scope="col">${esc(u.mean || "")}</th><th scope="col">${esc(u.unit || "")}</th></tr></thead><tbody>${b.syms.map(r => `<tr><th scope="row" class="mono">${symHTML(r[0])}</th><td>${fillNums(r[1])}</td><td>${esc(r[2])}</td></tr>`).join("")}</tbody></table></dd></div>`;
    if (b.ex) h += `<div class="eq-ex"><dt>${esc(u.ex || "")}</dt><dd>${fillNums(b.ex)}</dd></div>`;
    if (b.why) h += `<div class="eq-why"><dt>${esc(u.why || "")}</dt><dd>${fillNums(b.why)}</dd></div>`;
    return h + `</dl></figure>`;
  }
  function levelBar(c) {
    const u = c.ui || {}, el = $("#sciLevel"); if (!el) return;
    el.innerHTML = `<span class="lvl-l">${esc(u.level || "")}</span><span class="lvl-seg" role="group" aria-label="${esc(u.level || "")}" title="${esc(u.level_tip || "")}"><button type="button" data-lv="basic" aria-pressed="${LV === "basic"}">${esc(u.simple || "Basit")}</button><button type="button" data-lv="expert" aria-pressed="${LV === "expert"}">${esc(u.expert || "Uzman")}</button></span>`;
  }
  function srcBadge(k) { // kaynak türü rozeti: resmî / bilimsel / haber / yok
    const T = { resmi: ["Resmî", "Official", "ok"], bilimsel: ["Bilimsel", "Scientific", "ok"], "resmi+bilimsel": ["Resmî + bilimsel", "Official + scientific", "ok"], haber: ["Haber", "News", "warn"], yok: ["Kaynak yok", "No source", "no"] }[k];
    return T ? `<span class="srcb ${T[2]}">${esc(S.lang === "en" ? T[1] : T[0])}</span> ` : "";
  }
  function valTable(V, c) {
    if (!V || !V.olaylar) return `<p class="dim">${esc(c.val_none)}</p>`;
    const rows = V.olaylar.map(o => `<tr class="${o.eslesme === "eşleşiyor" ? "ok" : o.eslesme === "kısmen" ? "part" : "no"}"><td>${esc(o.il)}</td><td class="mono">${esc(o.bizim_baslangic)}</td><td class="mono">${fmtN(o.bizim_sure_saat, 0)}</td><td class="mono">${fmtN(o.bizim_frp_toplam_mw, 0)}</td><td>${esc(o.yangin_adi || "–")}</td><td class="mono">${esc(o.resmi_baslangic || "–")}</td><td class="mono">${o.yanan_alan_ha ? esc(String(o.yanan_alan_ha)) : "–"}</td><td>${esc(S.lang === "en" ? (MATCH_EN[o.eslesme] || o.eslesme) : o.eslesme)}</td><td>${srcBadge(o.kaynak_turu)}${(o.kaynaklar || []).slice(0, 2).map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener">[${i + 1}]</a>`).join(" ")}</td></tr>`).join("");
    const n = V.olaylar.length, ok = V.olaylar.filter(o => o.eslesme === "eşleşiyor").length, part = V.olaylar.filter(o => o.eslesme === "kısmen").length;
    const gen = V.genel ? `<h4>${esc(c.val_gen || "Genel kanıtlar")}</h4><ul class="small">${Object.values(V.genel).map(g => `<li>${esc(g.bilgi)}${g.uyari ? ` <span class="warnTxt">${esc(g.uyari)}</span>` : ""} ${(g.kaynaklar || []).map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener">[${i + 1}]</a>`).join(" ")}</li>`).join("")}</ul>` : "";
    return `<p class="valsum">${esc(c.val_sum.replace("{ok}", ok).replace("{part}", part).replaceAll("{n}", n))}</p><div class="scroll"><table class="dt valt"><thead><tr>${c.val_cols.map(h => `<th scope="col">${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>${gen}${V.yontem_notu ? `<p class="small dim">${esc(V.yontem_notu)}</p>` : ""}`;
  }
  async function render() {
    const c = await load(S.lang), V = await loadVal(), box = $("#sciBody");
    $("#sciIntro").textContent = c.intro; levelBar(c);
    $("#sciNav").innerHTML = c.steps.map((s, i) => `<button type="button" data-s="${i}" aria-pressed="${i === step}"><span class="solno">${i + 1}</span> ${esc(s.title)}</button>`).join("");
    const s = c.steps[step];
    let h = `<article class="scistep"><img class="scibird" src="img/${esc(s.pose)}.png" alt="Lintu"><div class="scitxt"><h2>${step + 1}. ${esc(s.title)}</h2>`;
    h += `<p class="lead2">${fillNums(s.simple)}</p>`;
    for (const b of s.blocks || []) {
      if (b.formula) { h += eqBlock(b, c); continue; }
      if (b.expert && LV !== "expert") continue;
      if (b.text) h += `<p>${fillNums(b.text)}</p>`;
      if (b.list) h += `<ul>${b.list.map(x => `<li>${fillNums(x)}</li>`).join("")}</ul>`;
      if (b.validation) h += valTable(V, c);
      if (b.cite) h += `<p class="cite small dim">${esc(b.cite)}</p>`;
    }
    if (s.go) h += `<button type="button" class="cta-btn" data-go="${esc(s.go.tab)}" data-anchor="${esc(s.go.anchor || "")}" data-jm="${s.go.jump ? 1 : ""}">${esc(s.go.label)}</button>`;
    h += `<div class="row scinav2"><button type="button" data-prev ${step === 0 ? "disabled" : ""}>${esc(t("tour.prev"))}</button><button type="button" data-next ${step === c.steps.length - 1 ? "disabled" : ""}>${esc(t("tour.next"))}</button></div></div></article>`;
    box.innerHTML = h;
  }
  function go(i) { step = i; return render(); }
  function bind() {
    const lv = $("#sciLevel"); if (lv) lv.addEventListener("click", e => { const b = e.target.closest("[data-lv]"); if (b) setLevel(b.dataset.lv); });
    $("#sciNav").addEventListener("click", e => { const b = e.target.closest("[data-s]"); if (b) go(+b.dataset.s); });
    $("#sciBody").addEventListener("click", e => {
      if (e.target.closest("[data-prev]")) return go(Math.max(0, step - 1));
      if (e.target.closest("[data-next]")) return go(step + 1);
      const g = e.target.closest("[data-go]"); if (!g) return;
      if (g.dataset.jm) { if (!XT.J.on) XT.jumpToggle(true); return; }
      showTab(g.dataset.go);
      setTimeout(() => { const a = g.dataset.anchor && $(g.dataset.anchor); if (a) a.scrollIntoView({ behavior: "smooth", block: "start" }); }, 80);
    });
    $("#sciTourBtn").addEventListener("click", () => TOUR.startSci());
  }
  return { render, bind, go, get step() { return step; }, count: async () => (await load(S.lang)).steps.length, content: () => load(S.lang) };
})();
window.SCI = SCI;
