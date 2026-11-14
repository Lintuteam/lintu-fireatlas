"""C03: hızlı kümeleme = kaba kuvvet bölümlemesi (örneklemde fark 0). Başarıda çıkış kodu 0.

Basitçe: Hızlı yöntem "yalnız yakın kutulara bakarak" kısa yol kullanır. Kaba kuvvet ise
her noktayı her noktayla tek tek karşılaştırır (yavaş ama şaşmaz). İkisi aynı gruplamayı
vermiyorsa kısa yolda hata var demektir.

Teknik olarak: 20 yıllık veriden il × zaman penceresi örneklemleri (yoğun ve seyrek, her dönem:
yalnız Terra, Terra+Aqua, MODIS+VIIRS) alınır. Her örneklemde ve her kural varyantında
(sabit / ayakizi_capraz / ayakizi_tum; sabit H / gecis; farklı D) tüm n² çift bu dosyadaki
BAĞIMSIZ yazılmış yüklemle değerlendirilir, bağlı bileşenler alınır ve iki bölümleme
kanonik etiketle karşılaştırılır. Ayrıca: (1) 20 yıllık tam veri kümelemesinin, olay-kapalı
örneklemlerle (seçili olayların tüm noktaları) kısıtı kaba kuvvetle aynı mı; (2) parça
büyüklüğü (chunk) sonucu değiştiriyor mu; (3) mutasyon: kasten bozulmuş hızlı yöntem
yakalanıyor mu (testin gücü).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from clustering import core  # noqa: E402

SEED = 20261113


def brute_link_block(A, r, i0, i1):
    """[i0, i1) satırlarını tüm j > i ile karşılaştır (bağımsız yazım)."""
    n = A.n
    I = np.arange(i0, i1)[:, None]
    J = np.arange(n)[None, :]
    upper = J > I
    lat1, lat2 = A.lat[I], A.lat[J]
    lon1, lon2 = A.lon[I], A.lon[J]
    dy = (lat1 - lat2) * r.km_deg
    dlon = np.abs(lon1 - lon2) % 360.0
    dlon = np.where(dlon > 180.0, 360.0 - dlon, dlon)
    dx = dlon * r.km_deg * np.cos(np.radians((lat1 + lat2) / 2.0))
    space = dx * dx + dy * dy <= r.D * r.D
    if r.mode in ("ayakizi_capraz", "ayakizi_tum"):
        m1, m2 = A.modis[I], A.modis[J]
        sx = np.where(m1, A.scan[I], A.scan[J])
        tx = np.where(m1, A.track[I], A.track[J])
        space = space | ((m1 ^ m2) & (np.abs(dx) <= sx / 2 + r.buffer) & (np.abs(dy) <= tx / 2 + r.buffer))
        if r.mode == "ayakizi_tum":
            space = space | ((m1 & m2) & (np.abs(dx) <= (A.scan[I] + A.scan[J]) / 2)
                             & (np.abs(dy) <= (A.track[I] + A.track[J]) / 2))
    t1, t2 = A.t[I], A.t[J]
    dt = np.abs(t1 - t2)
    if r.gap == "sabit":
        tim = dt <= int(round(r.H * 60))
    else:
        tim = dt <= int(round(r.Hmax * 60))
        # kaçırılan pencere: tamamen (min t, max t) içinde kalan gözlenmiş pencere
        ta, tb = np.minimum(t1, t2), np.maximum(t1, t2)
        miss = np.zeros(dt.shape, np.int32)
        for (lo, hi) in WINDOWS.values():
            sel = (lo >= A.t.min() - 10 * 1440) & (hi <= A.t.max() + 10 * 1440)
            for a, b in zip(lo[sel], hi[sel]):
                miss += ((a > ta) & (b < tb)).astype(np.int32)
        tim = tim & (miss <= r.L)
    ok = upper & space & tim
    ii, jj = np.nonzero(ok)
    return ii + i0, jj


def brute(A, r):
    ea, eb = [], []
    step = max(1, 4_000_000 // max(A.n, 1))
    for i0 in range(0, A.n, step):
        a, b = brute_link_block(A, r, i0, min(A.n, i0 + step))
        ea.append(a)
        eb.append(b)
    a = np.concatenate(ea) if ea else np.empty(0, int)
    b = np.concatenate(eb) if eb else np.empty(0, int)
    g = coo_matrix((np.ones(len(a), np.int8), (a, b)), shape=(A.n, A.n))
    return core.canonical(connected_components(g, directed=False)[1])


WINDOWS: dict = {}


def samples(p: pd.DataFrame, rng) -> list[tuple[str, np.ndarray]]:
    """(ad, dizin) örneklemleri: il × ay pencereleri, her dönemden, yoğun + rastgele."""
    out = []
    ym = p["t_utc"].dt.year * 100 + p["t_utc"].dt.month
    key = p["il"].astype(str) + "|" + ym.astype(str)
    size = key.value_counts()
    ok = size[(size >= 300) & (size <= 5000)]
    # dönem başına: en yoğun 2 + rastgele 2
    era = {k: int(k.split("|")[1][:4]) for k in ok.index}
    aq, vi = core.era_bounds(p)   # dönem sınırları veriden (sabit yıl yok)
    ymin, ymax = int(p["t_utc"].dt.year.min()), int(p["t_utc"].dt.year.max())
    eras = {"terra": (ymin, aq.year - 1), "modis": (aq.year + 1, vi.year - 1), "ortak": (vi.year, ymax)}
    for name, (y0, y1) in eras.items():
        ks = [k for k in ok.index if y0 <= era[k] <= y1]
        if not ks:
            continue
        pick = ks[:2] + list(rng.choice(ks, size=min(2, len(ks)), replace=False))
        for k in dict.fromkeys(pick):
            out.append((f"{name}:{k}", np.flatnonzero((key == k).to_numpy())))
    # en yoğun bölge × hafta (zincirleme/sanayi baskısı): 0,5° kare × 10 gün, 5000'i aşmayan en büyük
    cell = (np.floor(p["lat"] * 2).astype(int).astype(str) + "_" + np.floor(p["lon"] * 2).astype(int).astype(str)
            + "_" + (p["t_utc"].astype("int64") // (10 * 86400 * 10**6)).astype(str))
    cs = cell.value_counts()
    cs = cs[cs <= 6000]
    for k in cs.index[:3]:
        out.append((f"yogun:{k}", np.flatnonzero((cell == k).to_numpy())))
    return out


def main() -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    p = core.load_points()
    WINDOWS.update(core.build_windows(p))
    A = core.Arrays(p, WINDOWS)
    base = core.default_rule()
    rules = [
        core.Rule(D=1, H=24, buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=0.5, H=12, buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=2, H=48, mode="ayakizi_capraz", buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=1, H=24, mode="ayakizi_capraz", buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=1, H=24, mode="ayakizi_tum", buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=1, H=24, mode="ayakizi_capraz", gap="gecis", L=3, Hmax=72, buffer=base.buffer, km_deg=base.km_deg),
        core.Rule(D=1, H=24, mode="sabit", gap="gecis", L=1, Hmax=48, buffer=base.buffer, km_deg=base.km_deg),
        base,
    ]
    rules = list(dict.fromkeys(rules))
    smp = samples(p, rng)
    fails, n_cmp, n_pts = [], 0, 0
    for name, idx in smp:
        sub = core.subset(A, idx)
        n_pts += sub.n
        for r in rules:
            fast = core.canonical(core.components(sub.n, core.candidate_edges(sub, r)))
            slow = brute(sub, r)
            n_cmp += 1
            diff = int((fast != slow).sum())
            if diff:
                fails.append(f"{name} [{r.label()}] fark={diff} olay hızlı={fast.max()+1} kaba={slow.max()+1}")
        # parça büyüklüğü değişmezliği
        r = rules[-1]
        f1 = core.canonical(core.components(sub.n, core.candidate_edges(sub, r)))
        f2 = core.canonical(core.components(sub.n, core.candidate_edges(sub, r, chunk_pairs=997)))
        if (f1 != f2).any():
            fails.append(f"{name} parça büyüklüğü sonucu değiştirdi")
    # Tam veri kümelemesi (varsayılan kural, 20 yıl tek koşu) olay-kapalı örneklemlerde kaba kuvvetle aynı mı:
    # örneklem = seçili olayların TÜM noktaları (dışarıyla bağı olamaz), bölümleme birebir aynı olmalı.
    full = core.cluster(A, base)
    for name, idx in smp[::3]:
        ev_ids = np.unique(full[idx])
        sel = np.flatnonzero(np.isin(full, ev_ids))
        if len(sel) > 8000:
            continue
        sub = core.subset(A, sel)
        n_cmp += 1
        if (core.canonical(full[sel]) != brute(sub, base)).any():
            fails.append(f"tam veri kısıtı {name}: kaba kuvvetten farklı")
    # Testin gücü (mutasyon): ızgara hücresini kasten küçültülmüş hatalı bir hızlı yöntem,
    # en az bir örneklemde kaba kuvvetten FARKLI çıkmalı; çıkmıyorsa test kör demektir.
    orig = core.max_reach_km
    core.max_reach_km = lambda A_, r_: orig(A_, r_) * 0.3
    try:
        caught = 0
        for name, idx in smp:
            sub = core.subset(A, idx)
            r = rules[0]
            bad = core.canonical(core.components(sub.n, core.candidate_edges(sub, r)))
            caught += int((bad != brute(sub, r)).any())
    finally:
        core.max_reach_km = orig
    print(f"mutasyon testi: hatalı yöntem {caught}/{len(smp)} örneklemde yakalandı")
    if caught == 0:
        fails.append("mutasyon testi: hatalı yöntem yakalanmadı (test gücü yok)")
    print(f"örneklem={len(smp)} nokta={n_pts} kural={len(rules)} karşılaştırma={n_cmp} "
          f"fark_olan={len(fails)} süre={time.time()-t0:.1f}s")
    for f in fails[:20]:
        print("FARK:", f)
    if not fails:
        print("C03 GEÇTİ: hızlı kümeleme = kaba kuvvet (tüm örneklemlerde fark 0)")
    return 1 if fails else 0


if __name__ == "__main__":
    # Konsola yazıyorsa UTF-8; check_all gibi bir süreç okuyorsa onun yerel kodlaması (C03 çıktısı okunur kalsın).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8") if sys.stdout.isatty() else sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
