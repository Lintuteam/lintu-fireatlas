# Sanayi bölgelerinde kalan tespitler: denetim (salt okunur)

Veri: `arayuz/data` (events/points/arazi, 2000-2026), OSM ham öğeler (29.779 öğe), kural: `temizlik_yontemi.md` (Y=5, M=8, N=40, S=4, hücre 0,01°). Betikler: scratchpad `sanayi\a1..a9.py, w.py`. Hiçbir proje dosyası değiştirilmedi.

## 1. Noktalar hangi katmanlarda görünüyor?

- `events_<yıl>.bin` yalnız `temiz` (0) ve `aniz` (6) olay içerir. Varsayılan olay katmanı (`main.js`: `S.statuses=Set([0])`; yangın türü 'Tümü' = temiz+anız) bu olayları çizer. OSM bayrağı (`osm`) arayüzde hiçbir süzgeçte/çizimde kullanılmıyor, yalnız olay kartında gösteriliyor.
- Ham nokta katmanı (`mapview.js drawRaw`, `main.js refreshRaw`): `S.statuses` içindeki durumdaki noktaları (varsayılan temiz) zoom >= 9'da artı işaretiyle çizer; sanayi/statik_nasa/kalici_belirsiz noktalar yalnız kullanıcı o durumu işaretlerse görünür. Sızıntı kaynağı katman değil, **temiz etiketi**dir.
- Temiz olay: 302.863; bunlardan OSM sanayi/işletme/flare/taş ocağı/çöp/enerji <=300 m olan (osm>0): **22.280** (%7,4). Tür: sanayi/işletme/flare 16.937, enerji 3.173, taş ocağı 1.354, çöp 816. Anız olaylarında osm>0: 9.378 (simüle edilmedi).
- Enerji santrali (osm=4) bayraklı temiz olayların 2.439/3.173'ü `plant:source=solar` (GES); ısı kaynağı değil, kurala dahil edilmemeli.

## 2. Yıl ve il dağılımı (temiz, osm>0)

| yıl | temiz osm>0 | temiz içi pay | önerilen kuralla taşınan |
|---|---|---|---|
| 2000 | 1 | %1.2 | 0 |
| 2001 | 196 | %7.3 | 97 |
| 2002 | 306 | %9.0 | 165 |
| 2003 | 454 | %11.6 | 208 |
| 2004 | 429 | %11.0 | 234 |
| 2005 | 478 | %11.5 | 247 |
| 2006 | 473 | %9.6 | 220 |
| 2007 | 411 | %8.8 | 210 |
| 2008 | 405 | %13.9 | 211 |
| 2009 | 537 | %5.4 | 276 |
| 2010 | 495 | %7.1 | 264 |
| 2011 | 491 | %5.6 | 236 |
| 2012 | 686 | %6.5 | 247 |
| 2013 | 763 | %5.5 | 306 |
| 2014 | 626 | %6.8 | 257 |
| 2015 | 953 | %5.1 | 451 |
| 2016 | 790 | %4.8 | 281 |
| 2017 | 811 | %6.7 | 360 |
| 2018 | 891 | %6.3 | 292 |
| 2019 | 969 | %5.8 | 290 |
| 2020 | 991 | %5.5 | 342 |
| 2021 | 941 | %7.1 | 278 |
| 2022 | 1023 | %8.6 | 325 |
| 2023 | 1559 | %6.4 | 451 |
| 2024 | 2082 | %7.6 | 601 |
| 2025 | 2234 | %10.4 | 624 |
| 2026 | 2285 | %12.9 | 817 |

Not: 2023-2026'da artış (N20/N21 eklenmesi; 2026'da NRT: 61.147 nokta `type=-1`, NASA type=2 mirası yalnız arşiv type=2 hücrelerine uygulanıyor). 2026'da pay %12,9 (diğer yıllar ~%5-8).

| il | sanayi/işl. | taş ocağı | çöp | enerji | toplam | önerilen kural |
|---|---|---|---|---|---|---|
| Ankara | 1549 | 15 | 20 | 74 | 1658 | 809 |
| Bursa | 1353 | 23 | 33 | 86 | 1495 | 936 |
| İzmir | 859 | 53 | 42 | 200 | 1154 | 295 |
| Kayseri | 817 | 145 | 13 | 124 | 1099 | 593 |
| Şanlıurfa | 427 | 70 | 49 | 552 | 1098 | 152 |
| Tekirdağ | 818 | 52 | 45 | 67 | 982 | 471 |
| Konya | 640 | 32 | 16 | 264 | 952 | 253 |
| Uşak | 697 | 10 | 0 | 49 | 756 | 644 |
| Adana | 492 | 44 | 3 | 77 | 616 | 272 |
| Manisa | 327 | 145 | 41 | 86 | 599 | 186 |
| Gaziantep | 470 | 14 | 16 | 88 | 588 | 405 |
| Diyarbakır | 433 | 76 | 13 | 50 | 572 | 223 |
| Denizli | 384 | 19 | 14 | 47 | 464 | 295 |
| Kahramanmaraş | 276 | 67 | 23 | 87 | 453 | 111 |
| Balıkesir | 332 | 24 | 12 | 56 | 424 | 104 |
| Kütahya | 202 | 13 | 137 | 60 | 412 | 58 |
| İstanbul | 361 | 33 | 4 | 6 | 404 | 0 |
| Çorum | 271 | 21 | 67 | 43 | 402 | 225 |
| Mersin | 286 | 8 | 3 | 99 | 396 | 40 |
| Kırklareli | 317 | 20 | 9 | 24 | 370 | 224 |

## 3. En çok temiz olay üreten 30 saha (OSM öğesi bazlı; 2000-2026)

Saha = olayın <=350 m'deki aynı türden OSM öğesi (yoksa 0,01° hücre). Hücre-düzeyi kalıcılık: ny yıl / nd gün / nmon ay / medm (aktif yılda ay sayısı medyanı); eşikler 5/40/8/4.

| # | saha (OSM ad [tür]) | il | olay | yıl | FRP med/maks MW | hücre ny/nd/nmon/medm | 3x3 ny/nd/nmon/medm | 3x3 statik_nasa nokta | baskın neden |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Uşak Tekstil Organize Sanayi Bölgesi [factory] | Uşak | 427 | 26 | 8.1/40 | 26/277/7/4.0 | 26/537/11/5.5 | 450 | C |
| 2 |  [industrial] | Bursa | 311 | 22 | 10.2/30 | 26/247/7/4.0 | 26/475/8/5.0 | 150 | C |
| 3 | Mimarsinan Organize Sanayi Bölgesi [industrial] | Kayseri | 287 | 16 | 10.8/31 | 15/86/7/3.0 | 16/197/9/4.0 | 0 | C |
| 4 | Kayseri Organize Sanayi Bölgesi [industrial] | Kayseri | 259 | 26 | 8.6/68 | 12/25/6/1.0 | 23/104/8/3.0 | 26 | D |
| 5 | Çorum Organize Sanayi Bölgesi [industrial] | Çorum | 225 | 26 | 7.8/57 | 21/72/5/2.0 | 26/157/7/3.5 | 0 | D |
| 6 | Uşak Deri (Karma) Organize Sanayi Bölgesi [factory] | Uşak | 219 | 17 | 8.6/29 | 20/98/6/3.0 | 21/393/12/5.0 | 181 | C |
| 7 | Sivas OSB 2. Kısım [industrial] | Sivas | 184 | 21 | 8.1/35 | 16/51/7/2.0 | 21/162/8/3.0 | 0 | D |
| 8 | Aksaray Organize Sanayi Bölgesi [industrial] | Aksaray | 180 | 19 | 12.0/69 | 11/16/5/1.5 | 18/99/7/3.0 | 6 | D |
| 9 | Malatya OSB [industrial] | Malatya | 179 | 25 | 7.4/50 | 23/153/7/3.0 | 26/338/7/4.0 | 225 | D |
| 10 | Başpınar OSB [industrial] | Gaziantep | 177 | 24 | 9.3/65 | 13/23/7/1.5 | 23/138/10/4.0 | 391 | D |
| 11 | Ankara Sanayi Odası 1. Organize Sanayi Bölgesi [industrial] | Ankara | 167 | 21 | 7.7/16 | 19/52/6/2.0 | 26/186/8/3.0 | 50 | D |
| 12 | MAN Türkiye [industrial] | Ankara | 165 | 25 | 9.4/105 | 25/156/6/4.0 | 26/242/8/4.0 | 0 | C |
| 13 | Velimeşe Organize Sanayi Bölgesi [industrial] | Tekirdağ | 160 | 26 | 7.3/60 | 23/58/6/2.0 | 26/175/8/3.0 | 50 | D |
| 14 | TÜMOSAN Motor ve Traktör Sanayi A.Ş. [industrial] | Konya | 157 | 26 | 12.1/46 | 24/69/5/2.0 | 26/143/7/3.0 | 6 | D |
| 15 | Organize Sanayi Bölgesi [industrial] | Adıyaman | 154 | 21 | 9.2/35 | 21/165/6/4.0 | 21/265/11/4.0 | 0 | C |
| 16 | Eskişehir Organize Sanayi Bölgesi (OSB) [industrial] | Eskişehir | 153 | 25 | 9.0/39 | 9/15/5/1.0 | 24/95/7/2.0 | 26 | D |
| 17 | İvedik Organize Sanayi Bölgesi [industrial] | Ankara | 153 | 22 | 8.5/20 | 20/46/5/2.0 | 26/196/6/4.0 | 68 | D |
| 18 | Söğütsen Seramik Fabrikası [works] | Çankırı | 151 | 17 | 8.2/32 | 16/98/5/3.0 | 17/204/6/4.0 | 0 | D |
| 19 | Akın Tekstil [factory] | Kırklareli | 150 | 26 | 8.9/38 | 26/126/6/3.0 | 26/187/8/4.0 | 0 | C |
| 20 | Hacı Ömer Sabancı Organize Sanayi Bölgesi [industrial] | Adana | 146 | 24 | 9.1/167 | 12/18/6/1.0 | 23/104/9/3.0 | 12 | D |
| 21 | Beşevler Sanayi Sitesi [industrial] | Bursa | 145 | 18 | 7.6/16 | 24/155/6/3.5 | 25/195/6/4.0 | 29 | D |
| 22 | Isparta Mensucat San. Tic. A.Ş. [industrial] | Isparta | 139 | 26 | 8.0/15 | 23/73/5/2.0 | 26/219/5/4.0 | 0 | D |
| 23 | Evren Sanayi Sitesi [industrial] | Şanlıurfa | 138 | 24 | 6.8/33 | 25/181/7/3.0 | 26/261/7/4.0 | 0 | D |
| 24 | Niğde OSB [industrial] | Niğde | 134 | 26 | 8.4/29 | 22/33/6/1.0 | 26/125/8/2.5 | 5 | D |
| 25 | Ergene 1 Organize Sanayi Bölgesi [industrial] | Tekirdağ | 131 | 25 | 6.0/31 | 14/31/5/1.5 | 25/144/8/3.0 | 0 | D |
| 26 |  [industrial] | Gaziantep | 127 | 24 | 5.2/19 | 20/47/7/2.0 | 24/211/11/5.0 | 222 | B |
| 27 | Antalya Organize Sanayi Bölgesi [industrial] | Antalya | 123 | 24 | 10.0/160 | 11/26/4/1.0 | 21/104/6/3.0 | 13 | D |
| 28 | Denizli Organize Sanayi Bölgesi [industrial] | Denizli | 118 | 16 | 10.7/20 | 25/243/7/4.0 | 26/879/10/7.0 | 1363 | B |
| 29 | Sakarya 2. Organize Sanayi Bölgesi [industrial] | Sakarya | 116 | 19 | 9.6/25 | 16/66/6/2.0 | 19/205/11/4.0 | 1 | C |
| 30 | Akyurt Sanayi Bölgesi [industrial] | Ankara | 113 | 23 | 11.1/60 | 7/12/4/1.0 | 19/52/9/1.0 | 0 | D |

İlk 30 sahanın tamamı OSM `landuse=industrial/works` (OSB, tekstil, seramik, motor fabrikaları); hepsi 16-26 farklı yılda yanıyor, olay başına medyan 1 tespit, FRP medyanı 5-12 MW (maks 30-167). Rafineri/demir-çelik çekirdekleri (Ereğli, Karabük, İsdemir, Aliağa) zaten statik_nasa/sanayi ile yakalanmış (6 km çevrede on binlerce statik nokta). Ağır sanayi artıkları: Aliağa çevresi 149, Tüpraş İzmit 42, İsdemir çevresi 31, Karabük 18 temiz-osm olay; İskenderun, Afşin-Elbistan, Yatağan, Çayırhan çevresinde temiz-osm olay <=8 (maden/santral OSM 300 m dışında veya OSM'de yok).

## 4. Neden temizlikten kaçtı?

Hücre özellikleri tüm noktalardan yeniden hesaplandı; her temiz-osm olay için kural (ny>=5, nmon>=8, nd>=40, medm>=4) denendi:

| neden grubu | olay | pay |
|---|---|---|
| D: kendi hücresi kuralı sağlamıyor (çoğu medm<4 ve/veya nd<40, nmon<8): zayıf, aralıklı tespit | 18611 | %83.5 |
| C: tek hücre sağlamıyor, 3x3 havuz sağlıyor (OSB birkaç hücreye yayılmış) | 2533 | %11.4 |
| B: komşu hücre kuralı sağlıyor (konum ofseti >0,01°; VIIRS 375 m / MODIS 1 km hücre kayması) | 1099 | %4.9 |
| A: kendi hücresi sağlıyor, olay yine temiz (yangın koruması) | 37 | %0.2 |

Ek bulgular:
- Olayların %81'i tek-nokta (n=1), FRP medyanı ~8 MW: ısı sinyali her ayda değil yılda birkaç kez gelir; `medm>=4` ve `nd>=40` hücre başına tutmaz. Kural NASA type=2'ye (büyük/sürekli baca, meşale) göre kalibre edildi; OSB çatı/küçük baca ısısı ayrı bir popülasyon.
- 22.280 olayın 8.943'ü (%40) 3x3 çevresinde statik_nasa/sanayi/kalici nokta olan hücrelerde: komşu hücre etiketli, kendisi değil (ofset).
- NRT (2026): 61.147 `type=-1` nokta; arşivde type=2 olmayan tesislerde miras etkisiz. 2026'da osm>0 pay iki katı.
- Yeni tesis/OSM: kural yalnız hücre geçmişine bakar; OSM yalnız bayrak, etiket kararında kullanılmıyor.
- Koruma kuralı: kural-sağlayan hücrede temiz kalan yalnız 37 olay (%0,2): ana neden değil.

## 5. Önerilen kural (uygulanmadı) ve simülasyon

**`sanayi_osm_artik`:** olay `temiz` ve (osm=1 veya osm=4 ve plant:source solar/wind/hydro/geothermal değil) ve sahası (OSM öğesi) 2000-2026'da >=5 farklı yılda olay üretmiş ve saha olayları >=6 farklı takvim ayına yayılmış (mevsimsel tarla yakmasını ayırır) ve olay küçük (frp_max<100 MW, tespit <=5) ve +-3 gün / 15 km içinde büyük temiz olay (frp_max>=300 veya >=20 tespit) yok -> `status=sanayi` (neden `osm_kalici_artik`). frp_max>=300 MW veya >=20 tespitli olaylar baştan muaf.

Duyarlılık (taşınan temiz olay; büyük olaylar hariç):

| varyant | taşınan | frp>=100 | n>=10 |
|---|---|---|---|
| osm1, saha yıl>=5 | 13.124 | 26 | 24 |
| osm1,4, saha yıl>=5 | 15.043 | 29 | 34 |
| osm1-4, saha yıl>=5 | 15.689 | 35 | 43 |
| osm1,4, yıl>=5, frp<100, n<=5 | 14.892 | 0 | 0 |
| **önerilen** (+ay>=6, solar hariç, komşu-büyük koruması) | 8.290 | 0 | 0 |

**Önerilen kuralın etkisi:** 8.290 olay temizden çıkar (temizin %2.7'i, osm>0 temizin %37'i; 125 saha, 45 il). En çok: Bursa 936, Ankara 809, Uşak 644, Kayseri 593, Tekirdağ 471, Gaziantep 405, Denizli 295, İzmir 295. 2026: 817 olay. Taşınanın FRP maks. 96 MW, medyan 8.5 MW; tespit <=5; arazi örtüsü ağırlıkla yapılaşmış (WC 50: %72), ağaç payı ort. %3.2.

Güvenlik kontrolleri:
- frp_max>=300 MW veya >=20 tespitli olaylardan taşınan: **0** (65 osm>0 büyük olay muaf; frp>=100 MW: 0, >=10 tespit: 0). Daha gevşek varyantlar bu sınırı aşar (yukarı tablo), bu yüzden boyut sınırı şart.
- `gercek_dogrulama.json` 20 olay (event_id): hiçbiri osm>0 değil, taşınan **0**.
- `resmi_yangin_listesi.json` 29 yangın (2021/2025; konum ilçe merkezi): +-40 km ve başlangıç-2 gün...+35 gün gevşek pencerede 7 küçük 2025 olayı (tek nokta, 0,6-14 MW, 9-18 yıllık aktif OSB sahaları) taşınıyor; bunlar belgelenmiş yangının kendisi değil. Sıkı pencerede (10 km, 14 gün) 1 olay (İzmir 2025-06-25 yangınına 7 km, 8 MW tek nokta, OSM sanayi). Belgelenmiş yangın olaylarının hiçbiri taşınmıyor; bu 1 sınır vaka yangın değil sanayi ısısı olarak değerlendirildi (kesin 0 isteniyorsa listedeki yangın pencereleri muafiyete eklenir).
- Önerilen regresyon testi: yangın listelerindeki pencerelerde kural sonrası olay sayısı değişmemeli.

**Notlar:** Nokta düzeyi alternatif (3x3 havuz kalıcılığı, C+B = 3.632 olay) simüle edilmedi. Anız olaylarında osm>0 (9.378) ayrı karar ister. osm=2 (taş ocağı) ve 3 (çöp) kurala alınmadı: çöp sahası yangınları gerçek yangındır, taş ocağı ısı kaynağı değildir; ayrı bayrak önerilir.
