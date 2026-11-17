// Lintu FireAtlas · © 2026 Team Lintu · AGPL-3.0 · https://github.com/Lintuteam/lintu-fireatlas
/* v2.2 eklentileri: takvim ayrıntısı (ay / yıl / gün), seçim etiketi, haritada 2012 sıçrama modu.
   main.js'teki S, MX, LASTITEMS, t, fill, esc, $, $$, goToEvent, refresh, showTab kullanılır. */
"use strict";
const XT = (() => {
  const MONTHS = () => MN();
  const ftName = () => t("ft.name_" + (S.ft === "custom" ? "noaniz" : S.ft));

  /* ---- yardımcı: LASTITEMS içindeki olay indeksini bul (y, i) -> k ---- */
  let lookup = null, lookupFor = null;
  function kOf(y, i) {
    if (lookupFor !== LASTITEMS) { lookup = new Map(); for (let k = 0; k < LASTITEMS.n; k++) lookup.set(LASTITEMS.y[k] * 1e7 + LASTITEMS.i[k], k); lookupFor = LASTITEMS; }
    return lookup.get(y * 1e7 + i);
  }
  function evLine(o) {
    const e = D.ev[o.y], i = o.i, k = kOf(o.y, i);
    return `<li><span>${esc(D.man.ils[e.il[i]] || "–")} · ${dayISO(trDay(e.tmin[i]))} · ${fmtN(e.n_modis[i] + e.n_viirs[i])} ${esc(t("w.det"))} · <b>${esc(t("w.peak"))} ${fmtN(e.frp_max[i], 0)} MW</b> <small>(${esc(t("w.sumfrp"))} ${fmtN(e.frp_sum[i], 0)} MW)</small></span>${k !== undefined ? ` <button type="button" class="mini" data-k="${k}">${esc(t("cal.showmap"))}</button>` : ""}</li>`;
  }
  // süzgeçteki olaylar, TR gününe göre [d0, d1] aralığında
  function eventsBetween(d0, d1) {
    const F = makeFilter(S), out = [], y0 = dayYMD(d0)[0], y1 = dayYMD(d1)[0], ys = D.man.yillar.filter(y => y >= y0 - 1 && y <= y1 + 1);
    eachEvent(F, (e, i, y) => { const d = trDay(e.tmin[i]); if (d >= d0 && d <= d1) out.push({ y, i, f: e.frp_max[i], d, h: F.hid(e, i) }); }, ys);
    return out;
  }
  const top = (arr, n) => arr.filter(o => !o.h).sort((a, b) => b.f - a.f).slice(0, n); // gizli sanayi artıkları listelere girmez (sayılır)

  /* ---- takvim: ay hücresi ve yıl satırı ---- */
  function provTop(L, n) {
    const c = new Map(); for (const o of L) { const nm = D.man.ils[D.ev[o.y].il[o.i]] || "–"; c.set(nm, (c.get(nm) || 0) + 1); }
    return [...c].sort((a, b) => b[1] - a[1]).slice(0, n);
  }
  function monthRange(y, m) { const d0 = dateToDay(`${y}-${String(m + 1).padStart(2, "0")}-01`); return [d0, d0 + daysInMonth(y, m + 1) - 1]; }
  function monthDetail(y, m) {
    const [d0, d1] = monthRange(y, m);
    const L = eventsBetween(Math.max(d0, S.from), Math.min(d1, S.to)), days = new Set(L.map(o => o.d)).size;
    let h = `<h3>${esc(fill("cal.month_head", { m: MONTHS()[m], y, n: fmtN(L.length) }))}</h3><p class="small dim">${esc(fill("cal.measured_note", { ft: ftName() }))} · ${esc(fill("cal.days_fire", { d: days }))}</p>`;
    if (L.length) {
      let nm = 0, nv = 0; for (const o of L) { const e = D.ev[o.y]; nm += e.n_modis[o.i]; nv += e.n_viirs[o.i]; }
      const pm = nm + nv ? Math.round(100 * nm / (nm + nv)) : 0;
      let cmp = "";
      if (y - 1 >= D.man.yillar[0]) {
        const [p0, p1] = monthRange(y - 1, m);
        if (p0 >= S.from && p1 <= S.to && d0 >= S.from && d1 <= S.to) {
          const pc = eventsBetween(p0, p1).length, df = L.length - pc, pct = pc ? Math.round(100 * df / pc) : null;
          cmp = fill("cal.vsprev", { y: y - 1, p: fmtN(pc), c: (df > 0 ? "+" : "") + fmtN(df) + (pct === null ? "" : " (" + (pct > 0 ? "+" : "") + pct + "%)") });
        } else cmp = t("cal.vsprev_na");
      }
      h += `<p class="kv"><b>${esc(fill("cal.stat_count", { n: fmtN(L.length), d: days }))}</b></p>`;
      if (cmp) h += `<p class="small">${esc(cmp)}</p>`;
      h += `<p class="small">${esc(fill("cal.sens", { m: pm, v: 100 - pm }))}</p>`;
      h += `<h4>${esc(t("cal.top5"))}</h4><ol class="evlist">${top(L, 5).map(evLine).join("")}</ol>`;
      h += `<h4>${esc(t("cal.prov5"))}</h4><ol class="evlist">${provTop(L, 5).map(([n, c]) => `<li><span>${esc(n)} · <b>${fmtN(c)}</b> (${Math.round(100 * c / L.length)}%)</span></li>`).join("")}</ol>`;
    } else h += `<p>${esc(t("cal.none"))}</p>`;
    h += `<p><button type="button" class="hot2 tomap" data-tomap="${y}-${m}">${esc(t("cal.tomap"))}</button> <span class="small dim">${esc(t("cal.tomap_hint"))}</span></p>`;
    show("#calDetail", h);
    $$("#matrix td.sel").forEach(x => x.classList.toggle("sel", false));
    const td = $(`#matrix td.mc[data-y="${y}"][data-m="${m}"]`); if (td) td.classList.add("sel");
  }
  function monthToMap(y, m) {
    const [d0, d1] = monthRange(y, m);
    $("#dFrom").value = dayISO(Math.max(d0, D.dataFirst)); $("#dTo").value = dayISO(Math.min(d1, D.dataLast));
    refresh().then(() => showTab("map"));
  }
  function yearDetail(y) {
    const L = eventsBetween(Math.max(dateToDay(`${y}-01-01`), S.from), Math.min(dateToDay(`${y}-12-31`), S.to));
    const mc = new Array(12).fill(0); for (const o of L) mc[dayYMD(o.d)[1] - 1]++;
    const bm = mc.indexOf(Math.max(...mc)), mx = Math.max(1, ...mc), mn = MONTHS();
    let h = `<h3>${esc(fill("cal.year_head", { y, n: fmtN(L.length), m: mn[bm], mn: fmtN(mc[bm]) }))}</h3><p class="small dim">${esc(fill("cal.measured_note", { ft: ftName() }))}</p>`;
    h += `<div class="mbars" role="img" aria-label="${esc(mn.map((x, i) => x + " " + mc[i]).join(", "))}">${mc.map((v, i) => `<button type="button" class="mbar${i === bm ? " on" : ""}" data-y="${y}" data-m="${i}" title="${esc(mn[i] + ": " + fmtN(v))}"><i style="height:${Math.round(100 * v / mx)}%"></i><span>${esc(mn[i])}</span></button>`).join("")}</div>`;
    h += L.length ? `<h4>${esc(t("cal.biggest_year"))}</h4><ol class="evlist">${top(L, 5).map(evLine).join("")}</ol>` : `<p>${esc(t("cal.none"))}</p>`;
    show("#calDetail", h);
  }
  function show(sel, h) { const el = $(sel); el.innerHTML = h; el.hidden = false; }

  /* ---- gün gün ---- */
  function dayDetail(d) {
    const L = eventsBetween(d, d), iso = dayISO(d);
    let ob = -1; const C = D.cov; for (let k = 0; k < C.day.length; k++) if (C.day[k] === d) { ob = Math.max(ob, C.obs[k] ? 1 : 0); }
    let h = `<h3>${esc(fill("dg.day_head", { d: iso, n: fmtN(L.length) }))}</h3>`;
    if (ob === 0 && !L.length) h += `<p class="warnTxt">${esc(fill("dg.noobs_day", { d: iso }))}</p>`;
    h += `<p class="small dim">${esc(fill("cal.measured_note", { ft: ftName() }))}</p>`;
    if (L.length) h += `<ol class="evlist">${top(L, 8).map(evLine).join("")}</ol><button type="button" class="mini hot2" data-dayall="${d}">${esc(t("dg.day_map"))}</button>`;
    show("#dayDetail", h);
    $$("#dayGrid td.sel").forEach(x => x.classList.remove("sel"));
    const td = $(`#dayGrid td[data-d="${d}"]`); if (td) td.classList.add("sel");
  }
  function showDayOnMap(d) {
    $("#dFrom").value = dayISO(d); $("#dTo").value = dayISO(d);
    refresh().then(() => showTab("map"));
  }

  /* ---- işaretler: ★ en çok yangın, 🔥 en güçlü tek yangın (yıl satırı + genel) ---- */
  function mk(cls, tip) { return `<span class="mk ${cls}" title="${esc(tip)}">${cls.indexOf("fire") >= 0 ? "🔥" : "★"}</span>`; }
  function markRowMax() {
    const on = $("#rowMaxChk") && $("#rowMaxChk").checked;
    $$("#matrix td.rmax, #matrix td.gstar, #matrix td.gfire").forEach(x => { x.classList.remove("rmax", "gstar", "gfire"); });
    $$("#matrix .mk").forEach(x => x.parentNode.removeChild(x));
    if (!MX) return;
    const mf = new Map(); // yıl*12+ay -> o ayın en yüksek tepe FRP'si (frp_max, MW; uydu sayısına en az bağımlı ölçüt)
    const Fm = makeFilter(S);
    eachEvent(Fm, (e, i) => { if (Fm.hid(e, i)) return; const [yy, mo] = dayYMD(trDay(e.tmin[i])), k = yy * 12 + mo - 1; if (e.frp_max[i] > (mf.get(k) || 0)) mf.set(k, e.frp_max[i]); });
    const best = { s: [-1, null, -1], f: [-1, null, -1] };
    const rows = D.man.yillar.map(y => {
      const g = MX.grid[y]; let bi = -1, bv = 0, fi = -1, fv = 0;
      g.forEach((c, i) => { if (c.v !== null && c.v > bv) { bv = c.v; bi = i; } const f = mf.get(y * 12 + i) || 0; if (c.v !== null && f > fv) { fv = f; fi = i; } });
      if (bv > best.s[0]) best.s = [bv, y, bi]; if (fv > best.f[0]) best.f = [fv, y, fi];
      return [y, bi, fi, fv];
    });
    const put = (y, m, cls, tip) => { const td = $(`#matrix td.mc[data-y="${y}"][data-m="${m}"]`); if (td) td.insertAdjacentHTML("beforeend", mk(cls, tip)); return td; };
    for (const [y, bi, fi, fv] of rows) {
      if (bi >= 0) { const g = best.s[1] === y && best.s[2] === bi, td = put(y, bi, g ? "star g" : "star", t("cal.mk_star")); if (td) { if (on) td.classList.add("rmax"); if (g) td.classList.add("gstar"); } }
      if (fi >= 0) { const g = best.f[1] === y && best.f[2] === fi, td = put(y, fi, g ? "fire g" : "fire", t("cal.mk_fire") + ": " + fmtN(fv, 0) + " MW"); if (td && g) td.classList.add("gfire"); }
    }
  }
  /* gün ızgarası: ★ en çok yangın günü, 🔥 en güçlü yangın günü (seçili yıl) */
  function markDayExtremes() {
    $$("#dayGrid td.dmax, #dayGrid td.dfrp").forEach(x => { x.classList.remove("dmax", "dfrp"); delete x.dataset.mk; x.textContent = ""; });
    const y = S.year, f = dateToDay(`${y}-01-01`), l = dateToDay(`${y}-12-31`), n = new Map(), fr = new Map();
    for (const o of eventsBetween(f, l)) { n.set(o.d, (n.get(o.d) || 0) + 1); if (!o.h && o.f > (fr.get(o.d) || 0)) fr.set(o.d, o.f); }
    const arg = m => { let bd = null, bv = 0; for (const [d, v] of m) if (v > bv || (v === bv && bd !== null && d < bd)) { bv = v; bd = d; } return bd; };
    const ds = arg(n), df = arg(fr);
    const tag = (d, cls, glyph, tip) => { const td = d === null ? null : $(`#dayGrid td[data-d="${d}"]`); if (!td) return; td.classList.add(cls); td.dataset.mk = (td.dataset.mk || "") + glyph; td.textContent = td.dataset.mk; td.title += " · " + tip; };
    tag(ds, "dmax", "★", t("cal.mk_star") + ": " + (ds === null ? "" : fmtN(n.get(ds))));
    tag(df, "dfrp", "🔥", t("cal.mk_fire") + ": " + (df === null ? "" : fmtN(fr.get(df), 0) + " MW"));
  }
  /* ---- Ay ay / Gün gün geçişi ---- */
  let VIEW = "month";
  function setView(v) {
    VIEW = v; $("#calMonthView").hidden = v !== "month"; $("#calDayView").hidden = v !== "day";
    $("#cvMonth").setAttribute("aria-pressed", String(v === "month")); $("#cvDay").setAttribute("aria-pressed", String(v === "day"));
    $("#cvHint").textContent = t(v === "month" ? "cal.hint_month" : "cal.hint_day");
  }
  function markDays() { // gün ızgarasına tıklanabilirlik
    $$("#dayGrid td.dg:not(.pad)").forEach(td => { td.tabIndex = -1; });
  }

  /* ---- seçim etiketi ---- */
  function selChip() {
    const on = S.region.type !== "tr", chip = $("#selChip");
    chip.hidden = !on; $("#regClr").hidden = !on;
    if (on) $("#selChipTxt").textContent = fill("map.sel", { r: regionLabel(S.region, t) });
  }

  /* ---- 2012 sıçrama modu (harita) ---- */
  const JY = [2009, 2010, 2011, 2012, 2013, 2014, 2015];
  const J = { on: false, year: 2012, stage: 0, data: null, timer: null };
  async function jumpData() {
    if (J.data) return J.data;
    $("#jmInfo").textContent = t("jm.loading");
    const per = [{}, {}, {}], tot = [{}, {}, {}];
    for (const y of JY) {
      const P = await loadYear("pt", y), a = {}, c = {}; let na = 0, nc = 0;
      for (let i = 0; i < P.n; i++) { if (P.st[i] !== 0) continue; a[P.il[i]] = (a[P.il[i]] || 0) + 1; na++; if (P.sat[i] <= 1) { c[P.il[i]] = (c[P.il[i]] || 0) + 1; nc++; } }
      const e = D.ev[y], b = {}; let nb = 0; for (let i = 0; i < e.n; i++) { if (e.st[i] !== 0) continue; b[e.il[i]] = (b[e.il[i]] || 0) + 1; nb++; }
      per[0][y] = a; per[1][y] = b; per[2][y] = c; tot[0][y] = na; tot[1][y] = nb;
    }
    const R = yearRows(); for (const y of JY) tot[2][y] = D.harm.ana_seri[R[y]];
    const mx = per.map(p => { let m = 0; for (const y of JY) for (const k in p[y]) if (+k !== 255 && p[y][k] > m) m = p[y][k]; return m; });
    J.data = { per, tot, mx };
    $("#jmInfo").textContent = "";
    return J.data;
  }
  const pctWin = arr => { const a = (arr[2009] + arr[2010] + arr[2011]) / 3, b = (arr[2012] + arr[2013] + arr[2014]) / 3; return (b / a - 1) * 100; };
  function jumpChart(Dt) {
    const W = 300, H = 178, l = 34, r = 8, tp = 40, bt = 22, cols = [PAL.ham, PAL.kume, PAL.duz], dsh = [PAL_STYLE.ham.dash, PAL_STYLE.kume.dash, PAL_STYLE.duz.dash], mks = [PAL_STYLE.ham.mk, PAL_STYLE.kume.mk, PAL_STYLE.duz.mk];
    const idx = Dt.tot.map(s => { const base = (s[2009] + s[2010] + s[2011]) / 3; return JY.map(y => s[y] / base * 100); });
    const ymax = Math.max(260, ...idx.flat()), X = i => l + i * (W - l - r) / (JY.length - 1), Y = v => tp + (H - tp - bt) * (1 - v / ymax);
    let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(t("jm.chart"))}">`;
    for (const v of [0, 100, 200]) s += `<line x1="${l}" x2="${W - r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#1b2630"/><text x="${l - 4}" y="${Y(v) + 3}" text-anchor="end" font-size="9" fill="#a3afbc">${v}</text>`;
    const xi = JY.indexOf(J.year); s += `<rect x="${X(xi) - 9}" y="${tp}" width="18" height="${H - tp - bt}" fill="rgba(94,234,212,.12)"/>`;
    s += `<line x1="${X(3)}" x2="${X(3)}" y1="${tp}" y2="${H - bt}" stroke="${PAL.mark}" stroke-dasharray="1 3"/><text x="${X(3) + 3}" y="${tp + 8}" font-size="9" fill="${PAL.mark}">VIIRS</text>`;
    s += `<text x="2" y="9" font-size="9" fill="#a3afbc">${esc(t("jm.ylab"))}</text>`;
    [0, 1, 2].forEach(k => { const lx = 2 + k * 99; s += `<line x1="${lx}" x2="${lx + 14}" y1="22" y2="22" stroke="${cols[k]}" stroke-width="2" ${dsh[k] ? `stroke-dasharray="${dsh[k]}"` : ""}/>` + marker(mks[k], lx + 7, 22, cols[k], 2.6) + `<text x="${lx + 17}" y="25" font-size="9" fill="${k === J.stage ? "#e6edf3" : "#a3afbc"}" font-weight="${k === J.stage ? 700 : 400}">${esc(t("jm.l" + (k + 1)))}</text>`; });
    idx.forEach((a, k) => { s += `<polyline fill="none" stroke="${cols[k]}" stroke-width="${k === J.stage ? 3 : 1.4}" ${dsh[k] ? `stroke-dasharray="${dsh[k]}"` : ""} opacity="${k === J.stage ? 1 : .6}" points="${a.map((v, i) => X(i).toFixed(1) + "," + Y(v).toFixed(1)).join(" ")}"/>`; });
    JY.forEach((y, i) => { s += `<text x="${X(i)}" y="${H - 6}" text-anchor="middle" font-size="9" fill="${y === J.year ? "#5eead4" : "#a3afbc"}">${y}</text>`; });
    return s + "</svg>";
  }
  async function jumpRender() {
    const Dt = await jumpData(), st = J.stage, cnt = Dt.per[st][J.year], mx = Dt.mx[st];
    MV.choro.eachLayer(l => {
      const idx = l.feature.properties.idx, n = cnt[idx] || 0;
      l.setStyle({ fillColor: n ? palColor("ylorrd", Math.sqrt(n / mx)) : "#10202b", fillOpacity: 0.85, color: "#5b6b7b", weight: 1 });
      l.setTooltipContent(fill("jm.tip", { il: l.feature.properties.name, n: fmtN(n) }));
    });
    $$("#jmStages [data-st]").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.st === st)));
    $$("#jmYears [data-y]").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.y === J.year)));
    $("#jmDesc").textContent = t("jm.d" + (st + 1));
    $("#jmTotal").innerHTML = `<span class="jmn">${fmtN(Dt.tot[st][J.year])}</span> <span class="dim">${esc(t("jm.u" + (st + 1)))} · ${J.year}</span>`;
    $("#jmChart").innerHTML = jumpChart(Dt);
    $("#jmChange").textContent = fill("jm.change", { a: sg(pctWin(Dt.tot[0])), b: sg(pctWin(Dt.tot[1])), c: sg(pctWin(Dt.tot[2])), d: sg(mval("jump_modis_gercek_pct")), e: sg(mval("olay_temiz_jump_raw_pct")) });
    $("#choroLegend").innerHTML = `<span class="ramp2" style="background:linear-gradient(90deg,${PALETTES.ylorrd.join(",")})"></span><br>${esc(fill("jm.legend", { mx: fmtN(mx) }))}`;
    $("#choroTitle").textContent = t("jm.title");
  }
  function jumpToggle(on) {
    J.on = on; clearInterval(J.timer); J.timer = null; $("#jmPlay").textContent = t("jm.play");
    $("#jmPanel").hidden = !on; $("#jumpModeBtn").setAttribute("aria-pressed", String(on));
    $("#jumpModeBtn").textContent = t(on ? "jm.exit" : "jm.btn");
    document.body.classList.toggle("jumpmode", on);
    if (S.tab !== "map") showTab("map");
    if (on) { MV.map.removeLayer(MV.ev); MV.showRegion({ type: "tr" }); jumpRender(); }
    else { MV.ev.addTo(MV.map); refresh(); }
  }

  function afterRefresh() { markRowMax(); markDays(); markDayExtremes(); selChip(); setView(VIEW); if (J.on) jumpRender(); }

  function bind() {
    $("#matrix").addEventListener("click", e => {
      const td = e.target.closest("td.mc"); if (td) { if (td.classList.contains("oos")) return monthDetail(+td.dataset.y, +td.dataset.m); monthDetail(+td.dataset.y, +td.dataset.m); return monthToMap(+td.dataset.y, +td.dataset.m); } // tek tıklama: doğrudan haritaya (ayrıntı paneli takvime dönünce hazır)
      const th = e.target.closest("tbody th[scope=row]"); if (th && /^\d{4}$/.test(th.textContent.trim())) yearDetail(+th.textContent.trim());
    });
    $("#matrix").addEventListener("keydown", e => { if (e.key === "Enter") { const td = e.target.closest("td.mc"); if (td && !td.classList.contains("oos")) { monthDetail(+td.dataset.y, +td.dataset.m); monthToMap(+td.dataset.y, +td.dataset.m); } } });
    $$(".calview button").forEach(b => b.addEventListener("click", () => setView(b.dataset.view)));
    $("#calDetail").addEventListener("click", e => { const tm = e.target.closest("[data-tomap]"); if (tm) { const [yy, mm] = tm.dataset.tomap.split("-"); return monthToMap(+yy, +mm); } const b = e.target.closest("[data-k]"); if (b) return goToEvent(+b.dataset.k); const m = e.target.closest(".mbar"); if (m) monthDetail(+m.dataset.y, +m.dataset.m); });
    $("#dayDetail").addEventListener("click", e => { const b = e.target.closest("[data-k]"); if (b) return goToEvent(+b.dataset.k); const a = e.target.closest("[data-dayall]"); if (a) showDayOnMap(+a.dataset.dayall); });
    $("#dayGrid").addEventListener("click", e => { const td = e.target.closest("td[data-d]"); if (td) dayDetail(+td.dataset.d); });
    $("#dayPick").addEventListener("change", e => {
      const v = e.target.value; if (!v) return; const d = dateToDay(v), y = dayYMD(d)[0];
      if (!D.man.yillar.includes(y)) return;
      S.year = y; $("#yearSel").value = y; renderDayGrid(); markDays(); markDayExtremes(); dayDetail(d);
    });
    $("#rowMaxChk").addEventListener("change", markRowMax);
    $("#selChipX").addEventListener("click", () => $("#clrBtn").click());
    $("#regClr").addEventListener("click", () => $("#clrBtn").click());
    $("#jumpModeBtn").addEventListener("click", () => jumpToggle(!J.on));
    $("#jmStages").addEventListener("click", e => { const b = e.target.closest("[data-st]"); if (b) { J.stage = +b.dataset.st; jumpRender(); } });
    $("#jmYears").innerHTML = JY.map(y => `<button type="button" data-y="${y}" class="${y === 2012 ? "vy" : ""}">${y}</button>`).join("");
    $("#jmYears").addEventListener("click", e => { const b = e.target.closest("[data-y]"); if (b) { J.year = +b.dataset.y; jumpRender(); } });
    $("#jmPlay").addEventListener("click", () => {
      if (J.timer) { clearInterval(J.timer); J.timer = null; $("#jmPlay").textContent = t("jm.play"); return; }
      $("#jmPlay").textContent = t("jm.stop"); J.year = JY[0]; jumpRender();
      J.timer = setInterval(() => { const i = JY.indexOf(J.year); if (i >= JY.length - 1) { clearInterval(J.timer); J.timer = null; $("#jmPlay").textContent = t("jm.play"); return; } J.year = JY[i + 1]; jumpRender(); }, 1300);
    });
  }
  return { bind, afterRefresh, markDayExtremes, monthDetail, yearDetail, dayDetail, jumpToggle, J };
})();
window.XT = XT;
