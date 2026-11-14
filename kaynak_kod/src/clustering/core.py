"""Olay kümelemesi çekirdeği (U-10, U-11; C03).

Basitçe: Uydular aynı yangını defalarca "fotoğraflar". Bu modül, birbirine yakın (mesafe)
ve zamanca yakın (boşluk) fotoğrafları aynı yangın sayar. A ile B yakınsa, B ile C yakınsa
A, B, C aynı olaydır (zincirleme). İki sensör (MODIS ve VIIRS) birlikte kümelenir; böylece
aynı yangın iki kez sayılmaz.

Teknik olarak:
- Bağlantı kuralı (çift i, j):
    uzay:  d(i,j) <= D  VEYA  (eslestirme_modu'na göre) piksel ayak izi örtüşmesi
           d: dy = Δenlem·k, dx = |Δboylam|(±180 sarmalı)·k·cos(ortalama enlem), k = km_derece
           (../demo/app.js cluster() ile aynı metrik).
           ayakizi_capraz: MODIS–VIIRS çiftinde |dx| <= scan_M/2 + b ve |dy| <= track_M/2 + b
           ayakizi_tum:    ek olarak MODIS–MODIS: |dx| <= (scan_i+scan_j)/2, |dy| <= (track_i+track_j)/2
    zaman: sabit -> |Δt| <= H saat
           gecis -> |Δt| <= Hmax saat VE arada tamamen kalan GÖZLENMİŞ geçiş penceresi sayısı <= L
- Olay = bağlantı grafiğinin bağlı bileşeni (union-find / connected_components; demo ile aynı
  zincirleme anlamı).
- Hızlı yöntem: ızgara (hücre >= en büyük bağlantı mesafesi) + hücre içinde zamana göre sıralı
  dizide ikili arama ile aday çiftler; yalnız yarım komşuluk (5 ofset) taranır, her çift bir kez.
  Kesin yüklem aday çiftlere uygulanır. Kaba kuvvet eşdeğerliği bruteforce_check.py ile sınanır.
- Olay kimliği kanoniktir: olaylar ilk tespitlerinin (t_utc, pid) sırasına göre 0..n-1
  numaralanır; yöntemden bağımsızdır.
Kaynak: ızgara + union-find fikri ../demo/app.js cluster() (K7: demo değiştirilmedi).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from config import config as cfg  # noqa: E402
from pipeline.timeutil import TR_OFFSET_HOURS  # noqa: E402  (K11: TR günü tek tanım)

TR_OFFSET_MIN = TR_OFFSET_HOURS * 60

POINTS = ROOT / "data" / "processed" / "points.parquet"
COVERAGE = ROOT / "data" / "processed" / "coverage.parquet"
EXCLUDE_TYPES = (1, 3)          # volkan, açık deniz: kümelenmez (docs/F2_ORTAK.md)
MODIS_SATS = ("Terra", "Aqua")
# Geçiş pencere grupları: Aqua ve üç VIIRS uydusu aynı ~13:30/01:30 yörüngesinde (veride ölçüldü)
WINDOW_GROUPS = {"Terra": ("Terra",), "AV": ("Aqua", "SNPP", "N20", "N21")}
COLS = ["pid", "t_utc", "lat", "lon", "sensor", "sat", "scan", "track", "frp", "type",
        "day_tr", "dn", "il", "conf_cls"]


def era_bounds(p: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Dönem sınırları veriden ölçülür: ilk Aqua tespiti (Terra+Aqua dönemi) ve ilk VIIRS tespiti."""
    return (p.loc[p["sat"] == "Aqua", "t_utc"].min(), p.loc[p["sensor"] == "VIIRS", "t_utc"].min())


def kcfg(name):
    return cfg.load()["kumeleme"][name]


@dataclass(frozen=True)
class Rule:
    D: float                      # km
    H: float                      # saat (sabit kural)
    mode: str = "sabit"           # sabit | ayakizi_capraz | ayakizi_tum
    gap: str = "sabit"            # sabit | gecis
    L: int = 3                    # gecis: izin verilen boş gözlenmiş pencere
    Hmax: float = 72.0            # gecis: mutlak üst sınır (saat)
    buffer: float = 0.375         # km, VIIRS tamponu (eslesme_tamponu_km)
    km_deg: float = 111.0

    @property
    def tmax_min(self) -> int:
        return int(round((self.Hmax if self.gap == "gecis" else self.H) * 60))

    def label(self) -> str:
        g = f"H={self.H:g}" if self.gap == "sabit" else f"gecis L={self.L} Hmax={self.Hmax:g}"
        return f"D={self.D:g} {self.mode} {g}"


def default_rule(**over) -> Rule:
    r = Rule(D=float(cfg.esik("D")), H=float(cfg.esik("H")),
             mode=kcfg("eslestirme_modu")["value"], gap=kcfg("bosluk_kurali")["value"],
             L=int(kcfg("L")["value"]), Hmax=float(kcfg("Hmax")["value"]),
             buffer=float(cfg.esik("eslesme_tamponu_km")), km_deg=float(kcfg("km_derece")["value"]))
    return replace(r, **over)


# --------------------------------------------------------------------------- #
# Girdi
# --------------------------------------------------------------------------- #
STATUS = ROOT / "data" / "processed" / "points_status.parquet"
# Anız olay düzeyinde bir ETİKETTİR, olay yapısını değiştirmez (koordinatör kararı, döngü önleme):
# anız noktaları olaylarda kalır; events.status olay etiketini taşır.
CLUSTER_STATUSES = ("temiz", "aniz")
MCELL = ROOT / "data" / "processed" / "points_mcell.parquet"


def load_points(columns=COLS, only_clean: bool = True) -> pd.DataFrame:
    """Kümelemeye girecek noktalar, (t_utc, pid) sırasında.

    F2 ikinci adım (koordinatör kararı): girdi status ∈ CLUSTER_STATUSES ('temiz', 'aniz') noktalar
    (temizlik yan tablosu; anız olay etiketidir, kümeleme girdisinden çıkarılmaz). Temiz olmayanlar
    olay almaz (event_id = -1, sözleşme §2) ve zincire köprü olamaz. Yan tablo yoksa veya
    only_clean=False ise eski girdi: type ∉ {1,3} olan tüm noktalar.
    """
    p = pd.read_parquet(POINTS, columns=list(columns))
    p = p[~p["type"].isin(EXCLUDE_TYPES)]
    if only_clean and STATUS.exists():
        st = pd.read_parquet(STATUS, columns=["pid", "status"])
        p = p[p["pid"].isin(st.loc[st["status"].isin(CLUSTER_STATUSES), "pid"])]
    return p.sort_values(["t_utc", "pid"], kind="mergesort").reset_index(drop=True)


def minutes(t: pd.Series) -> np.ndarray:
    """UTC zaman damgası -> 1970'ten beri tam dakika (int64)."""
    return (t.dt.as_unit("s").astype("int64") // 60).to_numpy(np.int64)


# --------------------------------------------------------------------------- #
# Geçiş pencereleri (U-11)
# --------------------------------------------------------------------------- #
def build_windows(p: pd.DataFrame, cov: pd.DataFrame | None = None) -> dict:
    """Gözlenmiş geçiş pencereleri: {(grup, dn): (start_min[], end_min[])} sıralı, örtüşmesiz.

    Pencere saatleri her yıl, grup ve gündüz/gece için tespit saatlerinin yüzdeliklerinden
    ölçülür (tahmini; swath verisi yok). Bir UTC günündeki pencere, gruptaki uydulardan en az
    biri coverage.parquet'te o TR gününde observed=True ise vardır (yoksa "uydu geçmedi").
    """
    if cov is None:
        cov = pd.read_parquet(COVERAGE, columns=["sat", "day_tr", "observed"])
    lo_q, hi_q = kcfg("gecis_pencere_yuzdelik")["value"]
    t = p["t_utc"]
    mod = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    year = t.dt.year.to_numpy()
    obs = cov[cov["observed"]].copy()
    obs["day_tr"] = pd.to_datetime(obs["day_tr"])
    out = {}
    for g, sats in WINDOW_GROUPS.items():
        for dn in ("D", "N"):
            m = p["sat"].isin(sats).to_numpy() & (p["dn"] == dn).to_numpy()
            mm = mod[m].astype(np.int64)
            # Gece AV geçişi UTC gece yarısını keser (21:00-02:00): -720..720 aralığına kaydır.
            mm = np.where(mm >= 720, mm - 1440, mm) if (g == "AV" and dn == "N") else mm
            yy = year[m]
            ob_days = obs[obs["sat"].isin(sats)]["day_tr"].drop_duplicates()
            if not len(mm) or not len(ob_days):
                continue
            prof = (pd.DataFrame({"y": yy, "m": mm}).groupby("y")["m"]
                    .quantile([lo_q / 100, hi_q / 100]).unstack())
            prof.columns = ["lo", "hi"]
            # her UTC günü için pencere; gözlem günü: pencere merkezinin TR günü
            d0 = ob_days.min() - pd.Timedelta(days=1)
            d1 = ob_days.max() + pd.Timedelta(days=1)
            days = pd.date_range(d0, d1, freq="D")
            py = prof.reindex(days.year)
            py = py.ffill().bfill() if py.isna().any().any() else py  # profil olmayan yıla en yakın yıl
            base = (days.as_unit("s").asi8 // 60).astype(np.int64)
            lo = base + py["lo"].round().to_numpy().astype(np.int64)
            hi = base + py["hi"].round().to_numpy().astype(np.int64)
            center_tr_day = ((lo + hi) // 2 + TR_OFFSET_MIN) // 1440   # TR günü (gün sayısı)
            ob_num = (pd.DatetimeIndex(ob_days).as_unit("s").asi8 // 86400).astype(np.int64)
            keep = np.isin(center_tr_day, ob_num)
            lo, hi = lo[keep], hi[keep]
            assert np.all(lo[1:] > hi[:-1]), "pencereler örtüşmemeli"
            out[(g, dn)] = (lo, hi)
    return out


def window_index(tm: np.ndarray, windows: dict) -> tuple[np.ndarray, np.ndarray]:
    """Her nokta ve pencere türü için s=#(start <= t) ve e=#(end < t) (searchsorted)."""
    keys = sorted(windows)
    S = np.empty((len(keys), len(tm)), np.int32)
    E = np.empty((len(keys), len(tm)), np.int32)
    for k, key in enumerate(keys):
        lo, hi = windows[key]
        S[k] = np.searchsorted(lo, tm, "right")   # başı t'den <= olan pencere sayısı
        E[k] = np.searchsorted(hi, tm, "left")    # sonu t'den < olan pencere sayısı
    return S, E


def missed_windows(S, E, a, b, ta, tb) -> np.ndarray:
    """a ile b arasında tamamen kalan gözlenmiş pencere sayısı (a, b dizin dizileri)."""
    early = np.where(ta <= tb, a, b)
    late = np.where(ta <= tb, b, a)
    tot = np.zeros(len(a), np.int32)
    for k in range(S.shape[0]):
        tot += np.maximum(0, E[k, late] - S[k, early])
    return tot


# --------------------------------------------------------------------------- #
# Bağlantı yüklemi
# --------------------------------------------------------------------------- #
class Arrays:
    """Kümeleme için numpy dizileri (sıra: (t_utc, pid))."""

    def __init__(self, p: pd.DataFrame, windows: dict | None = None):
        self.n = len(p)
        self.pid = p["pid"].to_numpy(np.int64)
        self.t = minutes(p["t_utc"])
        self.lat = p["lat"].to_numpy(np.float64)
        self.lon = p["lon"].to_numpy(np.float64)
        self.modis = (p["sensor"] == "MODIS").to_numpy()
        self.scan = p["scan"].to_numpy(np.float64)
        self.track = p["track"].to_numpy(np.float64)
        self.S = self.E = None
        if windows is not None:
            self.S, self.E = window_index(self.t, windows)


def link(A: Arrays, r: Rule, i: np.ndarray, j: np.ndarray) -> np.ndarray:
    """Kesin bağlantı yüklemi (vektörel)."""
    dt = np.abs(A.t[i] - A.t[j])
    if r.gap == "sabit":
        ok_t = dt <= int(round(r.H * 60))
    else:
        ok_t = dt <= int(round(r.Hmax * 60))
        if ok_t.any():
            idx = np.flatnonzero(ok_t)
            ms = missed_windows(A.S, A.E, i[idx], j[idx], A.t[i[idx]], A.t[j[idx]])
            ok_t[idx] = ms <= r.L
    la, lb = A.lat[i], A.lat[j]
    dy = (la - lb) * r.km_deg
    dl = np.abs(A.lon[i] - A.lon[j]) % 360.0
    dl = np.where(dl > 180.0, 360.0 - dl, dl)
    dx = dl * r.km_deg * np.cos(np.radians((la + lb) / 2.0))
    ok_s = dx * dx + dy * dy <= r.D * r.D
    if r.mode != "sabit":
        mi, mj = A.modis[i], A.modis[j]
        cross = mi != mj
        m = np.where(mi, i, j)  # çaprazda MODIS olan
        fp = cross & (np.abs(dx) <= A.scan[m] / 2 + r.buffer) & (np.abs(dy) <= A.track[m] / 2 + r.buffer)
        if r.mode == "ayakizi_tum":
            mm = mi & mj
            fp |= mm & (np.abs(dx) <= (A.scan[i] + A.scan[j]) / 2) & (np.abs(dy) <= (A.track[i] + A.track[j]) / 2)
        ok_s |= fp
    return ok_t & ok_s


def max_reach_km(A: Arrays, r: Rule) -> float:
    """Herhangi bir bağlı çiftte |dx| ve |dy| için üst sınır (ızgara hücresi)."""
    c = r.D
    if r.mode != "sabit" and A.modis.any():
        c = max(c, A.scan[A.modis].max() / 2 + r.buffer, A.track[A.modis].max() / 2 + r.buffer)
        if r.mode == "ayakizi_tum":
            c = max(c, A.scan[A.modis].max(), A.track[A.modis].max())
    return float(c)


# --------------------------------------------------------------------------- #
# Hızlı kümeleme
# --------------------------------------------------------------------------- #
def candidate_edges(A: Arrays, r: Rule, chunk_pairs: int = 15_000_000):
    """Bağlı çiftleri (i, j) üretir (parça parça). i, j: A dizinleri."""
    n = A.n
    if n < 2:
        return
    lon_span = A.lon.max() - A.lon.min()
    assert lon_span < 180, "ızgara ±180° sarmasız varsayıyor (Türkiye); geniş alan için demo sarmalı ızgara gerekir"
    c = max_reach_km(A, r) * (1 + 1e-9) + 1e-9
    latmax = min(89.0, float(np.abs(A.lat).max()) + c / r.km_deg + 1e-6)
    row = np.floor(A.lat * r.km_deg / c).astype(np.int64)
    col = np.floor(A.lon * r.km_deg * np.cos(np.radians(latmax)) / c).astype(np.int64)
    row -= row.min()
    col -= col.min()
    ncol = int(col.max()) + 3
    key = (row + 1) * ncol + (col + 1)
    T = r.tmax_min
    t0 = A.t - A.t.min() + T
    span = int(t0.max()) + T + 1
    comp = key * span + t0
    order = np.argsort(comp, kind="mergesort")
    cs = comp[order]
    ks, ts = key[order], t0[order]
    pos = np.arange(n, dtype=np.int64)
    offsets = [(0, 0), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in offsets:
        tk = ks + dr * ncol + dc
        hi = np.searchsorted(cs, tk * span + ts + T, "right")
        lo = pos + 1 if (dr, dc) == (0, 0) else np.searchsorted(cs, tk * span + ts - T, "left")
        cnt = np.maximum(hi - lo, 0)
        cum = np.cumsum(cnt)
        start = 0
        while start < n:
            base = cum[start - 1] if start else 0
            stop = int(np.searchsorted(cum, base + chunk_pairs, "right"))
            stop = max(stop, start + 1)
            cc = cnt[start:stop]
            tot = int(cc.sum())
            if tot:
                ii = np.repeat(pos[start:stop], cc)
                off = np.arange(tot, dtype=np.int64) - np.repeat(np.cumsum(cc) - cc, cc)
                jj = np.repeat(lo[start:stop], cc) + off
                a, b = order[ii], order[jj]
                keep = link(A, r, a, b)
                if keep.any():
                    yield a[keep], b[keep]
            start = stop


def components(n: int, edge_iter) -> np.ndarray:
    """Kenarlardan bağlı bileşen etiketi. Bellek için kenarlar ara ara yıldıza sıkıştırılır."""
    ea, eb, held = [], [], 0
    labels = None

    def compact(ea, eb):
        a = np.concatenate(ea) if ea else np.empty(0, np.int64)
        b = np.concatenate(eb) if eb else np.empty(0, np.int64)
        g = coo_matrix((np.ones(len(a), np.int8), (a, b)), shape=(n, n))
        _, lab = connected_components(g, directed=False)
        return lab

    for a, b in edge_iter:
        ea.append(a.astype(np.int64))
        eb.append(b.astype(np.int64))
        held += len(a)
        if held > 40_000_000:
            lab = compact(ea, eb)
            # yıldız: her düğüm -> bileşeninin ilk düğümü
            first = np.full(lab.max() + 1, -1, np.int64)
            idx = np.arange(n, dtype=np.int64)
            first[lab[::-1]] = idx[::-1]
            rep = first[lab]
            nz = rep != idx
            ea, eb, held = [idx[nz]], [rep[nz]], int(nz.sum())
    labels = compact(ea, eb)
    return labels


def canonical(labels: np.ndarray) -> np.ndarray:
    """Bileşen etiketlerini ilk elemanın (dizin = zaman sırası) sırasına göre 0..k-1 yap."""
    n = len(labels)
    first = np.full(labels.max() + 1, n, np.int64)
    np.minimum.at(first, labels, np.arange(n))
    rank = np.empty_like(first)
    rank[np.argsort(first, kind="mergesort")] = np.arange(len(first))
    return rank[labels]


def cluster(A: Arrays, r: Rule, mask: np.ndarray | None = None) -> np.ndarray:
    """Hızlı kümeleme. mask verilirse yalnız o noktalar (diğerleri -1). Dönen: kanonik olay no."""
    if r.gap == "gecis" and A.S is None:
        raise ValueError("gecis kuralı için Arrays(windows=...) gerekli")
    if mask is None:
        lab = canonical(components(A.n, candidate_edges(A, r)))
        return lab
    idx = np.flatnonzero(mask)
    sub = subset(A, idx)
    lab = canonical(components(sub.n, candidate_edges(sub, r)))
    out = np.full(A.n, -1, np.int64)
    out[idx] = lab
    return out


def subset(A: Arrays, idx: np.ndarray) -> Arrays:
    B = Arrays.__new__(Arrays)
    B.n = len(idx)
    for f in ("pid", "t", "lat", "lon", "modis", "scan", "track"):
        setattr(B, f, getattr(A, f)[idx])
    B.S = None if A.S is None else A.S[:, idx]
    B.E = None if A.E is None else A.E[:, idx]
    return B
