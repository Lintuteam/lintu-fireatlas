"""Günlük tablodan hızlı aralık sayımı (kümülatif toplamlar) ve kesinti-düzeltmeli değer.

Basitçe: Her gün için "o gün uydular gerçekten bakabildi mi?" bilgisi bir ağırlıktır (1 = tam
gözlem, 0.5 = iki uydudan biri kesintide, 0 = hiç bakılamadı). Bir ayın yangın sayısı, bakılabilen
günlerin toplamının "bakılabilen gün ağırlığına" bölünüp ay uzunluğuyla çarpılmasıyla bulunur. Böylece
5 gün uydu kesintisi olan ay haksızca "sakin" görünmez; kesinti günleri paydadan da çıkar.

Teknik olarak: tahmin edici = Σ(sayım_g · 1[w_g>0]) / Σ w_g · n_hedef (oran tahmincisi). w_g =
gözlem yapan uydu / işleyen uydu (grup: modis, viirs, olay=hepsi). Kesinti payı = 1 − Σw / işleyen_gün.
`strict=True` (aylık hücre): işleyen gün < ay uzunluğu (kısmi ay: sensör başlangıcı/bitişi, veri sonu)
veya kesinti payı > eşik ise hücre BOŞ (NaN) olur (C06), sıfır yazılmaz. 'uydu başına' serilerde
oran, aralıktaki ortalama işleyen uydu sayısına bölünür. Birimler: 'TR', 7 coğrafi bölge, il.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

sys.path.insert(0, str(C.ROOT / "src" / "harmonize"))
from ortak import BOLGE7, IL_BOLGE  # noqa: E402

GRUPLAR = ("modis", "viirs", "olay")
_KAPSAM_AD = {"modis": "modis", "viirs": "viirs", "olay": "all"}


class Veri:
    def __init__(self, daily: pd.DataFrame, kapsam: pd.DataFrame):
        k = kapsam.copy()
        k["day"] = pd.to_datetime(k["day_tr"])
        k = k.sort_values("day").reset_index(drop=True)
        self.days = pd.DatetimeIndex(k["day"])
        D = len(k)
        d = daily
        ils = sorted(d["il"].astype(str).unique())
        self.ils = ils
        self.bolgeler = sorted(BOLGE7)
        self.units = ["TR"] + self.bolgeler + ils
        self.uidx = {u: i for i, u in enumerate(self.units)}
        M = np.zeros((len(self.units), len(ils)))
        M[0, :] = 1.0
        for j, il in enumerate(ils):
            b = IL_BOLGE.get(il)
            if b is not None:
                M[1 + self.bolgeler.index(b), j] = 1.0
            M[1 + len(self.bolgeler) + j, j] = 1.0
        self.bolgesiz_il = [il for il in ils if il not in IL_BOLGE]
        di = (pd.to_datetime(d["day_tr"]) - self.days[0]).dt.days.to_numpy()
        li = d["il"].astype(str).map({il: i for i, il in enumerate(ils)}).to_numpy()
        self.W, self.cW, self.cD, self.cO = {}, {}, {}, {}
        for g in GRUPLAR:
            kk = _KAPSAM_AD[g]
            nop = k[f"n_op_{kk}"].to_numpy(float)
            nob = k[f"n_obs_{kk}"].to_numpy(float)
            defined = nop > 0
            w = np.where(defined, nob / np.maximum(nop, 1), 0.0)
            self.W[g] = w
            self.cW[g] = np.concatenate([[0.0], np.cumsum(w)])
            self.cD[g] = np.concatenate([[0.0], np.cumsum(defined.astype(float))])
            self.cO[g] = np.concatenate([[0.0], np.cumsum(nop)])
        z = np.zeros(1)
        self.cN = np.concatenate([z, np.cumsum(k["n_nokta"].to_numpy(float) if "n_nokta" in k else np.zeros(D))])
        self.cNrt = np.concatenate([z, np.cumsum(k["n_nrt"].to_numpy(float) if "n_nrt" in k else np.zeros(D))])
        self.cm, self.cr = {}, {}
        for c in C.COLS_RAW:
            a = np.zeros((len(ils), D))
            a[li, di] = d[c].to_numpy(float)
            u = M @ a
            self.cr[c] = np.concatenate([np.zeros((len(self.units), 1)), np.cumsum(u, axis=1)], axis=1)
            um = u * (self.W[C.GRUP_KOL[c]] > 0)[None, :]
            self.cm[c] = np.concatenate([np.zeros((len(self.units), 1)), np.cumsum(um, axis=1)], axis=1)
        self.yil_bilgi = None

    @classmethod
    def yukle(cls):
        v = cls(pd.read_parquet(C.DAILY), pd.read_parquet(C.KAPSAM))
        v.yil_bilgi = pd.read_parquet(C.YIL_BILGI).set_index("yil")
        return v

    def idx(self, tarih) -> int:
        """Tarih -> gün indeksi (veri aralığı dışı için kırpılmaz; negatif olabilir)."""
        return int((pd.Timestamp(tarih).normalize() - self.days[0]).days)

    @property
    def son_gun(self):
        return self.days[-1]

    # ---------- değerler ----------
    def sayi(self, cols, grup, per_sat, i0, i1, n_hedef=None, strict=False):
        """[birim] vektörü: kesinti-düzeltmeli sayı ve ayrıntı sözlüğü."""
        i0c, i1c = max(i0, 0), min(i1, len(self.days))
        n_hedef = n_hedef or (i1 - i0)
        cm = sum(self.cm[c][:, i1c] - self.cm[c][:, i0c] for c in cols)
        sw = self.cW[grup][i1c] - self.cW[grup][i0c]
        dd = self.cD[grup][i1c] - self.cD[grup][i0c]
        with np.errstate(divide="ignore", invalid="ignore"):
            rate = cm / sw if sw > 0 else np.full_like(cm, np.nan)
            if per_sat:
                nop = (self.cO[grup][i1c] - self.cO[grup][i0c]) / dd if dd > 0 else np.nan
                rate = rate / nop
            kesinti = 1 - sw / dd if dd > 0 else np.nan
        val = rate * n_hedef
        if strict and (dd < n_hedef or not (kesinti <= C.t("kesinti_pay_max"))):
            val = np.full_like(val, np.nan)
        return val, {"sw": sw, "dd": dd, "kesinti": kesinti, "n_hedef": n_hedef, "rate": rate}

    def ham(self, c, i0, i1):
        """Düzeltmesiz ham sayı; sensör o aralıkta hiç işlemiyorsa NaN (0 değil)."""
        i0c, i1c = max(i0, 0), min(i1, len(self.days))
        g = C.GRUP_KOL[c]
        dd = self.cD[g][i1c] - self.cD[g][i0c]
        v = self.cr[c][:, i1c] - self.cr[c][:, i0c]
        return v if dd > 0 else np.full_like(v, np.nan)

    def nrt_payi(self, i0, i1) -> float:
        """Aralıktaki tespitlerin NRT (arşivlenmemiş, hızlı) ürününden gelen payı (TR geneli)."""
        i0c, i1c = max(i0, 0), min(i1, len(self.days))
        n = self.cN[i1c] - self.cN[i0c]
        return float((self.cNrt[i1c] - self.cNrt[i0c]) / n) if n > 0 else float("nan")

    def seri(self, seri, i0, i1, n_hedef=None, strict=False):
        cols, g, ps = C.SERI[seri]
        return self.sayi(cols, g, ps, i0, i1, n_hedef, strict)
