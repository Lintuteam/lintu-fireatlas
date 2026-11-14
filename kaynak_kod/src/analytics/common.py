"""Ortak yollar, eşikler ve seri tanımları (takvim-analiz).

Basitçe: Bütün takvim betiklerinin ortak "alet çantası": dosya yolları, eşikler (tek yerden, K9)
ve hangi "seri"nin neyi saydığının sözlüğü.

Teknik olarak: Seriler günlük tablodaki sütunlardan türetilir. Gruplar (kapsam ağırlığı için):
'modis' (Terra+Aqua), 'viirs' (SNPP+N20+N21), 'olay' (tüm uydular). `per_sat=True` olan seriler
VIIRS uydu sayısı değiştiği için "uydu başına" normalleştirilir (2012, 2018, 2023 geçişleri).
"Risk" terimi kullanılmaz (K14): burada hepsi "tarihsel hotspot aktivitesi"dir; yangın tehlikesi
tahmini değildir.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402

PROC = ROOT / "data" / "processed"
AGG = PROC / "agg"
POINTS = PROC / "points.parquet"
STATUS = PROC / "points_status.parquet"
EVENTS = PROC / "events.parquet"
COVERAGE = PROC / "coverage.parquet"
HARM = AGG / "harmonized.parquet"
DAILY = AGG / "daily.parquet"
KAPSAM = AGG / "daily_kapsam.parquet"
YIL_BILGI = AGG / "yil_bilgi.parquet"
MONTHLY = AGG / "monthly.parquet"
SERI_AYLIK = AGG / "seri_aylik.parquet"
PROFIL = AGG / "profile.parquet"
SIRALAMA = AGG / "ranking.parquet"
HAM_TEMIZ = AGG / "ranking_ham_temiz.parquet"
ANOMALI = AGG / "anomaly_monthly.parquet"
MEVCUT = AGG / "current_month.parquet"
PART = ROOT / "reports" / "metrics_parts" / "takvim_analiz.json"
VERI_SURUMU = "points v1"

COLS_RAW = ["modis_ham", "modis_temiz", "modis_aniz", "enerji_modis",
            "viirs_ham", "viirs_temiz", "viirs_aniz", "enerji_viirs", "olay", "olay_aniz"]
GRUP_KOL = {c: ("modis" if c.endswith("modis") or c.startswith("modis") else
                "viirs" if c.endswith("viirs") or c.startswith("viirs") else "olay")
            for c in COLS_RAW}

# ad: (sütunlar, grup, uydu_basina)
SERI = {
    "modis_ham": (["modis_ham"], "modis", False),
    "modis_temiz": (["modis_temiz"], "modis", False),
    "modis_temiz_aniz_dahil": (["modis_temiz", "modis_aniz"], "modis", False),
    "enerji_modis": (["enerji_modis"], "modis", False),
    "viirs_ham_ub": (["viirs_ham"], "viirs", True),
    "viirs_temiz_ub": (["viirs_temiz"], "viirs", True),
    "viirs_temiz_aniz_dahil_ub": (["viirs_temiz", "viirs_aniz"], "viirs", True),
    "enerji_viirs_ub": (["enerji_viirs"], "viirs", True),
    "olay": (["olay"], "olay", False),
    "olay_aniz_dahil": (["olay", "olay_aniz"], "olay", False),
}
ESDEGER = "modis_esdeger"
# harmonized.parquet (birim, kume) -> seri adı. Sütunlar yoksa (eski şema) yalnız tespit/temiz vardır.
ESDEGER_KAYNAK = {"modis_esdeger": ("tespit", "temiz"),
                  "modis_esdeger_aniz_dahil": ("tespit", "temiz_aniz"),
                  "olay_esdeger": ("olay", "temiz"),
                  "olay_esdeger_aniz_dahil": ("olay", "temiz_aniz")}
ESDEGER_SERILERI = tuple(ESDEGER_KAYNAK)
TUM_SERILER = list(SERI) + list(ESDEGER_SERILERI)


def is_esdeger(seri: str) -> bool:
    return seri in ESDEGER_KAYNAK
OLAY_SERILERI = ("olay", "olay_aniz_dahil")
# Sıralama ölçütü: sensör bileşimi yıllara göre değişen olay serisinde seviye değil ay payı
SIRALAMA_PAY = OLAY_SERILERI


def grup_of(seri: str) -> str:
    return "modis" if is_esdeger(seri) else SERI[seri][1]


def t(ad: str):
    return cfg.load()["takvim"][ad]["value"]
