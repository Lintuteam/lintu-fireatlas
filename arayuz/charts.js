/* Küçük SVG grafik yardımcıları (kütüphane yok; PNG/SVG indirme için nitelikler satır içi). */
"use strict";
const COL = { bg: "#0d141b", fg: "#e6edf3", muted: "#a3afbc", grid: "#1f2a35", accent: "#5eead4", purple: "#a99cff", warn: "#f5b455", line2: "#9fb3c8" };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmtN = (v, d) => v === null || v === undefined || Number.isNaN(v) ? "–" : Number(v).toLocaleString(document.documentElement.lang === "en" ? "en-US" : "tr-TR", { maximumFractionDigits: d === undefined ? 0 : d });

function niceMax(v) { if (v <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(v))), f = v / p; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p; }

function svgWrap(w, h, body, title, desc) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><desc>${esc(desc || "")}</desc><rect width="${w}" height="${h}" fill="${COL.bg}"/>${body}</svg>`;
}
function axes(w, h, m, x0, x1, y0, y1, o) {
  const X = v => m.l + (v - x0) / (x1 - x0) * (w - m.l - m.r), Y = v => h - m.b - (v - y0) / (y1 - y0) * (h - m.t - m.b);
  let s = "";
  const yt = 5;
  for (let i = 0; i <= yt; i++) {
    const v = y0 + (y1 - y0) * i / yt, y = Y(v);
    s += `<line x1="${m.l}" x2="${w - m.r}" y1="${y}" y2="${y}" stroke="${COL.grid}"/><text x="${m.l - 6}" y="${y + 4}" text-anchor="end" font-size="11" fill="${COL.muted}">${esc(fmtN(v, o.yDec || 0))}</text>`;
  }
  const ticks = o.xticks || [];
  for (const t of ticks) s += `<text x="${X(t.v)}" y="${h - m.b + 16}" text-anchor="middle" font-size="11" fill="${COL.muted}">${esc(t.l)}</text><line x1="${X(t.v)}" x2="${X(t.v)}" y1="${h - m.b}" y2="${h - m.b + 4}" stroke="${COL.muted}"/>`;
  s += `<line x1="${m.l}" x2="${w - m.r}" y1="${h - m.b}" y2="${h - m.b}" stroke="${COL.muted}"/>`;
  if (o.yLabel) s += `<text x="12" y="${m.t - 8}" font-size="11" fill="${COL.muted}">${esc(o.yLabel)}</text>`;
  return { s, X, Y };
}
/* Sabit, renk körü dostu (Okabe-Ito tabanlı) veri aşaması paleti: her yerde aynı anlam.
   ham = ham uydu tespiti, temiz = temizlenmiş, kume = kümelenmiş olay, duz = düzeltilmiş (MODIS-eşdeğer), modis/viirs = sensör.
   Aynı değerler app.css :root içinde --c-ham ... olarak da tanımlı. Çizgiler ayrıca kesik stili + işaretle ayrışır. */
const PAL = { ham: "#9aa5b1", temiz: "#56b4e9", kume: "#e69f00", duz: "#2ee6a6", modis: "#cc79a7", viirs: "#f0e442", mark: "#c9d1d9" };
const PAL_STYLE = { ham: { dash: "7 4", mk: "square" }, temiz: { dash: "2 3", mk: "diamond" }, kume: { dash: "", mk: "triangle" }, duz: { dash: "", mk: "circle" }, modis: { dash: "2 3", mk: "diamond" }, viirs: { dash: "", mk: "circle" } };
function marker(shape, x, y, c, r) {
  r = r || 3.4; x = +x; y = +y;
  if (shape === "square") return `<rect x="${(x - r).toFixed(1)}" y="${(y - r).toFixed(1)}" width="${2 * r}" height="${2 * r}" fill="${c}" stroke="${COL.bg}" stroke-width="0.8"/>`;
  if (shape === "triangle") return `<polygon points="${x.toFixed(1)},${(y - r - 0.8).toFixed(1)} ${(x - r - 0.6).toFixed(1)},${(y + r).toFixed(1)} ${(x + r + 0.6).toFixed(1)},${(y + r).toFixed(1)}" fill="${c}" stroke="${COL.bg}" stroke-width="0.8"/>`;
  if (shape === "diamond") return `<polygon points="${x.toFixed(1)},${(y - r - 1).toFixed(1)} ${(x + r + 1).toFixed(1)},${y.toFixed(1)} ${x.toFixed(1)},${(y + r + 1).toFixed(1)} ${(x - r - 1).toFixed(1)},${y.toFixed(1)}" fill="${c}" stroke="${COL.bg}" stroke-width="0.8"/>`;
  return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="${c}" stroke="${COL.bg}" stroke-width="0.8"/>`;
}
/* o: {w,h,title,desc,x0,x1,xticks,series:[{name,end,color,pts,dash,width,mk}],band:{name,lo,hi,color},vlines:[{x,label}],yLabel,xLabel}
   Başlık + sarmalı gösterge satırı SVG içindedir (PNG/SVG indirmede de kalır); çizgi uçlarında kısa doğrudan etiket (s.end). */
function lineChart(o) {
  const w = o.w || 760, ph = (o.h || 320) - 58;
  const items = o.series.map(s => ({ s, wd: 38 + s.name.length * 5.9 })); if (o.band) items.push({ band: o.band, wd: 24 + o.band.name.length * 5.9 });
  const maxEnd = Math.max(0, ...o.series.map(s => s.end ? s.end.length : 0)), mr = maxEnd ? 14 + maxEnd * 6 : 16;
  let rows = 1, cx = 56; for (const it of items) { if (cx + it.wd > w - 8 && cx > 56) { rows++; cx = 56; } it.row = rows - 1; it.x = cx; cx += it.wd + 6; }
  const m = { l: 56, r: mr, t: 34 + rows * 17 + 14, b: 44 }, h = m.t + ph + m.b;
  let ymax = 0;
  for (const s of o.series) for (const p of s.pts) if (p[1] !== null && p[1] > ymax) ymax = p[1];
  if (o.band) for (const p of o.band.hi) if (p[1] !== null && p[1] > ymax) ymax = p[1];
  const y1 = niceMax(ymax), a = axes(w, h, m, o.x0, o.x1, 0, y1, o);
  let b = a.s;
  b += `<text x="10" y="17" font-size="13" font-weight="700" fill="${COL.fg}">${esc(o.title)}</text>`;
  if (o.xLabel) b += `<text x="${(m.l + w - m.r) / 2}" y="${h - 6}" text-anchor="middle" font-size="11" fill="${COL.muted}">${esc(o.xLabel)}</text>`;
  if (o.band) {
    const hi = o.band.hi.filter(p => p[1] !== null), lo = o.band.lo.filter(p => p[1] !== null);
    if (hi.length) b += `<polygon points="${hi.map(p => a.X(p[0]) + "," + a.Y(p[1])).join(" ")} ${lo.slice().reverse().map(p => a.X(p[0]) + "," + a.Y(p[1])).join(" ")}" fill="${o.band.color}" fill-opacity="0.18" stroke="none"/>`;
  }
  for (const v of (o.vlines || [])) b += `<line x1="${a.X(v.x)}" x2="${a.X(v.x)}" y1="${m.t}" y2="${h - m.b}" stroke="${PAL.mark}" stroke-opacity="0.55" stroke-dasharray="1 4"/><text x="${a.X(v.x) + 3}" y="${m.t + 10 + (v.dy || 0)}" font-size="10" fill="${PAL.mark}">${esc(v.label)}</text>`;
  const ends = [];
  for (const s of o.series) {
    let d = "", pen = false, last = null; const mk = s.mk || "circle", dash = s.dash || "";
    for (const p of s.pts) { if (p[1] === null) { pen = false; continue; } d += (pen ? "L" : "M") + a.X(p[0]).toFixed(1) + " " + a.Y(p[1]).toFixed(1); pen = true; last = p; }
    b += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
    for (const p of s.pts) if (p[1] !== null) b += marker(mk, a.X(p[0]), a.Y(p[1]), s.color, s.width > 2.2 ? 3.6 : 3);
    if (s.end && last) ends.push({ y: a.Y(last[1]), x: a.X(last[0]), t: s.end, c: s.color });
  }
  ends.sort((p, q) => p.y - q.y); for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 13) ends[i].y = ends[i - 1].y + 13;
  for (const e of ends) b += `<text x="${e.x + 9}" y="${e.y + 4}" font-size="11" font-weight="600" fill="${e.c}">${esc(e.t)}</text>`;
  for (const it of items) {
    const y = 34 + it.row * 17;
    if (it.s) { const s = it.s; b += `<line x1="${it.x}" x2="${it.x + 22}" y1="${y}" y2="${y}" stroke="${s.color}" stroke-width="2.4" ${s.dash ? `stroke-dasharray="${s.dash}"` : ""}/>` + marker(s.mk || "circle", it.x + 11, y, s.color, 3.2) + `<text x="${it.x + 27}" y="${y + 4}" font-size="11" fill="${COL.fg}">${esc(s.name)}</text>`; }
    else b += `<rect x="${it.x}" y="${y - 5}" width="18" height="10" fill="${it.band.color}" fill-opacity="0.35"/><text x="${it.x + 23}" y="${y + 4}" font-size="11" fill="${COL.fg}">${esc(it.band.name)}</text>`;
  }
  return svgWrap(w, h, b, o.title, o.desc);
}
/* çubuk: o.bars [{a,b,v}] aralık a..b */
function barChart(o) {
  const w = o.w || 360, h = (o.h || 200) + 16, m = { l: 46, r: 10, t: 30, b: 44 };
  const x0 = o.bars[0].a, x1 = o.bars[o.bars.length - 1].b, ymax = niceMax(Math.max(...o.bars.map(x => x.v)));
  const ticks = []; for (let i = 0; i <= 4; i++) { const v = x0 + (x1 - x0) * i / 4; ticks.push({ v, l: v.toFixed(1) }); }
  const ax = axes(w, h, m, x0, x1, 0, ymax, { xticks: ticks, yLabel: o.yLabel });
  let b = ax.s;
  for (const r of o.bars) b += `<rect x="${ax.X(r.a) + 0.5}" y="${ax.Y(r.v)}" width="${Math.max(1, ax.X(r.b) - ax.X(r.a) - 1)}" height="${Math.max(0, h - m.b - ax.Y(r.v))}" fill="${o.color}"/>`;
  for (const mk of (o.marks || [])) b += `<line x1="${ax.X(mk.x)}" x2="${ax.X(mk.x)}" y1="${m.t}" y2="${h - m.b}" stroke="${PAL.mark}" stroke-dasharray="4 3"/><text x="${ax.X(mk.x) + 3}" y="${m.t + 9 + (mk.dy || 0)}" font-size="10" fill="${PAL.mark}">${esc(mk.label)}</text>`;
  b += `<text x="${w / 2}" y="14" text-anchor="middle" font-size="12" font-weight="700" fill="${o.color}">${esc(o.head || "")}</text>`;
  if (o.xLabel) b += `<text x="${(m.l + w - m.r) / 2}" y="${h - 6}" text-anchor="middle" font-size="11" fill="${COL.muted}">${esc(o.xLabel)}</text>`;
  return svgWrap(w, h, b, o.title, o.desc);
}
/* indirme */
function saveBlob(blob, name) { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
function downloadSVG(svg, name) { saveBlob(new Blob([svg], { type: "image/svg+xml" }), name + ".svg"); }
function downloadPNG(svg, name, scale) {
  const img = new Image(), url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
  img.onload = () => { const c = document.createElement("canvas"), k = scale || 2; c.width = img.width * k; c.height = img.height * k; const x = c.getContext("2d"); x.scale(k, k); x.drawImage(img, 0, 0); URL.revokeObjectURL(url); c.toBlob(b => saveBlob(b, name + ".png")); };
  img.src = url;
}
