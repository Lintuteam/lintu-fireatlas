# Duyarlılık (recall) ölçümü: resmî büyük yangınların kaçını yakaladık?

**Soru:** Belgelenmiş büyük orman yangınlarının kaçı bizim olay tablomuzda var? Bu, 16/20 doğrulamasının (bulduklarımız gerçek mi, yani kesinlik) tersidir.

**Referans liste:** `resmi_yangin_listesi.md`. 2021 için 15, 2025 için 14 yangın; kaynaklar haberler, OGM verisine dayanan akademik makale ve Vikipedi. Liste **eksiktir**: OGM verisine göre 2021'de ≥500 ha yangın sayısı 28, listemizde yaklaşık yarısı var. Koordinatlar yangın yeri değil **ilçe merkezidir**.

**Eşleştirme ölçütü:** olay tablosunda (tüm etiketler) resmî başlangıçtan 1 gün önce ile 3 gün sonra arasında başlayan, ilçe merkezine ≤ 30 km uzaklıkta ve en az 5 tespitli bir olay. Tarihi bilinmeyen 6 yangında pencere 1 Haziran – 30 Eylül, en az 20 tespit. Betik: oturum içi analiz; sonuçlar `recall_olcumu.json`.

## Sonuç

| Ölçüt | Sonuç |
|---|---|
| Katı ölçüt (30 km) | **26 / 28 (%93)** (kapsam aşağıda; genel tespit oranı değil) |
| Yalnız tarihli kayıtlar | 20 / 22 |
| Elle inceleme sonrası | 28 / 28 |
| Değerlendirilemeyen | 1 (Menteşe 2021, koordinat yok) |
| Yanlış etiket | Yakalanan 26 olayın tamamı "temiz": hiçbir büyük orman yangını anız ya da sanayi diye ayrılmamış |

**Kapsam uyarısı:** %93, eksik ve çoğunlukla büyük yangınlardan oluşan bir referans listesine (6 kaydı tarihsiz) göre ve 30 km'lik seçilmiş eşleştirme mesafesiyle ölçüldü; genel bir tespit oranı değildir. 16/20 doğrulaması ise yalnız en büyük 20 olayın kesinliğidir (seçilmiş örnek).

**Mesafeye duyarlılık:** 15 km'de 16/28, 30 km'de 26/28, 50 km'de 28/28. İlçe merkezi kaba bir konum olduğu için düşük yarıçapta kaçırma artıyor; bu, tespit eksikliği değil konum belirsizliğidir.

**Kaçan iki kaydın elle incelemesi:**

- **Akseki 2021-07-29:** Ayrı olay yok: Manavgat yangını Akseki'ye yayılmıştı ve kümeleme bunu tek olay yaptı (event 307626, merkez Akseki ilçe merkezine 32,8 km). Yakalandı, ama ayrı olay olarak değil.
- **Seyitgazi 2025-07-22:** Yangın İhsaniye'ye (Afyonkarahisar) taştı; olay 428284 (200 tespit, 9.982 MW) ilçe merkezine 34,3 km. Yakalandı, ölçüt dışında kaldı.

## Tablo

| Yıl | İl | İlçe | Resmî tarih | Sonuç | Bizim olay | Bizim başlangıç (TR) | Uzaklık (km) | Tespit | FRP toplam (MW) |
|---|---|---|---|---|---|---|---|---|---|
| 2021 | Antalya | Manavgat | 2021-07-28 | yakalandı | 307626 | 2021-07-28 12:00 | 14.3 | 6740 | 384683 |
| 2021 | Antalya | Gündoğmuş | 2021-07-29 | yakalandı | 307718 | 2021-07-29 12:53 | 5.5 | 2336 | 75470 |
| 2021 | Antalya | Akseki | 2021-07-29 | kaçırıldı | – | – | – | – | – |
| 2021 | Muğla | Marmaris | 2021-07-29 | yakalandı | 307723 | 2021-07-29 13:43 | 11.1 | 1783 | 43759 |
| 2021 | Muğla | Bodrum | 2021-07-31 | yakalandı | 307807 | 2021-07-31 23:34 | 28.6 | 2123 | 103176 |
| 2021 | Muğla | Milas | tarihsiz (yaz penceresi) | yakalandı | 307950 | 2021-08-06 12:53 | 27.0 | 369 | 4572 |
| 2021 | Muğla | Köyceğiz | 2021-07-28 | yakalandı | 307744 | 2021-07-29 23:47 | 12.4 | 1702 | 41700 |
| 2021 | Muğla | Menteşe | — | değerlendirilemedi (koordinat yok) | – | – | – | – | – |
| 2021 | Muğla | Kavaklıdere | tarihsiz (yaz penceresi) | yakalandı | 307866 | 2021-08-02 23:22 | 12.5 | 2318 | 68286 |
| 2021 | Muğla | Yatağan | tarihsiz (yaz penceresi) | yakalandı | 307866 | 2021-08-02 23:22 | 21.6 | 2318 | 68286 |
| 2021 | Muğla | Seydikemer | tarihsiz (yaz penceresi) | yakalandı | 307844 | 2021-08-02 01:57 | 17.3 | 89 | 4239 |
| 2021 | Mersin | Aydıncık | 2021-07-15 | yakalandı | 307200 | 2021-07-15 10:53 | 12.2 | 412 | 16842 |
| 2021 | Mersin | Silifke | 2021-07-29 | yakalandı | 307706 | 2021-07-29 11:05 | 28.3 | 536 | 23541 |
| 2021 | Adana | Kozan | 2021-07-28 | yakalandı | 307678 | 2021-07-28 23:04 | 22.8 | 343 | 6913 |
| 2021 | Osmaniye | Merkez | 2021-07-28 | yakalandı | 307679 | 2021-07-28 23:04 | 17.9 | 349 | 9067 |
| 2025 | İzmir | Seferihisar, Menderes | 2025-06-29 | yakalandı | 426373 | 2025-06-28 14:46 | 12.6 | 996 | 73305 |
| 2025 | İzmir | Çeşme | 2025-07-02 | yakalandı | 426891 | 2025-07-02 13:31 | 16.0 | 1208 | 57830 |
| 2025 | İzmir | Ödemiş | 2025-07-02 | yakalandı | 426927 | 2025-07-02 21:41 | 8.2 | 499 | 13165 |
| 2025 | İzmir | Buca | 2025-07-03 | yakalandı | 427042 | 2025-07-03 22:21 | 6.7 | 323 | 12583 |
| 2025 | Hatay | Antakya | tarihsiz (yaz penceresi) | yakalandı | 426617 | 2025-06-30 10:58 | 12.6 | 392 | 30019 |
| 2025 | Sakarya; Bilecik | Geyve, Taraklı; Gölpazarı, Osmaneli | 2025-07-20 | yakalandı | 428217 | 2025-07-20 22:04 | 19.7 | 1032 | 75410 |
| 2025 | Bursa | Orhaneli, Harmancık | 2025-07-26 | yakalandı | 428617 | 2025-07-27 12:49 | 20.2 | 500 | 32112 |
| 2025 | Eskişehir (Afyonkarahisar'a taştı) | Seyitgazi | 2025-07-22 | kaçırıldı | – | – | – | – | – |
| 2025 | Karabük | Safranbolu | 2025-07-23 | yakalandı | 428378 | 2025-07-23 20:46 | 19.3 | 1413 | 28531 |
| 2025 | Çanakkale | Gelibolu, Eceabat | 2025-08-16 | yakalandı | 429635 | 2025-08-16 21:48 | 20.7 | 609 | 19026 |
| 2025 | Muğla | Köyceğiz | 2025-09-19 | yakalandı | 432655 | 2025-09-19 02:29 | 16.9 | 505 | 12972 |
| 2025 | Muğla | Milas | 2025-09-19 | yakalandı | 432654 | 2025-09-19 02:28 | 14.7 | 31 | 317 |
| 2025 | İzmir | Aliağa, Foça | 2025-06-25 | yakalandı | 425916 | 2025-06-25 13:11 | 10.8 | 155 | 13309 |
| 2025 | Manisa | Akhisar | tarihsiz (yaz penceresi) | yakalandı | 426343 | 2025-06-28 13:06 | 11.5 | 382 | 35001 |

## Sınırlar (dürüstçe)

- Referans liste eksik ve yalnız büyük (çoğu ≥500 ha) yangınları içeriyor. **Küçük yangınlarda duyarlılık ölçülmedi.** Uydunun küçük ve kısa yangınları kaçırması fiziksel olarak beklenir (MODIS FRP50 ≈ 65 MW, tahmini).
- Tarihsiz 6 kayıtta eşleştirme gevşek: yaz penceresi ve 30 km. Örneğin Yatağan ve Kavaklıdere aynı olaya eşleşti; bunlar aynı yangın dalgasının parçaları olabilir.
- Milas 2025 eşleşmesi zayıf (31 tespit, 317 MW); aynı gün Köyceğiz'deki büyük olay da 30 km içinde.
- Yanan alan (MCD64A1 ya da OGM poligonları) ile alan bazında karşılaştırma yapılmadı; bu ölçüm olay varlığına dayanıyor.
- Ölçüt sonuçlar görülmeden belirlendi (30 km, −1/+3 gün), ama mesafe duyarlılığı yukarıda tam olarak verildi.


## Kaynak türü ve resmî/bilimsel kaynaklar (güncelleme 2026-11-14)

Haber sitesi ağırlıklı kaynaklar yerine resmî (OGM, Tarım ve Orman Bakanlığı, NASA, Copernicus) ve hakemli kaynaklar tarandı. Yalnızca açılıp tarih ve yer eşleşmesi doğrulananlar yazıldı; eski haber bağlantıları JSON'da 'ikincil kaynak' olarak korunuyor. Kaynak türü: resmi / bilimsel / haber / yok. Çoğu resmî duyuru yanan alanı hektar olarak vermez; hektar rakamı yalnızca OGM Muğla OBM tablosunda ve hakemli makalede bulundu. Copernicus EMS (EMSR) aktivasyonu Türkiye 2021/2025 yangınları için bulunamadı. OGM yıllık istatistiği yalnızca ulusal toplamdır (2021: 2.793 yangın, 139.503 ha; 2025: 3.224 yangın, 81.473 ha; OGM 2025 Faaliyet Raporu Tablo 16-17).

| Yıl | İl | İlçe | Kaynak türü | Resmî / bilimsel kaynak | İkincil |
|---|---|---|---|
| 2021 | Antalya | Manavgat | resmi+bilimsel | [bilimsel: Hakemli dergi](https://dergipark.org.tr/tr/download/article-file/4867209)<br>[resmi: Copernicus (AB)](https://www.copernicus.eu/en/media/image-day-gallery/violent-wildfires-turkey)<br>[resmi: NASA Earth Observatory](https://science.nasa.gov/earth/earth-observatory/fires-rage-in-turkey-148650) | – |
| 2021 | Antalya | Gündoğmuş | haber | resmî kaynak bulunamadı | – |
| 2021 | Antalya | Akseki | resmi | [resmi: Copernicus (AB)](https://www.copernicus.eu/en/media/image-day-gallery/violent-wildfires-turkey) | – |
| 2021 | Muğla | Marmaris | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023+Yili+Orman+Yanginlari+Degerlendirme+Raporu.pdf) | – |
| 2021 | Muğla | Bodrum | haber | resmî kaynak bulunamadı | – |
| 2021 | Muğla | Milas | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023+Yili+Orman+Yanginlari+Degerlendirme+Raporu.pdf) | – |
| 2021 | Muğla | Köyceğiz | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023+Yili+Orman+Yanginlari+Degerlendirme+Raporu.pdf) | – |
| 2021 | Muğla | Menteşe | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023+Yili+Orman+Yanginlari+Degerlendirme+Raporu.pdf) | – |
| 2021 | Muğla | Kavaklıdere | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023+Yili+Orman+Yanginlari+Degerlendirme+Raporu.pdf) | – |
| 2021 | Muğla | Yatağan | haber | resmî kaynak bulunamadı | – |
| 2021 | Muğla | Seydikemer | haber | resmî kaynak bulunamadı | – |
| 2021 | Mersin | Aydıncık | bilimsel | [bilimsel: Hakemli dergi](https://dergipark.org.tr/tr/download/article-file/4867209) | – |
| 2021 | Mersin | Silifke | bilimsel | [bilimsel: Hakemli dergi](https://dergipark.org.tr/tr/download/article-file/4867209) | – |
| 2021 | Adana | Kozan | bilimsel | [bilimsel: Hakemli dergi](https://dergipark.org.tr/tr/download/article-file/4867209) | – |
| 2021 | Osmaniye | Merkez | bilimsel | [bilimsel: Hakemli dergi](https://dergipark.org.tr/tr/download/article-file/4867209) | – |
| 2025 | İzmir | Seferihisar, Menderes | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6655/Bakan-Yumaklidan-Orman-Yanginlarina-Karsi-Toplumsal-Duyarlilik-Cagrisi)<br>[resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/izmirobm/haberler/seferihisar-kavakderede-cikan-yangin-sonrasi-agaclandirma-calismalari-suruyor) | – |
| 2025 | İzmir | Çeşme | resmi | [resmi: NASA Earthdata](https://www.earthdata.nasa.gov/news/worldview-image-archive/wildfires-izmir-province-turkey)<br>[resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6661/Bakan-Yumakli-Ulkemizde-Devam-Eden-Orman-Yanginlarinin-Son-Durumuna-Iliskin-Aciklamalarda-Bulundu) | – |
| 2025 | İzmir | Ödemiş | resmi | [resmi: NASA Earthdata](https://www.earthdata.nasa.gov/news/worldview-image-archive/wildfires-izmir-province-turkey)<br>[resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6661/Bakan-Yumakli-Ulkemizde-Devam-Eden-Orman-Yanginlarinin-Son-Durumuna-Iliskin-Aciklamalarda-Bulundu) | – |
| 2025 | İzmir | Buca | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6661/Bakan-Yumakli-Ulkemizde-Devam-Eden-Orman-Yanginlarinin-Son-Durumuna-Iliskin-Aciklamalarda-Bulundu) | – |
| 2025 | Hatay | Antakya | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6655/Bakan-Yumaklidan-Orman-Yanginlarina-Karsi-Toplumsal-Duyarlilik-Cagrisi) | – |
| 2025 | Sakarya; Bilecik | Geyve, Taraklı; Gölpazarı, Osmaneli | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6682/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlariyla-Ilgili-Aciklama-Yapti) | – |
| 2025 | Bursa | Orhaneli, Harmancık | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6684/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlarindaki-Son-Durumu-Paylasti)<br>[resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6685/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlariyla-Ilgili-Aciklama-Yapti) | – |
| 2025 | Eskişehir (Afyonkarahisar'a taştı) | Seyitgazi | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6682/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlariyla-Ilgili-Aciklama-Yapti) | – |
| 2025 | Karabük | Safranbolu | resmi | [resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6682/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlariyla-Ilgili-Aciklama-Yapti)<br>[resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6685/Tarim-Ve-Orman-Bakani-Yumakli-Orman-Yanginlariyla-Ilgili-Aciklama-Yapti) | – |
| 2025 | Çanakkale | Gelibolu, Eceabat | haber | resmî kaynak bulunamadı | – |
| 2025 | Muğla | Köyceğiz | haber | resmî kaynak bulunamadı | – |
| 2025 | Muğla | Milas | haber | resmî kaynak bulunamadı | – |
| 2025 | İzmir | Aliağa, Foça | haber | resmî kaynak bulunamadı | – |
| 2025 | Manisa | Akhisar | resmi | [resmi: Orman Genel Müdürlüğü](https://www.ogm.gov.tr/izmirobm/haberler/manisa-akhisar-musacada-yangin-sonrasi-agaclandirma-ve-genclestirme-calismalari)<br>[resmi: Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/6655/Bakan-Yumaklidan-Orman-Yanginlarina-Karsi-Toplumsal-Duyarlilik-Cagrisi) | – |
