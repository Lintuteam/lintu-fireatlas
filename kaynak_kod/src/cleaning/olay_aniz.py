"""Olay düzeyinde anız kararı ve birleşme–anız etkileşimi (U-09, U-12).

Basitçe: Anız kararı tek tek noktaya değil "olay"a (kümeleme ajanının birleştirdiği yangın)
verilir: olay küçük, kısa, zayıf ve bölgesinin anız ayında başladıysa olayın BÜTÜN noktaları
anız olur; değilse hiçbiri (kısmi etiket yok).
"Küçük"ü sayarken iki uyduyu toplamıyoruz: aynı küçük ateşi MODIS 1, VIIRS 3 noktayla
görebilir; toplayınca 4 olur ve 2012 sonrası (VIIRS dönemi) olaylar haksız yere "büyük" sayılır.
Bunun yerine MODIS ölçeğindeki eşleştirme birimini (n_mcell) sayıyoruz.

Teknik olarak:
- Girdi: events.parquet (yalnız {temiz, aniz} noktalardan kurulmuş olaylar), points_event.parquet.
- Büyüklük ölçüsü (`temizlik.aniz_olay_sayim`): 'n_mcell' (seçilen), 'sensor_max' = max(n_modis,
  n_viirs), 'toplam' = n (demo). Seçim gerekçesi: sensör dönemi tutarlılığı ölçülür
  (VIIRS öncesi/sonrası anız olay payı farkı; metrics temizlik_pay_viirs_*).
- Koşullar: büyüklük <= aniz_olay_max_tespit, sure_saat <= aniz_olay_max_sure_saat,
  olaydaki tüm noktalarda FRP < F_sensör (VIIRS eşdeğeri yüzdelik eşleştirme), TR başlangıç
  ayı olayın bölgesinin o yıl HARİÇ öğrenilmiş anız aylarında.
- uygula(): status 'aniz' önce 'temiz'e sıfırlanır, sonra yeniden yazılır -> idempotent.
  build_status.py sonunda otomatik çağrılır; tek başına: python src/cleaning/olay_aniz.py --yaz
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

TAKVIM = C.AUDIT / "aniz_takvimi.json"
EVENTS = C.PROCESSED / "events.parquet"
EVENTS_P = C.PROCESSED / "points_event.parquet"
BETIK = "src/cleaning/olay_aniz.py"
SAYIMLAR = ("n_mcell", "sensor_max", "toplam")


def hazir() -> bool:
    return EVENTS.exists() and EVENTS_P.exists()


def olay_tablosu(pts: pd.DataFrame, events: pd.DataFrame, yil_aylar: dict, frp_esik: dict) -> pd.DataFrame:
    """pts: pid, sensor, frp, event_id (olaydaki noktalar). Dönen: olay başına koşul sütunları."""
    p = pts[pts["event_id"] >= 0]
    kucuk = p["frp"].to_numpy() < np.where(p["sensor"].to_numpy() == "MODIS", frp_esik["MODIS"], frp_esik["VIIRS"])
    frp_ok = pd.Series(kucuk, index=p.index).groupby(p["event_id"]).all()
    ev = events.set_index("event_id")[["n", "n_modis", "n_viirs", "n_mcell", "sure_saat", "day_tr_start", "il"]].copy()
    ev["frp_ok"] = frp_ok.reindex(ev.index).fillna(False).astype(bool)
    d = pd.to_datetime(ev["day_tr_start"])
    ev["yr"], ev["mon"] = d.dt.year.to_numpy(), d.dt.month.to_numpy()
    ev["bolge"] = ev["il"].map(C.IL_BOLGE).fillna("bilinmeyen")
    lut = {(int(y), b, int(m)) for y, bm in yil_aylar.items() for b, ms in bm.items() for m in ms}
    ev["ay_ok"] = [(int(y), b, int(m)) in lut for y, b, m in zip(ev["yr"], ev["bolge"], ev["mon"])]
    ev["sensor_max"] = np.maximum(ev["n_modis"], ev["n_viirs"])
    ev["toplam"] = ev["n"]
    return ev


def karar(ev: pd.DataFrame, sayim: str, max_n, max_h) -> pd.Series:
    return (ev[sayim] <= max_n) & (ev["sure_saat"] <= max_h) & ev["frp_ok"] & ev["ay_ok"]


def uygula(st: pd.DataFrame, pts: pd.DataFrame, yil_aylar: dict, frp_esik: dict) -> tuple[pd.DataFrame, dict]:
    """st: pid, status, status_neden. pts: pid, sensor, frp, yr. Dönen: güncel st + ölçüler."""
    events = pd.read_parquet(EVENTS)
    pe = pd.read_parquet(EVENTS_P)
    s = st["status"].astype(str).to_numpy().copy()
    n_ = st["status_neden"].astype(str).to_numpy().copy()
    # idempotent: önceki anız etiketini geri al
    eski = s == "aniz"
    s[eski] = "temiz"
    n_ = (pd.Series(n_).str.replace(r"(^|;)olay_aniz(?=;|$)", "", regex=True)
          .str.strip(";").to_numpy(dtype=object))
    m = st[["pid"]].assign(_i=np.arange(len(st))).merge(pe, on="pid", how="left")
    m = m.sort_values("_i")
    eid = m["event_id"].fillna(-1).astype(np.int64).to_numpy()
    girdi = s == "temiz"
    tutarsiz = int(((eid >= 0) != girdi).sum())  # olay girdisi = {temiz, aniz}
    p = pts.assign(event_id=eid)
    ev = olay_tablosu(p, events, yil_aylar, frp_esik)
    max_n, max_h = C.t("aniz_olay_max_tespit"), C.t("aniz_olay_max_sure_saat")
    sayim = C.t("aniz_olay_sayim")
    olc = {"tutarsiz_nokta": tutarsiz}
    for sy in SAYIMLAR:
        k = karar(ev, sy, max_n, max_h)
        olc[f"olay_{sy}"] = int(k.sum())
        vy = C.t("viirs_baslangic_yili")  # geçiş yılı karşılaştırmaya girmez
        pre, post = ev["yr"] < vy, ev["yr"] > vy
        olc[f"pay_viirs_oncesi_{sy}"] = float(k[pre].mean())
        olc[f"pay_viirs_sonrasi_{sy}"] = float(k[post].mean())
    an = karar(ev, sayim, max_n, max_h)
    yaz = girdi & (eid >= 0) & an.reindex(eid, fill_value=False).to_numpy()
    s[yaz] = "aniz"
    n_[yaz] = np.where(n_[yaz] == "", "olay_aniz", n_[yaz] + ";olay_aniz")
    out = pd.DataFrame({"pid": st["pid"].to_numpy(),
                        "status": pd.Categorical(s, categories=st["status"].cat.categories),
                        "status_neden": pd.Categorical(n_)})
    aday = pd.Series(n_).str.contains("aniz_adayi").to_numpy() & (eid >= 0)
    ad_ev = ev.loc[eid[aday]]
    kay = ad_ev[~an.reindex(eid[aday]).to_numpy()]
    olc.update({"olay_aniz_olay": int(an.sum()), "olay_aniz_nokta": int(yaz.sum()),
                "aday_olayda_aniz_pay": float(an.reindex(eid[aday]).mean()),
                "kayip_nedeni_n": int((kay[sayim] > max_n).sum()), "kayip_nedeni_sure": int((kay["sure_saat"] > max_h).sum()),
                "kayip_nedeni_frp": int((~kay["frp_ok"]).sum()), "kayip_nedeni_ay": int((~kay["ay_ok"]).sum())})
    sens = []
    for mn in (1, 2, 3, 5, 10):
        row = {"deger": mn}
        for sy in SAYIMLAR:
            k = karar(ev, sy, mn, max_h)
            row[f"olay_{sy}"] = int(k.sum())
            row[f"nokta_{sy}"] = int((girdi & (eid >= 0) & k.reindex(eid, fill_value=False).to_numpy()).sum())
        sens.append(row)
    olc["_sens"] = sens
    return out, olc


def metrik_yaz(olc: dict):
    part = json.loads(C.PART.read_text(encoding="utf-8"))
    sens = olc.pop("_sens")
    for k, v in olc.items():
        # F2-05: sayımlar ve oranlar veriden sayılır -> ölçüldü; kuralın doğruluğu iddia edilmez (tanımda)
        if k.endswith("sure_sn"):
            unit = "s"
        elif "pay" in k:
            unit = "oran"
        elif k.startswith("olay_") and not k.endswith("_nokta"):
            unit = "olay"
        else:
            unit = "nokta"
        part["metrics"][f"temizlik_{k}"] = {
            "value": v, "unit": unit,
            "tanim": f"olay düzeyi anız: {k} (events.parquet; sayım={C.t('aniz_olay_sayim')}). Veriden sayıldı; "
                     "anız etiketi kurala göre etikettir, doğruluğu tahmini (arazi örtüsü uyumu: temizlik_aniz_arazi_ortusu)",
            "betik": BETIK, "veri_surumu": C.VERI_SURUMU, "etiket": "ölçüldü"}
    part["sensitivity"]["aniz_olay_max_tespit"] = sens
    C.PART.write_text(json.dumps(part, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


def main():
    t0 = time.time()
    takvim = json.loads(TAKVIM.read_text(encoding="utf-8"))
    st = pd.read_parquet(C.STATUS_OUT)
    pts = C.load_points()[["pid", "sensor", "frp"]]
    assert (pts["pid"].to_numpy() == st["pid"].to_numpy()).all()
    out, olc = uygula(st, pts, takvim["yil_aylar_loyo"], takvim["frp_esik"])
    olc["olay_aniz_sure_sn"] = round(time.time() - t0, 1)
    if "--yaz" in sys.argv:
        out.to_parquet(C.STATUS_OUT, index=False)
        metrik_yaz(dict(olc))
    print(json.dumps({k: v for k, v in olc.items() if k != "_sens"}, ensure_ascii=False, default=float))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
