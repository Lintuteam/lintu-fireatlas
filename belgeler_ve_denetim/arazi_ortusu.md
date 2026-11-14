# Arazi örtüsü katmanı (WorldCover 2021 + OpenStreetMap)

Her yangın olayına, düştüğü yerin arazi türünü bağımsız haritalardan ekledik. Böylece uygulama "orman yangını adayı" tahmini yerine ölçülmüş bir sınıf (orman / tarla / çalılık-otlak / yapılaşmış / sanayi) söyleyebilir.

## Yöntem

- **ESA WorldCover 2021 (10 m, v200)**: 3°x3° karolar indirildi (AWS açık veri), her olay merkezinin çevresinde yaklaşık ±250 m'lik pencerede (enlemde 27 piksel, boylamda enleme göre ~35 piksel; ~51x51-71 piksel) sınıf yüzdeleri hesaplandı: ağaç (10), çalılık (20), otlak (30), tarla (40), yapılaşmış (50), gerisi "diğer". Çoğunluk sınıfı da saklandı. Veri yoksa 255.
- **OpenStreetMap (Overpass API)**: landuse=industrial, landuse=quarry, landuse=landfill, man_made=works, power=plant, man_made=flare öğeleri 2°x2° parçalarla çekildi (ham yanıt geçici klasörde). 0,001° (~100 m) ızgaraya çizilip 300 m tampon uygulandı; olay merkezi tampon içindeyse bayrak: 1 sanayi/işletme/flare, 2 taş ocağı, 3 çöp sahası, 4 enerji santrali (çakışmada 4>3>2>1).
- **Çıktı**: `arayuz/data/arazi_<yıl>.bin` (7 uint8 sütun: wc_maj, p_tree, p_shrub, p_grass, p_crop, p_built, osm; olay dosyasıyla aynı sıra; kolon j başlangıcı = j*n) ve `arazi_manifest.json`.
- **Kod**: `kaynak_kod/src/landcover/arazi_etiket.py` (üretim), `arazi_rapor.py` (bu belge).

## Kaynaklar ve lisans

- © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium. Lisans CC BY 4.0. https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/
- © OpenStreetMap contributors, ODbL. Overpass API (https://overpass-api.de/api/interpreter).

## Sınırlar

- Arazi örtüsü tek yıla (2021) aittir; 2000-2026 olaylarında arazi değişimi (yangın sonrası kül/yanık alan, yeni yapılaşma, tarla-orman dönüşümü) yok sayılır. 2021 yangınlarında harita yangından önceki-sonraki sahneye bağlı olabilir.
- Merkez ±250 m penceresi büyük olayların tamamını temsil etmez; olay merkezi yangının ağırlık merkezidir.
- OSM tamlığı bölgeye göre değişir; OSM bayrağı yok demek "sanayi değil" demek değildir. İç boşluklu (inner) OSM çokgenleri doldurulur. WorldCover'ın kendi doğruluğu ayrıca sınırlıdır (üretici raporu).
- Karo kenarındaki olaylarda pencere karoda kırpılır.

## 1. Olay durumuna göre arazi özeti

| durum (birim) | sayı | WC verisi var | ort. ağaç % | çalılık % | otlak % | tarla % | yapılaşmış % | diğer % | OSM bayrağı % | çoğunluk sınıfı |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| temiz (olay) | 302,863 | 302,863 | 5.1 | 0.4 | 14.3 | 72.7 | 4.5 | 2.9 | 7.4 | tarla 78%, otlak 11%, yapılaşmış 5%, ağaç 4% |
| deniz (nokta) | 8,848 | 8,848 | 6.4 | 0.8 | 5.1 | 5.0 | 41.0 | 41.7 | 77.1 | yapılaşmış 51%, su 35%, tarla 4%, sulak 3% |
| volkan (nokta) | 5 | 5 | 0.0 | 0.0 | 60.0 | 39.6 | 0.0 | 0.4 | 0.0 | otlak 60%, tarla 40% |
| statik_nasa (nokta) | 328,379 | 328,379 | 9.3 | 0.1 | 8.1 | 3.9 | 62.5 | 16.1 | 89.8 | yapılaşmış 85%, çıplak 7%, ağaç 3%, otlak 3% |
| sanayi (nokta) | 27,012 | 27,012 | 10.7 | 0.4 | 14.6 | 7.5 | 46.2 | 20.7 | 92.5 | yapılaşmış 63%, çıplak 15%, otlak 10%, ağaç 5% |
| aniz (olay) | 169,115 | 169,114 | 4.4 | 0.4 | 14.1 | 75.2 | 3.4 | 2.6 | 5.5 | tarla 82%, otlak 11%, ağaç 3%, yapılaşmış 3% |
| kalici_belirsiz (nokta) | 6,208 | 6,208 | 8.3 | 0.2 | 21.2 | 31.4 | 24.5 | 14.4 | 57.8 | tarla 35%, yapılaşmış 32%, otlak 19%, çıplak 9% |

Birim: events dosyasında yalnız temiz ve aniz olay olarak bulunur (471,978 olay; WC verisi olmayan: 1); diğer durumlar yalnız tespit noktası düzeyindedir (points_<yıl>.bin), tablo nokta sayısıdır (367,043 benzersiz konum).

## 2. Sanayi / statik NASA etiketi ile bağımsız haritaların uyumu

- **sanayi** (27,012 nokta, 26,969 benzersiz konum): OSM bayrağı nokta 92.5% / konum 92.5%; WC çoğunluk yapılaşmış 63.4% / 63.4%; WC yapılaşmış payı ≥%20 75.7% / 75.7%; **OSM veya WC-yapılaşmış 93.4% / 93.4%**.
- **statik_nasa** (328,379 nokta, 325,182 benzersiz konum): OSM bayrağı nokta 89.8% / konum 89.9%; WC çoğunluk yapılaşmış 84.6% / 84.5%; WC yapılaşmış payı ≥%20 91.0% / 90.9%; **OSM veya WC-yapılaşmış 96.5% / 96.5%**.
- **kalici_belirsiz** (6,208 nokta, 6,206 benzersiz konum): OSM bayrağı nokta 57.8% / konum 57.8%; WC çoğunluk yapılaşmış 31.6% / 31.6%; WC yapılaşmış payı ≥%20 40.1% / 40.1%; **OSM veya WC-yapılaşmış 58.8% / 58.8%**.

Sanayi+statik_nasa birlikte: OSM veya WC çoğunluk yapılaşmış uyumu **%96.2 (nokta), %96.3 (benzersiz konum)**; OSM ya da WC yapılaşmış payı ≥%20 ile gevşetilirse %96.7 (nokta).

Temiz olaylar (302,863): OSM veya WC çoğunluk yapılaşmış **%8.3** (olası kaçırılmış sanayi; OSM tek başına %7.36, WC yapılaşmış tek başına %4.57); bunlardan OSM sanayi (kod 1) %5.59, taş ocağı %0.45, çöp sahası %0.27, santral %1.05. Yüksek FRP'li (frp_max ≥ 300 MW) temiz olaylarda: %1.4 (908 olay).

## 3. Belgelenmiş gerçek orman yangınları (gercek_dogrulama.json)

| olay | ad | durum | ağaç % | çalılık % | otlak % | tarla % | yapılaşmış % | ağaç+çalılık % | çoğunluk | OSM |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 426891 | Çeşme (Ildır) yangını, İzmir 2025 | temiz | 5 | 31 | 64 | 0 | 0 | 36 | otlak | yok |
| 307650 | Mersin yangınları, Aydıncık/Silifke/Gülnar bö | temiz | 22 | 31 | 47 | 0 | 0 | 53 | otlak | yok |
| 428617 | Orhaneli–Harmancık yangını (Bursa, Temmuz 202 | temiz | 71 | 5 | 24 | 0 | 0 | 76 | ağaç | yok |
| 426211 | Taraklı (Sakarya) → Gölpazarı (Bilecik) yangı | temiz | 78 | 0 | 20 | 2 | 0 | 78 | ağaç | yok |
| 426343 | Akhisar (Karaköy) yangını, Manisa 2025 | temiz | 82 | 5 | 13 | 0 | 0 | 87 | ağaç | yok |
| 426373 | Seferihisar (Doğanbey) – Menderes (Kuyucak) y | temiz | 55 | 35 | 10 | 0 | 0 | 90 | ağaç | yok |
| 429406 | Silifke yangını (Mersin, Ağustos 2025) | temiz | 71 | 25 | 3 | 0 | 0 | 96 | ağaç | yok |
| 459190 | Aksu–Kepez (Karaöz) yangını, Antalya 2026 | temiz | 95 | 1 | 4 | 0 | 0 | 96 | ağaç | yok |
| 307718 | Manavgat yangın kompleksinin doğu kolu / Günd | temiz | 95 | 1 | 4 | 0 | 0 | 96 | ağaç | yok |
| 307866 | Kavaklıdere–Yatağan–Yılanlı yangını (Muğla, 2 | temiz | 98 | 0 | 0 | 0 | 2 | 98 | ağaç | yok |
| 454809 | Seydikemer (Bayır) yangını, Muğla 2026 | temiz | 86 | 12 | 3 | 0 | 0 | 98 | ağaç | yok |
| 307807 | Milas (Beyciler) – Bodrum (Mazı/Gökpınar) yan | temiz | 96 | 3 | 0 | 0 | 0 | 99 | ağaç | yok |
| 307626 | Manavgat orman yangını (Antalya, 2021) | temiz | 90 | 9 | 1 | 0 | 0 | 99 | ağaç | yok |
| 426617 | Antakya (Karaali) yangını, Hatay 2025 | temiz | 100 | 0 | 0 | 0 | 0 | 100 | ağaç | yok |
| 307744 | Köyceğiz yangını (Muğla, 2021) | temiz | 93 | 7 | 0 | 0 | 0 | 100 | ağaç | yok |
| 427937 | Şarköy (Tekirdağ) → Gelibolu/Kavakköy (Çanakk | temiz | 100 | 0 | 0 | 0 | 0 | 100 | ağaç | yok |
| 428217 | Geyve (Sakarya) → Osmaneli (Bilecik) yangını, | temiz | 100 | 0 | 0 | 0 | 0 | 100 | ağaç | yok |
| 307723 | Marmaris yangını (Muğla, 2021) | temiz | 100 | 0 | 0 | 0 | 0 | 100 | ağaç | yok |
| 324714 | Marmaris (Bördübet/Hisarönü) yangını, 2022 | temiz | 99 | 1 | 0 | 0 | 0 | 100 | ağaç | yok |

19 olayda veri var. Ağaç payı: medyan 93, min 5, 25. yüzdelik 74. Ağaç+çalılık: medyan 98, min 36, 25. yüzdelik 88.
- ağaç+çalılık ≥ %30: gerçek orman yangınlarının 100% (19/19); tüm temiz olayların 6%
- ağaç+çalılık ≥ %40: gerçek orman yangınlarının 95% (18/19); tüm temiz olayların 5%
- ağaç+çalılık ≥ %50: gerçek orman yangınlarının 95% (18/19); tüm temiz olayların 4%
- ağaç+çalılık ≥ %60: gerçek orman yangınlarının 89% (17/19); tüm temiz olayların 3%
- ağaç ≥ %20: gerçek orman yangınlarının 95% (18/19); tüm temiz olayların 8%
- ağaç ≥ %30: gerçek orman yangınlarının 89% (17/19); tüm temiz olayların 6%
- ağaç ≥ %40: gerçek orman yangınlarının 89% (17/19); tüm temiz olayların 4%
- ağaç ≥ %50: gerçek orman yangınlarının 89% (17/19); tüm temiz olayların 3%

**Öneri (rakamlara dayalı):** 'orman/çalılık yangını' sınıfı için p_tree + p_shrub ≥ %30 (belgeli 19 olayın 19'i geçer; en düşük ağaç+çalılık payı %36). Tüm temiz olayların %6.2'i bu sınıfa girer. Sıkı 'orman' için p_tree ≥ %50 (belgeli olayların 17/19'ü; Ege/Akdeniz maki-çalılık yangınlarında ağaç payı düşük kalır, bu yüzden çalılığı da sayan eşik daha güvenlidir). Belgeli 19 olay küçük bir örneklemdir; eşik bir ölçüt önerisidir, kesin sınır değildir. Kaynaksız Adana 2012 (99294) olayı tarla çıktığı için (WC tarla %96) istatistiğe alınmadı.

## 4. En yüksek FRP'li 10 temiz olay (≥2 tespit)

| evid | yıl | frp_max | tespit | ağaç % | çalılık % | tarla % | yapılaşmış % | çoğunluk | OSM |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 307626 | 2021 | 4856 | 6740 | 90 | 9 | 0 | 0 | ağaç | yok |
| 459190 | 2026 | 4808 | 629 | 95 | 1 | 0 | 0 | ağaç | yok |
| 351200 | 2023 | 3773 | 344 | 85 | 5 | 2 | 0 | ağaç | yok |
| 46911 | 2008 | 3336 | 4 | 87 | 12 | 0 | 0 | ağaç | yok |
| 426211 | 2025 | 3248 | 1255 | 78 | 0 | 2 | 0 | ağaç | yok |
| 112395 | 2013 | 3123 | 29 | 92 | 7 | 0 | 0 | ağaç | yok |
| 428217 | 2025 | 3021 | 1032 | 100 | 0 | 0 | 0 | ağaç | yok |
| 280895 | 2020 | 2788 | 226 | 0 | 13 | 0 | 0 | otlak | yok |
| 33943 | 2006 | 2733 | 49 | 93 | 7 | 0 | 0 | ağaç | yok |
| 454809 | 2026 | 2639 | 561 | 86 | 12 | 0 | 0 | ağaç | yok |
