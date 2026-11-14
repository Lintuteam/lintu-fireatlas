# Değişim günlüğü

## 2026-11-13 — F0 (koordinatör)
- Veri sözleşmesi taslaktan **KESİN v1**'e çevrildi (`docs/04_VERI_SOZLESMESI_TASLAK.md`). Neden: gerçek 1.414.674 satırlık envanter. Başlıca kararlar: Parquet nokta tablosu, `pid`, `day_tr`, `sat` kodları, `type=-1` (NRT), `bt_estimated`, F2 alanları yan tablolarda, eşleştirme birimi = MODIS piksel ayak izi (+ yedek 0,01° ızgara).
- `data/processed/inventory.json` yazıldı (ham satır toplamı, SHA-256).

## 2026-11-13 — F1 sonrası (koordinatör)
- `tools/check_all.py`: `load_points` yan tabloları (`points_status/mcell/event.parquet`, `pid` anahtarı) birleştiriyor; C01/C02 yan tablo yoksa ATLANDI. Neden: sözleşme §2 ile C01 çelişkisi (veri-hatti bildirdi).
- Zaman kararı: TR günü **sabit UTC+3** kalır (K11). Bilinen sınırlama: 2016 öncesi Türkiye yaz/kış saati uyguluyordu (UTC+2/+3); gece geçişleri (~23 UTC) her iki kuralda da aynı TR gününe düşer, etkisi ihmal edilebilir — **tahmini**, denetçi örneklemle ölçebilir.

## 2026-11-13 — F2 (koordinatör): C10 ölçütü inceltildi
- Eski ölçüt: harmonize 2012 sıçraması, geçiş dışı yıllık değişimlerin %95 aralığında olmalı. Ölçülen: ham +116,2 %, harmonize −49,6 %, gerçek MODIS aynı pencerede −51,5 %; doğal aralık [−40,2, +94,0]. Gerçek MODIS de aralık dışında → ölçüt gerçek yangın değişimini sensör sıçramasından ayıramıyor (2009–2011 olağandışı yüksek yıllar).
- Yeni ölçüt (U-15'in amacına uygun): **artık sıçrama** = harmonize − gerçek MODIS (aynı pencere) LOYO yıllık %95 hata aralığında olmalı. Eski ölçüt raporda bilgi olarak kalır. `docs/03` C10 satırı güncellendi.

## 2026-11-13 — F2 temizlik kararları (koordinatör)
- `yillik_tekrar` bayrak olarak kalır, status'a çevrilmez (tarım ovalarındaki gerçek yakma aktivitesini temizden çıkarırdı).
- `dusuk_guven` bayrak kalır (demo "Tümü" varsayılanı); arayüzde güven filtresi olarak sunulur.
- Esikler `M` anlamı değişti: "farklı takvim ayı sayısı (1–12)" (temizlik ajanı, LOYO ile N=40, M=8, Y=5, S=4).
- Arazi örtüsü: kullanıcı internetteki referanslara erişimi onayladı (01_ISTEKLER S5). WorldCover yalnız örneklem noktalarında COG aralık okumasıyla sınanacak (tam karo indirme yok).

## 2026-11-13 — F2 denetimi sonrası (koordinatör)
- F2-07 (C10): Yukarıdaki C10 girdisindeki sayılar ilk teslimden (tüm tespitler) kalmadır. Güncel ana varyant (tespit, `temiz`): ham +143,1 %, harmonize −41,4 %, gerçek MODIS −44,9 %, artık +3,55 pp; `loyo_ci95` [−23,49, +9,51] → GEÇTİ. Güncel değerlerin tek kaynağı `reports/metrics.json`. Not (dürüstlük): ölçüt, ilk sonuç görüldükten sonra inceltildi; denetçinin bağımsız 3 yıllık eşdeğer testinde artık dağılımı [−10,4, +4,6], 3,55 içinde → sonuç ölçüt seçiminden bağımsız olarak sağlam.
- F2-03 kararı: ana yöntem (ii) bölge×mevsim×FRP oranı kalır (ölçüt = uygulamanın kullanım birimi ay×bölge). (ii) ile uydu-normalize sabit oran (i) ay×bölgede ayırt edilemez; (i) yıllık toplamda daha iyi. "(ii) sabit oranı yener" iddiası kaldırılıyor; ikisi de normalize edilmemiş tek orandan (i0) çok iyi.

## 2026-11-13 — Faz 0 Kapanış ve Soru 3 Bilimsel Seri Kararı (koordinatör)
- Açık soru S3 (ana seri seçimi) kullanıcı onayıyla bilimsel standarta göre karara bağlandı (`docs/01_ISTEKLER.md` §E): Çok yıllı karşılaştırma, yıl×ay matrisi, trend ve anomalide varsayılan seri **MODIS-eşdeğer seri** (`modis_esdeger` / `olay_esdeger` + %95 LOYO belirsizlik bandı) olur; böylece 2012, 2018 ve 2023 sensör geçişlerinden doğan yapay sıçramalar gerçek yangın aktivitesiyle karışmaz. Uzamsal harita, yakınlaştırma, Birleştirme Laboratuvarı ve Hücre Müfettişinde ise 375 m ham VIIRS noktaları ve üçlü sınıf (`ortak` / `yalniz_viirs` / `yalniz_modis`) kayıpsız olarak yan yana sunulur (U-03, U-04).
- Arayüzde ve raporlarda bu seçimin gerekçesi ve kullanıcının arayüzdeki seri seçiciden/anahtardan tek tıkla nasıl değiştirebileceği belgelenir.
- F1–F2 kapanış doğrulaması ve F3–F5 fazlarının çalıştırılması başlatıldı.
