"""Anız iklim takvimi: bölge × ay profili (yıl dışarıda bırakmayla) ve bağımsız hasat kontrolü.

Basitçe: Tarlada hasattan sonra sap/anız yakılır. Bu küçük, kısa, zayıf ateşler her yıl
aşağı yukarı aynı aylarda tekrar eder, ama aylar bölgeden bölgeye değişir (Çukurova'da
hasat erken, Doğu'da geç). Burada her coğrafi bölge için "küçük ateşler yılın hangi
aylarında yoğunlaşıyor?" sorusunu 20 yılın verisinden öğreniyoruz. Hile olmasın diye
bir yılın takvimini hep o yıl hariç diğer yıllardan öğreniyoruz. Sonra bu ayları, uydu
verisinden bağımsız bir kaynakla (hasat takvimi) karşılaştırıyoruz.

Teknik olarak:
- Küçük-aday (nokta düzeyi, olaydan önceki vekil): FRP < F_sensör ve aynı gün 3×3 hücre
  (~3 km) komşulukta en çok `aniz_kucuk_komsu` tespit. F MODIS ölçeğinde MW'dir; VIIRS
  eşdeğeri yüzdelik eşleştirmeyle bulunur (F'nin MODIS type=0 dağılımındaki yüzdeliği,
  VIIRS type=0 dağılımında aynı yüzdeliğe karşılık gelen FRP). Sabit oran yok (K8).
- Profil: bölge × yıl × ay aday sayısı -> yıl içi pay -> yıllar arası ortalama pay.
- Anız ayları: payı 1/12'yi aşan aylar (`aniz_ay_kurali`=uniform_ustu); duyarlılık için top3,
  top5, demo Ağu–Ara.
- LOYO: Y yılının ayları Y hariç yıllardan; ölçü: Y yılındaki adayların öğrenilen aylara düşme
  payı (kapsama) ve aynı aylara düşen büyük (aday olmayan) tespit payı (taban) -> kaldıraç.
- Bağımsız kontrol: `temizlik.hasat_penceresi` (web kaynaklı kaba ulusal hasat takvimi).
  Arazi örtüsü (tarım alanı) kontrolü bu adımda YAPILAMADI -> etiket 'doğrulanmadı'.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as C
import persistence as P

KURALLAR = ("uniform_ustu", "top3", "top5", "demo")


def frp_esikleri(df: pd.DataFrame, F: float) -> dict:
    """MODIS F (MW) -> VIIRS eşdeğeri, arşiv type=0 dağılımlarında yüzdelik eşleştirme."""
    a = df[(df["type"] == 0)]
    m = a.loc[a["sensor"] == "MODIS", "frp"].to_numpy()
    v = a.loc[a["sensor"] == "VIIRS", "frp"].to_numpy()
    q = float((m < F).mean())
    return {"MODIS": float(F), "VIIRS": float(np.quantile(v, q)), "yuzdelik": q,
            "modis_type0_medyan": float(np.median(m)), "viirs_type0_medyan": float(np.median(v))}


def kucuk_aday(df: pd.DataFrame, esik: dict, k_max: int) -> np.ndarray:
    """df: değerlendirilecek noktalar (genelde NASA/kalıcı dışı). Komşuluk sayımı aynı kümeden."""
    fthr = np.where(df["sensor"].to_numpy() == "MODIS", esik["MODIS"], esik["VIIRS"])
    yerel = P.komsu_gun_sayimi(df["cell"].to_numpy(), df["dayn"].to_numpy(),
                               df["cell"].to_numpy(), df["dayn"].to_numpy(), 1)
    return (df["frp"].to_numpy() < fthr) & (yerel <= k_max)


def profil(cand: pd.DataFrame, haric_yil=None) -> pd.DataFrame:
    """cand: aday noktalar (cbolge, yr, mon). Dönen: bölge × ay ortalama yıllık pay."""
    c = cand if haric_yil is None else cand[cand["yr"] != haric_yil]
    cnt = c.groupby(["cbolge", "yr", "mon"]).size().unstack(fill_value=0).reindex(columns=range(1, 13), fill_value=0)
    pay = cnt.div(cnt.sum(axis=1), axis=0)
    return pay.groupby(level="cbolge").mean()


def aylar(pr: pd.DataFrame, kural: str, demo_aylar) -> dict:
    out = {}
    for b, row in pr.iterrows():
        if kural == "uniform_ustu":
            out[b] = sorted(int(m) for m in row.index[row.to_numpy() > 1 / 12])
        elif kural in ("top3", "top5"):
            n = 3 if kural == "top3" else 5
            out[b] = sorted(int(m) for m in row.sort_values(ascending=False).index[:n])
        else:
            out[b] = sorted(int(m) for m in demo_aylar)
    return out


def ay_maskesi(am: dict, bolgeler) -> np.ndarray:
    """bölge kodu × ay (0..12) bool tablo."""
    tab = np.zeros((len(bolgeler), 13), bool)
    for i, b in enumerate(bolgeler):
        for m in am.get(b, []):
            tab[i, m] = True
    return tab


def ayda_mi(d: pd.DataFrame, am: dict, bolgeler) -> np.ndarray:
    code = pd.Categorical(d["cbolge"], categories=bolgeler).codes
    tab = ay_maskesi(am, bolgeler)
    ok = code >= 0
    out = np.zeros(len(d), bool)
    out[ok] = tab[code[ok], d["mon"].to_numpy()[ok]]
    return out


def loyo(df_eval: pd.DataFrame, is_cand: np.ndarray, kural: str, demo_aylar) -> dict:
    bolgeler = sorted(df_eval["cbolge"].unique())
    cand = df_eval[is_cand]
    big = df_eval[~is_cand]
    rows = []
    for y in sorted(df_eval["yr"].unique()):
        cy_ = cand[cand["yr"] == y]
        if len(cy_) < 50:
            continue
        am = aylar(profil(cand, haric_yil=y), kural, demo_aylar)
        by_ = big[big["yr"] == y]
        kap = float(ayda_mi(cy_, am, bolgeler).mean())
        tab = float(ayda_mi(by_, am, bolgeler).mean()) if len(by_) else float("nan")
        rows.append({"yil": int(y), "kapsama": kap, "taban": tab, "n_aday": int(len(cy_))})
    r = pd.DataFrame(rows)
    return {"kapsama_ort": float(r["kapsama"].mean()), "taban_ort": float(r["taban"].mean()),
            "kaldirac": float(r["kapsama"].mean() / r["taban"].mean()), "yil_sayisi": int(len(r)),
            "yillar": rows}


def hasat_uyumu(am: dict, pencere) -> dict:
    tum = [m for v in am.values() for m in v]
    ic = [m for m in tum if m in set(pencere)]
    return {"ay_sayisi": len(tum), "pencere_ici": len(ic), "pay": len(ic) / len(tum) if tum else float("nan")}
