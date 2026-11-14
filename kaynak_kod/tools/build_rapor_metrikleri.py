"""Rapor için veri özeti ve demo senaryosu metrikleri (reports/metrics_parts/rapor.json).

Basitçe: Raporlarda "veri kaç satır, hangi yıllar, demoda hangi günü açalım?" gibi
sayılar lazım. Bunları elle yazmıyoruz; gerçek tablolardan bu betik hesaplar ve
diğer ajanların fişleri gibi bir fiş (metrics_parts/rapor.json) bırakır.
`tools/build_metrics.py` bu fişi öteki fişlerle birleştirir.

Teknik olarak: points / points_status / points_event / events parquet dosyalarını
okur. Demo seçimi kurala bağlıdır (aşağıda): sabit tarih/il yazılmaz, veri değişirse
seçim kendiliğinden değişir.
  S1 çok tespit - az olay günü: nokta (olaya bağlı) / o gün başlayan olay oranı en büyük
     gün (en az 500 tespit).
  S2 sanayi bölgesi: 'sanayi' etiketli nokta sayısı en çok il.
  S3 sensör geçiş yılı: ilk VIIRS gününün yılı.
  S4 yalnız-VIIRS örneği: match_class = yalniz_viirs olaylar içinde en çok VIIRS noktalı.
Tüm değerler "ölçüldü"; seçim kuralı `tanim` alanında yazılıdır.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "reports" / "metrics_parts" / "rapor.json"
BETIK = "tools/build_rapor_metrikleri.py"
SURUM = "points v1"
M: dict = {}


def put(key, value, unit, tanim, etiket="ölçüldü"):
    if hasattr(value, "item"):
        value = value.item()
    M[key] = {"value": value, "unit": unit, "tanim": tanim, "betik": BETIK,
              "veri_surumu": SURUM, "etiket": etiket}


def main() -> int:
    pts = pd.read_parquet(P / "points.parquet", columns=["pid", "day_tr", "src_year", "sensor", "type", "il", "lat", "lon"])
    st = pd.read_parquet(P / "points_status.parquet", columns=["pid", "status"])
    pe = pd.read_parquet(P / "points_event.parquet")
    ev = pd.read_parquet(P / "events.parquet",
                         columns=["event_id", "day_tr_start", "il", "n_modis", "n_viirs", "frp_sum", "match_class", "n", "sure_saat"])
    pts = pts.merge(st, on="pid").merge(pe, on="pid")
    pts["status"] = pts["status"].astype(str)

    # ---- veri özeti
    put("veri_toplam_nokta", len(pts), "nokta", "points.parquet satır sayısı (ham tespit; hiçbiri silinmedi, K3)")
    put("veri_modis_nokta", (pts.sensor == "MODIS").sum(), "nokta", "MODIS (Terra+Aqua) tespit sayısı")
    put("veri_viirs_nokta", (pts.sensor == "VIIRS").sum(), "nokta", "VIIRS (SNPP, N20, N21) tespit sayısı")
    put("veri_yil_bas", pts.src_year.min(), "yıl", "veri dosyalarının ilk yılı")
    put("veri_yil_bit", pts.src_year.max(), "yıl", "veri dosyalarının son yılı (kısmi yıl, NRT içerir)")
    put("veri_son_gun", str(pts.day_tr.max()), "TR günü", "veride görülen son TR günü")
    put("veri_nrt_nokta", (pts["type"] == -1).sum(), "nokta", "NRT (type=-1) tespit sayısı: bu noktalarda NASA type etiketi yok")
    put("veri_ilk_viirs_yili", pd.to_datetime(pts.loc[pts.sensor == "VIIRS", "day_tr"]).dt.year.min(), "yıl",
        "ilk VIIRS tespitinin TR yılı (sensör geçiş yılı)")
    kum = pts.status.isin(["temiz", "aniz"]).sum()
    put("huni_kumeleme_girdi", kum, "nokta", "kümelemeye giren nokta: status temiz veya aniz")
    put("huni_temiz_pay", round(100 * (pts.status == "temiz").mean(), 1), "%", "status=temiz noktaların ham toplamdaki payı")
    put("huni_aniz_pay", round(100 * (pts.status == "aniz").mean(), 1), "%", "status=aniz noktaların ham toplamdaki payı")
    nasa = pts.status.isin(["deniz", "volkan", "statik_nasa"]).sum()
    kural = pts.status.isin(["sanayi", "kalici_belirsiz"]).sum()
    put("huni_nasa_etiket_pay", round(100 * nasa / len(pts), 1), "%", "NASA etiketiyle (deniz, volkan, statik kaynak) ayrılan nokta payı")
    put("huni_kural_etiket_pay", round(100 * kural / len(pts), 1), "%", "bizim kuralımızla (sanayi, kalıcı belirsiz) ayrılan nokta payı")
    put("huni_olay_sayisi", len(ev), "olay", "events.parquet satır sayısı (temiz + anız noktalardan)")
    put("huni_tek_tespitli_olay", int((ev.n == 1).sum()), "olay", "tek tespitten oluşan olay sayısı")
    put("huni_en_buyuk_olay_tespit", int(ev.n.max()), "tespit", "en büyük olayın tespit sayısı (gerçek mega yangın; zincir hatası değil, bkz. docs/kumeleme_yontemi.md)")

    # ---- S1: çok tespit - az olay günü
    d = ev.groupby("day_tr_start").agg(tespit=("n", "sum"), olay=("event_id", "size"))
    d = d[d.tespit >= 500]
    d["oran"] = d.tespit / d.olay
    gun = d["oran"].idxmax()
    r = d.loc[gun]
    sil = ev[ev.day_tr_start == gun]
    buyuk = sil.sort_values("n", ascending=False).iloc[0]
    put("demo1_gun", str(gun), "TR günü", "S1: o gün başlayan olayların tespit sayısı / olay sayısı en büyük gün (en az 500 tespit)")
    put("demo1_tespit", int(r.tespit), "tespit", "S1 gününde başlayan olayların toplam tespiti")
    put("demo1_olay", int(r.olay), "olay", "S1 gününde başlayan olay sayısı")
    put("demo1_oran", round(float(r.oran), 1), "tespit/olay", "S1 günü: tespit sayısının olay sayısına oranı")
    put("demo1_il", str(buyuk.il), "il", "S1 gününün en büyük olayının ili")
    put("demo1_en_buyuk_olay_tespit", int(buyuk.n), "tespit", "S1 gününde başlayan en büyük olayın tespit sayısı")
    put("demo1_en_buyuk_olay_sure", round(float(buyuk.sure_saat), 1), "saat", "S1 gününün en büyük olayının süresi")

    # ---- S2: sanayi bölgesi
    s2 = pts[pts.status == "sanayi"]
    il = s2.il.value_counts().index[0]
    sn = s2[s2.il == il]
    put("demo2_il", str(il), "il", "S2: 'sanayi' etiketli nokta sayısı en çok il")
    put("demo2_sanayi_nokta", len(sn), "nokta", "S2 ilindeki sanayi etiketli nokta")
    put("demo2_il_nokta_pay", round(100 * len(sn) / (pts.il == il).sum(), 1), "%", "S2 ilinde sanayi etiketli noktaların il toplamındaki payı")
    put("demo2_hucre", sn[["lat", "lon"]].round(2).drop_duplicates().shape[0], "hücre", "S2 ilinde sanayi noktalarının düştüğü 0,01° hücre sayısı")
    put("demo2_yil_sayisi", pd.to_datetime(sn.day_tr).dt.year.nunique(), "yıl", "S2 ilinde sanayi noktası görülen farklı yıl")

    # ---- S4: yalnız VIIRS örneği
    yv = ev[(ev.match_class == "yalniz_viirs") & (ev.n_modis == 0)].sort_values(["n_viirs", "frp_sum"], ascending=False).iloc[0]
    put("demo4_gun", str(yv.day_tr_start), "TR günü", "S4: yalnız-VIIRS sınıfında en çok VIIRS noktalı olayın günü")
    put("demo4_il", str(yv.il), "il", "S4 olayının ili")
    put("demo4_n_viirs", int(yv.n_viirs), "nokta", "S4 olayındaki VIIRS nokta sayısı")
    put("demo4_frp", round(float(yv.frp_sum), 1), "MW", "S4 olayının toplam FRP'si")
    put("demo4_olay_id", int(yv.event_id), "kimlik", "S4 olayının event_id değeri")

    # ---- denetçi bağımsız yeniden hesabı ve doğrulama seti (audit/ çıktıları)
    yh = json.loads((ROOT / "audit" / "yeniden_hesap.json").read_text(encoding="utf-8"))
    kar = {k: v for k, v in yh.items() if isinstance(v, dict) and "fark" in v}
    sifir = [k for k, v in kar.items() if v["fark"] == 0]
    bilgi = [k for k, v in kar.items() if v["fark"] != 0 and v.get("aciklama")]
    put("yh_girdi", len(kar), "karşılaştırma", "audit/yeniden_hesap.json içinde beklenen/bulunan karşılaştırması olan girdi")
    put("yh_fark_sifir", len(sifir), "karşılaştırma", "bağımsız yeniden hesapla fark = 0 olan girdi")
    put("yh_aciklanmis_fark", len(bilgi), "karşılaştırma", "fark ≠ 0 / karşılaştırılamaz ama açıklaması yazılı (bilgi) girdi")
    ds = pd.read_csv(ROOT / "audit" / "dogrulama_seti.csv")
    kul = ds[ds.durum == "kullan"]
    put("dogrulama_sanayi_tesis", int((kul.tur == "sanayi").sum()), "tesis", "doğrulama setinde kullanılan sanayi tesisi (OSM)")
    put("dogrulama_bilinen_yangin", int((kul.tur == "yangin").sum()), "yangın", "doğrulama setinde kullanılan bilinen yangın (Wikipedia + OSM ilçe merkezi)")
    put("dogrulama_ayiklanan", int((ds.durum == "ayikla").sum()), "kayıt", "çakışma/belirsizlik nedeniyle ayıklanan kayıt (F2-06)")

    # ---- erişilebilirlik, performans, kapsam (audit/ ve data/ çıktıları)
    er = json.loads((ROOT / "audit" / "erisilebilirlik.json").read_text(encoding="utf-8"))
    pf = json.loads((ROOT / "audit" / "performans.json").read_text(encoding="utf-8"))
    put("a11y_klavye_oran", er["klavye"]["oran"], "oran", "Tab ile ulaşılabilir etkileşimli öğe payı (audit/erisilebilirlik.json)")
    put("a11y_aria_adli_oran", er["aria"]["oran_adli"], "oran", "erişilebilir adı olan etkileşimli öğe payı")
    put("a11y_kontrast_min", er["kontrast_min"], "oran", "ölçülen en düşük yazı/zemin kontrast oranı (WCAG AA 4,5)")
    put("a11y_palet_min_de", er["renk_korlugu"]["min_palet_dE"], "CIE76 dE", "renk körlüğü simülasyonunda paletler arası en küçük ayırt edilebilirlik eşiği")
    put("perf_esik_degisimi_sn", pf["esik_degisimi_saniye"], "s", "eşik değişince tüm görünümlerin yeniden çizim süresi (tek ölçüm, bu makine)")
    put("perf_olay_sayisi", pf["olay_sayisi"], "olay", "performans ölçümünde arayüze yüklü olay sayısı")
    cov = pd.read_parquet(P / "coverage.parquet", columns=["observed"])
    put("kapsam_kesinti_uydu_gunu", int((~cov.observed).sum()), "uydu-gün", "çıkarımla kesinti işaretli uydu-günü (NASA geçiş listesi değil; etiket tahmini)", etiket="tahmini")

    # ---- C03 kaba kuvvet testi ve ham dosya sayısı
    inv = json.loads((P / "inventory.json").read_text(encoding="utf-8"))
    put("veri_dosya_sayisi", len(inv["files_sha256"]), "dosya", "ham FIRMS xlsx dosyası sayısı (SHA-256 envanteri)")
    cr = json.loads((ROOT / "audit" / "check_results.json").read_text(encoding="utf-8"))
    c03 = next(r for r in cr["results"] if r["code"] == "C03")
    det = c03.get("detail", "")
    try:
        det = det.encode("cp1252").decode("utf-8")
    except Exception:
        pass
    mo = re.search(r"=(\d+) nokta=(\d+) kural=(\d+) \S+=(\d+) fark_olan=(\d+)", det)
    mu = re.search(r"(\d+)/(\d+)", det)
    if mo and mu:
        a, b, c, d, e = map(int, mo.groups())
        t = "check_all C03 çıktısı (tools/check_all.py, src/clustering/bruteforce_check.py)"
        put("c03_orneklem", a, "örneklem", "kaba kuvvet karşılaştırmasında kullanılan örneklem sayısı; " + t)
        put("c03_nokta", b, "nokta", "kaba kuvvet örneklemlerindeki toplam nokta; " + t)
        put("c03_kural", c, "kural çeşidi", "denenen kümeleme kuralı çeşidi; " + t)
        put("c03_karsilastirma", d, "karşılaştırma", "hızlı kümeleme ile kaba kuvvet arası karşılaştırma sayısı; " + t)
        put("c03_fark_olan", e, "karşılaştırma", "bu karşılaştırmalardan fark çıkan; " + t)
        put("c03_mutasyon_yakalanan", int(mu.group(1)), "örneklem", "kasten hatalı yöntemin yakalandığı örneklem; " + t)
        put("c03_mutasyon_toplam", int(mu.group(2)), "örneklem", "mutasyon testi örneklem sayısı; " + t)
    else:
        print("UYARI: C03 ayrıntısı ayrıştırılamadı; c03_* metrikleri yazılmadı", file=sys.stderr)

    # ---- S5: takvim sıralaması ve mevcut ay (agg/ranking, agg/current_month)
    A = P / "agg"
    rk = pd.read_parquet(A / "ranking.parquet")
    rk = rk[(rk.birim == "TR") & (rk.seri == "modis_temiz") & (rk.top)].sort_values("sira")
    put("demo5_yildiz_aylar", [int(x) for x in rk.ay], "ay no", "ranking.parquet: TR, modis_temiz, ★ (top=True) aylar, sıra sırasıyla")
    put("demo5_yildiz_medyanlar", [int(x) for x in rk.medyan], "tespit", "aynı ayların tarihsel medyanı (tespit/ay)")
    put("demo5_ayirt_edilemez_aylar", [int(x) for x in rk[rk.ayirt_edilemez].ay], "ay no", "★ aylardan ayırt edilemez bayraklı olanlar (ekranda ≈)")
    cm = pd.read_parquet(A / "current_month.parquet")
    cm = cm[(cm.birim == "TR") & (cm.seri == "modis_temiz")]
    mv = cm[cm.hedef == "mevcut"].iloc[0]
    put("demo5_mevcut_bas", str(mv.bas), "TR günü", "current_month.parquet: mevcut ay başlangıcı")
    put("demo5_mevcut_bit", str(mv.bit), "TR günü", "mevcut ay bitişi (son veri günü)")
    put("demo5_mevcut_gun", int(mv.gun), "gün", "mevcut ayda veri günü (kısmi ay)")
    put("demo5_mevcut_deger", int(mv.deger), "tespit", "mevcut ay MODIS temiz değeri")
    put("demo5_mevcut_medyan", round(float(mv.tarihsel_medyan), 1), "tespit", "geçmiş yılların aynı ilk günlerinin medyanı")
    put("demo5_mevcut_oran", round(float(mv.oran), 3), "kat", "mevcut ay / tarihsel medyan")
    put("demo5_mevcut_viirs_oran", round(float(mv.viirs_olculen_oran), 3), "kat", "aynı oran VIIRS (uydu başına) için")
    st = cm[cm.hedef == "son_tam_ay"].iloc[0]
    put("demo5_son_tam_ay_bas", str(st.bas), "TR günü", "son tam ayın başlangıcı")
    put("demo5_son_tam_ay_deger", int(st.deger), "tespit", "son tam ay MODIS temiz değeri")
    put("demo5_son_tam_ay_medyan", round(float(st.tarihsel_medyan), 1), "tespit", "son tam ay tarihsel medyanı")
    put("demo5_son_tam_ay_oran", round(float(st.oran), 3), "kat", "son tam ay / tarihsel medyan")

    OUT.write_text(json.dumps({"metrics": M}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(M)} metrik -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
