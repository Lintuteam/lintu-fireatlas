# Mevcut Durum (`../demo`) ve Doğrulanmış Bulgular

Bu bölümdeki sayılar 12–13 Kasım 2026'da `FireCore`'u (`../demo/app.js`) gerçek `../demo/data/fire_data.js` üzerinde çalıştırarak elde edildi (varsayılan ayarlar: N=10, M=4, güven=Tümü, anız ayları Ağu–Ara, F=15 MW, D=1 km, H=24 saat, anız hariç). Bunları yeniden üretemiyorsan **dur ve koordinatöre bildir**.

## Demo ne yapıyor

- **Python hattı** (`pipeline/build_data.py`): MODIS ve VIIRS CSV'lerini ortak şemaya çevirir, her noktaya il, `cellDays`, `cellMonths` ekler, tek `fire_data.js` yazar.
- **Tarayıcı** (`app.js` içindeki saf `FireCore`): `computeStatus` her noktaya durum etiketi verir (deniz, sanayi, düşük güven, anız, temiz). `cluster` temiz noktaları mesafe ≤ D ve süre ≤ H kuralıyla union-find ile tek olaya birleştirir. İki sensör **ortak kümelenir**.
- **Kurallar:** deniz/volkan `type ∈ {1,3}`; sanayi `type==2 || (cellDays ≥ N && cellMonths ≥ M)`; anız: olay ≤3 tespit, ≤12 saat, anız ayında başlamış, en yüksek FRP < F.

## Doğrulanmış sayılar (Türkiye, 2 Oca 2025 – 11 Kas 2026)

| Ölçüm | Değer |
|---|---|
| Girdi | MODIS 9.499, VIIRS arşiv 21.555, VIIRS NRT 19.296; toplam 50.350 |
| Huni (Tümü) | 50.350 → deniz −200 → sanayi −14.423 → güven 0 → anız −14.043 → 21.684 temiz tespit → **10.088 olay** |
| Huni MODIS | 9.499 → 6.440 → 4.566 olay |
| Huni VIIRS | 40.851 → 14.997 → 5.527 olay |
| İzmir | 2.623 ham → 327 olay (sanayi −1.906) |
| Hatay / Konya / Şanlıurfa / Muğla | 203 / 395 / 2.162 / 53 olay |
| Muğla 29 Temmuz 2026 | 97 tespit = 1 aktif olay |
| Hakkari 10 Kasım 2025 | 33 tespit / 1 olay (olay toplamı 100 tespit: 20 MODIS + 80 VIIRS) |
| D duyarlılığı | D=0,5 → 12.065, D=1 → 10.088, D=2 → 8.504 olay (yaklaşık %30 oynama) |
| Anızı dahil et | 21.338 olay |
| Ay başlığı (ayda başlayan olay) | Haziran 2025: 1.168, Haziran 2026: 1.132; Temmuz 2025: 799, Temmuz 2026: 1.301 |
| Kas–Ara 2025 çakışması (783 temiz olay) | ikisi de gördü 146; yalnız MODIS 248; yalnız VIIRS 389 |
| Aynı dönem, sensörler ayrı kümelenince | MODIS 423, VIIRS 548 olay; ortak 10.088 ≤ ayrı 10.276 |
| Piksel alanı (km²) | MODIS min 1,0, medyan 1,32, %95 5,27, maks 9,6; VIIRS 0,137 / 0,198 / 0,44 / 0,624 |
| `type` | NRT'nin 19.296 noktasında `type` yok (−1) |

Testler: JS testleri (`tests/core.test.js`) ve Python testleri (`pipeline/test_build.py`) geçiyor.

## Çözülenler ve çözülmeyenler

- **Çözüldü:** aynı yangının iki sensörde çifte sayımı (ortak kümeleme; kaba kuvvetle doğrulandı), çok günlü yangının tek olay sayılması, "veri yok" günlerinin sayıma girmemesi.
- **Çözülmedi:** sensör hassasiyet farkı (VIIRS küçük yangınları görür). 2025 (MODIS) ile 2026 (VIIRS) karşılaştırılamıyor. Demo bunu **gizlemeden uyarıyor**, düzeltmiyor.
- **Şüphe (ölçülmedi, hipotez):** Çakışmada MODIS olaylarının yalnızca ~%37'sini VIIRS de gördü. VIIRS'in bu kadar kaçırması beklenmez. Muhtemel neden eşleştirme mesafesi: MODIS pikseli kenarda büyür, merkezi VIIRS noktasından 1 km'den fazla uzakta kalabilir. Test edilmeli.
- **Etkileşim riski (ölçülmedi):** Zincirleme birleşme yoğun tarım bölgesinde bitişik küçük yakmaları büyük olaya çevirip anız kuralındaki "olay ≤3 tespit" şartından çıkarabilir.

## Dikkat: demodaki tutarsız ve eski belgeler

- `../demo/RAPOR.md` gövdesinde eski sayılar var (11.294 olay, 22.850 temiz). Güncel değer **10.088 / 21.684**. Revizyon 3 kutusu doğru.
- `RAPOR.md` anız ayları "Ağu–Kas" diyor, kod **Ağu–Ara**.
- `RAPOR.html` ve `RAPOR.pdf` eski sürüm; kullanma.
- `area` ve `dn` sütunları veride var, hiçbir hesapta kullanılmıyor.
- Gün/ay hesabı sabit UTC+3 (yalnız Türkiye için doğru).

## Geçmiş denetimden dersler

- **B-01..B-05:** İlk sürümde iki sensör ölçeklenerek birleştirilmişti (kış oranı r=2,464 yaza uygulandı); bu, olay sayısını tespit sayısından büyük gösterdi. Ölçekleme kaldırıldı. **v2 aynı türde hataya düşmemeli**, bu yüzden oranlar sınanarak (bölge, mevsim, büyüklük) ve dışarıda bırakma testiyle kurulmalı.
- Gün görünümü başlığı ile tablonun aynı olay kümesini kullanması, güvenin kategorik olması gibi düzeltmeler demoda var, korunmalı.

## Dış bağlam (kaynaklar doğrulanmalı, tarihler 2026 itibarıyla)

- MODIS C6.1 kaydı Terra için Kasım 2000'den, Aqua için Temmuz 2002'den; VIIRS 375 m (S-NPP) 20 Ocak 2012'den (NASA ARSET soru-cevap belgesi).
- Terra MODIS 26 Mart 2026'da bekleme moduna alındı: https://www.earthdata.nasa.gov/data/alerts-outages/terra-modis-placed-standby-mode
- NASA, Terra MODIS'in Ocak 2027'de, Aqua MODIS'in yaklaşık Eylül 2027'de biteceğini planlıyor: https://atmosphere.copernicus.eu/drifting-away-modis-cams-global-fire-assimilation-system
- Suomi NPP'nin FIRMS aktif yangın verisi üretimi 2 Kasım 2026'da duruyor (yerine NOAA-20 ve NOAA-21): https://www.earthdata.nasa.gov/news/blog/transitioning-from-s-npp-viirs-omps-what-nasa-firms-users-need-know
- FIRMS uydu geçiş şeridi (swath outline) ürünü yayımlıyor: https://www.earthdata.nasa.gov/news/blog/new-firms-data-product-satellite-swath-outlines
- Bu bilgiler güçlü bir gerekçe: harmonizasyon, MODIS'ten VIIRS'e geçişte sürekli bir seri kurmanın tam kendisi. Kullanmadan önce bağlantıları yeniden kontrol et.
- FIRMS API kota ve tarih aralığı sınırları **doğrulanmadı**; resmî dokümandan teyit et.
