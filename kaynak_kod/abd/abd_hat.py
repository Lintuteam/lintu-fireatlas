"""ABD için sade veri hattı: Türkiye yöntemini ikinci bir ülkede sınar (2009-2015).

Basitçe: Türkiye'de kullandığımız aynı adımları ABD verisine uygular:
1) Temizlik: NASA'nın kendi 'type' etiketi (0 bitki yangını, 1 volkan, 2 statik kaynak, 3 açık deniz).
   Türkiye'ye özgü sanayi / anız / kalıcı ısı kuralları ABD için yeniden kalibre EDİLMEDİ (sınır).
2) Kümeleme: Türkiye kodunun AYNISI (src/clustering/core.py, varsayılan kural: D=1 km, MODIS ayak izi,
   geçiş kuralı L=3, en çok 72 sa). Ortak ve ayrı kümeleme farkı = çift sayım.
3) Harmonizasyon: Türkiye'deki tabakalı oran yöntemi (bölge x mevsim x FRP sınıfı, VIIRS hücreleri)
   ve sabit oran; bir yılı dışarıda bırakma (LOYO) 2012-2015.
4) Sıçrama: 2009-11 ortalaması ile 2012-14 ortalaması (Türkiye'deki 3+3 yıl penceresi).
5) Doğrulama: belgelenmiş 33 büyük ABD yangını ile olay eşleştirme.
Çıktı: veri_abd/cikti/*.json ve arayuz/data_abd/abd_data.js
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve()
KK = HERE.parents[1]                       # kaynak_kod
PROJ = HERE.parents[2]                     # NASA_Yangin_Takvimi_ABD
sys.path.insert(0, str(KK / "src"))
sys.path.insert(0, str(KK / "src" / "clustering"))
from clustering import core as C            # noqa: E402  (Türkiye kümeleme çekirdeği, değiştirilmeden)
from pipeline.timeutil import TR_OFFSET_HOURS  # noqa: E402

PQ = PROJ / "veri_abd" / "parquet"
OUT = PROJ / "veri_abd" / "cikti"
APP = PROJ / "arayuz" / "data_abd"
YANGIN = PROJ / "veri_abd" / "belgelenmis_yanginlar_abd.json"
SATMAP = {"Terra": "Terra", "Aqua": "Aqua", "Suomi NPP": "SNPP", "SNPP": "SNPP", "N": "SNPP", "NOAA-20": "N20", "N20": "N20"}
MEVSIM = {12: "kis", 1: "kis", 2: "kis", 3: "ilkbahar", 4: "ilkbahar", 5: "ilkbahar",
          6: "yaz", 7: "yaz", 8: "yaz", 9: "sonbahar", 10: "sonbahar", 11: "sonbahar"}
BOLGELER = ["Kuzeybatı", "Güneybatı", "Kuzey Ovalar", "Güney Ovalar", "Kuzeydoğu", "Güneydoğu", "Alaska", "Hawaii"]
FRP_SINIR = (10, 50)
HUCRE_KM = 1.0
GECIS_DK = 45
MIN_ORNEK = 200


def bolge(lat, lon):
    """Kaba ABD bölgesi (boylam/enlem kutuları; eyalet sınırı kullanılmadı)."""
    lat, lon = np.asarray(lat), np.asarray(lon)
    b = np.where(lon < -104, np.where(lat >= 40, 0, 1), np.where(lon < -90, np.where(lat >= 37, 2, 3), np.where(lat >= 37, 4, 5)))
    b = np.where((lat > 51) & (lon < -129), 6, b)
    b = np.where((lat < 23) & (lon < -150), 7, b)
    return b


def yukle():
    fs = sorted(PQ.glob("firms_abd_*.parquet"))
    p = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    p["t_utc"] = pd.to_datetime(p["acq_datetime_utc"], utc=True)
    p["sat"] = p["satellite"].astype(str).map(SATMAP).fillna(p["satellite"].astype(str))
    p = p.rename(columns={"latitude": "lat", "longitude": "lon", "frp_mw": "frp", "scan_km": "scan", "track_km": "track", "daynight": "dn"})
    n0 = len(p)
    disari = int((p["lon"] > -60).sum())            # Pasifik toprakları (Guam vb.): ızgara ±180 sarmasız
    p = p[p["lon"] <= -60].copy()
    p["type"] = pd.to_numeric(p["type"], errors="coerce").fillna(0).astype(int)
    p = p.sort_values(["t_utc", "sensor", "lat", "lon"], kind="mergesort").reset_index(drop=True)
    p["pid"] = np.arange(len(p), dtype=np.int64)
    p["yil"], p["ay"] = p["t_utc"].dt.year, p["t_utc"].dt.month
    p["day_tr"] = (p["t_utc"] + pd.Timedelta(hours=TR_OFFSET_HOURS)).dt.tz_localize(None).dt.normalize()
    p["bolge"] = bolge(p["lat"], p["lon"])
    p["mevsim"] = p["ay"].map(MEVSIM)
    p["status"] = p["type"].map({0: "temiz", 1: "volkan", 2: "statik_nasa", 3: "deniz"}).fillna("temiz")
    return p, n0, disari


def kumele(p):
    """Türkiye çekirdeği, varsayılan kural. Gözlem kapsamı: o gün en az bir tespit veren uydu gözlemiş sayılır."""
    q = p[p["status"].eq("temiz")].sort_values(["t_utc", "pid"], kind="mergesort").reset_index(drop=True)
    cov = q.groupby(["sat", "day_tr"]).size().reset_index(name="n")
    cov["observed"] = True
    win = C.build_windows(q, cov[["sat", "day_tr", "observed"]])
    A = C.Arrays(q, win)
    r = C.default_rule()
    t = time.time(); ortak = C.cluster(A, r); sure = time.time() - t
    ayri_m = C.cluster(A, r, mask=A.modis)
    ayri_v = C.cluster(A, r, mask=~A.modis)
    q["event_id"] = ortak
    n_ayri = int(ayri_m.max() + 1 + ayri_v.max() + 1)
    return q, {"kural": r.label(), "olay_ortak": int(ortak.max() + 1), "olay_ayri": n_ayri,
               "cift_sayim": n_ayri - int(ortak.max() + 1), "sure_sn": round(sure, 2), "nokta": int(len(q))}


def olaylar(q):
    g = q.groupby("event_id")
    ev = g.agg(lat=("lat", "mean"), lon=("lon", "mean"), t0=("t_utc", "min"), t1=("t_utc", "max"),
               n=("pid", "size"), frp_sum=("frp", "sum"), frp_max=("frp", "max"),
               n_modis=("sensor", lambda s: int((s == "MODIS").sum())))
    ev["n_viirs"] = ev["n"] - ev["n_modis"]
    ev["sure_sa"] = (ev["t1"] - ev["t0"]).dt.total_seconds() / 3600
    ev["yil"], ev["ay"] = ev["t0"].dt.year, ev["t0"].dt.month
    ev["bolge"] = bolge(ev["lat"], ev["lon"])
    return ev.reset_index()


def gecisler(v):
    """Uydu başına zaman sıralı; > GECIS_DK boşluk yeni geçiş."""
    v = v.sort_values(["sat", "t_utc"])
    tm = v["t_utc"].astype("int64") // 60_000_000_000
    yeni = (v["sat"] != v["sat"].shift()) | (tm.diff() > GECIS_DK)
    return yeni.cumsum().reindex(v.index)


def hucreler(v):
    lat0 = 39.0
    x = v["lon"].to_numpy() * 111.32 * np.cos(np.radians(lat0)) + v["pass_id"].to_numpy() * 1e5
    y = v["lat"].to_numpy() * 111.32
    pr = cKDTree(np.c_[x, y]).query_pairs(HUCRE_KM, output_type="ndarray")
    n = len(v)
    _, lab = connected_components(coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(n, n)), directed=False)
    return lab


def frp_sinif(f):
    return np.where(f < FRP_SINIR[0], "kucuk", np.where(f < FRP_SINIR[1], "orta", "buyuk"))


def harmonize(p):
    K = ["yil", "ay", "bolge"]
    c = p[p["status"].eq("temiz")]
    m = c[c["sensor"].eq("MODIS")].assign(fs=lambda d: frp_sinif(d["frp"].to_numpy()))
    v = c[c["sensor"].eq("VIIRS")].copy()
    v["pass_id"] = gecisler(v)
    v["cell"] = hucreler(v)
    cells = v.groupby("cell").agg(frp_sum=("frp", "sum"), yil=("yil", "first"), ay=("ay", "first"), bolge=("bolge", "first"))
    cells["fs"] = frp_sinif(cells["frp_sum"].to_numpy())
    T = m.groupby(K).size().rename("M_true").to_frame()
    T = T.join(m.groupby(K + ["fs"]).size().unstack("fs", fill_value=0).add_prefix("M_"), how="outer")
    T = T.join(v.groupby(K).size().rename("V_raw"), how="outer")
    T = T.join(cells.groupby(K + ["fs"]).size().unstack("fs", fill_value=0).add_prefix("V_"), how="outer")
    T = T.fillna(0).reset_index()
    for fs in ("kucuk", "orta", "buyuk"):
        for pre in ("M_", "V_"):
            if pre + fs not in T:
                T[pre + fs] = 0.0
    T["mevsim"] = T["ay"].map(MEVSIM)
    years = [2012, 2013, 2014, 2015]
    T["pred_i0"] = np.nan; T["pred_ii"] = np.nan
    for y in years:
        tr = T["yil"].isin(years) & ~T["yil"].eq(y); te = T["yil"].eq(y)
        T.loc[te, "pred_i0"] = T.loc[te, "V_raw"] * T.loc[tr, "M_true"].sum() / T.loc[tr, "V_raw"].sum()
        pred = pd.Series(0.0, index=T.index[te])
        for fs in ("kucuk", "orta", "buyuk"):
            a = T.loc[tr].groupby(["bolge", "mevsim"])[[f"M_{fs}", f"V_{fs}"]].sum()
            b = T.loc[tr].groupby("mevsim")[[f"M_{fs}", f"V_{fs}"]].sum()
            r1 = (a[f"M_{fs}"] / a[f"V_{fs}"]).where(a[f"V_{fs}"] >= MIN_ORNEK)
            r2 = b[f"M_{fs}"] / b[f"V_{fs}"].replace(0, np.nan)
            idx = pd.MultiIndex.from_frame(T.loc[te, ["bolge", "mevsim"]])
            r = pd.Series(r1.reindex(idx).to_numpy(), index=pred.index)
            r = r.fillna(pd.Series(r2.reindex(T.loc[te, "mevsim"]).to_numpy(), index=pred.index))
            pred += T.loc[te, f"V_{fs}"] * r.fillna(0)
        T.loc[te, "pred_ii"] = pred
    test = T[T["yil"].isin(years)]

    def olc(col):
        yl = test.groupby("yil")[["M_true", col]].sum()
        e = (yl[col] - yl["M_true"]) / yl["M_true"] * 100
        mr = test.groupby(K)[["M_true", col]].sum()
        ss = ((mr["M_true"] - mr[col]) ** 2).sum() / ((mr["M_true"] - mr["M_true"].mean()) ** 2).sum()
        tr_ = test.groupby(["yil", "ay"])[["M_true", col]].sum()
        ss2 = ((tr_["M_true"] - tr_[col]) ** 2).sum() / ((tr_["M_true"] - tr_["M_true"].mean()) ** 2).sum()
        return {"yillik_mape": round(float(e.abs().mean()), 2), "yillik_hata_pct": {int(k): round(float(x), 2) for k, x in e.items()},
                "ay_bolge_wape": round(float((mr[col] - mr["M_true"]).abs().sum() / mr["M_true"].sum() * 100), 2),
                "ay_bolge_r2": round(float(1 - ss), 4),
                "ay_ulke_wape": round(float((tr_[col] - tr_["M_true"]).abs().sum() / tr_["M_true"].sum() * 100), 2),
                "ay_ulke_r2": round(float(1 - ss2), 4)}
    sonuc = {"i0_sabit_oran": olc("pred_i0"), "ii_tabakali": olc("pred_ii")}
    kaz = min(sonuc, key=lambda k: sonuc[k]["ay_bolge_wape"])
    T["esdeger"] = T["M_true"].where(T["yil"] < 2012, T["pred_ii" if kaz.startswith("ii") else "pred_i0"])
    return T, sonuc, kaz, int(len(cells))


def sicrama(s, w=3, g=2012):
    return round(float((s.loc[g:g + w - 1].mean() - s.loc[g - w:g - 1].mean()) / s.loc[g - w:g - 1].mean() * 100), 2)


def dogrula(ev, q):
    fires = json.loads(YANGIN.read_text(encoding="utf-8"))["yanginlar"]
    kx = 111.32
    # Eşleştirme: yangın noktasının 40 km çevresinde, başlangıç −7 / +14 gün penceresindeki tespitlerin
    # EN ÇOĞUNU taşıyan olay (geç büyüyen ya da komşu yangınla birleşen olaylar da doğru bulunur).
    out = []
    evi = ev.set_index("event_id")
    for f in fires:
        s = pd.Timestamp(f["baslangic"], tz="UTC")
        w = q[(q["t_utc"] >= s - pd.Timedelta(days=7)) & (q["t_utc"] <= s + pd.Timedelta(days=14))]
        dx = (w["lon"] - f["lon"]) * kx * np.cos(np.radians(f["lat"])); dy = (w["lat"] - f["lat"]) * kx
        w = w[np.hypot(dx, dy) <= 40]
        rec = {"ad": f["ad"], "eyalet": f["eyalet"], "baslangic": f["baslangic"], "akre": f.get("akre"), "lat": f["lat"], "lon": f["lon"],
               "pencere_tespit": int(len(w))}
        if len(w) >= 5:
            eid = int(w["event_id"].value_counts().index[0])
            e = evi.loc[eid]
            yil_ev = ev[ev["yil"] == e["yil"]]
            km = float(np.hypot((e["lon"] - f["lon"]) * kx * np.cos(np.radians(f["lat"])), (e["lat"] - f["lat"]) * kx))
            rec.update({"durum": "eslesti", "event_id": eid, "tespit": int(e["n"]), "n_modis": int(e["n_modis"]),
                        "n_viirs": int(e["n_viirs"]), "sure_sa": round(float(e["sure_sa"]), 1), "uzaklik_km": round(km, 1),
                        "olay_baslangic": e["t0"].strftime("%Y-%m-%d"),
                        "basla_fark_gun": round(float((e["t0"] - s).total_seconds() / 86400), 1),
                        "yil_sirasi": int((yil_ev["n"] > e["n"]).sum() + 1), "frp_toplam": round(float(e["frp_sum"]), 1)})
        else:
            rec["durum"] = "bulunamadi"
        out.append(rec)
    return out


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True); APP.mkdir(parents=True, exist_ok=True)
    p, n0, disari = yukle()
    print("yüklendi", len(p), round(time.time() - t0), "s", flush=True)
    durum = p["status"].value_counts().to_dict()
    yil_sat = p.groupby(["yil", "sensor"]).size().unstack(fill_value=0)
    q, km = kumele(p)
    print("kümeleme", km, round(time.time() - t0), "s", flush=True)
    ev = olaylar(q)
    T, sonuc, kaz, n_cell = harmonize(p)
    print("harmonizasyon", kaz, sonuc[kaz]["yillik_mape"], round(time.time() - t0), "s", flush=True)
    c = p[p["status"].eq("temiz")]
    yl = pd.DataFrame({"modis": c[c.sensor == "MODIS"].groupby("yil").size(), "viirs": c[c.sensor == "VIIRS"].groupby("yil").size()}).fillna(0)
    yl["ham"] = yl["modis"] + yl["viirs"]
    yl["esdeger"] = T.groupby("yil")["esdeger"].sum()
    yl["olay"] = ev.groupby("yil").size()
    # ayrı kümelemenin yıllık sayımı (sıçrama aşaması için)
    yl = yl.fillna(0)
    jump = {"ham_pct": sicrama(yl["ham"]), "olay_ortak_pct": sicrama(yl["olay"]), "esdeger_pct": sicrama(yl["esdeger"]),
            "modis_gercek_pct": sicrama(yl["modis"])}
    jump["esdeger_eksi_modis_pct"] = round(jump["esdeger_pct"] - jump["modis_gercek_pct"], 2)
    dg = dogrula(ev, q)
    es = [d for d in dg if d["durum"] == "eslesti"]
    top = ev.sort_values("n", ascending=False).head(20)
    bolge_tab = []
    for i, b in enumerate(BOLGELER):
        e = ev[ev["bolge"] == i]; cc = c[c["bolge"] == i]
        bolge_tab.append({"bolge": b, "olay": int(len(e)), "tespit": int(len(cc)), "pay_pct": round(len(e) / len(ev) * 100, 1)})
    aylik = T.groupby(["yil", "ay"])[["M_true", "V_raw", "esdeger"]].sum().reset_index()
    aylik = aylik.merge(ev.groupby(["yil", "ay"]).size().rename("olay").reset_index(), on=["yil", "ay"], how="left").fillna(0)
    M = {
        "kapsam": {"yillar": [2009, 2015], "satir_kaynak": n0, "satir_analiz": int(len(p)), "pasifik_disarida": disari,
                   "yil_sensor": {int(y): {k: int(v) for k, v in r.items()} for y, r in yil_sat.iterrows()}},
        "durum": {k: int(v) for k, v in durum.items()},
        "kumeleme": km,
        "harmonizasyon": {"yontemler": sonuc, "kazanan": kaz, "viirs_hucre": n_cell, "loyo_yillari": [2012, 2015]},
        "sicrama": jump,
        "yillik": {int(y): {k: round(float(v), 1) for k, v in r.items()} for y, r in yl.iterrows()},
        "bolge": bolge_tab,
        "dogrulama": {"yangin_sayisi": len(dg), "eslesen": len(es), "liste": dg},
        "en_buyuk_20": [{"lat": round(float(r.lat), 3), "lon": round(float(r.lon), 3), "baslangic": r.t0.strftime("%Y-%m-%d"),
                         "tespit": int(r.n), "sure_sa": round(float(r.sure_sa), 1), "bolge": BOLGELER[int(r.bolge)]} for r in top.itertuples()],
        "sure_sn": round(time.time() - t0, 1),
    }
    (OUT / "abd_metrics.json").write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")
    ev.drop(columns=["t1"]).to_parquet(OUT / "abd_events.parquet")
    # Uygulama: harita için olaylar (>= 3 tespit), aylık seri
    e3 = ev[ev["n"] >= 3]
    harita = np.c_[e3["lat"].round(3), e3["lon"].round(3), e3["yil"], e3["ay"], e3["n"], e3["frp_sum"].round(0)].tolist()
    app = {"metrics": M, "aylik": aylik.round(1).to_dict("list"), "olaylar": harita, "bolgeler": BOLGELER}
    (APP / "abd_data.js").write_text("window.ABD=" + json.dumps(app, ensure_ascii=False, separators=(",", ":")) + ";", encoding="utf-8")
    print(json.dumps({k: M[k] for k in ("kumeleme", "sicrama")}, ensure_ascii=False))
    print("harm", json.dumps(sonuc, ensure_ascii=False))
    print("doğrulama", len(es), "/", len(dg), "harita olay", len(harita), "toplam", M["sure_sn"], "s")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
