/* Harita: Leaflet (yerel kopya), tuval katmanı, bölge seçimi (il tıklama, daire, çokgen).
   v2.1: izdüşüm bir kez hesaplanır (hızlı çizim); uzak görünümde yoğunluk ısı haritası, yakında noktalar. */
"use strict";
const CLSCOL = ["#F0E442", "#56B4E9", "#D55E00", "#CC79A7"];       // ortak, yalnız MODIS, yalnız VIIRS, tek sensör dönemi
const TR_BOUNDS = [[35.8, 25.6], [42.2, 44.9]];
const HEAT_RAMP = ["#4a0b0b", "#8f1414", "#d0341c", "#f2701d", "#f9a825", "#fcd34d", "#fff3b0"];
const HEAT_LUT = (() => { const o = []; for (let k = 0; k < 64; k++) { const t = k / 63, x = t * (HEAT_RAMP.length - 1), i = Math.min(HEAT_RAMP.length - 2, Math.floor(x)), f = x - i; const a = hex2rgb(HEAT_RAMP[i]), b = hex2rgb(HEAT_RAMP[i + 1]); o.push(`rgba(${a.map((v, j) => Math.round(v + (b[j] - v) * f)).join(",")},${(0.35 + 0.6 * t).toFixed(2)})`); } return o; })();
const TYPECOL = ["#c9d1d9", "#e0a030"];      // yangın türü: temiz (●), anız (■)
// Ham nokta katmanı rengi (durum sırası: temiz, deniz, volkan, statik_nasa, sanayi, dusuk_guven, aniz, kalici_belirsiz)
const RAWCOL = ["#ffffff", "#38bdf8", "#ef4444", "#c084fc", "#fb923c", "#facc15", "#e0a030", "#f472b6"];
const MV = { colorBy: "type", map: null, ev: null, raw: null, hooks: {}, vis: [true, true, true, true], rawOn: false, frpMode: false, view: "heat",
  sanShow: false, draw: { on: false, pts: [], line: null }, circ: { on: false, km: 25, prev: null }, regionLayer: null, items: null, rawItems: null, pickedLatLng: null, fitted: false, dense: false, screen: null };

function shapePath(ctx, k, x, y, r) {
  ctx.beginPath();
  if (k === 0) ctx.arc(x, y, r, 0, 6.2832);
  else if (k === 1) ctx.rect(x - r, y - r, 2 * r, 2 * r);
  else if (k === 2) { ctx.moveTo(x, y - r * 1.2); ctx.lineTo(x + r * 1.1, y + r * 0.9); ctx.lineTo(x - r * 1.1, y + r * 0.9); ctx.closePath(); }
  else if (k === 4) { const a = r * 0.5, b = r * 1.25; ctx.moveTo(x - a, y - b); ctx.lineTo(x + a, y - b); ctx.lineTo(x + a, y - a); ctx.lineTo(x + b, y - a); ctx.lineTo(x + b, y + a); ctx.lineTo(x + a, y + a); ctx.lineTo(x + a, y + b); ctx.lineTo(x - a, y + b); ctx.lineTo(x - a, y + a); ctx.lineTo(x - b, y + a); ctx.lineTo(x - b, y - a); ctx.lineTo(x - a, y - a); ctx.closePath(); }
  else if (k === 5) { ctx.moveTo(x - r * 1.1, y - r * 0.9); ctx.lineTo(x + r * 1.1, y - r * 0.9); ctx.lineTo(x, y + r * 1.2); ctx.closePath(); }
  else { ctx.moveTo(x, y - r * 1.2); ctx.lineTo(x + r * 1.2, y); ctx.lineTo(x, y + r * 1.2); ctx.lineTo(x - r * 1.2, y); ctx.closePath(); }
}
const CanvasLayer = L.Layer.extend({
  initialize(fn) { this._fn = fn; },
  onAdd(map) { this._map = map; this._c = L.DomUtil.create("canvas", "leaflet-zoom-hide"); this._c.setAttribute("aria-hidden", "true"); map.getPanes().overlayPane.appendChild(this._c); map.on("moveend zoomend resize", this.redraw, this); this.redraw(); },
  onRemove(map) { map.off("moveend zoomend resize", this.redraw, this); this._c.remove(); },
  redraw() {
    const m = this._map; if (!m) return; const s = m.getSize(), c = this._c; c.width = s.x; c.height = s.y;
    L.DomUtil.setPosition(c, m.containerPointToLayerPoint([0, 0]));
    this._fn(c.getContext("2d"), m, s);
  }
});

/* Web Mercator, zoom 0 piksel koordinatı (256 px dünya). Bir kez hesaplanır; her zoomda yalnız ölçek + kaydırma. */
function project0(lat, lon) {
  const s = Math.sin(Math.max(-85.0511, Math.min(85.0511, lat)) * Math.PI / 180);
  return [256 * (lon + 180) / 360, 256 * (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI))];
}
function screenXform(map) { const z = map.getZoom(), sc = Math.pow(2, z), tl = map.containerPointToLayerPoint([0, 0]).add(map.getPixelOrigin()); return { z, sc, tx: tl.x, ty: tl.y }; }

function drawEvents(ctx, map, size) {
  const it = MV.items; if (!it || size.x <= 0 || size.y <= 0) return;
  const X = screenXform(map), z = X.z, scr = MV.screen;
  for (let i = 0; i < it.n; i++) { scr[2 * i] = it.px[i] * X.sc - X.tx; scr[2 * i + 1] = it.py[i] * X.sc - X.ty; }
  // görünür olay sayısı -> yoğunluk mu nokta mı
  let nv = 0; for (let i = 0; i < it.n; i++) { const x = scr[2 * i], y = scr[2 * i + 1]; if (x >= 0 && y >= 0 && x <= size.x && y <= size.y && MV.vis[it.cls[i]] && !(it.hid && it.hid[i])) nv++; }
  MV.dense = MV.view === "heat" ? nv > 6000 && z < 10 : z < 8;
  MV.nVisible = nv;
  if (MV.dense && MV.view === "heat") drawHeat(ctx, it, scr, size);
  else if (!MV.dense) drawPoints(ctx, it, scr, size, z);
  if (MV.pickedLatLng) {
    const pp = map.latLngToContainerPoint(MV.pickedLatLng);
    ctx.strokeStyle = "#5eead4"; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(pp.x, pp.y, 11, 0, 6.2832); ctx.stroke();
    ctx.strokeStyle = "#ffffff"; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.arc(pp.x, pp.y, 15, 0, 6.2832); ctx.stroke();
  }
  if (MV.hooks.drawn) MV.hooks.drawn();
}
function drawHeat(ctx, it, scr, size) {
  const cs = 5, gw = Math.ceil(size.x / cs) + 1, gh = Math.ceil(size.y / cs) + 1, g = new Float32Array(gw * gh);
  for (let i = 0; i < it.n; i++) {
    if (!MV.vis[it.cls[i]] || (it.hid && it.hid[i])) continue;
    const x = scr[2 * i], y = scr[2 * i + 1]; if (x < 0 || y < 0 || x > size.x || y > size.y) continue;
    g[((y / cs) | 0) * gw + ((x / cs) | 0)] += 1;
  }
  const nz = []; for (let k = 0; k < g.length; k++) if (g[k]) nz.push(g[k]);
  if (!nz.length) return;
  nz.sort((a, b) => a - b);
  const top = nz[Math.floor(nz.length * 0.98)] || nz[nz.length - 1]; // %98'lik: birkaç aşırı hücre ölçeği ezmesin
  MV.heatMax = top; const lm = Math.log1p(top);
  for (let k = 0; k < g.length; k++) {
    const v = g[k]; if (!v) continue;
    const tt = Math.min(1, Math.log1p(v) / lm);
    ctx.fillStyle = HEAT_LUT[Math.round(63 * tt * tt)];
    ctx.fillRect((k % gw) * cs, ((k / gw) | 0) * cs, cs, cs);
  }
}
function drawPoints(ctx, it, scr, size, z) {
  const r0 = Math.max(2, Math.min(7, (z - 3) * 0.9)), zf = Math.max(0.3, Math.min(1, (z - 3) / 6)); // uzakta küçük simge
  const byT = MV.colorBy === "type" && it.st, NK = byT ? 2 : 4;
  for (let k = 0; k < NK; k++) {
    if (!byT && !MV.vis[k]) continue;
    ctx.fillStyle = byT ? TYPECOL[k] : CLSCOL[k]; ctx.strokeStyle = "#0b0f14"; ctx.lineWidth = 0.6; ctx.globalAlpha = 0.88;
    for (let i = 0; i < it.n; i++) {
      if (it.hid && it.hid[i]) continue; if (MV.sanShow && it.san && it.san[i]) continue; // sanayi artığı: gizli ya da kendi renginde ayrı çizilir
      if (byT ? ((it.st[i] === 6 ? 1 : 0) !== k || !MV.vis[it.cls[i]]) : it.cls[i] !== k) continue;
      const x = scr[2 * i], y = scr[2 * i + 1];
      if (x < -16 || y < -16 || x > size.x + 16 || y > size.y + 16) continue;
      const r = MV.frpMode ? Math.max(2, Math.min(16, 1.5 + Math.sqrt(it.frp[i]) * 0.5) * zf) : r0;
      shapePath(ctx, k, x, y, r); ctx.fill(); if (r >= 2.2) ctx.stroke();
    }
  }
  if (MV.sanShow && it.san) { // sanayi alanı artıkları: sanayi durumunun rengi (RAWCOL[4]), baklava
    ctx.fillStyle = RAWCOL[4]; ctx.strokeStyle = "#0b0f14"; ctx.lineWidth = 0.6; ctx.globalAlpha = 0.9;
    for (let i = 0; i < it.n; i++) {
      if (!it.san[i] || !MV.vis[it.cls[i]]) continue;
      const x = scr[2 * i], y = scr[2 * i + 1]; if (x < -16 || y < -16 || x > size.x + 16 || y > size.y + 16) continue;
      shapePath(ctx, 3, x, y, Math.max(2, r0)); ctx.fill(); ctx.stroke();
    }
  }
  ctx.globalAlpha = 1;
}
function drawRaw(ctx, map, size) {
  const it = MV.rawItems; if (!it) return;
  const seen = new Set(it.s), big = it.n > 30000; ctx.lineWidth = big ? 1 : 1.4;
  for (const k of seen) {
    ctx.strokeStyle = ctx.fillStyle = RAWCOL[k]; ctx.beginPath();
    for (let i = 0; i < it.n; i++) {
      if (it.s[i] !== k) continue;
      const p = map.latLngToContainerPoint([it.lat[i], it.lon[i]]);
      if (p.x < 0 || p.y < 0 || p.x > size.x || p.y > size.y) continue;
      if (big) ctx.rect(p.x - 1, p.y - 1, 2, 2); else { ctx.moveTo(p.x - 3.5, p.y); ctx.lineTo(p.x + 3.5, p.y); ctx.moveTo(p.x, p.y - 3.5); ctx.lineTo(p.x, p.y + 3.5); }
    }
    if (big) ctx.fill(); else ctx.stroke();
  }
}

/* il çokgeni içinde mi (GeoJSON [lon,lat]); sınır kutusu önce */
function ringHas(r, lat, lon) { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const xi = r[i][0], yi = r[i][1], xj = r[j][0], yj = r[j][1]; if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) c = !c; } return c; }
function polyHas(p, lat, lon) { if (!ringHas(p[0], lat, lon)) return false; for (let h = 1; h < p.length; h++) if (ringHas(p[h], lat, lon)) return false; return true; }
MV.ilAt = function (lat, lon) {
  for (const f of D.il.features) {
    const b = f._bb || (f._bb = L.geoJSON(f).getBounds());
    if (!b.contains([lat, lon])) continue;
    const g = f.geometry, ps = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
    if (ps.some(p => polyHas(p, lat, lon))) return f.properties.idx;
  }
  return -1;
};

MV.init = function (el, hooks) {
  MV.hooks = hooks;
  const map = MV.map = L.map(el, { zoomControl: true, preferCanvas: true, center: [39, 35], zoom: 6, minZoom: 4, zoomSnap: 0.5, keyboard: true, doubleClickZoom: true });
  MV.tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors (ODbL) · © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium (CC BY 4.0)", maxZoom: 18 });
  MV.choro = L.geoJSON(D.il, { style: { color: "#5b6b7b", weight: 1, fillColor: "#10202b", fillOpacity: 0.12 }, onEachFeature: (f, l) => l.bindTooltip(f.properties.name, { sticky: true }) }).addTo(map);
  MV.ev = new CanvasLayer((c, m, s) => drawEvents(c, m, s)).addTo(map);
  MV.raw = new CanvasLayer((c, m, s) => drawRaw(c, m, s));
  map.on("click", e => {
    if (MV.circ.on) { const km = MV.circ.km; MV.cancelCircle(); MV.hooks.region({ type: "circle", lat: +e.latlng.lat.toFixed(4), lon: +e.latlng.lng.toFixed(4), km }); return; }
    if (MV.draw.on) { MV.draw.pts.push([e.latlng.lat, e.latlng.lng]); MV.updateDraw(); return; }
    MV.pick(e.containerPoint, e.latlng);
  });
  map.on("mousemove", e => {
    if (!MV.circ.on) return;
    if (MV.circ.prev) MV.circ.prev.setLatLng(e.latlng);
    else MV.circ.prev = L.circle(e.latlng, { radius: MV.circ.km * 1000, color: "#5eead4", weight: 2, dashArray: "6 4", fillOpacity: 0.08, interactive: false }).addTo(map);
  });
  map.on("dblclick", e => { if (MV.draw.on) { e.originalEvent.preventDefault(); MV.finishDraw(); } });
  document.addEventListener("keydown", ev => { // odak nerede olursa olsun
    if (ev.key === "Enter" && MV.draw.on && map.getContainer().contains(document.activeElement)) MV.finishDraw();
    if (ev.key === "Escape" && (MV.draw.on || MV.circ.on)) { MV.cancelDraw(); MV.cancelCircle(); MV.hooks.status(); }
  });
};
MV.setChoro = function (cnt, pal, selIl) {
  let mx = 0; for (const k in cnt) if (cnt[k] > mx) mx = cnt[k];
  const strong = MV.view === "il";
  MV.choro.eachLayer(l => {
    const idx = l.feature.properties.idx, n = cnt[idx] || 0, sel = idx === selIl;
    l.setStyle({ fillColor: n && strong ? palColor(pal, Math.sqrt(n / mx)) : "#10202b", fillOpacity: strong ? 0.8 : (sel ? 0.02 : 0.12), color: sel ? "#5eead4" : "#5b6b7b", weight: sel ? 2.5 : 1 });
    l.setTooltipContent(MV.hooks.ilTip ? MV.hooks.ilTip(l.feature.properties.name, n) : `${l.feature.properties.name}: ${fmtN(n)}`);
  });
  return mx;
};
MV.showPick = function (latlng) { MV.pickedLatLng = latlng || null; if (MV.ev) MV.ev.redraw(); };
MV.setItems = function (it) {
  it.px = new Float64Array(it.n); it.py = new Float64Array(it.n);
  for (let i = 0; i < it.n; i++) { const p = project0(it.lat[i], it.lon[i]); it.px[i] = p[0]; it.py[i] = p[1]; }
  MV.items = it; MV.screen = new Float32Array(it.n * 2); MV.ev.redraw();
};
MV.setColorBy = function (m) { MV.colorBy = m; if (MV.ev) MV.ev.redraw(); };
MV.setSanShow = function (on) { MV.sanShow = !!on; if (MV.ev) MV.ev.redraw(); };
MV.setVis = function (vis) { MV.vis = vis; MV.ev.redraw(); };
MV.setRawOn = function (on) { MV.rawOn = on; if (on) MV.raw.addTo(MV.map); else MV.map.removeLayer(MV.raw); };
MV.setTiles = function (on) { if (on) MV.tiles.addTo(MV.map); else MV.map.removeLayer(MV.tiles); };
/* tıklama: yakında olay varsa olay ayrıntısı; yoksa (veya yoğunluk görünümünde) tıklanan il seçilir */
MV.pick = function (cp, latlng) {
  let best = -1, bd = 10 * 10, kind = "";
  const it = MV.items;
  if (it && !MV.dense && MV.screen) for (let i = 0; i < it.n; i++) {
    if (!MV.vis[it.cls[i]] || (it.hid && it.hid[i])) continue;
    const dx = MV.screen[2 * i] - cp.x, dy = MV.screen[2 * i + 1] - cp.y, d = dx * dx + dy * dy;
    if (d < bd) { bd = d; best = i; kind = "ev"; }
  }
  const rw = MV.rawItems;
  if (MV.rawOn && rw) for (let i = 0; i < rw.n; i++) {
    const p = MV.map.latLngToContainerPoint([rw.lat[i], rw.lon[i]]), dx = p.x - cp.x, dy = p.y - cp.y, d = dx * dx + dy * dy;
    if (d < bd) { bd = d; best = i; kind = "raw"; }
  }
  if (best >= 0) return MV.hooks.pick(kind, kind === "ev" ? it : rw, best);
  const il = latlng ? MV.ilAt(latlng.lat, latlng.lng) : -1;
  if (il >= 0 && MV.hooks.pickIl) return MV.hooks.pickIl(il);
  MV.hooks.pick("none");
};
/* daire: haritaya tıklayarak merkez seç */
MV.startCircle = function (km) { MV.cancelDraw(); MV.cancelCircle(); MV.circ.on = true; MV.circ.km = km; MV.map.getContainer().classList.add("drawing"); MV.hooks.status("map.circle_hint", { km }); };
MV.cancelCircle = function () { MV.circ.on = false; if (MV.circ.prev) MV.map.removeLayer(MV.circ.prev); MV.circ.prev = null; if (!MV.draw.on) MV.map.getContainer().classList.remove("drawing"); };
/* çokgen */
MV.startDraw = function () { MV.cancelCircle(); MV.cancelDraw(); MV.draw.on = true; MV.map.getContainer().classList.add("drawing"); MV.hooks.status("draw.hint"); };
MV.updateDraw = function () {
  if (MV.draw.line) MV.map.removeLayer(MV.draw.line);
  MV.draw.line = L.polyline(MV.draw.pts, { color: "#5eead4", weight: 2, dashArray: "5 4" }).addTo(MV.map);
};
MV.cancelDraw = function () { MV.draw.on = false; MV.draw.pts = []; if (MV.draw.line) MV.map.removeLayer(MV.draw.line); MV.draw.line = null; if (!MV.circ.on) MV.map.getContainer().classList.remove("drawing"); };
MV.finishDraw = function () { const p = MV.draw.pts.slice(); MV.cancelDraw(); if (p.length >= 3) MV.hooks.region({ type: "poly", poly: p }); };
MV.showRegion = function (R) {
  if (MV.regionLayer) MV.map.removeLayer(MV.regionLayer); MV.regionLayer = null;
  const sz = MV.map.getSize(), visible = sz && sz.x > 0 && sz.y > 0;
  if (!visible) MV.fitted = false;
  if (R.type === "tr") { if (visible) MV.map.fitBounds(TR_BOUNDS); return; }
  if (R.type === "bolge") {
    const fs = D.il.features.filter(f => D.man.il_bolge[D.man.ils[f.properties.idx]] === R.name);
    if (fs.length) { MV.regionLayer = L.geoJSON({ type: "FeatureCollection", features: fs }, { interactive: false, style: { color: "#5eead4", weight: 2, fill: false } }).addTo(MV.map); if (visible) MV.map.fitBounds(MV.regionLayer.getBounds()); }
    return;
  }
  if (R.type === "poly" && R.poly) MV.regionLayer = L.polygon(R.poly, { color: "#5eead4", weight: 2, fill: false, interactive: false }).addTo(MV.map);
  else if (R.type === "circle") MV.regionLayer = MV.editableCircle(R).addTo(MV.map);
  else if (R.type === "il") { const f = D.il.features.find(x => x.properties.idx === R.il); if (f) { MV.regionLayer = L.geoJSON(f, { interactive: false, style: { color: "#5eead4", weight: 2.5, fill: false } }).addTo(MV.map); if (visible) MV.map.fitBounds(MV.regionLayer.getBounds()); } }
  if (MV.regionLayer && R.type !== "il" && visible && R.fit !== false) MV.map.fitBounds(MV.regionLayer.getBounds());
};
MV.showCell = function (cellLayerData) {
  if (MV.cellLayer) MV.map.removeLayer(MV.cellLayer); MV.cellLayer = null;
  if (cellLayerData) MV.cellLayer = L.rectangle(cellLayerData, { color: "#ffffff", weight: 1.5, fill: false, dashArray: "3 3", interactive: false }).addTo(MV.map);
};

/* Düzenlenebilir daire: kenardaki tutamaçla yarıçap, ortadaki tutamaçla konum sürüklenir.
   Sürüklerken km/enlem/boylam kutuları canlı güncellenir; bırakınca bölge uygulanır (harita kaymaz). */
MV.editableCircle = function (R) {
  const map = MV.map, C = [R.lat, R.lon], dLon = km => km / (111.19 * Math.cos(R.lat * Math.PI / 180));
  const circ = L.circle(C, { radius: R.km * 1000, color: "#5eead4", weight: 2, fill: false, interactive: false });
  const mk = (ll, cls, tip) => L.marker(ll, { draggable: true, keyboard: false, title: tip, icon: L.divIcon({ className: "circ-h " + cls, html: "<i></i>", iconSize: [18, 18], iconAnchor: [9, 9] }) });
  const edge = mk([R.lat, R.lon + dLon(R.km)], "edge", MV.hooks.t ? MV.hooks.t("map.circ_edge") : "");
  const mid = mk(C, "mid", MV.hooks.t ? MV.hooks.t("map.circ_mid") : "");
  const live = () => { const c = circ.getLatLng(); if (MV.hooks.circLive) MV.hooks.circLive(+(circ.getRadius() / 1000).toFixed(1), +c.lat.toFixed(4), +c.lng.toFixed(4)); };
  edge.on("drag", e => { const km = Math.max(1, Math.min(500, map.distance(circ.getLatLng(), e.latlng) / 1000)); circ.setRadius(km * 1000); live(); });
  edge.on("dragend", () => { const c = circ.getLatLng(); MV.hooks.region({ type: "circle", lat: +c.lat.toFixed(4), lon: +c.lng.toFixed(4), km: +(circ.getRadius() / 1000).toFixed(1), fit: false }); });
  mid.on("drag", e => { circ.setLatLng(e.latlng); const km = circ.getRadius() / 1000; edge.setLatLng([e.latlng.lat, e.latlng.lng + km / (111.19 * Math.cos(e.latlng.lat * Math.PI / 180))]); live(); });
  mid.on("dragend", () => { const c = circ.getLatLng(); MV.hooks.region({ type: "circle", lat: +c.lat.toFixed(4), lon: +c.lng.toFixed(4), km: +(circ.getRadius() / 1000).toFixed(1), fit: false }); });
  return L.featureGroup([circ, edge, mid]);
};
