"""F2 bağımsız yeniden hesap (denetçi, C23).

Basitçe: Ajanların yazdığı kodu hiç çağırmadan, aynı ham tablolardan sayıları yeniden sayarız.
İki farklı mutfakta aynı tarifi pişirip tadı aynı mı diye bakmak gibi.

Teknik olarak: yalnız pandas/numpy; `src/` içinden hiçbir modül import EDİLMEZ. Tanımlar
docs/03, docs/04 ve yöntem belgelerinden alınır (kod değil). Sonuçlar
`audit/yeniden_hesap.json` dosyasına `f2_` önekiyle EKLENİR (F1 girdileri silinmez).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data" / "processed"
OUT = ROOT / "audit" / "yeniden_hesap.json"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

met = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))["metrics"]
mv = lambda k: met[k]["value"]
R: dict = {}


def kayit(ad, beklenen, bulunan, tanim, tol=0.0, fark_aciklamasi=None):
    if isinstance(beklenen, (int, float, np.integer, np.floating)) and isinstance(bulunan, (int, float, np.integer, np.floating)):
        fark = float(bulunan) - float(beklenen)
        fark = 0 if abs(fark) <= tol else round(fark, 4)
    else:
        fark = 0 if beklenen == bulunan else "farkli"
    d = {"beklenen": _j(beklenen), "bulunan": _j(bulunan), "fark": fark, "tanim": tanim}
    if fark != 0 and fark_aciklamasi:
        d["aciklama"] = fark_aciklamasi
    R["f2_" + ad] = d
    print(f"{ad:45s} beklenen={_j(beklenen)!s:>14} bulunan={_j(bulunan)!s:>14} fark={fark}")


def _j(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    return x


# ---------------- Yükle ----------------
pts = pd.read_parquet(P / "points.parquet", columns=["pid", "t_utc", "day_tr", "sensor", "sat", "il", "type", "frp"])
st = pd.read_parquet(P / "points_status.parquet")
pe = pd.read_parquet(P / "points_event.parquet")
ev = pd.read_parquet(P / "events.parquet")
cov = pd.read_parquet(P / "coverage.parquet", columns=["sat", "day_tr", "observed"])
df = pts.merge(st[["pid", "status"]], on="pid", how="left").merge(pe, on="pid", how="left")
assert len(df) == len(pts) == 1414674
# Yıl/ay: day_tr'den değil, t_utc + 3 saatten bağımsız türet (K11)
tr = pd.to_datetime(df["t_utc"], utc=True) + pd.Timedelta(hours=3)
df["yil"], df["ay"] = tr.dt.year, tr.dt.month

# ---------------- 1. Huni ----------------
kayit("huni_ham", 1414674, len(df), "points satırı = ham")
kayit("huni_status_bos", 0, int(df["status"].isna().sum()), "status atanmamış nokta (K3)")
sc = df["status"].value_counts()
for s in ["temiz", "deniz", "volkan", "statik_nasa", "sanayi", "kalici_belirsiz", "dusuk_guven", "aniz"]:
    kayit(f"huni_status_{s}", mv(f"temizlik_status_{s}"), int(sc.get(s, 0)), f"status={s} nokta sayısı vs metrics")
kayit("huni_status_toplam", 1414674, int(sc.sum()), "status kırılımı toplamı = ham (C01)")
for sen in ["MODIS", "VIIRS"]:
    x = df[df["sensor"] == sen]["status"].value_counts()
    R[f"f2_huni_{sen}_kirilim"] = {k: int(v) for k, v in x.items()}
ta = df["status"].isin(["temiz", "aniz"])
kayit("huni_kumelenen_nokta", int(ta.sum()), int((df["event_id"] >= 0).sum()), "event_id>=0 nokta = temiz+aniz nokta")
kayit("huni_disarida_eventli", 0, int(((df["event_id"] >= 0) & ~ta).sum()), "temiz/aniz olmayan ama olaya giren nokta")
kayit("huni_olay_toplam", mv("events_total"), int(df.loc[df["event_id"] >= 0, "event_id"].nunique()), "points_event'teki tekil olay = metrics events_total")
kayit("huni_olay_tablo", mv("events_total"), len(ev), "events.parquet satırı")

# ---------------- 2. Olay özeti ve match_class (kendi hesap) ----------------
_x = df[df["event_id"] >= 0].assign(_m=lambda d: (d["sensor"] == "MODIS").astype(int),
                                      _v=lambda d: (d["sensor"] == "VIIRS").astype(int),
                                      _a=lambda d: (d["status"] == "aniz").astype(int))
g = _x.groupby("event_id").agg(nm=("_m", "sum"), nv=("_v", "sum"), gun0=("day_tr", "min"),
                               n_aniz=("_a", "sum"), n_pts=("_a", "size"))
g["nst"] = np.where((g["n_aniz"] > 0) & (g["n_aniz"] < g["n_pts"]), 2, 1)
e2 = ev.set_index("event_id").join(g, how="left")
kayit("olay_n_modis_uyusmaz", 0, int((e2["nm"] != e2["n_modis"]).sum()), "events.n_modis vs noktalardan sayım")
kayit("olay_n_viirs_uyusmaz", 0, int((e2["nv"] != e2["n_viirs"]).sum()), "events.n_viirs vs noktalardan sayım")
kayit("olay_gun0_uyusmaz", 0, int((pd.to_datetime(e2["gun0"]) != pd.to_datetime(e2["day_tr_start"])).sum()), "day_tr_start vs min(day_tr)")
# Çakışma günü: iki ailenin en az bir uydusu observed (docs/04 §3 tanımı, kendi kodumla)
c = cov[cov["observed"]].copy()
c["fam"] = np.where(c["sat"].isin(["Terra", "Aqua"]), "M", "V")
fam = c.groupby("day_tr")["fam"].nunique()
ovl = set(pd.to_datetime(pd.Series(fam[fam == 2].index)).dt.date)
cak = pd.to_datetime(e2["day_tr_start"]).dt.date.isin(ovl)
mc = np.select([~cak, (e2["nm"] > 0) & (e2["nv"] > 0), e2["nm"] > 0],
               ["tek_sensor_donemi", "ortak", "yalniz_modis"], "yalniz_viirs")
mcs = pd.Series(mc).value_counts()
for k in ["ortak", "yalniz_modis", "yalniz_viirs", "tek_sensor_donemi"]:
    kayit(f"match_{k}", mv(f"events_match_{k}"), int(mcs.get(k, 0)), f"match_class={k} bağımsız")
kayit("match_class_satir_uyusmaz", 0, int((mc != e2["match_class"].to_numpy()).sum()), "satır bazında match_class farkı")
kayit("c05_uclu_toplam", int(cak.sum()), int(mcs.get("ortak", 0) + mcs.get("yalniz_modis", 0) + mcs.get("yalniz_viirs", 0)), "ortak+yalnız M+yalnız V = çakışma olayı")
kayit("c04_joint_overlap", mv("events_joint_overlap"), int(cak.sum()), "çakışma dönemi olay sayısı")
# Olay status kuralı: tüm noktalar aniz ise aniz (docs/temizlik: olay düzeyi) -> karışıklığı ölç
R["f2_olay_status_dagilim"] = ev["status"].value_counts().to_dict()
R["f2_olay_karisik_status"] = int((e2["nst"] > 1).sum())

# ---------------- 3. TR yıllık temiz tespit ----------------
yt = df[df["status"] == "temiz"].groupby(["yil", "sensor"]).size().unstack(fill_value=0)
R["f2_tr_yillik_temiz_tespit"] = {int(y): {k: int(v) for k, v in r.items()} for y, r in yt.iterrows()}
mo = pd.read_parquet(P / "agg" / "monthly.parquet")
trm = mo[mo["duzey"] == "TR"]
ty = trm.groupby("yil")[["modis_temiz", "viirs_temiz"]].sum(min_count=1)
d_m = int((ty["modis_temiz"].fillna(0).round().astype(int) - yt["MODIS"].reindex(ty.index).fillna(0)).abs().sum())
d_v = int((ty["viirs_temiz"].fillna(0).round().astype(int) - yt.get("VIIRS", pd.Series(dtype=int)).reindex(ty.index).fillna(0)).abs().sum())
kayit("monthly_TR_yillik_modis_temiz_abs_fark", 0, d_m, "monthly.parquet TR modis_temiz yıllık toplamı vs bağımsız")
kayit("monthly_TR_yillik_viirs_temiz_abs_fark", 0, d_v, "monthly.parquet TR viirs_temiz yıllık toplamı vs bağımsız (ham sayım)")

# ---------------- 4. il × ay olay sayısı ----------------
et = ev[ev["status"] == "temiz"].copy()
dd = pd.to_datetime(et["day_tr_start"])
et["yil"], et["ay"] = dd.dt.year, dd.dt.month
il_ay = et.groupby(["il", "yil", "ay"]).size()
mi = mo[mo["duzey"] == "il"].set_index(["birim", "yil", "ay"])["olay"]
j = pd.concat([il_ay.rename("ben"), mi.rename("onlar")], axis=1).fillna(0)
kayit("monthly_il_olay_abs_fark_toplam", 0, int((j["ben"] - j["onlar"]).abs().sum()), "tüm il×yıl×ay olay (status=temiz, başlangıç günü) farkı")
ornek = [("Antalya", 2021, 8), ("Muğla", 2021, 8), ("Adana", 2023, 6), ("Şanlıurfa", 2019, 6), ("İzmir", 2025, 7)]
for il, y, a in ornek:
    kayit(f"olay_{il}_{y}_{a:02d}", float(mi.get((il, y, a), np.nan)), int(il_ay.get((il, y, a), 0)), f"{il} {y}-{a:02d} temiz olay")

# ---------------- 5. TR ay medyanları (modis_temiz, normal yıllar 2003-2025) ----------------
mt = df[(df["status"] == "temiz") & (df["sensor"] == "MODIS")].groupby(["yil", "ay"]).size()
yb = pd.read_parquet(P / "agg" / "yil_bilgi.parquet")
norm = yb.loc[yb["normal_modis"], "yil"].tolist()
R["f2_normal_modis_yillari"] = norm
pr = pd.read_parquet(P / "agg" / "profile.parquet")
prt = pr[(pr["birim"] == "TR") & (pr["seri"] == "modis_temiz")].set_index("ay")["medyan"]
# monthly kk (kesinti düzeltmeli) sütunu medyanı da ayrıca: ham sayım medyanı ile kk medyanı
kk = trm.set_index(["yil", "ay"])["modis_temiz_kk"]
for a in range(1, 13):
    ham_med = float(np.median([mt.get((y, a), 0) for y in norm]))
    kk_med = float(np.median([kk.get((y, a), np.nan) for y in norm]))
    kayit(f"tr_medyan_modis_temiz_ay{a:02d}", float(prt.get(a)), kk_med, "profile medyan vs bağımsız (monthly _kk sütunu üstünden, normal yıllar)", tol=1e-6,
          fark_aciklamasi=None)
    R[f"f2_tr_medyan_modis_temiz_ay{a:02d}"]["ham_sayim_medyan"] = ham_med

# ---------------- 6. 2012 sıçraması ----------------
w = 3
def sic(s, g=2012):
    return float((s.loc[g:g + w - 1].mean() - s.loc[g - w:g - 1].mean()) / s.loc[g - w:g - 1].mean() * 100)
M = df[(df["status"] == "temiz") & (df["sensor"] == "MODIS")].groupby("yil").size()
V = df[(df["status"] == "temiz") & (df["sensor"] == "VIIRS")].groupby("yil").size().reindex(M.index, fill_value=0)
ham = M.copy(); ham.loc[2012:] = (M + V).loc[2012:]
kayit("jump_modis_gercek", mv("jump_modis_gercek_pct"), round(sic(M), 2), "gerçek MODIS (temiz) 2009-11 vs 2012-14", tol=0.006)
kayit("jump_raw_MplusV", mv("jump_raw_pct"), round(sic(ham), 2), "saf birleştirme M+V (temiz) sıçrama", tol=0.006)
hv = M.copy(); hv.loc[2012:] = V.loc[2012:]
kayit("jump_raw_viirs_only", mv("jump_raw_viirs_only_pct"), round(sic(hv), 2), "MODIS→yalnız VIIRS geçiş sıçraması", tol=0.006)
# Tamamen ham (status yok) bilgi
Ma = df[df["sensor"] == "MODIS"].groupby("yil").size(); Va = df[df["sensor"] == "VIIRS"].groupby("yil").size().reindex(Ma.index, fill_value=0)
ha = Ma.copy(); ha.loc[2012:] = (Ma + Va).loc[2012:]
R["f2_jump_tum_ham_MplusV_bilgi"] = round(sic(ha), 2)
R["f2_jump_tum_ham_modis_bilgi"] = round(sic(Ma), 2)
H = pd.read_parquet(P / "agg" / "harmonized.parquet")
hy = H[(H["birim"] == "tespit") & (H["kume"] == "temiz") & (H["duzey"] == "yil_TR")].set_index("yil")
hs = M.astype(float).copy(); hs.loc[2012:] = hy["modis_esdeger"].astype(float).reindex(hs.loc[2012:].index)
kayit("jump_harm", mv("jump_harm_pct"), round(sic(hs), 2), "harmonized.parquet yil_TR modis_esdeger ile sıçrama", tol=0.05,
      fark_aciklamasi="harmonized.parquet tamsayıya yuvarlanmış yıllık değer; metrics yuvarlamasız tahminle hesaplanmış (tol 0,05 puan)")
kayit("harm_yil_modis_gercek_uyusmaz", 0, int((hy["modis_gercek"].astype(float).reindex(M.index).dropna() - M.reindex(hy.index).dropna()).abs().sum()), "harmonized yil_TR modis_gercek vs bağımsız MODIS temiz")
# Null dağılımı (geçiş dışı 3+3 pencereler, MODIS)
nul = [sic(M, t) for t in range(2006, 2024) if t != 2012]
kayit("jump_null_ci95_alt", mv("jump_null_ci95")[0], round(float(np.percentile(nul, 2.5)), 2), "doğal değişim %2,5", tol=0.006)
kayit("jump_null_ci95_ust", mv("jump_null_ci95")[1], round(float(np.percentile(nul, 97.5)), 2), "doğal değişim %97,5", tol=0.006)
R["f2_jump_null_n"] = len(nul)

# ---------------- 7. LOYO: sabit oran (i0) bağımsız ----------------
yrs = list(range(2012, 2026))
err = []
for y in yrs:
    trn = [x for x in yrs if x != y]
    r = M.loc[trn].sum() / V.loc[trn].sum()
    err.append((r * V.loc[y] - M.loc[y]) / M.loc[y] * 100)
kayit("loyo_i0_yillik_mape", mv("harm_i0_yillik_mape"), round(float(np.mean(np.abs(err))), 2), "sabit oran (efor yok) LOYO yıllık MAPE", tol=0.006)
# Harmonize (ii) yıllık LOYO hatası harmonized.parquet'ten
he = (hy["modis_esdeger"].astype(float).loc[2012:2025] - M.loc[2012:2025]) / M.loc[2012:2025] * 100
kayit("loyo_ii_yillik_mape_parquet", mv("loyo_mape"), round(float(he.abs().mean()), 2), "harmonized.parquet modis_esdeger vs gerçek MODIS, 2012-2025", tol=0.05,
      fark_aciklamasi="parquet tamsayı yuvarlaması")
R["f2_loyo_ii_yillik_hata_pct"] = {int(k): round(float(v), 2) for k, v in he.items()}
# C10 artık: 3 yıllık pencere hatasının LOYO dağılımı (yıllık değil)
R["f2_c10_artik"] = mv("jump_resid_pct")
R["f2_loyo_ci95"] = mv("loyo_ci95")

# ---------------- 8. K8: olay > tespit saçmalığı ----------------
for col_o, col_t, ad in [("olay_esdeger", "modis_esdeger", "esdeger"), ("olay", "modis_temiz", "ham")]:
    for dz in ["TR", "bolge", "il"]:
        x = mo[mo["duzey"] == dz][[col_o, col_t]].dropna()
        R[f"f2_k8_{ad}_{dz}_olay_gt_tespit"] = {"hucre": int(len(x)), "olay>tespit": int((x[col_o] > x[col_t] + 1e-9).sum())}
x = mo[mo["duzey"] == "TR"][["yil", "ay", "olay_esdeger", "modis_esdeger"]].dropna()
R["f2_k8_TR_ornek_olay_gt"] = x[x["olay_esdeger"] > x["modis_esdeger"]].head(10).to_dict("records")

# ---------------- 9. Mevcut ay (2026-11 ilk 12 gün) ----------------
nov = df[(df["sensor"] == "MODIS") & (df["ay"] == 11) & (tr.dt.day <= 12)]
by = nov.groupby(["yil", "sat"]).size().unstack(fill_value=0)
R["f2_kasim_ilk12_modis_ham_uyduya_gore"] = {int(y): {k: int(v) for k, v in r.items()} for y, r in by.loc[2019:].iterrows()}
d26 = df[(df["sensor"] == "MODIS") & (df["yil"] == 2026) & (df["ay"].isin([10, 11]))]
R["f2_2026_ekim_kasim_gunluk_modis_ham"] = {str(k): int(v) for k, v in d26.groupby("day_tr").size().tail(20).items()}
oct_ = df[(df["sensor"] == "MODIS") & (df["ay"] == 10) & (df["status"] == "temiz")].groupby("yil").size()
R["f2_ekim_modis_temiz_2019_2026"] = {int(k): int(v) for k, v in oct_.loc[2019:].items()}

# ---------------- yaz (F1 girdilerini koru) ----------------
old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
old = {k: v for k, v in old.items() if not k.startswith("f2_")}
old.update(R)
OUT.write_text(json.dumps(old, ensure_ascii=False, indent=1, default=_j), encoding="utf-8")
print("yazıldı", OUT, len(R), "f2 girdisi")
