"""Aylık tablolar: agg/monthly.parquet (geniş) ve agg/seri_aylik.parquet (uzun, analiz girdisi).

Basitçe: Her birim (Türkiye, 7 bölge, 81 il) için her yıl-ay satırı: ham sayılar, kesinti
düzeltmeli sayılar ve uyarı bayrakları. Sensörün hiç çalışmadığı ay BOŞ kalır (sıfır değil).

Teknik olarak:
- monthly.parquet: birim, duzey (TR|bolge|il), yil, ay (TR günü ayı, K11), cal_gun, işleyen gün ve
  kesinti payı (modis/viirs/olay), ham sütunlar (düzeltmesiz), `<sütun>_kk` (kesinti-düzeltmeli, boş
  kurallı), MODIS-eşdeğer + belirsizlik bandı (yalnız TR ve bölge; il düzeyinde eşdeğer seri yoktur:
  oran tabakası bölgedir), bayrak.
- seri_aylik.parquet: birim × seri × yıl × ay: deger, alt, ust (yalnız eşdeğer), normal_yil, bayrak.
  Normal yıl kuralı (sensör tutarlı, tam yıl) yil_bilgi.parquet'ten gelir.
"""
from __future__ import annotations

import calendar
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from veri import Veri  # noqa: E402


def _duzey(u, v):
    return "TR" if u == "TR" else ("bolge" if u in v.bolgeler else "il")


def harm_oku() -> dict:
    """{seri adı: DataFrame[(birim, yil, ay)]}. Yeni şema: harmonized'da `birim` (tespit|olay) ve
    `kume` (temiz|temiz_aniz) sütunları var; eski şemada yalnız tespit/temiz."""
    h = pd.read_parquet(C.HARM)
    h = h[h["duzey"].isin(["ay_TR", "ay_bolge", "ay_il"])].copy()
    il = h["il"].astype(str) if "il" in h else pd.Series("", index=h.index)
    h["analiz_birimi"] = np.where(h["duzey"].eq("ay_TR"), "TR", np.where(h["duzey"].eq("ay_il"), il, h["bolge7"]))
    hb = h["birim"] if "birim" in h else pd.Series("tespit", index=h.index)
    hk = h["kume"] if "kume" in h else pd.Series("temiz", index=h.index)
    out = {}
    for ad, (b, k) in C.ESDEGER_KAYNAK.items():
        sub = h[(hb == b) & (hk == k)]
        if len(sub):
            out[ad] = sub.set_index(["analiz_birimi", "yil", "ay"])
    return out


def build(v: Veri | None = None) -> dict:
    t0 = time.time()
    v = v or Veri.yukle()
    yb = v.yil_bilgi
    h = harm_oku()
    ref_modis = yb["ref_era_modis"].iloc[0]
    months = pd.period_range(v.days[0], v.days[-1], freq="M")
    U = len(v.units)
    frames, srec = [], []
    for per in months:
        y, m = per.year, per.month
        i0 = max(v.idx(per.start_time), 0)
        i1 = min(v.idx((per + 1).start_time), len(v.days))
        cal = calendar.monthrange(y, m)[1]
        data = {"nrt_payi": np.full(U, v.nrt_payi(i0, i1)), "birim": v.units, "duzey": [_duzey(u, v) for u in v.units],
                "yil": np.full(U, y), "ay": np.full(U, m), "cal_gun": np.full(U, cal)}
        info = {}
        for g, c0 in (("modis", "modis_ham"), ("viirs", "viirs_ham"), ("olay", "olay")):
            _, inf = v.sayi([c0], g, False, i0, i1, cal)
            info[g] = inf
            data[f"isleyen_gun_{g}"] = np.full(U, inf["dd"])
            data[f"kesinti_pay_{g}"] = np.full(U, inf["kesinti"])
            if g != "olay":
                dd = inf["dd"]
                data[f"n_uydu_ort_{g}"] = np.full(U, (v.cO[g][i1] - v.cO[g][i0]) / dd if dd > 0 else np.nan)
        for c in C.COLS_RAW:
            data[c] = v.ham(c, i0, i1)
            data[c + "_kk"] = v.sayi([c], C.GRUP_KOL[c], False, i0, i1, cal, strict=True)[0]
        frames.append(pd.DataFrame(data))
        for s in C.SERI:
            vals = v.seri(s, i0, i1, cal, strict=True)[0]
            srec.append(pd.DataFrame({"birim": v.units, "seri": s, "yil": y, "ay": m, "deger": vals}))
    mo = pd.concat(frames, ignore_index=True)
    key = pd.MultiIndex.from_arrays([mo["birim"], mo["yil"], mo["ay"]])
    kis = mo["isleyen_gun_olay"] < mo["cal_gun"]
    hb = np.full(len(mo), "", dtype=object)
    for ad, hh in h.items():
        for c_out, c_in in ((ad, "ana_seri"), (ad + "_alt", "ana_alt"), (ad + "_ust", "ana_ust")):
            mo[c_out] = hh[c_in].reindex(key).to_numpy(dtype=float)
            mo.loc[kis, c_out] = np.nan          # kısmi ay tam aya benzetilmez
        mo[ad + "_bayrak"] = hh["bayrak"].reindex(key).fillna("").to_numpy(dtype=object)
        if ad == C.ESDEGER:
            mo["esdeger_kaynak"] = hh["ana_kaynak"].reindex(key).to_numpy(dtype=object)
            hb = hh["bayrak"].reindex(key).fillna("").to_numpy(dtype=object)
    ybi = yb.reindex(mo["yil"])
    gec = ybi["gecis_all"].to_numpy(bool)
    eski = (ybi["era_modis"].to_numpy() != ref_modis)
    kesmax = C.t("kesinti_pay_max")
    anyk = np.zeros(len(mo), bool)
    kcok = np.zeros(len(mo), bool)
    for g in ("modis", "viirs", "olay"):
        kp = mo[f"kesinti_pay_{g}"].fillna(0).to_numpy()
        anyk |= kp > 0
        kcok |= kp > kesmax
    parts = [(kis.to_numpy(), "kismi_ay"), (anyk, "kesinti_gunu_var"), (kcok, "kesinti_cok"),
             (eski, "eski_donem_modis_tek_uydu"), (gec, "sensor_gecis_yili")]
    fl = []
    for i in range(len(mo)):
        f = [n for msk, n in parts if msk[i]]
        if hb[i]:
            f.append("harm:" + str(hb[i]))
        fl.append(";".join(f))
    mo["bayrak"] = fl
    mo.to_parquet(C.MONTHLY, index=False)

    sl = pd.concat(srec, ignore_index=True)
    sl["alt"] = np.nan
    sl["ust"] = np.nan
    for ad in h:
        e = mo[mo[ad].notna()][["birim", "yil", "ay", ad, ad + "_alt", ad + "_ust"]]
        e = e.rename(columns={ad: "deger", ad + "_alt": "alt", ad + "_ust": "ust"})
        e["seri"] = ad
        sl = pd.concat([sl, e[sl.columns]], ignore_index=True)
    sl = sl[sl["deger"].notna()].copy()
    grup = sl["seri"].map(C.grup_of)
    nm = {"modis": yb["normal_modis"], "viirs": yb["normal_viirs"], "olay": yb["normal_olay"]}
    sl["normal_yil"] = False
    for g, ser in nm.items():
        msk = grup.eq(g)
        sl.loc[msk, "normal_yil"] = sl.loc[msk, "yil"].map(ser).to_numpy(bool)
    bay = pd.concat([mo[["birim", "yil", "ay", ad + "_bayrak"]].rename(columns={ad + "_bayrak": "harm_bayrak"}).assign(seri=ad)
                     for ad in h], ignore_index=True)
    sl = sl.merge(bay, on=["birim", "yil", "ay", "seri"], how="left")
    sl["harm_bayrak"] = sl["harm_bayrak"].fillna("")
    sl["sensor_gecis"] = sl["yil"].map(yb["gecis_all"]).to_numpy(bool)
    sl.to_parquet(C.SERI_AYLIK, index=False)
    return {"monthly_satir": len(mo), "seri_aylik_satir": len(sl), "sure_sn": round(time.time() - t0, 1)}


if __name__ == "__main__":
    print(build())
