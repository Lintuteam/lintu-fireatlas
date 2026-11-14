# Ek kaynaklar değerlendirmesi (veri-hatti, 2026-11-13)

**Basitçe:** Ana veri (FIRMS tespitleri) tek başına "nerede ısı var" der. Bu ek kaynaklar "orası ne tür yer", "gerçekten yandı mı", "uydu orayı gördü mü" sorularına yardım eder. Hangisini kullandığımızı ve neyin kontrol edilemediğini burada açıkça yazıyoruz.

**Teknik olarak:** Etiketler K5: **doğrulandı** (bu oturumda resmî sayfadan okundu), **doğrulanmadı** (bellekten/ikincil kaynaktan; kullanmadan önce kontrol edilmeli).

| Kaynak | Ne işe yarar | Erişim | Lisans | Boyut | Bu projede |
|---|---|---|---|---|---|
| FIRMS Area API | Eksik/yeni tespitleri çekmek | `/api/area/csv/{KEY}/{SOURCE}/{bbox}/{1-5 gün}/{tarih}`; MAP_KEY gerekir | doğrulanmadı (FIRMS kullanım şartları) | KB–MB/istek | Betik hazır: `src/pipeline/firms_api.py` (kota 5000 işlem/10 dk, gün aralığı 1–5: **doğrulandı**). Anahtar yok, çalıştırılmadı |
| Satellite Swath Outlines (FIRMS) | Uydunun o gün bölgeyi geçip geçmediği | Yalnız harita arayüzünde ("Satellite Swath Outlines & Orbit Tracks"); Terra, Aqua, NOAA-20 listeli. Toplu indirme/API/WMS **belgelenmemiş** (**doğrulandı**: haber sayfasında yok). Geçmiş aralığı belirtilmemiş | doğrulanmadı | — | **Kullanılamıyor** (otomatik erişim yok). Yerine `coverage.parquet` = uydu operasyonel aralığı çıkarımı (tahmini). NASA'nın duyurduğu "31 günlük geçiş tahmini" aracı henüz yok ("coming soon") |
| Static Thermal Anomalies (statik kaynak) maskesi | Sanayi/yakım bacası gibi sabit sıcak noktaları ayıklamak | FIRMS/LANCE sayfasından bulunamadı (bu oturumda **doğrulanmadı**). Veride VIIRS `type=2` zaten mevcut (315.439 satır; NRT'de `type` boş) | doğrulanmadı | küçük | Önce veri içi `type=2` ve çok yıllı hücre kalıcılığı (temizlik ajanı). Harici maske erişilebilirse bağımsız doğrulama olarak eklenir |
| ESA WorldCover (10 m, 2020/2021) | Anız/orman/tarım/yerleşim ayrımı, bağımsız doğrulama | AWS açık veri / Earth Engine; Türkiye için karolar | CC BY 4.0 (**doğrulanmadı**, bellekten) | Türkiye için birkaç GB; 0,01° hücreye özetlenip küçültülür | Evet: temizlik ajanı bağımsız doğrulama için (kalibrasyondan ayrı, K4). İndirme için ayrıca onay gerekir |
| MCD64A1 (yanmış alan, 500 m, aylık) | "Tespit gerçekten yangın mıydı" için bağımsız referans | NASA LP DAAC / Earthdata girişi gerekir | NASA açık veri (**doğrulanmadı**) | Türkiye karoları ~yüzlerce MB | Opsiyonel: yıl dışarıda bırakma doğrulamasında referans. Gecikmeli üretilir (güncel ay yok) |
| Hava verisi (ERA5 vb.) | Rüzgâr/sıcaklık, aktivite açıklaması | Copernicus CDS, hesap gerekir | doğrulanmadı | büyük | Şimdilik kullanılmaz (kapsam dışı) |

## Terra MODIS 2026 durumu
- `02_MEVCUT_DURUM.md` "26 Mart 2026'da beklemeye alındı" diyor. **Bu iddia doğrulanamadı**; veride Terra tespiti 2026-11-12'ye kadar sürüyor (ölçüldü), Mart sonrası boşluk yok.
- Bulunan kaynak: CAMS bildirimi (Şubat 2026, ikincil): NASA Terra MODIS veri toplamayı Ocak 2027'de, Aqua'yı yaklaşık Eylül 2027'de bitirmeyi planlıyor. NASA Earthdata FIRMS duyurusu: Terra tek sabah geçişi (Aqua'dan ~3 saat önce); Suomi NPP FIRMS üretimi 2026-11-02 13:00 UTC'de duruyor (veriyle uyumlu: SNPP son tespit 2026-11-02, **ölçüldü**).
- Sonuç: "Mart 2026 standby" ifadesi belgelerden çıkarılmalı veya "doğrulanmadı" denmeli; Terra için planlı bitiş 2027 başı (ikincil kaynak, **doğrulanmadı**).

Kaynaklar: https://firms.modaps.eosdis.nasa.gov/api/area/ ; https://www.earthdata.nasa.gov/news/blog/new-firms-data-product-satellite-swath-outlines ; https://www.earthdata.nasa.gov/news/blog/transitioning-from-suomi-npp-viirs-omps-what-firms-users-need-know ; https://atmosphere.copernicus.eu/drifting-away-modis-cams-global-fire-assimilation-system
