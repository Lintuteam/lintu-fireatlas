"""Ham FIRMS -> data/processed/points.parquet (şema v1, ilk 18 sütun + izlenebilirlik sütunları).

Basitçe: 27 xlsx dosyasındaki (içinde 59 tekil kaynak CSV, sütun `src_file`) her satırı, hepsi aynı sütun düzenine sahip tek bir
tabloya çeviriyoruz. Hiçbir satır atılmaz (K3); anlaşılmayan değerler sayılır ve rapora yazılır.

Teknik olarak:
- Girdi: data/interim/raw_all.parquet (F0 önbelleği; kaynağı data/raw xlsx). Yoksa xlsx'lerden okunur.
- il atama: ../demo/pipeline/build_data.py içindeki `assign_il` (even-odd nokta-çokgen) ve
  ../demo/pipeline/cache/tr-cities.json (il sınırı: cihadturhan/tr-geojson). demo DEĞİŞTİRİLMEZ,
  yalnız içe aktarılır (K7). Tekil (lat,lon) çiftleri üzerinde hesaplanır.
- Güven eşlemesi yalnız src/config/config.py (K10). Uydu kodu eşlemesi esikler.json.
- Çıktı yıl bazlı row group'lara yazılır (src_year sıralı) -> yıl filtreli okuma hızlıdır.

Kullanım: python src/pipeline/build_points.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402
from pipeline import timeutil  # noqa: E402

RAW_DIR = ROOT / "data" / "raw" / "FIRMS_Turkiye_Excel"
RAW_CACHE = ROOT / "data" / "interim" / "raw_all.parquet"
INV = ROOT / "data" / "processed" / "inventory.json"
OUT = ROOT / "data" / "processed" / "points.parquet"
META = ROOT / "data" / "processed" / "points.meta.json"
DEMO_BUILD = ROOT.parent / "demo" / "pipeline" / "build_data.py"
DEMO_GEO = ROOT.parent / "demo" / "pipeline" / "cache" / "tr-cities.json"
SCHEMA_VERSION = "v1"
OUT_COLS = ["pid", "t_utc", "day_tr", "src_year", "lat", "lon", "sensor", "sat", "frp", "scan", "track",
            "area", "conf_raw", "conf_cls", "bt_mir", "bt_tir", "bt_estimated", "dn", "type", "version",
            "src_product", "src_file", "il", "bolge"]


def peak_mem_mb():
    """Süreç zirve çalışma kümesi (MB, Windows); alınamazsa None."""
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        k32, ps = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        ps.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        ps.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return round(c.PeakWorkingSetSize / 1e6, 1)
    except Exception:
        return None


def load_raw():
    if RAW_CACHE.exists():
        return pd.read_parquet(RAW_CACHE)
    frames = []
    for p in sorted(RAW_DIR.glob("FIRMS_Turkiye_*.xlsx")):
        d = pd.read_excel(p, sheet_name=0)
        d["_file"] = p.name
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def _segments(feats):
    """Tüm il halkalarının doğru parçaları: (x1,y1,x2,y2) dizileri ve il indeksi."""
    xs1, ys1, xs2, ys2, ids = [], [], [], [], []
    for idx, f in enumerate(feats):
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:
                a = np.asarray(ring, dtype=float)[:, :2]
                b = np.roll(a, -1, axis=0)
                xs1.append(a[:, 0]); ys1.append(a[:, 1]); xs2.append(b[:, 0]); ys2.append(b[:, 1])
                ids.append(np.full(len(a), idx))
    return tuple(np.concatenate(v) for v in (xs1, ys1, xs2, ys2, ids))


def nearest_il_km(lat, lon, feats, chunk=400):
    """Çokgen dışı noktalar için en yakın ile (indeks) ve çokgen sınırına uzaklık (km).

    Basitçe: Noktadan her ilin kenar çizgisine olan en kısa mesafeyi ölçer, en yakın ili seçer.
    Teknik olarak: boylam farkı cos(enlem) ile ölçeklenen yerel düzlemde nokta-doğru parçası uzaklığı.
    İl çokgenlerinin birleşiminin dışındaki bir noktanın birleşime en yakın yeri bir dış kenardadır,
    bu yüzden tüm kenarlara en kısa mesafe = Türkiye sınırına uzaklıktır.
    """
    x1, y1, x2, y2, ids = _segments(feats)
    n_il = len(feats)
    out_km = np.empty(len(lat))
    out_il = np.empty(len(lat), dtype=np.int16)
    for s0 in range(0, len(lat), chunk):
        la, lo = lat[s0:s0 + chunk], lon[s0:s0 + chunk]
        kx = 111.32 * np.cos(np.radians(la))[:, None]
        px, py = lo[:, None], la[:, None]
        dx, dy = (x2 - x1)[None, :], (y2 - y1)[None, :]
        # parametrik izdüşüm (derece uzayında, ölçek cos ile düzeltilmiş)
        wx, wy = (px - x1) * kx, (py - y1) * 110.57
        vx, vy = dx * kx, dy * 110.57
        vv = vx * vx + vy * vy
        t = np.where(vv > 0, np.clip((wx * vx + wy * vy) / np.where(vv > 0, vv, 1), 0, 1), 0)
        d = np.hypot(wx - t * vx, wy - t * vy)
        best = np.full((len(la), n_il), np.inf)
        for k in range(n_il):
            m = ids == k
            if m.any():
                best[:, k] = d[:, m].min(axis=1)
        out_il[s0:s0 + chunk] = best.argmin(axis=1)
        out_km[s0:s0 + chunk] = best.min(axis=1)
    return out_il, out_km


def assign_il(lat, lon):
    """İl indeksi (-1 = çokgen dışı), ad listesi, en yakın il indeksi ve sınır uzaklığı (km).

    Yalnız tekil koordinatlarda hesaplar. Çokgen dışı noktalar için en yakın il ve uzaklık da döner
    (çokgen içindekilerde uzaklık 0, en yakın il = kendi ili).
    """
    spec = importlib.util.spec_from_file_location("demo_build_data", DEMO_BUILD)
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)  # yalnız tanımlar; main() çalışmaz (__name__ != __main__)
    feats = json.loads(DEMO_GEO.read_text(encoding="utf-8"))["features"]
    names = [f["properties"]["name"] for f in feats]
    key = pd.MultiIndex.from_arrays([lat, lon])
    codes, uniq = pd.factorize(key)
    ulat = np.array([u[0] for u in uniq], dtype=float)
    ulon = np.array([u[1] for u in uniq], dtype=float)
    uil = demo.assign_il(ulat, ulon, feats)
    near = uil.astype(np.int16).copy()
    dist = np.zeros(len(uil))
    out = np.where(uil < 0)[0]
    if len(out):
        ni, nd = nearest_il_km(ulat[out], ulon[out], feats)
        near[out], dist[out] = ni, nd
    return uil[codes], names, near[codes], dist[codes]


def build(raw):
    n_raw = len(raw)
    rep = {}
    ucfg = cfg.load()["uydu_kodlari"]
    t_utc = pd.to_datetime(raw["acq_datetime_utc"], utc=True)
    src_year = raw["_file"].str.extract(r"(\d{4})")[0].astype("int16")
    row_no = raw.groupby("_file").cumcount().astype("int64")
    pid = src_year.astype("int64") * 10_000_000 + row_no

    sat = raw["satellite"].map(cfg.uydu_kodu)
    unk_sat = sat.eq(ucfg["bilinmeyen_etiket"])
    rep["bilinmeyen_uydu_satir"] = int(unk_sat.sum())
    rep["bilinmeyen_uydu_adlari"] = raw.loc[unk_sat, "satellite"].value_counts().to_dict()
    exp_sensor = sat.map(ucfg["sensor"])
    rep["sensor_uydu_celiski"] = int((exp_sensor.notna() & (exp_sensor != raw["sensor"])).sum())

    conf_cls = cfg.guven_sinifi_seri(raw["sensor"], raw["confidence_raw"])
    bil = cfg.load()["guven"]["bilinmeyen_etiket"]
    rep["bilinmeyen_guven_satir"] = int(conf_cls.eq(bil).sum())
    # Yalnız DENETİM amaçlı (sonuca girmez): F0 önbelleğindeki ham low/nominal/high sütunuyla tutarlılık.
    # Güven cetveli tek yerdedir (config.py / esikler.json); aşağıdaki sözlük yalnız ham sütunu okumak içindir.
    ham_ad = cfg.load()["guven"]["VIIRS"]["esleme"]
    ham_ad = {"low": ham_ad["l"], "nominal": ham_ad["n"], "high": ham_ad["h"]}
    rep["guven_ham_sinifla_celisen"] = int((raw["confidence_cls"].map(ham_ad) != conf_cls).sum())

    il_idx, names, near_idx, dist_km = assign_il(raw["latitude"].to_numpy(), raw["longitude"].to_numpy())
    b_km = cfg.esik("B")
    inside = il_idx >= 0
    kiyi = ~inside & (dist_km <= b_km)
    yurt_disi = ~inside & ~kiyi
    lut = np.asarray(names + ["(yurt dışı)"], dtype=object)
    il = pd.Series(lut[np.where(yurt_disi, len(names), np.where(inside, il_idx, near_idx))])
    bolge = pd.Series(np.where(inside, "il", np.where(kiyi, "kiyi", "yurt_disi")))
    rep["il_atanamayan_satir"] = int((~inside).sum())
    rep["bolge_il_satir"] = int(inside.sum())
    rep["bolge_kiyi_satir"] = int(kiyi.sum())
    rep["bolge_yurt_disi_satir"] = int(yurt_disi.sum())
    rep["kiyi_tampon_km"] = b_km

    est = raw["bt_mir_band"].str.endswith("ornek_esleme") | raw["bt_tir_band"].str.endswith("ornek_esleme")
    is_nrt = raw["version"].astype(str).str.contains("NRT", na=False)
    df = pd.DataFrame({
        "pid": pid.to_numpy(),
        "t_utc": t_utc.to_numpy(),
        "day_tr": timeutil.tr_day(t_utc).to_numpy(),
        "src_year": src_year.to_numpy(),
        "lat": raw["latitude"].to_numpy("float64"),
        "lon": raw["longitude"].to_numpy("float64"),
        "sensor": raw["sensor"].astype("category").to_numpy(),
        "sat": sat.astype("category").to_numpy(),
        "frp": raw["frp_mw"].astype("float32").to_numpy(),
        "scan": raw["scan_km"].astype("float32").to_numpy(),
        "track": raw["track_km"].astype("float32").to_numpy(),
        "area": raw["pixel_area_km2"].astype("float32").to_numpy(),
        "conf_raw": raw["confidence_raw"].astype(str).to_numpy(),
        "conf_cls": conf_cls.astype("category").to_numpy(),
        "bt_mir": raw["bt_mir_k"].astype("float32").to_numpy(),
        "bt_tir": raw["bt_tir_k"].astype("float32").to_numpy(),
        "bt_estimated": est.to_numpy(),
        "dn": raw["daynight"].astype("category").to_numpy(),
        "type": raw["type"].fillna(-1).astype("int8").to_numpy(),
        "version": raw["version"].astype(str).to_numpy(),
        "src_product": pd.Series(np.where(is_nrt, "nrt", "archive")).astype("category").to_numpy(),
        "src_file": raw["source_file"].astype(str).to_numpy(),
        "il": il.astype("category").to_numpy(),
        "bolge": bolge.astype("category").to_numpy(),
    })
    assert len(df) == n_raw, "satır sayısı değişti (K3)"
    rep["nrt_satir"] = int(is_nrt.sum())
    rep["bt_estimated_satir"] = int(est.sum())
    rep["type_yok_satir"] = int((df["type"] == -1).sum())
    return df, rep


def write(df):
    """Yıl bazlı row group; yıl/zaman filtreli okuma için sıralı yazar."""
    df = df.sort_values(["src_year", "t_utc", "pid"], kind="stable").reset_index(drop=True)
    table = pa.Table.from_pandas(df[OUT_COLS], preserve_index=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    yrs = df["src_year"].to_numpy()
    with pq.ParquetWriter(tmp, table.schema, compression="zstd") as w:
        for yr in sorted(set(yrs.tolist())):
            idx = np.where(yrs == yr)[0]
            w.write_table(table.slice(int(idx[0]), len(idx)), row_group_size=len(idx))
    tmp.replace(OUT)


def main():
    t0 = time.perf_counter()
    raw = load_raw()
    t_read = time.perf_counter() - t0
    t1 = time.perf_counter()
    df, rep = build(raw)
    t_build = time.perf_counter() - t1
    t2 = time.perf_counter()
    write(df)
    t_write = time.perf_counter() - t2
    inv = json.loads(INV.read_text(encoding="utf-8")) if INV.exists() else {}
    files = inv.get("files_sha256", {})
    raw_hash = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(files.items())).encode()).hexdigest()
    meta = {
        "betik": "src/pipeline/build_points.py", "sema_surumu": SCHEMA_VERSION,
        "satir_sayisi": int(len(df)), "ham_satir_sayisi_beklenen": inv.get("raw_rows_total"),
        "sutunlar": OUT_COLS,
        "ham_girdi": str(RAW_CACHE.relative_to(ROOT)) if RAW_CACHE.exists() else "data/raw xlsx",
        "ham_dosya_sha256": files, "ham_birlesik_sha256": raw_hash,
        "il_kaynagi": "../demo/pipeline/build_data.py assign_il + cache/tr-cities.json (cihadturhan/tr-geojson)",
        "rapor": rep,
        "olcum": {"okuma_s": round(t_read, 2), "donusum_il_s": round(t_build, 2), "yazma_s": round(t_write, 2),
                  "toplam_s": round(time.perf_counter() - t0, 2), "zirve_bellek_mb": peak_mem_mb(),
                  "dosya_mb": round(OUT.stat().st_size / 1e6, 1)},
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"satir": len(df), **meta["olcum"], **rep}, ensure_ascii=False, default=str, indent=1))


if __name__ == "__main__":
    main()
