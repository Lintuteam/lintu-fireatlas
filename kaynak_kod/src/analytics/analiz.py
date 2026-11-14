"""Ay profili, aktivite sıralaması, ham-temiz farkı ve mevsimsel anomali (K4: normal test yılını içermez).

Basitçe: Her ay için "geçmiş yıllarda tipik (medyan) kaç sıcak nokta vardı" tablosu çıkarılır; en
yoğun 3 ay seçilir; iki ay birbirine çok yakınsa "ayırt edilemez" denir. Anomali: bir yılın o ayı,
O YIL HARİÇ diğer yılların aynı ayıyla kıyaslanır (sınav sorusunu ders kitabından ayırmak gibi).
"Aktivite" tarihsel hotspot aktivitesidir; yangın tehlikesi tahmini değildir (K14).

Teknik olarak: girdi seri_aylik.parquet (kesinti-düzeltmeli, boş hücreler yok sayılır). Normal yıl:
yil_bilgi.normal_* (sensör bileşimi sabit, geçiş/kısmi yıl hariç). Profil: n, medyan, Q1, Q3, min,
maks, ay payı. Medyan, n<2 ise boş; n<min_yil_medyan ise 'az_yil' uyarılı. Sıralama ölçütü: medyan;
olay serilerinde (sensör bileşimi yıllara göre değişir) ay payının medyanı. Ayırt edilemezlik: komşu
sıra göreli farkı < tol veya yıl bootstrap'ında top-N üyeliği kararsız. Anomali: log1p ölçeğinde
sağlam z = (x − medyan)/max(1.4826·MAD, taban); olay serilerinde normal yalnız AYNI sensör bileşimli
(era) yıllardan. Belirsizlik bandı (eşdeğer seri): z_alt/z_ust; işaret bantta değişiyorsa 'belirsiz_bant'.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)


def _cube(sl: pd.DataFrame, seri: str, units: list, years: list, col="deger"):
    s = sl[sl["seri"] == seri]
    A = np.full((len(units), len(years), 12), np.nan)
    ui = {u: i for i, u in enumerate(units)}
    yi = {y: i for i, y in enumerate(years)}
    if s.empty:
        return A
    A[s["birim"].map(ui).to_numpy(), s["yil"].map(yi).to_numpy(), s["ay"].to_numpy() - 1] = s[col].to_numpy()
    return A


def _grup_normal(yb, seri):
    return yb[f"normal_{C.grup_of(seri)}"]


def run() -> dict:
    t0 = time.time()
    sl = pd.read_parquet(C.SERI_AYLIK)
    yb = pd.read_parquet(C.YIL_BILGI).set_index("yil")
    units = list(pd.read_parquet(C.MONTHLY, columns=["birim"])["birim"].unique())
    years = sorted(int(y) for y in yb.index)
    min_yil, tol, B, top_n = C.t("min_yil_medyan"), C.t("ayirt_edilemez_tol"), int(C.t("bootstrap_B")), int(C.t("top_n"))
    zes, taban = C.t("z_esik"), C.t("olcek_taban")
    rng = np.random.default_rng(int(C.t("bootstrap_tohum")))
    prof, rank, anom = [], [], []
    ym = np.array(years)
    for seri in C.TUM_SERILER:
        A = _cube(sl, seri, units, years)
        if np.all(np.isnan(A)):
            continue
        Alt, Ust = (_cube(sl, seri, units, years, "alt"), _cube(sl, seri, units, years, "ust")) \
            if C.is_esdeger(seri) else (None, None)
        nrm = np.array([bool(_grup_normal(yb, seri).get(y, False)) for y in years])
        An = A[:, nrm, :]
        n = np.sum(~np.isnan(An), axis=1)                      # [U,12]
        med = np.where(n >= 2, np.nanmedian(An, axis=1), np.nan)
        q1 = np.where(n >= 2, np.nanpercentile(An, 25, axis=1), np.nan)
        q3 = np.where(n >= 2, np.nanpercentile(An, 75, axis=1), np.nan)
        mn, mx = np.nanmin(An, axis=1), np.nanmax(An, axis=1)
        full = np.all(~np.isnan(An), axis=2)                   # [U,Yn] yıl 12 ayı dolu
        tot = np.where(full, np.nansum(An, axis=2), np.nan)
        pay = An / tot[:, :, None]
        pay_med = np.where(n >= 2, np.nanmedian(pay, axis=1), np.nan)
        use_pay = seri in C.SIRALAMA_PAY
        basis_arr = pay if use_pay else An
        basis = pay_med if use_pay else med
        for ui, u in enumerate(units):
            if not np.any(n[ui] > 0):
                continue
            # --- bootstrap top-N üyeliği ---
            Bu = basis_arr[ui]                                   # [Yn,12]
            ok_y = np.where(np.any(~np.isnan(Bu), axis=1))[0]
            topp = np.full(12, np.nan)
            if len(ok_y) >= 2 and np.all(n[ui] >= 2):
                idx = rng.integers(0, len(ok_y), size=(B, len(ok_y)))
                bm = np.nanmedian(Bu[ok_y][idx], axis=1)         # [B,12]
                rk = np.argsort(-bm, axis=1)[:, :top_n]
                topp = np.array([(rk == m).any(axis=1).mean() for m in range(12)])
            order = np.argsort(-np.nan_to_num(basis[ui], nan=-np.inf))
            sira = np.empty(12, int)
            sira[order] = np.arange(1, 13)
            for m in range(12):
                if n[ui, m] == 0:
                    continue
                up = [] if sira[m] == 1 else [order[sira[m] - 2]]
                dn = [order[sira[m]]] if sira[m] < 12 else []
                ayirt = False
                if sira[m] <= top_n + 1:
                    for o in up + dn:
                        a, b = basis[ui, m], basis[ui, o]
                        if np.isfinite(a) and np.isfinite(b) and max(a, b) > 0 and \
                                abs(a - b) / max(a, b) < tol and min(sira[m], sira[o]) <= top_n:
                            ayirt = True
                uy = []
                if n[ui, m] < 2:
                    uy.append("medyan_yok_tek_yil")
                elif n[ui, m] < min_yil:
                    uy.append("az_yil")
                if ayirt:
                    uy.append("ayirt_edilemez")
                prof.append((u, seri, m + 1, int(n[ui, m]), med[ui, m], q1[ui, m], q3[ui, m], mn[ui, m],
                             mx[ui, m], pay_med[ui, m], int(sira[m]), bool(sira[m] <= top_n),
                             topp[m], bool(ayirt), "pay" if use_pay else "medyan", ";".join(uy)))
        # --- anomali (LOYO: test yılı normalden çıkar) ---
        era = yb["era_all"].to_dict()
        gecis = yb["gecis_" + C.grup_of(seri).replace("olay", "all")].to_dict()
        for ti, yr in enumerate(years):
            x = A[:, ti, :]
            if np.all(np.isnan(x)):
                continue
            base = nrm & (ym != yr)
            if seri in C.OLAY_SERILERI:
                e0 = era.get(yr, "")
                base &= np.array([bool(e0) and era.get(y, "") == e0 for y in years])
            Bv = A[:, base, :]
            nb = np.sum(~np.isnan(Bv), axis=1)
            L = np.log1p(Bv)
            lm = np.nanmedian(L, axis=1) if base.any() else np.full(x.shape, np.nan)
            mad = np.nanmedian(np.abs(L - lm[:, None, :]), axis=1) if base.any() else lm
            sc = np.maximum(1.4826 * mad, taban)
            mv = np.nanmedian(Bv, axis=1) if base.any() else lm
            enough = (nb >= min_yil) & ~np.isnan(x)
            z = np.where(enough, (np.log1p(x) - lm) / sc, np.nan)
            pct = np.where(enough & (mv > 0), (x / mv - 1) * 100, np.nan)
            ypct = np.where(enough, np.nanmean(Bv < x[:, None, :], axis=1) if base.any() else np.nan, np.nan)
            za = zu = np.full(x.shape, np.nan)
            if Alt is not None:
                za = np.where(enough, (np.log1p(Alt[:, ti, :]) - lm) / sc, np.nan)
                zu = np.where(enough, (np.log1p(Ust[:, ti, :]) - lm) / sc, np.nan)
            ui_, mi_ = np.where(~np.isnan(x))
            for u_i, m_i in zip(ui_, mi_):
                zz = z[u_i, m_i]
                if np.isnan(zz):
                    isr = "yetersiz_veri"
                else:
                    isr = "yuksek" if zz >= zes else "dusuk" if zz <= -zes else "normal"
                    if Alt is not None and not np.isnan(za[u_i, m_i]):
                        f = lambda q: 1 if q >= zes else -1 if q <= -zes else 0  # noqa: E731
                        if len({f(za[u_i, m_i]), f(zz), f(zu[u_i, m_i])}) > 1:
                            isr += ";belirsiz_bant"
                uy = []
                if gecis.get(yr, False):
                    uy.append("sensor_gecis_yili")
                if yr == years[-1] and yb.loc[yr, "kismi_yil"]:
                    uy.append("kismi_yil")
                anom.append((units[u_i], seri, yr, m_i + 1, x[u_i, m_i], int(nb[u_i, m_i]), mv[u_i, m_i],
                             pct[u_i, m_i], zz, za[u_i, m_i], zu[u_i, m_i], ypct[u_i, m_i], isr, ";".join(uy)))
    pc = ["birim", "seri", "ay", "n_yil", "medyan", "q1", "q3", "min", "maks", "pay_medyan", "sira", "top",
          "top_olasilik", "ayirt_edilemez", "siralama_olcut", "uyari"]
    P = pd.DataFrame(prof, columns=pc)
    P.to_parquet(C.PROFIL, index=False)
    R = P[P["sira"] <= top_n + 1].copy()
    R.to_parquet(C.SIRALAMA, index=False)
    ac = ["birim", "seri", "yil", "ay", "deger", "n_normal_yil", "normal_medyan", "sapma_yuzde", "z", "z_alt",
          "z_ust", "yuzdelik", "isaret", "uyari"]
    Aa = pd.DataFrame(anom, columns=ac)
    Aa.to_parquet(C.ANOMALI, index=False)
    ht = ham_temiz(P)
    ht.to_parquet(C.HAM_TEMIZ, index=False)
    return {"profil_satir": len(P), "anomali_satir": len(Aa), "ham_temiz_satir": len(ht),
            "sure_sn": round(time.time() - t0, 1)}


def ham_temiz(P: pd.DataFrame) -> pd.DataFrame:
    """Ham ve temiz (anız hariç) sıralamanın farkı: temizlik sıralamayı değiştiriyor mu?"""
    rows = []
    for ham, tem, snsr in (("modis_ham", "modis_temiz", "modis"), ("viirs_ham_ub", "viirs_temiz_ub", "viirs")):
        a = P[P["seri"] == ham].set_index(["birim", "ay"])
        b = P[P["seri"] == tem].set_index(["birim", "ay"])
        for u in sorted(set(a.index.get_level_values(0)) & set(b.index.get_level_values(0))):
            ma, mb = a.loc[u].sort_index(), b.loc[u].sort_index()
            if len(ma) < 12 or len(mb) < 12:
                continue
            ta = ma[ma["sira"] <= 3].sort_values("sira").index.tolist()
            tb = mb[mb["sira"] <= 3].sort_values("sira").index.tolist()
            ra, rb = ma["sira"].to_numpy(float), mb["sira"].to_numpy(float)
            rho = float(np.corrcoef(ra, rb)[0, 1]) if ra.std() > 0 and rb.std() > 0 else np.nan
            with np.errstate(divide="ignore", invalid="ignore"):
                tp = float(np.nanmedian(mb["medyan"].to_numpy() / ma["medyan"].to_numpy()))
            rows.append((u, snsr, ",".join(map(str, ta)), ",".join(map(str, tb)), len(set(ta) & set(tb)),
                         ta != tb, rho, tp))
    return pd.DataFrame(rows, columns=["birim", "sensor", "top3_ham", "top3_temiz", "ortak_ay_sayisi",
                                       "siralama_degisti", "sira_korelasyonu", "temiz_pay_medyan"])


if __name__ == "__main__":
    print(run())
