"""Harmonizasyon birim testleri (yapay küçük veri yalnız testte; K2).

Çalıştır: python -m pytest src/harmonize/test_harmonize.py -q   (ya da doğrudan python ile)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eslestirme  # noqa: E402
import guven_esleme  # noqa: E402
import seri  # noqa: E402

T0 = pd.Timestamp("2020-07-01 10:30", tz="UTC")


def _pts(rows):
    return pd.DataFrame(rows, columns=["pid", "lat", "lon", "t_utc", "scan", "track", "sat"])


def test_ayak_izi_ici_ve_disi():
    m = _pts([(1, 39.0, 35.0, T0, 2.0, 1.0, "Aqua")])
    km_lon = 1 / (111.32 * np.cos(np.radians(39.0)))
    v = _pts([
        (10, 39.0, 35.0 + 0.9 * km_lon, T0, .375, .375, "SNPP"),          # dx 0.9 < 1.0+0.375 -> içinde
        (11, 39.0, 35.0 + 1.5 * km_lon, T0, .375, .375, "SNPP"),          # dx 1.5 > 1.375 -> dışında
        (12, 39.0 + 0.8 / 111.32, 35.0, T0, .375, .375, "SNPP"),          # dy 0.8 < 0.5+0.375 -> içinde
        (13, 39.0 + 1.0 / 111.32, 35.0, T0, .375, .375, "SNPP"),          # dy 1.0 > 0.875 -> dışında
        (14, 39.0, 35.0, T0 + pd.Timedelta(hours=6), .375, .375, "SNPP"),  # zaman penceresi dışı
    ])
    pr = eslestirme.aday_ciftler(m, v)
    assert set(pr["v_pid"]) == {10, 12}


def test_kenar_kurali_tek_hucre():
    # İki üst üste binen iz; nokta ikisine de düşer ama normalize uzaklığı küçük olana gider
    km_lon = 1 / (111.32 * np.cos(np.radians(39.0)))
    m = _pts([(1, 39.0, 35.0, T0, 4.0, 2.0, "Aqua"), (2, 39.0, 35.0 + 2.0 * km_lon, T0, 4.0, 2.0, "Aqua")])
    v = _pts([(10, 39.0, 35.0 + 1.6 * km_lon, T0, .375, .375, "SNPP")])
    pr = eslestirme.aday_ciftler(m, v)
    assert len(pr) == 2
    sec = pr.sort_values("dnorm").iloc[0]
    assert sec["m_pid"] == 2


def test_esit_yuzdelik_sinirlar():
    rng = np.random.default_rng(0)
    deger = rng.integers(0, 101, 10000)
    cls = np.where(deger <= 20, "dusuk", np.where(deger <= 70, "nominal", "yuksek"))
    c1, c2, pay = guven_esleme.sinirlar(pd.DataFrame({"m_conf": deger, "v_cls": cls}))
    assert abs(c1 - 20) <= 1 and abs(c2 - 70) <= 1


def test_sicrama():
    s = pd.Series([10, 10, 10, 20, 20, 20], index=range(2009, 2015), dtype=float)
    assert abs(seri.sicrama(s, 2012, 3) - 100.0) < 1e-9


def test_olay_esdeger_tespit_esdegeri_asmaz():
    """F2-01: her (küme, yıl>=2012) için olay eşdeğeri <= tespit eşdeğeri: il->bölge toplamı,
    ay_TR ve yil_TR düzeyinde. Veri yoksa atlanır."""
    import ortak as O
    if not O.OUT_HARM.exists():
        return
    h = pd.read_parquet(O.OUT_HARM)
    h = h[h["yil"] >= 2012]
    ihlal = 0
    for kume, g in h.groupby("kume"):
        tb = g[(g["birim"] == "tespit") & (g["duzey"] == "ay_bolge")].set_index(["yil", "ay", "bolge7"])["ana_seri"]
        ob = g[(g["birim"] == "olay") & (g["duzey"] == "ay_il")].groupby(["yil", "ay", "bolge7"])["ana_seri"].sum()
        ihlal += int((ob > tb.reindex(ob.index).fillna(0)).sum())
        for d in ("ay_TR", "yil_TR"):
            tt = g[(g["birim"] == "tespit") & (g["duzey"] == d)].set_index(["yil", "ay"])["ana_seri"]
            oo = g[(g["birim"] == "olay") & (g["duzey"] == d)].set_index(["yil", "ay"])["ana_seri"]
            ihlal += int((oo > tt.reindex(oo.index).fillna(0)).sum())
    assert ihlal == 0, f"olay eşdeğeri tespit eşdeğerini {ihlal} hücrede aşıyor"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
