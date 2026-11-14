"""İl bazlı anız eşiği (varyant T + tavan 1,5x): isteğe bağlı bayrak dosyaları üretir.

Basitçe: ulusal anız kuralı "olaydaki tüm noktalar ulusal FRP medyanından küçük" der. Tarım ovası illerinde (Şanlıurfa, Adana,
Diyarbakır...) tek bir tarla yakması yüksek FRP verdiği için bu kural bazı anızları kaçırır. Burada eşik, ilin kendi 'temiz'
noktalarının medyanına yükseltilir (ulusaldan düşük olamaz, ulusalın 1,5 katından yüksek olamaz). Yalnız EK anız bulunur;
mevcut anız (st=6) olaylar aynen kalır; mevcut hiçbir veri dosyası değişmez.

Teknik olarak: sim.py/full.py/cap.py simülasyonunun (il_bazli_aniz_analizi.md) yeniden üretilebilir hâli.
  F[il, sensör] = clip( medyan( FRP of st==0 noktaları, il x sensör ), ulusal, 1,5 x ulusal ); n(il,sensör) < 300 ise bölge
  medyanı, o da yoksa ulusal. Ulusal: MODIS 15,0 MW, VIIRS 4,4 MW (esikler.json ile aynı).
  Olay anızdır eğer: n_mcell vekili <= 3 (max(n_modis, ceil(n_viirs/4))), süre <= 12 sa, TR başlangıç ayı bölgenin o yıl hariç
  anız aylarında (aniz_takvimi.json yil_aylar_loyo) ve olaydaki tüm MODIS noktaları < F_modis ve tüm VIIRS noktaları < F_viirs.
Çıktı: arayuz/data/aniz_il_<yıl>.bin  (uint8, events_<yıl>.bin ile aynı sıra; 1 = yalnız il bazlı kuralla anız, yalnız st==0 olaylar)
       arayuz/data/aniz_il_manifest.json (eşik tablosu, yıl sayıları, doğrulama)
Çalıştırma: python aniz_il_uret.py   (okunan: events/points bin + manifest + audit/aniz_takvimi.json; yazılan: yalnız yeni dosyalar)
"""
from __future__ import annotations
import json, pathlib, math
import numpy as np
import pandas as pd

R = pathlib.Path(__file__).resolve().parents[3]
D = R / "arayuz" / "data"
FM0, FV0 = 15.0, 4.400000095367432   # ulusal anız FRP eşikleri (MODIS, VIIRS), MW
MINN, CAP = 300, 1.5                  # il x sensör için asgari nokta sayısı; tavan çarpanı


def rd(M, kind, y):
    info = M[kind][str(y)]; n = info["n"]; b = (D / f"{kind}_{y}.bin").read_bytes()
    return pd.DataFrame({c["ad"]: np.frombuffer(b, dtype=np.dtype(c["tip"]).newbyteorder("<"), count=n, offset=c["ofs"]) for c in info["kolon"]})


def load(M, kind):
    fr = []
    for y in M["yillar"]:
        d = rd(M, kind, y); d["yil"] = y; fr.append(d)
    return pd.concat(fr, ignore_index=True)


def main():
    M = json.loads((D / "manifest.json").read_text(encoding="utf-8")); ils = M["ils"]; ilb = M["il_bolge"]
    E = load(M, "events"); P = load(M, "points")
    T = json.loads((R / "kaynak_kod" / "audit" / "aniz_takvimi.json").read_text(encoding="utf-8"))
    P["mod"] = P.sat.isin([0, 1]).to_numpy(); P["ilad"] = [ils[i] if i < len(ils) else "?" for i in P.il]
    E["ilad"] = [ils[i] for i in E.il]
    # olay başına en yüksek MODIS / VIIRS FRP (yoksa -1; noktası hiç olmayan olay NaN -> anız olmaz)
    p = P[P.evid >= 0]
    mx = p.assign(fm=np.where(p["mod"], p.frp, -1.0), fv=np.where(~p["mod"], p.frp, -1.0)).groupby("evid")[["fm", "fv"]].max()
    E["fm"] = mx.fm.reindex(E.evid).values; E["fv"] = mx.fv.reindex(E.evid).values
    tr = pd.to_datetime("2000-01-01") + pd.to_timedelta(E.tmin + 180, unit="m")
    E["yr"] = tr.dt.year.values; E["mon"] = tr.dt.month.values
    mp = {"Guneydogu": "Güneydoğu Anadolu", "IcAnadolu": "İç Anadolu", "DoguAnadolu": "Doğu Anadolu"}
    E["bolge"] = [mp.get(ilb.get(ils[i], "?"), ilb.get(ils[i], "?")) for i in E.il]
    lut = {(int(y), b, int(m)) for y, bm in T["yil_aylar_loyo"].items() for b, ms in bm.items() for m in ms}
    ay_ok = np.array([(a, b, c) in lut for a, b, c in zip(E.yr, E.bolge, E.mon)])
    h = E.dur.to_numpy() / 60.0
    proxy = np.maximum(E.n_modis.to_numpy(), np.ceil(E.n_viirs.to_numpy() / 4))
    base = ((E.st == 6).to_numpy() | (proxy <= 3)) & (h <= 12) & ay_ok
    # eşikler: il temiz (st==0) noktalarının medyanı, ulusal taban, 1,5x tavan
    sub = P[P.st == 0]
    g = sub.groupby(["ilad", "mod"]).frp.median(); n = sub.groupby(["ilad", "mod"]).size()
    gr = sub.assign(reg=sub.ilad.map(ilb)).groupby(["reg", "mod"]).frp.median()
    Fm, Fv, kaynak = {}, {}, {}
    for i in ils:
        for mod, F, nat in ((True, Fm, FM0), (False, Fv, FV0)):
            if (i, mod) in g.index and n[(i, mod)] >= MINN: v, src = g[(i, mod)], "il"
            elif (ilb.get(i), mod) in gr.index: v, src = gr[(ilb.get(i), mod)], "bolge"
            else: v, src = nat, "ulusal"
            F[i] = float(min(max(v, nat), CAP * nat)); kaynak[f"{i}|{'M' if mod else 'V'}"] = src
    s = base & (E.fm.to_numpy() < E.ilad.map(Fm).to_numpy()) & (E.fv.to_numpy() < E.ilad.map(Fv).to_numpy())
    flag = (s & (E.st == 0).to_numpy()).astype(np.uint8)
    off = 0; per_year = {}
    for y in M["yillar"]:
        k = M["events"][str(y)]["n"]; a = flag[off:off + k]; off += k
        (D / f"aniz_il_{y}.bin").write_bytes(a.tobytes()); per_year[str(y)] = int(a.sum())
    assert off == len(E)
    # doğrulama
    tem = (E.st == 0).to_numpy(); ur = (E.ilad == "Şanlıurfa").to_numpy(); after = tem & (flag == 0)
    g1 = json.loads((R / "belgeler_ve_denetim" / "gercek_dogrulama.json").read_text(encoding="utf-8"))["olaylar"]
    rc = json.loads((R / "belgeler_ve_denetim" / "recall_olcumu.json").read_text(encoding="utf-8"))["sonuclar"]
    ids = sorted({x["event_id"] for x in g1} | {x["event_id"] for x in rc if x.get("event_id")})
    doc = int(E.evid.isin(ids).to_numpy()[flag == 1].sum())
    byil = E[flag == 1].ilad.value_counts().head(15)
    ver = {"isaretli_olay": int(flag.sum()), "temiz_olay": int(tem.sum()), "isaretli_temiz_orani": float(flag.sum() / tem.sum()),
           "sanliurfa_temiz_payi_once": float(ur[tem].mean()), "sanliurfa_temiz_payi_sonra": float(ur[after].mean()),
           "belgeli_olay_sayisi": len(ids), "belgeli_olay_etkilenen": doc,
           "buyuk_olay_etkilenen": int(((E.frp_max >= 300) & ((E.n_modis + E.n_viirs) >= 20) & (E.dur / 60 > 24)).to_numpy()[flag == 1].sum()),
           "isaretli_en_buyuk_frp_max": float(E.frp_max.to_numpy()[flag == 1].max()), "isaretli_en_cok_tespit": int((E.n_modis + E.n_viirs).to_numpy()[flag == 1].max()),
           "il_en_cok_isaretli": {k: int(v) for k, v in byil.items()}}
    man = {"kural": "varyant T + tavan 1,5x (il_bazli_aniz_analizi.md)", "ulusal_esik": {"modis": FM0, "viirs": FV0}, "min_nokta": MINN, "tavan": CAP,
           "esik_modis": Fm, "esik_viirs": Fv, "esik_kaynagi": kaynak, "yillik_isaretli": per_year, "dogrulama": ver}
    (D / "aniz_il_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(ver, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
