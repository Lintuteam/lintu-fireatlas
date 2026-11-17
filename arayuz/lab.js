// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* Birleştirme Laboratuvarı (U-13) ve hücre/olay müfettişi. Gerçek nokta tablosundan (points_<yıl>.bin) çalışır.
   Basitçe: bir MODIS karesi ve içine düşen VIIRS noktaları, adım adım "ham -> hücre -> toplam -> karar -> olay".
   Teknik olarak: MODIS ayak izi = scan x track dikdörtgeni (yön bilgisi yok, eksen hizalı YAKLAŞIK çizilir). */
"use strict";
const SATN = () => D.man.sats;
const KM = 111.19;
async function labLoad(ex) {
  const P = await loadYear("pt", ex.yil), out = [], k = Math.cos(ex.lat * Math.PI / 180);
  for (let i = 0; i < P.n; i++) {
    if (P.day[i] !== ex.day) continue;
    const x = (P.lon[i] - ex.lon) * KM * k, y = (P.lat[i] - ex.lat) * KM;
    if (Math.abs(x) > 8 || Math.abs(y) > 8) continue;
    out.push({ i, x, y, sat: SATN()[P.sat[i]], modis: P.sat[i] <= 1, frp: P.frp[i], scan: P.scan[i], track: P.track[i], tmin: P.tmin[i], cell: P.cell[i], pid: P.pid[i], evid: P.evid[i], st: D.man.status[P.st[i]], conf: P.conf[i], cc: P.cc[i] });
  }
  return { ex, pts: out, P };
}
function labModelPoint(L) { return L.pts.find(p => p.pid === L.ex.cell); }
function labEvent(L, evid) {
  const E = D.ev[L.ex.yil] || null; if (!E || evid < 0) return null;
  for (let i = 0; i < E.n; i++) if (E.evid[i] === evid) return { n_modis: E.n_modis[i], n_viirs: E.n_viirs[i], frp_sum: E.frp_sum[i], frp_max: E.frp_max[i], cls: D.man.match_class[E.cls[i]], st: D.man.status[E.st[i]], dur: E.dur[i] };
  return null;
}
function confTxt(c) { return c >= 0 ? String(c) : ({ "-1": "l", "-2": "n", "-3": "h" })[c] || "?"; }
const hhmm = (tmin, ofs) => CSVU.tTr(tmin, ofs).slice(11);

function labSVG(L, step, t) {
  const W = 560, H = 440, sc = 30, cx = W / 2, cy = H / 2, m = labModelPoint(L);
  const X = v => cx + v * sc, Y = v => cy - v * sc;
  let s = "";
  for (let g = -6; g <= 6; g += 2) s += `<line x1="${X(g)}" x2="${X(g)}" y1="0" y2="${H}" stroke="${COL.grid}"/><line x1="0" x2="${W}" y1="${Y(g)}" y2="${Y(g)}" stroke="${COL.grid}"/><text x="${X(g)}" y="${H - 4}" font-size="10" text-anchor="middle" fill="${COL.muted}">${g}</text>`;
  s += `<text x="4" y="12" font-size="10" fill="${COL.muted}">${esc(t("lab.axis"))}</text>`;
  const mx = m ? m.x : 0, my = m ? m.y : 0;
  if (step >= 2 && m) s += `<rect x="${X(mx - m.scan / 2)}" y="${Y(my + m.track / 2)}" width="${m.scan * sc}" height="${m.track * sc}" fill="${COL.accent}" fill-opacity="0.10" stroke="${COL.accent}" stroke-width="1.5"/>`;
  for (const p of L.pts) {
    const inCell = p.cell === L.ex.cell;
    const dim = step >= 2 && !inCell, col = p.modis ? COL.purple : (step >= 2 && inCell ? COL.accent : COL.fg);
    const x = X(p.x), y = Y(p.y), op = dim ? 0.35 : 1;
    if (p.modis) s += `<rect x="${x - 6}" y="${y - 6}" width="12" height="12" fill="none" stroke="${col}" stroke-width="2.2" opacity="${op}"/><path d="M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x + 4} ${y - 4}L${x - 4} ${y + 4}" stroke="${col}" stroke-width="1.6" opacity="${op}"/>`;
    else s += `<circle cx="${x}" cy="${y}" r="${step >= 3 && inCell ? 3 + Math.sqrt(p.frp) : 4.5}" fill="${col}" fill-opacity="${op}" stroke="${COL.bg}"/>`;
    if (step >= 3 && inCell) s += `<text x="${x + 7}" y="${y - 6}" font-size="10" fill="${COL.fg}">${esc(fmtN(p.frp, 1))}</text>`;
  }
  return svgWrap(W, H, s, t("lab.title"), t("lab.svgdesc"));
}
function labText(L, step, t) {
  const m = labModelPoint(L), inC = L.pts.filter(p => p.cell === L.ex.cell), v = inC.filter(p => !p.modis), md = inC.filter(p => p.modis);
  const vOut = L.pts.filter(p => !p.modis && p.cell !== L.ex.cell), tm = L.pts.filter(p => p.modis);
  const f = (k, o) => t(k).replace(/\{(\w+)\}/g, (_, n) => o[n]);
  const sumV = v.reduce((a, p) => a + p.frp, 0), sumM = md.reduce((a, p) => a + p.frp, 0), thr = mval("modis_frp50_genel_mw");
  if (step === 1) return f("lab.s1", { n: L.pts.length, v: L.pts.filter(p => !p.modis).length, m: tm.length, day: dayISO(L.ex.day), il: L.ex.il });
  if (step === 2) return f("lab.s2", { w: fmtN(m.scan, 1), h: fmtN(m.track, 1), a: v.length, b: vOut.length }) + " " + t("lab.s2n");
  if (step === 3) { const sats = [...new Set(v.map(p => p.sat))]; return f("lab.s3", { sv: fmtN(sumV, 1), sm: fmtN(sumM, 1), nv: v.length, ns: sats.length, sats: sats.join(", ") }); }
  if (step === 4) {
    const sees = sumV >= thr, ok = md.length > 0;
    return f("lab.s4", { sv: fmtN(sumV, 1), thr: fmtN(thr, 1), rule: sees ? t("lab.expect_yes") : t("lab.expect_no"), real: ok ? t("lab.real_yes") : t("lab.real_no") }) + ` [${metric("modis_frp50_genel_mw").etiket}]`;
  }
  const ev = labEvent(L, m ? m.evid : -1);
  return ev ? f("lab.s5", { id: m.evid, nm: ev.n_modis, nv: ev.n_viirs, frp: fmtN(ev.frp_sum, 1), cls: t("cls." + ev.cls), st: ev.st, sum: ev.n_modis + ev.n_viirs }) : t("lab.s5none");
}
function labTable(L, t) {
  const rows = L.pts.filter(p => p.cell === L.ex.cell || true).sort((a, b) => a.tmin - b.tmin);
  const o = D.man.tr_ofset_dk;
  return `<table class="dt"><caption class="sr">${esc(t("lab.table"))}</caption><thead><tr>${["sat", "t_tr", "frp", "conf", "scan_track", "status", "cell"].map(h => `<th scope="col">${esc(t("col." + h))}</th>`).join("")}</tr></thead><tbody>${rows.map(p => `<tr class="${p.cell === L.ex.cell ? "in" : ""}"><td>${p.sat}</td><td>${hhmm(p.tmin, o)}</td><td>${fmtN(p.frp, 1)}</td><td>${confTxt(p.conf)}</td><td>${fmtN(p.scan, 2)}×${fmtN(p.track, 2)}</td><td>${p.st}</td><td>${p.cell === L.ex.cell ? "●" : "○"}</td></tr>`).join("")}</tbody></table>`;
}
/* Müfettiş: bir olayın veya hücrenin tüm noktaları (parent-child) */
async function inspectPoints(kind, key, year, t) {
  const yrs = [year, year + 1].filter(y => D.man.points[y]);
  const rows = [];
  for (const y of yrs) {
    const P = await loadYear("pt", y);
    for (let i = 0; i < P.n; i++) if (kind === "ev" ? P.evid[i] === key : P.cell[i] === key)
      rows.push({ sat: SATN()[P.sat[i]], tmin: P.tmin[i], frp: P.frp[i], conf: P.conf[i], scan: P.scan[i], track: P.track[i], st: D.man.status[P.st[i]], lat: P.lat[i], lon: P.lon[i], cell: P.cell[i], evid: P.evid[i], modis: P.sat[i] <= 1 });
  }
  return rows.sort((a, b) => a.tmin - b.tmin);
}
function inspectHTML(rows, expect, t) {
  const o = D.man.tr_ofset_dk, nm = rows.filter(r => r.modis).length, nv = rows.length - nm;
  const chk = expect ? (nm === expect.n_modis && nv === expect.n_viirs ? t("insp.ok") : t("insp.mismatch")) : "";
  const LIM = 40, shown = rows.length > LIM ? [...rows].sort((a, b) => b.frp - a.frp).slice(0, LIM).sort((a, b) => a.tmin - b.tmin) : rows;
  const more = rows.length > LIM ? `<p class="small dim">${esc(t("insp.more").replace("{k}", LIM).replace("{n}", fmtN(rows.length)))}</p>` : "";
  return `<p class="mono">${esc(t("insp.count").replace("{m}", nm).replace("{v}", nv))} ${chk ? "— " + esc(chk) : ""}</p>${more}<div class="scroll"><table class="dt"><thead><tr>${["sat", "t_utc", "t_tr", "lat", "lon", "frp", "conf", "scan_track", "status"].map(h => `<th scope="col">${esc(t("col." + h))}</th>`).join("")}</tr></thead><tbody>${shown.map(r => `<tr><td>${r.sat}</td><td>${CSVU.tUtc(r.tmin)}</td><td>${CSVU.tTr(r.tmin, o)}</td><td class="mono">${r.lat.toFixed(4)}</td><td class="mono">${r.lon.toFixed(4)}</td><td>${fmtN(r.frp, 1)}</td><td>${confTxt(r.conf)}</td><td>${fmtN(r.scan, 2)}×${fmtN(r.track, 2)}</td><td>${r.st}</td></tr>`).join("")}</tbody></table></div>`;
}
