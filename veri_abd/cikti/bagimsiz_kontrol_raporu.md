# Bağımsız Kontrol Raporu (ABD FIRMS 2009–2015)

Yöntem: Ham parquet dosyalarından (firms_abd_2009..2015) kendi kodumla yeniden hesaplandı; boru hattı kodu (abd_hat.py) yalnızca tanımları anlamak için okundu, kullanılmadı. Yardımcı betikler: `veri_abd\cikti\bagimsiz_kontrol\` (k1_sayilar.py, k3_kume.py, k3b_duyarlilik.py, k4_yanginlar.py, k4b_olay_adaylari.py, k5_frp.py; çıktılar kume_sonuc_*.csv, yangin_sonuc.csv).

## Özet hüküm

| Görev | Hüküm |
|---|---|
| 1. Satır/durum/yıllık/sıçrama | **Tutarlı** (hepsi birebir) |
| 2. Sabit oran LOYO hataları, MAPE | **Tutarlı** (birebir) |
| 3. Kümeleme makullüğü | **Kısmen tutarlı** (büyüklük mertebesi ve çift sayım payı uyumlu; boru hattı yıl başına %22–31 daha fazla olay üretiyor; olay sıçraması boru hattında %66, bende %49) |
| 4. Belgelenmiş yangın kontrolü | **Kısmen tutarlı** (31 eşleşmenin 16'sı ham sayımla ±%25 uyumlu; 2 yanlış-negatif, en az 1 olası yanlış eşleşme, birkaç parçalanma kaynaklı küçük eşleşme) |
| 5. Veri sağlığı | Ciddi sorun yok; 2063 satırda FRP ≤ 0 (1 satır negatif) |

## Görev 1: Sayımlar ve sıçramalar

| Büyüklük | Boru hattı | Benim | Fark |
|---|---|---|---|
| satir_kaynak / satir_analiz | 2 722 345 / 2 722 345 | 2 722 345 / 2 722 345 | 0 |
| Pasifik dışarıda (lon > -60) | 0 | 0 | 0 |
| temiz (type 0) | 2 324 661 | 2 324 661 | 0 |
| statik_nasa (2) | 352 202 | 352 202 | 0 |
| deniz (3) | 27 427 | 27 427 | 0 |
| volkan (1) | 18 055 | 18 055 | 0 |
| yil_sensor (tüm tipler) MODIS 2009..2015 | 115174, 98322, 123867, 137295, 102348, 98871, 146984 | aynı | 0 |
| yil_sensor VIIRS 2012..2015 | 536477, 404761, 377204, 581042 | aynı | 0 |

Yıllık temiz seri:

| Yıl | modis (boru/benim) | viirs (boru/benim) | ham (boru/benim) |
|---|---|---|---|
| 2009 | 112655 / 112655 | 0 / 0 | 112655 / 112655 |
| 2010 | 94062 / 94062 | 0 / 0 | 94062 / 94062 |
| 2011 | 119959 / 119959 | 0 / 0 | 119959 / 119959 |
| 2012 | 131606 / 131606 | 439689 / 439689 | 571295 / 571295 |
| 2013 | 95938 / 95938 | 313027 / 313027 | 408965 / 408965 |
| 2014 | 92394 / 92394 | 294820 / 294820 | 387214 / 387214 |
| 2015 | 139536 / 139536 | 490975 / 490975 | 630511 / 630511 |

| Sıçrama | Boru hattı | Benim | Fark |
|---|---|---|---|
| ham_pct | 318.6 | 318.60 | 0.00 |
| modis_gercek_pct | -2.06 | -2.063 | 0.00 |
| esdeger_pct | -4.78 | -4.777 | 0.00 |
| esdeger_eksi_modis_pct | -2.72 | -2.714 | 0.00 |

(olay_ortak_pct Görev 3'te.)

## Görev 2: Sabit oran, LOYO

Oran r = (diğer üç yılın MODIS toplamı) / (aynı yılların VIIRS toplamı); tahmin = r × VIIRS(y).

| Yıl | Tahmin (benim) | Hata % boru | Hata % benim | Fark |
|---|---|---|---|---|
| 2012 | 131195.0 | -0.31 | -0.312 | 0.00 |
| 2013 | 92858.5 | -3.21 | -3.210 | 0.00 |
| 2014 | 87017.2 | -5.82 | -5.819 | 0.00 |
| 2015 | 149953.4 | 7.47 | 7.466 | 0.00 |
| MAPE | | 4.20 | 4.202 | 0.00 |

Eşdeğer serideki yıllık değerler metrikteki `yillik.esdeger` ile birebir aynı. Not: ay_bolge/ay_ulke WAPE ve R² değerleri bu kontrolde yeniden hesaplanmadı.

Metodolojik not: Yalnızca 4 test yılı ve tek parametre var; 2009–2011 için VIIRS olmadığından oranın geriye doğru geçerliliği test edilemez, eşdeğer serinin o yıllar için "gerçek MODIS" kalması bu yüzden karşılaştırmaya girmiyor.

## Görev 3: Kümeleme makullüğü

Kendi kuralım: temiz noktalar, eşdikdörtgen km metriği (x = R·λ·cos φ, y = R·φ), mesafe ≤ 1 km, |Δt| ≤ 72 saat, bağlı bileşenler. Her yıl ayrı çalıştırıldı (yıl sınırında bölünen olaylar küçük bir şişirme yapar). "Ayrı" = MODIS ve VIIRS ayrı kümelenip toplanır. Boru hattı olayları t0 yılına göre sayıldı.

| Yıl | Temiz nokta | Olay ortak (benim) | Olay ortak (boru) | Benim/boru | Ayrı (benim) | Çift sayım payı (benim) |
|---|---|---|---|---|---|---|
| 2009 | 112655 | 50653 | 65020 | 0.78 | 50653 | %0 |
| 2010 | 94062 | 52216 | 67046 | 0.78 | 52216 | %0 |
| 2011 | 119959 | 56384 | 73949 | 0.76 | 56384 | %0 |
| 2012 | 571295 | 84003 | 120959 | 0.69 | 116569 | %38.8 |
| 2013 | 408965 | 75025 | 108083 | 0.69 | 103931 | %38.5 |
| 2014 | 387214 | 77667 | 113179 | 0.69 | 109930 | %41.5 |
| 2015 | 630511 | 80244 | 117150 | 0.69 | 114395 | %42.6 |
| Toplam | 2324661 | 476192 | 665386 | 0.72 | 604078 | %26.9 |

| Büyüklük | Boru hattı | Benim | Yorum |
|---|---|---|---|
| Toplam çift sayım payı (ayrı−ortak)/ortak | 159341/665386 = %23.9 | %26.9 | Aynı mertebe |
| Yalnız 2012–2015 payı | ≈ %34.7 (159341/459371; 2009–11'de çift sayım 0 varsayımıyla) | %40.3 | Aynı mertebe, benimki biraz yüksek |
| Olay sıçraması (2012–14 ort. vs 2009–11 ort.) | +%66.11 | +%48.6 | Aynı yön, 17.5 puan fark |

Yorum:
- Boru hattı her yıl benden daha fazla olay üretiyor: tek sensörlü 2009–11'de %22–24, VIIRS yıllarında %31 fazla. Tek sensörlü yıllarda ortak = ayrı olduğundan fark yalnızca mekânsal/zamansal kural farkından geliyor. Duyarlılık testi: mesafe eşiğini 0.7 km yapınca 2009'da 65080 olay çıkıyor (boru hattı 65020). Boru hattının fiilî bağlama kuralı benim 1 km kuralımdan daha sıkı çalışıyor olabilir (geçiş/gözlem kapsamı koşulları); bu yalnızca tutarlı bir hipotez, kural kodu ayrıntılı incelenmedi.
- Benim kuralımda zaman eşiği (72/24/12 saat) sonucu değiştirmedi: 1 km içindeki çiftlerin neredeyse hepsi aynı geçişten. Boru hattının zaman/geçiş kuralı bu yüzden farklı bir olay tanımı üretiyor.
- Çift sayım iki yöntemde de büyük (VIIRS yıllarında %24–43): MODIS (1 km) ve VIIRS (375 m) pikselleri aynı yangını ayrı kümeler olarak sayıyor. Ortak kümelemeden sonra bile olay sıçraması boru hattında +%66, bende +%49; ham tespitin +%319'una göre çok düşük, fakat sıfır değil. Yani olay bazlı ölçüm sensör kaynaklı sıçramayı tam gidermiyor; metin buna göre yazılmalı. Eşdeğer yöntem (-%4.78) bu bakımdan olay sayımından daha tutarlı.

## Görev 4: Belgelenmiş yangınlar

Ham sayım: temiz tespit, koordinata ≤ 40 km (haversine) ve [başlangıç−3 gün, başlangıç+30 gün]. Boru hattı: `dogrulama.liste.tespit`; olay konumu/boyutu events.parquet'ten event_id ile doğrulandı (tespit = n ve uzaklık_km birebir tutuyor).

| Yangın | Ham 40 km | Boru olay tespit | Oran | Uzaklık km | Değerlendirme |
|---|---|---|---|---|---|
| Station | 1368 | 744 | 0.54 | 12.0 | kısmen (parçalanma) |
| La Brea | 1198 | 1136 | 0.95 | 4.4 | iyi |
| Jesusita | 118 | 107 | 0.91 | 3.2 | iyi |
| Schultz | 151 | 45 | 0.30 | 9.5 | küçük, parçalanmış |
| Fourmile Canyon | 64 | 28 | 0.44 | 1.3 | kısmen |
| Bull | 83 | 41 | 0.49 | 9.9 | kısmen |
| Wallow | 3395 | 1695 | 0.50 | 22.4 | kısmen |
| Las Conchas | 1447 | 243 | 0.17 | 25.1 | şüpheli: 7–8 km'de ve başlangıç gününde 147 ve 228 tespitlik olaylar var, seçilen olay 4 gün sonra başlıyor |
| Bastrop County | 226 | 128 | 0.57 | 2.2 | kısmen |
| Rock House | 150 | 10 | 0.07 | 22.7 | şüpheli: 10 tespitlik, 11 saatlik olay; 150 ham tespit çok sayıda küçük olaya bölünmüş (en büyüğü 10) |
| Honey Prairie | 650 | 157 | 0.24 | 19.2 | parçalanmış (komşu olaylar 84, 37, 26) |
| Pagami Creek | 296 | yok | | | yanlış negatif: 7.9 km'de 244 tespitlik olay var, ancak t0 = 2011-09-07 (belgelenmiş başlangıçtan 20 gün sonra) |
| Pains Bay | 153 | 29 | 0.19 | 11.8 | parçalanmış |
| Whitewater-Baldy | 20017 | yok | | | **yanlış negatif**: event_id 254032, 19995 tespit, merkez 0.1 km, t0 = 2012-05-11 (belgelenmiş başlangıçtan 5 gün ÖNCE, eşleştirme penceresi dışında). Ham sayımla neredeyse birebir (20017) |
| High Park | 3462 | 3031 | 0.88 | 5.5 | iyi |
| Long Draw | 4250 | 1805 | 0.42 | 18.0 | kısmen |
| Waldo Canyon | 624 | 580 | 0.93 | 7.5 | iyi |
| Rush | 4948 | 2713 | 0.55 | 10.2 | kısmen |
| Ash Creek | 3710 | 4940 | 1.33 | 27.7 | makul (koordinat belgede "yaklaşık"; olay 40 km/pencere dışını da içeriyor) |
| Wood Hollow | 2482 | 2608 | 1.05 | 38.1 | **olası yanlış eşleşme**: seçilen olay (268117) koordinatın yaklaşık 38 km doğusunda (39.55, -111.13); 6 km'de, 1 gün sonra başlayan 560 tespitlik olay (267406) var. Seçilen olay aynı bölgedeki başka bir yangın olabilir; dış kaynakla teyit edilmedi |
| Rim | 20656 | 20283 | 0.98 | 16.2 | iyi |
| Black Forest | 454 | 454 | 1.00 | 6.8 | iyi |
| Yarnell Hill | 199 | 174 | 0.87 | 4.1 | iyi |
| Silver | 6534 | 6451 | 0.99 | 11.9 | iyi |
| Beaver Creek | 6764 | 5095 | 0.75 | 11.4 | iyi |
| Carlton Complex | 8251 | 6361 | 0.77 | 9.7 | iyi |
| King | 5488 | 4808 | 0.88 | 14.1 | iyi |
| Funny River | 4416 | 4300 | 0.97 | 12.9 | iyi |
| Happy Camp | 11996 | 12436 | 1.04 | 17.9 | iyi |
| Okanogan | 13851 | 13570 | 0.98 | 11.0 | iyi |
| Valley | 226 | 45 | 0.20 | 27.2 | **şüpheli**: olay 4.2 saatlik ve başlangıçtan 4 gün sonra; 2 gün önce başlayan iki ayrı 43 tespitlik olay var; 226 ham tespit hiçbiri 45'i geçmeyen küçük olaylara bölünmüş |
| Rough | 6246 | 12549 | 2.01 | 3.3 | olay 43 gün sürüyor, 30 günlük pencerenin dışını içeriyor; kabul edilebilir |
| Soda | 2639 | 2794 | 1.06 | 27.4 | iyi |

Özet: boru hattı uzaklık_km ve tespit değerleri events.parquet ile birebir uyuşuyor (veri bütünlüğü tamam). 31 eşleşmede boru/ham oranı medyan 0.87, ortalama 0.74; 16'sı 0.75–1.25 arasında, 10'u < 0.5. Küçük oranların başlıca nedeni, yangının tek olay yerine birçok küçük olaya parçalanması (özellikle MODIS-only 2009–2011). Bu nedenle olay sayısı yangın sayısı olarak okunmamalı.

Eşleştirme sorunları:
- Pencere kuralı belgelenmiş başlangıçtan önce başlayan olayları (Whitewater-Baldy, -5 gün) ve çok sonra patlayan olayları (Pagami Creek, +20 gün) dışlıyor; bunlar yanlış negatif.
- Las Conchas, Wood Hollow ve Valley'de daha yakın/daha erken olaylar varken uzaktaki daha geç/büyük olay seçilmiş görünüyor; bu, olay adaylarının incelenmesinden çıkarılmış bir izlenim, kaynak kod ayrıntılı okunmadı.
- Rock House, Valley, Las Conchas, Pains Bay'de eşleşen olay ham tespitlerin yalnızca %7–20'sini içeriyor.

## Görev 5: Veri sağlığı

| Kontrol | Sonuç |
|---|---|
| Tam yinelenen satır (zaman, enlem, boylam, sensör, uydu) | 0 |
| Enlem aralığı | 18.97 – 71.33 |
| Boylam aralığı | -178.81 – -66.98; lon > -60 ve lon > 0 satır yok (Pasifik filtresi etkisiz, Guam vb. veri setinde yok) |
| NaN enlem/boylam/zaman | 0 |
| Zaman aralığı | 2009-01-01 04:20Z – 2015-12-31 21:06Z (dışında 0) |
| FRP ≤ 0 | 2063 satır (%0.076): 2062 satır tam 0.0, 1 satır -59.2 (MODIS). Temiz sette 1978 satır (MODIS 517, VIIRS 1461) boru hattına dahil. FRP toplamlarına etkisi çok küçük |
| Sensör-uydu uyumu | MODIS: Terra 384 683, Aqua 438 178; VIIRS: yalnız Suomi NPP 1 899 484; uyumsuzluk 0 |
| VIIRS ilk tarihi | 2012-01-20 (2012 VIIRS yılı kısmi; sabit oran modelinde 2012 de eğitim/test yılı olarak tam yıl gibi kullanılıyor, bu 2012 oranını biraz yukarı çeker) |
| scan/track | MODIS 1.0–4.8 / 1.0–2.0 km; VIIRS 0.32–0.8 / 0.36–0.78 km (makul) |
| type dağılımı | MODIS: 786 150 temiz, 35 762 statik, 350 volkan, 599 deniz; VIIRS: 1 538 511 temiz, 316 440 statik, 17 705 volkan, 26 828 deniz |

## Bulunan sorunlar (kısa liste)

1. Whitewater-Baldy yanlış negatif: 19 995 tespitlik olay (254032) var, ancak başlangıçtan 5 gün önce başladığı için "bulunamadı" (dogrulama.eslesen 31/33, olması gereken en az 32/33).
2. Pagami Creek: 7.9 km'de 244 tespitlik olay var, 20 gün sonra başladığı için eşleşmedi.
3. Olası yanlış/zayıf eşleşmeler: Wood Hollow (38 km uzaktaki olay), Valley (45/226), Rock House (10/150), Las Conchas (243/1447).
4. Olay sayıları kurala duyarlı: benim 1 km/72 sa kuralım %22–31 daha az olay veriyor; olay sıçraması bende +%49, boru hattında +%66. Çift sayım iki yöntemde de %24–43; olay bazlı ölçüm sensör kaynaklı sıçramayı tam gidermiyor.
5. FRP ≤ 0: 2063 satır (1 negatif).
6. VIIRS 2012-01-20'de başlıyor; 2012 kısmi yıl olmasına rağmen LOYO'da tam yıl olarak kullanılıyor.
