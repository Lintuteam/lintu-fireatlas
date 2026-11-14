"""Takvim-analiz hattını baştan sona çalıştırır ve metrics_parts/takvim_analiz.json yazar (K1).

Basitçe: Girdiler (olaylar, durumlar, kapsam, harmonize seri) değişince tek komutla her tabloyu
yeniden üretir; ekrana/rapora giden her sayı buradan, hesaplanarak çıkar. Elle yazılmış sayı yoktur.

Kullanım: python src/analytics/run_all.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analiz  # noqa: E402
import build_daily  # noqa: E402
import build_monthly  # noqa: E402
import common as C  # noqa: E402
import query  # noqa: E402
from veri import Veri  # noqa: E402

BETIK = "src/analytics/run_all.py"


def _m(value, unit, tanim, etiket="ölçüldü", betik=BETIK):
    return {"value": value, "unit": unit, "tanim": tanim, "betik": betik,
            "veri_surumu": C.VERI_SURUMU, "etiket": etiket}


def etiket_seri(seri: str) -> str:
    """F2-05 tek kural: harmonize/uydu-başına/olay-eşdeğer türevi = tahmini; ham sensör sayımı = ölçüldü.
    Her metrik etiketi bu fonksiyondan gelir; aynı büyüklük iki etiket taşımaz."""
    return "tahmini" if (C.is_esdeger(seri) or seri.endswith("_ub") or seri.startswith("olay")) else "ölçüldü"


def main() -> int:
    t0 = time.time()
    r = {"daily": build_daily.build()}
    v = Veri.yukle()
    r["monthly"] = build_monthly.build(v)
    r["analiz"] = analiz.run()
    cm = query.mevcut_ay_tablosu(v)
    cm.to_parquet(C.MEVCUT, index=False)
    P = pd.read_parquet(C.PROFIL)
    A = pd.read_parquet(C.ANOMALI)
    HT = pd.read_parquet(C.HAM_TEMIZ)
    M = pd.read_parquet(C.MONTHLY)
    met = {}

    def top3(seri, unit="TR"):
        s = P[(P.birim == unit) & (P.seri == seri) & (P["top"])].sort_values("sira")
        return [int(a) for a in s["ay"]]
    for seri in ("modis_esdeger", "modis_ham", "modis_temiz", "viirs_ham_ub", "viirs_temiz_ub", "olay"):
        s = P[(P.birim == "TR") & (P.seri == seri)]
        if s.empty:
            continue
        sira = ("(sıra: ay payı medyanı)" if seri in C.SIRALAMA_PAY else "(sıra: medyan)")
        met[f"takvim_top3_ay_{seri}_TR"] = _m(
            top3(seri), "ay no", f"TR için en yoğun 3 takvim ayı (tarihsel hotspot aktivitesi), {seri} {sira}",
            etiket_seri(seri))
        met[f"takvim_ayirt_edilemez_{seri}_TR"] = _m(
            int(s[s["top"]]["ayirt_edilemez"].any()), "0/1",
            f"TR {seri}: en yoğun 3 ay içinde göreli fark < tol olan komşu çift var mı (1 = ayırt edilemez)",
            etiket_seri(seri))
        met[f"takvim_n_normal_yil_{seri}"] = _m(int(s["n_yil"].max()), "yıl",
                                                f"{seri} ay medyanında kullanılan tam, sensör-tutarlı yıl sayısı", etiket_seri(seri))
    ht = HT[HT.birim.isin(v.ils)]
    met["takvim_ham_temiz_top3_degisen_il_payi"] = _m(
        round(float(ht["siralama_degisti"].mean() * 100), 1), "%",
        "İl × sensör birimlerinde ham ve temiz (anız hariç) en yoğun 3 ayın sırası/üyeliği değişen pay (VIIRS kısmı uydu başına, tahmini)", "tahmini")
    tr = HT[HT.birim == "TR"].set_index("sensor")
    for sn in tr.index:
        met[f"takvim_ham_temiz_TR_{sn}"] = _m(f"ham {tr.loc[sn,'top3_ham']} -> temiz {tr.loc[sn,'top3_temiz']}", "ay no",
                                              f"TR {sn}: ham ve temiz en yoğun 3 ay", "ölçüldü" if sn == "modis" else "tahmini")
    an = A[A.seri == "modis_esdeger"]
    ok = an[an["isaret"] != "yetersiz_veri"]
    met["takvim_anomali_isaret_orani_esdeger"] = _m(
        round(float(ok["isaret"].str.startswith(("yuksek", "dusuk")).mean() * 100), 2), "%",
        "Eşdeğer seri, yıl dışarıda bırakmalı normale göre |z| ≥ eşik olan hücre payı (LOYO; K4)", "tahmini")
    met["takvim_anomali_belirsiz_bant_payi_esdeger"] = _m(
        round(float(ok["isaret"].str.contains("belirsiz_bant").mean() * 100), 2), "%",
        "Anomali işareti harmonizasyon belirsizlik bandında değişen hücre payı", "tahmini")
    mc = cm[(cm.birim == "TR") & (cm.hedef == "mevcut")].set_index("seri")
    for s_ in ("modis_temiz", "viirs_temiz_ub"):
        if s_ not in mc.index:
            continue
        x = mc.loc[s_]
        met[f"takvim_mevcut_ay_oran_{s_}_TR"] = _m(
            None if not np.isfinite(x["oran"]) else round(float(x["oran"]), 3), "kat",
            f"{x['bas']}..{x['bit']} ({x['gun']} gün, KISMİ AY) / geçmiş yılların aynı günlerinin medyanı, {s_}, TR",
            "tahmini")
    if "modis_temiz" in mc.index:
        x = mc.loc["modis_temiz"]
        met["takvim_mevcut_ay_kismi_gun_TR"] = _m(int(x["kismi_ay_gun"]) if np.isfinite(x["kismi_ay_gun"]) else 0, "gün",
                                                  "Mevcut ayın karşılaştırmaya giren gün sayısı (kısmi ay)")
        met["takvim_mevcut_ay_nrt_payi_TR"] = _m(round(float(x["nrt_payi"]) * 100, 1), "%",
                                                 "Mevcut ayda TR tespitlerinin NRT (hızlı) üründen gelen payı")
        met["takvim_mevcut_ay_aqua_yorunge_kaymasi"] = _m(
            int(bool(x["aqua_yorunge_kaymasi"])), "0/1",
            "Mevcut ay harmonizasyon bayrağında Aqua yörünge kayması var mı", "tahmini")
        met["takvim_mevcut_ay_ayrisma_yorum_TR"] = _m(
            str(x["ayrisma_yorum"]), "",
            "MODIS ve VIIRS oranı yan yana: düşüş iki sensörde mi (hava/gerçek) yoksa yalnız MODIS'te mi (sensör şüphesi)",
            "doğrulanmadı")
    met["takvim_kesintili_ay_hucresi"] = _m(
        int(((M.birim == "TR") & (M.modis_ham_kk.notna()) & (M.kesinti_pay_modis > 0)).sum()), "hücre",
        "TR için MODIS tarafında kesinti günü düzeltmesi uygulanan ay sayısı")
    met["takvim_bos_hucre_kismi_ay"] = _m(
        int(((M.birim == "TR") & M.modis_ham_kk.isna() & M.modis_ham.notna()).sum()), "hücre",
        "TR: ham sayısı var ama kısmi/kesinti-çok olduğundan düzeltmeli değeri BOŞ bırakılan MODIS ay hücresi")
    sl = pd.read_parquet(C.SERI_AYLIK)
    kirp = sl[sl["harm_bayrak"].str.contains("olay_tespitle_kirpildi")]
    met["takvim_olay_tespitle_kirpildi_hucre"] = _m(
        int(len(kirp)), "hücre",
        "Eşdeğer seride olay_tespitle_kirpildi bayrağı taşıyan ay hücresi (uyarılı)", "tahmini")
    for seri_ in ("modis_esdeger", "olay_esdeger"):
        x = cm[(cm.birim == "TR") & (cm.hedef == "son_tam_ay") & (cm.seri == seri_)]
        if len(x):
            x = x.iloc[0]
            met[f"takvim_son_tam_ay_oran_{seri_}_TR"] = _m(round(float(x["oran"]), 3), "kat",
                                                          f"{x['bas']}..{x['bit']} {seri_} / aynı ayın tarihsel medyanı", "tahmini")
            met[f"takvim_son_tam_ay_guvenilmez_{seri_}_TR"] = _m(
                int(bool(x["esdeger_guvenilmez"])), "0/1",
                "Eşdeğer oran iki ölçülmüş orandan (MODIS temiz, VIIRS uydu başına) eşikten fazla sapıyor mu", "doğrulanmadı")
            met[f"takvim_son_tam_ay_birincil_{seri_}_TR"] = _m(str(x["birincil_seri"]), "", "Birincil gösterim serisi", "doğrulanmadı")
    x = cm[(cm.birim == "TR") & (cm.hedef == "son_tam_ay") & (cm.seri == "modis_temiz")]
    if len(x):
        met["takvim_son_tam_ay_oran_modis_temiz_TR"] = _m(round(float(x.iloc[0]["oran"]), 3), "kat", "Son tam ay, MODIS temiz oranı (ölçülmüş)", "ölçüldü")
    x = cm[(cm.birim == "TR") & (cm.hedef == "son_tam_ay") & (cm.seri == "viirs_temiz_ub")]
    if len(x):
        met["takvim_son_tam_ay_oran_viirs_temiz_ub_TR"] = _m(round(float(x.iloc[0]["oran"]), 3), "kat", "Son tam ay, VIIRS uydu başına temiz oranı", "tahmini")
    met["takvim_birim_sayisi"] = _m(len(v.units), "birim", "TR + bölge + il")
    met["takvim_bolgesiz_il"] = _m(len(v.bolgesiz_il), "il", "7 bölge eşlemesinde olmayan il sayısı")
    met["takvim_son_gun"] = _m(str(v.son_gun.date()), "", "Günlük kapsamdaki son gün (mevcut ay buna göre)")
    met["takvim_sure_sn"] = _m(round(time.time() - t0, 1), "sn", "Tüm takvim hattı süresi")
    C.PART.parent.mkdir(parents=True, exist_ok=True)
    C.PART.write_text(json.dumps({"metrics": met}, ensure_ascii=False, indent=1), encoding="utf-8")
    r["metrics"] = len(met)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
