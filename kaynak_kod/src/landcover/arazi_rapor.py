"""arazi_<yıl>.bin sonuçlarından özet istatistik üretir -> belgeler_ve_denetim/arazi_ortusu.md (+ stdout özeti).
Önce arazi_etiket.py çalışmış olmalı. Çalıştırma: python arazi_rapor.py
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from pathlib import Path
import arazi_etiket as A

R = A.R; DATA = A.DATA
man = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
am = json.loads((DATA / "arazi_manifest.json").read_text(encoding="utf-8"))["arazi"]
STAT = man["status"]
rows = []
for y, info in man["events"].items():
    n = info["n"]; k = {c["ad"]: c for c in info["kolon"]}
    d = {a: np.fromfile(DATA / f"events_{y}.bin", dtype=np.dtype(k[a]["tip"]).newbyteorder("<"), count=n, offset=k[a]["ofs"])
         for a in ("evid", "lat", "lon", "frp_max", "n_modis", "n_viirs", "st")}
    raw = np.fromfile(DATA / f"arazi_{y}.bin", dtype=np.uint8)
    for j, c in enumerate(A.COLS): d[c] = raw[j * n:(j + 1) * n]
    d["yil"] = np.full(n, int(y)); rows.append(pd.DataFrame(d))
df = pd.concat(rows, ignore_index=True)
df["durum"] = df["st"].map(lambda i: STAT[i])
df["wc_ok"] = df["wc_maj"] != 255
df["diger"] = np.where(df.wc_ok, 100 - df[["p_tree", "p_shrub", "p_grass", "p_crop", "p_built"]].astype(float).sum(axis=1), np.nan)
SN = {10: "ağaç", 20: "çalılık", 30: "otlak", 40: "tarla", 50: "yapılaşmış", 60: "çıplak", 70: "kar", 80: "su", 90: "sulak", 95: "mangrov", 100: "yosun"}
OS = {0: "yok", 1: "sanayi", 2: "taş ocağı", 3: "çöp sahası", 4: "santral"}

z = np.load(A.TEMP / "nokta_etiket.npz")
pf = pd.DataFrame(z["wc"][z["inv"]], columns=["wc_maj", "p_tree", "p_shrub", "p_grass", "p_crop", "p_built"])
pf["osm"] = z["osm"][z["inv"]]; pf["durum"] = [STAT[i] for i in z["st"]]; pf["loc"] = z["inv"]
pf["wc_ok"] = pf.wc_maj != 255
pf["diger"] = np.where(pf.wc_ok, 100 - pf[["p_tree", "p_shrub", "p_grass", "p_crop", "p_built"]].astype(float).sum(axis=1), np.nan)
ALL = pd.concat([df.assign(birim="olay"), pf.assign(birim="nokta")], ignore_index=True)

L = []
w = L.append
w("# Arazi örtüsü katmanı (WorldCover 2021 + OpenStreetMap)\n")
w("Her yangın olayına, düştüğü yerin arazi türünü bağımsız haritalardan ekledik. Böylece uygulama \"orman yangını adayı\" tahmini yerine ölçülmüş bir sınıf (orman / tarla / çalılık-otlak / yapılaşmış / sanayi) söyleyebilir.\n")
w("## Yöntem\n")
w("- **ESA WorldCover 2021 (10 m, v200)**: 3°x3° karolar indirildi (AWS açık veri), her olay merkezinin çevresinde yaklaşık ±250 m'lik pencerede (enlemde 27 piksel, boylamda enleme göre ~35 piksel; ~51x51-71 piksel) sınıf yüzdeleri hesaplandı: ağaç (10), çalılık (20), otlak (30), tarla (40), yapılaşmış (50), gerisi \"diğer\". Çoğunluk sınıfı da saklandı. Veri yoksa 255.")
w("- **OpenStreetMap (Overpass API)**: landuse=industrial, landuse=quarry, landuse=landfill, man_made=works, power=plant, man_made=flare öğeleri 2°x2° parçalarla çekildi (ham yanıt geçici klasörde). 0,001° (~100 m) ızgaraya çizilip 300 m tampon uygulandı; olay merkezi tampon içindeyse bayrak: 1 sanayi/işletme/flare, 2 taş ocağı, 3 çöp sahası, 4 enerji santrali (çakışmada 4>3>2>1).")
w("- **Çıktı**: `arayuz/data/arazi_<yıl>.bin` (7 uint8 sütun: wc_maj, p_tree, p_shrub, p_grass, p_crop, p_built, osm; olay dosyasıyla aynı sıra; kolon j başlangıcı = j*n) ve `arazi_manifest.json`.")
w("- **Kod**: `kaynak_kod/src/landcover/arazi_etiket.py` (üretim), `arazi_rapor.py` (bu belge).\n")
w("## Kaynaklar ve lisans\n")
w("- © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium. Lisans CC BY 4.0. https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/")
w("- © OpenStreetMap contributors, ODbL. Overpass API (https://overpass-api.de/api/interpreter).\n")
w("## Sınırlar\n")
w("- Arazi örtüsü tek yıla (2021) aittir; 2000-2026 olaylarında arazi değişimi (yangın sonrası kül/yanık alan, yeni yapılaşma, tarla-orman dönüşümü) yok sayılır. 2021 yangınlarında harita yangından önceki-sonraki sahneye bağlı olabilir.")
w("- Merkez ±250 m penceresi büyük olayların tamamını temsil etmez; olay merkezi yangının ağırlık merkezidir.")
w("- OSM tamlığı bölgeye göre değişir; OSM bayrağı yok demek \"sanayi değil\" demek değildir. İç boşluklu (inner) OSM çokgenleri doldurulur. WorldCover'ın kendi doğruluğu ayrıca sınırlıdır (üretici raporu).")
w("- Karo kenarındaki olaylarda pencere karoda kırpılır.\n")

def dagit(sub):
    c = sub[sub.wc_ok]["wc_maj"].value_counts(normalize=True) * 100
    return ", ".join(f"{SN.get(int(k), k)} {v:.0f}%" for k, v in c.head(4).items())

w("## 1. Olay durumuna göre arazi özeti\n")
w("| durum (birim) | sayı | WC verisi var | ort. ağaç % | çalılık % | otlak % | tarla % | yapılaşmış % | diğer % | OSM bayrağı % | çoğunluk sınıfı |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
for s in STAT:
    sub = ALL[ALL.durum == s]; ok = sub[sub.wc_ok]
    if not len(sub): continue
    bi = sub.birim.iloc[0]
    w(f"| {s} ({bi}) | {len(sub):,} | {len(ok):,} | " + " | ".join(f"{ok[c].mean():.1f}" for c in ("p_tree", "p_shrub", "p_grass", "p_crop", "p_built", "diger"))
      + f" | {(sub.osm > 0).mean() * 100:.1f} | {dagit(sub)} |")
w(f"\nBirim: events dosyasında yalnız temiz ve aniz olay olarak bulunur ({len(df):,} olay; WC verisi olmayan: {(~df.wc_ok).sum():,}); diğer durumlar yalnız tespit noktası düzeyindedir (points_<yıl>.bin), tablo nokta sayısıdır ({pf['loc'].nunique():,} benzersiz konum).\n")

w("## 2. Sanayi / statik NASA etiketi ile bağımsız haritaların uyumu\n")
def uy(sub):
    return ((sub.osm > 0) | (sub.wc_ok & (sub.wc_maj == 50)))
for s_ in ("sanayi", "statik_nasa", "kalici_belirsiz"):
    sub = pf[pf.durum == s_]
    if not len(sub): continue
    ul = sub.drop_duplicates("loc")
    w(f"- **{s_}** ({len(sub):,} nokta, {len(ul):,} benzersiz konum): OSM bayrağı nokta {(sub.osm > 0).mean() * 100:.1f}% / konum {(ul.osm > 0).mean() * 100:.1f}%; WC çoğunluk yapılaşmış {(sub.wc_maj == 50).mean() * 100:.1f}% / {(ul.wc_maj == 50).mean() * 100:.1f}%; WC yapılaşmış payı ≥%20 {((sub.p_built >= 20) & sub.wc_ok).mean() * 100:.1f}% / {((ul.p_built >= 20) & ul.wc_ok).mean() * 100:.1f}%; **OSM veya WC-yapılaşmış {uy(sub).mean() * 100:.1f}% / {uy(ul).mean() * 100:.1f}%**.")
ss = pf[pf.durum.isin(["sanayi", "statik_nasa"])]; su = ss.drop_duplicates("loc")
w(f"\nSanayi+statik_nasa birlikte: OSM veya WC çoğunluk yapılaşmış uyumu **%{uy(ss).mean() * 100:.1f} (nokta), %{uy(su).mean() * 100:.1f} (benzersiz konum)**; OSM ya da WC yapılaşmış payı ≥%20 ile gevşetilirse %{(((ss.osm > 0) | ((ss.p_built >= 20) & ss.wc_ok)).mean() * 100):.1f} (nokta).")
tm = df[df.durum == "temiz"]
w(f"\nTemiz olaylar ({len(tm):,}): OSM veya WC çoğunluk yapılaşmış **%{uy(tm).mean() * 100:.1f}** (olası kaçırılmış sanayi; OSM tek başına %{(tm.osm > 0).mean() * 100:.2f}, WC yapılaşmış tek başına %{(tm.wc_maj == 50).mean() * 100:.2f}); bunlardan OSM sanayi (kod 1) %{(tm.osm == 1).mean() * 100:.2f}, taş ocağı %{(tm.osm == 2).mean() * 100:.2f}, çöp sahası %{(tm.osm == 3).mean() * 100:.2f}, santral %{(tm.osm == 4).mean() * 100:.2f}. Yüksek FRP'li (frp_max ≥ 300 MW) temiz olaylarda: %{uy(tm[tm.frp_max >= 300]).mean() * 100:.1f} ({len(tm[tm.frp_max >= 300]):,} olay).\n")

w("## 3. Belgelenmiş gerçek orman yangınları (gercek_dogrulama.json)\n")
gd = json.loads((R / "belgeler_ve_denetim" / "gercek_dogrulama.json").read_text(encoding="utf-8"))
ids = [o["event_id"] for o in gd["olaylar"] if o.get("kaynak_turu") != "yok"]  # kaynaksız (ör. 99294) olay hariç
g = df[df.evid.isin(ids)].copy()
g["tc"] = g.p_tree + g.p_shrub
names = {o["event_id"]: o["yangin_adi"] for o in gd["olaylar"]}
w("| olay | ad | durum | ağaç % | çalılık % | otlak % | tarla % | yapılaşmış % | ağaç+çalılık % | çoğunluk | OSM |")
w("|---|---|---|---:|---:|---:|---:|---:|---:|---|---|")
for _, r in g.sort_values("tc").iterrows():
    w(f"| {r.evid} | {(names[r.evid] or '-')[:45]} | {r.durum} | {r.p_tree} | {r.p_shrub} | {r.p_grass} | {r.p_crop} | {r.p_built} | {r.tc} | {SN.get(int(r.wc_maj), r.wc_maj)} | {OS[int(r.osm)]} |")
gv = g[g.wc_ok]
w(f"\n{len(gv)} olayda veri var. Ağaç payı: medyan {gv.p_tree.median():.0f}, min {gv.p_tree.min()}, 25. yüzdelik {gv.p_tree.quantile(.25):.0f}. Ağaç+çalılık: medyan {gv.tc.median():.0f}, min {gv.tc.min()}, 25. yüzdelik {gv.tc.quantile(.25):.0f}.")
for t in (30, 40, 50, 60):
    w(f"- ağaç+çalılık ≥ %{t}: gerçek orman yangınlarının {(gv.tc >= t).mean() * 100:.0f}% ({(gv.tc >= t).sum()}/{len(gv)}); tüm temiz olayların {((df.durum == 'temiz') & df.wc_ok & (df.p_tree + df.p_shrub >= t)).sum() / ((df.durum == 'temiz') & df.wc_ok).sum() * 100:.0f}%")
for t in (20, 30, 40, 50):
    w(f"- ağaç ≥ %{t}: gerçek orman yangınlarının {(gv.p_tree >= t).mean() * 100:.0f}% ({(gv.p_tree >= t).sum()}/{len(gv)}); tüm temiz olayların {((df.durum == 'temiz') & df.wc_ok & (df.p_tree >= t)).sum() / ((df.durum == 'temiz') & df.wc_ok).sum() * 100:.0f}%")
tt = (df.durum == "temiz") & df.wc_ok
n30 = int((gv.tc >= 30).sum()); n50 = int((gv.p_tree >= 50).sum())
w(f"\n**Öneri (rakamlara dayalı):** 'orman/çalılık yangını' sınıfı için p_tree + p_shrub ≥ %30 (belgeli {len(gv)} olayın {n30}'i geçer; en düşük ağaç+çalılık payı %{int(gv.tc.min())}). Tüm temiz olayların %{((df.p_tree + df.p_shrub >= 30) & tt).sum() / tt.sum() * 100:.1f}'i bu sınıfa girer. Sıkı 'orman' için p_tree ≥ %50 (belgeli olayların {n50}/{len(gv)}'ü; Ege/Akdeniz maki-çalılık yangınlarında ağaç payı düşük kalır, bu yüzden çalılığı da sayan eşik daha güvenlidir). Belgeli {len(gv)} olay küçük bir örneklemdir; eşik bir ölçüt önerisidir, kesin sınır değildir. Kaynaksız Adana 2012 (99294) olayı tarla çıktığı için (WC tarla %{int(df[df.evid == 99294].p_crop.iloc[0])}) istatistiğe alınmadı.\n")

w("## 4. En yüksek FRP'li 10 temiz olay (≥2 tespit)\n")
tp = df[(df.durum == "temiz") & (df.n_modis + df.n_viirs >= 2)].nlargest(10, "frp_max")
w("| evid | yıl | frp_max | tespit | ağaç % | çalılık % | tarla % | yapılaşmış % | çoğunluk | OSM |")
w("|---|---|---:|---:|---:|---:|---:|---:|---|---|")
for _, r in tp.iterrows():
    w(f"| {r.evid} | {r.yil} | {r.frp_max:.0f} | {r.n_modis + r.n_viirs} | {r.p_tree} | {r.p_shrub} | {r.p_crop} | {r.p_built} | {SN.get(int(r.wc_maj), r.wc_maj)} | {OS[int(r.osm)]} |")
out = R / "belgeler_ve_denetim" / "arazi_ortusu.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
