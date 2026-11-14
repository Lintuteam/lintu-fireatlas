"""Olay tablosu + kümeleme ölçümleri.

Basitçe: Tüm tespitleri yangın olaylarına böler, her olaya kimlik verir ve "bu olayı iki
sensör de gördü mü?" sorusunu cevaplar. Ayrıca kuralların (D, H, ayak izi, geçiş) sonucu ne
kadar oynattığını ölçer ve sayıları metrik fişine yazar (K1: sayılar betikten).

Teknik olarak:
  python src/clustering/build_events.py            # olaylar + tüm ölçümler (~birkaç dk)
  python src/clustering/build_events.py --hizli    # yalnız olaylar + temel metrikler
Çıktılar:
  data/processed/points_event.parquet   pid, event_id (type 1/3 -> -1)
  data/processed/events.parquet         sözleşme §3 sütunları + ek tanı sütunları
  reports/metrics_parts/kumeleme.json   metrikler + sensitivity.D / .H (C04, C12)
  data/interim/kumeleme_analiz.json     ayrıntılı tablolar (docs/kumeleme_yontemi.md bunlardan)
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from clustering import core  # noqa: E402
from config import config as cfg  # noqa: E402
from pipeline.timeutil import TR_OFFSET_HOURS  # noqa: E402

ERA = {}   # main() veriden doldurur: core.era_bounds

PROC = ROOT / "data" / "processed"
OUT_PE = PROC / "points_event.parquet"
OUT_EV = PROC / "events.parquet"
OUT_PART = ROOT / "reports" / "metrics_parts" / "kumeleme.json"
OUT_ANALIZ = ROOT / "data" / "interim" / "kumeleme_analiz.json"
STATUS = PROC / "points_status.parquet"
BETIK = "src/clustering/build_events.py"
VERI = "points v1"


def rss_mb() -> float:
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 2**20
    except ImportError:
        return float("nan")


# --------------------------------------------------------------------------- #
# Dönemler ve olay özetleri
# --------------------------------------------------------------------------- #
def overlap_days(cov: pd.DataFrame) -> set:
    """İki sensör ailesinin de (en az bir uydusu) gözlediği TR günleri."""
    sens = cfg.load()["uydu_kodlari"]["sensor"]
    c = cov[cov["observed"]].copy()
    c["sensor"] = c["sat"].map(sens)
    fam = c.groupby("day_tr")["sensor"].nunique()
    return set(fam[fam == 2].index)


def summarize(p: pd.DataFrame, ev: np.ndarray, ovl: set, km_deg: float) -> pd.DataFrame:
    """Olay başına özet (ev: p ile hizalı olay no, -1 = dışarıda)."""
    m = ev >= 0
    d = pd.DataFrame({
        "event_id": ev[m], "t": p["t_utc"].to_numpy()[m], "lat": p["lat"].to_numpy()[m],
        "lon": p["lon"].to_numpy()[m], "frp": p["frp"].to_numpy(np.float64)[m],
        "modis": (p["sensor"] == "MODIS").to_numpy()[m], "aqua": (p["sat"] == "Aqua").to_numpy()[m], "type2": (p["type"] == 2).to_numpy()[m],
        "il": p["il"].astype(str).to_numpy()[m], "day_tr": p["day_tr"].to_numpy()[m],
    })
    if "mcell" in p.columns:
        d["mcell"] = p["mcell"].to_numpy()[m]
    d["w"] = d["frp"].clip(lower=0)
    d["wlat"], d["wlon"] = d["w"] * d["lat"], d["w"] * d["lon"]
    g = d.groupby("event_id", sort=True)
    e = g.agg(t_start_utc=("t", "min"), t_end_utc=("t", "max"), n=("t", "size"),
              n_modis=("modis", "sum"), n_aqua=("aqua", "sum"), frp_sum=("frp", "sum"), frp_max=("frp", "max"),
              wsum=("w", "sum"), wlat=("wlat", "sum"), wlon=("wlon", "sum"),
              lat_mean=("lat", "mean"), lon_mean=("lon", "mean"),
              lat_min=("lat", "min"), lat_max=("lat", "max"), lon_min=("lon", "min"),
              lon_max=("lon", "max"), n_type2=("type2", "sum"), day_tr_start=("day_tr", "min"))
    e["n_viirs"] = e["n"] - e["n_modis"]
    if "mcell" in d.columns:   # olaydaki tekil eşleştirme birimi (harmonizasyon mcell) sayısı
        e["n_mcell"] = g["mcell"].nunique()
    pos = e["wsum"] > 0
    e["lat"] = np.where(pos, e["wlat"] / e["wsum"].where(pos, 1), e["lat_mean"])
    e["lon"] = np.where(pos, e["wlon"] / e["wsum"].where(pos, 1), e["lon_mean"])
    # il: en yüksek FRP'li tespitin ili
    top = d.sort_values(["event_id", "frp"], ascending=[True, False], kind="mergesort").drop_duplicates("event_id")
    e["il"] = top.set_index("event_id")["il"]
    e["sure_saat"] = (e["t_end_utc"] - e["t_start_utc"]).dt.total_seconds() / 3600
    mlat = np.radians((e["lat_min"] + e["lat_max"]) / 2)
    e["kapsam_km"] = np.hypot((e["lat_max"] - e["lat_min"]) * km_deg,
                              (e["lon_max"] - e["lon_min"]) * km_deg * np.cos(mlat))
    e["cakisma"] = e["day_tr_start"].isin(ovl)
    e["match_class"] = np.select(
        [~e["cakisma"], (e["n_modis"] > 0) & (e["n_viirs"] > 0), e["n_modis"] > 0],
        ["tek_sensor_donemi", "ortak", "yalniz_modis"], "yalniz_viirs")
    e = e.drop(columns=["wsum", "wlat", "wlon", "lat_mean", "lon_mean"])
    return e.reset_index()


def overlap_stats(e: pd.DataFrame) -> dict:
    o = e[e["cakisma"]]
    mc = o["match_class"].value_counts()
    nm = int((o["n_modis"] > 0).sum())
    nv = int((o["n_viirs"] > 0).sum())
    ort = int(mc.get("ortak", 0))
    return {"olay_cakisma": int(len(o)), "ortak": ort, "yalniz_modis": int(mc.get("yalniz_modis", 0)),
            "yalniz_viirs": int(mc.get("yalniz_viirs", 0)), "modis_olay": nm, "viirs_olay": nv,
            "modis_olaylarinin_viirste_gorulme_orani": round(ort / nm, 4) if nm else None,
            "yalniz_modis_yalniz_terra": int(((o["match_class"] == "yalniz_modis") & (o["n_aqua"] == 0)).sum()),
            "aqua_iceren_modis_olay": int((o["n_aqua"] > 0).sum()),
            "aqua_iceren_modis_olaylarinin_viirste_gorulme_orani": round(float((o.loc[o["n_aqua"] > 0, "n_viirs"] > 0).mean()), 4),
            "viirs_olaylarinin_modiste_gorulme_orani": round(ort / nv, 4) if nv else None}


def size_stats(e: pd.DataFrame) -> dict:
    n = e["n"]
    return {"olay": int(len(e)), "en_buyuk_olay_tespit": int(n.max()),
            "tek_tespitli_oran": round(float((n == 1).mean()), 4),
            "tespit_p50": float(n.median()), "tespit_p99": float(n.quantile(0.99)),
            "sure_saat_p50": round(float(e["sure_saat"].median()), 2),
            "sure_saat_p90": round(float(e["sure_saat"].quantile(0.9)), 2),
            "sure_saat_p99": round(float(e["sure_saat"].quantile(0.99)), 2),
            "sure_saat_max": round(float(e["sure_saat"].max()), 1),
            "kapsam_km_p99": round(float(e["kapsam_km"].quantile(0.99)), 2),
            "kapsam_km_max": round(float(e["kapsam_km"].max()), 1),
            "olay_100plus_tespit": int((n >= 100).sum()),
            "olay_1000plus_tespit": int((n >= 1000).sum())}


def era_counts(e: pd.DataFrame) -> dict:
    y = e["t_start_utc"].dt.tz_convert("UTC").dt.year
    d = e["t_start_utc"]
    terra = d < ERA["aqua"]
    mod = (~terra) & (d < ERA["viirs"])
    return {"donem_yalniz_terra": int(terra.sum()), "donem_terra_aqua": int(mod.sum()),
            "donem_modis_viirs": int((~terra & ~mod).sum()), "yil_sayisi": int(y.nunique())}


# --------------------------------------------------------------------------- #
# Analizler
# --------------------------------------------------------------------------- #
def footprint_diagnostic(p: pd.DataFrame, rule: core.Rule) -> dict:
    """Aqua MODIS tespitine ±60 dk içindeki en yakın VIIRS tespitinin uzaklığı (çakışma dönemi)."""
    from scipy.spatial import cKDTree
    win = int(cfg.load()["harmonizasyon"]["kalibrasyon_zaman_penceresi_dk"]["value"])
    tm = core.minutes(p["t_utc"])
    aq = np.flatnonzero((p["sat"] == "Aqua").to_numpy() & (tm >= tm[(p["sensor"] == "VIIRS").to_numpy()].min()))
    vi = np.flatnonzero((p["sensor"] == "VIIRS").to_numpy())
    k = rule.km_deg
    lat0 = np.radians(39.0)
    def xy(ix):
        return np.c_[p["lon"].to_numpy()[ix] * k * np.cos(lat0), p["lat"].to_numpy()[ix] * k]
    # aynı geçişte: zaman kovası (gün) bazında ağaç
    day_a = tm[aq] // 1440
    day_v = tm[vi] // 1440
    res_d, res_in, res_has = [], [], []
    vt = pd.Series(vi).groupby(day_v).apply(np.asarray)
    scan = p["scan"].to_numpy(np.float64)
    track = p["track"].to_numpy(np.float64)
    lat, lon = p["lat"].to_numpy(), p["lon"].to_numpy()
    for dd, grp in pd.Series(aq).groupby(day_a):
        if dd not in vt.index:
            res_has.extend([False] * len(grp)); res_d.extend([np.inf] * len(grp)); res_in.extend([False] * len(grp))
            continue
        cand = vt[dd]
        a = grp.to_numpy()
        tree = cKDTree(xy(cand))
        for i in a:
            js = tree.query_ball_point(xy(np.array([i]))[0], r=8.0)
            js = [cand[j] for j in js if abs(tm[cand[j]] - tm[i]) <= win]
            if not js:
                res_has.append(False); res_d.append(np.inf); res_in.append(False); continue
            js = np.array(js)
            dy = (lat[js] - lat[i]) * k
            dx = np.abs(lon[js] - lon[i]) * k * np.cos(np.radians((lat[js] + lat[i]) / 2))
            res_has.append(True)
            res_d.append(float(np.hypot(dx, dy).min()))
            res_in.append(bool(((dx <= scan[i] / 2 + rule.buffer) & (dy <= track[i] / 2 + rule.buffer)).any()))
    d = np.array(res_d); inn = np.array(res_in)
    sc = scan[aq]
    edge = sc >= np.quantile(sc, 0.75)
    out = {"aqua_tespit": int(len(aq)), "pencere_dk": win,
           "viirs_8km_icinde_oran": round(float(np.isfinite(d).mean()), 4),
           "en_yakin_viirs_1km_icinde_oran": round(float((d <= 1).mean()), 4),
           "en_yakin_viirs_2km_icinde_oran": round(float((d <= 2).mean()), 4),
           "ayakizi_tampon_icinde_oran": round(float(inn.mean()), 4),
           "kenar_piksel_scan_esik_km": float(np.quantile(sc, 0.75)),
           "kenar_1km_icinde_oran": round(float((d[edge] <= 1).mean()), 4),
           "kenar_ayakizi_icinde_oran": round(float(inn[edge].mean()), 4),
           "merkez_1km_icinde_oran": round(float((d[~edge] <= 1).mean()), 4),
           "merkez_ayakizi_icinde_oran": round(float(inn[~edge].mean()), 4),
           "uzaklik_p50_km_eslesenler": round(float(np.median(d[np.isfinite(d)])), 3)}
    return out


def aniz_compare(p: pd.DataFrame, labs: dict, km_deg: float) -> dict:
    """Demo anız olay kuralını farklı kümelemelerle uygula; anız sayılan noktaları karşılaştır."""
    ak = cfg.load()["kumeleme"]["aniz_karsilastirma"]
    F = float(cfg.esik("F")); months = set(cfg.esik("aniz_aylari"))
    nmax, hmax = int(ak["max_tespit"]), float(ak["max_sure_saat"])
    cand = p["type"].isin([0, -1]).to_numpy()   # statik kaynak (type 2) anız adayı değil
    tr_month = (p["t_utc"] + pd.Timedelta(hours=TR_OFFSET_HOURS)).dt.month.to_numpy()
    frp = p["frp"].to_numpy(np.float64)
    tm = core.minutes(p["t_utc"])
    out, flags = {}, {}
    for name, ev in labs.items():
        e = np.where(cand, ev, -1)
        m = e >= 0
        df = pd.DataFrame({"e": e[m], "t": tm[m], "f": frp[m], "mo": tr_month[m]})
        g = df.groupby("e").agg(n=("t", "size"), t0=("t", "min"), t1=("t", "max"), fmax=("f", "max"))
        first_mo = df.sort_values(["e", "t"]).drop_duplicates("e").set_index("e")["mo"]
        isa = (g["n"] <= nmax) & ((g["t1"] - g["t0"]) <= hmax * 60) & (g["fmax"] < F) & first_mo.reindex(g.index).isin(months)
        pt = np.zeros(len(p), bool)
        pt[np.flatnonzero(m)] = isa.reindex(df["e"]).to_numpy()
        flags[name] = pt
        # anız adayı gibi görünen ama olay büyüdüğü için kuraldan çıkan: tespit kendi başına
        # (FRP<F, anız ayı) kuralı sağlıyor, olay ise >nmax tespit
        big = (g["n"] > nmax).reindex(df["e"]).to_numpy()
        pt_like = (df["f"].to_numpy() < F) & np.isin(df["mo"].to_numpy(), list(months))
        out[name] = {"aniz_olay": int(isa.sum()), "aniz_nokta": int(pt.sum()),
                     "aniz_nokta_modis": int((pt & (p["sensor"] == "MODIS").to_numpy()).sum()),
                     "aniz_nokta_viirs": int((pt & (p["sensor"] == "VIIRS").to_numpy()).sum()),
                     "kucuk_ve_aniz_ayinda_ama_olay_buyuk_nokta": int((big & pt_like).sum())}
    ref = "ayri_sensor"
    for name in labs:
        if name != ref:
            out[name]["ayri_sensore_gore_aniz_kaybi_nokta"] = int((flags[ref] & ~flags[name]).sum())
            out[name]["ayri_sensore_gore_aniz_kazanci_nokta"] = int((~flags[ref] & flags[name]).sum())
    return out


def chain_cases(p: pd.DataFrame, ev: np.ndarray, e: pd.DataFrame, k: int = 8) -> list:
    """Zincirleme şüphelisi örnekler: geniş kapsamlı, düşük FRP'li, çok günlü ama statik olmayan olaylar."""
    c = e[(e["n_type2"] == 0) & (e["kapsam_km"] >= 10)].copy()
    c["frp_ort"] = c["frp_sum"] / c["n"]
    c = c.sort_values("kapsam_km", ascending=False)
    rows = []
    days = pd.Series(p["day_tr"].to_numpy()).groupby(ev).nunique()
    for _, r in c.head(k).iterrows():
        rows.append({"event_id": int(r["event_id"]), "il": r["il"], "baslangic": str(r["t_start_utc"])[:16],
                     "tespit": int(r["n"]), "gun": int(days.get(r["event_id"], 0)),
                     "sure_saat": round(float(r["sure_saat"]), 1), "kapsam_km": round(float(r["kapsam_km"]), 1),
                     "frp_ort": round(float(r["frp_ort"]), 1), "frp_max": round(float(r["frp_max"]), 1)})
    return rows


def link_spans(A: core.Arrays, rule: core.Rule, ev: np.ndarray, eids: list) -> dict:
    """Seçili olaylarda en uzun tek bağlantı (km): zincirin 'köprü' uzunluğu değil, olay
    kapsamı / tek bağ oranı zincirlenme göstergesidir."""
    out = {}
    for eid in eids:
        idx = np.flatnonzero(ev == eid)
        sub = core.subset(A, idx)
        a, b = [], []
        for x, y in core.candidate_edges(sub, rule):
            a.append(x); b.append(y)
        a = np.concatenate(a) if a else np.empty(0, int)
        b = np.concatenate(b) if b else np.empty(0, int)
        dy = (sub.lat[a] - sub.lat[b]) * rule.km_deg
        dx = (sub.lon[a] - sub.lon[b]) * rule.km_deg * np.cos(np.radians((sub.lat[a] + sub.lat[b]) / 2))
        out[int(eid)] = {"bag": int(len(a)), "bag_max_km": round(float(np.hypot(dx, dy).max()), 2) if len(a) else 0.0}
    return out


# --------------------------------------------------------------------------- #
def M(value, unit, tanim, etiket="ölçüldü"):
    return {"value": value, "unit": unit, "tanim": tanim, "betik": BETIK, "veri_surumu": VERI, "etiket": etiket}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hizli", action="store_true")
    args = ap.parse_args(argv)
    T0 = time.time()
    timing = {}
    p = core.load_points()
    if core.MCELL.exists():
        p = p.merge(pd.read_parquet(core.MCELL, columns=["pid", "mcell"]), on="pid", how="left")
    girdi = "status∈{temiz,aniz}" if core.STATUS.exists() else "type∉{1,3}"
    cov = pd.read_parquet(core.COVERAGE, columns=["sat", "day_tr", "observed"])
    W = core.build_windows(p, cov)
    ERA["aqua"], ERA["viirs"] = core.era_bounds(p)
    y0, y1 = cfg.load()["kumeleme"]["demo_donemi_yillari"]["value"]

    def demo_n(es):   # demo dönemi (TR yılı) olay sayısı
        y = pd.to_datetime(es["day_tr_start"]).dt.year
        return int(y.between(y0, y1).sum())
    A = core.Arrays(p, W)
    timing["yukleme_s"] = round(time.time() - T0, 2)
    rule = core.default_rule()
    ovl = overlap_days(cov)

    t = time.time(); r0 = rss_mb()
    ev = core.cluster(A, rule)
    timing["varsayilan_kumeleme_s"] = round(time.time() - t, 2)
    timing["rss_mb_sonra"] = round(rss_mb(), 0); timing["rss_mb_once"] = round(r0, 0)

    e = summarize(p, ev, ovl, rule.km_deg)
    # olay durumu: temizlik yan tablosu varsa noktaların durumundan
    if STATUS.exists():
        st = pd.read_parquet(STATUS, columns=["pid", "status"]).set_index("pid")["status"]
        sp = st.reindex(p["pid"]).to_numpy()
        ds = pd.DataFrame({"e": ev, "s": sp}).dropna()
        mode = ds.groupby("e")["s"].agg(lambda s: s.value_counts().index[0])
        nun = ds.groupby("e")["s"].nunique()
        e["status"] = e["event_id"].map(mode).fillna("bekliyor")
        e["status_karisik"] = e["event_id"].map(nun).fillna(1).gt(1)
    else:
        e["status"] = "bekliyor"          # temizlik yan tablosu henüz yok; ikinci adımda türetilir
        e["status_karisik"] = False
    PROC.mkdir(parents=True, exist_ok=True)
    allp = pd.read_parquet(core.POINTS, columns=["pid"])
    pe = allp.merge(pd.DataFrame({"pid": p["pid"].to_numpy(), "event_id": ev}), on="pid", how="left")
    pe["event_id"] = pe["event_id"].fillna(-1).astype("int64")
    assert len(pe) == len(allp)
    pe.to_parquet(OUT_PE, index=False)
    cols = ["event_id", "t_start_utc", "t_end_utc", "day_tr_start", "lat", "lon", "n_modis", "n_viirs",
            "frp_sum", "frp_max", "il", "match_class", "status", "status_karisik", "n", "n_type2",
            "sure_saat", "kapsam_km", "cakisma"] + (["n_mcell"] if "n_mcell" in e.columns else [])
    e[cols].to_parquet(OUT_EV, index=False)
    timing["olay_yazma_toplam_s"] = round(time.time() - T0, 2)

    # C04: ayrı kümeleme (sensör başına), çakışma dönemi
    modis = A.modis
    ev_m = core.cluster(A, rule, mask=modis)
    ev_v = core.cluster(A, rule, mask=~modis)
    sep = np.where(modis, ev_m, ev_v + ev_m.max() + 1)
    e_sep = summarize(p, sep, ovl, rule.km_deg)
    joint_ovl = int(e["cakisma"].sum())
    sep_ovl = int(e_sep["cakisma"].sum())
    ostat = overlap_stats(e)
    mc = e["match_class"].value_counts().to_dict()

    metrics = {
        "events_total": M(int(len(e)), "olay", f"Toplam olay (girdi: {girdi} noktalar, {rule.label()})"),
        "events_joint_overlap": M(joint_ovl, "olay", "Çakışma döneminde (iki sensör ailesi de gözlüyor) MODIS+VIIRS birlikte kümelenince olay sayısı"),
        "events_separate_overlap": M(sep_ovl, "olay", "Aynı dönemde sensörler ayrı ayrı kümelenince olay sayısı toplamı"),
        "events_double_count_avoided": M(sep_ovl - joint_ovl, "olay", "Ayrı kümelemede iki kez sayılacak olay (ayrı - ortak)"),
        "events_match_ortak": M(int(mc.get("ortak", 0)), "olay", "match_class=ortak (çakışma döneminde iki sensör de gördü)"),
        "events_match_yalniz_modis": M(int(mc.get("yalniz_modis", 0)), "olay", "match_class=yalniz_modis"),
        "events_match_yalniz_viirs": M(int(mc.get("yalniz_viirs", 0)), "olay", "match_class=yalniz_viirs"),
        "events_match_tek_sensor_donemi": M(int(mc.get("tek_sensor_donemi", 0)), "olay", "Çakışma dışı (yalnız bir sensör ailesi gözlüyor) olaylar"),
        "events_modis_seen_by_viirs_share": M(ostat["modis_olaylarinin_viirste_gorulme_orani"], "oran", f"Çakışmada MODIS tespiti içeren olayların VIIRS tespiti de içerme oranı ({rule.label()})"),
        "clustering_runtime_s": M(timing["varsayilan_kumeleme_s"], "s", "Varsayılan kuralla 20 yıllık tam veride kümeleme süresi (bu makine)"),
        "clustering_rss_mb": M(timing["rss_mb_sonra"], "MB", "Kümeleme sonrası süreç belleği (RSS)"),
    }
    analiz = {"girdi": girdi, "girdi_nokta": int(len(p)), "kural": rule.label(), "zaman": timing, "cakisma_varsayilan": ostat, "boyut_varsayilan": size_stats(e),
              "donem_varsayilan": era_counts(e), "match_class": {k: int(v) for k, v in mc.items()},
              "pencere_sayisi": {f"{g}_{d}": int(len(v[0])) for (g, d), v in W.items()}}
    sens = {}

    if not args.hizli:
        base = dict(buffer=rule.buffer, km_deg=rule.km_deg)
        cache = {}

        def run(r):
            t = time.time()
            if r not in cache:
                cache[r] = core.cluster(A, r)          # yalnız etiketler önbellekte (bellek)
            s_ = round(time.time() - t, 2)
            lab = cache[r]
            return lab, summarize(p, lab, ovl, r.km_deg), s_

        # 1) ayak izi
        analiz["ayakizi_tani"] = footprint_diagnostic(p, rule)
        modes = {}
        for mode in ("sabit", "ayakizi_capraz", "ayakizi_tum"):
            r = core.Rule(D=1, H=24, mode=mode, **base)
            lab, es, s = run(r)
            modes[mode] = {**overlap_stats(es), "olay_toplam": int(len(es)), "sure_s": s,
                           "tek_tespitli_oran": round(float((es["n"] == 1).mean()), 4)}
        analiz["eslestirme_modlari"] = modes

        # 2) geçiş kuralı
        gaps = {}
        rH = core.Rule(D=1, H=24, mode=rule.mode, **base)
        for r in [rH] + [core.Rule(D=1, H=24, mode=rule.mode, gap="gecis", L=L, Hmax=72, **base) for L in cfg.load()["kumeleme"]["duyarlilik"]["L"]] \
                + [core.Rule(D=1, H=24, mode=rule.mode, gap="gecis", L=3, Hmax=h, **base) for h in cfg.load()["kumeleme"]["duyarlilik"]["Hmax"]]:
            lab, es, s = run(r)
            gaps[r.label()] = {**size_stats(es), **era_counts(es), "sure_s": s,
                               "modis_viirste_gorulme": overlap_stats(es)["modis_olaylarinin_viirste_gorulme_orani"]}
        # gecis ile sabit H arasındaki fark: kesinti günlerine denk gelen birleşmeler
        labH = run(rH)[0]
        rG = core.Rule(D=1, H=24, mode=rule.mode, gap="gecis", L=3, Hmax=72, **base)
        labG = run(rG)[0]
        gaps["_karsilastirma"] = _compare_partitions(labH, labG)
        for h in (27, 30):   # geçiş saati oynaması: sabit H biraz büyütülünce ne olur
            r = core.Rule(D=1, H=h, mode=rule.mode, **base)
            lab, es, s = run(r)
            gaps[r.label()] = {**size_stats(es), **era_counts(es), "sure_s": s}
        # kapsam bilgisinin katkısı: tüm günler gözlenmiş sayılırsa (kesinti bilgisi yok)
        cov_all = cov.assign(observed=True)
        A_all = core.Arrays(p, core.build_windows(p, cov_all))
        lab_all = core.cluster(A_all, rG)
        del A_all
        gaps["_kesinti_bilgisi_etkisi"] = {**_compare_partitions(lab_all, labG),
                                          "aciklama": "a = kesinti bilgisi yok sayılarak, b = coverage.observed ile"}
        del lab_all
        analiz["bosluk_kurali"] = gaps

        # 3) D / H duyarlılığı (sabit H, varsayılan eşleştirme modu)
        rows_D, rows_H = [], []
        for D in cfg.load()["kumeleme"]["duyarlilik"]["D"]:
            r = replace(rule, D=float(D))
            lab, es, s = run(r)
            st = size_stats(es)
            rows_D.append({"deger": D, "kural": r.label(), "olay": st["olay"], "en_buyuk_olay": st["en_buyuk_olay_tespit"],
                           "tek_tespitli_oran": st["tek_tespitli_oran"], "olay_demo_donemi": demo_n(es),
                           "modis_viirste_gorulme": overlap_stats(es)["modis_olaylarinin_viirste_gorulme_orani"]})
        for H in cfg.load()["kumeleme"]["duyarlilik"]["H"]:
            r = core.Rule(D=1, H=float(H), mode=rule.mode, **base)
            lab, es, s = run(r)
            st = size_stats(es)
            rows_H.append({"deger": H, "kural": r.label(), "olay": st["olay"], "en_buyuk_olay": st["en_buyuk_olay_tespit"],
                           "tek_tespitli_oran": st["tek_tespitli_oran"], "olay_demo_donemi": demo_n(es),
                           "modis_viirste_gorulme": overlap_stats(es)["modis_olaylarinin_viirste_gorulme_orani"]})
        # D sabit modda da (demo karşılaştırması)
        rows_Ds = []
        for D in cfg.load()["kumeleme"]["duyarlilik"]["D"]:
            r = core.Rule(D=float(D), H=24, mode="sabit", **base)
            lab, es, s = run(r)
            st = size_stats(es)
            rows_Ds.append({"deger": D, "olay": st["olay"], "en_buyuk_olay": st["en_buyuk_olay_tespit"],
                            "tek_tespitli_oran": st["tek_tespitli_oran"], "olay_demo_donemi": demo_n(es)})
        rows_L = []
        for L in cfg.load()["kumeleme"]["duyarlilik"]["L"]:
            r = replace(rule, gap="gecis", L=int(L))
            lab, es, s = run(r)
            st = size_stats(es)
            rows_L.append({"deger": L, "kural": r.label(), "olay": st["olay"], "en_buyuk_olay": st["en_buyuk_olay_tespit"],
                           "tek_tespitli_oran": st["tek_tespitli_oran"], "sure_saat_p90": st["sure_saat_p90"],
                           "olay_demo_donemi": demo_n(es),
                           "modis_viirste_gorulme": overlap_stats(es)["modis_olaylarinin_viirste_gorulme_orani"]})
        sens = {"D": rows_D, "H": rows_H, "L": rows_L}
        analiz["duyarlilik_D_sabit_mod"] = rows_Ds

        # 4) zincirleme
        sz = e["n"]
        analiz["zincirleme"] = {
            "boyut_dagilimi": {f"<={b}": int((sz <= b).sum()) for b in (1, 3, 10, 100, 1000)} | {">1000": int((sz > 1000).sum())},
            "en_buyuk_10": e.nlargest(10, "n")[["event_id", "il", "t_start_utc", "n", "n_type2", "sure_saat", "kapsam_km", "frp_max"]]
                .assign(t_start_utc=lambda x: x["t_start_utc"].astype(str).str[:16], sure_saat=lambda x: x["sure_saat"].round(1),
                        kapsam_km=lambda x: x["kapsam_km"].round(1)).to_dict("records"),
            "type2_karisik_olay": int(((e["n_type2"] > 0) & (e["n_type2"] < e["n"])).sum()),
            "type2_karisik_olaydaki_type0_nokta": int((e.loc[(e["n_type2"] > 0) & (e["n_type2"] < e["n"]), "n"]
                                                      - e.loc[(e["n_type2"] > 0) & (e["n_type2"] < e["n"]), "n_type2"]).sum()),
            "ornek_vakalar": chain_cases(p, ev, e),
        }
        ex = analiz["zincirleme"]["ornek_vakalar"]
        analiz["zincirleme"]["ornek_bag_uzunlugu"] = link_spans(A, rule, ev, [r_["event_id"] for r_ in ex[:4]])
        # kesme önerisi: statik kaynak (type 2) noktalarını zincire köprü yapmadan kümele
        t = time.time()
        not2 = (p["type"] != 2).to_numpy()
        ev_n2 = core.cluster(A, rule, mask=not2)
        e_n2 = summarize(p, ev_n2, ovl, rule.km_deg)
        analiz["zincirleme"]["kesme_type2_haric"] = {**size_stats(e_n2), "sure_s": round(time.time() - t, 2),
                                                    "type0_nokta_olay_sayisi_once": int(e.loc[e["n_type2"] < e["n"]].shape[0])}
        # süre tavanı önerisi: 7 günden uzun olayı günlük alt olaylara bölmek yerine ölç
        tz = cfg.load()["kumeleme"]["tarim_zinciri"]
        mo = pd.to_datetime(e["day_tr_start"]).dt.month          # TR ayı (K11)
        big = (e["n_type2"] == 0) & (e["kapsam_km"] >= float(tz["min_kapsam_km"]))
        agri = big & (e["frp_sum"] / e["n"] < float(cfg.esik("F"))) & mo.isin(tz["aylar"])
        ntot = int(len(p))
        ex = e[agri].assign(frp_ort=lambda x: x["frp_sum"] / x["n"]).nlargest(5, "kapsam_km")
        analiz["zincirleme"]["tarim_zinciri_supheli"] = {
            "tanim": f"type2 içermeyen, kapsamı >= {tz['min_kapsam_km']} km, olay ortalama FRP < F, başlangıç TR ayı {tz['aylar']}",
            "olay": int(agri.sum()), "tespit": int(e.loc[agri, "n"].sum()),
            "tespit_payi": round(int(e.loc[agri, "n"].sum()) / ntot, 4),
            "il_ilk5": e.loc[agri, "il"].value_counts().head(5).to_dict(),
            "ornekler": [{"il": r.il, "baslangic_tr_gunu": str(r.day_tr_start), "tespit": int(r.n),
                          "sure_saat": round(float(r.sure_saat), 1), "kapsam_km": round(float(r.kapsam_km), 1),
                          "frp_ort": round(float(r.frp_ort), 1)} for r in ex.itertuples()]}
        analiz["zincirleme"]["kapsam_10km_ustu_type2siz"] = {"olay": int(big.sum()), "tespit": int(e.loc[big, "n"].sum()),
                                                            "tespit_payi": round(int(e.loc[big, "n"].sum()) / ntot, 4)}
        analiz["zincirleme"]["uzun_olay_gt7gun"] = int((e["sure_saat"] > 168).sum())
        analiz["zincirleme"]["uzun_olay_gt7gun_type2siz"] = int(((e["sure_saat"] > 168) & (e["n_type2"] == 0)).sum())

        # 5) anız etkileşimi
        labs = {"nokta_duzeyi": np.arange(len(p)), "ayri_sensor": sep,
                "ortak_sabit_D1_H24": run(core.Rule(D=1, H=24, mode="sabit", **base))[0],
                "ortak_capraz_H24": labH, "ortak_varsayilan": ev}
        analiz["aniz_etkilesimi"] = aniz_compare(p, labs, rule.km_deg)

        for k_, v_ in modes.items():
            metrics[f"events_modis_seen_by_viirs_share_{k_}"] = M(v_["modis_olaylarinin_viirste_gorulme_orani"], "oran",
                f"Çakışmada MODIS olaylarının VIIRS'te de görülme oranı, eşleştirme modu={k_}, D=1 km, H=24 sa")
            metrics[f"events_yalniz_modis_{k_}"] = M(v_["yalniz_modis"], "olay", f"Çakışmada yalnız MODIS olay sayısı, mod={k_}")
        fd = analiz["ayakizi_tani"]
        metrics["aqua_nearest_viirs_within_1km_share"] = M(fd["en_yakin_viirs_1km_icinde_oran"], "oran",
            f"Aqua MODIS tespitlerinden ±{fd['pencere_dk']} dk içinde 1 km'de VIIRS tespiti olanların oranı (çakışma dönemi)")
        metrics["aqua_viirs_in_footprint_share"] = M(fd["ayakizi_tampon_icinde_oran"], "oran",
            "Aynı oranın ayak izi (scan×track + tampon) ile ölçülmüşü", "tahmini")
        ae = analiz["aniz_etkilesimi"]
        metrics["aniz_points_separate"] = M(ae["ayri_sensor"]["aniz_nokta"], "nokta", "Demo anız olay kuralı, sensörler ayrı kümelenince anız sayılan nokta (karşılaştırma; nihai kural temizlikte)", "tahmini")
        metrics["aniz_points_joint"] = M(ae["ortak_varsayilan"]["aniz_nokta"], "nokta", "Aynı kural, ortak (varsayılan) kümelemede anız sayılan nokta", "tahmini")
        metrics["clustering_sensitivity_runtime_s"] = M(round(time.time() - T0, 1), "s", "Tüm ölçümlerle toplam koşu süresi")

    analiz["zaman"]["toplam_s"] = round(time.time() - T0, 1)
    analiz["zaman"]["rss_mb_son"] = round(rss_mb(), 0)
    OUT_PART.parent.mkdir(parents=True, exist_ok=True)
    part = {"metrics": metrics}
    if sens:
        part["sensitivity"] = sens
    elif OUT_PART.exists():  # --hizli: önceki duyarlılık tablosunu koru
        old = json.loads(OUT_PART.read_text(encoding="utf-8"))
        if "sensitivity" in old:
            part["sensitivity"] = old["sensitivity"]
        for k_, v_ in old.get("metrics", {}).items():
            part["metrics"].setdefault(k_, v_)
    OUT_PART.write_text(json.dumps(part, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not args.hizli:
        OUT_ANALIZ.parent.mkdir(parents=True, exist_ok=True)
        OUT_ANALIZ.write_text(json.dumps(analiz, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"olay": len(e), "kural": rule.label(), "zaman": analiz["zaman"], "match_class": analiz["match_class"],
                      "C04": [joint_ovl, sep_ovl]}, ensure_ascii=False, default=str))
    return 0


def _compare_partitions(a: np.ndarray, b: np.ndarray) -> dict:
    """b, a'nın birleşmesi mi? (b daha kaba) — kaç a-olayı b'de birleşti, kaç bölündü."""
    pairs = pd.DataFrame({"a": a, "b": b}).drop_duplicates()
    a_per_b = pairs.groupby("b").size()
    b_per_a = pairs.groupby("a").size()
    return {"olay_a": int(a.max() + 1), "olay_b": int(b.max() + 1),
            "b_de_birlesen_a_olaylari": int(a_per_b[a_per_b > 1].sum()),
            "b_olaylari_birden_cok_a_iceren": int((a_per_b > 1).sum()),
            "a_olaylari_b_de_bolunen": int((b_per_a > 1).sum())}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
