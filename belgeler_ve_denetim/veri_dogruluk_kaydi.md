# Veri doğruluk kaydı (salt-okunur denetim)

Tarih: 2026-11-14. Kapsam: `_yedek_v2.3_revize_oncesi` (sabah yedeği) ile `arayuz` (güncel) karşılaştırması. **Hiçbir mevcut dosya değiştirilmedi**; hesaplar bağımsız betiklerle `.bin` dosyalarından yapıldı (yalnız numpy/pandas, uygulama kodu çalıştırılmadı; kurallar core.js'ten okunup yeniden yazıldı).

## Sonuç özeti

- `data/` içinde 151 ortak dosyadan **150'si bayt bayt aynı** (SHA-256), **1'i değişmiş** (`gercek_dogrulama.json`), **28 yeni** dosya (`arazi_2000..2026.bin` + `arazi_manifest.json`), silinen dosya yok.
- **Hiçbir ölçüm/sayım değişmedi.** events_*.bin, points_*.bin, cal_*.json, metrics.json, harmonized.json, coverage.json, manifest.json, il.geojson, lab_examples.json, pixel_growth.json aynıdır. `gercek_dogrulama.json` içindeki 60 sayısal değerin 60'ı da aynıdır; fark yalnız kaynak/etiket metnidir.
- Belgelerdeki ana sayıların hepsi `.bin` dosyalarından bağımsız olarak yeniden üretildi (uyumsuzluk yok).
- "Veri çok kaydı" hissinin nedeni veri değil **ekran mantığındaki değişikliklerdir** (3. bölüm): en büyük 10 listesinin ölçütü, filtreli kipte anomali medyanı, 🔥 işareti, orman sınıfı.

## 1. Dosya bütünlüğü (SHA-256)

- Aynı: **150** dosya (events_*.bin 27, points_*.bin 27, cal_*.json 89, manifest.json, metrics.json, harmonized.json, coverage.json, il.geojson, lab_examples.json, pixel_growth.json).
- Değişen: `gercek_dogrulama.json`
- Yeni: 27 adet `arazi_<yıl>.bin` + `arazi_manifest.json`
- Silinen: yok

| Dosya | Yedek SHA-256 | Güncel SHA-256 |
|---|---|---|
| gercek_dogrulama.json | `02b4a44a55ecceca…` | `2b27731f52f7ae11…` |
| manifest.json | `d9511527b3f01dea…` | `d9511527b3f01dea…` |
| metrics.json | `8dd2a4ba3853142a…` | `8dd2a4ba3853142a…` |
| harmonized.json | `4011bd923e0fb735…` | `4011bd923e0fb735…` |
| coverage.json | `f3574c45b74c10a2…` | `f3574c45b74c10a2…` |
| events_2026.bin | `58b8e9b5b4b3ee37…` | `58b8e9b5b4b3ee37…` |
| points_2026.bin | `b47b147937c43c12…` | `b47b147937c43c12…` |
| cal_0.json | `a593569f641820e9…` | `a593569f641820e9…` |

Tam liste (tüm dosyaların tam hash'leri) .json kaydındadır.

### gercek_dogrulama.json farkı (sayısal içerik)

- Toplam 159 fark: {'metin': 35, 'eklendi': 109, 'uzunluk': 15}. Sayısal türde fark (`sayi`/`tip`): **0**. Tüm sayısal alanlar (60 adet) eşit.
- Eklenen alanlar (20 olayın her birinde): `kaynak_durumu`, `kaynak_turu`, `resmi_kaynaklar`, `ikincil_kaynaklar`, `ikincil_kaynak_etiketi`. Değişen: 14 olayda `kaynaklar` listesi uzadı; `genel` ve `yontem_notu` metinleri değişti.
- Sonuç: yalnız kaynak/atıf metni; eşleşme sayıları, FRP, tarih vb. ölçümler değişmedi.

## 2. Çekirdek sayılar (bin'lerden bağımsız hesap)

| Büyüklük | Belge değeri | Bağımsız hesap | metrics.json | Durum |
|---|---|---|---|---|
| Ham tespit (points toplamı) / veri_toplam_nokta | 1.414.674 | 1.414.674 | 1.414.674 | UYUMLU |
| MODIS nokta / veri_modis_nokta | 259.707 | 259.707 | 259.707 | UYUMLU |
| VIIRS nokta / veri_viirs_nokta | 1.154.967 | 1.154.967 | 1.154.967 | UYUMLU |
| Temizlenmiş (temiz+anız nokta) / huni_kumeleme_girdi | 1.044.222 | 1.044.222 | 1.044.222 | UYUMLU |
| Toplam olay (events_*.bin) / events_total | 471.978 | 471.978 | 471.978 | UYUMLU |
| Varsayılan süzgeç olay (st=temiz) / perf_olay_sayisi | 302.863 | 302.863 | 302.863 | UYUMLU |
| Olaylardaki toplam tespit (n_modis+n_viirs) = temizlenmiş girdi | 1.044.222 | 1.044.222 | 1.044.222 | UYUMLU |
| Çift sayım önlenen / events_double_count_avoided | 59.201 | binlerden hesaplanamaz (bkz. not) | 59.201 | UYUMLU |

Not: 59.201 çift sayım, birleşik ve ayrı kümeleme farkıdır (metrics: events_separate_overlap 440.176 − events_joint_overlap 380.975 = 59.201 ✔); bin'den yeniden üretilemez, yalnız metrics.json ile belgeyle tutarlılığı doğrulandı. Olay durumları: temiz 302.863, anız 169.115 (events dosyasında yalnız bu ikisi vardır).
Nokta durumları (points): temiz 827.043, deniz 8.848, volkan 5, statik_nasa 328.379, sanayi 27.012, aniz 217.179, kalici_belirsiz 6.208 (metrics temizlik_status_* ile eşit). Sensörler: Terra 136.626, Aqua 123.081, SNPP 637.595, N20 360.942, N21 156.430.

**Şanlıurfa:** tüm olaylarda 67.937 (%14.39); temiz olaylarda 46.490 (%15.35, belgedeki %15,4 ile uyumlu). Tekrarlayan yakma çıkarılınca Şanlıurfa temiz payı %5.04 (belge: %5 ✔).
En çok olay (tümü): Şanlıurfa 67.937, Adana 35.203, Mardin 34.291, Konya 33.085, Diyarbakır 32.658.

### Yıllara göre olay / durum / tespit

| Yıl | Olay | Temiz | Anız | Tespit (n_modis+n_viirs) | Nokta (points) |
|---|---|---|---|---|---|
| 2000 | 438 | 86 | 352 | 481 | 496 |
| 2001 | 4.361 | 2.689 | 1.672 | 5.055 | 5.162 |
| 2002 | 5.628 | 3.386 | 2.242 | 6.722 | 6.886 |
| 2003 | 6.290 | 3.919 | 2.371 | 7.501 | 7.733 |
| 2004 | 6.561 | 3.902 | 2.659 | 7.708 | 7.901 |
| 2005 | 6.868 | 4.169 | 2.699 | 8.075 | 8.303 |
| 2006 | 7.649 | 4.923 | 2.726 | 9.228 | 9.459 |
| 2007 | 7.087 | 4.689 | 2.398 | 8.544 | 8.791 |
| 2008 | 4.728 | 2.916 | 1.812 | 5.896 | 6.164 |
| 2009 | 15.574 | 9.903 | 5.671 | 19.710 | 19.979 |
| 2010 | 11.091 | 7.001 | 4.090 | 13.421 | 13.653 |
| 2011 | 14.684 | 8.786 | 5.898 | 18.206 | 18.465 |
| 2012 | 15.385 | 10.524 | 4.861 | 31.150 | 42.566 |
| 2013 | 23.579 | 13.855 | 9.724 | 50.483 | 63.610 |
| 2014 | 13.898 | 9.228 | 4.670 | 27.947 | 40.111 |
| 2015 | 30.614 | 18.721 | 11.893 | 73.228 | 84.887 |
| 2016 | 26.784 | 16.434 | 10.350 | 59.131 | 71.162 |
| 2017 | 19.255 | 12.143 | 7.112 | 39.649 | 53.291 |
| 2018 | 23.285 | 14.239 | 9.046 | 55.867 | 80.108 |
| 2019 | 27.719 | 16.821 | 10.898 | 62.784 | 88.538 |
| 2020 | 28.315 | 18.174 | 10.141 | 68.968 | 96.900 |
| 2021 | 20.771 | 13.342 | 7.429 | 66.324 | 98.065 |
| 2022 | 17.982 | 11.847 | 6.135 | 35.621 | 61.504 |
| 2023 | 34.974 | 24.487 | 10.487 | 86.856 | 122.190 |
| 2024 | 42.195 | 27.462 | 14.733 | 118.080 | 160.343 |
| 2025 | 29.700 | 21.503 | 8.197 | 84.187 | 128.485 |
| 2026 | 26.563 | 17.714 | 8.849 | 73.400 | 109.922 |

## 3. Ekranda değişen sayılar ve nedeni (mantık değişikliği, veri değil)

| Ekran öğesi | Eski | Yeni | Neden |
|---|---|---|---|
| Takvim anomalisi, Ekim 2026, "tekrarlayan yakmaları çıkar" açık (tarayıcı kipi) | +%417.5 (2026: 1.555, tüm yılların medyanı 300.5) | +%107.9 (aynı değer, medyan 748) | Normal (medyan) artık aynı uydu döneminden: 2012+ (MODIS+VIIRS). Eski kural 2001–2011 tek-MODIS yıllarını da medyana kattığı için normal düşüktü (2001–2011 medyanı 90); 2012'de VIIRS eklenince sayılar sıçradığından yeni aylar sahte +%400 görünüyordu. Ekim 2026 sayısı değişmedi (1.555). |
| Aynı, ek filtre olmadan ama ölçülen (tarayıcı) kipinde | +%185.7 | +%74.9 | Aynı neden. Medyan 1334.5 → 2179. Varsayılan süzgeçte hazır cal_*.json (agg) kipi kullanılır ve değişmedi. |
| Orman yangını adayı sayısı (tüm olaylar) | 2.063 | 24.830 (temiz: 17.000) | Eski kural (tahmin): ≥12 saat veya FRP toplamı ≥200 MW, ≥5 tespit ve aynı 0,01° karede başka yıl olay yok. Yeni kural: arazi örtüsü (WorldCover 2021, ±250 m) ağaç+çalı payı ≥%30, OSM sanayi yok, yapılaşmış değil. İki kümenin kesişimi yalnız 612. Bu bir **sınıflandırma ölçütü** değişikliğidir; olaylar aynı. |
| "Tekrarlayan yakmaları çıkar" | – | temiz olayların %69.8'i çıkar (211.413); kalan 91.450 | Kural değişmedi (aynı ~0,01° karede ≥3 farklı yıl). BENI_OKU'daki %70 ile uyumlu. |
| Takvim 🔥 işareti | FRP toplamı ölçütlü (ay/gün) | Tepe FRP'si (frp_max) en yüksek olay | frp_sum uydu sayısına (VIIRS sonrası) çok bağlı; frp_max (en yüksek tek tespit, MW) daha az bağımlı. Veri aynı, işaretin konumu değişebilir. |
| En büyük 10 listesi | FRP toplamına göre | Tepe FRP'ye göre; tek tespitli olaylar hariç (FRP toplamına geçiş düğmesi var) | Aşağıdaki iki liste. Tek tespitli olay tek pikseldir ve doğrulanamaz. |

### En büyük 10 (temiz, tüm tarihler, tüm sensörler)

Eski (FRP toplamı, MW):

| # | İl | Tarih | Tespit | FRP toplam | FRP max |
|---|---|---|---|---|---|
| 1 | Antalya | 2021-07-28 | 6.740 | 384.683 | 4.856 |
| 2 | Muğla | 2021-07-31 | 2.123 | 103.176 | 2.355 |
| 3 | Antalya | 2021-07-29 | 2.336 | 75.470 | 2.366 |
| 4 | Bilecik | 2025-07-20 | 1.032 | 75.410 | 3.021 |
| 5 | İzmir | 2025-06-28 | 996 | 73.305 | 1.289 |
| 6 | Muğla | 2021-08-02 | 2.318 | 68.286 | 2.188 |
| 7 | Çanakkale | 2025-07-15 | 825 | 65.550 | 2.559 |
| 8 | Bilecik | 2025-06-27 | 1.255 | 63.733 | 3.248 |
| 9 | İzmir | 2025-07-02 | 1.208 | 57.830 | 687 |
| 10 | Muğla | 2026-07-29 | 561 | 45.041 | 2.639 |

Yeni (tepe FRP, MW; ≥2 tespit):

| # | İl | Tarih | Tespit | FRP max | FRP toplam |
|---|---|---|---|---|---|
| 1 | Antalya | 2021-07-28 | 6.740 | 4.856 | 384.683 |
| 2 | Antalya | 2026-09-07 | 629 | 4.808 | 29.895 |
| 3 | Çanakkale | 2023-08-22 | 344 | 3.773 | 20.991 |
| 4 | Çanakkale | 2008-07-30 | 4 | 3.336 | 4.488 |
| 5 | Bilecik | 2025-06-27 | 1.255 | 3.248 | 63.733 |
| 6 | Çanakkale | 2013-07-28 | 29 | 3.123 | 6.353 |
| 7 | Bilecik | 2025-07-20 | 1.032 | 3.021 | 75.410 |
| 8 | İzmir | 2020-08-13 | 226 | 2.788 | 11.247 |
| 9 | Muğla | 2006-08-21 | 49 | 2.733 | 13.320 |
| 10 | Muğla | 2026-07-29 | 561 | 2.639 | 45.041 |

Dışlanan tek tespitli olay: eşiğin üstünde 1 adet (Ağrı, 2010-08-24, 3.058 MW). Antalya 2021-07-28 iki listede de 1. sıradadır; Muğla 2026-07-29 ikisinde de var. Değişen yalnız sıralama ölçütüdür.

## 4. Mantık sağlamaları

| Kontrol | Sonuç |
|---|---|
| NaN/Inf (olay float sütunları; nokta float sütunları) | 0 / 0 |
| Negatif değer (olay tüm sütunlar tmin hariç; nokta frp/scan/track) | 0 sütun |
| Enlem 35.823–42.079, boylam 25.697–44.794; kutu 35,5–42,5 / 25,5–45,0 dışı | olay 0, nokta 0 |
| Tarih aralığı (TR günü) | olay 2000-11-01 … 2026-11-12; 2000-11-01..2026-11-12 dışı: 0 (nokta: 0) |
| Yıl başına olay > 0 | 27 yılın tümü > 0 (sıfır olan yıl: 0) |
| 2012 öncesi VIIRS | n_viirs>0 olay 2000–2011: 0; ilk VIIRS olay günü 2012-01-20 (nokta: 2012-01-20); 2012-01-20 öncesi VIIRS olay/nokta: 0/0 |
| 2000–2011 olaylarında n_modis==0 | 0 |
| n_modis=0 ve n_viirs=0 olay | 0 |
| il indeksi geçersiz | 0 |

Notlar ve sınırlar: (1) Veri bir koordinat kutusudur, ülke sınırı değil (bulgular.md F1); kutu kontrolü bunu doğrular, ülke içi olmayı değil. (2) Kutu sınırları bu denetimde varsayılmıştır (TR + pay). (3) 3. bölümdeki "eski" değerler yedek core.js kurallarının yeniden yazımıdır; Ekim 2026 +%417,5 kullanıcının bildirdiği +%417 ile örtüşür, bu yeniden yazımın doğruluğunu destekler. (4) Tarayıcıda gerçek ekran okuması yapılmadı.

## Yeniden üretme

Betikler: `scratchpad/audit/integ.py`, `core.py`, `rapor.py` (salt okunur; yalnız bu kayıt dosyalarını yazar).


## v2.5.2 — isteğe bağlı il bazlı anız ve sanayi artığı bayrakları

Tarih: 2026-11-14. Etiket: tüm sayılar "ölçüldü" (yeni bin dosyalarından ve olay dosyalarından sayım); kuralların doğruluğu "doğrulanmadı" (tahmin, il_bazli_aniz_analizi.md ve sanayi_denetimi.md).

**Ne eklendi.** İki isteğe bağlı bayrak, ikisi de varsayılan KAPALI. (1) `arayuz/data/aniz_il_<yıl>.bin`: il bazlı anız eşiği (varyant T, il temiz medyanı, ulusal taban, 1,5x tavan, <300 nokta için bölge/ulusal); `kaynak_kod/src/aniz_il/aniz_il_uret.py` üretir. (2) `arayuz/data/sanayi_artik_<yıl>.bin`: OSM sanayi sahası artıkları; `kaynak_kod/src/sanayi/sanayi_artik_uret.py` üretir (rapordaki kural + belgelenmiş yangın penceresi ve olay_id muafiyeti: 40 km, başlangıç−2…+35 gün). Her bin: olay sırasıyla uint8 (1 = bayrak). Eşik tablosu ve yıl sayıları `aniz_il_manifest.json` ve `sanayi_artik_manifest.json` içinde. Mevcut hiçbir veri dosyası değiştirilmedi.

### Varsayılan durumda hiçbir şey değişmedi

| Büyüklük | Değer | Kaynak |
|---|---|---|
| Ham nokta (veri_toplam_nokta) | 1.414.674 | metrics.json (bayt aynı) |
| Temizlenmiş/kümelemeye giren nokta | 1.044.222 | metrics.json |
| Olay | 471.978 | events bin toplamı = metrics |
| Temiz olay (st=0) | 302.863 | events bin |
| Anız olay (st=6) | 169.115 | events bin = metrics.temizlik_olay_aniz_olay |

Dosya bütünlüğü: `arayuz/data` içindeki mevcut 179 dosyanın SHA-256'sı bu betikler çalıştırılmadan önce ve sonra aynı; `veri_dogruluk_kaydi.json` taban çizgisinin ("guncel") 179/179 değeriyle eşleşiyor (events/points/arazi/cal/metrics/harmonized/coverage dahil). Yeni: 56 dosya (27 + 27 yıl bini, 2 manifest; toplam 0,95 MB). Arayüz tarafında varsayılan: `isDefaultFilters` aynı sonucu verir, `aggMode` true kalır (hazır takvim tabloları), kartlar/grafikler/takvim aynı kodla aynı veriden; node ile core.js'in gerçek `makeFilter` çıktısı: varsayılan 302.863 olay, agg=true. Eksik bin dosyaları sıfır sayılır (sınandı).

### Bayrak sayıları (betik doğrulaması)

| Bayrak | Sayı | Doğrulama |
|---|---|---|
| aniz_il = 1 (yalnız st=0 olaylar) | 41.395 (temizin %13,67) | belgeli 33 olaydan etkilenen 0; en büyük bayraklı olay frp_max 22,4 MW, ≤15 tespit; büyük olay (frp≥300, n≥20, süre>24 sa) 0 |
| sanayi_artik = 1 | 8.283 (temizin %2,73; 125 saha, 45 il) | kural sonrası 8.290, muafiyetle 7 olay çıktı (rapordaki 7 küçük 2025 olayı); frp≥100 MW: 0; ≥10 tespit: 0; büyük olay: 0; en büyük frp_max 95,7 MW, ≤5 tespit; belgeli olay 0; resmî pencerede kalan 0 |
| İkisi birden bayraklı | 239 olay | arayüzde sanayi önceliklidir (sayımdan çıkarılınca düşer) |

### Senaryolar (tüm Türkiye, tüm tarihler, tüm sensör; "temiz" = yangın türü anız hariç)

| Senaryo | Temiz | Anız | Toplam yangın | Şanlıurfa temiz payı | İlk 5 il (temiz olay) |
|---|---|---|---|---|---|
| Varsayılan (bayrak yok) | 302.863 | 169.115 | 471.978 | %15,35 | Şanlıurfa 46.490, Mardin 24.481, Adana 22.621, Konya 21.739, Diyarbakır 20.880 |
| İl bazlı anız | 261.468 | 210.510 | 471.978 | %15,10 | Şanlıurfa 39.476, Mardin 21.209, Konya 18.145, Diyarbakır 17.606, Adana 17.156 |
| Sanayi artığı sayımdan hariç | 294.580 | 169.115 | 463.695 | %15,73 | Şanlıurfa 46.338, Mardin 24.456, Adana 22.349, Konya 21.486, Diyarbakır 20.657 |
| İkisi birden | 253.424 | 210.271 | 463.695 | %15,52 | Şanlıurfa 39.336, Mardin 21.187, Konya 17.896, Diyarbakır 17.423, Adana 16.912 |

Şanlıurfa temiz olayı il bazlı kuralla 46.490 → 39.476 (−7.014) iner ama ulusal temiz de düştüğü için pay yalnız %15,35 → %15,10 olur (sıfır kayıp: şişme Şanlıurfa'ya özgü değil, tarım ovası olgusu). Sanayi artıkları Şanlıurfa'da az olduğundan sanayi çıkarma payı hafifçe yükseltir (%15,73): Şanlıurfa'da sanayi artığı olayı yalnız 152, ulusal toplam 8.283. Sıralama (ilk 5) il bazlı anızda Konya/Diyarbakır/Adana yer değiştirir (Adana 3. → 5.); Şanlıurfa 1. kalır.

Anız payı (anız / (temiz+anız)), 2012 öncesi → sonrası: varsayılan 0,380 → 0,355; il bazlı anız 0,490 → 0,437 (fark 2,5 → 5,3 puan; rapordaki 0,490/0,437 ile aynı); ikisi birden 0,503 → 0,444. Yani il bazlı kural VIIRS döneminde göreli daha az anız yakalar (VIIRS 375 m tepe FRP'si).

### Yıllık temiz olay değişimi (varsayılana göre)

| Yıl | Varsayılan | İl bazlı anız Δ | Sanayi hariç Δ | İkisi Δ |
|---|---|---|---|---|
| 2000 | 86 | −27 | 0 | −27 |
| 2001 | 2.689 | −458 | −97 | −554 |
| 2002 | 3.386 | −611 | −165 | −773 |
| 2003 | 3.919 | −699 | −208 | −902 |
| 2004 | 3.902 | −773 | −234 | −1.004 |
| 2005 | 4.169 | −734 | −247 | −979 |
| 2006 | 4.923 | −824 | −220 | −1.044 |
| 2007 | 4.689 | −786 | −210 | −995 |
| 2008 | 2.916 | −508 | −211 | −716 |
| 2009 | 9.903 | −1.738 | −276 | −2.011 |
| 2010 | 7.001 | −1.224 | −264 | −1.482 |
| 2011 | 8.786 | −1.612 | −236 | −1.843 |
| 2012 | 10.524 | −1.112 | −247 | −1.347 |
| 2013 | 13.855 | −2.161 | −306 | −2.456 |
| 2014 | 9.228 | −1.136 | −257 | −1.382 |
| 2015 | 18.721 | −2.999 | −451 | −3.440 |
| 2016 | 16.434 | −2.374 | −281 | −2.650 |
| 2017 | 12.143 | −1.727 | −360 | −2.075 |
| 2018 | 14.239 | −2.007 | −292 | −2.288 |
| 2019 | 16.821 | −2.363 | −290 | −2.644 |
| 2020 | 18.174 | −2.223 | −342 | −2.553 |
| 2021 | 13.342 | −1.723 | −278 | −1.994 |
| 2022 | 11.847 | −1.227 | −325 | −1.540 |
| 2023 | 24.487 | −2.788 | −451 | −3.223 |
| 2024 | 27.462 | −3.565 | −601 | −4.143 |
| 2025 | 21.503 | −1.891 | −617 | −2.487 |
| 2026 | 17.714 | −2.105 | −817 | −2.887 |

### Belgelenmiş yangın kontrolleri

- `gercek_dogrulama.json` + `recall_olcumu.json` yakalanan olaylar (33 event_id): hiçbirinin durumu hiçbir senaryoda değişmedi (0/33); sanayi bayrağı için ayrıca belgeli olay 0, resmî pencerede bayraklı 0.
- Büyük olaylar (frp_max ≥ 300 MW veya ≥ 20 tespit): bayraklanan/değişen 0. frp_max ≥ 100 MW olan değişen olay: 0 (her iki bayrak için).
- Dolaylı etki (dürüst not): `resmi_yangin_listesi.json` 29 yangının 40 km ve başlangıç−2…+35 gün penceresindeki 700 olaydan, il bazlı anız 71 küçük/kısa yan olayı anıza çevirir (yangının kendisi değil); sanayi bayrağı için 0 (muafiyet).

### Arayüz davranışı (özet)

- "Anızı il bazlı eşikle çıkar": açılınca `st==0 && aniz_il==1` olaylar her tarayıcı hesabında anız sayılır (harita, en yüksek 10 listesi, takvim ve grafikler filtre modunda); `isDefaultFilters` false olur, hazır tablo kullanılmaz. Yangın türü düğmeleriyle birleşir.
- "Sanayi artıklarını sayımdan çıkar": açılınca bayraklı olaylar tüm sayımlardan düşer, filtre moduna geçilir. "Sanayi alanı artıklarını göster": yalnız harita katmanı. Varsayılan: bayraklı olaylar haritada ve en yüksek-FRP listesinde/🔥 işaretlerinde gizli, sayımlarda (kartlar, takvim ★, grafikler) hâlâ sayılır; "N sanayi artığı gizlendi" notu gösterilir. Gösterilince sanayi renginde (turuncu ◆) çizilir.
- Durum panelinde "Yangın sayılmayan ısı kaynakları" grubuna yeni sınıf ve sayısı eklendi (varsayılanda hâlâ temiz sayıldığı açıkça yazılı).
- Önbellek: tüm `?v=2.5.1` → `?v=2.5.2`.

### Sınırlar

Tarayıcıda görsel sınama yapılmadı (yalnız `node --check` ve node ile core.js süzgeç/yükleme sınaması). Sanayi kuralı ve il bazlı eşik tahmindir; OSM tamlığı bölgeye göre değişir. n_mcell uygulama verisinde yok, vekil max(n_modis, ⌈n_viirs/4⌉) kullanıldı (gerçek st=6 ile %99,94 uyum). Betikler: `kaynak_kod/src/aniz_il/aniz_il_uret.py`, `kaynak_kod/src/sanayi/sanayi_artik_uret.py` (OSM ham yanıtları gerekir: `--osm`); sayımlar için scratchpad `measure.py`.
