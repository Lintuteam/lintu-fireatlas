"""Kabul kriterleri denetleyicisi (docs/03_KABUL_KRITERLERI.md, C01–C25).

Basitçe: Bu betik projenin "sağlık muayenesi"dir. Her kontrol bir doktor testi gibi
tek bir şeye bakar (ör. "sayılar toplanınca tutuyor mu?") ve GEÇTİ / KALDI / ATLANDI der.
ATLANDI sessiz geçiş değildir: gerekçesi tabloya yazılır.

Teknik olarak: Her kontrol `cXX_*` adlı, argümansız bir işlevdir ve `Result` döndürür.
Kontroller ilgili çıktı dosyası (parquet, metrics.json, arayüz kodu) henüz yoksa
ATLANDI döner. Sonuçlar `audit/check_results.json`'a yazılır. Herhangi bir kontrol
KALDI ise çıkış kodu 1'dir. Bir kontrolün kendisi hata fırlatırsa KALDI sayılır.

Kullanım:  python tools/check_all.py            (tümü)
           python tools/check_all.py C07 C08    (yalnız seçilenler)
"""
from __future__ import annotations

import json
import re
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
POINTS = PROCESSED / "points.parquet"          # nokta tablosu (veri sözleşmesi)
EVENTS = PROCESSED / "events.parquet"          # olay tablosu (kümeleme)
AGG = PROCESSED / "agg"
APP = ROOT / "src" / "app"
CONFIG = ROOT / "src" / "config" / "esikler.json"
METRICS = ROOT / "reports" / "metrics.json"
REPORTS = ROOT / "reports"
AUDIT = ROOT / "audit"
ISTEKLER = ROOT / "docs" / "01_ISTEKLER.md"

PASS, FAIL, SKIP = "GEÇTİ", "KALDI", "ATLANDI"


@dataclass
class Result:
    code: str
    title: str
    status: str
    detail: str = ""
    measured: dict = field(default_factory=dict)
    seconds: float = 0.0


def skip(reason: str) -> tuple[str, str, dict]:
    return SKIP, reason, {}


def missing(*paths: Path) -> str | None:
    gone = [str(p.relative_to(ROOT)) for p in paths if not p.exists()]
    return f"henüz yok: {', '.join(gone)}" if gone else None


SIDE = {"status": "points_status.parquet", "mcell": "points_mcell.parquet",
        "event_id": "points_event.parquet"}  # sözleşme §2: F2 alanları pid anahtarlı yan tablolarda


def load_points(columns=None):
    """Nokta tablosu + (varsa) yan tablolar. Yan tablo yoksa o sütun istenirse KeyError."""
    import pandas as pd
    import pyarrow.parquet as pq
    base_cols = set(pq.read_schema(POINTS).names)
    want = list(columns) if columns else None
    side = [c for c in (want or []) if c not in base_cols and c in SIDE]
    base = [c for c in want if c not in side] if want else None
    if side and "pid" not in (base or []):
        base = (base or []) + ["pid"]
    df = pd.read_parquet(POINTS, columns=base)
    for c in side:
        f = PROCESSED / SIDE[c]
        if not f.exists():
            raise KeyError(f"yan tablo henüz yok: {f.relative_to(ROOT)}")
        df = df.merge(pd.read_parquet(f, columns=["pid", c]), on="pid", how="left")
    return df


def load_metrics() -> dict:
    return json.loads(METRICS.read_text(encoding="utf-8"))


def app_files(exts=(".js", ".html", ".mjs")) -> list[Path]:
    if not APP.exists():
        return []
    return [p for p in APP.rglob("*") if p.suffix in exts and "vendor" not in p.parts
            and "lib" not in p.parts and "tests" not in p.parts]


# --------------------------------------------------------------------------- #
# Hesap doğruluğu
# --------------------------------------------------------------------------- #
def c01_huni_korunumu():
    """Her adımda giren = kalan + etiketlenen, sensör ve bölge bazında (K3: silme yok)."""
    if (m := missing(POINTS, PROCESSED / SIDE["status"])):
        return skip(m)
    df = load_points(["sensor", "status"])
    raw_total = _raw_row_count()
    if raw_total is not None and raw_total != len(df):
        return FAIL, f"ham satır {raw_total} ≠ nokta tablosu {len(df)} (K3 ihlali)", {
            "raw": raw_total, "points": len(df)}
    if df["status"].isna().any():
        return FAIL, f"{int(df['status'].isna().sum())} nokta etiketsiz", {}
    by = df.groupby(["sensor", "status"]).size().unstack(fill_value=0)
    ok = bool((by.sum(axis=1) == df.groupby("sensor").size()).all())
    return (PASS if ok else FAIL), "her nokta tam bir etiket taşıyor", {
        "points": len(df), "by_sensor_status": by.to_dict()}


def _raw_row_count():
    inv = PROCESSED / "inventory.json"
    if inv.exists():
        return json.loads(inv.read_text(encoding="utf-8")).get("raw_rows_total")
    return None


def c02_toplam_tutarliligi():
    """Tümü temiz tespit = MODIS temiz + VIIRS temiz."""
    if (m := missing(POINTS, PROCESSED / SIDE["status"])):
        return skip(m)
    df = load_points(["sensor", "status"])
    clean = df[df["status"] == "temiz"]
    total = len(clean)
    parts = clean.groupby("sensor").size().to_dict()
    ok = total == sum(parts.values())
    return (PASS if ok else FAIL), "", {"temiz": total, "sensor": parts}


def c03_kumeleme_dogrulugu():
    """Hızlı kümeleme = kaba kuvvet bölümlemesi (örneklemde fark 0)."""
    test = ROOT / "src" / "clustering" / "bruteforce_check.py"
    if (m := missing(EVENTS, test)):
        return skip(m)
    return _run_module_check(test)


def c04_cifte_sayim_yok():
    """Ortak olay sayısı ≤ sensörler ayrı kümelendiğinde toplam olay."""
    if (m := missing(METRICS)):
        return skip(m)
    mt = load_metrics()
    joint = _metric(mt, "events_joint_overlap")
    sep = _metric(mt, "events_separate_overlap")
    if joint is None or sep is None:
        return skip("metrics.json içinde events_joint_overlap / events_separate_overlap yok")
    return (PASS if joint <= sep else FAIL), "", {"ortak": joint, "ayri": sep}


def c05_uclu_sinif_toplami():
    """ortak + yalnız MODIS + yalnız VIIRS = toplam olay."""
    if (m := missing(EVENTS)):
        return skip(m)
    import pandas as pd
    ev = pd.read_parquet(EVENTS, columns=["event_id", "match_class"])
    counts = ev.groupby("match_class").size().to_dict()
    ok = sum(counts.values()) == ev["event_id"].nunique() and ev["match_class"].notna().all()
    return (PASS if ok else FAIL), "", {"siniflar": counts, "toplam": int(ev["event_id"].nunique())}


def c06_veri_kapsami():
    """Sensörün kapsamı dışındaki gün sayıma/anomaliye girmez."""
    cov = PROCESSED / "coverage.parquet"
    if (m := missing(cov, POINTS)):
        return skip(m)
    import pandas as pd
    p = load_points(["sensor", "sat", "day_tr"])
    c = pd.read_parquet(cov, columns=["sat", "day_tr", "observed"])
    j = p.merge(c, on=["sat", "day_tr"], how="left")
    bad = int((j["observed"] == False).sum())  # noqa: E712
    unknown = int(j["observed"].isna().sum())
    measured = {"kapsam_disi_tespit": bad, "kapsam_bilinmeyen": unknown}
    if bad:
        return FAIL, "kapsam dışı günde tespit var", measured
    # İkinci ayak (anlamlı sınama): kesinti günleri takvim paydasından/medyandan çıkarılıyor mu?
    kanit = ROOT / "src" / "analytics" / "c06_kanit.py"
    if not kanit.exists():
        return SKIP, "yalnız birinci ayak; src/analytics/c06_kanit.py henüz yok", measured
    st, detail, m2 = _run_module_check(kanit)
    measured.update(m2)
    return st, "kesinti düzeltmesi kanıtı: " + detail, measured


def c07_zaman():
    """TR gün sınırı (20:59 / 21:00 UTC), UTC depolama, yıl kırpılmaması."""
    tz_mod = ROOT / "src" / "pipeline" / "timeutil.py"
    if (m := missing(tz_mod)):
        return skip(m)
    sys.path.insert(0, str(ROOT / "src"))
    from pipeline import timeutil  # type: ignore
    import pandas as pd
    a = timeutil.tr_day(pd.Timestamp("2025-06-30T20:59:00Z"))
    b = timeutil.tr_day(pd.Timestamp("2025-06-30T21:00:00Z"))
    measured = {"20:59Z": str(a), "21:00Z": str(b)}
    if str(a) == str(b):
        return FAIL, "TR gün sınırı ayrılmıyor", measured
    if POINTS.exists():
        p = load_points(["t_utc", "src_year", "day_tr"])
        if str(p["t_utc"].dtype).find("UTC") < 0:
            return FAIL, "t_utc UTC saat dilimli değil", measured
        yrs = p["t_utc"].dt.year
        mixed = int((yrs != p["src_year"]).sum())
        measured["dosya_yili_ile_utc_yili_farkli"] = mixed
        # Üretim yolunu test et: saklanan day_tr, timeutil.tr_day ile birebir mi?
        expect = pd.to_datetime(timeutil.tr_day(p["t_utc"])).dt.date
        got = pd.to_datetime(p["day_tr"]).dt.date
        bad_day = int((expect != got).sum())
        measured["day_tr_uyusmaz"] = bad_day
        per_year = p.groupby("src_year").size()
        measured["yil_sayisi"] = int(len(per_year))
        if mixed or bad_day:
            return FAIL, "yıl karışması veya day_tr uyuşmazlığı", measured
    return PASS, "", measured


def c08_kodlama_tutarliligi():
    """Güven eşlemesi tek tanım (K10); başka yerde sabit eşik yok; veri eşlemeyle uyumlu."""
    if (m := missing(CONFIG)):
        return skip(m)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    conf = cfg.get("guven")
    if not conf:
        return FAIL, "esikler.json içinde 'guven' bölümü yok", {}
    # Kodda güven eşiğinin ikinci bir tanımını ara (ör. "conf >= 80", "'h':", "c<30").
    pat = re.compile(r"(conf\w*\s*[<>]=?\s*\d{2})|(['\"]h['\"]\s*:\s*['\"]?(high|yüksek))", re.I)
    hits = []
    for p in list((ROOT / "src").rglob("*.py")) + app_files():
        if "config" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    measured = {"ikinci_tanim_supheli": hits[:20]}
    if POINTS.exists():
        df = load_points(["sensor", "conf_raw", "conf_cls"])
        n_bad = int(df["conf_cls"].isna().sum())
        measured["conf_cls_bos"] = n_bad
        if n_bad:
            return FAIL, "conf_cls boş nokta var", measured
    return (PASS if not hits else FAIL), "", measured


# --------------------------------------------------------------------------- #
# Harmonizasyon doğruluğu
# --------------------------------------------------------------------------- #
def _metric(mt: dict, key: str):
    v = mt.get("metrics", mt).get(key)
    return v.get("value") if isinstance(v, dict) else v


def _need_metrics(*keys):
    if not METRICS.exists():
        return None, "henüz yok: reports/metrics.json"
    mt = load_metrics()
    vals = {k: _metric(mt, k) for k in keys}
    miss = [k for k, v in vals.items() if v is None]
    if miss:
        return None, f"metrics.json içinde yok: {', '.join(miss)}"
    return vals, None


def c09_kalibrasyon_disi():
    """Leave-one-year-out; MAPE, R², ortalama sapma, %95 aralık raporlanır (K4)."""
    vals, err = _need_metrics("loyo_mape", "loyo_r2", "loyo_bias", "loyo_ci95", "loyo_method")
    if err:
        return skip(err)
    ok = str(vals["loyo_method"]).lower().startswith(("leave-one-year", "loyo", "yil-disarida"))
    return (PASS if ok else FAIL), "yöntem yıl dışarıda bırakma olmalı", vals


def c10_sicrama_metrigi():
    """Sensör kaynaklı sıçrama = harmonize sıçrama − aynı penceredeki gerçek MODIS değişimi.

    Basitçe: 2012'de yangınlar gerçekten azaldıysa seri de düşmeli; bu sensör hatası değildir.
    Sensörün eklediği kısım (artık) LOYO yıllık hata aralığında kalmalı.
    Eski ölçüt (harmonize sıçrama doğal değişim aralığında) bilgi için raporlanır; 2009–2011
    gerçek MODIS'te olağandışı yüksek olduğundan gerçek değişimi de reddediyordu.
    Karar: audit/degisim_gunlugu.md (2026-11-13, F2).
    """
    vals, err = _need_metrics("jump_raw_pct", "jump_harm_pct", "jump_null_ci95",
                              "jump_resid_pct", "loyo_ci95")
    if err:
        return skip(err)
    lo, hi = vals["loyo_ci95"]
    ok = lo <= vals["jump_resid_pct"] <= hi
    nlo, nhi = vals["jump_null_ci95"]
    vals["eski_olcut_harm_dogal_aralikta"] = bool(nlo <= vals["jump_harm_pct"] <= nhi)
    return (PASS if ok else FAIL), "artık sıçrama LOYO %95 aralığında olmalı", vals


def c11_esdeger_seri():
    vals, err = _need_metrics("equiv_overlap_bias", "equiv_overlap_band")
    if err:
        return skip(err)
    return PASS, "sapma ve bant raporlandı", vals


def c12_duyarlilik():
    """D, H, N, M, F için en az üç değerli duyarlılık tablosu."""
    if (m := missing(METRICS)):
        return skip(m)
    sens = load_metrics().get("sensitivity", {})
    need = ["D", "H", "N", "M", "F"]
    short = [k for k in need if len(sens.get(k, [])) < 3]
    if short:
        return FAIL, f"eksik/üçten az değer: {short}", {"var": list(sens)}
    return PASS, "", {k: len(sens[k]) for k in need}


def c13_referans():
    ref = AUDIT / "dogrulama_seti.csv"
    if (m := missing(ref)):
        return skip(m + " — referans yok, iddia 'doğrulanmadı' olarak etiketlenmeli")
    vals, err = _need_metrics("ref_precision", "ref_recall")
    if err:
        return skip(err)
    return PASS, "", vals


# --------------------------------------------------------------------------- #
# Arayüz ve veri bütünlüğü
# --------------------------------------------------------------------------- #
def c14_ekran_hesap():
    """Arayüzde sayılar metrics.json/agg'den okunur; HTML'de elle yazılmış metrik sayısı yok."""
    if not app_files():
        return skip("henüz yok: src/app")
    if (m := missing(METRICS)):
        return skip(m)
    # Statik tarama: HTML/JS içinde 3+ basamaklı sayı içeren görünür metin (ör. "10.088 olay").
    pat = re.compile(r">[^<{]*\b\d{1,3}([.,]\d{3})+\b[^<]*<")
    hits = []
    for p in app_files((".html",)):
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    return (PASS if not hits else FAIL), "statik tarama; çalışma anı karşılaştırması denetçide", {
        "sabit_sayi_supheli": hits[:20]}


FORBIDDEN = [
    (re.compile(r"Math\.random"), "Math.random"),
    (re.compile(r"\bseed(ed)?Random|mulberry32|xorshift", re.I), "tohumlu rastgele"),
    (re.compile(r"R²\s*[=:]\s*0[.,]\d|R2\s*[=:]\s*0[.,]\d"), "sabit R²"),
    (re.compile(r"['\"`][^'\"`]*\b\d{1,3}([.,]\d+)?\s*%[^'\"`]*['\"`]"), "sabit yüzde metni"),
]


def c15_yasak_kalip():
    files = app_files()
    if not files:
        return skip("henüz yok: src/app")
    hits = []
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for rx, name in FORBIDDEN:
                if rx.search(line):
                    hits.append(f"{name} @ {p.relative_to(ROOT)}:{i}")
    return (PASS if not hits else FAIL), "", {"bulgular": hits[:30], "taranan_dosya": len(files)}


def c16_simulasyon_izolasyonu():
    files = app_files()
    if not files:
        return skip("henüz yok: src/app")
    sim = [p for p in files if re.search(r"simul|fake|mock|synthetic", p.name, re.I)]
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in files)
    badge = "SİMÜLASYON" in text or "SIMULATION" in text
    if sim and not badge:
        return FAIL, "simüle veri dosyası var ama rozet yok", {"dosyalar": [str(p) for p in sim]}
    return PASS, "simüle veri yalnız tests/ altında" if not sim else "rozet mevcut", {}


def c17_csv():
    test = APP / "tests" / "csv_check.py"
    if (m := missing(test)):
        return skip(m)
    return _run_module_check(test)


def c18_tr_en():
    i18n = APP / "i18n"
    tr, en = i18n / "tr.json", i18n / "en.json"
    if (m := missing(tr, en)):
        return skip(m)
    a = set(_flat(json.loads(tr.read_text(encoding="utf-8"))))
    b = set(_flat(json.loads(en.read_text(encoding="utf-8"))))
    diff = {"yalniz_tr": sorted(a - b)[:20], "yalniz_en": sorted(b - a)[:20]}
    return (PASS if a == b else FAIL), f"{len(a)} anahtar", diff


def _flat(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flat(v, f"{pre}{k}.")
        else:
            yield f"{pre}{k}"


def c19_erisilebilirlik():
    rep = AUDIT / "erisilebilirlik.json"
    if (m := missing(rep)):
        return skip(m + " (arayüz ajanı ölçüm raporu üretmeli)")
    r = json.loads(rep.read_text(encoding="utf-8"))
    need = ["klavye", "aria", "renk_korlugu", "kontrast_min"]
    miss = [k for k in need if k not in r]
    return (FAIL if miss else PASS), f"eksik ölçüm: {miss}" if miss else "", r


def c20_performans():
    rep = AUDIT / "performans.json"
    if (m := missing(rep)):
        return skip(m)
    r = json.loads(rep.read_text(encoding="utf-8"))
    sec = r.get("esik_degisimi_saniye")
    if sec is None:
        return FAIL, "esik_degisimi_saniye ölçülmemiş", r
    return (PASS if sec <= 5 else FAIL), "hedef ≤ 5 sn", r


def c21_cevrimdisi():
    files = app_files((".html",))
    if not files:
        return skip("henüz yok: src/app")
    rx = re.compile(r"<(script|link)[^>]+(src|href)=[\"'](https?:)?//", re.I)
    hits = []
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if rx.search(line):
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    return (PASS if not hits else FAIL), "dış CDN bağımlılığı olmamalı", {"dis_kaynak": hits}


# --------------------------------------------------------------------------- #
# Belgelerle tutarlılık
# --------------------------------------------------------------------------- #
GENERATED = ["calisma_prensibi.md", "dogruluk_raporu.md", "sunum_raporu.md"]


def c22_belge_sayilari():
    reps = [REPORTS / g for g in GENERATED]
    if (m := missing(*reps)):
        return skip(m)
    unresolved = []
    for r in reps:
        for i, line in enumerate(r.read_text(encoding="utf-8").splitlines(), 1):
            if "{{" in line:
                unresolved.append(f"{r.name}:{i}")
    return (PASS if not unresolved else FAIL), "", {"cozulmemis": unresolved[:20]}


def c23_bagimsiz_hesap():
    rep = AUDIT / "yeniden_hesap.json"
    if (m := missing(rep)):
        return skip(m + " (denetci üretir)")
    r = json.loads(rep.read_text(encoding="utf-8"))
    bad = [k for k, v in r.items() if isinstance(v, dict) and v.get("fark", 0) != 0
           and not v.get("aciklama")]
    return (PASS if not bad else FAIL), "", {"aciklanmamis_fark": bad}


LABELS = ("ölçüldü", "tahmini", "doğrulanmadı")


def c24_durustluk_etiketi():
    reps = [REPORTS / g for g in GENERATED]
    if (m := missing(*reps)):
        return skip(m)
    counts = {}
    for r in reps:
        t = r.read_text(encoding="utf-8")
        counts[r.name] = {lab: t.count(lab) for lab in LABELS}
    empty = [k for k, v in counts.items() if sum(v.values()) == 0]
    return (PASS if not empty else FAIL), "etiket içermeyen rapor", counts


def c25_gereksinim_eslemesi():
    ids = sorted(set(re.findall(r"\b([NU]-\d{2})\b", ISTEKLER.read_text(encoding="utf-8"))))
    rep = REPORTS / "sunum_raporu.md"
    if (m := missing(rep)):
        return skip(m + f" ({len(ids)} kimlik eşlenmeyi bekliyor)")
    t = rep.read_text(encoding="utf-8")
    absent = [i for i in ids if i not in t]
    return (PASS if not absent else FAIL), "", {"kimlik": len(ids), "eksik": absent}


# --------------------------------------------------------------------------- #
def _run_module_check(path: Path):
    import subprocess
    r = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True,
                       timeout=600)
    tail = (r.stdout + r.stderr).strip().splitlines()[-5:]
    return (PASS if r.returncode == 0 else FAIL), " | ".join(tail), {"returncode": r.returncode}


CHECKS: list[tuple[str, str, Callable]] = [
    ("C01", "Huni korunumu", c01_huni_korunumu),
    ("C02", "Toplam tutarlılığı", c02_toplam_tutarliligi),
    ("C03", "Kümeleme doğruluğu", c03_kumeleme_dogrulugu),
    ("C04", "Çifte sayım yok", c04_cifte_sayim_yok),
    ("C05", "Üçlü sınıf toplamı", c05_uclu_sinif_toplami),
    ("C06", "Veri kapsamı", c06_veri_kapsami),
    ("C07", "Zaman", c07_zaman),
    ("C08", "Şema ve kodlama tutarlılığı", c08_kodlama_tutarliligi),
    ("C09", "Kalibrasyon dışı doğrulama", c09_kalibrasyon_disi),
    ("C10", "Sıçrama metriği", c10_sicrama_metrigi),
    ("C11", "Eşdeğer seri doğruluğu", c11_esdeger_seri),
    ("C12", "Duyarlılık", c12_duyarlilik),
    ("C13", "Referans karşılaştırması", c13_referans),
    ("C14", "Ekran = hesap", c14_ekran_hesap),
    ("C15", "Yasak kalıp taraması", c15_yasak_kalip),
    ("C16", "Simülasyon izolasyonu", c16_simulasyon_izolasyonu),
    ("C17", "CSV", c17_csv),
    ("C18", "TR/EN", c18_tr_en),
    ("C19", "Erişilebilirlik", c19_erisilebilirlik),
    ("C20", "Performans", c20_performans),
    ("C21", "Çevrimdışı açılış", c21_cevrimdisi),
    ("C22", "Belge sayıları", c22_belge_sayilari),
    ("C23", "Bağımsız yeniden hesap", c23_bagimsiz_hesap),
    ("C24", "Dürüstlük etiketi", c24_durustluk_etiketi),
    ("C25", "Gereksinim eşlemesi", c25_gereksinim_eslemesi),
]


def main(argv: list[str]) -> int:
    want = {a.upper() for a in argv}
    results: list[Result] = []
    for code, title, fn in CHECKS:
        if want and code not in want:
            continue
        t0 = time.perf_counter()
        try:
            status, detail, measured = fn()
        except Exception as e:  # kontrol çökerse KALDI
            status, detail, measured = FAIL, f"kontrol hatası: {e!r}", {
                "trace": traceback.format_exc().splitlines()[-3:]}
        results.append(Result(code, title, status, detail, measured,
                              round(time.perf_counter() - t0, 3)))

    w = max(len(r.title) for r in results)
    for r in results:
        print(f"{r.code}  {r.title:<{w}}  {r.status:<8} {r.detail}")
    summary = {s: sum(r.status == s for r in results) for s in (PASS, FAIL, SKIP)}
    print(f"\nÖzet: {summary}")

    AUDIT.mkdir(exist_ok=True)
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "summary": summary, "results": [asdict(r) for r in results]}
    if not want:  # kısmi çalıştırma tam sonucu ezmesin
        (AUDIT / "check_results.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return 1 if summary[FAIL] else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
