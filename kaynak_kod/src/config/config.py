"""Eşik ve kodlama yapılandırması okuyucusu (K9, K10).

Basitçe: "Güven yüksek mi, düşük mü?" sorusunun cevabı projede TEK yerde yazılıdır
(esikler.json). Bu dosya o cetveli okur; başka hiçbir modül kendi cetvelini yazmaz.

Teknik olarak: guven_sinifi() (tek değer) ve guven_sinifi_seri() (vektörel) aynı JSON
tablosundan çalışır. Bilinmeyen değer `bilinmeyen_etiket` döner (sessizce atılmaz).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "esikler.json"


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def esik(ad: str):
    """Eşik değerini döndürür (ör. esik('N'))."""
    return load()[ad]["value"]


def guven_sinifi(sensor: str, raw) -> str:
    """conf_raw -> 'dusuk'/'nominal'/'yuksek' (bilinmeyen -> bilinmeyen_etiket)."""
    g = load()["guven"]
    bil = g["bilinmeyen_etiket"]
    try:
        if str(sensor).upper() == "MODIS":
            v = float(str(raw).strip())
            for s in g["MODIS"]["siniflar"]:
                if s["min"] <= v <= s["max"]:
                    return s["cls"]
            return bil
        return g["VIIRS"]["esleme"].get(str(raw).strip().lower(), bil)
    except (TypeError, ValueError):
        return bil


def guven_sinifi_seri(sensor, raw):
    """Vektörel sürüm: pandas Series (sensor, raw) -> Series. Aynı tablo."""
    import pandas as pd
    g = load()["guven"]
    bil = g["bilinmeyen_etiket"]
    sensor = pd.Series(sensor)
    raw = pd.Series(raw, index=sensor.index).astype("string").str.strip()
    out = pd.Series(bil, index=sensor.index, dtype=object)
    is_m = sensor.eq("MODIS")
    num = pd.to_numeric(raw.where(is_m), errors="coerce")
    for s in g["MODIS"]["siniflar"]:
        out[is_m & (num >= s["min"]) & (num <= s["max"])] = s["cls"]
    is_v = ~is_m
    low = raw.str.lower()
    for k, cls in g["VIIRS"]["esleme"].items():
        out[is_v & low.eq(k)] = cls
    return out


def ogrenilen_guven_sinifi_seri(sensor, raw):
    """ÖĞRENİLMİŞ ortak güven dili (S1/U-01; harmonizasyon ajanı, yıl dışarıda bırakmayla).

    Basitçe: FIRMS'in MODIS cetveli (0-29/30-79/80-100) ham sınıftır (`conf_cls`). Bu işlev ayrı
    bir sütun (`conf_cls_ogr`) üretir: MODIS yüzdesini, aynı yangına aynı anda bakan VIIRS'in
    l/n/h oranlarına göre yeniden keser. VIIRS sınıfı olduğu gibi kalır (ortak dilin referansı).
    Tablo `esikler.json -> harmonizasyon.ogrenilen_guven_esleme`; boşsa bilinmeyen_etiket döner.
    """
    import pandas as pd
    g = load()["guven"]
    bil = g["bilinmeyen_etiket"]
    tab = load().get("harmonizasyon", {}).get("ogrenilen_guven_esleme")
    sensor = pd.Series(sensor)
    raw = pd.Series(raw, index=sensor.index).astype("string").str.strip()
    out = pd.Series(bil, index=sensor.index, dtype=object)
    if not tab:
        return out
    is_m = sensor.eq("MODIS")
    num = pd.to_numeric(raw.where(is_m), errors="coerce")
    for s in tab["MODIS"]["siniflar"]:
        out[is_m & (num >= s["min"]) & (num <= s["max"])] = s["cls"]
    is_v = ~is_m
    low = raw.str.lower()
    for k, cls in g["VIIRS"]["esleme"].items():
        out[is_v & low.eq(k)] = cls
    return out


def uydu_kodu(ad: str) -> str:
    u = load()["uydu_kodlari"]
    return u["esleme"].get(ad, u["bilinmeyen_etiket"])
