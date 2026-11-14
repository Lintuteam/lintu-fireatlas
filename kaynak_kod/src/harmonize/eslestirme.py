"""Eşleştirme birimi (U-02): VIIRS noktalarını MODIS pikselinin gerçek ayak izine bağlar.

Basitçe: MODIS bir yangını büyük bir "kare" (piksel) içinde görür; VIIRS aynı yangını küçük
karelerle görür. Her VIIRS noktasını, yakın zamanda geçen MODIS'in büyük karesine bağlarız.
Böylece "MODIS'te 1, VIIRS'te 4 yangın" sorunu tek hücreye iner; VIIRS noktaları silinmez,
yalnız hangi MODIS karesine düştükleri yazılır (ayrıntı korunur, U-04).

Teknik olarak:
- MODIS ayak izi = tespit merkezinde `scan` (doğu-batı) × `track` (kuzey-güney) km dikdörtgen,
  her yönde VIIRS yarım piksel tamponu (`eslesme_tamponu_km`) ile genişletilir. Yörünge eğimi
  (~10°) ihmal edilir; tampon bu sapmayı da karşılar (sınırlama, belgede).
- Zaman: |Δt| <= `mcell_zaman_penceresi_saat` (Terra ile VIIRS arasındaki ~2-3,6 saatlik farkı kapsar).
- Normalize uzaklık d = max(|dx|/(scan/2+tampon), |dy|/(track/2+tampon)); d <= 1 ise iz içinde.
- Kenar pikselleri büyür ve üst üste biner -> bir VIIRS noktası birden çok ize düşebilir.
  KURAL: önce kalibrasyon penceresi içindeki (eşzamanlı) izler, sonra en küçük d, sonra en küçük
  |Δt|, sonra en küçük alan. Böylece nokta her zaman TEK hücreye gider (çift sayım yok).
- VIIRS pikselinin iki MODIS hücresine taşması: nokta merkezi kuralı; FRP bölünmez, tampon
  yarım piksel taşmayı yakalar.
- İze düşmeyen VIIRS noktası (yalnız VIIRS) -> yedek sabit ızgara hücresi (`izgara_derece`).
- Her nokta ayrıca karşılaştırma için sabit ızgara kimliği `mcell_izgara` alır.
Çıktılar: data/processed/points_mcell.parquet (pid anahtarlı yan tablo; K3: tüm noktalar),
data/interim/harmonize/pairs.parquet (tüm aday çiftler), passes.parquet (yörünge geçiş kimliği).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak as O  # noqa: E402

BETIK = "src/harmonize/eslestirme.py"


def gecis_kimligi(p: pd.DataFrame) -> pd.Series:
    """Uydu başına zamana göre sıralayıp, ardışık tespitler arasında `gecis_ayirma_dk`'dan uzun
    boşluk varsa yeni yörünge geçişi başlatır. Ardışık yörüngeler ~100 dk arayla gelir."""
    gap = pd.Timedelta(minutes=float(O.h("gecis_ayirma_dk")))
    out = pd.Series(np.zeros(len(p), dtype=np.int64), index=p.index)
    base = 0
    for sat, g in p.sort_values("t_utc").groupby("sat", sort=True, observed=True):
        new = g["t_utc"].diff().gt(gap).cumsum().to_numpy()
        out.loc[g.index] = base + new
        base += int(new.max()) + 1
    return out


def aday_ciftler(m: pd.DataFrame, v: pd.DataFrame) -> pd.DataFrame:
    """MODIS izine düşen tüm (VIIRS, MODIS) aday çiftleri."""
    buf = O.tampon_km()
    W = float(O.h("mcell_zaman_penceresi_saat"))
    half = np.maximum(m["scan"].to_numpy(), m["track"].to_numpy()) / 2 + buf
    R = float(half.max()) * 1.08   # 1.08: sabit lat0 ile x ölçeğinin 36-42° arası sapma payı
    mx, my = O.km_xy(m["lat"], m["lon"])
    vx, vy = O.km_xy(v["lat"], v["lon"])
    t0 = pd.Timestamp("2000-01-01", tz="UTC")
    mt = (m["t_utc"] - t0).dt.total_seconds().to_numpy() / 3600.0
    vt = (v["t_utc"] - t0).dt.total_seconds().to_numpy() / 3600.0
    s = R / W
    tm = cKDTree(np.c_[mx, my, mt * s])
    tv = cKDTree(np.c_[vx, vy, vt * s])
    coo = tv.sparse_distance_matrix(tm, R, p=np.inf, output_type="coo_matrix")
    vi, mi = coo.row, coo.col
    mlat = m["lat"].to_numpy()[mi]
    dx = np.abs(v["lon"].to_numpy()[vi] - m["lon"].to_numpy()[mi]) * O.KM_PER_DEG * np.cos(np.radians(mlat))
    dy = np.abs(v["lat"].to_numpy()[vi] - mlat) * O.KM_PER_DEG
    hx = m["scan"].to_numpy()[mi] / 2 + buf
    hy = m["track"].to_numpy()[mi] / 2 + buf
    d = np.maximum(dx / hx, dy / hy)
    dt = (vt[vi] - mt[mi]) * 60.0
    ok = (d <= 1.0) & (np.abs(dt) <= W * 60.0)
    pr = pd.DataFrame({
        "v_pid": v["pid"].to_numpy()[vi[ok]], "m_pid": m["pid"].to_numpy()[mi[ok]],
        "v_sat": v["sat"].to_numpy()[vi[ok]], "m_sat": m["sat"].to_numpy()[mi[ok]],
        "dt_dk": dt[ok].astype("float32"), "dnorm": d[ok].astype("float32"),
        "m_area": (m["scan"].to_numpy()[mi[ok]] * m["track"].to_numpy()[mi[ok]]).astype("float32"),
    })
    return pr


def izgara_id(lat, lon) -> pd.Series:
    g = float(O.h("izgara_derece"))
    a = np.floor(np.asarray(lat) / g).astype(np.int64)
    b = np.floor(np.asarray(lon) / g).astype(np.int64)
    return pd.Series("G" + pd.Series(a).astype(str) + "_" + pd.Series(b).astype(str))


def main() -> dict:
    t_start = time.time()
    p = O.load_points()
    p["pass_id"] = gecis_kimligi(p)
    m = p[p["sensor"].eq("MODIS")].reset_index(drop=True)
    v = p[p["sensor"].eq("VIIRS")].reset_index(drop=True)
    pr = aday_ciftler(m, v)
    Wc = float(O.h("kalibrasyon_zaman_penceresi_dk"))
    pr["esz"] = pr["dt_dk"].abs() <= Wc
    # Kenar/üst üste binme kuralı: eşzamanlı önce, sonra d, |Δt|, alan
    pr["_k"] = (~pr["esz"]).astype(int)
    pr["_adt"] = pr["dt_dk"].abs()
    sec = (pr.sort_values(["v_pid", "_k", "dnorm", "_adt", "m_area"])
             .drop_duplicates("v_pid")[["v_pid", "m_pid", "m_sat", "dt_dk", "dnorm", "esz"]])
    n_cok = pr.groupby("v_pid").size()
    out = pd.DataFrame({"pid": p["pid"].to_numpy(), "sensor": p["sensor"].to_numpy(),
                        "yil": p["yil"].to_numpy()})
    out = out.merge(sec.rename(columns={"v_pid": "pid"}), on="pid", how="left")
    is_m = out["sensor"].eq("MODIS")
    out["mcell_izgara"] = izgara_id(p["lat"], p["lon"]).to_numpy()
    out["mcell"] = np.where(is_m, "M" + out["pid"].astype(str),
                            np.where(out["m_pid"].notna(),
                                     "M" + out["m_pid"].astype("Int64").astype(str),
                                     out["mcell_izgara"]))
    out["mcell_tur"] = np.where(is_m | out["m_pid"].notna(), "modis_izi", "izgara")
    out["n_aday_iz"] = out["pid"].map(n_cok).fillna(0).astype("int16")
    # Nokta düzeyi eşleşme sınıfı (olay düzeyi kumeleme'de: events.match_class)
    m_with_v = set(pr["m_pid"].unique())
    viirs_basla = int(p.loc[p["sensor"].eq("VIIRS"), "yil"].min())
    tek = out["yil"] < viirs_basla
    out["match_nokta"] = np.select(
        [tek, is_m & out["pid"].isin(m_with_v), is_m, out["m_pid"].notna()],
        ["tek_sensor_donemi", "ortak", "yalniz_modis", "ortak"], "yalniz_viirs")
    # Öğrenilmiş güven (S1; esikler.json -> harmonizasyon.ogrenilen_guven_esleme; K10)
    out["conf_cls_ogr"] = O.cfg.ogrenilen_guven_sinifi_seri(p["sensor"], p["conf_raw"]).to_numpy()
    out = out.rename(columns={"m_pid": "modis_pid"})
    out["modis_pid"] = out["modis_pid"].astype("Int64")
    O.OUT_MCELL.parent.mkdir(parents=True, exist_ok=True)
    cols = ["pid", "mcell", "mcell_tur", "mcell_izgara", "modis_pid", "dt_dk", "dnorm",
            "n_aday_iz", "match_nokta", "conf_cls_ogr"]
    assert len(out) == len(p), "K3: satır kaybı"
    out[cols].to_parquet(O.OUT_MCELL, index=False)
    O.INTERIM.mkdir(parents=True, exist_ok=True)
    pr.drop(columns=["_k", "_adt"]).to_parquet(O.INTERIM / "pairs.parquet", index=False)
    p[["pid", "pass_id"]].to_parquet(O.INTERIM / "passes.parquet", index=False)

    # --- Ölçümler: ayak izi vs sabit ızgara ("1 MODIS'e 4 VIIRS" sorunu) ---
    ov = out[(~is_m) & out["yil"].ge(viirs_basla)]
    iz = out[out["mcell_tur"].eq("modis_izi") & ~is_m]
    grp = iz.groupby("mcell")
    st = {
        "viirs_nokta_cakisma": int(len(ov)),
        "viirs_modis_izinde": int((ov["mcell_tur"] == "modis_izi").sum()),
        "viirs_coklu_iz_aday": int((ov["n_aday_iz"] > 1).sum()),
        "modis_izi_basina_viirs_ort": float(grp.size().mean()),
        "modis_izi_basina_izgara_hucre_ort": float(grp["mcell_izgara"].nunique().mean()),
        "modis_izi_birden_cok_izgaraya_bolunen_oran": float((grp["mcell_izgara"].nunique() > 1).mean()),
        "match_nokta": out["match_nokta"].value_counts().to_dict(),
        "aqua_viirs_dt_dk_yuzdelik": pr.loc[pr["m_sat"].eq("Aqua"), "dt_dk"].abs()
                                       .quantile([.05, .25, .5, .75, .95]).round(1).to_dict(),
        "sure_sn": round(time.time() - t_start, 1),
    }
    O.json_yaz(O.INTERIM / "eslestirme_olcum.json", st)
    return st


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import json
    print(json.dumps(main(), ensure_ascii=False, indent=1, default=str))
