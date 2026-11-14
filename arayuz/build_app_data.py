"""Parquet -> arayüzün okuduğu statik dosyalar (src/app/data/).

Basitçe: Büyük tabloları tarayıcının yutabileceği küçük dosyalara böler: her yıl için ayrı
"olay" ve "nokta" dosyası. Arayüz yalnız seçilen yılların dosyasını indirir.
Teknik olarak: sütunlu ikili (typed array) dosyalar; başlıkları manifest.json'da.
Sabit sayı yok: her şey parquet/metrics.json'dan türetilir (K1). Yeniden üretilebilir:
    python src/app/build_app_data.py
Kaynak notu: il çokgenleri ../demo/data/fire_data.js içinden (cihadturhan/tr-geojson) alınır (K7).
"""
import json, shutil, sys, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data" / "processed"
OUT = ROOT / "src" / "app" / "data"
EPOCH = pd.Timestamp("2000-01-01", tz="UTC")
STATUS = ["temiz", "deniz", "volkan", "statik_nasa", "sanayi", "dusuk_guven", "aniz", "kalici_belirsiz"]
CLS = ["ortak", "yalniz_modis", "yalniz_viirs", "tek_sensor_donemi"]
SATS = ["Terra", "Aqua", "SNPP", "N20", "N21"]


def wcols(path, cols):
    """cols: [(ad, ndarray)] — büyük öğe boyutu önce (hizalama). Başlık listesi döner."""
    cols = sorted(cols, key=lambda c: -c[1].dtype.itemsize)
    hdr, off = [], 0
    with open(path, "wb") as f:
        for name, a in cols:
            a = np.ascontiguousarray(a)
            f.write(a.tobytes())
            hdr.append({"ad": name, "tip": a.dtype.name, "ofs": off})
            off += a.nbytes
    return hdr, off


def days(s):  # tarih -> 2000-01-01'den gün
    return ((pd.to_datetime(s) - pd.Timestamp("2000-01-01")).dt.days).astype("int32")


def tmin(s):
    return ((s - EPOCH).dt.total_seconds() // 60).astype("int32")


def cell_code(m):
    out = np.zeros(len(m), dtype="float64")
    isM = m.str.startswith("M").to_numpy()
    out[isM] = m[isM].str[1:].astype("float64").to_numpy()
    g = m[~isM].str[1:].str.split("_", expand=True).astype("int64")
    out[~isM] = -(g[0] * 10000 + g[1]).to_numpy() - 1
    return out


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*"):
        if f.is_file():
            f.unlink()
    man = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "status": STATUS,
           "match_class": CLS, "sats": SATS, "simulated": False, "events": {}, "points": {}}
    s = (ROOT.parent / "demo" / "data" / "fire_data.js").read_text(encoding="utf-8")
    demo = json.loads(s[len("window.FIRE_DATA="):].rstrip().rstrip(";"))
    ils = list(demo["ils"])
    gj = demo["provinces"]
    for ft in gj["features"]:
        ft["properties"] = {"name": ft["properties"]["name"], "idx": ils.index(ft["properties"]["name"])}
    (OUT / "il.geojson").write_text(json.dumps(gj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    man["ils"] = ils
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "src" / "harmonize"))
    try:
        from harmonize.ortak import IL_BOLGE  # il -> 7 coğrafi bölge (harmonizasyonla aynı tanım)
        man["il_bolge"] = {k: v for k, v in IL_BOLGE.items()}
    except Exception as ex:  # noqa
        print("il_bolge okunamadı:", ex)
        man["il_bolge"] = {}
    shutil.copy(ROOT / "reports" / "metrics.json", OUT / "metrics.json")

    # ---- olaylar
    ev = pd.read_parquet(P / "events.parquet")
    il_ix = {n: i for i, n in enumerate(ils)}
    ev["il_i"] = ev["il"].map(il_ix).fillna(255).astype("uint8")
    ev["cls_i"] = ev["match_class"].map({c: i for i, c in enumerate(CLS)}).astype("uint8")
    ev["st_i"] = ev["status"].map({c: i for i, c in enumerate(STATUS)}).astype("uint8")
    ev["tmin"] = tmin(ev["t_start_utc"])
    ev["dur"] = ((ev["t_end_utc"] - ev["t_start_utc"]).dt.total_seconds() // 60).astype("int32")
    ev["day"] = days(ev["day_tr_start"])
    ev["yil"] = pd.to_datetime(ev["day_tr_start"]).dt.year
    for y, g in ev.groupby("yil"):
        hdr, nb = wcols(OUT / f"events_{y}.bin", [
            ("evid", g.event_id.astype("int32").to_numpy()), ("lat", g.lat.astype("float32").to_numpy()),
            ("lon", g.lon.astype("float32").to_numpy()), ("tmin", g.tmin.to_numpy()), ("dur", g.dur.to_numpy()),
            ("frp_sum", g.frp_sum.astype("float32").to_numpy()), ("frp_max", g.frp_max.astype("float32").to_numpy()),
            ("n_modis", g.n_modis.astype("uint16").to_numpy()), ("n_viirs", g.n_viirs.astype("uint16").to_numpy()),
            ("n_type2", g.n_type2.astype("uint16").to_numpy()), ("il", g.il_i.to_numpy()),
            ("cls", g.cls_i.to_numpy()), ("st", g.st_i.to_numpy()), ("karisik", g.status_karisik.astype("uint8").to_numpy())])
        man["events"][int(y)] = {"n": int(len(g)), "kolon": hdr, "bayt": nb}

    # takvim-analiz agg/monthly.parquet var mı? Arayüz matrisi olay tablosundan tarayıcıda hesaplar (eşik/bölge/aralık
    # etkileşimli değişebilsin diye); parquet varlığı manifest'e yazılır, denetçi çapraz karşılaştırır.
    man["monthly_parquet_var"] = (P / "agg" / "monthly.parquet").exists()

    # ---- harmonize: yalnız yıllık TR satırları (sıçrama grafiği); ay düzeyi takvim tablolarından gelir
    h = pd.read_parquet(P / "agg" / "harmonized.parquet")
    h = h[h["duzey"] == "yil_TR"]
    h = h.astype(object).where(h.notna(), None)
    (OUT / "harmonized.json").write_text(json.dumps({c: h[c].tolist() for c in h.columns}, ensure_ascii=False,
                                                    separators=(",", ":"), default=int), encoding="utf-8")

    # ---- takvim-analiz tabloları (tek kaynak, U-19): birim başına bir dosya (cal_<n>.json)
    A = P / "agg"
    sa = pd.read_parquet(A / "seri_aylik.parquet")
    an = pd.read_parquet(A / "anomaly_monthly.parquet")[["birim", "seri", "yil", "ay", "sapma_yuzde", "z", "isaret", "uyari"]]
    sa = sa.merge(an, on=["birim", "seri", "yil", "ay"], how="left")
    pr = pd.read_parquet(A / "profile.parquet")
    cu = pd.read_parquet(A / "current_month.parquet")
    mo_full = pd.read_parquet(A / "monthly.parquet", columns=["birim", "duzey", "yil", "ay", "bayrak"])
    mo = mo_full[["birim", "duzey"]].drop_duplicates()
    duz = dict(zip(mo.birim, mo.duzey))
    y0, y1 = int(sa.yil.min()), int(sa.yil.max())
    N = (y1 - y0 + 1) * 12
    SER = ["olay", "olay_aniz_dahil", "modis_temiz", "modis_temiz_aniz_dahil", "modis_ham", "enerji_modis", "viirs_temiz_ub",
           "viirs_temiz_aniz_dahil_ub", "viirs_ham_ub", "enerji_viirs_ub", "modis_esdeger", "modis_esdeger_aniz_dahil",
           "olay_esdeger", "olay_esdeger_aniz_dahil"]
    man["seri_sirasi"] = [x for x in SER if x in set(sa.seri)]
    man["cal_y0"] = y0
    man["birimler"] = []

    def fl(x):
        a = np.full(N, np.nan); return a

    def lst(a, d=3):
        return [None if not np.isfinite(v) else round(float(v), d) for v in a]

    for n, (b, g) in enumerate(sa.groupby("birim", sort=True)):
        tbl = {"": 0}

        def tid(x):
            x = "" if pd.isna(x) else str(x)
            return tbl.setdefault(x, len(tbl))
        out = {"birim": b, "duzey": duz.get(b, ""), "y0": y0, "seri": {}, "profil": {}, "mevcut": {}}
        for sr, q in g.groupby("seri"):
            i = ((q.yil - y0) * 12 + q.ay - 1).to_numpy()
            def col(c, d=3):
                a = np.full(N, np.nan); a[i] = q[c].to_numpy(dtype=float); return lst(a, d)
            iso = [0] * N; uy = [0] * N; sg = [0] * N
            for k, (a_, b_, c_) in enumerate(zip(q.isaret, q.uyari, q.sensor_gecis)):
                iso[i[k]] = tid(a_); uy[i[k]] = tid(b_); sg[i[k]] = int(bool(c_))
            out["seri"][sr] = {"v": col("deger"), "lo": col("alt"), "hi": col("ust"), "an": col("sapma_yuzde", 1), "z": col("z", 2), "iso": iso, "uy": uy, "sg": sg}
        for sr, q in pr[pr.birim == b].groupby("seri"):
            rows = [None] * 12
            for r in q.itertuples():
                rows[int(r.ay) - 1] = {"n": int(r.n_yil), "med": None if pd.isna(r.medyan) else float(r.medyan), "q1": None if pd.isna(r.q1) else float(r.q1), "q3": None if pd.isna(r.q3) else float(r.q3),
                                       "sira": None if pd.isna(r.sira) else int(r.sira), "top": bool(r.top), "ayirt": bool(r.ayirt_edilemez), "uy": tid(r.uyari)}
            out["profil"][sr] = rows
        for sr, q in cu[cu.birim == b].groupby("seri"):
            out["mevcut"][sr] = [{"hedef": r.hedef, "bas": r.bas, "bit": r.bit, "gun": int(r.gun), "kapsam": r.kapsam, "v": None if pd.isna(r.deger) else float(r.deger),
                                  "med": None if pd.isna(r.tarihsel_medyan) else float(r.tarihsel_medyan), "oran": None if pd.isna(r.oran) else float(r.oran),
                                  "yuzdelik": None if pd.isna(r.yuzdelik) else float(r.yuzdelik), "n_yil": int(r.n_yil), "uy": tid(r.uyari),
                                  "kismi_gun": None if pd.isna(r.kismi_ay_gun) else float(r.kismi_ay_gun), "nrt": None if pd.isna(r.nrt_payi) else float(r.nrt_payi),
                                  "aqua": str(r.aqua_yorunge_kaymasi), "viirs_oran": None if pd.isna(r.viirs_oran) else float(r.viirs_oran),
                                  "yorum": "" if pd.isna(r.ayrisma_yorum) else str(r.ayrisma_yorum), "yorum_etiket": "" if pd.isna(r.ayrisma_yorum_etiket) else str(r.ayrisma_yorum_etiket),
                                  "etiket": "" if pd.isna(r.etiket) else str(r.etiket),
                                  "birincil": str(r.birincil_seri), "guvensiz": bool(r.esdeger_guvenilmez), "neden": "" if pd.isna(r.guvensizlik_nedeni) else str(r.guvensizlik_nedeni),
                                  "mo": None if pd.isna(r.modis_olculen_oran) else float(r.modis_olculen_oran), "vo": None if pd.isna(r.viirs_olculen_oran) else float(r.viirs_olculen_oran)} for r in q.itertuples()]
        bay = [0] * N
        for r in mo_full[mo_full.birim == b].itertuples():
            bay[(int(r.yil) - y0) * 12 + int(r.ay) - 1] = tid(r.bayrak)
        out["bay"] = bay
        out["tablo"] = list(tbl)
        fn = f"cal_{n}.json"
        (OUT / fn).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        man["birimler"].append({"ad": b, "duzey": out["duzey"], "dosya": fn})
    yb = pd.read_parquet(A / "yil_bilgi.parquet")
    man["yil_bilgi"] = {int(r.yil): {"kismi": bool(r.kismi_yil), "normal_olay": bool(r.normal_olay)} for r in yb.itertuples()}

    # ---- noktalar
    pt = pd.read_parquet(P / "points.parquet", columns=["pid", "t_utc", "day_tr", "lat", "lon", "sensor", "sat", "frp",
                                                        "scan", "track", "conf_raw", "conf_cls", "type", "il"])
    pt = pt.merge(pd.read_parquet(P / "points_status.parquet", columns=["pid", "status"]), on="pid")
    pt = pt.merge(pd.read_parquet(P / "points_event.parquet"), on="pid")
    pt = pt.merge(pd.read_parquet(P / "points_mcell.parquet", columns=["pid", "mcell"]), on="pid")
    pt["yil"] = pd.to_datetime(pt["day_tr"]).dt.year
    pg = {}
    for sn, g in pt.groupby("sensor", observed=True):
        sc = g.scan.astype(float)
        cnt, edges = np.histogram(sc, bins=24)
        al = g.scan.astype(float) * g.track.astype(float)
        pg[str(sn)] = {"n": int(len(g)), "bin_kenar": edges.round(3).tolist(), "sayim": cnt.tolist(),
                       "scan_min": float(sc.min()), "scan_p05": float(sc.quantile(.05)), "scan_p50": float(sc.median()),
                       "scan_p95": float(sc.quantile(.95)), "scan_max": float(sc.max()),
                       "alan_p05": float(al.quantile(.05)), "alan_med": float(al.median()),
                       "alan_p95": float(al.quantile(.95)), "alan_max": float(al.max())}
    (OUT / "pixel_growth.json").write_text(json.dumps(pg), encoding="utf-8")
    pt["sat_i"] = pt["sat"].astype(str).map({c: i for i, c in enumerate(SATS)}).astype("uint8")
    pt["st_i"] = pt["status"].astype(str).map({c: i for i, c in enumerate(STATUS)}).astype("uint8")
    pt["il_i"] = pt["il"].astype(str).map(il_ix).fillna(255).astype("uint8")
    cr = pt["conf_raw"].astype(str)
    cv = pd.to_numeric(cr, errors="coerce")
    cv = cv.where(cv.notna(), cr.map({"l": -1, "n": -2, "h": -3})).fillna(-9).astype("int16")
    pt["cv"] = cv
    pt["cc"] = pt["conf_cls"].astype(str).map({"dusuk": 0, "nominal": 1, "yuksek": 2}).fillna(255).astype("uint8")
    pt["cell"] = cell_code(pt["mcell"].astype(str))
    pt["tm"] = tmin(pt["t_utc"])
    pt["day"] = days(pt["day_tr"])
    for y, g in pt.groupby("yil"):
        hdr, nb = wcols(OUT / f"points_{y}.bin", [
            ("pid", g.pid.astype("float64").to_numpy()), ("cell", g.cell.to_numpy()),
            ("lat", g.lat.astype("float32").to_numpy()), ("lon", g.lon.astype("float32").to_numpy()),
            ("tmin", g.tm.to_numpy()), ("evid", g.event_id.astype("int32").to_numpy()), ("day", g.day.to_numpy()),
            ("frp", g.frp.astype("float32").to_numpy()), ("scan", g.scan.astype("float32").to_numpy()),
            ("track", g.track.astype("float32").to_numpy()), ("conf", g.cv.to_numpy()),
            ("sat", g.sat_i.to_numpy()), ("st", g.st_i.to_numpy()), ("cc", g.cc.to_numpy()),
            ("il", g.il_i.to_numpy()), ("tip", g.type.astype("int8").to_numpy())])
        man["points"][int(y)] = {"n": int(len(g)), "kolon": hdr, "bayt": nb}
    first = pt.groupby("sat", observed=True)["day"].min()
    man["sat_ilk_gun"] = {str(k): int(v) for k, v in first.items()}
    man["epoch"] = "2000-01-01"
    man["tr_ofset_dk"] = 180

    # ---- Birleştirme laboratuvarı örnekleri. Kural: 2018 sonrası, MODIS izinde 2..12 VIIRS; eşit aralıklı 8 seçim.
    v = pt[(pt.sensor.astype(str) == "VIIRS") & (pt.cell > 0) & (pt.yil >= 2018)]
    cnt = v.groupby("cell").size()
    cands = np.sort(cnt[(cnt >= 2) & (cnt <= 12)].index.to_numpy())
    pick = cands[np.linspace(0, len(cands) - 1, 8).astype(int)]
    mp = pt[pt.pid.isin(pick.astype("int64"))].set_index("pid")
    ex = []
    for c in pick:
        r = mp.loc[int(c)]
        ex.append({"cell": int(c), "yil": int(r.yil), "day": int(r.day), "lat": float(r.lat), "lon": float(r.lon),
                   "il": str(r.il), "sat": str(r.sat), "n_viirs": int(cnt[c])})
    (OUT / "lab_examples.json").write_text(json.dumps(ex), encoding="utf-8")
    # ---- kapsam
    cv_ = pd.read_parquet(P / "coverage.parquet")
    cov = {"sat": cv_.sat.astype(str).map({c: i for i, c in enumerate(SATS)}).tolist(), "day": days(cv_.day_tr).tolist(),
           "obs": cv_.observed.astype(int).tolist(), "n": cv_.n_tespit.astype(int).tolist(),
           "kaynak": sorted(cv_.source.astype(str).unique().tolist()), "etiket": sorted(cv_.etiket.astype(str).unique().tolist())}
    (OUT / "coverage.json").write_text(json.dumps(cov, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    man["yillar"] = sorted(man["events"])
    man["build_sn"] = round(time.time() - t0, 1)
    man["boyut_mb"] = round(sum(f.stat().st_size for f in OUT.glob("*")) / 1e6, 1)
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    print("tamam", man["build_sn"], "sn;", man["boyut_mb"], "MB;", len(man["events"]), "yıl")


if __name__ == "__main__":
    sys.exit(main())
