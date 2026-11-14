"""MODIS-eşdeğer seri, üç yöntemin yarışı, yıl dışarıda bırakma ve sıçrama metriği.

Basitçe: VIIRS çok daha keskin gözlü olduğu için MODIS'in "göremeyeceği" küçük yangınları da
sayar. Biz "MODIS bu yangınları görseydi kaç tane sayardı?" sorusunu soruyoruz. Üç farklı
tarif deniyoruz ve hangisinin daha iyi olduğunu, cevabı BİLMEDİĞİ yıllarda sınıyoruz: her
seferinde bir yılı saklıyoruz, kalan yıllarla öğreniyoruz, saklanan yılı tahmin ediyoruz
(sınavdaki soruyu ders kitabından ayırmak gibi, K4).

Teknik olarak (hedef: Terra+Aqua tespit sayısı, ay × 7 coğrafi bölge; type 0/-1):
- Gözlem eforu: VIIRS uyduları (SNPP 2012-, N20 2018-, N21 2023-) ayrı ayrı sayılır, günlük
  "gözleyen uydu başına ortalama" alınır (coverage.parquet `observed`). Gözlemsiz günler ay içinde
  gözlenen günlerin ortalamasıyla ölçeklenir. Böylece uydu eklenmesi sayıyı şişirmez.
- Yöntem (i0) sabit oran, efor yok: M = r * tüm VIIRS tespiti.
- Yöntem (i)  sabit oran, eforlu: M = r * uydu başına VIIRS tespiti.
- Yöntem (ii) tabakalı oran: bölge × mevsim × FRP büyüklük sınıfı; VIIRS "sözde MODIS hücresi"
  sayısına oran (yetersiz tabakada mevsim × büyüklüğe düşülür).
- Yöntem (iii) FRP eşiği: aynı geçişteki VIIRS noktaları `hucre_baglanti_km` ile hücreye
  zincirlenir; hücre toplam FRP'sine göre "bu hücrede Aqua kaç tespit verir" eğrisi g(F)
  (log-FRP kutuları; bölge × mevsim × gündüz/gece, yetersizse üst tabaka) eşzamanlı Aqua
  çiftlerinden öğrenilir; yalnız-MODIS payı f_u (uydu × gündüz/gece × mevsim) eklenir; Terra
  payı k_TA (bölge × mevsim × gündüz/gece, MODIS'in kendi verisinden) ile Terra+Aqua'ya çıkılır.
  Ayrıca fiziksel yorum için MODIS tespit sınırı FRP50 (lojistik, P(Aqua görür)=0,5) raporlanır.
- Değerlendirme: 2012-2025 her yıl dışarıda bırakılır (LOYO). Seçim ölçütü (belgede sonuçlardan
  önce yazıldı; git kaydı olmadığından doğrulanamaz): ay × bölge düzeyinde en düşük WAPE (Σ|tahmin-gerçek| / Σgerçek) — mevsimsel yanlış ölçeklemeyi
  (K8, B-04) yakalayan düzey budur. Sabit oran kazanmadıkça kullanılmaz.
- Sıçrama (C10): geçiş 2012; önceki 3 yıl (gerçek MODIS) ile sonraki 3 yıl ortalamasının farkı.
  Harmonize seride sonraki yıllar LOYO tahminleridir (bağımsız). Doğal değişim dağılımı: MODIS
  serisinde geçiş dışı tüm 3+3 yıl pencereleri (2003-2025).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortak as O  # noqa: E402

BETIK = "src/harmonize/seri.py"
KEYS = ["yil", "ay", "bolge7"]


# --------------------------------------------------------------------------- #
# Veri hazırlığı
# --------------------------------------------------------------------------- #
def hazirla(kume: str = "temiz"):
    p = O.load_points()
    p = p.merge(pd.read_parquet(O.INTERIM / "passes.parquet"), on="pid")
    p["day"] = pd.to_datetime(p["day_tr"])
    keep = O.analiz_kumesi(p, kume)
    cov = pd.read_parquet(O.COVERAGE, columns=["sat", "day_tr", "observed"])
    cov["day"] = pd.to_datetime(cov["day_tr"])
    return p, keep, cov


def hucreler(v: pd.DataFrame) -> pd.Series:
    """Aynı geçişte <= hucre_baglanti_km zincirlenen VIIRS noktaları -> hücre kimliği."""
    L = float(O.h("hucre_baglanti_km"))
    x, y = O.km_xy(v["lat"], v["lon"])
    x = x + v["pass_id"].to_numpy().astype(float) * 1e5   # geçişleri uzayda ayır
    t = cKDTree(np.c_[x, y])
    pr = t.query_pairs(L, output_type="ndarray")
    n = len(v)
    g = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    return pd.Series(lab, index=v.index)


def efor_normalize(df: pd.DataFrame, cov: pd.DataFrame, vals: list[str], extra: list[str]):
    """(sat, day, bolge7, extra) toplamları -> (yil, ay, bolge7, extra) gözleyen uydu başına,
    gözlemsiz günler için ay içi ölçekli toplam."""
    cv = cov[cov["sat"].isin(O.VIIRS_SATS)]
    nobs = cv.groupby("day")["observed"].sum()
    gun = pd.DataFrame({"day": nobs.index, "nobs": nobs.to_numpy()})
    gun["yil"], gun["ay"] = gun["day"].dt.year, gun["day"].dt.month
    olc = gun.groupby(["yil", "ay"]).agg(n_gun=("day", "size"), n_obs_gun=("nobs", lambda s: (s > 0).sum()),
                                         uydu_ort=("nobs", "mean"))
    olc["olcek"] = olc["n_gun"] / olc["n_obs_gun"].clip(lower=1)
    a = df.groupby(["day", "bolge7"] + extra, observed=True)[vals].sum().reset_index()
    a = a.merge(gun[["day", "nobs"]], on="day")
    a = a[a["nobs"] > 0]
    a[vals] = a[vals].div(a["nobs"], axis=0)
    a["yil"], a["ay"] = a["day"].dt.year, a["day"].dt.month
    m = a.groupby(KEYS + extra, observed=True)[vals].sum().reset_index()
    m = m.merge(olc[["olcek"]].reset_index(), on=["yil", "ay"])
    m[vals] = m[vals].mul(m["olcek"], axis=0)
    return m.drop(columns="olcek"), olc


def frp_sinif(f):
    e = O.h("frp_sinif_sinirlari_mw")
    return np.where(f < e[0], "kucuk", np.where(f < e[1], "orta", "buyuk"))


def tablolar(kume: str = "temiz"):
    t0 = time.time()
    p, keep, cov = hazirla(kume)
    Wc = float(O.h("kalibrasyon_zaman_penceresi_dk"))
    # --- VIIRS hücreleri (2012+, analiz kümesi) ---
    v = p[keep & p["sensor"].eq("VIIRS")].copy()
    v["cell"] = hucreler(v)
    v["_r"] = v.groupby("cell")["frp"].rank(method="first", ascending=False)
    lead = v[v["_r"] == 1].set_index("cell")[["sat", "day", "yil", "ay", "mevsim", "dn", "bolge7", "pass_id"]]
    cells = v.groupby("cell").agg(frp_sum=("frp", "sum"), n_pts=("frp", "size")).join(lead)
    # --- Aqua tespitleri hücrelere (uydu başına tek hücre) ---
    pr = pd.read_parquet(O.INTERIM / "pairs.parquet")
    aq = p[keep & p["sat"].eq("Aqua")][["pid", "day", "yil", "ay", "mevsim", "dn", "bolge7", "frp"]]
    pa = pr[pr["m_sat"].eq("Aqua") & (pr["dt_dk"].abs() <= Wc)]
    pa = pa[pa["m_pid"].isin(aq["pid"])].merge(v[["pid", "cell"]].rename(columns={"pid": "v_pid"}), on="v_pid")
    pa = pa.sort_values(["m_pid", "v_sat", "dnorm"]).drop_duplicates(["m_pid", "v_sat"])
    n_aq = pa.groupby("cell").size()
    cells["n_aqua"] = cells.index.map(n_aq).fillna(0).astype(float)
    # Yalnız-MODIS Aqua tespitleri (o gün uydu s gözlüyorken s ile eşleşmeyen)
    obs = pd.read_parquet(O.COVERAGE, columns=["sat", "day_tr", "observed"])
    obs["day"] = pd.to_datetime(obs["day_tr"])
    obs = obs[obs["sat"].isin(O.VIIRS_SATS) & obs["observed"]][["sat", "day"]]
    aqs = aq.merge(obs, on="day")       # her Aqua tespiti x o gün gözleyen VIIRS uydusu
    eslesen = set(zip(pa["m_pid"], pa["v_sat"]))
    aqs["eslesti"] = [(a, b) in eslesen for a, b in zip(aqs["pid"], aqs["sat"])]
    # --- Aylık hedef ve özellikler ---
    m = p[keep & p["sensor"].eq("MODIS")].copy()
    m["fs"] = frp_sinif(m["frp"].to_numpy())
    M = m.groupby(KEYS).size().rename("M_true").reset_index()
    Mfrp = m.groupby(KEYS)["frp"].sum().rename("frp_modis").reset_index()
    Mc = m.groupby(KEYS + ["fs"]).size().unstack("fs", fill_value=0).add_prefix("M_").reset_index()
    Mta = m.groupby(KEYS + ["sat"]).size().unstack("sat", fill_value=0).reset_index()
    vv = v.assign(one=1.0)
    Vraw = vv.groupby(KEYS).size().rename("V_raw").reset_index()
    Vdet, olc = efor_normalize(vv.assign(frpv=vv["frp"].astype(float)), cov, ["one", "frpv"], [])
    Vdet = Vdet.rename(columns={"one": "V_eff_det", "frpv": "frp_viirs_efor"})
    cc = cells.reset_index().assign(fs=lambda d: frp_sinif(d["frp_sum"].to_numpy()), one=1.0)
    Vc, _ = efor_normalize(cc, cov, ["one"], ["fs"])
    Vc = Vc.pivot_table(index=KEYS, columns="fs", values="one", fill_value=0).add_prefix("V_").reset_index()
    T = M.merge(Mfrp, on=KEYS, how="outer")
    for d in (Mc, Mta, Vraw, Vdet, Vc):
        T = T.merge(d, on=KEYS, how="outer")
    T = T.fillna(0)
    T["mevsim"] = T["ay"].map(O.MEVSIM)
    T = T.merge(olc[["uydu_ort"]].reset_index(), on=["yil", "ay"], how="left")
    return dict(p=p, keep=keep, cov=cov, cells=cells, aqs=aqs, m=m, T=T, olc=olc,
                pa=pa, sure=time.time() - t0)


# --------------------------------------------------------------------------- #
# Yöntemler (her biri: train yılları -> test yılı ay × bölge tahmini)
# --------------------------------------------------------------------------- #
def y_sabit(T, tr, te, col):
    r = T.loc[tr, "M_true"].sum() / T.loc[tr, col].sum()
    return T.loc[te, col] * r


def y_tabakali(T, tr, te):
    mn = float(O.h("min_ornek"))
    pred = pd.Series(0.0, index=T.index[te])
    for fs in ("kucuk", "orta", "buyuk"):
        a = T.loc[tr].groupby(["bolge7", "mevsim"])[[f"M_{fs}", f"V_{fs}"]].sum()
        b = T.loc[tr].groupby(["mevsim"])[[f"M_{fs}", f"V_{fs}"]].sum()
        r1 = (a[f"M_{fs}"] / a[f"V_{fs}"]).where(a[f"V_{fs}"] >= mn)
        r2 = b[f"M_{fs}"] / b[f"V_{fs}"]
        idx = pd.MultiIndex.from_frame(T.loc[te, ["bolge7", "mevsim"]])
        r = pd.Series(r1.reindex(idx).to_numpy(), index=pred.index)
        r = r.fillna(pd.Series(r2.reindex(T.loc[te, "mevsim"]).to_numpy(), index=pred.index))
        pred += T.loc[te, f"V_{fs}"] * r.fillna(0)
    return pred


def _hiyerarsik(tr_df, te_df, levels, val, mn, cnt_col=None):
    """te_df için val ortalaması; en ince düzey yeterli örnekli değilse üst düzeye düş."""
    out = pd.Series(np.nan, index=te_df.index)
    for lv in levels:
        g = tr_df.groupby(lv, observed=True)[val].agg(["mean", "size"])
        g = g[g["size"] >= mn]
        key = pd.MultiIndex.from_frame(te_df[lv]) if len(lv) > 1 else te_df[lv[0]]
        out = out.fillna(pd.Series(g["mean"].reindex(key).to_numpy(), index=te_df.index))
    return out


def y_esik(D, tr_years, te_year, T_te_idx):
    """Yöntem (iii). Hücre düzeyinde beklenen Aqua tespiti -> efor -> Terra payı."""
    cells, aqs, m, cov, T = D["cells"], D["aqs"], D["m"], D["cov"], D["T"]
    mn = int(O.h("min_ornek"))
    nb = int(O.h("frp_egri_kutu_sayisi"))
    ctr = cells[cells["yil"].isin(tr_years)]
    cte = cells[cells["yil"].eq(te_year)].copy()
    lf_tr = np.log10(ctr["frp_sum"].clip(lower=0.1))
    edges = np.unique(np.quantile(lf_tr, np.linspace(0, 1, nb + 1)[1:-1]))
    ctr = ctr.assign(bin=np.searchsorted(edges, lf_tr))
    cte["bin"] = np.searchsorted(edges, np.log10(cte["frp_sum"].clip(lower=0.1)))
    lv = [["bolge7", "mevsim", "dn", "bin"], ["mevsim", "dn", "bin"], ["dn", "bin"], ["bin"]]
    g = _hiyerarsik(ctr, cte, lv, "n_aqua", max(mn // nb, 20))
    # yalnız-MODIS payı
    atr = aqs[aqs["yil"].isin(tr_years)]
    fu = 1 - atr.groupby(["sat", "dn", "mevsim"])["eslesti"].mean()
    fu_g = 1 - atr.groupby(["sat", "dn"])["eslesti"].mean()
    k = pd.MultiIndex.from_frame(cte[["sat", "dn", "mevsim"]])
    f = pd.Series(fu.reindex(k).to_numpy(), index=cte.index)
    f = f.fillna(pd.Series(fu_g.reindex(pd.MultiIndex.from_frame(cte[["sat", "dn"]])).to_numpy(), index=cte.index))
    cte["aq_eq"] = g / (1 - f.clip(upper=0.95))
    A, _ = efor_normalize(cte, cov, ["aq_eq"], ["dn", "mevsim"])
    # Terra payı (MODIS'in kendi verisi, test yılı hariç, Aqua'nın tam olduğu yıllar)
    mm = m[m["yil"].between(2003, 2025) & ~m["yil"].eq(te_year)]
    ct = mm.groupby(["bolge7", "mevsim", "dn", "sat"]).size().unstack("sat", fill_value=0)
    ct2 = mm.groupby(["mevsim", "dn", "sat"]).size().unstack("sat", fill_value=0)
    k1 = (ct["Terra"] / ct["Aqua"]).where(ct["Aqua"] >= mn)
    k2 = ct2["Terra"] / ct2["Aqua"]
    kk = pd.Series(k1.reindex(pd.MultiIndex.from_frame(A[["bolge7", "mevsim", "dn"]])).to_numpy(), index=A.index)
    kk = kk.fillna(pd.Series(k2.reindex(pd.MultiIndex.from_frame(A[["mevsim", "dn"]])).to_numpy(), index=A.index))
    A["M_eq"] = A["aq_eq"] * (1 + kk.fillna(1.0))
    out = A.groupby(KEYS)["M_eq"].sum()
    key = pd.MultiIndex.from_frame(T.loc[T_te_idx, KEYS])
    return pd.Series(out.reindex(key).fillna(0).to_numpy(), index=T_te_idx)


def frp50(cells, years) -> dict:
    """MODIS (Aqua) tespit sınırı: P(hücrede Aqua tespiti | log10 FRP) = 0,5 noktası (lojistik).
    Yalnız Aqua ile eşzamanlı eşleşme veren VIIRS geçişleri × bölge (Aqua şeridi ve saat uyumu vekili)."""
    c = cells[cells["yil"].isin(years)]
    aq_gun = c.groupby(["pass_id", "bolge7"])["n_aqua"].transform("sum") > 0
    c = c[aq_gun]
    res = {}
    def fit(d):
        x = np.log10(d["frp_sum"].clip(lower=0.1).to_numpy())
        yy = (d["n_aqua"] > 0).to_numpy().astype(float)
        if len(d) < int(O.h("min_ornek")) or yy.sum() < 20:
            return None
        b0, b1 = 0.0, 1.0
        for _ in range(50):    # Newton-Raphson lojistik regresyon (2 parametre)
            z = np.clip(b0 + b1 * x, -30, 30)
            pr = 1 / (1 + np.exp(-z))
            w = pr * (1 - pr) + 1e-9
            H = np.array([[w.sum(), (w * x).sum()], [(w * x).sum(), (w * x * x).sum()]])
            gr = np.array([(yy - pr).sum(), ((yy - pr) * x).sum()])
            step = np.linalg.solve(H, gr)
            b0, b1 = b0 + step[0], b1 + step[1]
            if np.abs(step).max() < 1e-8:
                break
        return {"frp50_mw": round(float(10 ** (-b0 / b1)), 2) if b1 > 0 else None,
                "egim": round(float(b1), 3), "n_hucre": int(len(d)), "tespit_orani": round(float(yy.mean()), 4)}
    res["genel"] = fit(c)
    for dn, d in c.groupby("dn"):
        res[f"dn={dn}"] = fit(d)
    for (ms, dn), d in c.groupby(["mevsim", "dn"]):
        res[f"{ms}/{dn}"] = fit(d)
    for b, d in c.groupby("bolge7"):
        res[f"bolge={b}"] = fit(d)
    return res


# --------------------------------------------------------------------------- #
# LOYO ve ölçütler
# --------------------------------------------------------------------------- #
def olcutler(df: pd.DataFrame, pred: str) -> dict:
    """df: KEYS + M_true + pred (yalnız test tahminleri)."""
    yil = df.groupby("yil")[["M_true", pred]].sum()
    e = (yil[pred] - yil["M_true"]) / yil["M_true"] * 100
    ss = ((yil["M_true"] - yil[pred]) ** 2).sum() / ((yil["M_true"] - yil["M_true"].mean()) ** 2).sum()
    mr = df.groupby(["yil", "ay", "bolge7"])[["M_true", pred]].sum()
    ss_m = ((mr["M_true"] - mr[pred]) ** 2).sum() / ((mr["M_true"] - mr["M_true"].mean()) ** 2).sum()
    tr = df.groupby(["yil", "ay"])[["M_true", pred]].sum()
    return {
        "yillik_mape": round(float(e.abs().mean()), 2), "yillik_bias": round(float(e.mean()), 2),
        "yillik_r2": round(float(1 - ss), 4),
        "yillik_ci95": [round(float(np.percentile(e, 2.5)), 2), round(float(np.percentile(e, 97.5)), 2)],
        "ay_bolge_wape": round(float((mr[pred] - mr["M_true"]).abs().sum() / mr["M_true"].sum() * 100), 2),
        "ay_bolge_r2": round(float(1 - ss_m), 4),
        "ay_ulke_wape": round(float((tr[pred] - tr["M_true"]).abs().sum() / tr["M_true"].sum() * 100), 2),
        "yillik_hata_pct": {int(k): round(float(x), 2) for k, x in e.items()},
    }


def loyo(D):
    T = D["T"]
    a, b = O.h("loyo_test_yillari")
    years = list(range(a, b + 1))
    preds = {k: pd.Series(np.nan, index=T.index) for k in ("i0", "i", "ii", "iii")}
    for y in years + [b + 1]:            # b+1 (2026): tüm test yıllarıyla eğitilmiş, test değil
        tr = T["yil"].isin(years) & ~T["yil"].eq(y)
        te = T["yil"].eq(y)
        if not te.any():
            continue
        preds["i0"][te] = y_sabit(T, tr, te, "V_raw")
        preds["i"][te] = y_sabit(T, tr, te, "V_eff_det")
        preds["ii"][te] = y_tabakali(T, tr, te)
        preds["iii"][te] = y_esik(D, [x for x in years if x != y], y, T.index[te])
    for k, s in preds.items():
        T[f"pred_{k}"] = s
    test = T[T["yil"].isin(years)]
    sonuc = {k: olcutler(test, f"pred_{k}") for k in preds}
    return sonuc, years


def bant_quantilleri(T, years, pred):
    """Ay × bölge ve ay × ülke düzeyinde LOYO artıklarından %95 bant (log oran, büyüklük kutulu).
    Kapsama, her yıl için bant DİĞER yılların artıklarından kurularak dürüstçe ölçülür."""
    out = {}
    for lvl, keys in (("bolge", ["yil", "ay", "bolge7"]), ("TR", ["yil", "ay"])):
        d = T[T["yil"].isin(years)].groupby(keys)[["M_true", pred]].sum().reset_index()
        d["lr"] = np.log((d["M_true"] + 1) / (d[pred] + 1))
        edges = np.quantile(d[pred], [1 / 3, 2 / 3])
        d["kb"] = np.searchsorted(edges, d[pred])
        q = d.groupby("kb")["lr"].quantile([0.025, 0.975]).unstack()
        kaps = []
        for y in years:
            o = d[d["yil"] != y].groupby("kb")["lr"].quantile([0.025, 0.975]).unstack()
            t = d[d["yil"] == y]
            lo = (t[pred] + 1) * np.exp(o.loc[t["kb"], 0.025].to_numpy()) - 1
            hi = (t[pred] + 1) * np.exp(o.loc[t["kb"], 0.975].to_numpy()) - 1
            kaps.append(((t["M_true"] >= np.floor(lo)) & (t["M_true"] <= np.ceil(hi))).to_numpy())
        out[lvl] = {"edges": edges.tolist(), "q": q.to_dict("index"),
                    "kapsama_loyo": round(float(np.concatenate(kaps).mean()), 4)}
    return out


def bant_uygula(pred, bq):
    kb = np.searchsorted(bq["edges"], pred)
    lo = np.array([bq["q"][k][0.025] for k in kb])
    hi = np.array([bq["q"][k][0.975] for k in kb])
    return (np.floor(np.clip((pred + 1) * np.exp(lo) - 1, 0, None)).astype(int),
            np.ceil((pred + 1) * np.exp(hi) - 1).astype(int))


def sicrama(seri: pd.Series, gecis: int, w: int) -> float:
    once = seri.loc[gecis - w:gecis - 1].mean()
    sonra = seri.loc[gecis:gecis + w - 1].mean()
    return float((sonra - once) / once * 100)


def sicrama_paketi(yil: pd.DataFrame, pred: str) -> dict:
    """C10 sıçrama ölçümleri. yil: yıl indeksli M_true, V_raw, V_eff_det, pred sütunları."""
    w = int(O.h("sicrama_pencere_yil"))
    modis = yil["M_true"]
    ham = modis.copy()
    ham.loc[2012:] = (yil["M_true"] + yil["V_raw"]).loc[2012:]      # saf birleştirme: tüm tespitler
    ham_v = modis.copy()
    ham_v.loc[2012:] = yil["V_raw"].loc[2012:]                       # yalnız VIIRS'e geçiş
    harm = modis.copy()
    harm.loc[2012:] = yil[pred].loc[2012:]
    null = []
    for t in range(2003 + w, 2025 - w + 2):
        if t == 2012:
            continue
        null.append(sicrama(modis, t, w))
    null = np.array(null)
    ci = [round(float(np.percentile(null, 2.5)), 2), round(float(np.percentile(null, 97.5)), 2)]
    j = {
        "jump_raw_pct": round(sicrama(ham, 2012, w), 2),
        "jump_raw_viirs_only_pct": round(sicrama(ham_v, 2012, w), 2),
        "jump_harm_pct": round(sicrama(harm, 2012, w), 2),
        "jump_modis_gercek_pct": round(sicrama(modis, 2012, w), 2),
        "jump_null_ci95": ci, "jump_null_n": int(len(null)),
        "jump_null_degerler": [round(float(x), 2) for x in null],
    }
    j["jump_harm_eksi_modis_pct"] = round(j["jump_harm_pct"] - j["jump_modis_gercek_pct"], 2)
    # VIIRS içi geçişler (N20 2018, N21 2023): ham toplam vs eforlu
    vy = yil[["V_raw", "V_eff_det"]]
    j["viirs_ici"] = {str(g): {"ham_viirs_pct": round(sicrama(vy["V_raw"], g, w if g == 2018 else 2), 2),
                               "eforlu_viirs_pct": round(sicrama(vy["V_eff_det"], g, w if g == 2018 else 2), 2),
                               "modis_gercek_pct": round(sicrama(modis, g, w if g == 2018 else 2), 2)}
                      for g in (2018, 2023)}
    j["jump_resid_pct"] = j["jump_harm_eksi_modis_pct"]
    return j


def main(kume: str = "temiz") -> dict:
    t0 = time.time()
    D = tablolar(kume)
    T = D["T"]
    sonuc, years = loyo(D)
    # Önceden belirlenmiş seçim ölçütü
    kazanan = min(sonuc, key=lambda k: sonuc[k]["ay_bolge_wape"])
    pred = f"pred_{kazanan}"
    bq = bant_quantilleri(T, years, pred)
    j = sicrama_paketi(T.groupby("yil")[["M_true", "V_raw", "V_eff_det", pred]].sum(), pred)
    D["jump_yontem"] = {k: sicrama_paketi(T.groupby("yil")[["M_true", "V_raw", "V_eff_det", f"pred_{k}"]].sum(), f"pred_{k}")
                        for k in sonuc}
    D["sonuc"], D["kazanan"], D["bq"], D["jump"], D["years"] = sonuc, kazanan, bq, j, years
    D["frp50"] = frp50(D["cells"], years)
    D["sure_toplam"] = time.time() - t0
    return D


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import json
    D = main()
    for k, s in D["sonuc"].items():
        print(k, {a: b for a, b in s.items() if a != "yillik_hata_pct"})
    print("kazanan", D["kazanan"])
    print(json.dumps(D["jump"], indent=1))
    print(json.dumps(D["frp50"], indent=1))
    print({k: v["kapsama_loyo"] for k, v in D["bq"].items()}, round(D["sure_toplam"], 1))
