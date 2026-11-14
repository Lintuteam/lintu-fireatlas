"""Harmonizasyon boru hattı: eşleştirme -> güven eşlemesi -> seri/LOYO/sıçrama -> çıktılar.

Basitçe: Tek komutla bütün harmonizasyonu baştan üretir ve ölçtüğü her sayıyı
reports/metrics_parts/harmonizasyon.json'a yazar (K1: sayılar hesaplanır, yazılmaz).

Teknik olarak: `python src/harmonize/run_all.py` sonra `python tools/build_metrics.py`.
Çıktılar:
- data/processed/points_mcell.parquet  (eslestirme.py; tüm noktalar, K3)
- data/processed/agg/harmonized.parquet (ay × bölge, ay × ülke, yıl × ülke düzeyleri)
- data/interim/harmonize/*.json         (ayrıntılı ölçümler: güven, FRP50, yöntem tabloları)
Tüm olay sayıları tamsayıdır; belirsizlik alt/üst bant sütunlarıyla verilir.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak as O  # noqa: E402
import eslestirme  # noqa: E402
import guven_esleme  # noqa: E402
import seri  # noqa: E402
import olay  # noqa: E402

YONTEM_AD = {"i0": "(i0) sabit oran, efor yok", "i": "(i) sabit oran, eforlu",
             "ii": "(ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu",
             "iii": "(iii) FRP eşik eğrisi + yalnız-MODIS payı + Terra payı, eforlu"}


def eski_donem_ust(T: pd.DataFrame) -> pd.Series:
    """Yalnız-Terra ayları için üst bant çarpanı (mevsim başına): 2003-2011 ülke geneli
    mevsimlik Aqua/Terra oranının %97,5 yüzdeliği. Ay/bölge düzeyindeki küçük sayılar oranı
    gürültülü yaptığı için ülke × mevsim düzeyi kullanılır. Nokta değer DÜZELTİLMEZ (gerçek Terra
    sayısı kalır); yalnız üst bant "Aqua da olsaydı en çok bu kadar" diye genişler (tahmini)."""
    d = T[T["yil"].between(2003, 2011)].groupby(["mevsim", "yil"])[["Aqua", "Terra"]].sum()
    d = d[d["Terra"] > 0]
    return (d["Aqua"] / d["Terra"]).groupby(level="mevsim").quantile(0.975)


SAYI = ["M_true", "Terra", "Aqua", "V_raw", "V_eff_det", "frp_modis", "frp_viirs_efor"]


def harmonized_tablo(D, birim: str, kume: str, eski_k: pd.Series) -> pd.DataFrame:
    """Bir (birim, küme) varyantı için harmonize seri satırları.
    Düzeyler: tespit -> ay_bolge, ay_TR, yil_TR; olay -> ay_il, ay_TR, yil_TR."""
    T, k, bq = D["T"].copy(), D["kazanan"], D["bq"]
    pred = f"pred_{k}"
    for c in SAYI:
        if c not in T:
            T[c] = np.nan
    son_yil = int(O.h("loyo_test_yillari")[1])
    e0, e1 = O.h("eski_donem_yillari")
    yer = "il" if birim == "olay" else "bolge7"
    satirlar = []
    for duzey, by, lvl in ((f"ay_{'il' if birim == 'olay' else 'bolge'}", ["yil", "ay", yer], "bolge"),
                           ("ay_TR", ["yil", "ay"], "TR")):
        d = T.groupby(by)[SAYI + [pred]].sum(min_count=1).reset_index()
        if yer not in d:
            d[yer] = "TR"
        d["duzey"] = duzey
        has = d["yil"] >= 2012
        lo, hi = seri.bant_uygula(d.loc[has, pred].fillna(0).to_numpy(), bq[lvl])
        d["modis_esdeger"] = pd.array([pd.NA] * len(d), dtype="Int64")
        d.loc[has, "modis_esdeger"] = np.round(d.loc[has, pred].fillna(0)).astype(int).to_numpy()
        d["esdeger_alt"] = pd.array([pd.NA] * len(d), dtype="Int64")
        d["esdeger_ust"] = pd.array([pd.NA] * len(d), dtype="Int64")
        d.loc[has, "esdeger_alt"], d.loc[has, "esdeger_ust"] = lo, hi
        eski = ((d["yil"] < e1) | ((d["yil"] == e1) & (d["ay"] <= 7))) & (d["yil"] >= e0)
        ku = d["ay"].map(O.MEVSIM).map(eski_k)
        mt = d["M_true"].fillna(0)
        d["ana_seri"] = np.where(has, d["modis_esdeger"].fillna(0).astype(int), mt.astype(int))
        d["ana_alt"] = np.where(has, d["esdeger_alt"].fillna(0).astype(int), mt.astype(int))
        d["ana_ust"] = np.where(has, d["esdeger_ust"].fillna(0).astype(int),
                                np.where(eski, np.ceil(mt * (1 + ku)), mt).astype(int))
        satirlar.append(d)
    h = pd.concat(satirlar, ignore_index=True)
    ci = D["sonuc"][k]["yillik_ci95"]
    agg = {c: (c, lambda s: s.sum(min_count=1)) for c in SAYI}
    y = h[h["duzey"] == "ay_TR"].groupby("yil").agg(p=(pred, "sum"), ana_ust_e=("ana_ust", "sum"), **agg).reset_index()
    y["duzey"], y["ay"], y[yer] = "yil_TR", 0, "TR"
    has = y["yil"] >= 2012
    y["modis_esdeger"] = pd.array(np.where(has, np.round(y["p"]), np.nan), dtype="Float64").astype("Int64")
    # tahmin = gerçek*(1+e/100) => gerçek = tahmin/(1+e/100): yıllık LOYO hata yüzdeliklerinden ters bant
    y["esdeger_alt"] = pd.array(np.where(has, np.floor(y["p"] / (1 + ci[1] / 100)), np.nan), dtype="Float64").astype("Int64")
    y["esdeger_ust"] = pd.array(np.where(has, np.ceil(y["p"] / (1 + ci[0] / 100)), np.nan), dtype="Float64").astype("Int64")
    y["ana_seri"] = np.where(has, y["modis_esdeger"].fillna(0), y["M_true"]).astype(int)
    y["ana_alt"] = np.where(has, y["esdeger_alt"].fillna(0), y["M_true"]).astype(int)
    y["ana_ust"] = np.where(has, y["esdeger_ust"].fillna(0), y["ana_ust_e"]).astype(int)
    y = y.rename(columns={"p": pred}).drop(columns="ana_ust_e")
    h = pd.concat([h, y], ignore_index=True)
    eski = ((h["yil"] < e1) | ((h["yil"] == e1) & (h["ay"].between(1, 7)))) & (h["yil"] >= e0)
    eski |= (h["duzey"] == "yil_TR") & h["yil"].between(e0, e1)
    has = h["yil"] >= 2012
    h["ana_kaynak"] = np.where(has, "viirs_modis_esdeger", "modis_gercek")
    h["bayrak"] = np.select([eski, h["yil"] > son_yil], ["eski_donem_yalniz_terra", "kismi_yil_nrt"], "")
    h["etiket"] = np.select([eski, h["yil"] > son_yil, has],
                            ["tahmini (düşük güven)", "tahmini (düşük güven)", "tahmini"], "ölçüldü")
    if birim == "olay":
        h["bolge7"] = np.where(h["il"].eq("TR"), "TR", h["il"].map(O.IL_BOLGE))
    else:
        h["il"] = np.where(h["bolge7"].eq("TR"), "TR", "")
    h = h.rename(columns={"M_true": "modis_gercek", "Terra": "modis_terra", "Aqua": "modis_aqua",
                          "V_raw": "viirs_ham", "V_eff_det": "viirs_uydu_basina",
                          "frp_modis": "frp_modis_mw", "frp_viirs_efor": "frp_viirs_uydu_basina_mw"})
    for c in ("modis_gercek", "modis_terra", "modis_aqua", "viirs_ham", "viirs_uydu_basina"):
        h[c] = pd.array(np.round(h[c].astype(float)), dtype="Float64").astype("Int64")
    h["yontem"] = YONTEM_AD[k] if birim == "tespit" else YONTEM_AD_OLAY[k]
    h["birim"], h["kume"] = birim, kume
    return h[COLS].sort_values(["duzey", "bolge7", "il", "yil", "ay"]).reset_index(drop=True)


COLS = ["birim", "kume", "duzey", "yil", "ay", "bolge7", "il", "ana_seri", "ana_alt", "ana_ust", "ana_kaynak",
        "modis_gercek", "modis_terra", "modis_aqua", "modis_esdeger", "esdeger_alt", "esdeger_ust", "viirs_ham",
        "viirs_uydu_basina", "frp_modis_mw", "frp_viirs_uydu_basina_mw", "bayrak", "etiket", "yontem"]
YONTEM_AD_OLAY = {"i0": "(i0) sabit oran, efor yok (olay)", "i": "(i) sabit oran, eforlu (olay)",
                  "ii": "(ii) bölge × mevsim × VIIRS FRP sınıfı oranı + yalnız-MODIS payı, eforlu (olay)"}


def metrikler(D, es, gv, h) -> dict:
    k = D["kazanan"]
    S = D["sonuc"][k]
    B = seri.BETIK
    j = D["jump"]
    yil = D["years"]
    T = D["T"]
    pred = f"pred_{k}"
    t = T[T["yil"].isin(yil)]
    pooled = float((t[pred].sum() - t["M_true"].sum()) / t["M_true"].sum() * 100)
    mt = t.groupby(["yil", "ay"])[["M_true", pred]].sum()
    mt = mt[mt["M_true"] > 0]
    me = (mt[pred] - mt["M_true"]) / mt["M_true"] * 100
    w = int(O.h("sicrama_pencere_yil"))
    ici = j["jump_null_ci95"][0] <= j["jump_harm_pct"] <= j["jump_null_ci95"][1]
    M = {
        "loyo_method": O.metrik(f"leave-one-year-out ({yil[0]}-{yil[-1]}, {len(yil)} yıl; kazanan {YONTEM_AD[k]})",
                                "", "Doğrulama yöntemi: her yıl dışarıda bırakılıp kalan yıllarla öğrenilir", B),
        "loyo_mape": O.metrik(S["yillik_mape"], "%", "Yıllık ülke toplamı MODIS-eşdeğer tahmininin gerçek MODIS'e (Terra+Aqua) ortalama mutlak yüzde hatası, LOYO", B),
        "loyo_r2": O.metrik(S["yillik_r2"], "", "Yıllık ülke toplamında R² (LOYO, 14 yıl)", B),
        "loyo_bias": O.metrik(S["yillik_bias"], "%", "Yıllık ortalama işaretli yüzde hata (LOYO)", B),
        "loyo_ci95": O.metrik(S["yillik_ci95"], "%", "Yıllık yüzde hataların %2,5-%97,5 yüzdelikleri (14 değer, kaba)", B, "tahmini"),
        "loyo_ay_bolge_wape": O.metrik(S["ay_bolge_wape"], "%", "Ay × 7 bölge düzeyinde ağırlıklı mutlak yüzde hata (seçim ölçütü)", B),
        "loyo_ay_bolge_r2": O.metrik(S["ay_bolge_r2"], "", "Ay × bölge düzeyinde R² (LOYO)", B),
        "harm_kazanan_yontem": O.metrik(YONTEM_AD[k], "", "Ana yöntem: en düşük ay × bölge WAPE (uygulamanın kullanım birimi). (i) uydu-normalize sabit oranla ay × bölgede AYIRT EDİLEMEZ (bkz. harm_ii_eksi_i_wape_ci95); (i) yıllık toplamda daha iyi", B, "tahmini"),
        "jump_raw_pct": O.metrik(j["jump_raw_pct"], "%", f"Ham seri (2012 öncesi MODIS, sonrası MODIS+VIIRS tüm tespitler) geçiş sıçraması: sonraki {w} yıl / önceki {w} yıl ortalaması - 1", B),
        "jump_raw_viirs_only_pct": O.metrik(j["jump_raw_viirs_only_pct"], "%", "Ham seri (2012 sonrası yalnız VIIRS tespitleri) geçiş sıçraması", B),
        "jump_harm_pct": O.metrik(j["jump_harm_pct"], "%", "Harmonize seri (2012 sonrası VIIRS'ten LOYO MODIS-eşdeğer) geçiş sıçraması", B, "tahmini"),
        "jump_modis_gercek_pct": O.metrik(j["jump_modis_gercek_pct"], "%", "Aynı pencerede gerçek MODIS serisinin değişimi (harmonize sıçramanın hedefi)", B),
        "jump_harm_eksi_modis_pct": O.metrik(j["jump_harm_eksi_modis_pct"], "yüzde puan", "Harmonizasyonun eklediği sıçrama = harmonize sıçrama - gerçek MODIS değişimi", B, "tahmini"),
        "jump_resid_pct": O.metrik(j["jump_harm_eksi_modis_pct"], "yüzde puan", "C10 (koordinatör kararı): artık sıçrama = harmonize sıçrama - aynı penceredeki (2009-2011 -> 2012-2014) gerçek MODIS değişimi; loyo_ci95 içinde olmalı", B, "tahmini"),
        "jump_modis_real_pct": O.metrik(j["jump_modis_gercek_pct"], "%", "Aynı pencerede (2009-2011 -> 2012-2014) gerçek MODIS (Terra+Aqua) serisinin değişimi", B),
        "jump_null_ci95": O.metrik(j["jump_null_ci95"], "%", f"Geçiş dışı {j['jump_null_n']} adet 3+3 yıl penceresinde MODIS doğal değişiminin %2,5-%97,5 yüzdelikleri", B, "tahmini"),
        "jump_harm_dogal_aralikta": O.metrik(bool(ici), "", "Harmonize sıçrama doğal değişim %95 aralığında mı (C10 ölçütü; tahmini harmonize değerden türer)", B, "tahmini"),
        "jump_n20_2018_ham_pct": O.metrik(j["viirs_ici"]["2018"]["ham_viirs_pct"], "%", "NOAA-20 eklenişinde ham VIIRS toplamının sıçraması (3+3 yıl)", B),
        "jump_n20_2018_eforlu_pct": O.metrik(j["viirs_ici"]["2018"]["eforlu_viirs_pct"], "%", "NOAA-20 eklenişinde uydu başına (eforlu) VIIRS değişimi", B),
        "jump_n20_2018_modis_pct": O.metrik(j["viirs_ici"]["2018"]["modis_gercek_pct"], "%", "Aynı pencerede gerçek MODIS değişimi", B),
        "jump_n21_2023_ham_pct": O.metrik(j["viirs_ici"]["2023"]["ham_viirs_pct"], "%", "NOAA-21 eklenişinde ham VIIRS sıçraması (2+2 yıl; 2026 kısmi dışarıda)", B),
        "jump_n21_2023_eforlu_pct": O.metrik(j["viirs_ici"]["2023"]["eforlu_viirs_pct"], "%", "NOAA-21 eklenişinde eforlu VIIRS değişimi (2+2 yıl)", B),
        "jump_n21_2023_modis_pct": O.metrik(j["viirs_ici"]["2023"]["modis_gercek_pct"], "%", "Aynı pencerede gerçek MODIS değişimi (2+2 yıl)", B),
        "equiv_overlap_bias": O.metrik(round(pooled, 2), "%", "Çakışma döneminde (2012-2025) VIIRS'ten türetilen MODIS-eşdeğer toplamın gerçek MODIS'e göre sapması, LOYO tahminleri", B, "tahmini"),
        "equiv_overlap_band": O.metrik([round(float(np.percentile(me, 2.5)), 2), round(float(np.percentile(me, 97.5)), 2)],
                                       "%", "Aylık ülke toplamında LOYO yüzde hatasının %2,5-%97,5 yüzdelikleri", B, "tahmini"),
        "equiv_band_kapsama_ay_bolge": O.metrik(D["bq"]["bolge"]["kapsama_loyo"], "oran", "Ay × bölge %95 bandının, bant diğer yıllardan kurulduğunda gerçek MODIS'i kapsama oranı", B),
        "equiv_band_kapsama_ay_tr": O.metrik(D["bq"]["TR"]["kapsama_loyo"], "oran", "Ay × ülke %95 bandının LOYO kapsama oranı", B),
    }
    for kk, s in D["sonuc"].items():
        M[f"harm_{kk}_ay_bolge_wape"] = O.metrik(s["ay_bolge_wape"], "%", f"{YONTEM_AD[kk]}: ay × bölge WAPE (LOYO)", B)
        M[f"harm_{kk}_yillik_mape"] = O.metrik(s["yillik_mape"], "%", f"{YONTEM_AD[kk]}: yıllık MAPE (LOYO)", B)
        M[f"harm_{kk}_yillik_r2"] = O.metrik(s["yillik_r2"], "", f"{YONTEM_AD[kk]}: yıllık R² (LOYO)", B)
    f = D["frp50"]
    for key, ad in (("genel", "genel"), ("dn=D", "gunduz"), ("dn=N", "gece")):
        if f.get(key):
            M[f"modis_frp50_{ad}_mw"] = O.metrik(f[key]["frp50_mw"], "MW", f"Aqua'nın bir VIIRS hücresini %50 olasılıkla gördüğü hücre toplam FRP'si ({ad}; eşzamanlı geçişler, şerit vekilli, etkin sınır)", B, "tahmini")
    E = eslestirme.BETIK
    M["mcell_viirs_modis_izinde"] = O.metrik(es["viirs_modis_izinde"], "nokta", "MODIS ayak izine bağlanan VIIRS noktası", E)
    M["mcell_viirs_toplam"] = O.metrik(es["viirs_nokta_cakisma"], "nokta", "Toplam VIIRS noktası", E)
    M["mcell_viirs_coklu_iz"] = O.metrik(es["viirs_coklu_iz_aday"], "nokta", "Birden çok (kenar/üst üste binen) MODIS izine düşen VIIRS noktası; kural ile teke indirildi", E)
    M["mcell_iz_basina_viirs"] = O.metrik(round(es["modis_izi_basina_viirs_ort"], 3), "nokta", "VIIRS içeren MODIS izi başına ortalama VIIRS noktası ('1 MODIS 4 VIIRS' sorunu)", E)
    M["mcell_iz_basina_izgara"] = O.metrik(round(es["modis_izi_basina_izgara_hucre_ort"], 3), "hücre", "Aynı MODIS izi içindeki VIIRS noktalarının sabit 0,01° ızgarada dağıldığı ortalama hücre sayısı", E)
    M["mcell_izgarada_bolunen_oran"] = O.metrik(round(es["modis_izi_birden_cok_izgaraya_bolunen_oran"], 4), "oran", "Sabit ızgara kullanılsaydı birden çok hücreye bölünecek MODIS izi oranı", E)
    G = guven_esleme.BETIK
    M["guven_cift_sayisi"] = O.metrik(gv["n_cift"], "çift", "Aqua-VIIRS eşzamanlı güven çifti", G)
    M["guven_ogrenilen_sinirlar"] = O.metrik([gv["c1"], gv["c2"]], "MODIS %", "Öğrenilmiş MODIS sınırları: düşük <= c1 < nominal <= c2 < yüksek", G, "tahmini")
    M["guven_loyo_c1_aralik"] = O.metrik(gv["loyo_c1_aralik"], "MODIS %", "Yıl dışarıda bırakmada c1 aralığı", G)
    M["guven_loyo_c2_aralik"] = O.metrik(gv["loyo_c2_aralik"], "MODIS %", "Yıl dışarıda bırakmada c2 aralığı", G)
    M["guven_loyo_kappa_ogrenilen"] = O.metrik(gv["loyo_kappa_ogr_ort"], "", "Dışarıda bırakılan yılda öğrenilmiş sınıfla VIIRS sınıfı uyumu (Cohen kappa ort.)", G)
    M["guven_loyo_kappa_firms"] = O.metrik(gv["loyo_kappa_firms_ort"], "", "Aynı sınamada FIRMS sınıfı (0-29/30-79/80-100) kappa ort.", G)
    M["guven_spearman"] = O.metrik(gv["spearman_modis_viirs"], "", "Tespit düzeyinde MODIS yüzdesi ile VIIRS sınıfı sıra ilişkisi", G)
    for r in gv["kosullu_modis_yuzdesi"]:
        M[f"guven_viirs_{r['v_cls']}_modis_medyan"] = O.metrik(r[0.5], "MODIS %", f"VIIRS '{r['v_cls']}' iken aynı yangında MODIS güveninin medyanı (çeyrekler {r[0.25]}-{r[0.75]})", G)
    M["harmonize_seri_satir"] = O.metrik(int(len(h)), "satır", "harmonized.parquet satır sayısı", "src/harmonize/run_all.py")
    for kk, s in D["sonuc"].items():
        M[f"harm_{kk}_yillik_bias"] = O.metrik(s["yillik_bias"], "%", f"{YONTEM_AD[kk]}: yıllık ortalama işaretli hata (LOYO)", B)
        M[f"harm_{kk}_yillik_ci95"] = O.metrik(s["yillik_ci95"], "%", f"{YONTEM_AD[kk]}: yıllık hata %95 aralığı (LOYO)", B, "tahmini")
        M[f"harm_{kk}_jump_resid_pct"] = O.metrik(D["jump_yontem"][kk]["jump_resid_pct"], "yüzde puan", f"{YONTEM_AD[kk]}: C10 artık sıçrama", B, "tahmini")
    lo, hi, fark = wape_bootstrap(D["T"], D["years"], "pred_ii", "pred_i")
    M["harm_ii_eksi_i_wape"] = O.metrik(fark, "yüzde puan", "Ay × bölge WAPE farkı (ii) - (i), LOYO", B)
    M["harm_ii_eksi_i_wape_ci95"] = O.metrik([lo, hi], "yüzde puan", "Aynı farkın yıl bootstrap'ı (2000 tekrar) %95 aralığı; 0'ı içeriyorsa ayırt edilemez", B, "tahmini")
    return M


def wape_bootstrap(T, years, a, b, n=2000):
    """Yıl düzeyinde yeniden örnekleme ile ay × bölge WAPE farkı (a - b) %95 aralığı."""
    t = T[T["yil"].isin(years)].groupby(["yil", "ay", "bolge7"])[["M_true", a, b]].sum().reset_index()
    g = t.assign(ea=(t[a] - t["M_true"]).abs(), eb=(t[b] - t["M_true"]).abs()).groupby("yil")[["ea", "eb", "M_true"]].sum()
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(g), size=(n, len(g)))
    E, F, M_ = g["ea"].to_numpy()[idx].sum(1), g["eb"].to_numpy()[idx].sum(1), g["M_true"].to_numpy()[idx].sum(1)
    d = (E - F) / M_ * 100
    fark = (g["ea"].sum() - g["eb"].sum()) / g["M_true"].sum() * 100
    return round(float(np.percentile(d, 2.5)), 2), round(float(np.percentile(d, 97.5)), 2), round(float(fark), 2)


def olay_tespit_tutarliligi(h: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """F2-01: Olay eşdeğeri (en az bir MODIS tespiti içeren olay) tanım gereği tespit eşdeğerini
    aşamaz. 2012+ eşdeğer satırlarında: (1) il toplamı bölgenin tespit eşdeğerini aşarsa il
    değerleri orantılı ve en büyük kalan yöntemiyle tamsayı olarak tespit değerine indirilir;
    (2) ay_TR ve yil_TR olay değerleri min(olay, tespit) ile kırpılır. Kırpılan satırlar
    `bayrak` içinde 'olay_tespitle_kirpildi' taşır; sayıları metrik olarak raporlanır."""
    h = h.copy()
    say = {}
    ek = "olay_tespitle_kirpildi"

    def bayrak_ekle(mask):
        h.loc[mask, "bayrak"] = np.where(h.loc[mask, "bayrak"].eq(""), ek, h.loc[mask, "bayrak"] + ";" + ek)

    for kume in h["kume"].unique():
        k_ = h["kume"].eq(kume) & h["yil"].ge(2012)
        tb = h[k_ & h["birim"].eq("tespit") & h["duzey"].eq("ay_bolge")].set_index(["yil", "ay", "bolge7"])["ana_seri"]
        oi = h[k_ & h["birim"].eq("olay") & h["duzey"].eq("ay_il")]
        top = oi.groupby(["yil", "ay", "bolge7"])["ana_seri"].sum()
        hedef = tb.reindex(top.index).fillna(0).astype(int)
        asan = top[top > hedef].index
        say[f"{kume}_ay_bolge"] = int(len(asan))
        for key in asan:
            rows = oi[(oi["yil"] == key[0]) & (oi["ay"] == key[1]) & (oi["bolge7"] == key[2])]
            v = rows["ana_seri"].to_numpy().astype(float)
            T_ = int(hedef[key])
            x = v * T_ / v.sum()
            fl = np.floor(x).astype(int)
            r = T_ - fl.sum()
            fl[np.argsort(-(x - fl))[:r]] += 1
            h.loc[rows.index, "ana_seri"] = fl
            h.loc[rows.index, "modis_esdeger"] = fl
            bayrak_ekle(h.index.isin(rows.index))
        for duzey in ("ay_TR", "yil_TR"):
            tt = h[k_ & h["birim"].eq("tespit") & h["duzey"].eq(duzey)].set_index(["yil", "ay"])["ana_seri"]
            oo = h[k_ & h["birim"].eq("olay") & h["duzey"].eq(duzey)]
            lim = tt.reindex(pd.MultiIndex.from_frame(oo[["yil", "ay"]])).to_numpy()
            m = oo["ana_seri"].to_numpy() > lim
            idx = oo.index[m]
            say[f"{kume}_{duzey}"] = int(m.sum())
            h.loc[idx, "ana_seri"] = lim[m].astype(int)
            h.loc[idx, "modis_esdeger"] = lim[m].astype(int)
            bayrak_ekle(h.index.isin(idx))
    o = h["birim"].eq("olay") & h["yil"].ge(2012)
    h.loc[o, "ana_alt"] = np.minimum(h.loc[o, "ana_alt"], h.loc[o, "ana_seri"])
    h.loc[o, "esdeger_alt"] = h.loc[o, "esdeger_alt"].clip(upper=h.loc[o, "ana_seri"])
    return h, say


def yorunge_ve_ciftler(D) -> pd.DataFrame:
    """F2-04: yıllık gündüz geçiş saati medyanı (UTC) ve Aqua-VIIRS eşzamanlı çift payı."""
    p = D["p"]
    g = p[p["dn"].eq("D")]
    hr = (g["t_utc"].dt.hour + g["t_utc"].dt.minute / 60).groupby([g["yil"], g["sat"]]).median().unstack()
    pr = pd.read_parquet(O.INTERIM / "pairs.parquet", columns=["m_pid", "m_sat", "esz"])
    pr = pr[pr["m_sat"].eq("Aqua")]
    pay = pr.groupby(pr["m_pid"] // 10**7)["esz"].mean().rename("aqua_viirs_esz_cift_payi")
    return hr.round(2).join(pay.round(3), how="left")


def belge_doldur(M: dict, D, gv) -> None:
    """docs/harmonizasyon_yontemi.md içindeki OTOMATIK bloğunu metriklerden doldurur (K1)."""
    doc = O.ROOT / "docs" / "harmonizasyon_yontemi.md"
    t = doc.read_text(encoding="utf-8")
    a, b = "<!-- OTOMATIK:BASLA -->", "<!-- OTOMATIK:BITIR -->"

    def v(k):
        return M[k]["value"]

    L = [a, f"_Üretildi: {time.strftime('%Y-%m-%d %H:%M')} — `src/harmonize/run_all.py`; değerler `reports/metrics.json` ile aynıdır._", ""]
    L += ["**Yöntem yarışı (LOYO 2012–2025, hedef Terra+Aqua tespit):**", "",
          "| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Yıllık sapma % | Yıllık %95 hata aralığı |",
          "|---|---|---|---|---|---|"]
    for k, s in D["sonuc"].items():
        L.append(f"| {YONTEM_AD[k]} | {s['ay_bolge_wape']} | {s['yillik_mape']} | {s['yillik_r2']} | {s['yillik_bias']} | {s['yillik_ci95']} |")
    L += ["", f"Ana yöntem (en düşük ay × bölge WAPE): **{v('harm_kazanan_yontem')}**. **Dürüst okuma:** (ii) ile uydu-normalize "
          f"sabit oran (i) ay × bölgede ayırt edilemez (WAPE {v('harm_ii_ay_bolge_wape')} vs {v('harm_i_ay_bolge_wape')}; yıl bootstrap'ıyla "
          f"(ii)−(i) farkı %95 aralığı {v('harm_ii_eksi_i_wape_ci95')} puan); (i) yıllık toplamda daha iyi (MAPE {v('harm_i_yillik_mape')} vs "
          f"{v('harm_ii_yillik_mape')}; %95 {v('harm_i_yillik_ci95')} vs {v('harm_ii_yillik_ci95')}); ikisi de normalize edilmemiş tek orandan (i0) çok "
          f"iyi (WAPE {v('harm_i0_ay_bolge_wape')}). (ii) uygulamanın kullanım birimi ay × bölge olduğu için ana yöntem bırakıldı "
          f"(koordinatör kararı); bu bir üstünlük iddiası değildir. Ölçüt belgede sonuçlardan önce yazıldı ama git kaydı olmadığından "
          f"bu doğrulanamaz; kazananın hatası seçim etkisiyle hafif iyimser olabilir. C10 artığı (i) ile: {v('harm_i_jump_resid_pct')} yp.", "",
          f"**Eşdeğer seri (C11):** çakışma toplam sapması `equiv_overlap_bias` = {v('equiv_overlap_bias')} %; aylık ülke hata bandı `equiv_overlap_band` = {v('equiv_overlap_band')} %; bant kapsaması (LOYO) ay×bölge {v('equiv_band_kapsama_ay_bolge')}, ay×ülke {v('equiv_band_kapsama_ay_tr')}.", "",
          "**Sıçrama (C10), geçiş 2012, 3+3 yıl:**", "",
          "| Seri | Sıçrama % |", "|---|---|",
          f"| Ham (MODIS → MODIS+VIIRS tüm tespit) | {v('jump_raw_pct')} |",
          f"| Ham (MODIS → yalnız VIIRS) | {v('jump_raw_viirs_only_pct')} |",
          f"| Harmonize (LOYO MODIS-eşdeğer) | {v('jump_harm_pct')} |",
          f"| Gerçek MODIS (aynı pencere) | {v('jump_modis_gercek_pct')} |",
          f"| Harmonizasyonun eklediği (harmonize − gerçek MODIS) | {v('jump_harm_eksi_modis_pct')} yüzde puan |",
          "", f"Doğal değişim %95 aralığı (`jump_null_ci95`, {D['jump']['jump_null_n']} pencere): {v('jump_null_ci95')}. "
          f"Harmonize sıçrama bu aralıkta mı: **{'EVET' if v('jump_harm_dogal_aralikta') else 'HAYIR'}**."]
    if not v("jump_harm_dogal_aralikta"):
        L.append("Eski C10 ölçütü (bilgi amaçlı) **sağlanmıyor**: 2009–2011 MODIS'in kendi kayıtlarında olağan dışı yüksek "
                 "yıllardır; gerçek MODIS de aynı pencerede doğal aralığın dışına düşüyor.")
    ici2 = v("loyo_ci95")[0] <= v("jump_resid_pct") <= v("loyo_ci95")[1]
    L += ["", "**C10 ANA ölçütü (koordinatör kararı):** artık sıçrama `jump_resid_pct` = harmonize sıçrama − aynı "
          "penceredeki gerçek MODIS değişimi (`jump_modis_real_pct`); yıllık LOYO %95 hata aralığı `loyo_ci95` içinde "
          "olmalı. Ana varyant: **birim = tespit, küme = temiz**.",
          f"Değer: {v('jump_resid_pct')} yüzde puan; aralık {v('loyo_ci95')} → **{'SAĞLANIYOR' if ici2 else 'SAĞLANMIYOR'}**.",
          "", "**Varyantlar (bilgi; aynı LOYO ve sıçrama tanımı):**", "",
          "| Birim | Küme | Kazanan | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | loyo_ci95 | Ham sıçrama % | Harmonize % | Gerçek MODIS % | Artık (yp) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in VARYANT_OZET:
        L.append("| " + " | ".join(str(r[c]) for c in ("birim", "kume", "kazanan", "ay_bolge_wape", "yillik_mape", "yillik_r2",
                                                          "yillik_ci95", "jump_raw_pct", "jump_harm_pct", "jump_modis_gercek_pct",
                                                          "jump_resid_pct")) + " |")
    if YORUNGE:
        y = YORUNGE[0]
        L += ["", "**Yörünge kayması ve eşzamanlı çift payı (F2-04):** gündüz geçiş saati medyanı (UTC) ve Aqua-VIIRS aday "
              "çiftlerinde |Δt| ≤ kalibrasyon penceresi payı. Aqua'nın geç kayması kalibrasyon çiftlerini azaltır; "
              f"2026 değerleri düşük güven bayraklıdır (`kismi_yil_nrt;aqua_yorunge_kaymasi`). 2026 bant kapsaması: {v('harm_2026_bant_kapsama')}.", "",
              "| Yıl | Terra | Aqua | SNPP | N20 | N21 | Aqua-VIIRS eşzamanlı çift payı |", "|---|---|---|---|---|---|---|"]
        for yy, r in y.iterrows():
            L.append(f"| {yy} | " + " | ".join("" if pd.isna(r.get(c)) else str(r.get(c)) for c in ("Terra", "Aqua", "SNPP", "N20", "N21", "aqua_viirs_esz_cift_payi")) + " |")
    L += ["", "**Olay/tespit tutarlılığı (F2-01):** olay eşdeğeri tespit eşdeğerini aşamaz; aşan hücreler kırpıldı: "
          + ", ".join(f"{k.replace('olay_tespitle_kirpilan_', '')} {M[k]['value']}" for k in M if k.startswith("olay_tespitle_kirpilan_")) + "."]
    L += ["", "**VIIRS içi uydu eklenişleri (efor normalizasyonunun etkisi):**", "",
          "| Geçiş | Ham VIIRS % | Eforlu VIIRS % | Gerçek MODIS % |", "|---|---|---|---|",
          f"| NOAA-20 2018 (3+3) | {v('jump_n20_2018_ham_pct')} | {v('jump_n20_2018_eforlu_pct')} | {v('jump_n20_2018_modis_pct')} |",
          f"| NOAA-21 2023 (2+2) | {v('jump_n21_2023_ham_pct')} | {v('jump_n21_2023_eforlu_pct')} | {v('jump_n21_2023_modis_pct')} |",
          "", "**Güven eşlemesi (S1):**", "",
          f"- Çift sayısı {gv['n_cift']}; VIIRS payları {gv['pay']}.",
          f"- Öğrenilmiş MODIS sınırları: düşük 0–{gv['c1']}, nominal {gv['c1'] + 1}–{gv['c2']}, yüksek {gv['c2'] + 1}–100 (FIRMS: 0–{gv['firms_sinirlari'][0]} / –{gv['firms_sinirlari'][1]} / –100).",
          f"- LOYO kararlılığı: c1 {gv['loyo_c1_aralik']}, c2 {gv['loyo_c2_aralik']} ({gv['loyo_yil_sayisi']} yıl).",
          f"- Bağımsız sınama: doğru sınıf oranı öğrenilmiş {gv['loyo_uyum_ogr_ort']} / FIRMS {gv['loyo_uyum_firms_ort']}; kappa {gv['loyo_kappa_ogr_ort']} / {gv['loyo_kappa_firms_ort']}; öğrenilmiş daha iyi olduğu yıl {gv['loyo_ogr_daha_iyi_yil']}/{gv['loyo_yil_sayisi']}.",
          f"- Sıra ilişkisi (Spearman): en yüksek sınıf kuralı {gv['spearman_modis_viirs']}, en büyük FRP kuralı {gv['spearman_alternatif_maxfrp_kurali']}.",
          f"- Gündüz/gece ayrı: {gv['gunduz_gece_ayri']}.", "",
          "| VIIRS sınıfı | n | MODIS %5 | %25 | medyan | %75 | %95 |", "|---|---|---|---|---|---|---|"]
    for r in gv["kosullu_modis_yuzdesi"]:
        L.append(f"| {r['v_cls']} | {r['n']} | {r[0.05]} | {r[0.25]} | {r[0.5]} | {r[0.75]} | {r[0.95]} |")
    L += ["", "**MODIS (Aqua) etkin tespit sınırı FRP50 (tahmini):**", "",
          "| Tabaka | FRP50 MW | eğim | hücre | tespit oranı |", "|---|---|---|---|---|"]
    for k, s in D["frp50"].items():
        L.append(f"| {k} | " + (f"{s['frp50_mw']} | {s['egim']} | {s['n_hucre']} | {s['tespit_orani']}" if s else "yetersiz örnek | | |") + " |")
    L += ["", f"**Eşleştirme birimi:** VIIRS noktası {v('mcell_viirs_toplam')}, MODIS izinde {v('mcell_viirs_modis_izinde')}, "
          f"çoklu ize düşen (kural ile teke) {v('mcell_viirs_coklu_iz')}; iz başına VIIRS {v('mcell_iz_basina_viirs')}, "
          f"aynı iz sabit ızgarada {v('mcell_iz_basina_izgara')} hücreye dağılırdı (bölünen iz oranı {v('mcell_izgarada_bolunen_oran')}).", b]
    i, j = t.index(a), t.index(b) + len(b)
    doc.write_text(t[:i] + "\n".join(L) + t[j:], encoding="utf-8")


VARYANT_OZET: list[dict] = []
YORUNGE: list = []


def varyant_ozet(birim, kume, D) -> dict:
    S, j = D["sonuc"][D["kazanan"]], D["jump"]
    return {"birim": birim, "kume": kume, "kazanan": D["kazanan"], "ay_bolge_wape": S["ay_bolge_wape"],
            "yillik_mape": S["yillik_mape"], "yillik_r2": S["yillik_r2"], "yillik_ci95": S["yillik_ci95"],
            "ay_il_wape": S.get("ay_il_wape"), "jump_raw_pct": j["jump_raw_pct"], "jump_harm_pct": j["jump_harm_pct"],
            "jump_modis_gercek_pct": j["jump_modis_gercek_pct"], "jump_resid_pct": j["jump_resid_pct"],
            "yontemler": {k: {a: s[a] for a in ("ay_bolge_wape", "yillik_mape", "yillik_r2") if a in s} | (
                {"ay_il_wape": s["ay_il_wape"]} if "ay_il_wape" in s else {}) for k, s in D["sonuc"].items()}}


def varyant_metrikleri(M: dict, ozet: dict) -> None:
    on = f"{ozet['birim']}_{ozet['kume']}"
    B = olay.BETIK if ozet["birim"] == "olay" else seri.BETIK
    ad = f"(birim={ozet['birim']}, küme={ozet['kume']})"
    M[f"{on}_kazanan"] = O.metrik(ozet["kazanan"], "", f"{ad} en düşük ay × bölge WAPE ile seçilen yöntem", B, "tahmini")
    for key, unit, t in (("yillik_mape", "%", "yıllık MAPE (LOYO)"), ("yillik_r2", "", "yıllık R² (LOYO)"),
                         ("ay_bolge_wape", "%", "ay × bölge WAPE (LOYO)"), ("ay_il_wape", "%", "ay × il WAPE (LOYO)"),
                         ("yillik_ci95", "%", "yıllık LOYO hata %95 aralığı"),
                         ("jump_raw_pct", "%", "ham sıçrama 2012"), ("jump_harm_pct", "%", "harmonize sıçrama 2012"),
                         ("jump_modis_gercek_pct", "%", "gerçek MODIS değişimi 2012"),
                         ("jump_resid_pct", "yüzde puan", "artık sıçrama (harmonize - gerçek MODIS)")):
        if ozet.get(key) is not None:
            M[f"{on}_{key}"] = O.metrik(ozet[key], unit, f"{ad} {t}", B, "tahmini" if key in ("yillik_ci95", "jump_harm_pct", "jump_resid_pct") else "ölçüldü")


def main():
    t0 = time.time()
    es = eslestirme.main()
    gv = guven_esleme.main()
    cfg_tab = O.cfg.load()["harmonizasyon"]["ogrenilen_guven_esleme"]
    cuts = [s["max"] for s in cfg_tab["MODIS"]["siniflar"]][:2] if cfg_tab else None
    if cuts != [gv["c1"], gv["c2"]]:
        print(f"UYARI: esikler.json ogrenilen_guven_esleme {cuts} != hesaplanan {[gv['c1'], gv['c2']]} -> config'i güncelle")
    VARYANT_OZET.clear()
    tablolar, olcum = [], {}
    D = None
    for kume in ("temiz", "temiz_aniz"):
        Dk = seri.main(kume)
        if kume == "temiz":
            D = Dk            # ANA varyant: tespit, temiz
        tablolar.append(harmonized_tablo(Dk, "tespit", kume, eski_donem_ust(Dk["T"])))
        VARYANT_OZET.append(varyant_ozet("tespit", kume, Dk))
        olcum[f"tespit_{kume}"] = {"sonuc": Dk["sonuc"], "jump": Dk["jump"], "frp50": Dk["frp50"], "bant": Dk["bq"],
                                   "kazanan": Dk["kazanan"]}
        Ek = olay.main(kume)
        tablolar.append(harmonized_tablo(Ek, "olay", kume, Ek["eski_k"]))
        VARYANT_OZET.append(varyant_ozet("olay", kume, Ek))
        olcum[f"olay_{kume}"] = {"sonuc": Ek["sonuc"], "jump": Ek["jump"], "bant": Ek["bq"], "kazanan": Ek["kazanan"],
                                 "eski_k": Ek["eski_k"].to_dict()}
    h = pd.concat(tablolar, ignore_index=True)
    h, kirp = olay_tespit_tutarliligi(h)
    son_yil = int(O.h("loyo_test_yillari")[1])
    m26 = h["yil"].gt(son_yil) & h["ana_kaynak"].eq("viirs_modis_esdeger")
    h.loc[m26, "bayrak"] = h.loc[m26, "bayrak"].str.replace("kismi_yil_nrt", "kismi_yil_nrt;aqua_yorunge_kaymasi", regex=False)
    h.loc[m26, "etiket"] = "tahmini (düşük güven)"
    yor = yorunge_ve_ciftler(D)
    O.AGG.mkdir(parents=True, exist_ok=True)
    h.to_parquet(O.OUT_HARM, index=False)
    M = metrikler(D, es, gv, h)
    for oz in VARYANT_OZET:
        varyant_metrikleri(M, oz)
    for key, n in kirp.items():
        M[f"olay_tespitle_kirpilan_{key}"] = O.metrik(n, "hücre", f"Olay eşdeğeri tespit eşdeğerini aştığı için kırpılan hücre ({key}, 2012+)", "src/harmonize/run_all.py")
    t26 = h[h["birim"].eq("tespit") & h["kume"].eq("temiz") & h["duzey"].eq("ay_TR") & m26]
    M["harm_2026_bant_kapsama"] = O.metrik(round(float(((t26["modis_gercek"] >= t26["ana_alt"]) & (t26["modis_gercek"] <= t26["ana_ust"])).mean()), 3),
                                           "oran", f"2026 (eğitim dışı, NRT, Aqua kayması) ay × ülke bandının gerçek MODIS'i kapsama oranı ({len(t26)} ay)", "src/harmonize/run_all.py")
    for y in (2015, 2025, int(yor.index.max())):
        if y in yor.index:
            M[f"aqua_gunduz_gecis_utc_{y}"] = O.metrik(float(yor.loc[y, "Aqua"]), "saat (UTC)", f"Aqua gündüz tespitlerinin medyan geçiş saati, {y}", "src/harmonize/run_all.py")
            M[f"aqua_viirs_esz_cift_payi_{y}"] = O.metrik(float(yor.loc[y, "aqua_viirs_esz_cift_payi"]), "oran", f"Aqua-VIIRS aday çiftlerinden |Δt| <= kalibrasyon penceresi olanların payı, {y}", "src/harmonize/run_all.py")
    YORUNGE.clear()
    YORUNGE.append(yor)
    M["c10_ana_varyant"] = O.metrik("jump_resid_pct (birim=tespit, küme=temiz) loyo_ci95 içinde", "",
                                    "C10 ana ölçütü (koordinatör kararı); diğer varyantlar bilgi amaçlı", "src/harmonize/run_all.py")
    M["harm_sure_sn"] = O.metrik(round(time.time() - t0, 1), "s", "run_all toplam süresi (bu makine)", "src/harmonize/run_all.py")
    M["guven_config_uyumlu"] = O.metrik(cuts == [gv["c1"], gv["c2"]], "", "esikler.json'daki öğrenilmiş sınırlar yeniden hesaplananla aynı mı", "src/harmonize/run_all.py")
    O.json_yaz(O.PART, {"metrics": M, "sensitivity": {}})
    belge_doldur(M, D, gv)
    O.json_yaz(O.INTERIM / "seri_olcum.json", olcum)
    print(f"harmonized.parquet {len(h)} satır; süre {time.time() - t0:.1f} s")
    for oz in VARYANT_OZET:
        print({k: v for k, v in oz.items() if k != "yontemler"})
    return M


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
