"""Nokta durum etiketleri (points_status.parquet), duyarlılık tabloları ve referans karşılaştırması.

Basitçe: Her sıcak noktaya bir "kimlik kartı" yazıyoruz: temiz mi, denizde mi, NASA'nın
statik kaynağı mı, bizim kuralımıza göre sanayi mi, kalıcı-belirsiz mi? Hiçbir nokta silinmez
(K3); yalnız etiket alır ve neden o etiketi aldığı `status_neden` sütununa yazılır.
Anız kararı olay düzeyinde verilecek (kümeleme sonrası, ikinci adım); burada yalnız
"anız adayı" bayrağı konur, nokta 'temiz' kalır.

Teknik olarak (öncelik sırası; ilk tutan kural kazanır):
 1. NASA type=1 -> volkan, type=3 -> deniz, type=2 -> statik_nasa (demo davranışı, U-07).
 2. NRT (type=-1): hücrenin arşiv noktalarının >= nasa_miras_payi kadarı type 1/3 ise volkan/deniz,
    type=2 ise statik_nasa (neden: nrt_nasa_*_mirasi). Bu, NRT'de eksik `type`ın kural ile telafisi.
 3. Sanayi kuralı (N, M, Y, S; tüm yıllardan hücre özellikleri) -> sanayi (kurala göre etiket).
 4. Kalıcı-belirsiz: Y ve M tutan, N veya S tutmayan, tespitlerinin çoğu gece olan hücre.
 5. Yangın koruması: 3/4'teki nokta, aynı gün ~5 km içinde kalıcı olmayan hücrelerde >=G tespit
    varsa temiz kalır (neden: yangin_korumasi). NASA etiketlerine dokunulmaz.
 6. Diğerleri temiz. dusuk_guven, yillik_tekrar (rastlantı modeline göre olağan dışı yıllık
    tekrar; çoğu tarım ovası) ve aniz_adayi status_neden'de bayraktır, status'u değiştirmez.
Çalıştırma: python src/cleaning/build_status.py  (~birkaç dakika; süre çıktıda)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aniz_takvim as A  # noqa: E402
import olay_aniz as O  # noqa: E402
import common as C  # noqa: E402
import persistence as P  # noqa: E402

KALIB = C.AUDIT / "temizlik_kalibrasyon.json"
TAKVIM_OUT = C.AUDIT / "aniz_takvimi.json"
REF = C.AUDIT / "dogrulama_seti.csv"
BETIK = "src/cleaning/build_status.py"
KALICI_STATUS = ("statik_nasa", "sanayi", "kalici_belirsiz")


# --------------------------------------------------------------------------- hazırlık
def hazirla() -> dict:
    df = C.load_points()
    land = ~df["type"].isin([1, 3]).to_numpy()
    cy = P.cell_year_table(df[land])
    f = P.features(cy)
    arch = df[df["type"] >= 0]
    c13 = arch.assign(t1=arch["type"] == 1, t3=arch["type"] == 3).groupby("cell").agg(
        na=("type", "size"), t1=("t1", "sum"), t3=("t3", "sum"))
    cell_il = df[land].groupby("cell")["il"].agg(lambda s: s.mode().iat[0])
    return {"df": df, "land": land, "cy": cy, "f": f, "c13": c13, "cell_il": cell_il}


def nasa_temel(pr: dict) -> tuple[np.ndarray, np.ndarray]:
    df, f, c13 = pr["df"], pr["f"], pr["c13"]
    pay = C.t("nasa_miras_payi")
    st = np.full(len(df), "", dtype=object)
    ne = np.full(len(df), "", dtype=object)
    ty = df["type"].to_numpy()
    st[ty == 1], ne[ty == 1] = "volkan", "nasa_type1"
    st[ty == 3], ne[ty == 3] = "deniz", "nasa_type3"
    st[ty == 2], ne[ty == 2] = "statik_nasa", "nasa_type2"
    nrt = ty == -1
    cell = df["cell"]
    sh1 = (c13["t1"] / c13["na"]).reindex(cell).fillna(0).to_numpy()
    sh3 = (c13["t3"] / c13["na"]).reindex(cell).fillna(0).to_numpy()
    sh2 = f["t2pay"].reindex(cell).fillna(0).to_numpy()
    m = nrt & (sh1 >= pay); st[m], ne[m] = "volkan", "nrt_nasa_volkan_mirasi"
    m = nrt & (st == "") & (sh3 >= pay); st[m], ne[m] = "deniz", "nrt_nasa_deniz_mirasi"
    m = nrt & (st == "") & (sh2 >= pay); st[m], ne[m] = "statik_nasa", "nrt_nasa_statik_mirasi"
    return st, ne


def yillik_tekrar_hucreler(pr: dict, alfa: float) -> pd.Series:
    key = ("tekrar", alfa)
    if key not in pr:
        k = P.kalici_null(pr["cy"], pr["cell_il"], alfa, C.t("kalici_min_yil"))
        pr[key] = k["kalici"]
    return pr[key]


def etiketle(pr: dict, N, M, Y, S, gece, G, k_koruma) -> dict:
    df, f = pr["df"], pr["f"]
    if "nasa" not in pr:
        pr["nasa"] = nasa_temel(pr)
    st0, ne0 = pr["nasa"]
    st, ne = st0.copy(), ne0.copy()
    cell = df["cell"]
    san_c = P.sanayi_kurali(f, N, M, Y, S)
    kal_c = P.kalici_kurali(f, san_c, M, Y, gece)
    statik_c = P.nasa_mirasi(f, C.t("nasa_miras_payi"))
    kalici_c = san_c | kal_c | statik_c
    is_san = san_c.reindex(cell, fill_value=False).to_numpy()
    is_kal = kal_c.reindex(cell, fill_value=False).to_numpy()
    acik = st == ""
    aday = acik & (is_san | is_kal)
    # Yangın koruması: kaynak = kalıcı olmayan hücrelerdeki kara noktaları
    kc = kalici_c.reindex(cell, fill_value=False).to_numpy()
    src = pr["land"] & ~kc
    q = np.where(aday)[0]
    cnt = P.komsu_gun_sayimi(df["cell"].to_numpy()[src], df["dayn"].to_numpy()[src],
                             df["cell"].to_numpy()[q], df["dayn"].to_numpy()[q], k_koruma)
    korunan = np.zeros(len(df), bool); korunan[q[cnt >= G]] = True
    m = aday & is_san & ~korunan; st[m], ne[m] = "sanayi", "kural_sanayi"
    m = aday & is_kal & ~korunan; st[m], ne[m] = "kalici_belirsiz", "kural_kalici"
    m = aday & korunan; st[m], ne[m] = "temiz", "yangin_korumasi"
    st[st == ""] = "temiz"
    return {"status": st, "neden": ne, "san_c": san_c, "kal_c": kal_c, "kalici_c": kalici_c, "korunan": korunan}


def koruma_G_sec(pr: dict, et: dict, k_koruma: int, hedef: float) -> dict:
    """NASA type=2 çoğunluklu VE kural-sanayi hücrelerindeki noktalarda koruma sayımının dağılımı."""
    df, f = pr["df"], pr["f"]
    statik_c = P.nasa_mirasi(f, C.t("nasa_miras_payi")) & et["san_c"]
    cell = df["cell"]
    m = statik_c.reindex(cell, fill_value=False).to_numpy() & pr["land"]
    src = pr["land"] & ~et["kalici_c"].reindex(cell, fill_value=False).to_numpy()
    q = np.where(m)[0]
    cnt = P.komsu_gun_sayimi(df["cell"].to_numpy()[src], df["dayn"].to_numpy()[src],
                             df["cell"].to_numpy()[q], df["dayn"].to_numpy()[q], k_koruma)
    tablo = {int(g): float((cnt >= g).mean()) for g in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 50)}
    secilen = next((g for g in sorted(tablo) if tablo[g] <= hedef), None)
    return {"n_nokta": int(len(q)), "pay_ge_G": tablo, "secilen_G": secilen, "hedef_pay": hedef}


# --------------------------------------------------------------------------- anız
def aniz(pr: dict, status: np.ndarray, F: float, kural: str) -> dict:
    df = pr["df"]
    esik = A.frp_esikleri(df, F)
    land = pr["land"]
    temiz = status == "temiz"
    sub = df[land]
    small_land = A.kucuk_aday(sub, esik, C.t("aniz_kucuk_komsu"))
    small = np.zeros(len(df), bool); small[np.where(land)[0]] = small_land
    ev = df[temiz]
    is_c = small[temiz]
    demo = C.top("aniz_aylari")
    lo = A.loyo(ev, is_c, kural, demo)
    cand = ev[is_c]
    bolgeler = sorted(df["cbolge"].unique())
    # Her yılın anız ayları o yıl HARİÇ diğer yıllardan (döngüselliği azaltır)
    in_month = np.zeros(len(df), bool)
    idx_t = np.where(temiz)[0]
    yil_aylar = {}
    for y in sorted(ev["yr"].unique()):
        am = A.aylar(A.profil(cand, haric_yil=y), kural, demo)
        yil_aylar[int(y)] = am
        sel = (ev["yr"].to_numpy() == y)
        in_month[idx_t[sel]] = A.ayda_mi(ev[sel], am, bolgeler)
    pr_all = A.profil(cand)
    am_all = A.aylar(pr_all, kural, demo)
    aday = temiz & small & in_month
    return {"aday": aday, "esik": esik, "loyo": lo, "aylar": am_all, "profil": pr_all, "yil_aylar": yil_aylar,
            "hasat": A.hasat_uyumu(am_all, C.t("hasat_penceresi")), "n_kucuk_temiz": int((small & temiz).sum())}


# --------------------------------------------------------------------------- referans (C13)
def referans(pr: dict, status: np.ndarray, san_c: pd.Series) -> dict:
    """C13. Her nokta EN FAZLA bir referansa atanır: önce sanayi tesisleri (kapsayan en yakın
    merkez), sonra tesis tamponu dışındaki yangın pencereleri (kapsayan en yakın merkez).
    `durum=ayikla` kayıtlar kullanılmaz. Sınıf dengesi için makro (tesis/yangın başına ortalama)
    ve dengeli kesinlik raporlanır; nokta düzeyi değerler ayrıca durur (F2-06)."""
    ref_tum = pd.read_csv(REF, encoding="utf-8")
    ref = ref_tum[ref_tum["durum"].fillna("kullan") == "kullan"] if "durum" in ref_tum else ref_tum
    if "ref_atama" not in pr:
        pr["ref_atama"] = _ref_atama(pr, ref)
    atama = pr["ref_atama"]
    ind = np.char.startswith(atama.astype(str), "S")
    fire = np.char.startswith(atama.astype(str), "Y")
    return _ref_olc(pr, ref, ref_tum, atama, ind, fire, status, san_c)


def _ref_atama(pr: dict, ref: pd.DataFrame) -> np.ndarray:
    df = pr["df"]
    land = pr["land"]
    lat, lon = df["lat"].to_numpy(), df["lon"].to_numpy()
    day = pd.to_datetime(df["day_tr"]).to_numpy()
    land = pr["land"]

    def mesafe(r):
        dy = (lat - r.lat) * 111.32
        dx = (lon - r.lon) * 111.32 * np.cos(np.radians(r.lat))
        return np.sqrt(dy * dy + dx * dx)

    atama = np.full(len(df), "", dtype=object)
    enyakin = np.full(len(df), np.inf)
    for tur in ("sanayi", "yangin"):
        for r in ref[ref["tur"] == tur].itertuples():
            d = mesafe(r)
            m = land & (d <= r.yaricap_km)
            if tur == "yangin":
                m &= (day >= np.datetime64(r.tarih_bas)) & (day <= np.datetime64(r.tarih_bit))
                m &= ~np.char.startswith(atama.astype(str), "S")  # tesis tamponundaki nokta yangına atanmaz
            gunc = m & ((atama == "") | (d < enyakin)) & ~(np.char.startswith(atama.astype(str), "S") & (tur == "yangin"))
            atama[gunc] = r.id
            enyakin[gunc] = d[gunc]
    return atama


def _ref_olc(pr, ref, ref_tum, atama, ind, fire, status, san_c) -> dict:
    df = pr["df"]
    flag_sys = np.isin(status, KALICI_STATUS)
    flag_nasa = status == "statik_nasa"
    flag_rule = san_c.reindex(df["cell"], fill_value=False).to_numpy()  # yalnız kural (NASA'sız)
    out = {"n_sanayi_nokta": int(ind.sum()), "n_yangin_nokta": int(fire.sum()),
           "n_site": int((ref["tur"] == "sanayi").sum()), "n_yangin": int((ref["tur"] == "yangin").sum()),
           "n_ayiklanan_kayit": int((ref_tum.get("durum") == "ayikla").sum())}
    a_ser = pd.Series(atama)
    for ad, fl in (("sistem", flag_sys), ("kural", flag_rule), ("nasa", flag_nasa)):
        tp = int((fl & ind).sum()); fp = int((fl & fire).sum())
        per = pd.Series(fl).groupby(a_ser).mean()
        site = per[per.index.str.startswith("S")]
        yang = per[per.index.str.startswith("Y")]
        tpr, fpr = float(site.mean()), float(yang.mean())
        out[ad] = {"nokta_precision": tp / (tp + fp) if tp + fp else None, "nokta_recall": tp / max(ind.sum(), 1),
                   "tp": tp, "fp_yangin": fp, "yangin_koruma": 1 - fp / max(fire.sum(), 1),
                   "makro_tesis_recall": tpr, "makro_yangin_fpr": fpr,
                   "dengeli_precision": tpr / (tpr + fpr) if tpr + fpr else None,
                   "site_recall": float((site >= 0.5).mean()), "n_site_tespitli": int(len(site)),
                   "n_yangin_tespitli": int(len(yang))}
    sts = pd.Series(status)
    out["siteler"] = []
    for r in ref.itertuples():
        m = atama == r.id
        out["siteler"].append({"id": r.id, "ad": r.ad, "tur": r.tur, "n": int(m.sum()),
                               "kalici_pay": float(flag_sys[m].mean()) if m.sum() else None,
                               "status": sts[m].value_counts().to_dict() if m.sum() else {}})
    return out


def modis_donemi_tesis(pr: dict, status: np.ndarray, vy: int) -> dict:
    """F2-09: VIIRS öncesi 'sanayi' MODIS noktalarının bilinen tesise yakınlığı (bağımsız referans)."""
    df = pr["df"]
    km = C.t("modis_donemi_tesis_km")
    ref = pd.read_csv(REF, encoding="utf-8")
    ref = ref[ref["tur"] == "sanayi"]
    m = (status == "sanayi") & (df["sensor"].to_numpy() == "MODIS") & (df["yr"].to_numpy() < vy)
    la, lo = df["lat"].to_numpy()[m], df["lon"].to_numpy()[m]
    yakin = np.zeros(int(m.sum()), bool)
    for r in ref.itertuples():
        yakin |= np.hypot((la - r.lat) * 111.32, (lo - r.lon) * 111.32 * np.cos(np.radians(r.lat))) <= km
    return {"n": int(m.sum()), "pay": float(yakin.mean()) if m.sum() else float("nan"), "km": km}


def loyo_tablo(kalib: dict, N, M, Y, S):
    v = kalib["sanayi_loyo"]["sabit_kombinasyon_loyo"].get(f"{N},{M},{Y},{S}")
    if not v:
        return None, None
    tp, fp, fn = v
    return tp / (tp + fp) if tp + fp else None, tp / (tp + fn)


# --------------------------------------------------------------------------- ana akış
def main():
    t0 = time.time()
    pr = hazirla()
    df = pr["df"]
    kalib = json.loads(KALIB.read_text(encoding="utf-8"))
    N, M, F = C.top("N"), C.top("M"), C.top("F")
    Y, S = C.t("Y"), C.t("S")
    alfa, G, kk = C.t("kalici_alfa"), C.t("koruma_G"), C.t("koruma_komsu_k")
    gece = C.t("kalici_gece_payi")
    kural = C.t("aniz_ay_kurali")
    mod = kalib["sanayi_loyo"]["mod_secim"]
    if (mod["N"], mod["M"], mod["Y"], mod["S"]) != (N, M, Y, S):
        print("UYARI: config (N,M,Y,S) LOYO mod seçimiyle aynı değil:", mod)

    et = etiketle(pr, N, M, Y, S, gece, G, kk)
    gsec = koruma_G_sec(pr, et, kk, C.t("koruma_yanlis_pay"))
    if gsec["secilen_G"] != G:
        print("UYARI: koruma_G config", G, "!= veriden seçilen", gsec["secilen_G"], gsec["pay_ge_G"])
    an = aniz(pr, et["status"], F, kural)
    st, ne = et["status"], et["neden"].copy()
    dg = (df["conf_cls"].to_numpy() == "dusuk")
    if C.t("dusuk_guven_etiketle"):
        st = np.where(dg & (st == "temiz"), "dusuk_guven", st)
    tekrar = yillik_tekrar_hucreler(pr, alfa).reindex(df["cell"], fill_value=False).to_numpy() & (st == "temiz")
    for flag, ad in ((dg, "dusuk_guven"), (tekrar, "yillik_tekrar"), (an["aday"], "aniz_adayi")):
        ne = np.where(flag, np.where(ne == "", ad, ne + ";" + ad), ne)
    ref = referans(pr, st, et["san_c"])

    out = pd.DataFrame({"pid": df["pid"].to_numpy(),
                        "status": pd.Categorical(st, categories=["temiz", "deniz", "volkan", "statik_nasa", "sanayi",
                                                                  "dusuk_guven", "aniz", "kalici_belirsiz"]),
                        "status_neden": pd.Categorical(ne)})
    # Olay düzeyi anız (ikinci adım): events.parquet varsa her koşuda yeniden uygulanır (idempotent;
    # kümeleme girdisi {temiz, aniz} olduğundan olay yapısı değişmez).
    olc = None
    if O.hazir():
        out, olc = O.uygula(out, df[["pid", "sensor", "frp"]], an["yil_aylar"], an["esik"])
        if olc["tutarsiz_nokta"]:
            print("UYARI: points_event girdisi {temiz, aniz} ile uyuşmuyor:", olc["tutarsiz_nokta"], "nokta (kümelemeyi yeniden çalıştırın)")
        st = out["status"].astype(str).to_numpy()
    assert len(out) == len(df) and out["status"].notna().all()
    out.to_parquet(C.STATUS_OUT, index=False)

    # ---- duyarlılık (C12)
    sens = {"N": [], "M": [], "F": [], "Y": [], "S": [], "aniz_aylari": [], "kalici_alfa": [],
            "kalici_gece": [], "koruma_G": []}

    def satir(param, deger, e, extra=None):
        s = e["status"]
        r = referans(pr, s, e["san_c"])
        row = {"deger": deger, "sanayi": int((s == "sanayi").sum()), "kalici_belirsiz": int((s == "kalici_belirsiz").sum()),
               "temiz": int((s == "temiz").sum()), "yangin_korumasi": int(e["korunan"].sum()),
               "ref_precision": r["sistem"]["dengeli_precision"], "ref_recall": r["sistem"]["makro_tesis_recall"],
               "yangin_koruma": r["sistem"]["yangin_koruma"]}
        row.update(extra or {})
        return row

    for n in (10, 20, 40, 80):
        e = et if n == N else etiketle(pr, n, M, Y, S, gece, G, kk)
        lp, lr = loyo_tablo(kalib, n, M, Y, S)
        sens["N"].append(satir("N", n, e, {"loyo_precision_type2": lp, "loyo_recall_type2": lr}))
    for mm in (4, 6, 8, 10, 12):
        e = et if mm == M else etiketle(pr, N, mm, Y, S, gece, G, kk)
        lp, lr = loyo_tablo(kalib, N, mm, Y, S)
        sens["M"].append(satir("M", mm, e, {"loyo_precision_type2": lp, "loyo_recall_type2": lr}))
    for yy in (2, 3, 5, 8):
        e = et if yy == Y else etiketle(pr, N, M, yy, S, gece, G, kk)
        lp, lr = loyo_tablo(kalib, N, M, yy, S)
        sens["Y"].append(satir("Y", yy, e, {"loyo_precision_type2": lp, "loyo_recall_type2": lr}))
    for ss in (1, 2, 4, 6):
        e = et if ss == S else etiketle(pr, N, M, Y, ss, gece, G, kk)
        lp, lr = loyo_tablo(kalib, N, M, Y, ss)
        sens["S"].append(satir("S", ss, e, {"loyo_precision_type2": lp, "loyo_recall_type2": lr}))
    for gg in (0.3, 0.5, 0.7):
        e = et if gg == gece else etiketle(pr, N, M, Y, S, gg, G, kk)
        sens["kalici_gece"].append(satir("gece", gg, e))
    temiz_m = et["status"] == "temiz"
    for a in (1e-2, 1e-3, 1e-4, 1e-6):
        tk = yillik_tekrar_hucreler(pr, a).reindex(df["cell"], fill_value=False).to_numpy()
        sens["kalici_alfa"].append({"deger": a, "yillik_tekrar_bayrakli_temiz": int((tk & temiz_m).sum()),
                                    "temiz": int(temiz_m.sum())})
    for gg in (1, 2, 3, 5, 10):
        e = et if gg == G else etiketle(pr, N, M, Y, S, gece, gg, kk)
        sens["koruma_G"].append(satir("G", gg, e))
    for ff in (5, 10, 15, 20, 30):
        a2 = an if ff == F else aniz(pr, et["status"], ff, kural)
        sens["F"].append({"deger": ff, "F_viirs_esdeger": a2["esik"]["VIIRS"], "yuzdelik": a2["esik"]["yuzdelik"],
                          "aniz_adayi": int(a2["aday"].sum()), "kucuk_temiz": a2["n_kucuk_temiz"],
                          "loyo_kapsama": a2["loyo"]["kapsama_ort"], "loyo_kaldirac": a2["loyo"]["kaldirac"]})
    for kr in A.KURALLAR:
        a2 = an if kr == kural else aniz(pr, et["status"], F, kr)
        sens["aniz_aylari"].append({"deger": kr, "aniz_adayi": int(a2["aday"].sum()),
                                    "loyo_kapsama": a2["loyo"]["kapsama_ort"], "loyo_taban": a2["loyo"]["taban_ort"],
                                    "loyo_kaldirac": a2["loyo"]["kaldirac"], "hasat_penceresi_payi": a2["hasat"]["pay"],
                                    "aylar": a2["aylar"]})

    # ---- anız takvimi çıktısı
    TAKVIM_OUT.write_text(json.dumps({
        "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "kural": kural, "etiket": "tahmini (arazi örtüsü doğrulanmadı)",
        "frp_esik": an["esik"], "aylar": an["aylar"], "yil_aylar_loyo": an["yil_aylar"],
        "profil": {b: {int(m): float(v) for m, v in row.items()} for b, row in an["profil"].iterrows()},
        "loyo": an["loyo"], "hasat_uyumu": an["hasat"]}, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- metrikler
    sure = round(time.time() - t0, 1)
    vc = pd.Series(st).value_counts()
    sl = kalib["sanayi_loyo"]
    fo = pd.DataFrame(sl["folds"])
    def havuz(d):
        tp, fp, fn = d["test_tp"].sum(), d["test_fp"].sum(), d["test_fn"].sum()
        return tp / (tp + fp), tp / (tp + fn)
    vy = C.t("viirs_baslangic_yili")
    pm, rm = havuz(fo[fo["yil"] < vy]); pv, rv = havuz(fo[fo["yil"] >= vy])
    nrt = kalib["nrt_telafi_loyo"]["birlesim"]
    mt = {}

    def put(k, v, unit, tanim, etiket="ölçüldü", betik=BETIK):
        mt[k] = {"value": v, "unit": unit, "tanim": tanim, "betik": betik, "veri_surumu": C.VERI_SURUMU, "etiket": etiket}

    for s_ in ["temiz", "deniz", "volkan", "statik_nasa", "sanayi", "kalici_belirsiz", "dusuk_guven", "aniz"]:
        put(f"temizlik_status_{s_}", int(vc.get(s_, 0)), "nokta", f"status='{s_}' olan nokta sayısı (K3: silme yok)")
    put("temizlik_nrt_statik_mirasi", int((ne == "nrt_nasa_statik_mirasi").sum() + pd.Series(ne).str.startswith("nrt_nasa_statik_mirasi;").sum()),
        "nokta", "NRT (type yok) noktalarından hücre mirasıyla statik_nasa alanlar")
    put("temizlik_yangin_korumasi_nokta", int(et["korunan"].sum()), "nokta", "Kalıcı hücrede olup çevresinde aynı gün yangın olduğu için temiz bırakılan nokta")
    put("temizlik_yillik_tekrar_bayrakli_temiz", int(tekrar.sum()), "nokta",
        "status=temiz ama hücresi rastlantı modeline göre olağan dışı sık yıl aktif (çoğu tarım ovası; bayrak, silinmez). Sayım ölçüldü; bayrağın doğruluğu doğrulanmadı")
    put("temizlik_aniz_adayi_nokta", int(an["aday"].sum()), "nokta", "status_neden'de aniz_adayi bayrağı taşıyan nokta sayısı (nokta düzeyi vekil). Sayım ölçüldü; kuralın doğruluğu tahmini")
    put("temizlik_sanayi_loyo_precision", sl["havuz"]["precision"], "oran", "Sanayi kuralının NASA type=2 ile uyuşması, yıl dışarıda bırakma (havuz, tüm yıllar). type=2 yer gerçeği değil, NASA maskesidir")
    put("temizlik_sanayi_loyo_recall", sl["havuz"]["recall"], "oran", "Aynı LOYO, NASA type=2 noktalarının kuralla yakalanan payı")
    mk = modis_donemi_tesis(pr, et["status"], vy)
    put("temizlik_sanayi_loyo_precision_modis_donemi", pm, "oran",
        "LOYO NASA type=2 ile UYUŞMA (doğruluk değil), viirs_baslangic_yili öncesi (yalnız MODIS). Düşüklüğün kaynağı referans "
        f"seyrekliği: o dönemde NASA MODIS type=2 çok seyrek; kuralın 'sanayi' dediği MODIS noktalarının {mk['pay']:.2f} payı "
        f"doğrulama setindeki bir tesise <= {mk['km']} km (temizlik_modis_donemi_sanayi_tesis_payi). Kural hatası değil, referans eksikliği (F2-09)")
    put("temizlik_modis_donemi_sanayi_tesis_payi", mk["pay"], "oran",
        f"viirs_baslangic_yili öncesi status=sanayi MODIS noktalarından ({mk['n']}) doğrulama setindeki bir tesise <= {mk['km']} km olanların payı")
    put("temizlik_sanayi_loyo_recall_modis_donemi", rm, "oran", "LOYO NASA type=2 yakalama, viirs_baslangic_yili öncesi (referans seyrek)")
    put("temizlik_sanayi_loyo_precision_viirs_donemi", pv, "oran", "LOYO NASA type=2 ile uyuşma, viirs_baslangic_yili ve sonrası")
    put("temizlik_sanayi_loyo_recall_viirs_donemi", rv, "oran", "LOYO NASA type=2 yakalama, viirs_baslangic_yili ve sonrası")
    put("temizlik_sanayi_loyo_kat_kararliligi", sl["secim_sikligi"][str(tuple(mod.values()))] / len(sl["folds"]), "oran",
        "LOYO katlarının kaçında config'teki (N,M,Y,S) seçildi")
    put("temizlik_nrt_telafi_precision", nrt["precision"], "oran", "NRT telafisi (NASA hücre mirası ∪ sanayi kuralı) LOYO'da NASA type=2 ile uyuşma")
    put("temizlik_nrt_telafi_recall", nrt["recall"], "oran", "NRT telafisi LOYO yakalama")
    rs, rk, rn = ref["sistem"], ref["kural"], ref["nasa"]
    sinif = (f"{ref['n_sanayi_nokta']} tesis noktası ({rs['n_site_tespitli']} tesis) / {ref['n_yangin_nokta']} yangın noktası "
             f"({rs['n_yangin_tespitli']} yangın); {ref['n_ayiklanan_kayit']} çakışan kayıt ayıklandı, her nokta tek referansa atandı")
    put("ref_precision", rs["dengeli_precision"], "oran",
        "C13 dengeli kesinlik = makro tesis yakalama / (makro tesis yakalama + makro yangın yanlış-işaret oranı); sınıflar eşit "
        f"ağırlıklı (nokta düzeyi kesinlik sınıf dengesizliğiyle şişer: temizlik_ref_nokta_precision). {sinif}", "tahmini")
    put("ref_recall", rs["makro_tesis_recall"], "oran",
        f"C13 makro tesis yakalama: tesis başına kalıcı etiketli nokta payının ortalaması (tesis düzeyi >=%50 ölçütü: temizlik_ref_site_recall). {sinif}", "tahmini")
    put("temizlik_ref_nokta_precision", rs["nokta_precision"], "oran", f"Nokta düzeyi kesinlik; sınıf dengesizliği nedeniyle yüksek görünür, sunumda kullanmayın. {sinif}", "tahmini")
    put("temizlik_ref_nokta_recall", rs["nokta_recall"], "oran", f"Nokta düzeyi yakalama (büyük tesisler baskın). {sinif}", "tahmini")
    put("temizlik_ref_site_recall", rs["site_recall"], "oran", "Tespiti olan tesislerden noktalarının en az yarısı kalıcı etiketli olanların payı (tesis düzeyi yakalama)", "tahmini")
    put("temizlik_ref_yangin_koruma", rs["yangin_koruma"], "oran", "Bilinen yangın noktalarının kalıcı etiket ALMAMA payı (nokta düzeyi)", "tahmini")
    put("temizlik_ref_makro_yangin_fpr", rs["makro_yangin_fpr"], "oran", "Yangın başına kalıcı etiketli nokta payının ortalaması (gerçek yangını yanlış işaretleme)", "tahmini")
    put("temizlik_ref_kural_makro_recall", rk["makro_tesis_recall"], "oran", "Yalnız sanayi kuralı (NASA type olmadan; NRT senaryosu) makro tesis yakalama", "tahmini")
    put("temizlik_ref_kural_dengeli_precision", rk["dengeli_precision"], "oran", "Yalnız sanayi kuralı dengeli kesinlik", "tahmini")
    put("temizlik_ref_nasa_makro_recall", rn["makro_tesis_recall"], "oran", "Yalnız NASA statik etiketi (statik_nasa) makro tesis yakalama: sistem yakalamasında NASA katkısı", "tahmini")
    put("temizlik_sta_maskesi_karsilastirma", None, "", "FIRMS Static Thermal Anomalies maskesi deneysel; toplu indirme/API bulunamadı -> karşılaştırma yapılmadı", "doğrulanmadı")
    put("temizlik_aniz_loyo_kapsama", an["loyo"]["kapsama_ort"], "oran", "Bir yılın küçük-aday tespitlerinin, o yıl hariç öğrenilen bölge anız aylarına düşme payı (ortalama)")
    put("temizlik_aniz_loyo_taban", an["loyo"]["taban_ort"], "oran", "Aynı aylara düşen büyük (aday olmayan) tespit payı")
    put("temizlik_aniz_loyo_kaldirac", an["loyo"]["kaldirac"], "oran", "kapsama / taban (1'den büyükse takvim küçük ateşleri ayırt ediyor)")
    put("temizlik_aniz_hasat_penceresi_payi", an["hasat"]["pay"], "oran", "Öğrenilen bölge-anız aylarının web kaynaklı kaba hasat penceresi (Haz-Eki) içinde kalma payı", "tahmini")
    put("temizlik_aniz_arazi_ortusu", None, "", "Anız adaylarının tarım alanında olup olmadığı (ESA WorldCover) kontrol edilmedi: indirme onayı gerekiyor", "doğrulanmadı")
    put("temizlik_F_modis_medyan", an["esik"]["modis_type0_medyan"], "MW", "MODIS arşiv type=0 FRP medyanı (F seçim gerekçesi)")
    put("temizlik_F_viirs_esdeger", an["esik"]["VIIRS"], "MW", "F'nin VIIRS eşdeğeri (yüzdelik eşleştirme)")
    put("temizlik_koruma_G_veriden", gsec["secilen_G"], "tespit", "Statik hücrelerde yanlış koruma payı <= koruma_yanlis_pay olan en küçük G")
    put("temizlik_sure_sn", sure, "s", "build_status.py çalışma süresi (duyarlılık dahil)")
    C.PART.parent.mkdir(parents=True, exist_ok=True)
    C.PART.write_text(json.dumps({"metrics": mt, "sensitivity": sens}, ensure_ascii=False, indent=1, default=float),
                      encoding="utf-8")
    if olc is not None:
        O.metrik_yaz(dict(olc))
    import worldcover as W  # arazi örtüsü sonuçları (varsa) korunur
    W.birlestir()
    (C.AUDIT / "temizlik_ozet.json").write_text(json.dumps(
        {"koruma_G": gsec, "referans": ref, "status": {k: int(v) for k, v in vc.items()}, "sure_sn": sure},
        ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(vc.to_string())
    print("referans", json.dumps(ref, default=float))
    print("koruma G", gsec)
    print("anız", an["esik"], an["loyo"]["kapsama_ort"], an["loyo"]["taban_ort"], an["hasat"], an["aylar"])
    print("süre", sure, "sn")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
