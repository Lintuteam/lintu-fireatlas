# Veri Sözleşmesi — KESİN v1 (2026-11-13)

> Dosya adı geriye uyumluluk için "TASLAK" olarak kaldı; içerik **kesindir (şema v1)**.
> Gerçek veriye bakılarak F0'da koordinatör tarafından kesinleştirildi. Değişiklik geçmişi: `audit/degisim_gunlugu.md`.
> Değişiklik yalnız koordinatör onayıyla yapılır; sütun anlamı değişirse şema sürümü artar.

**Basitçe:** Bu belge, bütün ajanların aynı dili konuşması için yazılmış "sözlük ve kurallar"dır. Bir ajan "conf_cls" dediğinde diğeri ne anlama geldiğini kesin bilir.

**Teknik olarak:** Ham Excel → tek bir sütunlu (Parquet) nokta tablosu; üstüne olay tablosu, kapsam tablosu ve toplu tablolar. Her tablo `meta` (betik, ham dosyalar, SHA-256, şema sürümü) taşır.

## 1. Girdi: ölçülmüş envanter (data/raw, salt okunur — K6)

Kaynak: `data/raw/FIRMS_Turkiye_Excel/FIRMS_Turkiye_<YIL>.xlsx` (27 dosya, 2000–2026). Her dosyanın ilk sayfası `Yangın verileri` (20 sütun); diğer sayfalar sözlük/açıklama. Envanter 2026-11-13'te pandas ile sayıldı (**ölçüldü**).

| Uydu | Sensör | İlk | Son | Satır | Not |
|---|---|---|---|---|---|
| Terra | MODIS | 2000-11-01 | 2026-11-12 | 136.626 | 2026-09 sonrası NRT |
| Aqua | MODIS | 2002-07-04 | 2026-11-12 | 123.081 | 2026-09 sonrası NRT |
| Suomi NPP | VIIRS | 2012-01-20 | 2026-11-02 | 637.595 | 2026-08 sonrası NRT; 2 Kas 2026'da biter |
| NOAA-20 | VIIRS | 2018-04-01 | 2026-11-12 | 360.942 | 2026-08 sonrası NRT |
| NOAA-21 | VIIRS | 2023-03-01 | 2026-11-12 | 156.430 | 2026-08 sonrası NRT |
| **Toplam** | | | | **1.414.674** | MODIS 259.707, VIIRS 1.154.967 |

Ölçülmüş gerçekler:
- Her uydu, aktif olduğu aralıkta **hiç boş ay içermiyor**.
- Tam yinelenen satır **0**; (zaman, enlem, boylam, uydu) anahtarında yinelenen **0**.
- **NRT ile arşiv örtüşmüyor:** NRT yalnız arşivin bittiği tarihten sonra başlıyor (VIIRS 2026-08-01, MODIS 2026-09-01). Aynı uydu+dakika+<0,005° eşleşen NRT satırı 0/61.147.
- NRT satırlarında `type` boş (61.147 satır: VIIRS 58.465, MODIS 2.682). Statik kaynak bayrağı bu dönemde **yok**; temizlik çok yıllı hücre kalıcılığıyla ayırmalı.
- Zaman damgası yılı = dosya yılı (fark 0). Tüm sütunlar dolu (yalnız `type` NRT'de boş).
- Kapsam kutusu: enlem 35,82–42,08, boylam 25,69–44,80.
- MODIS `confidence_cls` FIRMS kuralıyla birebir: low 0–29, nominal 30–79, high 80–100.
- VIIRS `type=2` (statik kara kaynağı) oranı yıllara göre %15–%41 — büyük bir pay; arayüzde ayrı gösterilmeli.
- 184.902 VIIRS satırında parlaklık kanalı `VIIRS_I4_ornek_esleme` (arşiv dosyalarında brightness→I4 eşlemesi örneğe dayalı çıkarım). Parlaklık sıcaklığı bu satırlarda **tahmini** etiketlidir; çekirdek hesaplar (sayım, FRP) bundan etkilenmez.
- Dikkat (**doğrulanmadı**): `02_MEVCUT_DURUM.md` Terra MODIS'in 26 Mart 2026'da beklemeye alındığını söylüyor, ama veride Terra tespitleri 2026-11-12'ye kadar sürüyor. `veri-hatti` kaynağı yeniden kontrol eder.

## 2. Nokta tablosu — `data/processed/points.parquet` (şema v1)

Her ham satır **tam bir** satır olur (K3). Satır sayısı = 1.414.674 (C01 bunu `data/processed/inventory.json` → `raw_rows_total` ile karşılaştırır).

| Sütun | Tip | Kaynak / anlam |
|---|---|---|
| `pid` | int64 | Kalıcı nokta kimliği (dosya yılı × 10⁷ + satır no) |
| `t_utc` | timestamp[UTC] | `acq_datetime_utc` (depolama UTC — K11) |
| `day_tr` | date | TR takvim günü = (t_utc + 3 saat).date (K11; 20:59Z ve 21:00Z farklı gün). Bilinen sınırlama: 2016 öncesi TR kış saati UTC+2 idi; sabit UTC+3 kuralı denetçi ölçümüyle 88 satırın gününü kaydırıyor (**ölçüldü**, ihmal edilebilir, bilinçli karar) |
| `src_year` | int16 | Dosya yılı (kırpma yok) |
| `lat`, `lon` | float64 | WGS84 |
| `sensor` | category | `MODIS` / `VIIRS` |
| `sat` | category | `Terra`, `Aqua`, `SNPP`, `N20`, `N21` (ham `satellite_raw` `N`/`SNPP` → `SNPP`). Bilinmeyen kod sayılır, raporlanır, atılmaz |
| `frp` | float32 | MW |
| `scan`, `track` | float32 | km |
| `area` | float32 | `pixel_area_km2` (= scan × track) |
| `conf_raw` | string | MODIS "0"–"100", VIIRS "l"/"n"/"h" |
| `conf_cls` | category | `dusuk` / `nominal` / `yuksek` — **yalnız** `src/config/esikler.json → guven` eşlemesinden (K10) |
| `bt_mir`, `bt_tir` | float32 | K; `bt_estimated` (bool) = kanal eşlemesi örneğe dayalı mı |
| `dn` | category | `D` / `N` |
| `type` | int8 | 0 bitki örtüsü, 1 volkan, 2 statik kara, 3 açık deniz, **-1 = yok (NRT)** |
| `version` | string | ör. `6.2`, `61.03`, `2`, `2.0NRT` |
| `src_product` | category | `archive` / `nrt` (`version` içinde `NRT` ⇒ nrt) |
| `src_file` | string | Ham `source_file` (izlenebilirlik) |
| `il` | category | İl adı (demodaki il sınırından; kaynak belirtilir) |
| `bolge` | category | `il` (il çokgeni içi) / `kiyi` (çokgen dışı, sınıra ≤ B km; il = en yakın il) / `yurt_disi`; B `esikler.json`'da. Ölçüldü: il 1.400.632, kiyi 14.042, yurt_disi 0 |
| `mcell` | string | Eşleştirme birimi kimliği (bkz. §5) — `harmonizasyon` doldurur |
| `status` | category | `temiz` / `deniz` / `volkan` / `statik_nasa` / `sanayi` / `dusuk_guven` / `aniz` / `kalici_belirsiz` — `temizlik` doldurur |
| `event_id` | int64 | Ortak olay kimliği (iki sensör birlikte) — `kumeleme` doldurur; temiz olmayanlar -1 |

Tablo F1'de ilk 18 sütunla yazılır; `mcell`, `status`, `event_id` F2'de **ayrı yan tablolar** olarak (`points_<alan>.parquet`, `pid` anahtarlı) yazılır ve aynı ajanın dosyasına iki ajan yazmaz.

## 3. Olay tablosu — `data/processed/events.parquet`
`event_id, t_start_utc, t_end_utc, day_tr_start, lat, lon (FRP ağırlıklı merkez), n_modis, n_viirs, frp_sum, frp_max, il, match_class (ortak | yalniz_modis | yalniz_viirs), status`. `match_class` yalnız iki sensörün de geçtiği dönem/gözlemde anlamlıdır; diğerleri `tek_sensor_donemi`.

## 4. Gözlem kapsamı — `data/processed/coverage.parquet`
`sat, day_tr, observed (bool), n_overpass, source (swath | çıkarım)`. Swath ürünü yoksa geçiş saatlerinden çıkarım yapılır ve `source='çıkarım'`, etiket **tahmini**. Sahte bulut yok (K2).

## 5. Eşleştirme birimi (harmonizasyon ↔ kümeleme ortak tanımı)

**Basitçe:** MODIS bir yangını büyük bir "kare" içinde görür, VIIRS aynı yerde küçük "kareler" görür. Her VIIRS noktasını, yakınındaki MODIS'in büyük karesine bağlıyoruz; böylece "MODIS'te 1, VIIRS'te 4" sorunu tek yangın olur.

**Teknik olarak:** Birim = **MODIS piksel ayak izi**: MODIS tespit merkezinde, `scan` (enine) × `track` (boyuna) km dikdörtgen + VIIRS yarım piksel tamponu. Sabit ızgara yerine ayak izi seçildi çünkü MODIS pikseli tarama kenarında 4,8 km'ye kadar büyüyor (ölçüldü: scan maks 4,8, %95 3,2 km). MODIS tespiti olmayan yerlerde (yalnız VIIRS) yedek birim **sabit 1 km ızgara (0,01°)**. Zaman penceresi ve D/H değerleri `esikler.json`'da. İki sensörün en yakın eşzamanlı çifti **Aqua (13:30) ↔ SNPP/N20/N21 (13:30)** geçişleridir; kalibrasyon çiftleri öncelikle buradan kurulur.

## 6. Toplu tablolar — `data/processed/agg/`
- `daily.parquet`: il × day_tr × sensor/seri: temiz tespit, aktif olay, sınıf kırılımı, FRP.
- `monthly.parquet`: il × yıl × ay; ay medyanı ve dağılım (`takvim-analiz`).
- `harmonized.parquet`: MODIS-eşdeğer seri, ham VIIRS serisi, belirsizlik bandı (`harmonizasyon`).

## 7. Yapılandırma — `src/config/esikler.json`
Tüm eşikler (N, M, F, D, H, anız ayları, eşleştirme tamponu, güven eşlemesi) değer + gerekçe + kaynak ile burada (K9, K10). Kod sabit eşik yazmaz; C08 bunu tarar.

## 8. Çıktılar
- `reports/metrics.json`: tek doğruluk kaynağı. Her metrik `{value, unit, tanim, betik, veri_surumu, etiket}`.
- `audit/check_results.json`: `tools/check_all.py` sonucu.
- CSV dışa aktarma: UTF-8 BOM, `t_utc` ve `t_tr` sütunları, formül enjeksiyonu önlemi (C17).

## 9. Kurallar
- Ham → nokta tablosu tekrar üretilebilir (`python src/pipeline/build_points.py`).
- `data/interim/raw_all.parquet` F0 envanterinde üretilen hızlı okuma önbelleğidir (ham 20 sütun + `_file`); kaynak hâlâ `data/raw`.
