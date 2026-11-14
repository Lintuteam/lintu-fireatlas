"""Güven yüzdelik eşleştirmesi (U-01, U-05, Yusuf'un S1 isteği).

Basitçe: VIIRS bir yangına "düşük / normal / yüksek" der, MODIS 0-100 arası bir yüzde verir.
"VIIRS 'düşük' derken MODIS yüzde kaç diyor?" sorusunu, AYNI YANGINA AYNI ANDA bakan uydu
çiftleriyle (Aqua ~13:30 ve VIIRS ~13:30) cevaplıyoruz. Sonra MODIS yüzdesini, VIIRS'in
düşük/normal/yüksek oranlarına uyacak yerlerden kesiyoruz (ör. VIIRS çiftlerin %20'sine 'düşük'
diyorsa, MODIS'in en düşük %20'si 'düşük' olur). Bu, iki termometreyi aynı cetvele oturtmak gibidir.

Teknik olarak:
- Çift: Aqua tespiti + ayak izi içinde |Δt| <= kalibrasyon_zaman_penceresi_dk olan VIIRS
  noktaları (eslestirme.py aday çiftleri). Her Aqua tespitine bir VIIRS sınıfı: izindeki VIIRS
  noktalarının EN YÜKSEK sınıfı (MODIS pikseli tüm alt pikselleri kapsar; içinde bir tane bile
  güçlü sinyal varsa MODIS güveni yükselir). Alternatif "en büyük FRP'li noktanın sınıfı" kuralı
  ölçüldü ve daha zayıf ilişki verdi (Spearman ~0,01'e karşı ~0,21; belge). Yalnız type 0/-1.
- Eşit yüzdelik (equipercentile) eşleme: p_l, p_n = çiftlerde VIIRS l ve n payı. MODIS sınırları
  c1, c2 tamsayıları, F_MODIS(c1) ~ p_l ve F_MODIS(c2) ~ p_l + p_n olacak şekilde seçilir.
- Kararlılık: her yıl dışarıda bırakılarak sınırlar yeniden öğrenilir (aralık raporlanır).
- Bağımsız sınama (K4): dışarıda bırakılan yılda, öğrenilmiş sınırlar ile FIRMS sınırlarının
  VIIRS sınıfıyla uyumu (doğru sınıf oranı, ağırlıksız Cohen kappa) karşılaştırılır.
FIRMS eşlemesi (conf_cls) HAM sınıf olarak kalır; öğrenilmiş eşleme ayrı sütundur (conf_cls_ogr).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak as O  # noqa: E402

BETIK = "src/harmonize/guven_esleme.py"
SIN = ["dusuk", "nominal", "yuksek"]


def ciftler() -> pd.DataFrame:
    p = O.load_points()
    keep = O.analiz_kumesi(p, "temiz_aniz")   # güven: gerçek yangın noktaları (anız da yangın)
    pr = pd.read_parquet(O.INTERIM / "pairs.parquet")
    pr = pr[pr["m_sat"].eq("Aqua") & pr["esz"]]
    pv = p.loc[keep & p["sensor"].eq("VIIRS"), ["pid", "frp", "conf_cls"]].rename(
        columns={"pid": "v_pid", "frp": "v_frp", "conf_cls": "v_cls"})
    pm = p.loc[keep & p["sat"].eq("Aqua"), ["pid", "conf_raw", "dn", "yil", "bolge7", "mevsim"]].rename(
        columns={"pid": "m_pid"})
    x = pr.merge(pv, on="v_pid").merge(pm, on="m_pid")
    x["_r"] = x["v_cls"].map({c: i for i, c in enumerate(SIN)})
    x["m_conf"] = pd.to_numeric(x["conf_raw"], errors="coerce")
    x = x.dropna(subset=["m_conf"])
    alt = x.sort_values(["m_pid", "v_frp"], ascending=[True, False]).drop_duplicates("m_pid")
    x = x.sort_values(["m_pid", "_r", "v_frp"], ascending=[True, False, False]).drop_duplicates("m_pid")
    x.attrs["spearman_alt_maxfrp"] = float(alt["m_conf"].corr(alt["_r"], method="spearman"))
    return x


def sinirlar(x: pd.DataFrame) -> tuple[int, int, dict]:
    pay = x["v_cls"].value_counts(normalize=True)
    pl, pn = float(pay.get("dusuk", 0)), float(pay.get("nominal", 0))
    conf = np.sort(x["m_conf"].to_numpy())
    ks = np.arange(0, 101)
    F = np.searchsorted(conf, ks, side="right") / len(conf)
    c1 = int(ks[np.argmin(np.abs(F - pl))])
    c2 = int(ks[np.argmin(np.abs(F - (pl + pn)))])
    return c1, c2, {"p_dusuk": pl, "p_nominal": pn, "p_yuksek": 1 - pl - pn}


def sinifla(conf, c1, c2):
    return np.where(conf <= c1, "dusuk", np.where(conf <= c2, "nominal", "yuksek"))


def kappa(a, b) -> float:
    a, b = pd.Series(a), pd.Series(b)
    po = float((a.to_numpy() == b.to_numpy()).mean())
    pa, pb = a.value_counts(normalize=True), b.value_counts(normalize=True)
    pe = float(sum(pa.get(k, 0) * pb.get(k, 0) for k in SIN))
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main() -> dict:
    x = ciftler()
    c1, c2, pay = sinirlar(x)
    firms = O.cfg.load()["guven"]["MODIS"]["siniflar"]
    f1 = [s["max"] for s in firms if s["cls"] == "dusuk"][0]
    f2 = [s["max"] for s in firms if s["cls"] == "nominal"][0]
    # Koşullu dağılım: VIIRS sınıfı verildiğinde MODIS yüzdesi
    kos = (x.groupby("v_cls")["m_conf"].quantile([.05, .25, .5, .75, .95]).unstack().round(0)
             .reindex(SIN))
    kos["n"] = x["v_cls"].value_counts().reindex(SIN)
    capraz = pd.crosstab(sinifla(x["m_conf"], f1, f2), x["v_cls"], normalize="index").round(3)
    # LOYO kararlılık + bağımsız sınama
    rows = []
    for y in sorted(x["yil"].unique()):
        tr, te = x[x["yil"] != y], x[x["yil"] == y]
        if len(te) < 30:
            continue
        a1, a2, _ = sinirlar(tr)
        ogr = sinifla(te["m_conf"], a1, a2)
        frm = sinifla(te["m_conf"], f1, f2)
        rows.append({"yil": int(y), "n_test": int(len(te)), "c1": a1, "c2": a2,
                     "uyum_ogr": float((ogr == te["v_cls"]).mean()),
                     "uyum_firms": float((frm == te["v_cls"]).mean()),
                     "kappa_ogr": kappa(ogr, te["v_cls"]), "kappa_firms": kappa(frm, te["v_cls"])})
    lo = pd.DataFrame(rows)
    gece_gunduz = {}
    for dn, g in x.groupby("dn"):
        a1, a2, pp = sinirlar(g)
        gece_gunduz[dn] = {"c1": a1, "c2": a2, "n": int(len(g)), **{k: round(v, 3) for k, v in pp.items()}}
    sonuc = {
        "n_cift": int(len(x)), "yillar": [int(x["yil"].min()), int(x["yil"].max())],
        "c1": c1, "c2": c2, "pay": {k: round(v, 4) for k, v in pay.items()},
        "firms_sinirlari": [f1, f2],
        "loyo_c1_aralik": [int(lo["c1"].min()), int(lo["c1"].max())],
        "loyo_c2_aralik": [int(lo["c2"].min()), int(lo["c2"].max())],
        "loyo_uyum_ogr_ort": round(float(lo["uyum_ogr"].mean()), 4),
        "loyo_uyum_firms_ort": round(float(lo["uyum_firms"].mean()), 4),
        "loyo_kappa_ogr_ort": round(float(lo["kappa_ogr"].mean()), 4),
        "loyo_kappa_firms_ort": round(float(lo["kappa_firms"].mean()), 4),
        "loyo_ogr_daha_iyi_yil": int((lo["uyum_ogr"] > lo["uyum_firms"]).sum()),
        "loyo_yil_sayisi": int(len(lo)),
        "spearman_modis_viirs": round(float(pd.Series(x["m_conf"]).corr(
            x["v_cls"].map({"dusuk": 0, "nominal": 1, "yuksek": 2}), method="spearman")), 4),
        "spearman_alternatif_maxfrp_kurali": round(x.attrs["spearman_alt_maxfrp"], 4),
        "kosullu_modis_yuzdesi": kos.reset_index().to_dict("records"),
        "firms_modis_sinifina_gore_viirs_payi": capraz.reset_index().to_dict("records"),
        "gunduz_gece_ayri": gece_gunduz,
        "loyo_tablo": lo.round(4).to_dict("records"),
    }
    O.json_yaz(O.INTERIM / "guven_esleme.json", sonuc)
    return sonuc


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import json
    s = main()
    s.pop("loyo_tablo")
    print(json.dumps(s, ensure_ascii=False, indent=1, default=str))
