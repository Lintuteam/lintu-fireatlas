/* CSV üretimi (C17). Saf işlev: tarayıcıda window.CSVU, Node'da module.exports (tests/csv_check.py). */
(function (root) {
  var BOM = "\uFEFF";
  // Formül enjeksiyonu: metin hücre = + - @ TAB CR ile başlarsa başına tek tırnak konur. Sayılar dokunulmaz.
  function safeText(s) {
    s = String(s);
    return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
  }
  function cell(v) {
    if (v === null || v === undefined) return "";
    if (typeof v === "number") return Number.isFinite(v) ? String(v) : "";
    var s = safeText(v);
    return /[",\r\n;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function iso(ms) {
    var d = new Date(ms);
    return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate()) + " " + pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes());
  }
  var EPOCH = Date.UTC(2000, 0, 1);
  // tmin: 2000-01-01 UTC'den dakika. t_tr = UTC + 3 saat (K11)
  function tUtc(tmin) { return iso(EPOCH + tmin * 60000); }
  function tTr(tmin, ofsMin) { return iso(EPOCH + (tmin + ofsMin) * 60000); }
  function toCSV(cols, rows) {
    var out = [cols.map(cell).join(",")];
    for (var i = 0; i < rows.length; i++) out.push(rows[i].map(cell).join(","));
    return BOM + out.join("\r\n") + "\r\n";
  }
  var api = { BOM: BOM, safeText: safeText, cell: cell, toCSV: toCSV, tUtc: tUtc, tTr: tTr };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.CSVU = api;
})(typeof window !== "undefined" ? window : globalThis);
