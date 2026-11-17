# Küçük ve orta olaylar için bağımsız doğrulama denemesi (yansız örneklem)

Bu belge, mevcut `gercek_dogrulama.*` çalışmasının yalnızca en büyük 20 olayı kontrol etmesi nedeniyle "büyük yangınlara yanlı" olduğu eleştirisine yanıt vermek için hazırlandı. Burada **küçük (S) ve orta (M)** olaylardan rastgele örneklem alındı ve her biri için web'de haber/resmî kayıt arandı.

## Kısa sonuç (dürüst özet)

**50 olayın hiçbiri için, tarih ve yer birlikte eşleşen bir haber/resmî kayıt bulunamadı (S: 0/25, M: 0/25).** Bu sonuç "50 olayın 50'si yanlış" demek **değildir**; aşağıda açıklandığı gibi bu yöntem küçük yangınları bulmak için zaten duyarlı değildir. Bu deneme **kesinlik (precision) kanıtı üretememiştir**; kesinlik için haber araması yerine uydu görüntüsü (Sentinel-2 yanık izi) gibi bağımsız bir yöntem gerekir (bkz. Öneriler).

## Yöntem

- **Evren:** `status = temiz` (varsayılan uygulama görünümü), 2019-2025, `gercek_dogrulama.json`'daki 20 olay hariç. Evren: 133.619 olay.
- **Tabakalar:** tespit sayısı = `n_modis + n_viirs`.
  - **S (küçük):** 1-3 tespit **ve** tepe FRP < 20 MW. Evren: 98.617.
  - **M (orta):** S dışında kalan ve (4-19 tespit **veya** tepe FRP 20-100 MW). Evren: 33.856.
- **Örnekleme:** her tabakadan 25 olay, `pandas.DataFrame.sample(25, random_state=20261114)`. **Tohum = 20261114** (tabakalar ayrı örneklendi). Toplam 50 olay. Tüm olaylar 2019-2025 ve `temiz`.
- **Konum adı:** il = uygulamanın il verisi; ilçe/köy = OpenStreetMap Nominatim ters coğrafi kodlama (yalnızca koordinat gönderildi). Bazı kayıtlarda ilçe boş (Nominatim döndürmedi).
- **Arama:** her olay için WebSearch ile Türkçe sorgular ("<ilçe> <köy> yangın <tarih>", ayrıca "anız/orman yangını" varyantları), ±2 gün penceresi. Arama aracı tarih filtresi sunmuyor; sonuçta tarih görünmeyen veya farklı yıl/yerdeki haberler **eşleşme sayılmadı**. İki olay (291289 Bismil, 326542 Viranşehir) komşu olayların sorgusuyla birlikte arandı.
- **Sınıflar:** (a) belgeli orman/çalılık yangını, (b) belgeli anız/tarla yangını, (c) belgeli diğer gerçek yangın (çöplük, bina, sanayi), (d) kayıt bulunamadı.
- **Arazi bağlamı:** projenin kendi `arazi_<yıl>.bin` katmanından (ESA WorldCover 2021, ±250 m; OSM sanayi/çöplük bayrakları). İnternetten dosya indirilmedi.

## Sonuçlar

| Gösterge | S (küçük), n=25 | M (orta), n=25 |
|---|---|---|
| Belgeli gerçek yangın (a+b+c) | 0/25 = %0 (%95 Wilson GA: %0-13,3) | 0/25 = %0 (%0-13,3) |
| Orman/çalılık yangını (a) | 0 = %0 (%0-13,3) | 0 = %0 (%0-13,3) |
| Anız/tarla yangını (b) | 0 = %0 (%0-13,3) | 0 = %0 (%0-13,3) |
| Diğer gerçek yangın (c) | 0 | 0 |
| Kayıt yok (d) | 25/25 = %100 (%86,7-100) | 25/25 = %100 (%86,7-100) |

Arazi bağlamı (WorldCover): S'de 22 tarla, 3 otlak; M'de 21 tarla, 4 otlak. Hiçbir olay orman/ağaç sınıfında değil. OSM sanayi bayrağı: S'de 0, M'de 1 (İzmir-Aliağa 401227, sanayi/rafineri bölgesi). Projenin kendi `aniz_il` bayrağı: S'de 6, M'de 2 olayda var. Yani örneklem büyük ölçüde güneydoğu/İç Anadolu tarım ovalarında, sonbahar-kış ve yaz hasat sonrası dönemde yoğunlaşıyor: bu, bu olayların büyük çoğunlukla anız/tarla yakma olasılığı taşıdığı anlamına gelir, ama bunu bu çalışma **kanıtlamamıştır**.

Wilson aralığının üst sınırı (%13,3) şu anlama gelir: 0/25 gözlemi, gerçek "habere yansıyan olay oranı" için %13'ten yüksek değerlerle de uyumsuz değildir.

## "Kayıt yok" neden "yanlış alarm" demek değildir

1. **Küçük yangınlar haber olmaz.** 1-3 uydu tespitli, tepe gücü < 20 MW olan bir olay tipik olarak birkaç dekarlık bir tarla/anız yangınıdır; köylü veya itfaiye söndürür, haber/valilik açıklaması üretmez. OGM yalnızca orman alanlarındaki yangınları sayar; tarla ve anız yangınları resmî orman istatistiğinde yoktur.
2. **Arama aracının sınırı.** WebSearch (ABD merkezli genel arama) tarih filtresi sunmaz, yerel haber arşivlerini (İHA/DHA/AA'nın eski sayfaları, yerel gazeteler) sistematik taramaz; sonuçların çoğunda yayın tarihi görünmez. Aracın duyarlılığı kontrol edilmedi. Büyük bir olayda (21 Haziran 2024 Diyarbakır-Mardin anız yangını, 15 ölü) araç sonuçları kolayca buldu; yani araç büyük olayları buluyor, küçükleri bulamıyor. Bu da doğrulama yanlılığının **ters yönünü** gösterir: haberle doğrulama büyük olaylara yanlıdır, küçük olaylarda "kayıt yok" beklenen sonuçtur.
3. **Bazı olaylar zaten haber değeri taşımayan ısı kaynağı olabilir.** Kış aylarındaki (Ocak, Şubat, Mart, Aralık) tek tespitli olaylar çiftçi yakması, sobalı yapı/sanayi ısısı veya düşük güvenli tespit olabilir. Bu belgede bu ayrımı yapacak bağımsız veri yoktur.
4. **Aday ama reddedilen kayıtlar.** Bazı olayların yakınında aynı ilde başka tarihli yangın haberleri çıktı (örn. Hatay-Hassa Ağustos 2025 orman yangını, Mardin-Savur 2026 anız haberi, Adana-Kozan 8-11 Eylül 2021). Tarih veya konum eşleşmediği için sayılmadı; her olayın `not` alanında ve `arama` alanında kaydı vardır.

## Sınırlar ve uyarılar

- n=25/tabaka küçüktür; bu sonuç yalnızca "haber araması bu olaylar için pozitif örnek üretmedi" bilgisini verir.
- Konum adları otomatik ters coğrafi kodlamadandır, bazı köy/mahalle adları yanlış olabilir; arama yalnızca birkaç sorguyla sınırlıdır (olay başına ~1-2 sorgu).
- Bu belge, `gercek_dogrulama.*` sonucunu (20 büyük olayın 16'sı eşleşiyor, 3'ü kısmi) **değiştirmez**; onu tamamlar: büyük olaylarda dış doğrulama güçlü, küçük olaylarda haberle doğrulama bu yöntemle mümkün olmadı.
- Önerilen dürüst ifade: "Küçük ve orta olayların kesinliği haber kayıtlarıyla ölçülemedi (0/50 eşleşme, 95% GA üst sınırı %13/tabaka; küçük yangınlar haberleşmez). Bu olayların büyük çoğunluğu tarım arazisi üzerinde olduğundan 'tarla/anız yangını veya tarımsal yakma' olarak yorumlanır ve uygulamada 'anız' bayrağı ile ayrılır."

## Öneriler (yapılmadı)

- Rastgele alt örneklemde Sentinel-2/Landsat yanık izi (dNBR) kontrolü, ya da EFFIS/GWIS yanık alan ürünüyle kesişim; bu, haber bağımlılığını ortadan kaldırır.
- Haber araması için tarih filtreli bir arşiv (AA/DHA/İHA arşivi, GDELT) kullanmak.

## Örneklenen 50 olay

(ayrıntı, arama metni ve notlar `kucuk_yangin_dogrulama.json` içinde; S = küçük, M = orta; tarih UTC+3; süre saat; "a." = projenin anız-il bayrağı var)

| Tabaka | event_id | Tarih | İl/İlçe | Enlem, boylam | Tespit | Tepe FRP (MW) | Süre (sa) | Arazi | Anız bayrağı | Sınıf |
|---|---|---|---|---|---|---|---|---|---|---|
| S | 250531 | 2019-07-21 | Aksaray/- | 38.5356, 33.8269 | 1 | 0.3 | 0.0 | tarla |  | d |
| S | 265623 | 2019-11-04 | Diyarbakır/Yenişehir | 38.0746, 40.0013 | 2 | 12.7 | 0.8 | tarla |  | d |
| S | 269076 | 2019-11-20 | Denizli/Tavas | 37.5108, 29.0407 | 1 | 5.2 | 0.0 | tarla |  | d |
| S | 273952 | 2020-04-11 | Kırıkkale/Delice | 40.149, 34.0546 | 2 | 4.4 | 0.0 | tarla |  | d |
| S | 276233 | 2020-06-20 | Hatay/Hassa | 36.8215, 36.5726 | 2 | 3.7 | 13.2 | tarla |  | d |
| S | 293088 | 2020-10-27 | Konya/Çumra | 37.6544, 33.1465 | 1 | 11.4 | 0.0 | tarla |  | d |
| S | 295402 | 2020-11-11 | Konya/Karatay | 38.1588, 33.1292 | 1 | 5.8 | 0.0 | tarla | a. | d |
| S | 307902 | 2021-08-04 | Mardin/Savur | 37.6049, 40.8888 | 1 | 5.6 | 0.0 | otlak | a. | d |
| S | 310019 | 2021-09-09 | Adana/Karataş | 36.7572, 35.0313 | 1 | 4.6 | 0.0 | tarla | a. | d |
| S | 327284 | 2022-08-14 | Şanlıurfa/Ceylanpınar | 36.8707, 39.9423 | 3 | 10.3 | 0.0 | tarla |  | d |
| S | 338652 | 2023-01-01 | Konya/Cihanbeyli | 38.6299, 32.7833 | 1 | 7.8 | 0.0 | tarla |  | d |
| S | 339122 | 2023-01-04 | Adana/- | 37.2062, 36.0325 | 1 | 2.3 | 0.0 | tarla |  | d |
| S | 343165 | 2023-03-26 | Eskişehir/İnönü | 39.7199, 30.2246 | 1 | 1.7 | 0.0 | tarla |  | d |
| S | 353435 | 2023-09-09 | Hatay/Kırıkhan | 36.5864, 36.4412 | 1 | 4.6 | 0.0 | tarla | a. | d |
| S | 355378 | 2023-09-17 | Adana/- | 37.1078, 36.0416 | 1 | 5.5 | 0.0 | tarla | a. | d |
| S | 362006 | 2023-10-15 | Çanakkale/Biga | 40.1912, 27.1302 | 1 | 6.3 | 0.0 | otlak |  | d |
| S | 369913 | 2023-11-26 | Konya/Karapınar | 37.6054, 33.249 | 3 | 5.8 | 0.4 | tarla | a. | d |
| S | 390981 | 2024-08-28 | Adıyaman/Gölbaşı | 37.7111, 37.5566 | 1 | 2.6 | 0.0 | otlak |  | d |
| S | 392601 | 2024-09-08 | Adıyaman/Besni | 37.5675, 38.0038 | 2 | 6.6 | 0.4 | tarla |  | d |
| S | 403861 | 2024-10-22 | Konya/Selçuklu | 38.2375, 32.5584 | 1 | 9.8 | 0.0 | tarla |  | d |
| S | 406640 | 2024-10-28 | Şanlıurfa/Eyyübiye | 37.0042, 39.1641 | 2 | 8.3 | 0.0 | tarla |  | d |
| S | 417924 | 2025-02-01 | Aksaray/- | 38.5038, 33.7986 | 2 | 3.6 | 0.0 | tarla |  | d |
| S | 421348 | 2025-03-16 | Eskişehir/Mahmudiye | 39.6255, 30.9303 | 1 | 3.3 | 0.0 | tarla |  | d |
| S | 422354 | 2025-04-19 | Malatya/Yazıhan | 38.569, 38.28 | 1 | 12.1 | 0.0 | tarla |  | d |
| S | 445055 | 2025-12-24 | Şanlıurfa/Suruç | 36.9543, 38.4041 | 3 | 5.1 | 0.3 | tarla |  | d |
| M | 252969 | 2019-08-25 | Nevşehir/Hacıbektaş | 39.0547, 34.6596 | 1 | 30.0 | 0.0 | tarla |  | d |
| M | 267553 | 2019-11-12 | Mardin/Kızıltepe | 37.0661, 40.19 | 1 | 21.8 | 0.0 | tarla |  | d |
| M | 276312 | 2020-06-21 | Mardin/Kızıltepe | 37.2468, 40.4724 | 5 | 36.4 | 0.8 | tarla |  | d |
| M | 278414 | 2020-07-06 | Şanlıurfa/Hilvan | 37.5035, 39.2016 | 11 | 50.6 | 1.7 | tarla |  | d |
| M | 288975 | 2020-10-08 | Kırşehir/Kaman | 39.4468, 33.7508 | 4 | 26.5 | 25.4 | otlak |  | d |
| M | 290249 | 2020-10-15 | Diyarbakır/Sur | 38.099, 40.3675 | 15 | 3.6 | 1.7 | tarla |  | d |
| M | 291289 | 2020-10-19 | Diyarbakır/Bismil | 37.8778, 40.5152 | 4 | 8.3 | 12.2 | tarla |  | d |
| M | 291963 | 2020-10-23 | Edirne/İpsala | 40.8774, 26.2747 | 10 | 11.5 | 1.7 | tarla |  | d |
| M | 304518 | 2021-06-09 | Mardin/Artuklu | 37.1405, 40.8755 | 1 | 22.4 | 0.0 | tarla | a. | d |
| M | 325569 | 2022-06-30 | Şanlıurfa/Viranşehir | 37.2543, 39.5361 | 1 | 50.1 | 0.0 | otlak |  | d |
| M | 326542 | 2022-07-16 | Şanlıurfa/Viranşehir | 37.1094, 39.5789 | 1 | 20.1 | 0.0 | tarla |  | d |
| M | 329364 | 2022-09-19 | Şanlıurfa/Siverek | 37.6917, 39.0561 | 6 | 14.8 | 0.8 | tarla |  | d |
| M | 354553 | 2023-09-14 | Şanlıurfa/Siverek | 37.6827, 39.0383 | 2 | 21.8 | 0.4 | tarla |  | d |
| M | 359934 | 2023-10-09 | Batman/Kozluk | 38.105, 41.2671 | 5 | 9.4 | 0.8 | tarla |  | d |
| M | 370858 | 2023-12-03 | Hakkâri/Yüksekova | 37.5007, 44.3541 | 21 | 31.7 | 1.7 | otlak |  | d |
| M | 382310 | 2024-06-20 | Şanlıurfa/Halfeti | 37.3055, 38.1017 | 8 | 21.7 | 0.9 | tarla | a. | d |
| M | 382484 | 2024-06-21 | Kahramanmaraş/Dulkadiroğlu | 37.3925, 37.0044 | 29 | 92.0 | 25.3 | tarla |  | d |
| M | 383400 | 2024-06-26 | Kırklareli/- | 41.7103, 27.1463 | 5 | 18.1 | 0.4 | tarla |  | d |
| M | 385535 | 2024-07-14 | Şanlıurfa/Viranşehir | 37.0989, 39.5704 | 3 | 50.1 | 2.4 | tarla |  | d |
| M | 397014 | 2024-09-30 | Muş/Malazgirt | 39.1428, 42.4601 | 2 | 25.5 | 0.4 | tarla |  | d |
| M | 401227 | 2024-10-15 | İzmir/Aliağa | 38.7537, 26.9349 | 7 | 1.4 | 25.4 | otlak |  | d |
| M | 430130 | 2025-08-24 | Adana/- | 37.0919, 36.0165 | 10 | 26.4 | 49.0 | tarla |  | d |
| M | 439223 | 2025-11-05 | Gaziantep/Araban | 37.4279, 37.6342 | 1 | 26.4 | 0.0 | tarla |  | d |
| M | 442016 | 2025-11-24 | Şanlıurfa/Siverek | 37.4352, 39.2695 | 3 | 20.4 | 0.8 | tarla |  | d |
| M | 443307 | 2025-12-02 | Mardin/Derik | 37.2644, 40.0195 | 4 | 5.8 | 25.9 | tarla |  | d |
