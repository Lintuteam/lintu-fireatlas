"""Olay düzeyi harmonize seri (ay × il): "MODIS bu ayda bu ilde kaç yangın olayı görürdü?"

Basitçe: Tespit (piksel) yerine yangın olayını sayıyoruz (kumeleme ajanının ortak olayları:
MODIS ve VIIRS aynı yangını tek olay sayar). Hedef: içinde en az bir MODIS tespiti olan olay
sayısı. VIIRS'in gördüğü olaylardan bu sayıyı tahmin ediyoruz; yine her yılı saklayıp sınıyoruz.

Teknik olarak:
- Olay: events.parquet (`status` ∈ küme). Gerçek = n_modis > 0 olan olaylar.
- VIIRS olay özelliği: olaydaki VIIRS noktalarının FRP toplamı -> büyüklük sınıfı
  (`frp_sinif_sinirlari_mw`); VIIRS'siz olaylar "viirs_yok".
- Gözlem eforu: her VIIRS uydusu için "o uydunun gördüğü olay" o uydunun olaydaki ilk günüyle
  sayılır; günlük gözleyen uydu başına ortalama alınır (seri.efor_normalize).
- Yöntemler: (i0) sabit oran efor yok; (i) sabit oran eforlu; (ii) bölge × mevsim × VIIRS FRP
  sınıfı oranı (yalnız-MODIS olaylar bölge × mevsim payıyla) eforlu. Tespit düzeyinde kaybeden
  (iii) olay düzeyinde koşulmadı (belge §10).
- Seçim: tespit düzeyindeki ölçüt, ay × bölge WAPE (LOYO 2012-2025). Çıktı il düzeyinde de verilir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak as O  # noqa: E402
import seri  # noqa: E402

BETIK = "src/harmonize/olay.py"
SIN = ("kucuk", "orta", "buyuk")
KEYS = ["yil", "ay", "il"]


def tablo(kume: str):
    e = pd.read_parquet(O.EVENTS, columns=["event_id", "day_tr_start", "il", "n_modis", "n_viirs", "status"])
    e = e[e["status"].isin(O.KUMELER[kume])].copy()
    d = pd.to_datetime(e["day_tr_start"])
    e["yil"], e["ay"] = d.dt.year, d.dt.month
    e["mevsim"] = e["ay"].map(O.MEVSIM)
    e["bolge7"] = e["il"].map(O.IL_BOLGE).fillna("bilinmeyen")
    p = pd.read_parquet(O.POINTS, columns=["pid", "sat", "sensor", "frp", "day_tr"])
    p = p.merge(pd.read_parquet(O.POINTS_EVENT), on="pid")
    p = p[p["event_id"].isin(e["event_id"])]
    v = p[p["sensor"].eq("VIIRS")]
    vf = v.groupby("event_id")["frp"].sum()
    e["vfrp"] = e["event_id"].map(vf)
    e["fs"] = np.where(e["n_viirs"] > 0, seri.frp_sinif(e["vfrp"].fillna(0).to_numpy()), "viirs_yok")
    e["modis"] = e["n_modis"] > 0
    # Uydu başına görülen olay (ilk gün) -> eforlu sayım
    vs = v.groupby(["event_id", "sat"])["day_tr"].min().reset_index()
    vs["day"] = pd.to_datetime(vs["day_tr"])
    vs = vs.merge(e[["event_id", "il", "bolge7", "fs"]], on="event_id")
    vs["one"] = 1.0
    cov = pd.read_parquet(O.COVERAGE, columns=["sat", "day_tr", "observed"])
    cov["day"] = pd.to_datetime(cov["day_tr"])
    vs = vs.rename(columns={"bolge7": "_b"}).assign(bolge7=lambda x: x["il"])   # efor_normalize 'bolge7' anahtarını il için kullan
    Ve, _ = seri.efor_normalize(vs, cov, ["one"], ["fs"])
    Ve = Ve.rename(columns={"bolge7": "il"}).pivot_table(index=KEYS, columns="fs", values="one", fill_value=0)
    Ve = Ve.add_prefix("V_").reset_index()
    Ve["V_eff_det"] = Ve[[f"V_{s}" for s in SIN]].sum(axis=1)
    M = e[e["modis"]].groupby(KEYS).size().rename("M_true")
    Mc = e[e["modis"]].groupby(KEYS + ["fs"]).size().unstack("fs", fill_value=0).add_prefix("M_")
    Vraw = e[e["n_viirs"] > 0].groupby(KEYS).size().rename("V_raw")
    T = pd.concat([M, Mc, Vraw], axis=1).reset_index().merge(Ve, on=KEYS, how="outer").fillna(0)
    for s in SIN + ("viirs_yok",):
        for pre in ("M_", "V_"):
            if pre + s not in T:
                T[pre + s] = 0.0
    T["bolge7"] = T["il"].map(O.IL_BOLGE).fillna("bilinmeyen")
    T["mevsim"] = T["ay"].map(O.MEVSIM)
    return T, e


def y_tabakali(T, tr, te):
    mn = float(O.h("min_ornek"))
    pred = pd.Series(0.0, index=T.index[te])
    idx2 = pd.MultiIndex.from_frame(T.loc[te, ["bolge7", "mevsim"]])
    for fs in SIN:
        a = T.loc[tr].groupby(["bolge7", "mevsim"])[[f"M_{fs}", f"V_{fs}"]].sum()
        b = T.loc[tr].groupby("mevsim")[[f"M_{fs}", f"V_{fs}"]].sum()
        r1 = (a[f"M_{fs}"] / a[f"V_{fs}"]).where(a[f"V_{fs}"] >= mn)
        r = pd.Series(r1.reindex(idx2).to_numpy(), index=pred.index)
        r = r.fillna(pd.Series((b[f"M_{fs}"] / b[f"V_{fs}"]).reindex(T.loc[te, "mevsim"]).to_numpy(), index=pred.index))
        pred += T.loc[te, f"V_{fs}"] * r.fillna(0)
    # yalnız-MODIS olaylar: bölge × mevsim, VIIRS olayı başına pay
    a = T.loc[tr].groupby(["bolge7", "mevsim"])[["M_viirs_yok", "V_eff_det"]].sum()
    b = T.loc[tr].groupby("mevsim")[["M_viirs_yok", "V_eff_det"]].sum()
    r1 = (a["M_viirs_yok"] / a["V_eff_det"]).where(a["V_eff_det"] >= mn)
    r = pd.Series(r1.reindex(idx2).to_numpy(), index=pred.index)
    r = r.fillna(pd.Series((b["M_viirs_yok"] / b["V_eff_det"]).reindex(T.loc[te, "mevsim"]).to_numpy(), index=pred.index))
    return pred + T.loc[te, "V_eff_det"] * r.fillna(0)


def main(kume: str = "temiz") -> dict:
    T, e = tablo(kume)
    a, b = O.h("loyo_test_yillari")
    years = list(range(a, b + 1))
    preds = {k: pd.Series(np.nan, index=T.index) for k in ("i0", "i", "ii")}
    for y in years + [b + 1]:
        tr = T["yil"].isin(years) & ~T["yil"].eq(y)
        te = T["yil"].eq(y)
        preds["i0"][te] = seri.y_sabit(T, tr, te, "V_raw")
        preds["i"][te] = seri.y_sabit(T, tr, te, "V_eff_det")
        preds["ii"][te] = y_tabakali(T, tr, te)
    for k, s in preds.items():
        T[f"pred_{k}"] = s
    test = T[T["yil"].isin(years)]
    sonuc = {k: seri.olcutler(test, f"pred_{k}") for k in preds}
    kaz = min(sonuc, key=lambda k: sonuc[k]["ay_bolge_wape"])
    pred = f"pred_{kaz}"
    # il düzeyi WAPE (bilgi)
    for k in preds:
        g = test.groupby(KEYS)[["M_true", f"pred_{k}"]].sum()
        sonuc[k]["ay_il_wape"] = round(float((g[f"pred_{k}"] - g["M_true"]).abs().sum() / g["M_true"].sum() * 100), 2)
    # Bant: il ve ülke düzeyi (bölge anahtarına il koyarak aynı işlev)
    Ti = T.rename(columns={"bolge7": "_b7"}).rename(columns={"il": "bolge7"})
    bq = seri.bant_quantilleri(Ti, years, pred)
    j = seri.sicrama_paketi(T.groupby("yil")[["M_true", "V_raw", "V_eff_det", pred]].sum(), pred)
    # Eski dönem üst bant: 2003-2011 olaylarında Aqua'nın Terra'ya eklediği olay payı (mevsim başına)
    p = pd.read_parquet(O.POINTS, columns=["pid", "sat"]).merge(pd.read_parquet(O.POINTS_EVENT), on="pid")
    s = p[p["sat"].isin(O.MODIS_SATS)].groupby(["event_id", "sat"]).size().unstack(fill_value=0)
    ee = e[e["yil"].between(2003, 2011) & e["modis"]].set_index("event_id")
    s = s.reindex(ee.index).fillna(0)
    ee["terra"], ee["yalniz_aqua"] = s.get("Terra", 0) > 0, (s.get("Aqua", 0) > 0) & (s.get("Terra", 0) == 0)
    k = ee.groupby(["mevsim", "yil"])[["yalniz_aqua", "terra"]].sum()
    eski_k = (k["yalniz_aqua"] / k["terra"].clip(lower=1)).groupby(level="mevsim").quantile(0.975)
    jy = {k: seri.sicrama_paketi(T.groupby("yil")[["M_true", "V_raw", "V_eff_det", f"pred_{k}"]].sum(), f"pred_{k}")
          for k in preds}
    return dict(T=T, jump_yontem=jy, sonuc=sonuc, kazanan=kaz, bq=bq, jump=j, years=years, eski_k=eski_k, kume=kume)
