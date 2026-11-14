"""Gözlem kapsamı (çıkarım) -> data/processed/coverage.parquet + coverage_kesintiler.csv.

Basitçe: Bir uydunun Türkiye'yi hangi günlerde "gözlemlediğini" bilmiyoruz (bulut/şerit verisi yok, K2).
Ama bir ipucu var: uydu 3+ gün üst üste hiç tespit vermemişken AYNI SENSÖR AİLESİNDEKİ kardeş uydular
aynı günlerde bol tespit veriyorsa, sorun yangınsızlık değil uydunun kesintisidir (SNPP, Temmuz-Ağustos 2022).
Bu günler "gözlenmedi" sayılır; takvim ve anomaliye "yangın yok" diye girmesin.

Teknik olarak (hepsi etiket: TAHMİNİ, K5):
- Aile: MODIS = {Terra, Aqua}, VIIRS = {SNPP, N20, N21}. Kardeş = aynı ailedeki diğer uydular.
- Uydu s için günlük tespit sayısı n_s(d), s'nin [ilk, son] gün aralığında (points.parquet'ten).
- Ardışık >= G gün n_s = 0 ve aynı günlerde kardeşlerin toplamı >= K ise bu günler
  observed=False, source='çıkarım_kesinti'. (G, K: esikler.json, K9)
- Kardeşin hiç çalışmadığı günler (Terra 2000-2002, SNPP 2012-2018 tek başına): kesinti bilinemez,
  observed=True, source='çıkarım_aralık_kardessiz'.
- Diğer günler observed=True, source='çıkarım_aralık' (aralıktaki bilinmeyen kesinti olabilir).
- n_overpass bilinmez (<NA>). FIRMS swath ürünü toplu indirilemiyor (docs/ek_kaynaklar.md) -> 'swath' satırı yok.
Sınırlama: G günden kısa kesintiler ve kardeşin de sönük olduğu kesintiler yakalanmaz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402

POINTS = ROOT / "data" / "processed" / "points.parquet"
OUT = ROOT / "data" / "processed" / "coverage.parquet"
OUT_GAPS = ROOT / "data" / "processed" / "coverage_kesintiler.csv"
OUT_META = ROOT / "data" / "processed" / "coverage.meta.json"
FAMILIES = {"MODIS": ["Terra", "Aqua"], "VIIRS": ["SNPP", "N20", "N21"]}
SRC_RANGE, SRC_NOSIB, SRC_GAP = "çıkarım_aralık", "çıkarım_aralık_kardessiz", "çıkarım_kesinti"


def daily_counts(p: pd.DataFrame) -> pd.DataFrame:
    """Gün (satır) x uydu (sütun) tespit sayısı; her uydunun kendi [ilk,son] aralığı dışı NaN."""
    d = p.groupby(["day_tr", "sat"], observed=True).size().unstack(fill_value=0)
    days = pd.date_range(d.index.min(), d.index.max(), freq="D")
    d = d.reindex(days, fill_value=0).astype(float)
    for s in d.columns:
        nz = d.index[d[s] > 0]
        d.loc[(d.index < nz.min()) | (d.index > nz.max()), s] = np.nan
    return d


def find_gaps(d: pd.DataFrame, G: int, K: int) -> pd.DataFrame:
    """Kesinti çalışmaları: sat, baslangic, bitis, gun, kardes_tespit."""
    rows = []
    for fam, sats in FAMILIES.items():
        for s in [x for x in sats if x in d.columns]:
            sib = [x for x in sats if x != s and x in d.columns]
            zero = (d[s] == 0).to_numpy()
            sib_n = d[sib].fillna(0).sum(axis=1).to_numpy() if sib else np.zeros(len(d))
            i, n = 0, len(d)
            while i < n:
                if not zero[i]:
                    i += 1
                    continue
                j = i
                while j + 1 < n and zero[j + 1]:
                    j += 1
                tot = int(sib_n[i:j + 1].sum())
                if j - i + 1 >= G and tot >= K:
                    rows.append({"sat": s, "baslangic": d.index[i].date(), "bitis": d.index[j].date(),
                                 "gun": j - i + 1, "kardes_tespit": tot})
                i = j + 1
    return pd.DataFrame(rows, columns=["sat", "baslangic", "bitis", "gun", "kardes_tespit"])


def build(p: pd.DataFrame, G: int, K: int):
    d = daily_counts(p)
    gaps = find_gaps(d, G, K)
    rows = []
    for s in d.columns:
        fam = next(f for f, v in FAMILIES.items() if s in v)
        sib = [x for x in FAMILIES[fam] if x != s and x in d.columns]
        col = d[s]
        days = col.index[col.notna()]
        sib_alive = d.loc[days, sib].notna().any(axis=1) if sib else pd.Series(False, index=days)
        src = np.where(sib_alive.to_numpy(), SRC_RANGE, SRC_NOSIB).astype(object)
        obs = np.ones(len(days), dtype=bool)
        for g in gaps[gaps["sat"] == s].itertuples():
            m = (days >= pd.Timestamp(g.baslangic)) & (days <= pd.Timestamp(g.bitis))
            obs[m] = False
            src[m] = SRC_GAP
        rows.append(pd.DataFrame({
            "sat": s, "day_tr": days.date, "observed": obs,
            "n_overpass": pd.array([pd.NA] * len(days), dtype="Int16"),
            "source": src, "etiket": "tahmini", "n_tespit": col.loc[days].astype("int32").to_numpy()}))
    return pd.concat(rows, ignore_index=True), gaps


def main():
    G, K = cfg.esik("G"), cfg.esik("K")
    p = pd.read_parquet(POINTS, columns=["sat", "day_tr"])
    p["day_tr"] = pd.to_datetime(p["day_tr"])
    cov, gaps = build(p, G, K)
    cov["sat"] = cov["sat"].astype(str)
    cov.to_parquet(OUT, index=False)
    gaps.to_csv(OUT_GAPS, index=False)
    d = daily_counts(p)
    sens = {}
    for g in (2, 3, 5):
        gg = find_gaps(d, g, K)
        sens[f"G={g}"] = {"kesinti_gun": int(gg["gun"].sum()), "kesinti_sayisi": len(gg),
                          "uydu_bazinda_gun": {k: int(v) for k, v in gg.groupby("sat")["gun"].sum().items()}}
    meta = {"G": G, "K": K, "satir": len(cov), "observed_false": int((~cov["observed"]).sum()),
            "source_dagilimi": {k: int(v) for k, v in cov["source"].value_counts().items()},
            "duyarlilik_K50": sens,
            "uydu_gun": {k: int(v) for k, v in cov.groupby("sat").size().items()}}
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print(gaps.to_string())


if __name__ == "__main__":
    main()
