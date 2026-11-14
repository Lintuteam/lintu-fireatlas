"""Çok yıllı hücre kalıcılığı: sanayi, kalıcı-belirsiz ve yangın koruması.

Basitçe: Bir orman yangını birkaç gün, bazen birkaç hafta sürer; ama yıllar boyu, yılın
her ayında aynı 1 km'lik karede ısı görünüyorsa orada büyük olasılıkla bir baca, rafineri
meşalesi veya maden ocağı vardır. Bu dosya her kare için "kaç yıl, kaç farklı ay, kaç gün,
yıl içinde kaç ay sürüyor, ne kadarı gece" sorularını sayar ve kurala göre etiket önerir.
Etiket bir tahmindir (kurala göre etiket), yerinde doğrulama değildir.

Teknik olarak:
- Hücre × yıl tablosu (cy): n, gece sayısı, type=2 sayısı, arşiv (type>=0) sayısı,
  farklı gün sayısı, 12 bitlik ay maskesi.
- features(cy, haric_yil): bir yıl dışarıda bırakılarak (LOYO, K4) hücre özellikleri:
  ny (farklı yıl), nd (farklı gün toplamı), nmon (farklı takvim ayı, 1–12), medm (aktif
  yıllarda yıl içi farklı ay sayısının medyanı), gece payı, NASA type=2 payı.
- Sanayi kuralı: ny>=Y & nmon>=M & nd>=N & medm>=S (eşikler config'te).
- Kalıcı-belirsiz: Y ve M tutuyor ama N veya S tutmuyor (sanayi değil) ve tespitlerin çoğu
  gece (kalici_gece_payi). Kömür ocağı, çöplük, aralıklı yakma bacası gibi belirsiz kaynaklar.
- Yıllık tekrar bayrağı (status DEĞİŞMEZ): il bazında yıllık aktif-hücre oranlarından
  Poisson-binom rastlantı modeli; hücrenin aktif yıl sayısı olağan dışıysa (P<alfa).
  Bu tanım status için reddedildi: tarım ovalarında ~196 bin noktayı işaretliyordu.
- Yangın koruması: kalıcı hücredeki nokta, aynı gün ~5 km komşulukta kalıcı OLMAYAN
  hücrelerde >=G tespit varsa (çevrede yangın var) temiz bırakılır.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

POPCOUNT = np.array([bin(i).count("1") for i in range(4096)], dtype=np.int8)


def cell_year_table(df: pd.DataFrame) -> pd.DataFrame:
    """df: type 1/3 hariç noktalar (cell, yr, mon, day_tr, dn, type)."""
    d = df[["cell", "yr", "mon"]].drop_duplicates()
    d = d.assign(bit=np.left_shift(1, d["mon"].to_numpy().astype(np.int64) - 1))
    mask = d.groupby(["cell", "yr"])["bit"].sum()
    nd = df[["cell", "yr", "dayn"]].drop_duplicates().groupby(["cell", "yr"]).size()
    tmp = pd.DataFrame({"cell": df["cell"].to_numpy(), "yr": df["yr"].to_numpy(),
                        "nig": (df["dn"] == "N").to_numpy(), "is2": (df["type"] == 2).to_numpy(),
                        "isa": (df["type"] >= 0).to_numpy()})
    cy = tmp.groupby(["cell", "yr"]).agg(n=("nig", "size"), nn=("nig", "sum"), t2=("is2", "sum"),
                                         na=("isa", "sum"))
    cy["nd"] = nd
    cy["mask"] = mask
    cy = cy.reset_index()
    cy["nm"] = POPCOUNT[cy["mask"].to_numpy()]
    return cy


def features(cy: pd.DataFrame, haric_yil=None) -> pd.DataFrame:
    c = cy if haric_yil is None else cy[cy["yr"] != haric_yil]
    g = c.groupby("cell")
    f = pd.DataFrame({
        "ny": g.size(),
        "nd": g["nd"].sum(),
        "mask": g["mask"].agg(np.bitwise_or.reduce),
        "medm": g["nm"].median(),
        "n": g["n"].sum(),
        "nn": g["nn"].sum(),
        "t2": g["t2"].sum(),
        "na": g["na"].sum(),
    })
    f["nmon"] = POPCOUNT[f["mask"].to_numpy()]
    f["gece"] = f["nn"] / f["n"]
    f["t2pay"] = np.where(f["na"] > 0, f["t2"] / f["na"].clip(lower=1), np.nan)
    return f


def sanayi_kurali(f: pd.DataFrame, N, M, Y, S) -> pd.Series:
    return (f["ny"] >= Y) & (f["nmon"] >= M) & (f["nd"] >= N) & (f["medm"] >= S)


def kalici_kurali(f: pd.DataFrame, san: pd.Series, M, Y, gece_payi) -> pd.Series:
    """Kalıcı-belirsiz: Y yıl ve M takvim ayı koşulu tutuyor, sanayi değil, tespitlerin çoğu gece."""
    return (f["ny"] >= Y) & (f["nmon"] >= M) & (f["gece"] >= gece_payi) & ~san


def nasa_mirasi(f: pd.DataFrame, pay) -> pd.Series:
    """Hücrenin (başka yıllardaki) arşiv noktalarının >= pay kadarı NASA type=2 mi."""
    return f["t2pay"].fillna(0) >= pay


def kalici_null(cy: pd.DataFrame, cell_il: pd.Series, alfa: float, min_yil: int,
                haric_yil=None) -> pd.DataFrame:
    """İl × yıl aktif-hücre oranından Poisson-binom kuyruk olasılığı.

    Evren = o ilde herhangi bir yıl aktif olmuş hücreler (gerçek alan daha büyük olduğu için
    p olduğundan büyük tahmin edilir; sonuç ihtiyatlı: daha az hücre işaretlenir).
    """
    c = cy if haric_yil is None else cy[cy["yr"] != haric_yil]
    c = c.assign(il=c["cell"].map(cell_il))
    years = np.sort(c["yr"].unique())
    univ = c.groupby("il")["cell"].nunique()
    act = c.groupby(["il", "yr"])["cell"].nunique().unstack(fill_value=0).reindex(columns=years, fill_value=0)
    ny = c.groupby("cell").size()
    out = pd.DataFrame({"ny": ny, "il": ny.index.map(cell_il)})
    tail = np.ones(len(out))
    for il, row in act.iterrows():
        p = (row.to_numpy() / max(univ.get(il, 1), 1)).clip(0, 1)
        pmf = np.zeros(len(p) + 1); pmf[0] = 1.0
        for pi in p:  # Poisson-binom dağılımı (dinamik programlama)
            pmf[1:] = pmf[1:] * (1 - pi) + pmf[:-1] * pi
            pmf[0] *= (1 - pi)
        sf = pmf[::-1].cumsum()[::-1]  # sf[k] = P(X >= k)
        m = (out["il"] == il).to_numpy()
        k = out["ny"].to_numpy()[m]
        tail[m] = sf[np.minimum(k, len(sf) - 1)]
    out["p_tail"] = tail
    out["kalici"] = (out["p_tail"] < alfa) & (out["ny"] >= min_yil)
    return out


def komsu_gun_sayimi(src_cell: np.ndarray, src_day: np.ndarray, q_cell: np.ndarray,
                     q_day: np.ndarray, k: int) -> np.ndarray:
    """Her sorgu (hücre, gün) için (2k+1)^2 komşulukta aynı gün kaynak tespit sayısı."""
    key = src_cell.astype(np.int64) * 100_000 + src_day.astype(np.int64)
    cnt = pd.Series(key).value_counts()
    tot = np.zeros(len(q_cell), dtype=np.int64)
    for di in range(-k, k + 1):
        for dj in range(-k, k + 1):
            qk = (q_cell.astype(np.int64) + di * 100_000 + dj) * 100_000 + q_day.astype(np.int64)
            tot += cnt.reindex(qk).fillna(0).to_numpy(dtype=np.int64)
    return tot
