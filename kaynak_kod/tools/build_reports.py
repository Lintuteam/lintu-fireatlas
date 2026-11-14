"""Üç raporu şablondan üretir (U-21, C22, C24, C25).

Basitçe: Raporlar el ile yazılmaz. `reports/SABLON_*.md` dosyalarında sayı yerine
çift süslü parantezli yer tutucular durur; bu betik her yer tutucuyu
`reports/metrics.json` (tek sayı kaynağı, K1) içindeki değerle doldurur. Bir yer
tutucunun karşılığı yoksa üretim DURUR (çıkış kodu 1): yarım rapor yayımlanmaz.

Teknik olarak
  Yer tutucu biçimi:  {{anahtar}}  ya da  {{anahtar|değiştirici,değiştirici}}
    değiştiriciler:  e = etiket ekle (ölçüldü / tahmini / doğrulanmadı, K5)
                     b = birim ekle      t = birim + etiket
                     yuzde = oranı yüzdeye çevir (0,478 -> %47,8)
                     ay = ay numaralarını ad yap ([8,9,6] -> Ağu > Eyl > Haz)
  Noktalı anahtarlar (meta.*, kontrol.*, gereksinim.*, juri.*, sinirlar.*, ...) kod
  tarafında üretilen bloklardır (kontrol sonuçları, bulgular, tablolar). Bunlar da
  yalnız `audit/`, `reports/metrics.json`, `src/config/esikler.json` ve
  `reports/*.json` veri dosyalarından türetilir; sayı yazılmaz.
  Çıktı: reports/{calisma_prensibi,dogruluk_raporu,juri_sunum}.md ve .html
  (PDF için bu ortamda kütüphane yok: HTML, tarayıcıdan "PDF olarak yazdır" ile
  PDF'e çevrilir; baskı stili hazırdır).
Kullanım:  python tools/build_reports.py
Çıkış: 0 = üretildi; 1 = çözülmemiş yer tutucu / eksik kanıt / eksik kimlik.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
AUDIT = ROOT / "audit"
DOCS = ROOT / "docs"
OUTPUTS = ["calisma_prensibi", "dogruluk_raporu", "juri_sunum"]
LABELS = ("ölçüldü", "tahmini", "doğrulanmadı")
AYLAR = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
NO_UNIT = {"", "oran", "0/1", "ay no", "kimlik", "yıl", "TR günü", "il"}

M: dict = {}
SENS: dict = {}
ERRORS: list[str] = []
PH = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([^{}]+?)\s*)?\}\}")


# --------------------------------------------------------------------------- #
# Sayı biçimi (TR: binlik nokta, ondalık virgül)
# --------------------------------------------------------------------------- #
def _tr(r: float, nd: int) -> str:
    s = f"{abs(r):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    ip, _, fp = s.partition(".")
    ip = f"{int(ip):,}".replace(",", ".")
    out = ip + ("," + fp if fp else "")
    return ("−" + out) if r < 0 and float(s) != 0 else out


YORUM_TR = {
    "MODIS'e_ozgu_ek_dusus: sensor omru sonu/NRT/yorunge kaymasi suphesi":
        "MODIS'e özgü ek düşüş: sensör ömrü sonu, NRT veya yörünge kayması şüphesi",
    "iki_sensor_uyumlu": "iki sensör birbiriyle uyumlu",
}


def yorum_tr(x: str) -> str:
    """Ham kod metnini okunur Türkçeye çevirir (F5-02); bilinmeyen kodda alt çizgi boşluğa döner."""
    return YORUM_TR.get(x, x.replace("_", " "))


def fmt(v, mods=()):
    if v is None:
        return "yok"
    if isinstance(v, bool):
        return "evet" if v else "hayır"
    if isinstance(v, int):
        if "ay" in mods:
            return AYLAR[v]
        return str(v) if YEAR_KEY[0] else _tr(v, 0)
    if isinstance(v, float):
        if "yuzde" in mods:
            return "%" + _tr(v * 100, 1)
        a = abs(v)
        return _tr(v, 0 if a >= 1000 else 2 if a >= 10 else 4 if a >= 0.01 else 6)
    if isinstance(v, str) and "yorum" in mods:
        return yorum_tr(v)
    if isinstance(v, (list, tuple)):
        if "ay" in mods:
            return " > ".join(AYLAR[int(x)] for x in v)
        return "[" + " ; ".join(fmt(x) for x in v) + "]"
    return str(v)


def metric_text(key: str, mods: tuple, used: list | None, after: str = "") -> str:
    if key not in M:
        ERRORS.append(f"çözülmemiş yer tutucu: {key}")
        return f"[[ÇÖZÜLMEDİ:{key}]]"
    m = M[key]
    if used is not None:
        used.append(key)
    v = m["value"]
    unit = m.get("unit", "")
    YEAR_KEY[0] = unit == "yıl"
    s = fmt(v, mods)
    YEAR_KEY[0] = False
    dup = len(unit) >= 4 and after.lstrip().lower().startswith(unit[:4].lower())  # birim metinde zaten var
    if ("b" in mods or "t" in mods) and unit not in NO_UNIT and v is not None and "yuzde" not in mods and not dup:
        s += (" " + unit) if unit != "%" else " %"
    if "e" in mods or "t" in mods:
        s += f" ({m['etiket']})"
    return s


BLOCKS: dict = {}
YEAR_KEY = [False]  # yıl birimli tamsayılarda binlik ayracı yazılmaz


def cfg_value(path: str) -> str:
    """src/config/esikler.json içindeki eşik değerini (K9) yazar: {{cfg:D}}, {{cfg:kumeleme.L}}."""
    d = json.loads((ROOT / "src" / "config" / "esikler.json").read_text(encoding="utf-8"))
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            ERRORS.append(f"çözülmemiş yer tutucu: cfg:{path}")
            return f"[[ÇÖZÜLMEDİ:cfg:{path}]]"
        d = d[part]
    return fmt(d["value"] if isinstance(d, dict) and "value" in d else d)


def render(text: str, used: list | None = None) -> str:
    def sub(mo):
        key = mo.group(1).strip()
        mods = tuple(x.strip() for x in (mo.group(2) or "").split(",") if x.strip())
        if key.startswith("etiket:"):
            k = key[7:]
            if k not in M:
                ERRORS.append(f"çözülmemiş yer tutucu: {key}")
                return f"[[ÇÖZÜLMEDİ:{key}]]"
            if used is not None:
                used.append(k)
            return M[k]["etiket"]
        if key.startswith("cfg:"):
            return cfg_value(key[4:])
        if key in BLOCKS:
            out = BLOCKS[key]()
            return render(out, used) if "{{" in out else out
        return metric_text(key, mods, used, mo.string[mo.end():mo.end() + 12])
    return PH.sub(sub, text)


# --------------------------------------------------------------------------- #
# Girdi okuyucular
# --------------------------------------------------------------------------- #
def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def fix_mojibake(s: str) -> str:
    try:
        return s.encode("cp1252").decode("utf-8")
    except Exception:
        return s


def check_results() -> dict:
    return jload(AUDIT / "check_results.json")


def parse_bulgular() -> list[dict]:
    out = []
    for ln in (AUDIT / "bulgular.md").read_text(encoding="utf-8").splitlines():
        mo = re.match(r"^### (F\d-\d+) · (YÜKSEK|ORTA|DÜŞÜK) · (.*)$", ln)
        if not mo:
            continue
        rest = mo.group(3)
        dur = "kapandı" if "KAPANDI" in rest else "kısmen" if "KISMEN" in rest else "açık"
        title = re.sub(r"\s*—\s*\*\*.*$", "", rest).strip()
        out.append({"id": mo.group(1), "seviye": mo.group(2), "baslik": title, "durum": dur})
    return out


def acik(b, level):
    return [x for x in b if x["seviye"] == level and x["durum"] != "kapandı"]


def parse_juri_sorulari() -> tuple[list[dict], str]:
    rows, tail = [], ""
    for ln in (AUDIT / "juri_sorulari.md").read_text(encoding="utf-8").splitlines():
        if ln.startswith("| ") and re.match(r"^\|\s*\d+\s*\|", ln):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows.append({"n": int(cells[0]), "soru": cells[1], "durum": cells[-1]})
        elif ln.startswith("**Cevaplanamaz"):
            tail = ln
    return rows, tail


# --------------------------------------------------------------------------- #
# Bloklar
# --------------------------------------------------------------------------- #
def b_meta_veri():
    esik = jload(ROOT / "src" / "config" / "esikler.json")
    return render("FIRMS MODIS C6.1 + VIIRS 375 m, {{veri_yil_bas}}–{{veri_yil_bit}} (son gün {{veri_son_gun}}), "
                  "{{veri_toplam_nokta}} nokta, veri şeması " + str(esik.get("sema_surumu")) +
                  ", `reports/metrics.json` üretimi " + META["generated"])


def b_meta_tarih():
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())


def b_meta_denetim():
    b = parse_bulgular()
    cr = check_results()["summary"]
    y = acik(b, "YÜKSEK")
    s = (f"check_all: {cr.get('GEÇTİ', 0)} geçti, {cr.get('KALDI', 0)} kaldı, {cr.get('ATLANDI', 0)} atlandı; "
         f"denetçi bulguları: açık yüksek {len(y)}, açık orta {len(acik(b, 'ORTA'))}, açık düşük {len(acik(b, 'DÜŞÜK'))}")
    if y:
        s += (" — **DİKKAT: açık yüksek bulgu var (" + ", ".join(x["id"] for x in y) +
              "); denetçi kapısı kapanmadan bu rapor 'son hâl' sayılmamalıdır.**")
    else:
        s += " — denetçi kapısı açık yüksek bulgu içermiyor"
    return s


def b_kontrol(which):
    cr = check_results()
    sm = cr["summary"]
    tot = len(cr["results"])
    if which == "gecen":
        return str(sm.get("GEÇTİ", 0))
    if which == "kalan":
        return str(sm.get("KALDI", 0))
    if which == "atlanan":
        return str(sm.get("ATLANDI", 0))
    if which == "toplam":
        return str(tot)
    if which == "bagimsiz":
        return render("{{yh_girdi|t}} karşılaştırmanın {{yh_fark_sifir}} tanesinde bağımsız yeniden hesapla fark 0; "
                      "{{yh_aciklanmis_fark}} girdi açıklamalı bilgi kaydıdır (fark değil). C23 sonucu: " +
                      next(r["status"] for r in cr["results"] if r["code"] == "C23"))
    if which == "tablo":
        lines = ["| Kod | Kontrol | Durum | Not |", "|---|---|---|---|"]
        for r in cr["results"]:
            d = fix_mojibake(r.get("detail", "")).replace("|", "/")
            d = d if len(d) < 140 else d[:137] + "..."
            st = r["status"]
            if st == "ATLANDI" and r["code"] in ("C22", "C24", "C25") and d.startswith("henüz yok"):
                d = "bu raporların kendisi; üretimden sonra `check_all.py` yeniden çalışır"
            lines.append(f"| {r['code']} | {r['title']} | {st} | {d} |")
        return "\n".join(lines)
    raise KeyError(which)


def b_bagimsiz_tablo():
    y = jload(AUDIT / "yeniden_hesap.json")
    rows = [(k, v) for k, v in y.items() if isinstance(v, dict) and "fark" in v and "beklenen" in v]
    pick = [r for r in rows if not r[0].startswith("f2_")][:10] + [r for r in rows if r[0].startswith("f2_")][:10]
    out = ["Denetçi bu sayıları üretim kodundan bağımsız (openpyxl, polars, pandas) yeniden hesapladı "
           "(`audit/f1/`, `audit/f2/`). Aşağıda örnek satırlar; tamamı `audit/yeniden_hesap.json`. Etiket: ölçüldü.", "",
           "| Girdi | Beklenen (üretim hattı) | Bulunan (bağımsız) | Fark |", "|---|---|---|---|"]
    for k, v in pick:
        out.append(f"| {k} | {fmt(v['beklenen'])} | {fmt(v['bulunan'])} | {fmt(v['fark'])} |")
    return "\n".join(out)


def b_bulgu(which):
    b = parse_bulgular()
    if which == "acik_yuksek":
        return str(len(acik(b, "YÜKSEK")))
    if which == "acik_orta":
        return str(len(acik(b, "ORTA")))
    if which == "acik_dusuk":
        return str(len(acik(b, "DÜŞÜK")))
    if which == "kapanan":
        return str(len([x for x in b if x["durum"] == "kapandı"]))
    if which == "liste":
        out = ["| Kimlik | Seviye | Durum | Başlık |", "|---|---|---|---|"]
        for x in b:
            out.append(f"| {x['id']} | {x['seviye'].lower()} | {x['durum']} | {x['baslik'][:110].replace('|', '/')} |")
        return "\n".join(out)
    raise KeyError(which)


def _sinir_items():
    items = jload(REPORTS / "sinirlar.json")
    return items


def b_sinirlar(which):
    items = _sinir_items()
    cr = check_results()
    auto = []
    for r in cr["results"]:
        if r["status"] == "KALDI":
            auto.append(f"- **{r['code']} KALDI** ({r['title']}): {fix_mojibake(r.get('detail', ''))[:160]} (doğrulanmadı)")
        if r["status"] == "ATLANDI" and not (r["code"] in ("C22", "C24", "C25") and r.get("detail", "").startswith("henüz yok")):
            auto.append(f"- **{r['code']} ATLANDI** ({r['title']}): {fix_mojibake(r.get('detail', ''))[:160]} (doğrulanmadı)")
    for b in parse_bulgular():
        if b["durum"] != "kapandı":
            auto.append(f"- Açık denetim bulgusu **{b['id']}** ({b['seviye'].lower()}, {b['durum']}): {b['baslik'][:120]} (doğrulanmadı)")
    if which == "kisa":
        return "; ".join(x["baslik"] for x in items[:6]) + " (tam liste: Doğruluk Raporu §9)"
    if which == "liste":
        out = []
        for i, x in enumerate(items, 1):
            out.append(f"{i}. **{x['baslik']}** [{x['etiket']}]: " + render(x["metin"]))
        out.append("")
        out.append("Otomatik eklenenler (`audit/check_results.json` ve `audit/bulgular.md`; güzelleştirilemez):")
        out.extend(auto or ["- (yok)"])
        return "\n".join(out)
    if which == "dogrulanmayan":
        out = ["| # | Konu | Etiket | Açıklama | Kaynak |", "|---|---|---|---|---|"]
        for i, x in enumerate(items, 1):
            out.append(f"| {i} | {x['baslik']} | {x['etiket']} | {render(x['metin']).replace('|', '/')} | {x.get('kaynak', '')} |")
        out.append("")
        nd = [(k, v) for k, v in M.items() if v["etiket"] == "doğrulanmadı"]
        out.append(f"`metrics.json` içinde **doğrulanmadı** etiketli {len(nd)} metrik var:")
        out.append("")
        out.append("| Metrik kimliği | Değer | Tanım |")
        out.append("|---|---|---|")
        for k, v in nd:
            out.append(f"| {k} | {fmt(v['value'], ('yorum',))} | {v['tanim'][:110].replace('|', '/')} |")
        out.append("")
        out.append("Otomatik eklenenler:")
        out.extend(auto or ["- (yok)"])
        return "\n".join(out)
    raise KeyError(which)


def b_kod():
    rows = [("Veri hattı, şema, kapsam", "src/pipeline/build_points.py, build_coverage.py, timeutil.py", "docs/04_VERI_SOZLESMESI_TASLAK.md"),
            ("Eşikler ve güven kodlaması (K9, K10)", "src/config/esikler.json, src/config/config.py", "—"),
            ("Temizlik (sanayi, anız, NASA etiketi)", "src/cleaning/kalibrasyon.py, build_status.py, olay_aniz.py, worldcover.py", "docs/temizlik_yontemi.md"),
            ("Kümeleme (olay)", "src/clustering/core.py, build_events.py, bruteforce_check.py", "docs/kumeleme_yontemi.md"),
            ("Harmonizasyon", "src/harmonize/eslestirme.py, guven_esleme.py, seri.py, olay.py", "docs/harmonizasyon_yontemi.md"),
            ("Takvim ve anomali", "src/analytics/build_monthly.py, analiz.py, query.py", "docs/takvim_yontemi.md"),
            ("Arayüz", "src/app/index.html, main.js, core.js, mapview.js, lab.js, charts.js, csv.js", "referans/STIL_NOTU.md"),
            ("Metrik ve rapor üretimi", "tools/build_metrics.py, build_rapor_metrikleri.py, build_reports.py", "reports/metrics.json"),
            ("Kontroller", "tools/check_all.py, audit/f1/, audit/f2/", "docs/03_KABUL_KRITERLERI.md")]
    out = ["| Konu | Kod | Belge |", "|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def b_esik():
    e = jload(ROOT / "src" / "config" / "esikler.json")
    out = ["| Eşik | Değer | Birim | Gerekçe (`src/config/esikler.json`) |", "|---|---|---|---|"]

    def walk(d, p=""):
        for k, v in d.items():
            if isinstance(v, dict) and "value" in v:
                g = str(v.get("gerekce", "")).replace("|", "/")
                out.append(f"| {p}{k} | {fmt(v['value'])} | {v.get('unit', '')} | {g[:230]}{'…' if len(g) > 230 else ''} |")
            elif isinstance(v, dict) and not k.startswith("_") and k in ("temizlik", "harmonizasyon", "kumeleme", "takvim"):
                walk(v, k + ".")
    walk(e)
    return "\n".join(out)


def b_duyarlilik(grup):
    sets = {"kumeleme": ["D", "H", "L"], "temizlik": ["N", "M", "Y", "S", "F", "koruma_G", "kalici_gece", "aniz_olay_max_tespit"]}[grup]
    out = []
    for p in sets:
        rows = SENS.get(p)
        if not rows:
            ERRORS.append(f"duyarlılık tablosu yok: {p}")
            continue
        cols = [c for c, v in rows[0].items() if not isinstance(v, (dict, list)) and c != "kural"]
        out.append(f"**{p}** (en az {len(rows)} değer; ölçüldü, `ref_*` sütunları tahmini)")
        out.append("")
        out.append("| " + " | ".join(cols) + " |")
        out.append("|" + "---|" * len(cols))
        for r in rows:
            out.append("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |")
        out.append("")
    return "\n".join(out)


def b_huni():
    st = [("temiz (yangın olarak sayılır)", "temizlik_status_temiz"), ("anız (olay düzeyinde etiket)", "temizlik_status_aniz"),
          ("NASA statik kaynak (type=2)", "temizlik_status_statik_nasa"), ("deniz (type=3)", "temizlik_status_deniz"),
          ("volkan (type=1)", "temizlik_status_volkan"), ("sanayi (bizim kural)", "temizlik_status_sanayi"),
          ("kalıcı ısı kaynağı, belirsiz", "temizlik_status_kalici_belirsiz")]
    out = ["| Etiket | Nokta | Etiket durumu |", "|---|---|---|",
           f"| **Ham toplam** | {fmt(M['veri_toplam_nokta']['value'])} | {M['veri_toplam_nokta']['etiket']} |"]
    for ad, k in st:
        out.append(f"| {ad} | {fmt(M[k]['value'])} | {M[k]['etiket']} |")
    return "\n".join(out)


def b_gereksinim(which):
    ids = []
    for ln in (DOCS / "01_ISTEKLER.md").read_text(encoding="utf-8").splitlines():
        mo = re.match(r"^\|\s*(N-\d{2})\s*\|\s*(.*?)\s*\|", ln) or re.match(r"^- \*\*(U-\d{2})\*\*\s*(.*)$", ln)
        if mo:
            ids.append((mo.group(1), mo.group(2)))
    eşl = jload(REPORTS / "gereksinim_eslemesi.json")
    rows, sayac, eksik = [], {"yapıldı": 0, "kısmen": 0, "yapılmadı": 0}, []
    yuksek = bool(acik(parse_bulgular(), "YÜKSEK"))
    for kid, metin in ids:
        e = eşl.get(kid)
        if e is None:
            ERRORS.append(f"gereksinim eşlemesi yok: {kid}")
            continue
        durum = e["durum"]
        yok = [p for p in e["kanit"] if not (ROOT / p).exists()]
        if yok:
            ERRORS.append(f"{kid}: kanıt yolu yok: {yok}")
        if yuksek and e.get("yuksek_bulgu_etkisi") and durum == "yapıldı":
            durum = "kısmen"
        sayac[durum] += 1
        if durum != "yapıldı":
            eksik.append(kid)
        kis = re.sub(r"\*\*|`", "", metin)
        kis = kis if len(kis) <= 110 else kis[:107] + "..."
        rows.append((kid, kis, durum, ", ".join(f"`{p}`" for p in e["kanit"]), render(e["not"]).replace("|", "/")))
    if which == "tablo":
        out = ["| Kimlik | İstek | Durum | Kanıt yolu | Not (etiketli) |", "|---|---|---|---|---|"]
        for r in rows:
            out.append("| " + " | ".join(r) + " |")
        return "\n".join(out)
    if which == "durum":
        tot = sum(sayac.values())
        out = [f"Toplam {tot} istek: **yapıldı {sayac['yapıldı']}**, **kısmen {sayac['kısmen']}**, **yapılmadı {sayac['yapılmadı']}**. "
               "Durum değerlendirmesi kanıt dosyasının varlığına ve açık denetim bulgularına bağlanmıştır (kanıt yolu yoksa üretim durur).", "",
               "| Durum | Kimlikler |", "|---|---|"]
        for d in ("yapıldı", "kısmen", "yapılmadı"):
            out.append(f"| {d} | {', '.join(r[0] for r in rows if r[2] == d) or '—'} |")
        out.append("")
        out.append("Yapılmayan veya kısmen kalanların nedeni:")
        for r in rows:
            if r[2] != "yapıldı":
                out.append(f"- **{r[0]}** ({r[2]}): {r[4]}")
        return "\n".join(out)
    raise KeyError(which)


def b_soru_cevap(which):
    rows, tail = parse_juri_sorulari()
    tmpl = (REPORTS / "SABLON_juri_soru_cevap.md").read_text(encoding="utf-8")
    parts = re.split(r"^## S(\d+)\s*$", tmpl, flags=re.M)
    ans = {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    out, eksik = [], []
    for r in rows:
        if r["n"] not in ans:
            ERRORS.append(f"jüri sorusu {r['n']} için şablonda cevap yok")
            continue
        used: list = []
        body = render(ans[r["n"]], used)
        keys = ", ".join(dict.fromkeys(used)) or "—"
        out.append(f"### Soru {r['n']}. {r['soru']}\n\n{body}\n\n*Denetçi durumu:* {r['durum']}. *metrics.json kimlikleri:* {keys}\n")
        if re.search(r"eksik|cevaplanamaz", r["durum"], re.I):
            eksik.append(f"- Soru {r['n']}: {r['soru']} — **{r['durum']}**")
    if which == "soru_cevap":
        return "\n".join(out)
    if which == "cevaplanamayan":
        return "\n".join(eksik + ["", tail.replace("**Cevaplanamaz/eksik kalanlar:**", "Denetçinin eksik listesi:")])
    raise KeyError(which)


def b_slayt():
    sl = jload(REPORTS / "slaytlar.json")
    out = ["| # | Slayt | Ana mesaj | Kullanılan sayılar (metrics.json kimliği = değer, etiket) |", "|---|---|---|---|"]
    for i, s in enumerate(sl, 1):
        refs = []
        for k in s["metrikler"]:
            if k not in M:
                ERRORS.append(f"slayt {i}: metrik yok {k}")
                continue
            mods = ("ay",) if k.startswith("takvim_top3") else ()
            refs.append(f"`{k}` = {fmt(M[k]['value'], mods)} ({M[k]['etiket']})")
        out.append(f"| {i} | {s['baslik']} | {render(s['mesaj']).replace('|', '/')} | {'; '.join(refs)} |")
    return "\n".join(out)


def b_demo():
    sc = jload(REPORTS / "demo_senaryolari.json")
    out = []
    for s in sc:
        out.append(f"### {s['baslik']}")
        out.append("")
        out.append(render(s["secim"]))
        out.append("")
        out.append("Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):")
        for j, a in enumerate(s["adimlar"], 1):
            out.append(f"{j}. {render(a)}")
        out.append("")
        out.append("Beklenen: " + render(s["beklenen"]))
        out.append("")
    return "\n".join(out)


BLOCKS.update({
    "meta.veri_surumu": b_meta_veri, "meta.uretim_tarihi": b_meta_tarih, "meta.denetim_durumu": b_meta_denetim,
    "kontrol.gecen": lambda: b_kontrol("gecen"), "kontrol.toplam": lambda: b_kontrol("toplam"),
    "kontrol.kalan": lambda: b_kontrol("kalan"), "kontrol.atlanan": lambda: b_kontrol("atlanan"),
    "kontrol.bagimsiz_sonuc": lambda: b_kontrol("bagimsiz"), "kontrol.tablo": lambda: b_kontrol("tablo"),
    "denetim.bagimsiz_tablo": b_bagimsiz_tablo,
    "bulgu.acik_yuksek": lambda: b_bulgu("acik_yuksek"), "bulgu.acik_orta": lambda: b_bulgu("acik_orta"),
    "bulgu.acik_dusuk": lambda: b_bulgu("acik_dusuk"), "bulgu.kapanan": lambda: b_bulgu("kapanan"),
    "bulgu.liste": lambda: b_bulgu("liste"),
    "sinirlar.kisa": lambda: b_sinirlar("kisa"), "sinirlar.liste": lambda: b_sinirlar("liste"),
    "sinirlar.dogrulanmayan": lambda: b_sinirlar("dogrulanmayan"),
    "kod.harita": b_kod, "esik.tablosu": b_esik,
    "duyarlilik.kumeleme": lambda: b_duyarlilik("kumeleme"), "duyarlilik.temizlik": lambda: b_duyarlilik("temizlik"),
    "huni.tablo": b_huni,
    "gereksinim.tablo": lambda: b_gereksinim("tablo"), "gereksinim.durum_tablosu": lambda: b_gereksinim("durum"),
    "juri.soru_cevap": lambda: b_soru_cevap("soru_cevap"), "juri.cevaplanamayan": lambda: b_soru_cevap("cevaplanamayan"),
    "juri.slayt_iskeleti": b_slayt, "juri.demo_senaryolari": b_demo,
})


# --------------------------------------------------------------------------- #
# Markdown -> HTML (küçük, bağımlılıksız)
# --------------------------------------------------------------------------- #
CSS = """:root{--bg:#070b10;--card:#0d141b;--line:#1b2630;--tx:#e6edf3;--dim:#7b8794;--ac:#5eead4}
body{background:var(--bg);color:var(--tx);font:15px/1.6 Inter,system-ui,sans-serif;margin:0}
main{max-width:980px;margin:0 auto;padding:24px 16px}
h1,h2,h3{font-weight:500}h2{border-top:1px solid var(--line);padding-top:18px;margin-top:28px}
h1{font-size:1.7em}code{font:12.5px ui-monospace,monospace;background:var(--card);padding:1px 5px;border-radius:4px;color:var(--ac)}
table{border-collapse:collapse;width:100%;margin:12px 0;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top;font-size:13.5px}
th{background:var(--card);color:var(--dim);font:600 11.5px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.05em}
blockquote{border-left:3px solid var(--ac);margin:12px 0;padding:2px 14px;color:var(--dim);background:var(--card)}
strong{color:#fff}
@media print{:root{--bg:#fff;--card:#f3f5f7;--line:#c9d1d9;--tx:#111;--dim:#444;--ac:#0b6b5f}strong{color:#000}}
"""


UL_RX = re.compile(r"^\s*[-*] ")
OL_RX = re.compile(r"^\d+\. ")


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def md_to_html(md: str, title: str) -> str:
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1]):
            hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in hdr) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue
        mo = re.match(r"^(#{1,4}) (.*)$", ln)
        if mo:
            n = len(mo.group(1))
            out.append(f"<h{n}>{inline(mo.group(2))}</h{n}>")
        elif re.match(r"^\s*[-*] ", ln):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                out.append("<li>" + inline(UL_RX.sub("", lines[i])) + "</li>")
                i += 1
            out.append("</ul>")
            continue
        elif re.match(r"^\d+\. ", ln):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                out.append("<li>" + inline(OL_RX.sub("", lines[i])) + "</li>")
                i += 1
            out.append("</ol>")
            continue
        elif ln.startswith(">"):
            blk = []
            while i < len(lines) and lines[i].startswith(">"):
                blk.append(lines[i].lstrip("> "))
                i += 1
            out.append("<blockquote>" + inline(" ".join(blk)) + "</blockquote>")
            continue
        elif ln.strip():
            para = [ln]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|\||>|\s*[-*] |\d+\. )", lines[i + 1]):
                i += 1
                para.append(lines[i])
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        i += 1
    return (f"<!doctype html><html lang=\"tr\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>" + "\n".join(out) + "</main></body></html>")


# --------------------------------------------------------------------------- #
META: dict = {}


def main() -> int:
    global M, SENS
    mj = jload(REPORTS / "metrics.json")
    M, SENS = mj["metrics"], mj.get("sensitivity", {})
    META["generated"] = mj.get("generated_utc", "?")
    ok_out = {}
    for name in OUTPUTS:
        tpl = (REPORTS / f"SABLON_{name}.md").read_text(encoding="utf-8")
        ok_out[name] = render(tpl)
    left = [m for t in ok_out.values() for m in re.findall(r"\{\{.*?\}\}", t)]
    if left:
        ERRORS.append(f"çıktıda kalan yer tutucu: {left[:5]}")
    if ERRORS:
        print("RAPOR ÜRETİLMEDİ (C22):")
        for e in dict.fromkeys(ERRORS):
            print(" -", e)
        return 1
    # etiket sayacı (C24 ön kontrol)
    for name, text in ok_out.items():
        (REPORTS / f"{name}.md").write_text(text, encoding="utf-8")
        (REPORTS / f"{name}.html").write_text(md_to_html(text, name), encoding="utf-8")
        n = {lab: text.count(lab) for lab in LABELS}
        print(f"{name}.md/.html  {len(text):,} karakter  etiket: {n}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
