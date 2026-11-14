"""Olay arazi örtüsü etiketleme (ESA WorldCover 2021 + OpenStreetMap sanayi katmanı).

Basitçe: Her yangın olayının düştüğü yerin "orman mı, tarla mı, çalılık/otlak mı,
yapılaşmış mı, sanayi mi" olduğunu bağımsız haritalardan okuyup olay sırasıyla ikili dosyaya yazar.

Aşamalar (python arazi_etiket.py wc | osm | yaz | hepsi; ek: nokta = olay dışı durumlar için istatistik etiketi):
  wc   : WorldCover 10 m karolarını (3°x3°) geçici klasöre indirir, her olay merkezinde ~±250 m
         pencerede (enlem 27 px, boylam 250 m / (9.27 m*cos(enlem)) px) sınıf payları ve çoğunluk sınıfı
         hesaplar, karoyu siler. Karo kenarında pencere kırpılır.
  osm  : Overpass API'den landuse=industrial/quarry/landfill, man_made=works, power=plant,
         man_made=flare öğelerini 2°x2° parçalarla çeker (ham yanıt TEMP/osm_raw'da).
         0.001° (~100 m) ızgaraya çizer, 300 m tampon uygular, olay merkezine bakar.
  yaz  : R/arayuz/data/arazi_<yıl>.bin (+ arazi_manifest.json) yazar (olay dosyasıyla aynı sıra).
Çıktı sütunları (uint8, her biri n uzunluğunda, sırayla): wc_maj, p_tree, p_shrub, p_grass, p_crop, p_built, osm.
255 = veri yok. osm: 0 yok, 1 sanayi/işletme/flare, 2 taş ocağı, 3 çöp sahası, 4 enerji santrali (çakışmada 4>3>2>1).
Kaynaklar/lisans: © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021)
processed by ESA WorldCover consortium (CC BY 4.0); © OpenStreetMap contributors, ODbL.
Sınırlar: tek yıl (2021) arazi örtüsü; merkez ±250 m penceresi; OSM tamlığı bölgeye göre değişir.
"""
from __future__ import annotations
import json, sys, time, datetime
from pathlib import Path
import numpy as np
import requests

R = Path(__file__).resolve().parents[3]
DATA = R / "arayuz" / "data"
TEMP = Path(r"C:\Users\Yusuf\AppData\Local\Temp\claude\a2e1d24144cd373a\500b5864-3dfd-4c89-80b7-3d7709bc36b1\scratchpad\landcover")
TEMP.mkdir(parents=True, exist_ok=True)
WC_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{t}_Map.tif"
OVERPASS = "https://overpass-api.de/api/interpreter"
COLS = ["wc_maj", "p_tree", "p_shrub", "p_grass", "p_crop", "p_built", "osm"]
BBOX = (35.8, 25.6, 42.2, 44.9)  # güney, batı, kuzey, doğu
G = 0.001


def olaylar():
    f = TEMP / "events_cache.npz"
    if f.exists():
        z = np.load(f); return z["lat"], z["lon"], z["yil"], z["st"]
    m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    lat, lon, yil, st = [], [], [], []
    for y, info in m["events"].items():
        n = info["n"]; k = {c["ad"]: c for c in info["kolon"]}
        rd = lambda a: np.fromfile(DATA / f"events_{y}.bin", dtype=np.dtype(k[a]["tip"]).newbyteorder("<"), count=n, offset=k[a]["ofs"])
        lat.append(rd("lat")); lon.append(rd("lon")); st.append(rd("st")); yil.append(np.full(n, int(y), np.int16))
    lat, lon, yil, st = map(np.concatenate, (lat, lon, yil, st))
    np.savez(f, lat=lat, lon=lon, yil=yil, st=st)
    return lat, lon, yil, st


def karo(la, lo):
    a = int(np.floor(la / 3) * 3); b = int(np.floor(lo / 3) * 3)
    return f"{'N' if a >= 0 else 'S'}{abs(a):02d}{'E' if b >= 0 else 'W'}{abs(b):03d}"


def wc():
    lat, lon, _, _ = olaylar()
    out, byte = wc_etiketle(lat, lon)
    np.save(TEMP / "wc_out.npy", out)
    (TEMP / "wc_bytes.txt").write_text(str(byte))


def wc_etiketle(lat, lon):
    import rasterio
    out = np.full((len(lat), 6), 255, np.uint8)
    la3 = (np.floor(lat / 3) * 3).astype(int); lo3 = (np.floor(lon / 3) * 3).astype(int)
    key = la3 * 1000 + lo3
    byte = 0; t0 = time.time()
    for kk in np.unique(key):
        idx = np.where(key == kk)[0]
        t = karo(lat[idx[0]], lon[idx[0]])
        fn = TEMP / f"wc_{t}.tif"
        r = requests.get(WC_URL.format(t=t), stream=True, timeout=120)
        if r.status_code != 200:
            print(t, "yok", r.status_code, len(idx), "olay -> 255", flush=True); continue
        with open(fn, "wb") as f:
            for ch in r.iter_content(1 << 20): f.write(ch); byte += len(ch)
        with rasterio.open(fn) as ds:
            a = ds.read(1); T = ds.transform
            rr = ((T.f - lat[idx]) / -T.e).astype(int); cc = ((lon[idx] - T.c) / T.a).astype(int)
            for j, i in enumerate(idx):
                dr = 27; dc = max(1, int(round(250 / (9.27 * np.cos(np.radians(lat[i]))))))
                r0, c0 = rr[j], cc[j]
                if not (0 <= r0 < a.shape[0] and 0 <= c0 < a.shape[1]): continue
                w = a[max(0, r0 - dr):r0 + dr + 1, max(0, c0 - dc):c0 + dc + 1].ravel()
                h = np.bincount(w, minlength=101); tot = h.sum()
                if tot == 0 or h[0] == tot: continue
                out[i, 0] = np.argmax(h)
                for q, c in enumerate((10, 20, 30, 40, 50)):
                    out[i, 1 + q] = int(round(100 * h[c] / tot))
        del a; fn.unlink()
        print(t, len(idx), f"{byte/1e6:.0f} MB", f"{time.time()-t0:.0f}s", flush=True)
    return out, byte


def nokta():
    """Olay dosyasında olmayan durumlar (sanayi, statik_nasa, kalici_belirsiz, ...) yalnız nokta düzeyindedir
    (points_<yıl>.bin). Bu noktaların benzersiz (lat,lon) konumlarını etiketler -> TEMP/nokta_etiket.npz
    (yalnız istatistik içindir; uygulamaya dosya yazılmaz)."""
    m = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    P = []
    for y, p in m["points"].items():
        k = {c["ad"]: c for c in p["kolon"]}; n = p["n"]
        rd = lambda a: np.fromfile(DATA / f"points_{y}.bin", dtype=np.dtype(k[a]["tip"]).newbyteorder("<"), count=n, offset=k[a]["ofs"])
        st = rd("st"); s = ~np.isin(st, [0, 6])  # temiz/aniz olay dosyasında
        P.append(np.column_stack([rd("lat")[s], rd("lon")[s], st[s]]))
    P = np.concatenate(P)
    u, inv = np.unique(P[:, :2], axis=0, return_inverse=True)
    inv = inv.ravel()
    print("nokta:", len(P), "benzersiz konum:", len(u), flush=True)
    out, byte = wc_etiketle(u[:, 0].astype(np.float32), u[:, 1].astype(np.float32))
    np.savez(TEMP / "nokta_etiket.npz", wc=out, osm=osm_etiket(u[:, 0], u[:, 1])[0], inv=inv, st=P[:, 2].astype(np.uint8), ulat=u[:, 0], ulon=u[:, 1], byte=byte)


FILT = ['["landuse"="industrial"]', '["landuse"="quarry"]', '["landuse"="landfill"]', '["man_made"="works"]',
        '["power"="plant"]', '["man_made"="flare"]']


def osm():
    raw = TEMP / "osm_raw"; raw.mkdir(exist_ok=True)
    s, w, n, e = BBOX
    for la in np.arange(s, n, 2.0):
        for lo in np.arange(w, e, 2.0):
            f = raw / f"osm_{la:.1f}_{lo:.1f}.json"
            if f.exists(): continue
            b = f"{la},{lo},{min(la+2,n)},{min(lo+2,e)}"
            q = "[out:json][timeout:300];(" + "".join(f"nwr{x}({b});" for x in FILT) + ");out geom;"
            for deneme in range(4):
                r = requests.post(OVERPASS, data={"data": q}, timeout=400, headers={"User-Agent": "nasa-spaceapps-yangin-takvimi/1.0"})
                if r.status_code == 200: break
                print("overpass", r.status_code, b, "tekrar", flush=True); time.sleep(30 * (deneme + 1))
            else:
                raise SystemExit("overpass basarisiz " + b)
            f.write_bytes(r.content); print(f.name, len(r.content) // 1000, "KB", flush=True); time.sleep(8)


def tip_kodu(tags):
    if tags.get("power") == "plant": return 4
    if tags.get("landuse") == "landfill": return 3
    if tags.get("landuse") == "quarry": return 2
    if tags.get("landuse") == "industrial" or tags.get("man_made") in ("works", "flare"): return 1
    return 0


def osm_etiket(lat, lon):
    from PIL import Image, ImageDraw
    from scipy import ndimage
    s, w, n, e = BBOX
    H = int(round((n - s) / G)); W = int(round((e - w) / G))
    kat = {k: Image.new("L", (W, H), 0) for k in (1, 2, 3, 4)}
    dr = {k: ImageDraw.Draw(v) for k, v in kat.items()}
    seen = set(); nf = {1: 0, 2: 0, 3: 0, 4: 0}
    px = lambda la, lo: ((lo - w) / G, (n - la) / G)
    for f in sorted((TEMP / "osm_raw").glob("osm_*.json")):
        for el in json.loads(f.read_text(encoding="utf-8")).get("elements", []):
            key = (el["type"], el["id"])
            if key in seen: continue
            seen.add(key); k = tip_kodu(el.get("tags", {}))
            if not k: continue
            nf[k] += 1
            if el["type"] == "node":
                dr[k].point(px(el["lat"], el["lon"]), 255)
            elif el["type"] == "way" and "geometry" in el:
                pts = [px(p["lat"], p["lon"]) for p in el["geometry"]]
                if len(pts) >= 3: dr[k].polygon(pts, fill=255)
                dr[k].line(pts, fill=255)
            elif el["type"] == "relation":
                for m in el.get("members", []):
                    if m.get("geometry") and m.get("role") in ("outer", ""):
                        pts = [px(p["lat"], p["lon"]) for p in m["geometry"]]
                        if len(pts) >= 3: dr[k].polygon(pts, fill=255)
                        dr[k].line(pts, fill=255)
    # 300 m tampon: enlemde 3 hücre (~333 m), boylamda 4 hücre (~340 m @ 39°N)
    st = np.ones((7, 9), bool)
    flag = np.zeros(len(lat), np.uint8)
    ri = np.clip(((n - lat) / G).astype(int), 0, H - 1); ci = np.clip(((lon - w) / G).astype(int), 0, W - 1)
    for k in (1, 2, 3, 4):  # büyük kod sonra yazılır -> öncelik 4>3>2>1
        a = ndimage.binary_dilation(np.asarray(kat[k]) > 0, structure=st)
        flag[a[ri, ci]] = k; del a
    print("OSM öğe sayıları (tür 1..4):", nf, flush=True)
    return flag, nf


def yaz():
    lat, lon, yil, st = olaylar()
    wcm = np.load(TEMP / "wc_out.npy")
    osmf, nf = osm_etiket(lat, lon)
    tum = np.column_stack([wcm, osmf]).astype(np.uint8)
    np.save(TEMP / "arazi_tum.npy", tum)
    man = {}
    for y in np.unique(yil):
        m = yil == y; n = int(m.sum())
        (DATA / f"arazi_{y}.bin").write_bytes(b"".join(np.ascontiguousarray(tum[m, j]).tobytes() for j in range(7)))
        man[str(y)] = {"n": n}
    bf = TEMP / "wc_bytes.txt"
    nb = int(bf.read_text()) if bf.exists() else None
    js = {"arazi": {
        "kolonlar": [{"ad": c, "tip": "uint8", "kolon_no": j} for j, c in enumerate(COLS)],
        "ofset_kurali": "kolon j baslangic bayti = j * n (n = manifest.json events[yil].n); sira events_<yil>.bin ile ayni",
        "yillar": man,
        "wc_siniflari": {"10": "agac", "20": "cali", "30": "cayir", "40": "ekili_alan", "50": "yapilasmis", "60": "ciplak",
                         "70": "kar_buz", "80": "su", "90": "sulak", "95": "mangrov", "100": "yosun_liken", "255": "veri_yok"},
        "pay_kolonlari": "p_* = olay merkezi +-250 m penceredeki piksel yuzdesi 0-100; diger = 100 - toplam; 255 = veri yok",
        "osm_kodlari": {"0": "yok", "1": "sanayi/isletme/flare", "2": "tas ocagi", "3": "cop sahasi", "4": "enerji santrali"},
        "osm_kurali": "merkez poligon icinde veya ~300 m icinde (0.001 derece izgara, enlem 3/boylam 4 hucre tampon); oncelik 4>3>2>1",
        "osm_ogeleri": {str(k): v for k, v in nf.items()},
        "kaynaklar": [
            {"ad": "ESA WorldCover 10 m v200 (2021)", "url": WC_URL, "lisans": "CC BY 4.0",
             "atif": "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium"},
            {"ad": "OpenStreetMap (Overpass API)", "url": OVERPASS, "lisans": "ODbL",
             "atif": "© OpenStreetMap contributors, ODbL"}],
        "olusturma_tarihi": datetime.date.today().isoformat(),
        "indirilen_wc_mb": round(nb / 1e6) if nb else None,
        "sinirlar": ["Tek yil (2021) arazi ortusu; 2000-2026 olaylari icin degisim yok sayilir",
                     "Olay merkezi +-250 m penceresi; buyuk olaylarin tamamini temsil etmez",
                     "Karo kenarinda pencere kirpilir", "OSM tamligi bolgeye gore degisir; bos = 'sanayi degil' demek degildir",
                     "OSM cokgenlerinin ic bosluklari (inner) doldurulur"]}}
    (DATA / "arazi_manifest.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi", len(man), "yil")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if a in ("wc", "hepsi"): wc()
    if a == "nokta": nokta()
    if a in ("osm", "hepsi"): osm()
    if a in ("yaz", "hepsi"): yaz()
