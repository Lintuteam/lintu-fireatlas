"""Takvim-analiz testleri (pytest gerekmez: python src/analytics/test_analytics.py).

Basitçe: "Toplamlar tutuyor mu, kesinti günleri doğru ele alınıyor mu, ay/yıl sınırları doğru mu?"
Sentetik veri YALNIZ bu testlerdedir (K2); gerçek veri testleri parquet varsa çalışır.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import query as Q  # noqa: E402
from veri import Veri  # noqa: E402
from pipeline import timeutil  # noqa: E402

IL = "Adana"


def _sentetik(kesinti_gunleri=(), gun_basi=2, bas="2003-01-01", bit="2005-12-31", n_sat=2):
    """Her gün Adana'da gun_basi MODIS tespiti; kesinti günlerinde uydu bakamaz, tespit 0."""
    days = pd.date_range(bas, bit)
    kes = set(pd.to_datetime(list(kesinti_gunleri)))
    nobs = np.array([0 if d in kes else n_sat for d in days])
    k = pd.DataFrame({"day_tr": days.date, "n_op_modis": n_sat, "n_obs_modis": nobs, "n_op_viirs": 0,
                      "n_obs_viirs": 0, "n_op_all": n_sat, "n_obs_all": nobs})
    d = pd.DataFrame({"il": IL, "day_tr": days.date})
    for c in C.COLS_RAW:
        d[c] = 0
    gb = np.where(nobs > 0, gun_basi, 0)
    for c in ("modis_ham", "modis_temiz"):
        d[c] = gb
    d["olay"] = gb
    d = d[gb > 0].reset_index(drop=True)
    v = Veri(d, k)
    v.yil_bilgi = pd.DataFrame({"normal_modis": True, "normal_viirs": False, "normal_olay": True,
                                "gecis_all": False, "era_all": "x", "gecis_modis": False, "era_modis": "x",
                                "kismi_yil": False}, index=pd.Index([2003, 2004, 2005], name="yil"))
    return v


def _ay(v, y, m, seri="modis_temiz", strict=True):
    import calendar
    p = pd.Period(f"{y}-{m:02d}")
    i0, i1 = v.idx(p.start_time), v.idx((p + 1).start_time)
    return v.seri(seri, i0, i1, calendar.monthrange(y, m)[1], strict)


# ------------------------------------------------------------ C06 kanıtı
def test_kesinti_gunleri_paydadan_cikar():
    """10 gün kesinti: düzeltmeli ay = gerçek günlük oran × 31; düzeltmesiz ham daha düşük."""
    kes = pd.date_range("2004-07-05", periods=10)
    v = _sentetik(kes)
    val, inf = _ay(v, 2004, 7)
    assert abs(val[0] - 2 * 31) < 1e-9, val
    assert abs(inf["kesinti"] - 10 / 31) < 1e-12
    assert v.ham("modis_temiz", v.idx("2004-07-01"), v.idx("2004-08-01"))[0] == 2 * 21   # düzeltmesiz
    # kesintisiz kontrol ayı aynı değer
    assert abs(_ay(v, 2004, 6)[0][0] - 2 * 30) < 1e-9


def test_cok_kesintili_ay_bos_sifir_degil():
    kes = pd.date_range("2004-07-01", periods=20)      # 20/31 > eşik
    v = _sentetik(kes)
    val, _ = _ay(v, 2004, 7)
    assert np.isnan(val[0])
    assert v.ham("modis_temiz", v.idx("2004-07-01"), v.idx("2004-08-01"))[0] == 2 * 11


def test_medyandan_cikar():
    """Boş (NaN) ay hücresi medyanı sıfıra çekmemeli."""
    kes = pd.date_range("2004-07-01", periods=20)
    v = _sentetik(kes)
    vals = [_ay(v, y, 7)[0][0] for y in (2003, 2004, 2005)]
    assert np.isnan(vals[1]) and abs(np.nanmedian(vals) - 62) < 1e-9


def test_kapsamsiz_donem_bos():
    v = _sentetik()
    val, _ = v.seri("viirs_ham_ub", 0, 31, 31, True)          # VIIRS hiç işlemiyor
    assert np.isnan(val[0])
    assert np.isnan(v.ham("viirs_ham", 0, 31)[0])


def test_kisi_ay_bos():
    v = _sentetik(bas="2003-01-01", bit="2005-11-12")
    val, _ = _ay(v, 2005, 11)                                 # veri 12. günde bitiyor
    assert np.isnan(val[0])


def test_aralik_sorgu_ay_hucresiyle_tutarli():
    v = _sentetik(pd.date_range("2004-07-05", periods=10))
    r = Q.aralik_analiz(v, "TR", "modis_temiz", "2004-07-01", "2004-07-31")
    assert abs(r["deger"] - _ay(v, 2004, 7)[0][0]) < 1e-9
    assert r["n_yil"] == 2 and "yetersiz_yil" not in r["uyari"]


def test_test_yili_normalden_haric():
    v = _sentetik()
    r = Q.aralik_analiz(v, "TR", "modis_temiz", "2004-07-01", "2004-07-31", test_yil=2004)
    assert r["n_yil"] == 2                                     # 2003 ve 2005; 2004 hariç (K4)


def test_az_yil_uyarisi():
    v = _sentetik(bas="2003-01-01", bit="2004-12-31")
    v.yil_bilgi = v.yil_bilgi.loc[[2003, 2004]]
    r = Q.aralik_analiz(v, "TR", "modis_temiz", "2004-07-01", "2004-07-31")
    assert r["n_yil"] == 1 and "yetersiz_yil" in r["uyari"] and np.isnan(r["medyan"])


def test_harmonized_yeni_sema():
    """harmonized'da birim/kume varsa tespit+temiz ana seridir; eski şema da çalışır."""
    import build_monthly as B
    rows = []
    for b, k, val in (("tespit", "temiz", 10), ("tespit", "temiz_aniz", 20), ("olay", "temiz", 5)):
        rows.append({"duzey": "ay_TR", "yil": 2010, "ay": 1, "bolge7": "TR", "ana_seri": val, "ana_alt": val - 1,
                     "ana_ust": val + 1, "ana_kaynak": "x", "bayrak": "", "birim": b, "kume": k})
    old = pd.read_parquet
    try:
        pd.read_parquet = lambda *a, **k: pd.DataFrame(rows)
        h = B.harm_oku()
    finally:
        pd.read_parquet = old
    assert h["modis_esdeger"].loc[("TR", 2010, 1), "ana_seri"] == 10
    assert h["modis_esdeger_aniz_dahil"].loc[("TR", 2010, 1), "ana_seri"] == 20
    assert h["olay_esdeger"].loc[("TR", 2010, 1), "ana_seri"] == 5


# ------------------------------------------------------------ gerçek veri
def _gerek(*paths):
    return all(Path(p).exists() for p in paths)


def test_il_toplami_TR_ve_ay_yil():
    if not _gerek(C.MONTHLY):
        return
    m = pd.read_parquet(C.MONTHLY)
    il = m[m.duzey == "il"].groupby(["yil", "ay"])[C.COLS_RAW].sum(min_count=1)
    tr = m[m.birim == "TR"].set_index(["yil", "ay"])[C.COLS_RAW]
    assert np.allclose(il.fillna(-1).to_numpy(), tr.reindex(il.index).fillna(-1).to_numpy())
    bol = m[m.duzey == "bolge"].groupby(["yil", "ay"])[C.COLS_RAW].sum(min_count=1)
    assert np.allclose(bol.fillna(-1).to_numpy(), tr.reindex(bol.index).fillna(-1).to_numpy())
    # ay toplamı = yıl toplamı (ham)
    yil = m[m.birim == "TR"].groupby("yil")["modis_ham"].sum()
    p = pd.read_parquet(C.POINTS, columns=["day_tr", "sensor"])
    py = p[p.sensor.astype(str).eq("MODIS")].groupby(pd.to_datetime(p["day_tr"]).dt.year).size()
    assert (yil.reindex(py.index) == py).all()


def test_olay_toplami_ve_status():
    if not _gerek(C.MONTHLY, C.EVENTS):
        return
    e = pd.read_parquet(C.EVENTS, columns=["status"])
    m = pd.read_parquet(C.MONTHLY)
    tr = m[m.birim == "TR"]
    assert int(tr["olay"].sum()) == int((e.status == "temiz").sum())
    assert int(tr["olay_aniz"].sum()) == int((e.status == "aniz").sum())
    assert int(tr["olay"].sum() + tr["olay_aniz"].sum()) <= len(e)


def test_ay_siniri_TR_UTC():
    """20:59Z ve 21:00Z: TR ay/yıl sınırı. Bağımsız hesap: (t_utc+3h) ayı = aylık tablodaki ay."""
    if not _gerek(C.MONTHLY, C.POINTS):
        return
    p = pd.read_parquet(C.POINTS, columns=["t_utc", "sensor"])
    p = p[p.sensor.astype(str).eq("MODIS")]
    tr = (p["t_utc"].dt.tz_convert("UTC") + pd.Timedelta(hours=timeutil.TR_OFFSET_HOURS))
    g = p.groupby([tr.dt.year, tr.dt.month]).size()
    m = pd.read_parquet(C.MONTHLY)
    m = m[m.birim == "TR"].set_index(["yil", "ay"])["modis_ham"]
    assert (m.reindex(g.index) == g.to_numpy()).all()
    # 2025-12-31 21:00Z TR'de 2026-01-01'dir (yıl kırpılmaz, K11)
    assert timeutil.tr_day(pd.Timestamp("2025-12-31T21:00Z")) == pd.Timestamp("2026-01-01").date()
    assert timeutil.tr_day(pd.Timestamp("2025-12-31T20:59Z")) == pd.Timestamp("2025-12-31").date()


def test_eksik_yil_2026_bos_ve_kismi():
    if not _gerek(C.MONTHLY):
        return
    m = pd.read_parquet(C.MONTHLY)
    t = m[(m.birim == "TR") & (m.yil == 2026)]
    son = t.sort_values("ay").iloc[-1]
    assert "kismi_ay" in son["bayrak"] and np.isnan(son["modis_ham_kk"])          # düzeltmeli değer boş
    v = m[(m.birim == "TR") & (m.yil < 2012)]
    assert v["viirs_ham"].isna().all() and v["viirs_ham_kk"].isna().all()         # VIIRS öncesi sıfır değil boş


def test_sifir_veri_il_sifir_ama_bos_degil():
    """Gözlenen ayda tespiti olmayan il: 0 (gözlendi, tespit yok); sensör yokken NaN."""
    if not _gerek(C.MONTHLY):
        return
    m = pd.read_parquet(C.MONTHLY)
    x = m[(m.duzey == "il") & (m.yil == 2020) & (m.modis_ham == 0)]
    assert len(x) and x["modis_ham_kk"].eq(0).all()


def test_normal_yillar_test_yilini_icermez():
    if not _gerek(C.ANOMALI):
        return
    a = pd.read_parquet(C.ANOMALI)
    s = a[(a.birim == "TR") & (a.seri == "modis_ham") & (a.ay == 7)]
    sl = pd.read_parquet(C.SERI_AYLIK)
    z = sl[(sl.birim == "TR") & (sl.seri == "modis_ham") & (sl.ay == 7) & sl.normal_yil]
    yr = int(z["yil"].iloc[5])
    base = z[z.yil != yr]["deger"].to_numpy()
    r = s[s.yil == yr].iloc[0]
    assert abs(r["normal_medyan"] - np.median(base)) < 1e-6 and r["n_normal_yil"] == len(base)


def test_risk_kelimesi_yok():
    bad = []
    for f in Path(__file__).parent.glob("*.py"):
        if f.name == "test_analytics.py":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if "risk" in line.lower() and "K14" not in line:
                bad.append(f"{f.name}:{i}")
    assert not bad, bad


if __name__ == "__main__":
    fails = 0
    tests = [(k, f) for k, f in sorted(globals().items()) if k.startswith("test_") and callable(f)]
    for k, f in tests:
        try:
            f()
            print("OK  ", k)
        except Exception:
            fails += 1
            print("FAIL", k)
            traceback.print_exc()
    print(f"{len(tests) - fails}/{len(tests)} geçti")
    sys.exit(1 if fails else 0)
