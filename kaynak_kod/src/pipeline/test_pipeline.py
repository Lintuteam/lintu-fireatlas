"""F1 veri hattı sağlamlık testleri (düz assert; pytest varsa da çalışır).

Basitçe: Hattın en kırılgan yerlerini (gün sınırı, yıl kırpma, güven cetveli, bilinmeyen uydu,
satır kaybı) küçük örneklerle ve gerçek çıktı dosyasıyla sınar.
Çalıştırma: python src/pipeline/test_pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402
from pipeline import build_points, timeutil  # noqa: E402

POINTS = ROOT / "data" / "processed" / "points.parquet"
INV = ROOT / "data" / "processed" / "inventory.json"


def _mini(**over):
    base = {"acq_datetime_utc": ["2025-12-31T21:00:00Z"], "latitude": [39.9], "longitude": [32.8],
            "sensor": ["MODIS"], "satellite": ["Terra"], "satellite_raw": ["Terra"], "frp_mw": [5.0],
            "scan_km": [1.0], "track_km": [1.0], "pixel_area_km2": [1.0], "confidence_raw": ["50"],
            "confidence_cls": ["nominal"], "bt_mir_k": [300.0], "bt_mir_band": ["MODIS_21_22"],
            "bt_tir_k": [290.0], "bt_tir_band": ["MODIS_31"], "daynight": ["D"], "type": [0.0],
            "version": ["6.2"], "source_file": ["x.csv"], "_file": ["FIRMS_Turkiye_2025.xlsx"]}
    base.update(over)
    return pd.DataFrame(base)


def test_tr_gun_siniri():
    a = timeutil.tr_day(pd.Timestamp("2025-06-30T20:59:00Z"))
    b = timeutil.tr_day(pd.Timestamp("2025-06-30T21:00:00Z"))
    assert str(a) == "2025-06-30" and str(b) == "2025-07-01"
    s = timeutil.tr_day(pd.Series(pd.to_datetime(["2025-06-30T20:59:00Z", "2025-06-30T21:00:00Z"], utc=True)))
    assert [str(x) for x in s] == ["2025-06-30", "2025-07-01"]


def test_yil_kirpilmaz():
    # UTC 31 Aralık 21:00 -> TR günü 1 Ocak, ama dosya yılı (src_year) 2025 kalır (K11)
    df, _ = build_points.build(_mini())
    assert int(df.loc[0, "src_year"]) == 2025
    assert str(df.loc[0, "day_tr"]) == "2026-01-01"
    assert str(df.loc[0, "t_utc"].year) == "2025"


def test_guven_sinirlari():
    for v, exp in [(0, "dusuk"), (29, "dusuk"), (30, "nominal"), (79, "nominal"), (80, "yuksek"), (100, "yuksek")]:
        assert cfg.guven_sinifi("MODIS", str(v)) == exp, v
    assert cfg.guven_sinifi("VIIRS", "l") == "dusuk"
    assert cfg.guven_sinifi("VIIRS", "n") == "nominal"
    assert cfg.guven_sinifi("VIIRS", "h") == "yuksek"
    assert cfg.guven_sinifi("MODIS", "101") == "bilinmeyen"
    assert cfg.guven_sinifi("VIIRS", "x") == "bilinmeyen"
    s = cfg.guven_sinifi_seri(pd.Series(["MODIS", "MODIS", "VIIRS", "VIIRS"]), pd.Series(["29", "80", "l", "q"]))
    assert list(s) == ["dusuk", "yuksek", "dusuk", "bilinmeyen"]


def test_bilinmeyen_uydu_sayilir_atilmaz():
    raw = pd.concat([_mini(), _mini(satellite=["UFO-1"])], ignore_index=True)
    df, rep = build_points.build(raw)
    assert len(df) == 2                       # satır atılmadı
    assert rep["bilinmeyen_uydu_satir"] == 1  # sayıldı
    assert "UFO-1" in rep["bilinmeyen_uydu_adlari"]
    assert df["sat"].tolist() == ["Terra", "bilinmeyen"]


def test_satir_sayisi_korunur():
    assert POINTS.exists(), "önce build_points.py çalıştırılmalı"
    n = len(pd.read_parquet(POINTS, columns=["pid"]))
    exp = json.loads(INV.read_text(encoding="utf-8"))["raw_rows_total"]
    assert n == exp, (n, exp)


def test_pid_tekil_ve_utc():
    p = pd.read_parquet(POINTS, columns=["pid", "t_utc", "sat"])
    assert p["pid"].is_unique
    assert str(p["t_utc"].dtype).endswith("UTC]")
    assert set(p["sat"].unique()) <= {"Terra", "Aqua", "SNPP", "N20", "N21"}


def test_pid_ham_xlsx_satirina_karsilik_gelir():
    """pid = yıl*10^7 + dosya-içi satır sırası; ham xlsx'i openpyxl ile doğrudan okuyup sınar (F1-07).

    Basitçe: Satır numarası kimliğin parçası. Önbellek sırası değişirse kimlikler sessizce kayar;
    bu test iki yıldan örnek satırı ham Excel'deki aynı satırla karşılaştırıp bunu yakalar.
    """
    import openpyxl
    raw_dir = ROOT / "data" / "raw" / "FIRMS_Turkiye_Excel"
    for yr in (2005, 2012):  # MODIS dönemi ve VIIRS'in ilk yılı
        wb = openpyxl.load_workbook(raw_dir / f"FIRMS_Turkiye_{yr}.xlsx", read_only=True, data_only=True)
        it = wb.worksheets[0].iter_rows(values_only=True)
        hdr = list(next(it))
        rows = [dict(zip(hdr, r)) for r in it if r is not None and not all(v is None for v in r)]
        wb.close()
        n = len(rows)
        p = pd.read_parquet(POINTS, filters=[("src_year", "==", yr)])
        assert len(p) == n, (yr, len(p), n)
        p = p.set_index("pid")
        for k in sorted({0, 1, n // 2, n - 2, n - 1}):
            r, q = rows[k], p.loc[yr * 10_000_000 + k]
            assert pd.Timestamp(r["acq_datetime_utc"]) == q["t_utc"], (yr, k)
            assert abs(float(r["latitude"]) - q["lat"]) < 1e-9 and abs(float(r["longitude"]) - q["lon"]) < 1e-9, (yr, k)
            assert abs(float(r["frp_mw"]) - float(q["frp"])) < 1e-3, (yr, k)
            assert str(r["source_file"]) == q["src_file"], (yr, k)
            assert cfg.uydu_kodu(str(r["satellite"])) == q["sat"], (yr, k)


def test_bolge_tutarli():
    p = pd.read_parquet(POINTS, columns=["il", "bolge"])
    assert set(p["bolge"].astype(str).unique()) <= {"il", "kiyi", "yurt_disi"}
    assert (p.loc[p["bolge"] == "yurt_disi", "il"] == "(yurt dışı)").all()
    assert (p.loc[p["bolge"] != "yurt_disi", "il"] != "(yurt dışı)").all()


def test_kesinti_snpp_2022():
    cov = pd.read_parquet(ROOT / "data" / "processed" / "coverage.parquet")
    c = cov[(cov["sat"] == "SNPP") & (pd.to_datetime(cov["day_tr"]).between("2022-07-27", "2022-08-10"))]
    assert len(c) == 15 and (~c["observed"]).all() and (c["source"] == "çıkarım_kesinti").all()
    assert (cov["etiket"] == "tahmini").all()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("OK ", f.__name__)
    print(f"{len(fns)} test geçti")
