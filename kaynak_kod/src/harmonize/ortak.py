"""Harmonizasyon ortak yardımcıları: yollar, eşikler, bölge ve mevsim.

Basitçe: Bütün harmonizasyon betiklerinin kullandığı "alet çantası". Türkiye'yi 7 coğrafi
bölgeye, yılı 4 mevsime ayırır; eşikleri tek yerden (esikler.json) okur.

Teknik olarak: Eşikler `src/config/esikler.json -> harmonizasyon` bölümünden okunur (K9).
İl -> coğrafi bölge eşlemesi geleneksel 7 bölge ayrımıdır (1941 Coğrafya Kongresi; il,
topraklarının çoğunun bulunduğu bölgeye atanır). Bu eşleme bir eşik değil, sabit bir sözlüktür.
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
COVERAGE = ROOT / "data" / "processed" / "coverage.parquet"
OUT_MCELL = ROOT / "data" / "processed" / "points_mcell.parquet"
POINTS_STATUS = ROOT / "data" / "processed" / "points_status.parquet"
POINTS_EVENT = ROOT / "data" / "processed" / "points_event.parquet"
EVENTS = ROOT / "data" / "processed" / "events.parquet"
AGG = ROOT / "data" / "processed" / "agg"
OUT_HARM = AGG / "harmonized.parquet"
INTERIM = ROOT / "data" / "interim" / "harmonize"
PART = ROOT / "reports" / "metrics_parts" / "harmonizasyon.json"
VERI_SURUMU = "points v1"
KM_PER_DEG = 111.32
VIIRS_SATS = ["SNPP", "N20", "N21"]
MODIS_SATS = ["Terra", "Aqua"]


def h(ad: str):
    """harmonizasyon bölümündeki eşiğin değeri."""
    return cfg.load()["harmonizasyon"][ad]["value"]


def tampon_km() -> float:
    return float(cfg.esik("eslesme_tamponu_km"))


BOLGE7 = {
    "Marmara": ["Edirne", "Kırklareli", "Tekirdağ", "İstanbul", "Kocaeli", "Yalova", "Sakarya",
                "Bilecik", "Bursa", "Balıkesir", "Çanakkale"],
    "Ege": ["İzmir", "Manisa", "Aydın", "Denizli", "Muğla", "Afyon", "Kütahya", "Uşak"],
    "Akdeniz": ["Antalya", "Isparta", "Burdur", "Mersin", "Adana", "Hatay", "Osmaniye",
                "Kahramanmaraş"],
    "IcAnadolu": ["Ankara", "Konya", "Kayseri", "Eskişehir", "Sivas", "Kırıkkale", "Aksaray",
                  "Karaman", "Kırşehir", "Niğde", "Nevşehir", "Yozgat", "Çankırı"],
    "Karadeniz": ["Rize", "Trabzon", "Artvin", "Sinop", "Tokat", "Çorum", "Kastamonu", "Samsun",
                  "Zonguldak", "Ordu", "Düzce", "Bolu", "Amasya", "Bartın", "Karabük", "Giresun",
                  "Gümüşhane", "Bayburt"],
    "DoguAnadolu": ["Erzurum", "Malatya", "Elazığ", "Van", "Kars", "Ağrı", "Muş", "Bitlis",
                    "Bingöl", "Tunceli", "Erzincan", "Hakkari", "Ardahan", "Iğdır"],
    "Guneydogu": ["Gaziantep", "Diyarbakır", "Şanlıurfa", "Mardin", "Batman", "Siirt", "Şırnak",
                  "Adıyaman", "Kilis"],
}
IL_BOLGE = {il: b for b, ils in BOLGE7.items() for il in ils}
MEVSIM = {12: "kis", 1: "kis", 2: "kis", 3: "ilkbahar", 4: "ilkbahar", 5: "ilkbahar",
          6: "yaz", 7: "yaz", 8: "yaz", 9: "sonbahar", 10: "sonbahar", 11: "sonbahar"}


def load_points() -> pd.DataFrame:
    cols = ["pid", "t_utc", "day_tr", "src_year", "lat", "lon", "sensor", "sat", "frp", "scan",
            "track", "conf_raw", "conf_cls", "dn", "type", "il"]
    p = pd.read_parquet(POINTS, columns=cols)
    p["bolge7"] = p["il"].map(IL_BOLGE).fillna("bilinmeyen")
    d = pd.to_datetime(p["day_tr"])
    p["ay"] = d.dt.month.astype("int8")
    p["yil"] = d.dt.year.astype("int16")   # TR günü yılı (K11); src_year ile aynı (ölçüldü: fark 0)
    p["mevsim"] = p["ay"].map(MEVSIM)
    return p


KUMELER = {"temiz": ["temiz"], "temiz_aniz": ["temiz", "aniz"]}


def analiz_kumesi(p: pd.DataFrame, kume: str = "temiz") -> pd.Series:
    """Sayım/kalibrasyon için kullanılan noktalar (temizlik ajanının `status` etiketi).
    Varsayılan 'temiz' (anız hariç); ikinci varyant 'temiz_aniz'. Hiçbir nokta silinmez, yalnız
    bu hesapta kullanılmaz (K3). İlk teslimde type 0/-1 süzgeci kullanılmıştı (belge §8)."""
    if "status" not in p:
        st = pd.read_parquet(POINTS_STATUS, columns=["pid", "status"])
        p["status"] = p["pid"].map(st.set_index("pid")["status"]).astype(str)
    return p["status"].isin(KUMELER[kume])


def km_xy(lat, lon, lat0: float = 39.0):
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    return lon * KM_PER_DEG * np.cos(np.radians(lat0)), lat * KM_PER_DEG


def metrik(value, unit, tanim, betik, etiket="ölçüldü"):
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    return {"value": value, "unit": unit, "tanim": tanim, "betik": betik,
            "veri_surumu": VERI_SURUMU, "etiket": etiket}


def json_yaz(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=_conv), encoding="utf-8")


def _conv(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))
