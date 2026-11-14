/* Veri yükleme, süzme ve toplama. Hiçbir sayı burada yazılı değil (K1): her şey data/ altındaki dosyalardan gelir.
   Basitçe: yıl dosyalarını indirir, seçili bölge/tarih/sensöre göre sayar.
   Teknik olarak: ikili sütun dosyaları -> typed array; tek döngüde süzme + toplama. */
"use strict";
const DAYMS = 86400000;
const EPOCH = Date.UTC(2000, 0, 1);
const TYPES = { float64: Float64Array, float32: Float32Array, int32: Int32Array, int16: Int16Array, uint16: Uint16Array, uint8: Uint8Array, int8: Int8Array };
const D = { man: null, metrics: null, harm: null, cov: null, il: null, pix: null, lab: null, ev: {}, pt: {}, load: {} };

/* Ağ kopmalarına karşı yeniden deneme: bağlantı sıfırlanırsa (ERR_CONNECTION_RESET vb.) 4 kez daha dener. */
async function fetchRetry(u, tries = 5) {
  for (let i = 0; ; i++) {
    try { const r = await fetch(u); if (r.ok || r.status === 404 || i >= tries - 1) return r; }
    catch (e) { if (i >= tries - 1) throw e; }
    await new Promise(res => setTimeout(res, 400 * (i + 1)));
  }
}
async function getJSON(u) { const r = await fetchRetry(u); if (!r.ok) throw new Error(u + " " + r.status); return r.json(); }
function parseBin(buf, meta) {
  const c = { n: meta.n };
  for (const k of meta.kolon) c[k.ad] = new TYPES[k.tip](buf, k.ofs, meta.n);
  return c;
}
/* İsteğe bağlı bayrak dosyaları (v2.5.2): olayla aynı sıra, uint8. Dosya yoksa/uzunluk uymuyorsa hepsi 0 (bayrak yok). */
async function loadFlag(name, y, n) {
  try { const r = await fetchRetry(`data/${name}_${y}.bin`); if (r.ok) { const b = await r.arrayBuffer(); if (b.byteLength === n) return new Uint8Array(b); } } catch (e) { /* yok: sıfır */ }
  return new Uint8Array(n);
}
async function loadYear(kind, y) {
  const store = kind === "ev" ? D.ev : D.pt;
  if (store[y]) return store[y];
  const key = kind + y;
  if (!D.load[key]) {
    const meta = (kind === "ev" ? D.man.events : D.man.points)[y];
    const main = fetchRetry(`data/${kind === "ev" ? "events" : "points"}_${y}.bin`).then(r => { if (!r.ok) throw new Error("bin " + r.status); return r.arrayBuffer(); });
    const extra = kind === "ev" ? Promise.all([loadFlag("aniz_il", y, meta.n), loadFlag("sanayi_artik", y, meta.n)]) : Promise.resolve(null);
    D.load[key] = Promise.all([main, extra]).then(([b, fl]) => {
      const o = parseBin(b, meta); if (fl) { o.anizil = fl[0]; o.san = fl[1]; } store[y] = o;
      return o;
    });
  }
  return D.load[key];
}
async function loadAllEvents(onProg) {
  let i = 0; const ys = D.man.yillar, B = 6;
  for (let k = 0; k < ys.length; k += B) await Promise.all(ys.slice(k, k + B).map(async y => { await loadYear("ev", y); if (onProg) onProg(++i, ys.length); }));
}
/* Tekrarlayan yakma şüphesi: aynı ~1 km (0,01°) karede olay görülen farklı yıl sayısı (e.ny). */
const FOREST = { grid: 0.01, repeatYears: 3 }; // repeatYears: >= bu kadar farklı yıl yanan kare = tekrarlayan yakma şüphesi
function computeForest() {
  const key = (lat, lon) => Math.round(lat / FOREST.grid) * 100000 + Math.round(lon / FOREST.grid);
  const yrs = new Map();
  for (const y of D.man.yillar) { const e = D.ev[y]; if (!e) continue; for (let i = 0; i < e.n; i++) { const k = key(e.lat[i], e.lon[i]); let s = yrs.get(k); if (!s) yrs.set(k, s = new Set()); s.add(y); } }
  for (const y of D.man.yillar) {
    const e = D.ev[y]; if (!e) continue; e.ny = new Uint8Array(e.n);
    for (let i = 0; i < e.n; i++) e.ny[i] = Math.min(255, yrs.get(key(e.lat[i], e.lon[i])).size);
  }
}
/* İsteğe bağlı bayrakların özeti (açıklama metinleri için; hepsi dosyalardan hesaplanır, yazılı sayı yok). */
function flagStats() {
  if (D.fs) return D.fs;
  const ur = D.man.ils.indexOf("Şanlıurfa"); let tem = 0, ai = 0, san = 0, urT = 0, urA = 0, sanBoth = 0;
  for (const y of D.man.yillar) { const e = D.ev[y]; if (!e) continue;
    for (let i = 0; i < e.n; i++) { if (e.san && e.san[i]) san++; if (e.st[i] !== 0) continue; tem++; if (e.il[i] === ur) urT++;
      if (e.anizil && e.anizil[i]) { ai++; if (e.il[i] === ur) urA++; if (e.san && e.san[i]) sanBoth++; } } }
  return D.fs = { tem, ai, san, p: tem ? ai / tem * 100 : 0, ps: tem ? san / tem * 100 : 0, u0: tem ? urT / tem * 100 : 0, u1: tem - ai ? (urT - urA) / (tem - ai) * 100 : 0 };
}
async function initData() {
  D.man = await getJSON("data/manifest.json");
  [D.metrics, D.harm, D.cov, D.il, D.pix, D.lab] = await Promise.all(["metrics.json", "harmonized.json", "coverage.json", "il.geojson", "pixel_growth.json", "lab_examples.json"].map(f => getJSON("data/" + f)));
  D.dataFirst = 1e9; D.dataLast = -1e9;
  for (let i = 0; i < D.cov.day.length; i++) if (D.cov.obs[i]) { const d = D.cov.day[i]; if (d < D.dataFirst) D.dataFirst = d; if (d > D.dataLast) D.dataLast = d; }
}
const metric = k => D.metrics.metrics[k];
const mval = k => (D.metrics.metrics[k] || {}).value;

/* --- takvim yardımcıları (UTC tabanlı gün sayısı) --- */
const dayToDate = d => new Date(EPOCH + d * DAYMS);
const dateToDay = s => Math.round((Date.parse(s + "T00:00:00Z") - EPOCH) / DAYMS);
const dayISO = d => dayToDate(d).toISOString().slice(0, 10);
const dayYMD = d => { const x = dayToDate(d); return [x.getUTCFullYear(), x.getUTCMonth() + 1, x.getUTCDate()]; };
const trDay = (tmin) => Math.floor((tmin + D.man.tr_ofset_dk) / 1440);
const daysInMonth = (y, m) => new Date(Date.UTC(y, m, 0)).getUTCDate();

/* --- bölge --- */
function regionPred(R) {
  if (R.type === "il") return (lat, lon, il) => il === R.il;
  if (R.type === "bolge") { const set = new Set(D.man.ils.map((n, i) => D.man.il_bolge[n] === R.name ? i : -1)); return (lat, lon, il) => set.has(il); }
  if (R.type === "poly" && R.poly && R.poly.length >= 3) {
    const P = R.poly;
    return (lat, lon) => {
      let c = false;
      for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
        const yi = P[i][0], xi = P[i][1], yj = P[j][0], xj = P[j][1];
        if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) c = !c;
      }
      return c;
    };
  }
  if (R.type === "circle") {
    const k = Math.cos(R.lat * Math.PI / 180);
    return (lat, lon) => { const dy = (lat - R.lat) * 111.19, dx = (lon - R.lon) * 111.19 * k; return dx * dx + dy * dy <= R.km * R.km; };
  }
  return () => true;
}
function regionLabel(R, t) {
  if (R.type === "il") return D.man.ils[R.il];
  if (R.type === "bolge") return R.name;
  if (R.type === "poly" && R.poly && R.poly.length >= 3) return t("region.poly") + " (" + R.poly.length + ")";
  if (R.type === "circle") return `${t("region.circle")} ${R.lat.toFixed(3)}, ${R.lon.toFixed(3)}, ${R.km} km`;
  return t("region.tr");
}

/* --- süzme --- */
/* İsteğe bağlı bayraklar (varsayılan KAPALI: sayılar değişmez):
   S.anizIl   : st==0 && anizil==1 olaylar anız sayılır (il bazlı anız eşiği).
   S.sanKaldir: sanayi artığı olaylar sayımdan çıkar. S.sanGoster: sanayi artığı olaylar haritada çizilir (varsayılan gizli; sayıyı etkilemez). */
function makeFilter(S) {
  const rp = regionPred(S.region);
  let mask = 0; S.statuses.forEach(i => { mask |= 1 << i; });
  const sm = S.sensor, norep = !!S.norepeat, REP = FOREST.repeatYears, ai = !!S.anizIl, sk = !!S.sanKaldir, hideSan = !S.sanGoster && !sk;
  return {
    from: S.from, to: S.to, mask, minFrp: S.minFrp,
    est(e, i) { return ai && e.st[i] === 0 && e.anizil && e.anizil[i] ? 6 : e.st[i]; }, // etkin durum
    hid(e, i) { return hideSan && !!e.san && e.san[i] === 1; },                       // haritada/listede gizli sanayi artığı (sayılır)
    ok(e, i) {
      if (sk && e.san && e.san[i]) return false;
      if (!((mask >> (ai && e.st[i] === 0 && e.anizil && e.anizil[i] ? 6 : e.st[i])) & 1)) return false;
      if (norep && e.ny && e.ny[i] >= REP) return false; // tekrarlayan yakma şüphesi (duyarlılık)
      if (sm === "modis" ? e.n_modis[i] === 0 : sm === "viirs" ? e.n_viirs[i] === 0 : false) return false;
      if (e.frp_sum[i] < this.minFrp) return false;
      const d = trDay(e.tmin[i]);
      if (d < this.from || d > this.to) return false;
      return rp(e.lat[i], e.lon[i], e.il[i]);
    }
  };
}
// Süzülmüş olayları verilen işleve verir. Yalnız yüklü yıllar.
function eachEvent(F, fn, years) {
  for (const y of (years || D.man.yillar)) {
    const e = D.ev[y]; if (!e) continue;
    for (let i = 0; i < e.n; i++) if (F.ok(e, i)) fn(e, i, y);
  }
}

/* --- yıl x ay matrisi (U-16) --- */
function monthCoverage(y, m, S) {
  const a = Math.max(S.from, D.dataFirst), b = Math.min(S.to, D.dataLast);
  const f = dateToDay(`${y}-${String(m).padStart(2, "0")}-01`), l = f + daysInMonth(y, m) - 1;
  if (l < a || f > b) return "yok";
  return (f >= a && l <= b) ? "tam" : "kismi";
}
function median(a) { if (!a.length) return null; const s = [...a].sort((x, y) => x - y), k = s.length >> 1; return s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2; }

/* --- hazır takvim tabloları (agg/, takvim-analiz çıktısı): tek kaynak (U-19) --- */
D.cal = {};
async function loadCal(birim) {
  const e = D.man.birimler.find(b => b.ad === birim); if (!e) return null;
  if (!D.cal[birim]) D.cal[birim] = await getJSON("data/" + e.dosya);
  return D.cal[birim];
}
const regionBirim = R => R.type === "tr" ? "TR" : R.type === "il" ? D.man.ils[R.il] : R.type === "bolge" ? R.name : null;
// Hazır tablo yalnız: TR/bölge/il + varsayılan süzgeçler (temiz, il bazlı anız ve sanayi çıkarma kapalı, FRP sınırı yok, tüm sensör, tüm tarih). Aksi halde tarayıcıda hesaplanır.
function isDefaultFilters(S) { return !S.norepeat && !S.anizIl && !S.sanKaldir && S.statuses.size === 1 && S.statuses.has(0) && S.minFrp === 0 && S.sensor === "all" && S.from <= D.dataFirst && S.to >= D.dataLast; }
const aggMode = S => !!regionBirim(S.region) && isDefaultFilters(S);
// Tarayıcı içi aylık sayım (olay tablosundan): tutarlılık testi (tests/tutarlilik_check.py) bu işlevi çalıştırır.
function browserMonthly(S) {
  const cnt = {}, F = makeFilter(S), frp = S.metric === "frp";
  eachEvent(F, (e, i) => { const d = dayYMD(trDay(e.tmin[i])), k = d[0] * 12 + d[1]; cnt[k] = (cnt[k] || 0) + (frp ? e.frp_sum[i] : 1); });
  return cnt;
}

const VIIRS_Y0 = 2012; // VIIRS (S-NPP) FIRMS kayıtları Ocak 2012'de başlar
const eraOf = y => (y >= VIIRS_Y0 ? 1 : 0); // 0: yalnız MODIS dönemi, 1: MODIS + VIIRS dönemi
function buildMatrix(S) {
  const ys = D.man.yillar, grid = {}, agg = aggMode(S), cal = agg ? D.cal[regionBirim(S.region)] : null;
  let sr = null, ser = null, prof = null;
  if (agg) { sr = cal.seri[S.aggSeries] ? S.aggSeries : "olay"; ser = cal.seri[sr]; prof = cal.profil[sr]; }
  const cnt = agg ? null : browserMonthly(S);
  for (const y of ys) {
    grid[y] = [];
    for (let m = 1; m <= 12; m++) {
      let v = null, lo = null, hi = null, flag = "", an = null, cov = "yok", iso = "", uy = "";
      if (agg) {
        const k = (y - cal.y0) * 12 + m - 1; v = ser.v[k]; lo = ser.lo[k]; hi = ser.hi[k]; an = ser.an[k];
        iso = cal.tablo[ser.iso[k]]; uy = cal.tablo[ser.uy[k]] + (cal.bay && cal.tablo[cal.bay[k]] ? ";" + cal.tablo[cal.bay[k]] : ""); flag = ser.sg[k] ? "gecis" : "";
        cov = v === null ? "yok" : "tam";
      } else {
        cov = monthCoverage(y, m, S); if (cov !== "yok") v = cnt[y * 12 + m] || 0;
      }
      grid[y].push({ v, lo, hi, cov, flag, an, iso, uy });
    }
  }
  let med, full, top3, rank, ayirt = new Array(12).fill(false);
  if (agg) {
    med = prof.map(r => r ? r.med : null); full = prof.map(r => r ? r.n : 0);
    top3 = prof.map((r, i) => r && r.top ? i : -1).filter(i => i >= 0);
    rank = prof.map((r, i) => [r && r.sira, i]).filter(x => x[0] !== null && x[0] !== undefined).sort((a, b) => a[0] - b[0]).map(x => x[1]);
    prof.forEach((r, i) => { if (r) ayirt[i] = r.ayirt; });
  } else {
    // Ölçülen (düzeltilmemiş) sayımda 2012'de VIIRS eklenince sayılar ~5 kat sıçrar. Normal (medyan) her ay için
    // AYNI UYDU DÖNEMİNİN yıllarından alınır: yoksa eski tek-MODIS yılları normali düşürür ve yeni aylar sahte +%400 görünür.
    const medE = { 0: [], 1: [] }, fullE = { 0: [], 1: [] };
    for (const e of [0, 1]) for (let m = 0; m < 12; m++) { const a = []; for (const y of ys) { if (eraOf(y) !== e) continue; const c = grid[y][m]; if (c.v !== null && c.cov === "tam") a.push(c.v); } medE[e].push(median(a)); fullE[e].push(a.length); }
    med = medE[1]; full = fullE[1]; // gösterilen medyan satırı: güncel (MODIS+VIIRS) dönem
    for (const y of ys) for (let m = 0; m < 12; m++) { const c = grid[y][m], md = medE[eraOf(y)][m]; c.an = (c.v !== null && md) ? (c.v - md) / md * 100 : null; c.medE = md; }
    rank = med.map((v, i) => [v, i]).filter(x => x[0] !== null).sort((a, b) => b[0] - a[0]).map(x => x[1]); top3 = rank.slice(0, 3);
  }
  let cur = [];
  if (agg) { const cs = [sr, "modis_esdeger", "modis_temiz"].find(k => cal.mevcut[k]);
    cur = cs ? cal.mevcut[cs].map(r => {
      const p = r.guvensiz && r.birincil !== cs ? (cal.mevcut[r.birincil] || []).find(x => x.hedef === r.hedef) : null; // F4-01: güvenilmezse birincil seri ana değer
      return Object.assign({}, r, { uyTxt: cal.tablo[r.uy], curSeri: cs, matSeri: sr, prim: p ? Object.assign({}, p, { uyTxt: cal.tablo[p.uy] }) : null });
    }) : []; }
  else { // son TAM ay: veri ay sonuna ulaşmadıysa bir önceki ay (yarım ayı tam ay medyanıyla kıyaslama)
    let [ly, lm, ld] = dayYMD(D.dataLast);
    if (ld < daysInMonth(ly, lm)) { lm -= 1; if (lm < 1) { lm = 12; ly -= 1; } ld = daysInMonth(ly, lm); }
    const c = grid[ly] ? grid[ly][lm - 1] : null, mm = String(lm).padStart(2, "0");
    if (c && c.v !== null) cur = [{ hedef: "son_tam_ay", bas: `${ly}-${mm}-01`, bit: `${ly}-${mm}-${String(ld).padStart(2, "0")}`, gun: ld, v: c.v, med: med[lm - 1], oran: med[lm - 1] ? c.v / med[lm - 1] : null, yuzdelik: null, n_yil: full[lm - 1], uyTxt: "" }]; }
  return { grid, med, full, top3, rank, ayirt, cur, mode: agg ? "agg" : "browser", seri: sr, cal };
}

/* --- gün x hafta ızgarası: olay sayısı + gerçek kapsam (coverage.parquet) --- */
function buildDayGrid(S, year) {
  const f = dateToDay(`${year}-01-01`), l = dateToDay(`${year}-12-31`);
  const n = new Array(l - f + 1).fill(0);
  eachEvent(makeFilter(S), (e, i) => { const d = trDay(e.tmin[i]); if (d >= f && d <= l) n[d - f] += 1; }, [year]);
  const obs = new Array(l - f + 1).fill(-1); // -1 kapsam kaydı yok, 0 gözlenmedi, 1 gözlendi
  const C = D.cov;
  for (let i = 0; i < C.day.length; i++) { const d = C.day[i]; if (d >= f && d <= l && C.obs[i]) obs[d - f] = 1; }
  for (let i = 0; i < C.day.length; i++) { const d = C.day[i]; if (d >= f && d <= l && !C.obs[i] && obs[d - f] !== 1) obs[d - f] = 0; }
  return { f, l, n, obs };
}

/* --- palet --- */
const PALETTES = {
  viridis: ["#440154", "#472d7b", "#3b528b", "#2c728e", "#21918c", "#28ae80", "#5ec962", "#addc30", "#fde725"],
  cividis: ["#00224e", "#123570", "#3b496c", "#575d6d", "#707173", "#8a8678", "#a59c74", "#c3b369", "#e1cc55", "#fee838"],
  ylorrd: ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#bd0026", "#800026"]
};
const hex2rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
function palColor(name, t) {
  const p = PALETTES[name]; t = Math.max(0, Math.min(1, t));
  const x = t * (p.length - 1), i = Math.min(p.length - 2, Math.floor(x)), f = x - i;
  const a = hex2rgb(p[i]), b = hex2rgb(p[i + 1]);
  return "rgb(" + a.map((v, k) => Math.round(v + (b[k] - v) * f)).join(",") + ")";
}
// diverging (anomali) için: mavi-beyaz-turuncu, renk körü güvenli ikili
function divColor(t) { // t in [-1,1]
  const neg = ["#f7f7f7", "#92c5de", "#2166ac"], pos = ["#f7f7f7", "#fdae61", "#b2182b"];
  const p = t < 0 ? neg : pos, a = Math.min(1, Math.abs(t)) * 2, i = Math.min(1, Math.floor(a)), f = a - i;
  const c0 = hex2rgb(p[i]), c1 = hex2rgb(p[i + 1]);
  return "rgb(" + c0.map((v, k) => Math.round(v + (c1[k] - v) * f)).join(",") + ")";
}
