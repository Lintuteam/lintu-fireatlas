"""Temizlik modülü sağlamlık testleri (düz assert; pytest varsa da çalışır).

Basitçe: "Hiç nokta kaybolmadı mı? NASA'nın etiketleri korundu mu? Kural küçük örnekte
beklediğimizi yapıyor mu? Kodda gizli sabit eşik var mı?" sorularını sınar.
Çalıştırma: python src/cleaning/test_cleaning.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
import persistence as P  # noqa: E402

KATEGORI = {"temiz", "deniz", "volkan", "statik_nasa", "sanayi", "dusuk_guven", "aniz", "kalici_belirsiz"}


def _mini():
    """Sentetik test verisi (K2: yalnız testte). Hücre A: 6 yıl, her yıl 12 ay, gece (baca).
    Hücre B: 6 yıl, her yıl yalnız Ağustos, gündüz (tarla)."""
    rows = []
    for y in range(2015, 2021):
        for m in range(1, 13):
            for d in (3, 10, 17, 24):
                rows.append(dict(cell=1, yr=y, mon=m, dayn=(y - 2000) * 372 + m * 31 + d, dn="N", type=0))
        rows.append(dict(cell=2, yr=y, mon=8, dayn=(y - 2000) * 372 + 8 * 31 + 5, dn="D", type=0))
    return pd.DataFrame(rows)


def test_kural_kucuk_ornek():
    f = P.features(P.cell_year_table(_mini()))
    san = P.sanayi_kurali(f, N=40, M=8, Y=5, S=4)
    assert bool(san.loc[1]) and not bool(san.loc[2]), san
    assert f.loc[1, "nmon"] == 12 and f.loc[2, "nmon"] == 1 and f.loc[1, "ny"] == 6
    kal = P.kalici_kurali(f, san, M=8, Y=5, gece_payi=0.5)
    assert not kal.any()


def test_loyo_haric_yil():
    cy = P.cell_year_table(_mini())
    f = P.features(cy, haric_yil=2015)
    assert f.loc[1, "ny"] == 5 and f.loc[2, "ny"] == 5


def test_komsu_sayim():
    cnt = P.komsu_gun_sayimi(np.array([100_000 * 5 + 5, 100_000 * 5 + 6, 100_000 * 9 + 9]),
                             np.array([1, 1, 1]), np.array([100_000 * 5 + 5]), np.array([1]), 1)
    assert cnt[0] == 2


def test_cikti_butunlugu():
    if not C.STATUS_OUT.exists():
        print("ATLANDI: points_status.parquet yok"); return
    st = pd.read_parquet(C.STATUS_OUT)
    pts = pd.read_parquet(C.POINTS, columns=["pid", "type"])
    assert len(st) == len(pts) and st["pid"].is_unique, "K3: satır sayısı korunmalı"
    assert set(st["pid"]) == set(pts["pid"])
    assert st["status"].notna().all() and set(st["status"].astype(str)) <= KATEGORI
    m = pts.merge(st, on="pid")
    assert (m.loc[m["type"] == 1, "status"] == "volkan").all()
    assert (m.loc[m["type"] == 3, "status"] == "deniz").all()
    assert (m.loc[m["type"] == 2, "status"] == "statik_nasa").all()


def test_olay_aniz_kismi_yok():
    """Anız kararı olay düzeyinde: bir olayın ya tüm noktaları anız ya hiçbiri."""
    pe_f = C.PROCESSED / "points_event.parquet"
    if not (C.STATUS_OUT.exists() and pe_f.exists()):
        print("ATLANDI: olay tablosu yok"); return
    m = pd.read_parquet(C.STATUS_OUT).merge(pd.read_parquet(pe_f), on="pid")
    m = m[m["event_id"] >= 0]
    pay = (m["status"].astype(str) == "aniz").groupby(m["event_id"]).mean()
    assert ((pay == 0) | (pay == 1)).all(), "kısmi anız etiketi var"
    assert set(m["status"].astype(str)) <= {"temiz", "aniz"}, "olay girdisi {temiz, aniz} olmalı"


def test_sabit_esik_yok():
    """Kodda eşik karşılaştırması sayıyla yazılmamalı (K9): '>= 40', '< 15' gibi."""
    pat = re.compile(r"(nd|nmon|ny|medm|frp|gece)\"?\]?\s*[<>]=?\s*\d")
    for p in HERE.glob("*.py"):
        if p.name.startswith("test_"):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            assert not pat.search(line), f"{p.name}:{i} sabit eşik: {line.strip()}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK", name)
