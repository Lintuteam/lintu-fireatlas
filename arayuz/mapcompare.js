// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* Harita sekmesi: (1) sınıf/tür açıklaması ve lejant, (2) küçük "MODIS-VIIRS birleştirme" haritası.
   Veri uydurulmaz: seçilen olayın gerçek ham noktaları lab.js inspectPoints ile (points_<yıl>.bin) okunur.
   Aşamalar: 1 ham iki uydu -> 2 her sensör ayrı kümelenmiş (zarf) -> 3 ortak küme (tek olay). Zarf = dışbükey çevreleyen çokgen (yaklaşık). */
"use strict";
const MC = { map: null, grp: null, rows: null, evid: null, stage: 1, tok: 0, tiles: null };
const MC_COL = { modis: PAL.modis, viirs: PAL.viirs, joint: PAL.duz }; // charts.js ile aynı renkler
const MC_KM = 111.19;

function mcHull(P) { // P: [[x,y],...] (monotone chain)
  P = P.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (P.length < 3) return P;
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]), lo = [], up = [];
  for (const p of P) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (let i = P.length - 1; i >= 0; i--) { const p = P[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  lo.pop(); up.pop(); return lo.concat(up);
}
function mcCorners(r) { // bir tespitin kapladığı alan: MODIS = scan x track dikdörtgeni, VIIRS = ~0,4 km
  const k = Math.cos(r.lat * Math.PI / 180), hy = (r.modis ? r.track : 0.4) / 2 / MC_KM, hx = (r.modis ? r.scan : 0.4) / 2 / (MC_KM * k);
  return [[r.lon - hx, r.lat - hy], [r.lon + hx, r.lat - hy], [r.lon + hx, r.lat + hy], [r.lon - hx, r.lat + hy]];
}
function mcOutline(rows) { const pts = []; for (const r of rows) pts.push(...mcCorners(r)); return mcHull(pts).map(p => [p[1], p[0]]); }

MC.bind = function () {
  const el = document.getElementById("mcMap"); if (!el || MC.map) return;
  const map = MC.map = L.map(el, { zoomControl: true, preferCanvas: true, center: [39, 35], zoom: 4, minZoom: 4, zoomSnap: 0.5 });
  L.geoJSON(D.il, { interactive: false, style: { color: "#5b6b7b", weight: 1, fillColor: "#10202b", fillOpacity: 0.12 } }).addTo(map);
  MC.tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors (ODbL) · © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (CC BY 4.0)", maxZoom: 18 });
  MC.grp = L.layerGroup().addTo(map);
  map.fitBounds(TR_BOUNDS);
  $("#mcStages").addEventListener("click", e => { const b = e.target.closest("[data-mc]"); if (b) MC.setStage(+b.dataset.mc); });
  $("#mcJoinBtn").onclick = () => { showTab("join"); setTimeout(() => { const a = $("#labSvg"); if (a && a.scrollIntoView) a.scrollIntoView({ behavior: "smooth", block: "center" }); }, 60); };
  $("#colorSel").onchange = e => { MV.setColorBy(e.target.value); MC.legend(); };
  $("#tileToggle").addEventListener("change", e => { if (e.target.checked) MC.tiles.addTo(map); else map.removeLayer(MC.tiles); });
  MC.draw();
};
MC.resize = function () { if (MC.map) { MC.map.invalidateSize(); if (!MC.rows) MC.region(S.region); } };
MC.region = function (R) { // seçili alana göre görünüm (olay seçiliyse onu bozma)
  if (!MC.map || MC.rows) return;
  const sz = MC.map.getSize(); if (!sz || sz.x <= 0) return;
  const b = MV.regionLayer && MV.regionLayer.getBounds ? MV.regionLayer.getBounds() : null;
  if (b && b.isValid() && R.type !== "tr") MC.map.fitBounds(b, { maxZoom: 11 }); else MC.map.fitBounds(TR_BOUNDS);
};
MC.focus = async function (kind, it, idx) {
  if (!MC.map) return;
  const tok = ++MC.tok; let rows;
  try {
    if (kind === "ev") { const y = it.y[idx], e = D.ev[y]; MC.evid = e.evid[it.i[idx]]; rows = await inspectPoints("ev", MC.evid, y, t); }
    else if (kind === "raw") { const y = it.y[idx], P = await loadYear("pt", y); MC.evid = null; rows = await inspectPoints("cell", P.cell[it.i[idx]], y, t); }
    else { MC.rows = null; MC.evid = null; MC.draw(); return; }
  } catch (err) { rows = []; }
  if (tok !== MC.tok) return;
  MC.rows = rows.length ? rows : null; MC.stage = 1; MC.draw(true);
};
MC.setStage = function (s) { MC.stage = s; MC.draw(false); };
MC.draw = function (fit) {
  if (!MC.map) return;
  const g = MC.grp, R = MC.rows, st = MC.stage; g.clearLayers();
  $$("#mcStages [data-mc]").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.mc === st)));
  const info = $("#mcInfo");
  if (!R) { info.textContent = t("mc.i0"); return; }
  const M = R.filter(r => r.modis), V = R.filter(r => !r.modis);
  if (st >= 2 && st < 3) { // ayrı kümeler
    if (M.length) L.polygon(mcOutline(M), { color: MC_COL.modis, weight: 2.5, dashArray: "6 4", fillColor: MC_COL.modis, fillOpacity: 0.12, interactive: false }).addTo(g);
    if (V.length) L.polygon(mcOutline(V), { color: MC_COL.viirs, weight: 2.5, dashArray: "2 4", fillColor: MC_COL.viirs, fillOpacity: 0.12, interactive: false }).addTo(g);
  }
  if (st === 3) L.polygon(mcOutline(R), { color: MC_COL.joint, weight: 3.5, fillColor: MC_COL.joint, fillOpacity: 0.14, interactive: false }).addTo(g);
  for (const r of M.slice(0, 1500)) { const c = mcCorners(r); L.rectangle([[c[0][1], c[0][0]], [c[2][1], c[2][0]]], { color: MC_COL.modis, weight: 1.5, fillColor: MC_COL.modis, fillOpacity: 0.18, interactive: false }).addTo(g); L.circleMarker([r.lat, r.lon], { radius: 3, color: "#fff", weight: 1, fillColor: MC_COL.modis, fillOpacity: 1, interactive: false }).addTo(g); }
  for (const r of V.slice(0, 1500)) L.circleMarker([r.lat, r.lon], { radius: 4, color: "#0b0f14", weight: 1, fillColor: MC_COL.viirs, fillOpacity: 0.95, interactive: false }).addTo(g);
  const o = { m: M.length, v: V.length, n: R.length, id: MC.evid === null ? "–" : MC.evid };
  info.textContent = st === 1 ? fill("mc.i1", o)
    : st === 2 ? (M.length && V.length ? fill("mc.i2", o) : fill("mc.i2one", { s: M.length ? "MODIS" : "VIIRS" }))
    : (M.length && V.length ? fill("mc.i3", o) : fill("mc.i3one", o));
  if (fit !== false) {
    const b = L.latLngBounds(R.flatMap(r => mcCorners(r).map(p => [p[1], p[0]])));
    MC.map.invalidateSize(); MC.map.fitBounds(b, { padding: [28, 28], maxZoom: 14 });
  }
};

/* Ana harita: yangın türü sözlüğü + lejant (renk/şekil ne demek, nasıl belirlendi) */
MC.legend = function () {
  const gl = $("#ftGloss"), lg = $("#mapLegend"); if (!gl || !lg || !LASTITEMS) return;
  const sw = (c, k) => `<span class="gl" style="color:${c}">${["●", "■", "▲", "◆"][k]}</span>`;
  const it = LASTITEMS, nt = [0, 0];
  if (it.st) for (let i = 0; i < it.n; i++) nt[it.st[i] === 6 ? 1 : 0]++;
  const rows = [["all", "#fff", 0], ["noaniz", TYPECOL[0], 0], ["aniz", TYPECOL[1], 1]];
  gl.innerHTML = rows.map(([k, c, s]) => `<li${S.ft === k ? ' class="on"' : ""}>${k === "all" ? '<span class="gl">●■</span>' : sw(c, s)} <b>${esc(t("ftg." + k + ".n"))}</b> ${esc(t("ftg." + k + ".d"))}</li>`).join("");
  const byT = MV.colorBy === "type";
  lg.innerHTML = `<h4>${esc(t(byT ? "leg.t.title" : "leg.s.title"))}</h4><ul class="legul">` + (byT
    ? [0, 1].map(k => `<li>${sw(TYPECOL[k], k)} <b>${esc(t("leg.t" + k + ".n"))}</b> <span class="mono dim">${fmtN(nt[k])}</span><br><span class="small dim">${esc(t("leg.t" + k + ".d"))}</span></li>`).join("") + (MV.sanShow && it.san ? `<li><span class="gl" style="color:${RAWCOL[4]}">◆</span> <b>${esc(t("fx.san.name"))}</b> <span class="mono dim">${fmtN(it.san.reduce((a, b) => a + b, 0))}</span><br><span class="small dim">${esc(t("fx.san.leg"))}</span></li>` : "")
    : D.man.match_class.map((c, i) => `<li>${sw(CLSCOL[i], i)} <b>${esc(t("cls." + c))}</b></li>`).join("")) + `</ul><p class="small dim">${esc(t(byT ? "leg.t.note" : "leg.s.note"))}</p>`;
};
window.MC = MC;
