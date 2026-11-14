"""Temizlik modülünün ortak yardımcıları.

Basitçe: Türkiye'yi yaklaşık 1 km'lik karelere (hücre) bölüyoruz. Her sıcak noktayı
düştüğü kareye yazıyoruz; sonra "bu kare kaç yıl, kaç farklı ayda, kaç gün yandı?"
diye soruyoruz. Bu dosya kareleri, il -> coğrafi bölge eşlemesini ve eşikleri okur.

Teknik olarak: hücre = floor(lat/R), floor(lon/R), R = esikler.json -> temizlik.hucre_derece.
Eşikler yalnız src/config/esikler.json'dan okunur (K9). Kod sabit eşik yazmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402

POINTS = ROOT / "data" / "processed" / "points.parquet"
PROCESSED = ROOT / "data" / "processed"
STATUS_OUT = PROCESSED / "points_status.parquet"
AUDIT = ROOT / "audit"
PART = ROOT / "reports" / "metrics_parts" / "temizlik.json"
VERI_SURUMU = "points v1"

# Türkiye'nin 7 coğrafi bölgesi (resmî coğrafi bölge ayrımı; il adları points.parquet'teki yazımla).
# Kaynak: Türkiye coğrafi bölgeleri (1941 Birinci Coğrafya Kongresi ayrımı), il bazına indirgenmiş.
# Not: Bölge sınırı il sınırını kesen iller (ör. Bilecik, Kütahya) tek bölgeye atanmıştır.
COGRAFI_BOLGE = {
    "Marmara": ["Balıkesir", "Bilecik", "Bursa", "Çanakkale", "Edirne", "İstanbul", "Kırklareli",
                "Kocaeli", "Sakarya", "Tekirdağ", "Yalova"],
    "Ege": ["Afyon", "Aydın", "Denizli", "İzmir", "Kütahya", "Manisa", "Muğla", "Uşak"],
    "Akdeniz": ["Adana", "Antalya", "Burdur", "Hatay", "Isparta", "Kahramanmaraş", "Mersin", "Osmaniye"],
    "İç Anadolu": ["Aksaray", "Ankara", "Çankırı", "Eskişehir", "Karaman", "Kayseri", "Kırıkkale",
                   "Kırşehir", "Konya", "Nevşehir", "Niğde", "Sivas", "Yozgat"],
    "Karadeniz": ["Amasya", "Artvin", "Bartın", "Bayburt", "Bolu", "Çorum", "Düzce", "Giresun",
                  "Gümüşhane", "Karabük", "Kastamonu", "Ordu", "Rize", "Samsun", "Sinop", "Tokat",
                  "Trabzon", "Zonguldak"],
    "Doğu Anadolu": ["Ağrı", "Ardahan", "Bingöl", "Bitlis", "Elazığ", "Erzincan", "Erzurum", "Hakkari",
                     "Iğdır", "Kars", "Malatya", "Muş", "Tunceli", "Van"],
    "Güneydoğu Anadolu": ["Adıyaman", "Batman", "Diyarbakır", "Gaziantep", "Kilis", "Mardin", "Siirt",
                          "Şanlıurfa", "Şırnak"],
}
IL_BOLGE = {il: b for b, iller in COGRAFI_BOLGE.items() for il in iller}


def t(ad: str):
    """temizlik.<ad> eşiğinin değeri."""
    return cfg.load()["temizlik"][ad]["value"]


def top(ad: str):
    """Üst düzey eşik (N, M, F, aniz_aylari)."""
    return cfg.esik(ad)


def load_points() -> pd.DataFrame:
    cols = ["pid", "t_utc", "day_tr", "lat", "lon", "sensor", "sat", "frp", "dn", "type",
            "src_product", "il", "bolge", "conf_cls"]
    df = pd.read_parquet(POINTS, columns=cols)
    R = float(t("hucre_derece"))
    ci = np.floor(df["lat"].to_numpy() / R).astype(np.int64)
    cj = np.floor(df["lon"].to_numpy() / R).astype(np.int64)
    df["ci"], df["cj"] = ci, cj
    df["cell"] = ci * 100_000 + cj
    d = pd.to_datetime(df["day_tr"])
    df["yr"] = d.dt.year.astype(np.int16)
    df["mon"] = d.dt.month.astype(np.int8)
    df["dayn"] = (d - pd.Timestamp("2000-01-01")).dt.days.astype(np.int32)
    df["cbolge"] = df["il"].map(IL_BOLGE).fillna("bilinmeyen")
    return df


def neighbors(cell: np.ndarray, k: int = 1) -> list[np.ndarray]:
    """(2k+1)^2 komşu hücre kimlikleri (kendisi dahil)."""
    out = []
    for di in range(-k, k + 1):
        for dj in range(-k, k + 1):
            out.append(cell + di * 100_000 + dj)
    return out


def prf(pred: np.ndarray, truth: np.ndarray) -> dict:
    pred, truth = np.asarray(pred, bool), np.asarray(truth, bool)
    tp = int((pred & truth).sum()); fp = int((pred & ~truth).sum()); fn = int((~pred & truth).sum())
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * p * r / (p + r) if (p + r) and not np.isnan(p + r) else float("nan")
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}
