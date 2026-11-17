// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* Arayüz denetleyicisi. Ekrandaki her sayı D (data/ dosyaları) veya metrics.json'dan hesaplanır (K1, C14). */
"use strict";
const S = { lang: "tr", pal: "viridis", cvd: "none", sade: false, region: { type: "tr" }, from: 0, to: 0, sensor: "all", statuses: new Set([0]), minFrp: 0,
  metric: "count", aggSeries: "olay_esdeger", mmode: "abs", tab: "map", year: 0, tiles: false, vis: [true, true, true, true], frpSize: false, rawOn: false, ft: "noaniz", norepeat: false, anizIl: false, sanKaldir: false, sanGoster: false };
const FT_ST = { all: [0, 6], noaniz: [0], aniz: [6] }; // yangın türü -> dahil durumlar (0 temiz, 6 anız)
let TOP = [], TOPMODE = "max"; // "max" = tepe FRP (frp_max), "sum" = FRP toplamı (uydu sayısına bağlı)
const DICT = {};
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
const t = k => (DICT[S.lang] && DICT[S.lang][k] !== undefined) ? DICT[S.lang][k] : k;
const fill = (k, o) => t(k).replace(/\{(\w+)\}/g, (_, n) => o[n]);
let MX = null, LABST = { step: 1, L: null, idx: 0 }, JUMPSVG = "", PIXSVG = {}, MATSVG = "", LASTITEMS = null, TIMING = {};

function applyI18n() {
  document.documentElement.lang = S.lang;
  for (const el of $$("[data-i18n]")) el.textContent = t(el.dataset.i18n);
  for (const el of $$("[data-i18n-label]")) el.setAttribute("aria-label", t(el.dataset.i18nLabel));
  for (const el of $$("[data-i18n-title]")) el.title = t(el.dataset.i18nTitle);
  document.title = t("app.title");
  $("#langBtn").textContent = S.lang === "tr" ? "EN" : "TR";
  syncSciMode();
}
function syncSciMode() {
  const btn = $("#sciModeBtn"), lbl = $("#sciModeLabel");
  if (!btn || !lbl) return;
  const isEq = String(S.aggSeries || "").includes("esdeger");
  const avail = typeof aggMode === "function" ? aggMode(S) : true;
  if (!avail) {
    btn.disabled = true; btn.setAttribute("aria-pressed", "false"); lbl.textContent = t("btn.scimode_meas"); btn.title = t("btn.scimode_meas_tip"); return;
  }
  btn.disabled = false; btn.title = t("btn.scimode_tip");
  btn.setAttribute("aria-pressed", String(isEq));
  lbl.textContent = isEq ? t("btn.scimode_eq") : t("btn.scimode_raw");
}
function toggleSciMode() {
  const isEq = S.aggSeries.includes("esdeger"), target = isEq ? "olay" : "olay_esdeger", sel = $("#seriesSel");
  if (sel) {
    const opts = [...sel.options].map(o => o.value);
    const chosen = opts.includes(target) ? target : (isEq ? (opts.find(k => !k.includes("esdeger")) || target) : (opts.find(k => k.includes("esdeger")) || target));
    sel.value = chosen; S.aggSeries = chosen;
  } else { S.aggSeries = target; }
  refresh();
}
async function loadDicts() { for (const l of ["tr", "en"]) DICT[l] = await getJSON(`i18n/${l}.json?v=2.7`); }

/* ---------- "Veri ve yöntem" paneli ve uyarılar (dürüstlük: kaynak, aralık, sensör kapsamı, etiketler) ---------- */
function honesty() {
  const sf = D.man.sat_ilk_gun, o = [];
  o.push(fill("hon.source", { gen: D.man.generated_utc.slice(0, 10) }));
  o.push(fill("hon.range", { a: dayISO(D.dataFirst), b: dayISO(D.dataLast) }));
  o.push(fill("hon.sensors", { aqua: dayISO(sf.Aqua), snpp: dayISO(sf.SNPP), n20: dayISO(sf.N20), n21: dayISO(sf.N21) }));
  $("#honBar").innerHTML = o.map(x => `<span>${esc(x)}</span>`).join("");
  $("#honNotes").textContent = t("warn.label") + " " + t("warn.nobase");
  const w = [fill("warn.terra", { a: dayISO(D.dataFirst), b: dayISO(sf.Aqua - 1) })];
  const ly = dayYMD(D.dataLast);
  if (D.dataLast < dateToDay(ly[0] + "-12-31")) w.push(fill("warn.partial", { y: ly[0], d: dayISO(D.dataLast) }));
  $("#warnBar").textContent = w.join(" ");
  $("#simBadge").hidden = !(D.man.simulated && !S.sade);
}

/* ---------- süzgeç denetimleri ---------- */
function buildControls() {
  const sel = $("#regSel");
  sel.innerHTML = `<option value="tr">${esc(t("region.tr"))}</option><optgroup label="${esc(t("region.bolge"))}">` + D.man.birimler.filter(b => b.duzey === "bolge").map(b => `<option value="b:${esc(b.ad)}">${esc(b.ad)}</option>`).join("") + `</optgroup><optgroup label="${esc(t("region.il"))}">` + D.man.ils.map((n, i) => `<option value="${i}">${esc(n)}</option>`).join("") + "</optgroup>";
  { const rg = S.region || { type: "tr" }, want = rg.type === "il" ? String(rg.il) : rg.type === "bolge" ? "b:" + rg.name : "tr"; if ([...sel.options].some(o => o.value === want)) sel.value = want; }
  const st = $("#statusBox");
  { const FIRE = ["temiz", "aniz"], row = (s, i) => `<div class="strow"><label class="chk"><input type="checkbox" data-st="${i}" ${S.statuses.has(i) ? "checked" : ""}> <span class="stsw" style="color:${RAWCOL[i]}" aria-hidden="true">${FIRE.includes(s) ? "●" : "✚"}</span> <b>${esc(t("st." + s))}</b></label><p class="small dim stexp">${esc(t("st." + s + ".d"))}</p><p class="small mono stcnt" data-stn="${i}"></p></div>`;
    const ix = D.man.status.map((s, i) => [s, i]);
    st.innerHTML = `<h4 class="stgh">${esc(t("stg.fire"))}</h4>` + ix.filter(([s]) => FIRE.includes(s)).map(([s, i]) => row(s, i)).join("") +
      `<h4 class="stgh">${esc(t("stg.nofire"))}</h4><p class="small dim">${esc(t("stg.nofire.d"))}</p>` + ix.filter(([s]) => !FIRE.includes(s)).map(([s, i]) => row(s, i)).join("") +
      `<div class="strow"><p class="small"><span class="stsw" style="color:${RAWCOL[4]}" aria-hidden="true">◆</span> <b>${esc(t("fx.san.name"))}</b></p><p class="small dim stexp">${esc(t("fx.san.status_d"))}</p><p class="small mono stcnt" id="sanCnt"></p></div>`; }
  const cl = $("#clsBox");
  const glyph = ["●", "■", "▲", "◆"];
  cl.innerHTML = D.man.match_class.map((c, i) => `<label class="chk"><input type="checkbox" data-cls="${i}" ${S.vis[i] ? "checked" : ""}> <span class="gl" style="color:${CLSCOL[i]}">${glyph[i]}</span> <span>${esc(t("cls." + c))}</span> <span class="mono dim" data-cln="${i}"></span></label>`).join("");
  $("#dFrom").value = dayISO(S.from); $("#dTo").value = dayISO(S.to);
  $("#dFrom").min = $("#dTo").min = dayISO(D.dataFirst); $("#dFrom").max = $("#dTo").max = dayISO(D.dataLast);
  const ys = $("#yearSel"); ys.innerHTML = D.man.yillar.map(y => `<option>${y}</option>`).join(""); ys.value = S.year;
}
const sg = v => (v > 0 ? "+" : v < 0 ? "−" : "") + fmtN(Math.abs(v), 0); // gerçek eksi işareti
function updateCards() { // dört özet kartı: tüm sayılar süzgeçten, hazır tablolardan ve metrics.json'dan
  const mn = MN(), y0 = D.man.yillar[0], y1 = D.man.yillar[D.man.yillar.length - 1];
  $("#cTotal").textContent = fmtN(LASTITEMS ? LASTITEMS.n : 0);
  $("#cTotalSub").textContent = fill("card.total.s2", { ft: t("ft.name_" + S.ft) + (S.norepeat ? " · " + t("rep.short") : "") + (S.anizIl ? " · " + t("fx.aniz.short") : "") + (S.sanKaldir ? " · " + t("fx.san.short") : ""), reg: regionLabel(S.region, t), a: dayISO(S.from), b: dayISO(S.to) });
  // en yoğun 3 ay, SIRALI: ayırt edilemeyen komşular "≈", diğerleri ">"
  const r3 = MX.rank.slice(0, 3);
  $("#cTop").textContent = r3.length ? r3.map((m, i) => (i ? (MX.ayirt[r3[i - 1]] && MX.ayirt[m] ? " ≈ " : " > ") : "") + mn[m]).join("") : "–";
  { const ya = dayYMD(Math.max(S.from, D.dataFirst))[0], yb = dayYMD(Math.min(S.to, D.dataLast))[0]; $("#cTopSub").textContent = fill("card.top.s2", { ser: MX.mode === "agg" ? serName(MX.seri) : t("mat.browser_short"), a: ya, b: yb }).replace(ya + "–" + yb, ya === yb ? String(ya) : ya + "–" + yb); } // seçili tarih aralığı
  const row = MX.cur.find(c => c.hedef === "son_tam_ay") || MX.cur[0], main = row ? (row.prim || row) : null;
  const curT = $(".kart:nth-child(3) h2");
  if (main && main.med !== null && main.med !== undefined && main.med < 10 && main.v !== null && main.v !== undefined) { // az sayıda yüzde yanıltır (ör. orman modu)
    curT.textContent = fill("card.cur.t2", { m: main.bit.slice(0, 7) });
    $("#cCur").textContent = fmtN(main.v, 0); $("#cCur").className = "val";
    $("#cCurSub").textContent = fill("card.cur.few", { v: fmtN(main.v, 0), med: fmtMed(main.med) });
  } else if (main && main.oran !== null && main.oran !== undefined) {
    const p = Math.round((main.oran - 1) * 100);
    curT.textContent = fill("card.cur.t2", { m: main.bit.slice(0, 7) });
    $("#cCur").textContent = (p > 0 ? "+" : p < 0 ? "−" : "") + fmtN(Math.abs(p), 0) + "%";
    $("#cCur").className = "val " + (p > 10 ? "up" : p < -10 ? "down" : "");
    $("#cCurSub").innerHTML = esc(fill(p >= 0 ? "card.cur.above" : "card.cur.below", { p: fmtN(Math.abs(p), 0) })) + ". " + esc(fill(MX && MX.mode === "browser" ? "card.cur.ratio_era" : "card.cur.ratio", { r: fmtN(main.oran * 100, 0) })) + " " + badge(row.etiket || "ölçüldü") +
      (row.prim ? `<br><span class="warnTxt">${esc(t("card.cur.unrel"))}</span> ${badge("doğrulanmadı")}` : "");
  } else { $("#cCur").textContent = "–"; $("#cCur").className = "val"; $("#cCurSub").textContent = t("card.cur.none"); }
  const jr = mval("jump_raw_pct"), jh = mval("jump_harm_pct"), jm = mval("jump_modis_gercek_pct");
  $("#cJump").innerHTML = `<span class="c-ham">${esc(sg(jr))}%</span> → <span class="c-duz">${esc(sg(jh))}%</span>`;
  { const ks = $$(".kart"); if (ks[0]) ks[0].dataset.stage = "kume"; if (ks[3]) ks[3].dataset.stage = "duz"; }
  $("#cJumpSub").innerHTML = esc(fill("card.jump.s", { c: sg(jm) })) + " " + badge(metric("jump_harm_pct").etiket);
  $("#calTitle").textContent = fill("cal.title", { a: y0, b: y1 });
  $("h1").textContent = t("app.title") + " (" + y0 + "–" + y1 + ")";
}
function countsFooter() {
  const sc = new Array(8).fill(0), cc = [0, 0, 0, 0];
  for (const y of D.man.yillar) { const e = D.ev[y]; if (!e) continue; for (let i = 0; i < e.n; i++) { sc[e.st[i]]++; } }
  $$("[data-stn]").forEach(el => { const i = +el.dataset.stn, pt = mval("temizlik_status_" + D.man.status[i]) || 0;
    el.textContent = sc[i] > 0 ? fill("st.cnt_ev", { n: fmtN(sc[i]), p: fmtN(pt) }) : pt > 0 ? fill("st.cnt_pt", { p: fmtN(pt) }) : t("st.cnt_zero"); });
  if (LASTITEMS) { for (let i = 0; i < LASTITEMS.n; i++) cc[LASTITEMS.cls[i]]++; }
  $$("[data-cln]").forEach(el => el.textContent = fmtN(cc[+el.dataset.cln]));
  { const el = $("#sanCnt"), f = flagStats(); if (el) el.textContent = fill("fx.san.cnt", { n: fmtN(f.san), ps: fmtN(f.ps, 1) }); }
}
function readControls() {
  { const fx = v => { const d = dateToDay(v); return Number.isFinite(d) ? d : NaN; }; let a = fx($("#dFrom").value), b = fx($("#dTo").value);
    if (!Number.isFinite(a)) a = D.dataFirst; if (!Number.isFinite(b)) b = D.dataLast; if (a > b) [a, b] = [b, a];
    S.from = a; S.to = b; if ($("#dFrom").value !== dayISO(a)) $("#dFrom").value = dayISO(a); if ($("#dTo").value !== dayISO(b)) $("#dTo").value = dayISO(b); }
  S.sensor = $("#sensSel").value; S.minFrp = +$("#minFrp").value || 0; S.metric = $("#metricSel").value; S.aggSeries = $("#seriesSel").value || "olay_esdeger"; S.mmode = $("#mmodeSel").value;
  S.statuses = new Set($$("[data-st]").filter(c => c.checked).map(c => +c.dataset.st));
  S.vis = $$("[data-cls]").map(c => c.checked);
}

/* ---------- ana yenileme ---------- */
async function refresh() {
  const t0 = performance.now();
  readControls();
  const bk = regionBirim(S.region); if (bk) await loadCal(bk);
  fillSeries(bk);
  honesty();
  $("#regLabel").textContent = regionLabel(S.region, t);
  // harita öğeleri
  const F = makeFilter(S), A = { lat: [], lon: [], cls: [], frp: [], fmax: [], y: [], i: [], il: [], st: [], san: [], hid: [] };
  eachEvent(F, (e, i, y) => { A.lat.push(e.lat[i]); A.lon.push(e.lon[i]); A.cls.push(e.cls[i]); A.frp.push(e.frp_sum[i]); A.fmax.push(e.frp_max[i]); A.y.push(y); A.i.push(i); A.il.push(e.il[i]); A.st.push(F.est(e, i)); A.san.push(e.san ? e.san[i] : 0); A.hid.push(F.hid(e, i) ? 1 : 0); });
  LASTITEMS = { n: A.lat.length, lat: Float32Array.from(A.lat), lon: Float32Array.from(A.lon), cls: Uint8Array.from(A.cls), frp: Float32Array.from(A.frp), fmax: Float32Array.from(A.fmax), y: Uint16Array.from(A.y), i: Int32Array.from(A.i), il: Uint8Array.from(A.il), st: Uint8Array.from(A.st), san: Uint8Array.from(A.san), hid: Uint8Array.from(A.hid) };
  LASTITEMS.nhid = LASTITEMS.hid.reduce((a, b) => a + b, 0);
  MV.sanShow = !!S.sanGoster; fillFxHelp();
  syncFt();
  if (S.norepeat) { // kaç olay çıktı: aynı süzgeç, tekrar filtresi kapalı
    let all = 0; const F0 = makeFilter(Object.assign({}, S, { norepeat: false })); eachEvent(F0, () => { all++; });
    $("#repNote").textContent = fill("rep.note", { n: fmtN(all - A.lat.length), p: fmtN(all ? (all - A.lat.length) / all * 100 : 0, 0) });
  } else $("#repNote").textContent = "";
  MV.pal = S.pal; MV.frpMode = S.frpSize; MV.vis = S.vis; MV.setItems(LASTITEMS);
  const cnt = {}; for (let k = 0; k < LASTITEMS.n; k++) cnt[LASTITEMS.il[k]] = (cnt[LASTITEMS.il[k]] || 0) + 1;
  const cmx = MV.setChoro(cnt, S.pal, S.region.type === "il" ? S.region.il : -1);
  $("#choroLegend").innerHTML = MV.view === "il"
    ? `<span class="ramp2" style="background:linear-gradient(90deg,${PALETTES[S.pal].join(",")})"></span><br>0 → ${fmtN(cmx)} ${esc(t("map.legend_unit"))}`
    : `<span class="ramp2" style="background:linear-gradient(90deg,${HEAT_RAMP.join(",")})"></span><br>${esc(t("map.heat_legend"))}`;
  $("#choroTitle").textContent = t(MV.view === "il" ? "map.legend_title" : "map.view_heat");
  renderTop(); updateMapInfo();
  const t1 = performance.now();
  MX = buildMatrix(S);
  renderMatrix(); renderRank(); renderDayGrid();
  const t2 = performance.now();
  renderJump(); renderPixel(); renderMetricsTable(); countsFooter(); updateCards(); renderSolution(); syncSciMode();
  Object.assign(TIMING, { harita_ms: t1 - t0, matris_ms: t2 - t1, toplam_ms: performance.now() - t0 });
  refreshRaw();
  if (window.XT) XT.afterRefresh();
}
function updateMapInfo() {
  if (!LASTITEMS) return;
  if (window.MC) MC.legend();
  $("#mapInfo").textContent = fill("map.count", { n: fmtN(LASTITEMS.n) }) + (LASTITEMS.nhid ? " " + fill("fx.san.hidden", { n: fmtN(LASTITEMS.nhid) }) : "") + (MV.dense ? " " + t("map.zoomin") : "");
}
/* ---------- isteğe bağlı bayraklar: il bazlı anız, sanayi artığı (varsayılan KAPALI) ---------- */
function fillFxHelp() { // açıklamalardaki sayılar dosyalardan hesaplanır (yazılı sayı yok)
  if (!D.ev[D.man.yillar[D.man.yillar.length - 1]]) return;
  const f = flagStats(), o = { n: fmtN(f.ai), p: fmtN(f.p, 1), u0: fmtN(f.u0, 2), u1: fmtN(f.u1, 2), s: fmtN(f.san), ps: fmtN(f.ps, 1) };
  $$("[data-fxhelp]").forEach(el => { el.textContent = fill("fx." + el.dataset.fxhelp + ".help", o); });
}
function applySanShow() { // yalnız harita katmanı: sayılar değişmez
  const it = LASTITEMS; if (!it) return;
  MV.sanShow = !!S.sanGoster;
  for (let k = 0; k < it.n; k++) it.hid[k] = it.san[k] && !S.sanGoster && !S.sanKaldir ? 1 : 0;
  it.nhid = it.hid.reduce((a, b) => a + b, 0);
  MV.ev.redraw(); renderTop(); updateMapInfo(); if (window.XT) XT.afterRefresh();
}
/* ---------- yangın türü (anız aç/kapat) ---------- */
function setFireType(ft) {
  S.ft = ft;
  const want = new Set(FT_ST[ft]);
  $$("[data-st]").forEach(c => { c.checked = want.has(+c.dataset.st); });
  refresh();
}
function syncFt() { // gelişmiş paneldeki durum kutuları elle değişirse düğmeleri eşle
  { const k = [...S.statuses].sort().join(","); S.ft = k === "0,6" ? "all" : k === "6" ? "aniz" : k === "0" ? "noaniz" : "custom"; }
  $$("[data-ft]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.ft === S.ft)));
}
/* ---------- FRP'si en yüksek 10 olay (seçili süzgeçte; varsayılan: tepe FRP = en yüksek tek tespit, MW) ---------- */
function renderTop() {
  const it = LASTITEMS, best = [], A = TOPMODE === "sum" ? it.frp : it.fmax;
  let single = 0; // tek tespitli olaylar listeye girmez: tek piksel doğrulanamaz (ör. 2010 Ağrı, 1 tespit, 3 GW)
  for (let k = 0; k < it.n; k++) {
    if (it.hid[k]) continue; // gizli sanayi artığı listeye girmez (harita ile tutarlı)
    const f = A[k]; if (best.length === 10 && f <= best[9].f) continue;
    const e0 = D.ev[it.y[k]], i0 = it.i[k]; if (e0.n_modis[i0] + e0.n_viirs[i0] < 2) continue;
    best.push({ k, f }); best.sort((a, b) => b.f - a.f); if (best.length > 10) best.pop();
  }
  const thr = best.length ? best[best.length - 1].f : Infinity; // ilk 10'a girecek kadar yüksek olup tek tespitli olanlar
  for (let k = 0; k < it.n; k++) if (A[k] > thr && !it.hid[k]) { const e0 = D.ev[it.y[k]], i0 = it.i[k]; if (e0.n_modis[i0] + e0.n_viirs[i0] < 2) single++; }
  TOP = best.map(b => b.k);
  $("#topList").innerHTML = TOP.length ? TOP.map((k, r) => {
    const e = D.ev[it.y[k]], i = it.i[k];
    return `<li><button type="button" data-top="${r}" class="topbtn"><span class="rk">${r + 1}</span><span>${esc(fill("map.top_item", { il: D.man.ils[e.il[i]] || "–", d: dayISO(trDay(e.tmin[i])), n: fmtN(e.n_modis[i] + e.n_viirs[i]), f: fmtN(TOPMODE === "sum" ? e.frp_sum[i] : e.frp_max[i], 0) }))}</span></button></li>`;
  }).join("") : `<li class="dim">${esc(t("map.top_none"))}</li>`;
  $$("[data-topm]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.topm === TOPMODE)));
  const nt = $("#topNote"); if (nt) nt.textContent = t(TOPMODE === "sum" ? "map.top_note_sum" : "map.top_note") + (single ? " " + fill("map.top_single", { n: fmtN(single) }) : "") + (it.nhid ? " " + fill("fx.san.hidden", { n: fmtN(it.nhid) }) : "");
}
function goToEvent(k) {
  const it = LASTITEMS; if (!it || k === undefined) return;
  if (window.XT && XT.J.on) XT.jumpToggle(false);
  MV.fitted = true;
  if (S.tab !== "map") showTab("map");
  setTimeout(() => {
    MV.map.invalidateSize();
    const ll = [it.lat[k], it.lon[k]];
    MV.map.flyTo(ll, 11, { duration: 1.2 });
    setTimeout(() => { if (Math.abs(MV.map.getZoom() - 11) > 0.6) MV.map.setView(ll, 11, { animate: false }); }, 1700); // animasyon çalışmazsa doğrudan git
    MV.showPick([it.lat[k], it.lon[k]]);
    onPick("ev", it, k);
    const m = $("#map"); if (m.scrollIntoView) m.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 60);
}
/* ---------- "Ne yaptık?" şeridi: ham tespit -> temizlik -> olay -> düzeltme ---------- */
function renderSolution() {
  const R = yearRows(), H = D.harm, ys = Object.keys(R).map(Number).sort((a, b) => a - b);
  const raw = ys.map(y => H.modis_gercek[R[y]] + H.viirs_ham[R[y]]), har = ys.map(y => H.ana_seri[R[y]]);
  const mx = Math.max(...raw, ...har), W = 150, Hh = 38;
  const pl = a => a.map((v, i) => `${(i / (a.length - 1) * W).toFixed(1)},${(Hh - v / mx * (Hh - 2)).toFixed(1)}`).join(" ");
  const sx = (ys.indexOf(dayYMD(D.man.sat_ilk_gun.SNPP)[0]) / (ys.length - 1) * W).toFixed(1);
  const spark = `<svg class="spark" viewBox="0 0 ${W} ${Hh}" width="${W}" height="${Hh}" role="img" aria-label="${esc(t("jump.raw") + " / " + t("jump.har"))}"><line x1="${sx}" x2="${sx}" y1="0" y2="${Hh}" stroke="${PAL.mark}" stroke-dasharray="1 3"/><polyline points="${pl(raw)}" fill="none" stroke="${PAL.ham}" stroke-dasharray="${PAL_STYLE.ham.dash}" stroke-width="1.6"/><polyline points="${pl(har)}" fill="none" stroke="${PAL.duz}" stroke-width="2.4"/></svg>`;
  const steps = [
    { n: fmtN(mval("veri_toplam_nokta")), tt: "sol.s1.t", d: fill("sol.s1.d", { a: D.man.yillar[0], b: D.man.yillar[D.man.yillar.length - 1] }), go: "map", st: "ham" },
    { n: fmtN(mval("huni_kumeleme_girdi")), tt: "sol.s2.t", d: t("sol.s2.d"), go: "map", st: "temiz" },
    { n: fmtN(mval("events_total")), tt: "sol.s3.t", d: fill("sol.s3.d", { n: fmtN(mval("events_double_count_avoided")) }), go: "join", anchor: "#labSvg", st: "kume" },
    { n: `${sg(mval("jump_raw_pct"))}% → ${sg(mval("jump_harm_pct"))}%`, tt: "sol.s4.t", d: fill("sol.s4.d", { a: sg(mval("jump_raw_pct")), b: sg(mval("jump_harm_pct")), c: sg(mval("jump_modis_gercek_pct")) }), go: "join", anchor: "#jumpChart", extra: spark, st: "duz", use: true }
  ];
  $("#solSteps").innerHTML = steps.map((s, i) => `<li><button type="button" class="solstep st-${s.st}" data-go="${s.go}" data-anchor="${s.anchor || ""}"><span class="solno">${i + 1}</span><span class="solt">${esc(t(s.tt))}</span><span class="soln">${esc(s.n)}</span>${s.extra || ""}<span class="sold">${esc(s.d)}</span>${s.use ? `<span class="soluse">${esc(t("sol.use"))}</span>` : ""}<span class="solgo">${esc(t("sol.go"))}</span></button></li>`).join("");
}
/* Ham nokta katmanı: elle açılırsa seçili tüm durumlar; olaylarda bulunmayan durum (deniz, sanayi, statik NASA ...) seçilince
   otomatik açılır ve YALNIZ o durumların noktaları çizilir (temiz/anız zaten olay olarak çiziliyor). Her durumun kendi rengi var. */
async function refreshRaw() {
  const nonEv = new Set([...S.statuses].filter(x => x !== 0 && x !== 6)), manual = $("#rawToggle").checked, want = manual ? S.statuses : nonEv;
  S.rawOn = manual || nonEv.size > 0; MV.setRawOn(S.rawOn);
  if (!S.rawOn) { MV.rawItems = null; $("#rawInfo").textContent = ""; return; }
  const z = MV.map.getZoom(), need = MV.RAWZOOM, rp = regionPred(S.region), regional = S.region.type !== "tr" || nonEv.size > 0 || want.size > 1 || !want.has(0);
  if (z < need && !regional) { MV.rawItems = null; MV.raw.redraw(); $("#rawInfo").textContent = fill("raw.zoom", { z: need }); return; }
  const b = MV.map.getBounds(), a = { lat: [], lon: [], y: [], i: [], s: [] }, [y0] = dayYMD(S.from), [y1] = dayYMD(S.to), RAWMAX = 400000; let cut = false;
  $("#rawInfo").textContent = t("raw.loading");
  for (let y = y0; y <= y1; y++) {
    if (!D.man.points[y]) continue;
    const P = await loadYear("pt", y);
    for (let i = 0; i < P.n; i++) {
      if ((S.sensor === "modis" ? P.sat[i] > 1 : S.sensor === "viirs" ? P.sat[i] < 2 : false) || !want.has(P.st[i]) || P.day[i] < S.from || P.day[i] > S.to || (!regional && !b.contains([P.lat[i], P.lon[i]])) || !rp(P.lat[i], P.lon[i], P.il[i])) continue;
      if (a.lat.length >= RAWMAX) { cut = true; break; }
      a.lat.push(P.lat[i]); a.lon.push(P.lon[i]); a.y.push(y); a.i.push(i); a.s.push(P.st[i]);
    }
  }
  MV.rawItems = { n: a.lat.length, lat: a.lat, lon: a.lon, y: a.y, i: a.i, s: a.s };
  const per = new Array(8).fill(0); for (const k of a.s) per[k]++;
  $("#rawInfo").textContent = fill("raw.count", { n: fmtN(a.lat.length) }) + (cut ? " " + t("raw.cut") : "") + " · " + D.man.status.map((k, j) => per[j] ? t("st." + k) + " " + fmtN(per[j]) : "").filter(Boolean).join(", ");
  MV.raw.redraw();
}

/* ---------- yıl x ay matrisi ---------- */
function cellColor(c, mx) {
  if (c.v === null) return null;
  if (S.mmode === "anom") return c.an === null ? null : divColor(Math.max(-1, Math.min(1, c.an / 100)));
  return palColor(S.pal, mx > 0 ? c.v / mx : 0);
}
function lum(rgb) { const m = rgb.match(/\d+/g).map(Number).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]; }
const MN = () => Array.from({ length: 12 }, (_, i) => new Intl.DateTimeFormat(S.lang, { month: "short", timeZone: "UTC" }).format(new Date(Date.UTC(2000, i, 1))));
const BDG = { "ölçüldü": "olculdu", "tahmini": "tahmini", "doğrulanmadı": "dogrulanmadi" };
function badge(e) { const w = String(e || "").trim().split(/[\s(]/)[0], k = BDG[w]; return k ? `<span class="bdg bdg-${k}" title="${esc(e)}">${esc(t("etiket." + k))}</span>` : ""; }
function warnTxt(u) { return String(u || "").split(";").filter(Boolean).map(x => { const y = t("uy." + x); return y === "uy." + x ? x : y; }).join("; ") || "–"; }
const serName = k => { const x = t("ser." + k); return x === "ser." + k ? k : x; };
function fillSeries(bk) {
  const sel = $("#seriesSel"), cal = bk ? D.cal[bk] : null, keep = S.aggSeries;
  const list = cal ? D.man.seri_sirasi.filter(k => cal.seri[k]) : [];
  sel.innerHTML = list.map(k => `<option value="${k}">${esc(serName(k))}</option>`).join(""); sel.disabled = !cal;
  S.aggSeries = list.includes(keep) ? keep : (["olay_esdeger", "modis_esdeger", "olay"].find(k => list.includes(k)) || list[0] || keep || "olay_esdeger"); if (cal) sel.value = S.aggSeries;
}
function seriesUnit(k) { return k.startsWith("enerji") ? t("unit.frp") : k.startsWith("olay") ? t("unit.events") : t("unit.det"); }
function humanYorum(s) { // kod anahtarı + ayrıntı -> i18n; sayılar yerel ondalıkla
  const i = s.indexOf(":"), key = i < 0 ? s : s.slice(0, i), rest = i < 0 ? "" : s.slice(i + 1).trim();
  const tx = k => { const y = t("uy." + k); return y === "uy." + k ? k : y; };
  let r = rest ? (t("uyx." + rest) !== "uyx." + rest ? t("uyx." + rest) : rest.replace(/esdeger/g, t("w.equiv")).replace(/\d+\.\d+/g, x => fmtN(parseFloat(x), 2))) : "";
  return tx(key) + (r ? ": " + r : "");
}
function extraCur(c) {
  const o = [];
  if (c.kismi_gun !== null && c.kismi_gun !== undefined) o.push(fill("cur.kismi", { d: fmtN(c.kismi_gun, 0) }));
  if (c.nrt !== null && c.nrt !== undefined) o.push(fill("cur.nrt", { p: fmtN(c.nrt * 100, 0) }));
  if (c.viirs_oran !== null && c.viirs_oran !== undefined) o.push(fill("cur.viirs", { r: fmtN(c.viirs_oran * 100, 0) }));
  if (/true/i.test(c.aqua || "")) o.push(t("cur.aqua"));
  if (c.yorum) o.push(esc(humanYorum(c.yorum)) + " " + badge(c.yorum_etiket || "doğrulanmadı"));
  return o.length ? "<br><span class=\"dim small\">" + o.map(x => x).join(" · ") + "</span>" : "";
}
function fmtCell(c) { return S.mmode === "anom" ? (c.an === null ? "–" : (c.an > 0 ? "+" : "") + fmtN(c.an, 0) + "%") : fmtN(c.v, S.metric === "frp" && S.series !== "esdeger" ? 0 : 0); }
function renderMatrix() {
  const ys = D.man.yillar, mn = MN();
  let mx = 0; for (const y of ys) for (const c of MX.grid[y]) if (c.v !== null && c.v > mx) mx = c.v;
  const unit = MX.mode === "agg" ? serName(MX.seri) + " (" + seriesUnit(MX.seri) + ")" : (S.metric === "frp" ? t("unit.frp") : t("unit.events"));
  $("#matCap").textContent = fill("mat.caption", { region: regionLabel(S.region, t), unit, mode: t(S.mmode === "anom" ? "mat.anom" : "mat.abs") });
  let h = `<thead><tr><th scope="col">${esc(t("mat.year"))}</th>${mn.map(m => `<th scope="col">${esc(m)}</th>`).join("")}</tr></thead><tbody>`;
  for (const y of ys) {
    h += `<tr><th scope="row">${y}</th>`;
    MX.grid[y].forEach((c, mi) => {
      const col = cellColor(c, mx), cls = ["mc"];
      if (c.cov === "yok" || c.v === null) cls.push("oos"); if (c.cov === "kismi") cls.push("part"); if (c.flag === "gecis") cls.push("gecis"); if (c.flag === "eski_donem_yalniz_terra") cls.push("terra");
      const txt = c.v === null ? "–" : fmtCell(c);
      const fg = col ? (lum(col) > 0.179 ? "#000000" : "#ffffff") : "";
      const lab = `${y} ${mn[mi]}: ${c.v === null ? t("mat.out") : fmtCell(c)}${c.cov === "kismi" ? " (" + t("mat.partial") + ")" : ""}${c.lo !== null && c.lo !== undefined ? ` [${fmtN(c.lo)}–${fmtN(c.hi)}]` : ""}${c.iso ? " · " + c.iso : ""}${c.uy ? " · " + c.uy : ""}`;
      h += `<td class="${cls.join(" ")}" tabindex="-1" data-y="${y}" data-m="${mi}" style="${col ? `background:${col};color:${fg}` : ""}" aria-label="${esc(lab)}" title="${esc(lab)}">${esc(txt)}</td>`;
    });
    h += "</tr>";
  }
  h += `<tr class="medrow"><th scope="row">${esc(t("mat.median"))}</th>${MX.med.map((v, i) => `<td class="${MX.top3.includes(i) ? "top" : ""}" aria-label="${esc(mn[i] + " " + t("mat.median") + " " + fmtN(v))}">${MX.top3.includes(i) ? "★ " : ""}${fmtMed(v)}</td>`).join("")}</tr>`;
  h += `<tr class="medrow"><th scope="row">${esc(t("mat.nyears"))}</th>${MX.full.map(n => `<td>${n}</td>`).join("")}</tr></tbody>`;
  $("#matrix").innerHTML = h;
  const cells = $$("#matrix td.mc"); if (cells.length) cells[0].tabIndex = 0;
  MATSVG = matrixSVG(mx);
  // etiket ve seri notu
  const eq = MX.mode === "agg" && /esdeger/.test(MX.seri);
  $("#matMode").textContent = MX.mode === "agg" ? fill("mat.mode_agg", { b: regionBirim(S.region) }) : t("mat.mode_browser");
  $("#matNote").textContent = [eq ? t("mat.note_eq") : "", MX.mode === "agg" ? "" : t("mat.note_raw"), MX.mode === "agg" && S.region.type === "il" && eq ? t("mat.note_il") : ""].filter(Boolean).join(" ");
  // gösterge
  $("#matLegend").innerHTML = S.mmode === "anom" ? `<span class="ramp div"></span> ${esc(t("mat.lg_anom"))}` : `${esc(t("mat.lg_abs"))} <span class="ramp" style="background:linear-gradient(90deg,${PALETTES[S.pal].join(",")})"></span> 0 → ${fmtN(mx)}`;
  $("#curMonth").innerHTML = MX.cur.map(curLine).join("<br>");
}
function fmtMed(v) { return fmtN(v, v !== null && v !== undefined && Math.abs(v) < 100 ? 1 : 0); }
function curLine(c0) {
  const main = c0.prim || c0, fall = c0.curSeri !== c0.matSeri;
  let h = esc(fill("mat.cur", { h: serName(main.curSeri && !c0.prim ? main.curSeri : (c0.prim ? c0.birincil : c0.curSeri)) + " — " + t("cur." + c0.hedef), a: main.bas, b: main.bit, d: main.gun, v: fmtN(main.v), med: fmtMed(main.med), r: main.oran === null ? "–" : fmtN(main.oran * 100, 0), p: main.yuzdelik === null ? "–" : fmtN(main.yuzdelik, 0), n: main.n_yil, u: warnTxt(main.uyTxt) })) + " " + badge(c0.etiket || "ölçüldü");
  if (c0.prim) h += `<br><span class="warnTxt">${esc(fill("cur.unreliable", { s: serName(c0.curSeri), r: c0.oran === null ? "–" : fmtN(c0.oran * 100, 0), why: warnTxt(c0.neden) }))}</span> ${badge("doğrulanmadı")}`;
  if (fall) h += `<br><span class="dim small">${esc(fill("cur.fallback", { s: serName(c0.matSeri), f: serName(c0.curSeri) }))}</span>`;
  if (c0.mo !== null || c0.vo !== null) h += `<br><span class="dim small">${esc(fill("cur.measured", { m: c0.mo === null ? "–" : fmtN(c0.mo * 100, 0), v: c0.vo === null ? "–" : fmtN(c0.vo * 100, 0) }))} ${badge("ölçüldü")}</span>`;
  return h + extraCur(c0);
}
function matrixSVG(mx) {
  const ys = D.man.yillar, mn = MN(), cw = 52, ch = 18, l = 56, top = 40, W = l + 12 * cw + 10, H = top + (ys.length + 1) * ch + 20;
  let b = `<text x="8" y="16" font-size="12" fill="${COL.fg}">${esc($("#matCap").textContent)}</text>`;
  mn.forEach((m, i) => b += `<text x="${l + i * cw + cw / 2}" y="${top - 6}" text-anchor="middle" font-size="10" fill="${COL.muted}">${esc(m)}</text>`);
  ys.forEach((y, r) => {
    b += `<text x="${l - 6}" y="${top + r * ch + 13}" text-anchor="end" font-size="10" fill="${COL.muted}">${y}</text>`;
    MX.grid[y].forEach((c, i) => { const col = cellColor(c, mx); b += `<rect x="${l + i * cw}" y="${top + r * ch}" width="${cw - 1}" height="${ch - 1}" fill="${col || COL.grid}"/>` + (c.v !== null ? `<text x="${l + i * cw + cw / 2}" y="${top + r * ch + 13}" text-anchor="middle" font-size="9" fill="${col && lum(col) > 0.179 ? "#000000" : "#ffffff"}">${esc(fmtCell(c))}</text>` : ""); });
  });
  MX.med.forEach((v, i) => b += `<text x="${l + i * cw + cw / 2}" y="${top + ys.length * ch + 13}" text-anchor="middle" font-size="9" fill="${MX.top3.includes(i) ? COL.accent : COL.fg}">${MX.top3.includes(i) ? "★" : ""}${esc(fmtN(v))}</text>`);
  b += `<text x="${l - 6}" y="${top + ys.length * ch + 13}" text-anchor="end" font-size="10" fill="${COL.muted}">${esc(t("mat.median"))}</text>`;
  return svgWrap(W, H, b, t("mat.title"), $("#matNote").textContent);
}
function renderRank() {
  const mn = MN();
  const shown = MX.rank.map(m => fmtMed(MX.med[m]));
  $("#rankList").innerHTML = MX.rank.map((m, i) => { const tie = shown[i] === shown[i - 1] || shown[i] === shown[i + 1]; return `<li class="${MX.top3.includes(m) ? "top" : ""}" title="${MX.ayirt[m] || tie ? esc(t("mat.ayirt")) : ""}"><span>${MX.top3.includes(m) ? "★ " : ""}${esc(mn[m])}${MX.ayirt[m] || tie ? " ≈" : ""}</span><span class="mono">${shown[i]}</span></li>`; }).join("");
}
/* ---------- gün x hafta ızgarası (gözlem yok != yangın yok) ---------- */
function renderDayGrid() {
  const y = S.year, G = buildDayGrid(S, y), f = dayToDate(G.f).getUTCDay(), off = (f + 6) % 7; // Pazartesi başlangıç
  const cols = Math.ceil((G.l - G.f + 1 + off) / 7); let mx = 0; for (const v of G.n) if (v > mx) mx = v;
  const dn = Array.from({ length: 7 }, (_, i) => new Intl.DateTimeFormat(S.lang, { weekday: "short", timeZone: "UTC" }).format(new Date(Date.UTC(2024, 0, 1 + i))));
  let h = `<tbody>`;
  for (let r = 0; r < 7; r++) {
    h += `<tr><th scope="row">${esc(dn[r])}</th>`;
    for (let c = 0; c < cols; c++) {
      const k = c * 7 + r - off; if (k < 0 || k > G.l - G.f) { h += `<td class="dg pad"></td>`; continue; }
      const n = G.n[k], ob = G.obs[k], dt = dayISO(G.f + k);
      let cls = "dg", st = "", tx = "";
      if (ob !== 1) { cls += ob === 0 ? " noobs" : " nocov"; tx = ob === 0 ? t("dg.noobs") : t("dg.nocov"); }
      else if (n === 0) { cls += " zero"; tx = t("dg.zero"); } else { st = `background:${palColor(S.pal, Math.sqrt(n / mx))}`; tx = fmtN(n); }
      h += `<td class="${cls}" data-d="${G.f + k}" style="${st}" title="${esc(dt + ": " + tx)}" aria-label="${esc(dt + ": " + tx)}"></td>`;
    }
    h += "</tr>";
  }
  $("#dayGrid").innerHTML = h + "</tbody>";
  const nOb = G.obs.filter(v => v === 0).length, nNo = G.obs.filter(v => v === -1).length;
  $("#dgInfo").textContent = fill("dg.info", { y, no: nOb, nc: nNo, src: D.cov.kaynak.join(", "), lab: D.cov.etiket.join(", ") });
}

/* ---------- sıçrama grafiği (U-15) ---------- */
function yearRows() {
  const H = D.harm, r = {}; for (let i = 0; i < H.yil.length; i++) if (H.duzey[i] === "yil_TR" && H.birim[i] === "tespit" && H.kume[i] === "temiz") r[H.yil[i]] = i; return r;
}
function renderJump() {
  const H = D.harm, R = yearRows(), ys = Object.keys(R).map(Number).sort((a, b) => a - b), sf = D.man.sat_ilk_gun;
  const ev = {}; // kümelenmiş: TR, yalnız 'temiz' olaylar, sabit süzgeç (arayüz süzgecinden bağımsız)
  const Ff = makeFilter({ region: { type: "tr" }, statuses: new Set([0]), sensor: "all", minFrp: 0, from: D.dataFirst, to: D.dataLast });
  eachEvent(Ff, (e, i) => { const y = dayYMD(trDay(e.tmin[i]))[0]; ev[y] = (ev[y] || 0) + 1; });
  const frac = d => { const [y, m, dd] = dayYMD(d); return y + (m - 1) / 12 + (dd - 1) / 365; };
  const raw = ys.map(y => [y + 0.5, H.modis_gercek[R[y]] + H.viirs_ham[R[y]]]);
  const clu = ys.map(y => [y + 0.5, ev[y] || 0]);
  const har = ys.map(y => [y + 0.5, H.ana_seri[R[y]]]);
  const mod = ys.map(y => [y + 0.5, H.modis_gercek[R[y]]]);
  const o = { title: t("jump.title"), desc: t("jump.desc"), x0: ys[0], x1: ys[ys.length - 1] + 1, yLabel: t("jump.y"), w: 820, h: 360,
    xticks: ys.filter(y => y % 2 === 0).map(y => ({ v: y + 0.5, l: String(y) })),
    xLabel: t("jump.x"),
    series: [{ name: t("jump.raw"), end: t("jump.raw.e"), color: PAL.ham, pts: raw, dash: PAL_STYLE.ham.dash, mk: PAL_STYLE.ham.mk, width: 2 }, { name: t("jump.clu"), end: t("jump.clu.e"), color: PAL.kume, pts: clu, dash: PAL_STYLE.kume.dash, mk: PAL_STYLE.kume.mk, width: 2 }, { name: t("jump.har"), end: t("jump.har.e"), color: PAL.duz, pts: har, dash: PAL_STYLE.duz.dash, mk: PAL_STYLE.duz.mk, width: 3 }, { name: t("jump.mod"), end: t("jump.mod.e"), color: PAL.modis, pts: mod, dash: PAL_STYLE.modis.dash, mk: PAL_STYLE.modis.mk, width: 1.6 }],
    band: { name: t("jump.band"), color: PAL.duz, hi: ys.map(y => [y + 0.5, H.ana_ust[R[y]]]), lo: ys.map(y => [y + 0.5, H.ana_alt[R[y]]]) },
    vlines: [{ x: frac(sf.Aqua), label: "Aqua", dy: 0 }, { x: frac(sf.SNPP), label: "SNPP (VIIRS)", dy: 12 }, { x: frac(sf.N20), label: "N20", dy: 0 }, { x: frac(sf.N21), label: "N21", dy: 12 }] };
  JUMPSVG = lineChart(o);
  $("#jumpChart").innerHTML = JUMPSVG;
  howBox("jumpHow", $("#jumpChart"), "jump.how", "jump.use");
  // öncesi/sonrası: geçiş yılı = SNPP ilk yılı; pencere = metrik tanımı (3 yıl önce / 3 yıl sonra)
  const cut = dayYMD(sf.SNPP)[0], mean = (arr, a, b) => { let s = 0, n = 0; for (let y = a; y <= b; y++) if (R[y] !== undefined) { s += arr(R[y]); n++; } return n ? s / n : null; };
  const rows = [["jump.raw", i => H.modis_gercek[i] + H.viirs_ham[i], "jump_raw_pct"], ["jump.har", i => H.ana_seri[i], "jump_harm_pct"], ["jump.mod", i => H.modis_gercek[i], "jump_modis_gercek_pct"]];
  $("#jumpBA").innerHTML = `<thead><tr><th scope="col">${esc(t("jump.series"))}</th><th scope="col">${esc(t("jump.before"))} (${cut - 3}–${cut - 1})</th><th scope="col">${esc(t("jump.after"))} (${cut}–${cut + 2})</th><th scope="col">${esc(t("jump.pct_metric"))}</th><th scope="col">${esc(t("lbl.label"))}</th></tr></thead><tbody>` +
    rows.map(([k, f, mk]) => { const a = mean(f, cut - 3, cut - 1), b = mean(f, cut, cut + 2); return `<tr><th scope="row">${esc(t(k))}</th><td>${fmtN(a)}</td><td>${fmtN(b)}</td><td title="${esc(metric(mk).tanim)}">${fmtN(mval(mk), 1)}%</td><td>${badge(metric(mk).etiket)}</td></tr>`; }).join("") + "</tbody>";
  const ci = mval("jump_null_ci95");
  const fl = [...new Set(Object.values(R).map(i => H.bayrak[i]).filter(Boolean).flatMap(x => x.split(";")))];
  $("#jumpFlags").innerHTML = esc(t("jump.flags")) + " " + (fl.length ? fl.map(x => `<span class="bdg bdg-tahmini">${esc(warnTxt(x))}</span>`).join(" ") : "–");
  $("#jumpNat").innerHTML = esc(fill("jump.natural", { lo: fmtN(ci[0], 1), hi: fmtN(ci[1], 1), lab: "" })) + " " + badge(metric("jump_null_ci95").etiket) + " " + esc( (mval("jump_harm_dogal_aralikta") ? t("jump.inside") : t("jump.outside")));
}
function renderMetricsTable() {
  const keys = ["loyo_mape", "loyo_r2", "loyo_bias", "loyo_ci95", "equiv_overlap_bias", "equiv_overlap_band", "equiv_band_kapsama_ay_tr", "events_joint_overlap", "events_separate_overlap", "events_double_count_avoided", "mcell_iz_basina_viirs", "modis_frp50_genel_mw"];
  $("#metTable").innerHTML = `<thead><tr><th scope="col">${esc(t("met.key"))}</th><th scope="col">${esc(t("met.val"))}</th><th scope="col">${esc(t("lbl.label"))}</th><th scope="col">${esc(t("met.def"))}</th></tr></thead><tbody>` +
    keys.filter(k => metric(k)).map(k => { const m = metric(k), v = Array.isArray(m.value) ? m.value.map(x => fmtN(x, 1)).join(" … ") : fmtN(m.value, 3); return `<tr><th scope="row" class="mono">${k}</th><td>${v} ${esc(m.unit || "")}</td><td>${badge(m.etiket)}</td><td>${esc(m.tanim)}</td></tr>`; }).join("") + "</tbody>";
}
/* ---------- piksel büyümesi (gerçek scan x track dağılımı) ---------- */
/* grafiğin altına "Nasıl okunur?" + "✔ Kullanılması gereken" kutusu (yoksa oluşturur, her çağrıda dili yeniler) */
function howBox(id, after, howKey, useKey) {
  let el = document.getElementById(id);
  if (!el) { el = document.createElement("div"); el.id = id; el.className = "howbox"; after.insertAdjacentElement("afterend", el); }
  el.innerHTML = `<p><b>${esc(t("how.t"))}</b> ${esc(t(howKey))}</p><p class="use"><b>${esc(t("use.t"))}</b> ${esc(t(useKey))}</p>`;
}
function renderPixel() {
  const box = $("#pixBox"); let h = ""; PIXSVG = {};
  for (const sn of Object.keys(D.pix)) {
    const g = D.pix[sn], bars = g.sayim.map((v, i) => ({ a: g.bin_kenar[i], b: g.bin_kenar[i + 1], v }));
    const svg = barChart({ title: `${sn} ${t("pix.title")}`, desc: t("pix.desc"), head: `${sn} — ${t("pix.head2")}`, bars, color: sn === "MODIS" ? PAL.modis : PAL.viirs, yLabel: t("pix.y"), xLabel: t("pix.x"),
      marks: [{ x: g.scan_p05, label: t("pix.nadir"), dy: 0 }, { x: g.scan_p95, label: t("pix.edge"), dy: 12 }] });
    PIXSVG[sn] = svg;
    h += `<figure>${svg}<figcaption class="mono">${esc(fill("pix.cap", { n: fmtN(g.n), p05: fmtN(g.scan_p05, 2), p50: fmtN(g.scan_p50, 2), p95: fmtN(g.scan_p95, 2), mx: fmtN(g.scan_max, 2), am: fmtN(g.alan_med, 2), a95: fmtN(g.alan_p95, 2), amx: fmtN(g.alan_max, 2) }))}</figcaption></figure>`;
  }
  box.innerHTML = h;
  howBox("pixHow", box, "pix.how", "pix.use");
}

/* ---------- müfettiş ---------- */
async function onPick(kind, it, idx) {
  const box = $("#inspBody"); MV.showCell(null);
  if (kind === "none") { MV.showPick(null); box.textContent = t("insp.none"); return; }
  MV.showPick([it.lat[idx], it.lon[idx]]);
  if (window.MC) MC.focus(kind, it, idx);
  box.textContent = t("insp.loading");
  if (kind === "ev") {
    const y = it.y[idx], i = it.i[idx], e = D.ev[y], evid = e.evid[i];
    const exp = { n_modis: e.n_modis[i], n_viirs: e.n_viirs[i] };
    const rows = await inspectPoints("ev", evid, y, t);
    const o = D.man.tr_ofset_dk;
    box.innerHTML = `<dl class="kv"><dt>event_id</dt><dd class="mono">${evid}</dd><dt>${esc(t("insp.cls"))}</dt><dd>${esc(t("cls." + D.man.match_class[e.cls[i]]))}</dd><dt>${esc(t("insp.status"))}</dt><dd>${esc(t("st." + D.man.status[e.st[i]]))}${e.karisik[i] ? " (" + esc(t("insp.mixed")) + ")" : ""}${S.anizIl && e.anizil && e.anizil[i] ? " · " + esc(t("fx.insp.aniz")) : ""}${e.san && e.san[i] ? " · " + esc(t("fx.insp.san")) : ""}</dd><dt>FRP ${esc(t("insp.sum"))}/max</dt><dd class="mono">${fmtN(e.frp_sum[i], 1)} / ${fmtN(e.frp_max[i], 1)} MW</dd><dt>t_start</dt><dd class="mono">${CSVU.tUtc(e.tmin[i])} UTC · ${CSVU.tTr(e.tmin[i], o)} TR</dd><dt>${esc(t("insp.il"))}</dt><dd>${esc(D.man.ils[e.il[i]] || "–")}</dd><dt>${esc(t("insp.dur"))}</dt><dd>${esc(fill("insp.hours", { h: fmtN(e.dur[i] / 60, 1) }))}</dd></dl>` + inspectHTML(rows, exp, t);
    const mp = rows.find(r => r.modis);
    if (mp) { const k = Math.cos(mp.lat * Math.PI / 180); MV.showCell([[mp.lat - mp.track / 2 / KM, mp.lon - mp.scan / 2 / (KM * k)], [mp.lat + mp.track / 2 / KM, mp.lon + mp.scan / 2 / (KM * k)]]); }
  } else { // ham VIIRS noktası -> hücresindeki tüm noktalar
    const y = it.y[idx], P = await loadYear("pt", y), i = it.i[idx], cell = P.cell[i];
    const rows = await inspectPoints("cell", cell, y, t);
    box.innerHTML = `<p class="mono">${esc(t("insp.cell"))}: ${cell > 0 ? "M" + cell : "G" + (-cell - 1)}</p>` + inspectHTML(rows, null, t);
    const mp = rows.find(r => r.modis); if (mp) { const k = Math.cos(mp.lat * Math.PI / 180); MV.showCell([[mp.lat - mp.track / 2 / KM, mp.lon - mp.scan / 2 / (KM * k)], [mp.lat + mp.track / 2 / KM, mp.lon + mp.scan / 2 / (KM * k)]]); }
  }
}

/* ---------- laboratuvar ---------- */
async function labOpen(idx) {
  LABST.idx = idx; LABST.L = await labLoad(D.lab[idx]); labRender();
}
function labRender() {
  const L = LABST.L, st = LABST.step; if (!L) return;
  $("#labSvg").innerHTML = labSVG(L, st, t);
  $("#labText").textContent = labText(L, st, t);
  $("#labTable").innerHTML = labTable(L, t);
  $$("#labSteps button").forEach(b => { b.setAttribute("aria-pressed", String(+b.dataset.step === st)); b.classList.toggle("on", +b.dataset.step === st); });
  $("#labStepInfo").textContent = `${st} / ${$$("#labSteps button").length}: ${t("lab.st" + st)}`;
}

/* ---------- dışa aktarma ---------- */
function exportEvents() {
  const o = D.man.tr_ofset_dk, rows = [], reg = regionLabel(S.region, t);
  const cols = ["event_id", "t_utc", "t_tr", "day_tr", "lat", "lon", "il", "match_class", "status", "n_modis", "n_viirs", "frp_sum_mw", "frp_max_mw", "bolge", "sensor_modu", "aralik_baslangic", "aralik_bitis", "seri"];
  const F2 = makeFilter(S);
  eachEvent(F2, (e, i) => rows.push([e.evid[i], CSVU.tUtc(e.tmin[i]), CSVU.tTr(e.tmin[i], o), dayISO(trDay(e.tmin[i])), Math.round(e.lat[i] * 1e5) / 1e5, Math.round(e.lon[i] * 1e5) / 1e5, D.man.ils[e.il[i]] || "", D.man.match_class[e.cls[i]], D.man.status[F2.est(e, i)], e.n_modis[i], e.n_viirs[i], Math.round(e.frp_sum[i] * 100) / 100, Math.round(e.frp_max[i] * 100) / 100, reg, S.sensor, dayISO(S.from), dayISO(S.to), "olay_olculen"]));
  saveBlob(new Blob([CSVU.toCSV(cols, rows)], { type: "text/csv;charset=utf-8" }), `yangin_olaylar_${S.sensor}_${dayISO(S.from)}_${dayISO(S.to)}.csv`);
}
function exportMatrix() {
  const mn = MN(), rows = [], reg = regionLabel(S.region, t);
  for (const y of D.man.yillar) MX.grid[y].forEach((c, i) => rows.push([y, i + 1, c.v === null ? "" : c.v, c.an === null ? "" : Math.round(c.an * 10) / 10, c.cov, MX.med[i] === null ? "" : MX.med[i], reg, S.sensor, MX.mode === "agg" ? MX.seri : "olay_tarayici", MX.mode === "agg" ? "agg" : "tarayicida_hesaplandi", dayISO(S.from), dayISO(S.to)]));
  saveBlob(new Blob([CSVU.toCSV(["yil", "ay", "deger", "anomali_pct", "kapsam", "ay_medyani", "bolge", "sensor_modu", "seri", "kaynak", "aralik_baslangic", "aralik_bitis"], rows)], { type: "text/csv;charset=utf-8" }), "yangin_yil_ay_matrisi.csv");
}
function exportJump() {
  const H = D.harm, rows = [], R = yearRows();
  for (const y of Object.keys(R).map(Number).sort((a, b) => a - b)) { const i = R[y]; rows.push([y, H.modis_gercek[i], H.viirs_ham[i], H.ana_seri[i], H.ana_alt[i], H.ana_ust[i], H.ana_kaynak[i], H.bayrak[i] || "", H.etiket[i]]); }
  saveBlob(new Blob([CSVU.toCSV(["yil", "modis_gercek", "viirs_ham", "ana_seri_modis_esdeger", "alt", "ust", "kaynak", "bayrak", "etiket"], rows)], { type: "text/csv;charset=utf-8" }), "harmonize_yillik_seri.csv");
}

/* ---------- başlatma ---------- */
function bind() {
  $("#langBtn").onclick = () => { S.lang = S.lang === "tr" ? "en" : "tr"; buildControls(); applyI18n(); refresh(); labRender(); setStatusMsg(); if (S.tab === "sci") SCI.render(); };
  $("#sadeBtn").onclick = e => { S.sade = !S.sade; e.currentTarget.setAttribute("aria-pressed", String(S.sade)); document.body.classList.toggle("sade", S.sade); honesty(); };
  $("#infoBtn").onclick = e => { const p = $("#infoPanel"); p.hidden = !p.hidden; e.currentTarget.setAttribute("aria-expanded", String(!p.hidden)); };
  $("#palSel").onchange = e => { S.pal = e.target.value; refresh(); };
  $("#cvdSel").onchange = e => { S.cvd = e.target.value; document.body.dataset.cvd = S.cvd; };
  const re = () => { refresh(); };
  ["#dFrom", "#dTo", "#sensSel", "#minFrp", "#metricSel", "#seriesSel", "#mmodeSel"].forEach(s => $(s).addEventListener("change", re));
  $("#statusBox").addEventListener("change", () => { refresh(); }); $("#clsBox").addEventListener("change", () => { readControls(); MV.setVis(S.vis); });
  $("#yearSel").onchange = e => { S.year = +e.target.value; renderDayGrid(); if (window.XT) XT.markDayExtremes(); };
  $("#frpSize").onchange = e => { S.frpSize = e.target.checked; MV.frpMode = S.frpSize; MV.ev.redraw(); };
  $("#maxEvBtn").onclick = () => goToEvent(TOP[0]); // tepe FRP'si en yüksek olay (süzgeçteki; TOPMODE ile aynı ölçüt)
  $$("[data-topm]").forEach(b => b.onclick = () => { TOPMODE = b.dataset.topm; if (LASTITEMS) renderTop(); });
  $("#topList").addEventListener("click", e => { const b = e.target.closest("[data-top]"); if (b) goToEvent(TOP[+b.dataset.top]); });
  $("#ftSeg").addEventListener("click", e => { const b = e.target.closest("[data-ft]"); if (b) setFireType(b.dataset.ft); });
  if (window.MC) MC.bind();
  $("#viewSel").onchange = e => { MV.view = e.target.value; refresh(); };
  $("#solSteps").addEventListener("click", e => {
    const b = e.target.closest("[data-go]"); if (!b) return; showTab(b.dataset.go);
    setTimeout(() => { const a = b.dataset.anchor ? $(b.dataset.anchor) : $("#tab-" + b.dataset.go); if (a) a.scrollIntoView({ behavior: "smooth", block: "start" }); }, 80);
  });
  $("#repChk").onchange = e => { S.norepeat = e.target.checked; refresh(); };
  $$("[data-fx]").forEach(c => c.onchange = () => { const k = c.dataset.fx, v = c.checked; S[k] = v; $$(`[data-fx="${k}"]`).forEach(x => { x.checked = v; }); if (k === "sanGoster") applySanShow(); else refresh(); });
  $("#dateResetBtn").onclick = () => { $("#dFrom").value = dayISO(D.dataFirst); $("#dTo").value = dayISO(D.dataLast); refresh(); };
  $("#rawToggle").onchange = () => { refreshRaw(); };
  $("#tileToggle").onchange = e => { MV.setTiles(e.target.checked); $("#tileWarn").hidden = !e.target.checked; };
  MV.map.on("moveend", () => { if (S.rawOn) refreshRaw(); }); MV.map.on("zoomend", updateMapInfo);
  $("#regSel").onchange = e => { const v = e.target.value; S.region = v === "tr" ? { type: "tr" } : v.startsWith("b:") ? { type: "bolge", name: v.slice(2) } : { type: "il", il: +v }; MV.showRegion(S.region); refresh(); };
  $("#drawBtn").onclick = () => { if (S.tab !== "map") showTab("map"); MV.startDraw(); }; $("#finBtn").onclick = () => { if (S.tab !== "map") showTab("map"); MV.finishDraw(); };
  const num = s => { s = String(s || "").trim().replace(",", "."); return s === "" ? NaN : +s; }; // boş kutu 0 sayılmasın (eski hata: daire 0°,0°'a gidiyordu)
  const radius = () => { const km = num($("#cRad").value); return Number.isFinite(km) && km > 0 && km <= 500 ? km : null; };
  $("#circBtn").onclick = () => { const km = radius(); if (!km) return setStatusMsg("circle.bad"); if (S.tab !== "map") showTab("map"); MV.startCircle(km); $("#map").focus(); };
  $("#circApplyBtn").onclick = () => { const lat = num($("#cLat").value), lon = num($("#cLon").value), km = radius(); if (!km || !(lat >= 35 && lat <= 43 && lon >= 25 && lon <= 45.5)) return setStatusMsg("circle.bad"); if (S.tab !== "map") showTab("map"); applyRegion({ type: "circle", lat, lon, km }); };
  $("#clrBtn").onclick = () => { MV.cancelDraw(); MV.cancelCircle(); $("#regSel").value = "tr"; applyRegion({ type: "tr" }); };
  $("#exEv").onclick = exportEvents; $("#exMat").onclick = exportMatrix; $("#exJump").onclick = exportJump;
  if ($("#sciModeBtn")) $("#sciModeBtn").onclick = toggleSciMode;
  if ($("#quickExportBtn")) $("#quickExportBtn").onclick = exportEvents;
  $("#exMatPng").onclick = () => downloadPNG(MATSVG, "yil_ay_matrisi"); $("#exMatSvg").onclick = () => downloadSVG(MATSVG, "yil_ay_matrisi");
  $("#exJumpPng").onclick = () => downloadPNG(JUMPSVG, "sicrama_grafigi"); $("#exJumpSvg").onclick = () => downloadSVG(JUMPSVG, "sicrama_grafigi");
  $("#exPixPng").onclick = () => Object.keys(PIXSVG).forEach(k => downloadPNG(PIXSVG[k], "piksel_" + k)); $("#exPixSvg").onclick = () => Object.keys(PIXSVG).forEach(k => downloadSVG(PIXSVG[k], "piksel_" + k));
  // sekmeler
  const tabs = $$('[role="tab"]');
  tabs.forEach((b, i) => { b.onclick = () => showTab(b.dataset.tab); b.onkeydown = e => { const n = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (n) { const x = tabs[(i + n + tabs.length) % tabs.length]; x.focus(); showTab(x.dataset.tab); } }; });
  // matris: ok tuşları (roving tabindex)
  $("#matrix").addEventListener("keydown", e => {
    const c = e.target.closest("td.mc"); if (!c) return;
    const dy = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0, dm = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dy && !dm) return;
    e.preventDefault(); const ys = D.man.yillar, yi = ys.indexOf(+c.dataset.y) + dy, mi = +c.dataset.m + dm;
    const n = $(`#matrix td.mc[data-y="${ys[Math.max(0, Math.min(ys.length - 1, yi))]}"][data-m="${Math.max(0, Math.min(11, mi))}"]`); if (n) { c.tabIndex = -1; n.tabIndex = 0; n.focus(); }
  });
  $$("#labSteps button").forEach(b => b.onclick = () => { LABST.step = +b.dataset.step; labRender(); });
  $("#labPrev").onclick = () => { LABST.step = Math.max(1, LABST.step - 1); labRender(); };
  $("#labNext").onclick = () => { LABST.step = Math.min(5, LABST.step + 1); labRender(); };
  $("#labSel").onchange = e => labOpen(+e.target.value);
}
function setStatusMsg(k, o) { const m = k ? (o ? fill(k, o) : t(k)) : ""; $("#statusMsg").textContent = m; if ($("#mapStatus")) $("#mapStatus").textContent = m; }
function applyRegion(R) { S.region = R; setStatusMsg(); MV.showRegion(R); if (window.MC) MC.region(R); refresh(); }
function pickIl(il) { $("#regSel").value = String(il); applyRegion({ type: "il", il }); }
function showTab(id) {
  S.tab = id;
  $$('[role="tab"]').forEach(b => { const on = b.dataset.tab === id; b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1; });
  $$('[role="tabpanel"]').forEach(p => p.hidden = p.id !== "tab-" + id);
  if (id === "sci" && window.SCI) SCI.render();
  if (id === "map") setTimeout(() => { if (window.MC) MC.resize(); MV.map.invalidateSize(); if (!MV.fitted) { MV.fitted = true; MV.showRegion(S.region); } MV.ev.redraw(); if (S.rawOn) refreshRaw(); }, 30);
}
async function main() {
  await loadDicts(); await initData();
  S.from = D.dataFirst; S.to = D.dataLast; S.year = D.man.yillar[D.man.yillar.length - 2] || D.man.yillar[0];
  const t0 = performance.now(); $("#loadMsg").textContent = t("load.events");
  buildControls(); applyI18n();
  $("#labSel").innerHTML = D.lab.map((x, i) => `<option value="${i}">${esc(x.il)} · ${dayISO(x.day)} · ${x.sat} · ${x.n_viirs} VIIRS</option>`).join("");
  MV.RAWZOOM = 9; MV.POINTZOOM = 0; // olay noktaları tüm zoomlarda görünür; ham nokta katmanı yalnız yakınlaşınca yüklenir (C20)
  MV.init($("#map"), { pick: onPick, region: applyRegion, status: setStatusMsg, pickIl, ilTip: (name, n) => fill("map.il_tip", { il: name, n: fmtN(n) }), drawn: updateMapInfo, t, circLive: (km, lat, lon) => { $("#cRad").value = km; $("#cLat").value = lat; $("#cLon").value = lon; } });
  bind(); if (window.XT) XT.bind(); if (window.SCI) SCI.bind(); showTab("cal");
  await loadAllEvents((i, n) => { $("#loadMsg").textContent = `${t("load.events")} ${i}/${n}`; });
  computeForest();
  TIMING.yukleme_ms = performance.now() - t0; $("#loadMsg").textContent = "";
  await refresh(); TIMING.ilk_cizim_sonrasi_ms = performance.now() - t0; await labOpen(0);
  window.APP = { S, refresh, TIMING: () => TIMING, bench, showTab, setFireType };
  if (window.TOUR) TOUR.autoStart();
}
/* ölçüm: eşik (en düşük FRP / durum kümesi) değişince tüm ekranın yeniden hesap süresi */
async function bench() {
  const out = { esik_degisimi_ms: [], ilk_yukleme_ms: TIMING.yukleme_ms, olay_sayisi: LASTITEMS.n };
  const mf = mval("temizlik_F_modis_medyan"); // gerçek bir eşik değeri (metrics.json'dan)
  for (let k = 0; k < 5; k++) { $("#minFrp").value = k % 2 ? 0 : mf; const a = performance.now(); await refresh(); out.esik_degisimi_ms.push(performance.now() - a); await new Promise(r => setTimeout(r, 30)); }
  $("#minFrp").value = 0; await refresh();
  const a = performance.now(); const P = await loadYear("pt", D.man.yillar[D.man.yillar.length - 2]); out.nokta_yili_ilk_yukleme_ms = performance.now() - a; out.nokta_yili_satir = P.n;
  const bytes = D.man.yillar.reduce((s, y) => s + D.man.events[y].bayt, 0); out.olay_toplam_mb = bytes / 1e6; out.yil_sayisi = D.man.yillar.length;
  return out;
}
window.addEventListener("DOMContentLoaded", () => main().catch(e => { $("#loadMsg").textContent = "HATA: " + e.message; console.error(e); }));
