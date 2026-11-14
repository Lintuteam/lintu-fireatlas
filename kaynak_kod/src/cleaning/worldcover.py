"""Arazi örtüsüyle bağımsız doğrulama (ESA WorldCover 2021, U-09).

Basitçe: Uydunun "anız" dediğimiz ateşleri gerçekten tarlada mı, "sanayi" dediklerimiz
gerçekten yapılaşmış alanda mı? Bunu yangın verisinden tamamen bağımsız bir haritayla,
Avrupa Uzay Ajansı'nın 10 m'lik arazi örtüsü haritasıyla (WorldCover 2021) kontrol ediyoruz.
Haritanın tamamını indirmiyoruz; yalnız örnek noktaların düştüğü küçük parçaları okuyoruz.

Teknik olarak:
- Kaynak: resmî AWS S3 açık veri, COG karoları
  https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_<N..E..>_Map.tif
  Lisans: CC BY 4.0 (esa-worldcover.org veri erişim sayfası ve karo meta verisi, 2026-11-13).
  Atıf: "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021)
  processed by ESA WorldCover consortium".
- Okuma: GDAL /vsicurl aralık istekleri, iç genel görünüm düzeyi `temizlik.wc_overview_duzey`
  (düzey 1 = 4× küçültme, ~33 m piksel). Her noktada ±`temizlik.wc_pencere_px` piksellik
  pencerede (~VIIRS pikseli) en sık sınıf. Bayt sayacı (blok sayısı × ölçülen blok boyu) ile
  trafik `temizlik.wc_trafik_mb` sınırını aşarsa okuma durur.
- Örneklem (sabit tohum, yalnız seçim için): anız, kural-kalıcı (sanayi + kalici_belirsiz),
  NASA statik, büyük temiz olay (events n_mcell >= temizlik.wc_buyuk_olay_mcell, anız değil).
- Sınırlama: WorldCover 2021 tek yıl; 2000–2026 noktaları için arazi değişimi yok sayılır.
  WorldCover'ın kendi doğruluğu sınırlıdır (üretici raporu; bu projede ölçülmedi).
Çalıştırma: python src/cleaning/worldcover.py  -> audit/worldcover_ornek.csv + metrikler
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

URL = "/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{t}_Map.tif"
SINIF = {10: "agac", 20: "cali", 30: "cayir", 40: "ekili_alan", 50: "yapilasmis", 60: "ciplak",
         70: "kar", 80: "su", 90: "sulak", 95: "mangrov", 100: "yosun", 0: "veri_yok"}
OUT = C.AUDIT / "worldcover_ornek.csv"
BETIK = "src/cleaning/worldcover.py"
METR = C.AUDIT / "worldcover_metrikler.json"


def karo(lat, lon):
    la = int(np.floor(lat / 3) * 3); lo = int(np.floor(lon / 3) * 3)
    return f"{'N' if la >= 0 else 'S'}{abs(la):02d}{'E' if lo >= 0 else 'W'}{abs(lo):03d}"


def birlestir():
    """WorldCover metriklerini temizlik parçasına ekler (build_status yeniden yazınca da çağrılır)."""
    if METR.exists() and C.PART.exists():
        part = json.loads(C.PART.read_text(encoding="utf-8"))
        part["metrics"].update(json.loads(METR.read_text(encoding="utf-8")))
        C.PART.write_text(json.dumps(part, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


def ornekle() -> pd.DataFrame:
    n = C.t("wc_ornek_sayisi")
    rng = np.random.default_rng(C.t("wc_tohum"))
    p = C.load_points()[["pid", "lat", "lon", "yr"]].merge(pd.read_parquet(C.STATUS_OUT), on="pid")
    ev = pd.read_parquet(C.PROCESSED / "events.parquet", columns=["event_id", "n_mcell"])
    pe = pd.read_parquet(C.PROCESSED / "points_event.parquet")
    p = p.merge(pe, on="pid", how="left").merge(ev, on="event_id", how="left")
    st = p["status"].astype(str)
    gruplar = {
        "aniz": st == "aniz",
        "kural_kalici": st.isin(["sanayi", "kalici_belirsiz"]),
        "statik_nasa": st == "statik_nasa",
        "buyuk_temiz": (st == "temiz") & (p["n_mcell"].fillna(0) >= C.t("wc_buyuk_olay_mcell")),
    }
    parca = []
    for g, m in gruplar.items():
        idx = np.where(m.to_numpy())[0]
        k = n if g != "statik_nasa" else n // 4
        sec = rng.choice(idx, size=min(k, len(idx)), replace=False)
        parca.append(p.iloc[sec][["pid", "lat", "lon", "yr", "status"]].assign(grup=g, havuz=len(idx)))
    return pd.concat(parca, ignore_index=True)


def _boyut(t: str) -> float:
    import urllib.request
    req = urllib.request.Request(URL.format(t=t).replace("/vsicurl/", ""), method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return float(r.headers["Content-Length"])


def oku(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    import rasterio
    from rasterio.windows import Window
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
    lvl, w, sinir = C.t("wc_overview_duzey"), C.t("wc_pencere_px"), C.t("wc_trafik_mb") * 1e6
    df = df.assign(karo=[karo(a, b) for a, b in zip(df["lat"], df["lon"])], sinif=-1)
    bloklar, bayt = set(), 0.0
    t0 = time.time()
    with rasterio.Env(GDAL_CACHEMAX=512):
        for t, g in df.groupby("karo"):
            try:
                ds = rasterio.open(URL.format(t=t), OVERVIEW_LEVEL=lvl)
            except Exception as e:  # karo yoksa (deniz) veri_yok kalır
                print("karo açılamadı", t, type(e).__name__); continue
            with ds:
                # blok başına bayt (üst sınır): karo dosya boyu (HTTP HEAD) / tam çözünürlük blok sayısı
                blk = ds.block_shapes[0]
                ort_blok = _boyut(t) / (np.ceil(ds.profile["width"] * 2 ** (lvl + 1) / blk[1]) ** 2)
                for i, r in g.iterrows():
                    row, col = ds.index(r["lon"], r["lat"])
                    for rr in (row - w, row + w):
                        for cc in (col - w, col + w):
                            b = (t, rr // blk[0], cc // blk[1])
                            if b not in bloklar:
                                if bayt + ort_blok > sinir:
                                    raise RuntimeError(f"trafik sınırı aşılacak: {bayt/1e6:.1f} MB")
                                bloklar.add(b); bayt += ort_blok
                    win = Window(col - w, row - w, 2 * w + 1, 2 * w + 1)
                    a = ds.read(1, window=win, boundless=True, fill_value=0).ravel()
                    a = a[a > 0]
                    df.at[i, "sinif"] = int(np.bincount(a).argmax()) if a.size else 0
    return df, {"blok": len(bloklar), "tahmini_trafik_mb": round(bayt / 1e6, 1), "sure_sn": round(time.time() - t0, 1)}


def main():
    s = ornekle()
    s, trf = oku(s)
    s["sinif_ad"] = s["sinif"].map(SINIF).fillna("diger")
    s.to_csv(OUT, index=False, encoding="utf-8")
    dag = (s.groupby("grup")["sinif_ad"].value_counts(normalize=True).unstack(fill_value=0))
    part = {"metrics": {}}
    tanim_ek = "ESA WorldCover 2021 (CC BY 4.0), örneklem noktasında ±wc_pencere_px genel görünüm pikseli (~±110 m) pencerede en sık sınıf; WorldCover tek yıl (2021)"
    for g in dag.index:
        n = int((s["grup"] == g).sum())
        for c in ("ekili_alan", "yapilasmis", "agac", "cali", "cayir"):
            v = float(dag.loc[g, c]) if c in dag.columns else 0.0
            part["metrics"][f"temizlik_wc_{g}_{c}_pay"] = {
                "value": v, "unit": "oran", "tanim": f"{g} örnekleminde (n={n}) arazi sınıfı '{c}' payı. {tanim_ek}",
                "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "etiket": "ölçüldü"}
    orman = ("agac", "cali", "cayir")
    def pay(g, cs):
        return float(sum(dag.loc[g, c] for c in cs if c in dag.columns)) if g in dag.index else None
    part["metrics"]["temizlik_aniz_arazi_ortusu"] = {
        "value": pay("aniz", ("ekili_alan",)), "unit": "oran",
        "tanim": "Olay düzeyi anız noktalarının WorldCover 2021 'ekili alan' sınıfına düşme payı (bağımsız doğrulama; "
                 "karşılaştırma: temizlik_wc_buyuk_temiz_ekili_alan_pay). " + tanim_ek,
        "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "etiket": "ölçüldü"}
    part["metrics"]["temizlik_wc_kural_kalici_yapilasmis_pay"]["tanim"] += " (sanayi kuralı beklentisi: yapılaşmış)"
    part["metrics"]["temizlik_wc_buyuk_temiz_dogal_ortu_pay"] = {
        "value": pay("buyuk_temiz", orman), "unit": "oran", "tanim": "Büyük temiz olay noktalarında ağaç+çalı+çayır payı. " + tanim_ek,
        "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "etiket": "ölçüldü"}
    part["metrics"]["temizlik_wc_trafik_mb"] = {
        "value": trf["tahmini_trafik_mb"], "unit": "MB", "tanim": f"Okunan blok sayısı × ortalama blok boyu (tahmini üst sınır); {trf['blok']} blok",
        "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "etiket": "tahmini"}
    METR.write_text(json.dumps(part["metrics"], ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    birlestir()
    print(trf); print((dag * 100).round(1).to_string())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
