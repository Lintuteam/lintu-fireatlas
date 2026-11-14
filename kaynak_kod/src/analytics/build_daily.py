"""Günlük tablolar: agg/daily.parquet, agg/daily_kapsam.parquet, agg/yil_bilgi.parquet.

Basitçe: Önce her ilin her günü için "kaç sıcak nokta / kaç olay" defterini tutuyoruz. Yanına,
o gün hangi uyduların GÖZLEM YAPABİLDİĞİNİ yazıyoruz. Gözlemsiz gün "sıfır yangın" demek değildir,
"bakılamadı" demektir; ay toplamı ve medyan hesabında bu fark kritik.

Teknik olarak:
- daily.parquet: il × day_tr (TR günü, K11), SEYREK: yalnız en az bir sayımı olan (il, gün) satırı;
  sıfır günler satır yazmaz, sorgu (veri.py) kapsamla doldurur. 'TR' satırı yoktur (il toplamı = TR).
  Sütunlar: modis_ham/temiz/aniz, viirs_ham/temiz/aniz (nokta sayısı; ham = tüm status, K3),
  enerji_modis/viirs (FRP MW, yalnız status=temiz), olay (status=temiz, day_tr_start günü),
  olay_aniz (status=aniz). Anız hariç varsayılandır; anız dahil = temiz + aniz.
- daily_kapsam.parquet: gün başına işleyen uydu (n_op) ve gözlem yapan uydu (n_obs): modis, viirs, all.
- yil_bilgi.parquet: yıl başına sensör bileşimi (era), geçiş yılı ve normal-yıl bayrakları.
Tekrar çalıştırılabilir: girdiler değişince yeniden çalıştır (sabit sayı gömülü değildir).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def sat_sensor() -> dict:
    return {k: v.lower() for k, v in C.cfg.load()["uydu_kodlari"]["sensor"].items()}


def build() -> dict:
    t0 = time.time()
    ss = sat_sensor()  # Terra/Aqua/SNPP/N20/N21 -> modis/viirs
    p = pd.read_parquet(C.POINTS, columns=["pid", "day_tr", "sensor", "frp", "il", "src_product"])
    st = pd.read_parquet(C.STATUS, columns=["pid", "status"])
    p = p.merge(st, on="pid", how="left")
    p["day"] = pd.to_datetime(p["day_tr"])
    p["il"] = p["il"].astype(str)
    s = p["sensor"].astype(str).str.lower()
    stat = p["status"].astype(str)
    temiz, aniz = stat.eq("temiz"), stat.eq("aniz")
    frp = p["frp"].astype("float64")
    cols = {}
    for g in ("modis", "viirs"):
        m = s.eq(g)
        cols[f"{g}_ham"] = m
        cols[f"{g}_temiz"] = m & temiz
        cols[f"{g}_aniz"] = m & aniz
        cols[f"enerji_{g}"] = frp.where(m & temiz, 0.0)
    df = pd.DataFrame({"il": p["il"], "day": p["day"]})
    for k, v in cols.items():
        df[k] = v.astype("float64")
    a = df.groupby(["il", "day"], sort=False).sum()
    e = pd.read_parquet(C.EVENTS, columns=["day_tr_start", "il", "status"])
    e["day"] = pd.to_datetime(e["day_tr_start"])
    e["il"] = e["il"].astype(str)
    ed = pd.DataFrame({"il": e["il"], "day": e["day"],
                       "olay": e["status"].astype(str).eq("temiz").astype("float64"),
                       "olay_aniz": e["status"].astype(str).eq("aniz").astype("float64")})
    b = ed.groupby(["il", "day"], sort=False).sum()
    d = a.join(b, how="outer").fillna(0.0).reset_index()
    for c in C.COLS_RAW:
        d[c] = d[c].astype("float32" if c.startswith("enerji") else "int32")
    d["day_tr"] = d["day"].dt.date
    d = d[["il", "day_tr"] + C.COLS_RAW].sort_values(["il", "day_tr"]).reset_index(drop=True)
    C.AGG.mkdir(parents=True, exist_ok=True)
    d.to_parquet(C.DAILY, index=False)

    # ---- kapsam ----
    cov = pd.read_parquet(C.COVERAGE, columns=["sat", "day_tr", "observed"])
    cov["day"] = pd.to_datetime(cov["day_tr"])
    cov["g"] = cov["sat"].astype(str).map(ss)
    bil = cov[cov["g"].isna()]["sat"].unique().tolist()
    days = pd.date_range(min(cov["day"].min(), df["day"].min()), cov["day"].max(), freq="D")
    k = pd.DataFrame({"day": days})
    for g in ("modis", "viirs", "all"):
        sub = cov if g == "all" else cov[cov["g"].eq(g)]
        op = sub.groupby("day").size()
        ob = sub[sub["observed"]].groupby("day").size()
        k[f"n_op_{g}"] = k["day"].map(op).fillna(0).astype("int16")
        k[f"n_obs_{g}"] = k["day"].map(ob).fillna(0).astype("int16")
    tum = p.groupby("day").size()
    nrt = p[p["src_product"].astype(str).eq("nrt")].groupby("day").size()
    k["n_nokta"] = k["day"].map(tum).fillna(0).astype("int32")
    k["n_nrt"] = k["day"].map(nrt).fillna(0).astype("int32")
    k["day_tr"] = k["day"].dt.date
    k = k.drop(columns="day")
    k.to_parquet(C.KAPSAM, index=False)

    # ---- yıl bilgisi ----
    last = cov["day"].max()
    rows = []
    for y in range(cov["day"].dt.year.min(), last.year + 1):
        cal = (min(pd.Timestamp(y, 12, 31), last) - pd.Timestamp(y, 1, 1)).days + 1
        r = {"yil": y, "kismi_yil": bool(y == last.year and last < pd.Timestamp(y, 12, 31))}
        sub = cov[cov["day"].dt.year == y]
        n_by = sub.groupby("sat").size()
        for g in ("modis", "viirs", "all"):
            sats = [s_ for s_, gg in ss.items() if g == "all" or gg == g]
            full = sorted(s_ for s_ in sats if n_by.get(s_, 0) == cal)
            part = [s_ for s_ in sats if 0 < n_by.get(s_, 0) < cal]
            r[f"era_{g}"] = "+".join(full)
            r[f"gecis_{g}"] = bool(part)
        rows.append(r)
    yb = pd.DataFrame(rows)
    ok = yb[~yb["kismi_yil"]]
    ref = ok["era_modis"].iloc[-1]
    yb["ref_era_modis"] = ref
    yb["normal_modis"] = (~yb["gecis_modis"]) & yb["era_modis"].eq(ref) & ~yb["kismi_yil"]
    yb["normal_viirs"] = (~yb["gecis_viirs"]) & yb["era_viirs"].ne("") & ~yb["kismi_yil"]
    yb["normal_olay"] = (~yb["gecis_all"]) & yb["era_all"].ne("") & ~yb["kismi_yil"]
    yb.to_parquet(C.YIL_BILGI, index=False)
    return {"daily_satir": len(d), "kapsam_gun": len(k), "bilinmeyen_sat": bil,
            "sure_sn": round(time.time() - t0, 1)}


if __name__ == "__main__":
    print(build())
