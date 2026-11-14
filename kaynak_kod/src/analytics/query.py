"""Serbest tarih aralığı sorgusu ve "mevcut ay vs tarihsel medyan" (arayüz bunları çağırır; N-03, N-06).

Basitçe: Kullanıcı bir başlangıç-bitiş seçer. Biz o aralıktaki aktiviteyi, AYNI takvim günlerinin
geçmiş yıllardaki değerleriyle kıyaslarız ("geçen aylara" değil, "geçmiş yılların aynı dönemine").
Kesinti günleri paydadan çıkar; eksik veri sıfır sayılmaz.

Teknik olarak: aralik_analiz(v, birim, seri, bas, bit): test değeri = oran tahmincisi × gün sayısı
(veri.py). Tarihsel pencere: her normal yıl y (test yılı hariç, K4) için aralığın y yılına kaydırılmış
hâli; aralık pencere_min_gun'den kısaysa merkez çevresinde simetrik genişletilir ve oran gün sayısına
ölçeklenir. Olay serilerinde yalnız aynı sensör bileşimli (era) yıllar. Çıktı: değer, medyan, MAD,
oran (değer/medyan), yüzdelik, sağlam z (log1p), n_yil, uyarılar. n_yil < min_yil_medyan ise
'yetersiz' (medyan iddiası yok; n_yil < 2 ise medyan boş).
Eşdeğer seri günlük değildir: aylık hücre için ay_karsilastir() kullanılır.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from veri import Veri  # noqa: E402

TERIM = "aktivite = tarihsel hotspot aktivitesi (yangın tehlikesi tahmini değildir)"


def _gunler(v: Veri, bas, bit):
    i0, i1 = v.idx(bas), v.idx(bit) + 1
    return i0, i1


def aralik_analiz(v: Veri, birim: str, seri: str, bas, bit, test_yil=None) -> dict:
    if C.is_esdeger(seri):
        return {"hata": "esdeger_gunluk_degil", "uyari": ["eşdeğer seri aylıktır: ay_karsilastir kullan"]}
    bas, bit = pd.Timestamp(bas).normalize(), pd.Timestamp(bit).normalize()
    if bit < bas:
        return {"hata": "bitis_baslangictan_once"}
    u = v.uidx[birim]
    yb = v.yil_bilgi
    i0, i1 = _gunler(v, bas, bit)
    n = i1 - i0
    test_yil = int(test_yil or bas.year)
    uy = []
    val, inf = v.seri(seri, i0, i1, n)
    cov = inf["sw"] / n if n else 0.0
    deger = float(val[u]) if cov >= C.t("min_kapsam_orani") else np.nan
    if i0 < 0 or i1 > len(v.days):
        uy.append("aralik_veri_disi")
    if cov < C.t("min_kapsam_orani"):
        uy.append("kapsam_yetersiz")
    elif inf["kesinti"] and inf["kesinti"] > 0:
        uy.append("kesinti_gunleri_paydadan_cikarildi")
    grup = C.grup_of(seri)
    normal = yb[f"normal_{'olay' if grup == 'olay' else grup}"]
    era = yb["era_all"]
    wl = max(n, int(C.t("pencere_min_gun")))
    ek0 = (wl - n) // 2
    ek1 = wl - n - ek0
    base = []
    for y in normal.index:
        if y == test_yil or not bool(normal[y]):
            continue
        if seri in C.OLAY_SERILERI and (not era.get(test_yil, "") or era[y] != era[test_yil]):
            continue
        k = y - test_yil
        s = bas + pd.DateOffset(years=k) - pd.Timedelta(days=ek0)
        e = bit + pd.DateOffset(years=k) + pd.Timedelta(days=ek1)
        j0, j1 = v.idx(s), v.idx(e) + 1
        if j0 < 0 or j1 > len(v.days):
            continue
        vv, ii = v.seri(seri, j0, j1, j1 - j0)
        if ii["sw"] / (j1 - j0) < C.t("min_kapsam_orani"):
            continue
        base.append(float(vv[u]) / (j1 - j0) * n)     # gün oranı × test gün sayısı
    b = np.array([x for x in base if np.isfinite(x)])
    out = {"birim": birim, "seri": seri, "bas": str(bas.date()), "bit": str(bit.date()), "gun": n,
           "deger": deger, "kapsam_orani": float(cov), "n_yil": int(len(b)), "terim": TERIM,
           "pencere_gun": wl, "yontem": "oran tahmincisi / aynı takvim günü penceresi / test yılı hariç",
           "etiket": "tahmini" if grup != "modis" or seri in ("modis_ham",) else "ölçüldü"}
    if len(b) < 2:
        uy.append("yetersiz_yil")
        out.update(medyan=np.nan, mad=np.nan, oran=np.nan, yuzdelik=np.nan, z=np.nan)
    else:
        med = float(np.median(b))
        L = np.log1p(b)
        mad = float(np.median(np.abs(L - np.median(L))))
        sc = max(1.4826 * mad, C.t("olcek_taban"))
        out.update(medyan=med, mad=float(np.median(np.abs(b - med))),
                   oran=(deger / med if med > 0 and np.isfinite(deger) else np.nan),
                   yuzdelik=float((b < deger).mean() * 100) if np.isfinite(deger) else np.nan,
                   z=float((np.log1p(deger) - np.median(L)) / sc) if np.isfinite(deger) else np.nan)
        if len(b) < C.t("min_yil_medyan"):
            uy.append("az_yil")
    if bool(yb.loc[test_yil, "gecis_all"]) if test_yil in yb.index else False:
        uy.append("sensor_gecis_yili")
    out["uyari"] = uy
    return out


def mevcut_ay(v: Veri, birim: str, seri: str) -> dict:
    """Verideki son ay: ayın ilk D günü, geçmiş yılların AYNI ilk D gününe karşı (kısmi ay açık etiketli)."""
    son = v.son_gun
    bas = son.replace(day=1)
    r = aralik_analiz(v, birim, seri, bas, son)
    ay_sonu = (son + pd.Timedelta(days=1)).month != son.month
    r["kapsam"] = "tam_ay" if ay_sonu else "ayin_ilk_gunleri"
    if not ay_sonu:
        r["uyari"] = list(r.get("uyari", [])) + ["kismi_ay_ilk_%d_gun" % r["gun"]]
    return r


def ay_karsilastir(birim: str, seri: str, yil: int, ay: int, sl: pd.DataFrame | None = None) -> dict:
    """Aylık hücre vs aynı ayın normal yıllarının medyanı (eşdeğer seri dahil; belirsizlik bandıyla)."""
    sl = sl if sl is not None else pd.read_parquet(C.SERI_AYLIK)
    s = sl[(sl["birim"] == birim) & (sl["seri"] == seri) & (sl["ay"] == ay)]
    hedef = s[s["yil"] == yil]
    b = s[(s["normal_yil"]) & (s["yil"] != yil)]["deger"].to_numpy()
    if hedef.empty:
        return {"hata": "hucre_bos", "uyari": ["kısmi/kapsamsız ay: boş hücre"]}
    x = float(hedef["deger"].iloc[0])
    r = {"birim": birim, "seri": seri, "yil": yil, "ay": ay, "deger": x, "n_yil": len(b), "terim": TERIM,
         "alt": float(hedef["alt"].iloc[0]), "ust": float(hedef["ust"].iloc[0]), "uyari": []}
    if len(b) >= 2:
        med = float(np.median(b))
        r.update(medyan=med, oran=x / med if med > 0 else np.nan, yuzdelik=float((b < x).mean() * 100))
        if len(b) < C.t("min_yil_medyan"):
            r["uyari"].append("az_yil")
    else:
        r.update(medyan=np.nan, oran=np.nan, yuzdelik=np.nan)
        r["uyari"].append("yetersiz_yil")
    return r


def mevcut_ay_tablosu(v: Veri) -> pd.DataFrame:
    """Tüm birimler × günlük seriler için mevcut ay ve son tam ay; eşdeğer için son tam ay (aylık)."""
    rows = []
    son = v.son_gun
    ay_basi = son.replace(day=1)
    son_tam_bit = ay_basi - pd.Timedelta(days=1)
    for birim in v.units:
        for seri in C.SERI:
            for etiket, bas, bit in (("mevcut", ay_basi, son), ("son_tam_ay", son_tam_bit.replace(day=1), son_tam_bit)):
                r = aralik_analiz(v, birim, seri, bas, bit)
                tam = (bit + pd.Timedelta(days=1)).month != bit.month
                rows.append((birim, seri, etiket, str(bas.date()), str(bit.date()), r["gun"],
                             "tam_ay" if tam else "ayin_ilk_gunleri", r["deger"], r["medyan"], r["oran"],
                             r["yuzdelik"], r["z"], r["n_yil"], ";".join(r["uyari"])))
    sl = pd.read_parquet(C.SERI_AYLIK)
    sl = sl[sl["seri"].isin(C.ESDEGER_SERILERI) & sl["ay"].eq(son_tam_bit.month)]
    for seri in C.ESDEGER_SERILERI:
        for birim in v.units:
            r = ay_karsilastir(birim, seri, son_tam_bit.year, son_tam_bit.month, sl)
            if "hata" not in r:
                rows.append((birim, seri, "son_tam_ay", str(son_tam_bit.replace(day=1).date()),
                             str(son_tam_bit.date()), son_tam_bit.day, "tam_ay", r["deger"], r["medyan"], r["oran"],
                             r["yuzdelik"], np.nan, r["n_yil"], ";".join(r["uyari"])))
    df = pd.DataFrame(rows, columns=["birim", "seri", "hedef", "bas", "bit", "gun", "kapsam", "deger",
                                     "tarihsel_medyan", "oran", "yuzdelik", "z", "n_yil", "uyari"])
    return uyari_ekle(v, df)


_VIIRS_ESLES = {"modis_ham": "viirs_ham_ub", "modis_temiz": "viirs_temiz_ub",
                "modis_temiz_aniz_dahil": "viirs_temiz_aniz_dahil_ub", "enerji_modis": "enerji_viirs_ub"}


def uyari_ekle(v: Veri, df: pd.DataFrame) -> pd.DataFrame:
    """F2-04: kısmi ay (gün sayısı), NRT payı, Aqua yörünge kayması ve VIIRS oranını yan yana koyar.

    Basitçe: "Bu ay çok düşük" sonucunun yanına nedenleri yazılır: ay yarım mı, veri hızlı (NRT)
    üründen mi geliyor, Aqua'nın geçiş saati mi kaydı; ve VIIRS aynı şeyi söylüyor mu? İkisi de
    düşükse sensör farkı tek başına açıklamaz; yalnız MODIS düşükse sensör/yörünge şüphesi artar.
    Yorum doğrulanmış değildir; yalnız ayrıştırma ipucudur.
    """
    import build_monthly as B
    h = B.harm_oku().get(C.ESDEGER)
    d = df.copy()
    nrt, kay, kis = [], [], []
    flag = C.t("yorunge_kaymasi_bayragi")
    for _, r in d.iterrows():
        b = pd.Timestamp(r["bas"])
        i0, i1 = v.idx(b), v.idx(r["bit"]) + 1
        nrt.append(v.nrt_payi(i0, i1))
        bay = ""
        if h is not None and ("TR", b.year, b.month) in h.index:
            bay = str(h.loc[("TR", b.year, b.month), "bayrak"])
        kay.append(flag in bay)
        kis.append(int(r["gun"]) if r["kapsam"] != "tam_ay" else np.nan)
    d["kismi_ay_gun"] = kis
    d["nrt_payi"] = nrt
    d["aqua_yorunge_kaymasi"] = kay
    key = d.set_index(["birim", "seri", "hedef"])["oran"]
    d["viirs_oran"] = [key.get((r["birim"], _VIIRS_ESLES[r["seri"]], r["hedef"]), np.nan)
                       if r["seri"] in _VIIRS_ESLES else np.nan for _, r in d.iterrows()]
    es, dus = C.t("ayrisma_oran_esigi"), C.t("dusuk_oran_esigi")
    sap = C.t("esdeger_sapma_esigi")
    mm = d.set_index(["birim", "hedef", "seri"])["oran"]
    d["modis_olculen_oran"] = [mm.get((r["birim"], r["hedef"], "modis_temiz"), np.nan) for _, r in d.iterrows()]
    d["viirs_olculen_oran"] = [mm.get((r["birim"], r["hedef"], "viirs_temiz_ub"), np.nan) for _, r in d.iterrows()]
    yorum, guv, birincil, neden = [], [], [], []
    for _, r in d.iterrows():
        m, vv = r["oran"], r["viirs_oran"]
        om, ov = r["modis_olculen_oran"], r["viirs_olculen_oran"]
        isd = C.is_esdeger(r["seri"])
        y, g, bs, nd = "", False, r["seri"], ""
        if isd:
            if np.isfinite(m) and np.isfinite(om) and np.isfinite(ov):
                dm, dv = abs(m / om - 1) if om > 0 else np.inf, abs(m / ov - 1) if ov > 0 else np.inf
                if dm > sap and dv > sap:
                    g, nd = True, "esdeger_iki_olculen_orandan_saptı"
                    y = "esdeger_olcumlerle_celisiyor: MODIS %.2f, VIIRS %.2f, esdeger %.2f" % (om, ov, m)
                else:
                    y = "esdeger_en_az_bir_olcumle_uyumlu"
            if bool(r["aqua_yorunge_kaymasi"]):
                g, nd = True, (nd + ";" if nd else "") + "aqua_yorunge_kaymasi_yillari"
            if g:
                bs = "modis_temiz"
        elif r["seri"] in _VIIRS_ESLES and np.isfinite(m) and np.isfinite(vv):
            if m < dus and vv < dus and max(m, vv) / max(min(m, vv), 1e-9) < es:
                y = "iki_sensorde_de_dusuk: gercek dusus ve/veya hava; sensor farki tek basina aciklamaz"
            elif vv / max(m, 1e-9) >= es:
                y = "MODIS'e_ozgu_ek_dusus: sensor omru sonu/NRT/yorunge kaymasi suphesi"
            elif m / max(vv, 1e-9) >= es:
                y = "VIIRS'e_ozgu_ek_dusus: VIIRS uydu sayisi/NRT suphesi"
            else:
                y = "iki_sensor_uyumlu"
        yorum.append(y)
        guv.append(g)
        birincil.append(bs)
        neden.append(nd)
    d["esdeger_guvenilmez"] = guv
    d["birincil_seri"] = birincil
    d["guvensizlik_nedeni"] = neden
    d["ayrisma_yorum"] = yorum
    d["ayrisma_yorum_etiket"] = np.where(d["ayrisma_yorum"] != "", "doğrulanmadı", "")
    d["etiket"] = np.where(d["esdeger_guvenilmez"], "doğrulanmadı", "tahmini")
    ek = []
    for _, r in d.iterrows():
        e = [x for x in str(r["uyari"]).split(";") if x]
        if r["kapsam"] != "tam_ay":
            e.append("kismi_ay")
        if r["nrt_payi"] and r["nrt_payi"] > 0:
            e.append("nrt_donemi")
        if r["aqua_yorunge_kaymasi"]:
            e.append(flag)
        if r["esdeger_guvenilmez"]:
            e.append("esdeger_guvenilmez")
        ek.append(";".join(dict.fromkeys(e)))
    d["uyari"] = ek
    return d
