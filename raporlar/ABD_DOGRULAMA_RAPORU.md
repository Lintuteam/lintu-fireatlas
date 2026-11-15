# ABD doğrulama raporu: yöntemimiz ikinci bir ülkede çalışıyor mu?

**Soru:** Türkiye için kurduğumuz veri hattı (temizlik → ortak kümeleme → MODIS-eşdeğer harmonizasyon) Türkiye'ye özgü bir ayar mı, yoksa başka bir ülkede de aynı sonucu veriyor mu?

**Kısa cevap:** Çalışıyor. ABD'de ham veri 2012'de **%319** sıçrıyor; gerçek MODIS aynı dönemde **%2,1** düşüyor. Bizim düzeltilmiş serimiz **%4,8** düşüş veriyor; gerçeğe **2,7 puan** yakın. Türkiye'de bu fark 3,5 puandı. Belgelenmiş 33 büyük ABD yangınının **32'si** uydu olayıyla eşleşti.

---

## 1. Veri

| | |
|---|---|
| Kaynak | NASA FIRMS ülke arşivi, ABD (`veri_abd/FIRMS_ABD_2009_2015.xlsx`) |
| Dönem | 2009–2015 (MODIS: Terra + Aqua; VIIRS: Suomi NPP, 20 Ocak 2012'den itibaren) |
| Satır | 2.722.345 tespit (hiçbiri silinmedi) |
| Etiketler | temiz 2.324.661 · statik kaynak 352.202 · açık deniz 27.427 · volkan 18.055 (NASA `type` alanı) |
| Dönüştürme | `veri_abd/xlsx_to_parquet.py` → `veri_abd/parquet/` |
| Hat | `kaynak_kod/abd/abd_hat.py` (≈ 78 sn) → `veri_abd/cikti/abd_metrics.json`, `arayuz/data_abd/abd_data.js` |

## 2. Sonuçlar ve Türkiye ile karşılaştırma

| Ölçü | Türkiye (2000–2026) | ABD (2009–2015) |
|---|---|---|
| Ham 2012 sıçraması (2009–11 → 2012–14) | +%143,1 | **+%318,6** |
| Gerçek MODIS, aynı dönem | −%44,9 | **−%2,1** |
| Kümeleme sonrası olay sıçraması | +%31 | +%66,1 |
| Bizim MODIS-eşdeğer seri | −%41,4 | **−%4,8** |
| Düzeltme − gerçek MODIS | 3,5 puan | **2,7 puan** |
| Yıllık LOYO hatası (MAPE) | %8,3 | **%4,2** |
| Ay × bölge R² | — | 0,87 |
| Ortak kümeleme olayı | 471.978 | 665.386 |
| Önlenen çift sayım | 59.201 | **159.341** |
| Belgelenmiş yangın doğrulaması | en büyük 20 olayın 16'sı | **33 yangının 32'si** |
| Seçilen yöntem (aynı ölçüt: en düşük ay × bölge WAPE) | tabakalı oran | sabit oran |

Okuma notları:
- **Sıçrama ABD'de Türkiye'dekinden de büyük.** VIIRS ABD'deki çok sayıdaki küçük tarım ve reçete yakma yangınını da görüyor.
- **Kümeleme tek başına yetmiyor, iki ülkede de.** Kümelemeden sonra olay sayısı yine +%66 sıçrıyor (Türkiye +%31). Bu yüzden VIIRS'i MODIS ölçeğine çeviren harmonizasyon adımı şart.
- **Yöntem seçimi kendi işini yaptı.** Aynı önceden yazılmış ölçüt Türkiye'de tabakalı oranı, ABD'de sabit oranı seçti. ABD'de MODIS–VIIRS çakışması yalnız 4 yıl (2012–2015). Tabakalı oran 3 yılla öğrenildiğinde yetersiz kalıyor: yıllık hatası %23,7, sabit oranınki %4,2.

**LOYO yıllık hataları (sabit oran):**

| 2012 | 2013 | 2014 | 2015 |
|---|---|---|---|
| −%0,3 | −%3,2 | −%5,8 | +%7,5 |

## 3. Belgelenmiş yangın doğrulaması

- **Liste:** 2009–2015 arası 33 büyük ABD yangını. Bir Sonnet alt ajanı web kaynaklarından (InciWeb, Wikipedia, NIFC, USFS ve diğerleri) derledi: `veri_abd/belgelenmis_yanginlar_abd.json`. Konumu yaklaşık olan 9 yangın dosyada işaretli.
- **Eşleştirme kuralı:** Yangın noktasının 40 km çevresinde, başlangıçtan 7 gün önce ile 14 gün sonra arasındaki tespitlerin çoğunu taşıyan olay.

**Güçlü eşleşmeler (o yılın en büyük 4 olayından biri):**

| Yangın | Yıl | Yıl içindeki sıra | Tespit |
|---|---|---|---|
| Rim | 2013 | 1 | 20.283 |
| Whitewater-Baldy | 2012 | 1 | 19.995 |
| Wallow | 2011 | 1 | 1.695 |
| Happy Camp | 2014 | 1 | 12.436 |
| Okanogan | 2015 | 2 | 13.570 |
| Carlton | 2014 | 2 | 6.361 |
| La Brea | 2009 | 2 | 1.136 |
| King | 2014 | 3 | — |
| Silver | 2013 | 3 | — |
| Rough | 2015 | 3 | — |
| Station | 2009 | 4 | — |
| Beaver Creek | 2013 | 4 | — |
| Funny River | 2014 | 4 | — |

**Zayıf eşleşmeler (eşleşen olay küçük ya da 30 km'den uzak):**
- Fourmile Canyon, Rock House, Pains Bay, Valley, Wood Hollow ve diğerleri.
- Bağımsız kontrol, Valley, Rock House, Wood Hollow ve Las Conchas'ın yangının parçalanmış küçük olaylarından birine bağlandığını gösterdi.

**Bulunamadı:** Pagami Creek (MN). Yangın ilk iki hafta çok küçük kaldı, ancak 12 Eylül'de büyüdü. Pencere bu tarihi kapsamıyor.

## 4. Bağımsız kontrol (Sonnet alt ajanı)

Ayrı bir Sonnet alt ajanı, hattın kodunu kullanmadan ham parquet dosyalarından yeniden hesap yaptı. Ayrıntılı rapor: `veri_abd/cikti/bagimsiz_kontrol_raporu.md`.

| Görev | Sonuç |
|---|---|
| Satır sayıları, etiketler, yıllık seriler, sıçramalar | **Tutarlı:** birebir aynı |
| Sabit oran LOYO hataları ve MAPE | **Tutarlı:** birebir aynı |
| Kümeleme | **Kısmen tutarlı:** basit 1 km / 72 sa kuralı %28 daha az olay buluyor. Çift sayım payı aynı büyüklükte (%27 vs %24). Hattın geçiş kuralı (3 gözlenmiş geçişten uzun boşluk olayı böler) daha sıkı. Kümeleme sonrası sıçramanın kalması iki yöntemde de görülüyor. |
| Belgelenmiş yangınlar | **Kısmen tutarlı.** Kontrol ilk koşudaki eşleştirmeyi denetledi. Whitewater-Baldy için bildirdiği hata, eşleştirme kuralı düzeltilince giderildi. Zayıf eşleşmeler uygulamada ayrıca işaretlendi. |
| Veri sağlığı | **Sorun yok:** tekrar satır, geçersiz koordinat veya zaman yok. 2.063 satırda FRP ≤ 0 (%0,08). |

## 5. Sınırlar

- **Temizlik yalnız NASA'nın kendi etiketiyle yapıldı.** Türkiye'deki sanayi, anız ve kalıcı ısı kuralları ABD için yeniden kalibre edilmedi.
- **Bölgeler kaba.** Eyalet sınırı yerine boylam/enlem kutuları kullanıldı (8 bölge, Alaska ve Hawaii dahil).
- **Kapsama hesabı basit.** Gözlem kapsamı, "o gün en az bir tespit veren uydu gözlemiş sayılır" diye alındı.
- **Çakışma dönemi kısa.** MODIS–VIIRS çakışması 4 yıl; LOYO sonuçları Türkiye'deki 14 yıllık sınamadan daha az kesin. 2012 kısmi bir VIIRS yılı (VIIRS 20 Ocak'ta başlıyor).
- **Arazi örtüsü katmanı ABD için kurulmadı.** Türkiye'deki ESA WorldCover / orman–tarım katmanı ABD'de yok.

## 6. Uygulamada nerede?

- Ana ekranın başlığında **Türkiye | ABD** düğmesi var.
- ABD sayfası (`arayuz/abd.html`) şunları gösteriyor:
  - özet kartları ve Türkiye–ABD karşılaştırma tablosu,
  - yıllık sıçrama grafiği,
  - yıl × ay takvimi,
  - olay haritası,
  - tıklanabilir doğrulama tablosu,
  - bölge ve kümeleme özeti.
- Canlı: https://lintuteam.github.io/lintu-fireatlas/arayuz/abd.html (telefonda da açılır). Kaynak kod: https://github.com/Lintuteam/lintu-fireatlas
- Yerelde çalıştırmak için: `BASLAT_ARAYUZ.bat`, sonra **ABD**.
