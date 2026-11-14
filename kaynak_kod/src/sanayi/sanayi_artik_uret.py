"""Sanayi alanı artıkları (`sanayi_osm_artik`): isteğe bağlı bayrak dosyaları üretir.

Basitçe: OSB/fabrika sahalarında yıllarca, her mevsim küçük (çoğu tek pikselli) ısı tespiti gelir; kalıcı-kaynak kuralı bunları
yakalayamadı ve 'temiz' kaldılar. Burada bu olaylar ayrıca işaretlenir (etiket/sayı değişmez; arayüz isteğe bağlı gizler/çıkarır).
Mevcut hiçbir veri dosyası değiştirilmez.

Teknik olarak (sanayi_denetimi.md, öneri + sıkı muafiyet): olay `temiz` (st=0) ve
  (osm=1  veya  osm=4 ve OSM öğesi plant:source solar/wind/hydro/geothermal DEĞİL)  ve
  saha (<=350 m'deki OSM öğesi; yoksa 0,01° hücre) >= 5 farklı yılda temiz-osm olay üretmiş ve >= 6 farklı takvim ayına yayılmış
  ve olay küçük (frp_max < 100 MW, tespit <= 5)  ve
  15 km / +-3 gün içinde büyük temiz olay (frp_max >= 300 veya >= 20 tespit) yok  ve
  [SIKI MUAFİYET] resmi_yangin_listesi.json'daki bir yangının 40 km ve (başlangıç-2 .. başlangıç+35 gün; kontrol tarihi varsa
  kontrol+5 güne kadar) penceresinde DEĞİL ve olay_id gercek_dogrulama.json / recall_olcumu.json'da DEĞİL.
Girdi: arayuz/data (events/arazi bin), OSM ham yanıtları (arazi_etiket.py osm aşaması; --osm klasörü).
Çıktı: arayuz/data/sanayi_artik_<yıl>.bin (uint8, events_<yıl>.bin sırası; 1 = sanayi artığı), arayuz/data/sanayi_artik_manifest.json
Çalıştırma: python sanayi_artik_uret.py [--osm <osm_raw klasörü>]
"""
from __future__ import annotations
import argparse, collections, glob, json, math, pathlib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

R = pathlib.Path(__file__).resolve().parents[3]
D = R / "arayuz" / "data"
OSM_DEFAULT = pathlib.Path(__file__).resolve().parents[2] / "veri_ham" / "osm_sanayi"  # OSM Overpass (ODbL)
NOT_THERMAL = {"solar", "wind", "hydro", "geothermal"}
MIN_YRS, MIN_MON, FRP_MAX, N_MAX = 5, 6, 100.0, 5
BIG_FRP, BIG_N, GUARD_KM, GUARD_D = 300.0, 20, 15.0, 3
DOC_KM, DOC_PRE, DOC_POST = 40.0, 2, 35


def tipk(t):
    if t.get("power") == "plant": return 4
    if t.get("landuse") == "landfill": return 3
    if t.get("landuse") == "quarry": return 2
    if t.get("landuse") == "industrial" or t.get("man_made") in ("works", "flare"): return 1
    return 0


def load_osm(folder):
    feats = {}
    for f in sorted(glob.glob(str(folder / "*.json"))):
        for el in json.load(open(f, encoding="utf-8"))["elements"]:
            k = (el["type"], el["id"])
            if k in feats: continue
            t = el.get("tags", {}); c = tipk(t)
            if not c: continue
            if "bounds" in el: b = el["bounds"]; bb = (b["minlat"], b["minlon"], b["maxlat"], b["maxlon"])
            elif "lat" in el: bb = (el["lat"], el["lon"], el["lat"], el["lon"])
            elif "center" in el: bb = (el["center"]["lat"], el["center"]["lon"]) * 2
            else: continue
            nm = t.get("name") or t.get("name:en") or t.get("operator") or t.get("brand") or ""
            sub = t.get("industrial") or t.get("plant:source") or t.get("generator:source") or t.get("product") or t.get("man_made") or t.get("landuse") or ""
            feats[k] = (c, bb, sub, nm)
    return feats


def dist_m(lat, lon, bb):
    dy = max(bb[0] - lat, 0, lat - bb[2]) * 111000; dx = max(bb[1] - lon, 0, lon - bb[3]) * 111000 * math.cos(math.radians(lat))
    return math.hypot(dx, dy)


def match_sites(T, feats):
    keys = list(feats); grid = collections.defaultdict(list)
    for i, k in enumerate(keys):
        bb = feats[k][1]
        for iy in range(int((bb[0] - .004) * 100), int((bb[2] + .004) * 100) + 1):
            if (bb[2] - bb[0]) > 0.5: break
            for ix in range(int((bb[1] - .005) * 100), int((bb[3] + .005) * 100) + 1):
                grid[(iy, ix)].append(i)
    fid, src = [], []
    Fn = {k[1]: v for k, v in feats.items()}  # kimlik çakışmasında son öğe (denetim betiğiyle aynı davranış)
    for lat, lon, o in zip(T.lat.values, T.lon.values, T.osm.values):
        best = None
        for i in grid.get((int(lat * 100), int(lon * 100)), []):
            c, bb, sub, nm = feats[keys[i]]
            if c != o: continue
            d = dist_m(lat, lon, bb)
            if d <= 350 and (best is None or d < best[0] or (d == best[0] and nm and not best[2])): best = (d, i, nm)  # eşit uzaklıkta adlı öğe öncelikli
        if best is None:
            for i in grid.get((int(lat * 100), int(lon * 100)), []):
                c, bb, sub, nm = feats[keys[i]]; d = dist_m(lat, lon, bb)
                if d <= 350 and (best is None or d < best[0]): best = (d, i, nm)
        f = keys[best[1]][1] if best else -1
        fid.append(f); v = Fn.get(f); src.append(v[2] if v and v[0] == 4 else ("" if not v else "-"))
    return np.array(fid), np.array(src)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--osm", default=str(OSM_DEFAULT)); a = ap.parse_args()
    M = json.loads((D / "manifest.json").read_text(encoding="utf-8")); ils = M["ils"]
    fr = []
    for y in M["yillar"]:
        s = M["events"][str(y)]; n = s["n"]; b = (D / f"events_{y}.bin").read_bytes()
        df = pd.DataFrame({c["ad"]: np.frombuffer(b, dtype=np.dtype(c["tip"]).newbyteorder("<"), count=n, offset=c["ofs"]) for c in s["kolon"]})
        df["osm"] = np.frombuffer((D / f"arazi_{y}.bin").read_bytes(), dtype=np.uint8).reshape(7, n)[6]; df["yr"] = y; fr.append(df)
    E = pd.concat(fr, ignore_index=True)
    E["n"] = E.n_modis + E.n_viirs
    E["t0"] = np.datetime64("2000-01-01") + E.tmin.values.astype("timedelta64[m]")
    E["mon"] = pd.DatetimeIndex(E.t0).month
    T = E[(E.st == 0) & (E.osm > 0)].copy()
    feats = load_osm(pathlib.Path(a.osm))
    fid, src = match_sites(T, feats)
    T["fid"] = fid; T["src"] = src
    T["site"] = np.where(T.fid > 0, T.fid.astype(str), "c" + np.floor(T.lat * 100).astype(int).astype(str) + "_" + np.floor(T.lon * 100).astype(int).astype(str))
    T["site_yrs"] = T.site.map(T.groupby("site").yr.nunique()); T["site_mon"] = T.site.map(T.groupby("site").mon.nunique())
    thermal = T.osm.eq(1) | (T.osm.eq(4) & ~T.src.isin(NOT_THERMAL))
    big = (T.frp_max >= BIG_FRP) | (T.n >= BIG_N)
    moved = thermal & (T.site_yrs >= MIN_YRS) & (T.site_mon >= MIN_MON) & (T.frp_max < FRP_MAX) & (T.n <= N_MAX) & ~big
    # komşu-büyük koruması: 15 km / +-3 gün içinde büyük temiz olay
    B = E[(E.st == 0) & ((E.frp_max >= BIG_FRP) | (E.n >= BIG_N))]
    xy = lambda d: np.c_[d.lat.values * 111, d.lon.values * 111 * np.cos(np.radians(39))]
    tr = cKDTree(xy(B)); tb = B.tmin.values; guard = np.zeros(len(T), bool)
    for i, (l, tt) in enumerate(zip(tr.query_ball_point(xy(T), GUARD_KM), T.tmin.values)):
        for j in l:
            if abs(tb[j] - tt) <= GUARD_D * 1440: guard[i] = True; break
    T["guard"] = guard
    m0 = moved & ~T.guard
    # sıkı muafiyet: belgelenmiş yangın pencereleri ve belgeli olaylar
    g1 = json.loads((R / "belgeler_ve_denetim" / "gercek_dogrulama.json").read_text(encoding="utf-8"))["olaylar"]
    rc = json.loads((R / "belgeler_ve_denetim" / "recall_olcumu.json").read_text(encoding="utf-8"))["sonuclar"]
    ids = sorted({x["event_id"] for x in g1} | {x["event_id"] for x in rc if x.get("event_id")})
    yl = json.loads((R / "belgeler_ve_denetim" / "resmi_yangin_listesi.json").read_text(encoding="utf-8"))["yanginlar"]
    docw = np.zeros(len(T), bool)
    for x in yl:
        if x["yaklasik_lat"] is None: continue
        b0 = np.datetime64(x["baslangic"])
        t0 = b0 - np.timedelta64(DOC_PRE, "D"); t1 = b0 + np.timedelta64(DOC_POST, "D")
        if x["kontrol"]: t1 = max(t1, np.datetime64(x["kontrol"]) + np.timedelta64(5, "D"))
        dlat = (T.lat.values - x["yaklasik_lat"]) * 111; dlon = (T.lon.values - x["yaklasik_lon"]) * 111 * np.cos(np.radians(x["yaklasik_lat"]))
        docw |= (np.hypot(dlat, dlon) <= DOC_KM) & (T.t0.values >= t0) & (T.t0.values <= t1)
    T["docwin"] = docw | T.evid.isin(ids).values
    final = m0 & ~T.docwin
    E["flag"] = 0; E.loc[final[final].index, "flag"] = 1
    off = 0; per_year = {}
    for y in M["yillar"]:
        k = M["events"][str(y)]["n"]; v = E.flag.values[off:off + k].astype(np.uint8); off += k
        (D / f"sanayi_artik_{y}.bin").write_bytes(v.tobytes()); per_year[str(y)] = int(v.sum())
    assert off == len(E)
    F = T[final]
    ver = {"isaretli_olay": int(final.sum()), "kural_oncesi_muafiyet": int(m0.sum()), "muafiyetle_cikarilan": int((m0 & T.docwin).sum()),
           "komsu_buyuk_korumasiyla_cikarilan": int((moved & T.guard).sum()), "saha_sayisi": int(F.site.nunique()), "il_sayisi": int(F.il.nunique()),
           "temiz_olay": int((E.st == 0).sum()), "frp_100_ustu": int((F.frp_max >= 100).sum()), "tespit_10_ustu": int((F.n >= 10).sum()),
           "buyuk_olay": int(((F.frp_max >= BIG_FRP) | (F.n >= BIG_N)).sum()), "en_buyuk_frp_max": float(F.frp_max.max()), "en_cok_tespit": int(F.n.max()),
           "belgeli_olay_etkilenen": int(F.evid.isin(ids).sum()),
           "resmi_pencere_icinde": int(F.docwin.sum()),
           "il_en_cok": {ils[i]: int(v) for i, v in F.il.value_counts().head(8).items()}}
    (D / "sanayi_artik_manifest.json").write_text(json.dumps({"kural": "sanayi_osm_artik (sanayi_denetimi.md) + sıkı muafiyet", "yillik_isaretli": per_year, "dogrulama": ver}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ver, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
