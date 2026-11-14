# Takvim ve mevsimsel analiz yöntemi (takvim-analiz)

**Terim (K14):** Burada "aktivite" = tarihsel hotspot aktivitesidir. Yangın tehlikesi tahmini **değildir**.
Tüm sayılar `python src/analytics/run_all.py` ile veriden üretilir; metrikler `reports/metrics_parts/takvim_analiz.json` -> `reports/metrics.json`.

## Basitçe
- Her ilin her günü için "kaç sıcak nokta / kaç yangın olayı" defteri tutulur; yanına "o gün uydular gerçekten bakabildi mi?" yazılır. Bakılamayan gün "sıfır yangın" demek değildir.
- Bir ayın sayısı, bakılabilen günlerin hızı ay uzunluğuyla çarpılarak bulunur (kesinti günleri paydadan çıkar). Bir ay neredeyse hiç bakılamadıysa veya ay yarımsa hücre **boş** kalır; sıfır yazılmaz.
- "En yoğun ay" = geçmiş yılların o ayının **medyanı** en yüksek olan ay. İki ay birbirine çok yakınsa "ayırt edilemez" denir.
- Anomali: bir yılın bir ayı, **o yıl hariç** diğer yılların aynı ayıyla kıyaslanır (sınav sorusunu ders kitabından ayırmak gibi).
- Sensör farkı yok sayılmaz: yalnız sensör bileşimi sabit yıllar birbirine karşı kıyaslanır; VIIRS "uydu başına" normalleştirilir.

## Teknik olarak
**Girdiler:** `points.parquet`+`points_status.parquet` (nokta, status), `events.parquet` (olay, `day_tr_start`, status temiz/aniz), `coverage.parquet` (observed), `agg/harmonized.parquet` (MODIS-eşdeğer + bant; `birim`/`kume` sütunları varsa dört eşdeğer seri: `modis_esdeger`, `_aniz_dahil`, `olay_esdeger`, `olay_esdeger_aniz_dahil`).
**Zaman (K11):** ay/yıl `day_tr` (UTC+3) ile; 2025-12-31 21:00Z -> 2026-01-01. Yıl kırpılmaz.

**Tablolar (`data/processed/agg/`):** `daily.parquet` (il×gün, seyrek), `daily_kapsam.parquet` (gün başına işleyen/gözlem yapan uydu), `yil_bilgi.parquet`, `monthly.parquet` (birim×yıl×ay: ham ve `_kk` düzeltmeli sütunlar, bayrak; birim = TR, 7 bölge, 81 il; il toplamı = TR), `seri_aylik.parquet` (uzun), `profile.parquet` (ay profili), `ranking.parquet` (en yoğun aylar), `ranking_ham_temiz.parquet`, `anomaly_monthly.parquet`, `current_month.parquet`.

**Seriler:** `modis_ham`, `modis_temiz` (anız hariç, varsayılan), `modis_temiz_aniz_dahil`, `enerji_modis` (FRP, temiz), `viirs_*_ub` (uydu başına), `olay`, `olay_aniz_dahil`, `modis_esdeger*` (yalnız TR+bölge; il düzeyinde eşdeğer seri yok, tabaka bölgedir).

**Kesinti düzeltmesi (C06):** tahmin edici `Σ sayım(w>0) / Σ w × ay_uzunluğu`; w = gözlem yapan uydu / işleyen uydu. Hücre BOŞ: işleyen gün < ay uzunluğu (sensör başlangıcı/bitişi, veri sonu: 2026-11 gibi) veya kesinti payı > `takvim.kesinti_pay_max`. Sensör hiç işlemiyorsa (VIIRS<2012) NaN. Kanıt: `src/analytics/c06_kanit.py`, testler `test_kesinti_*`.

**Normal yıl:** tam yıl, sensör bileşimi referansla aynı (MODIS: Terra+Aqua -> 2003-2025; 2000-2002 Terra bayraklı hariç), geçiş yılları (2012, 2018, 2023) ve 2026 hariç (VIIRS ve olay serileri için). Eşdeğer seri geçiş yıllarında dahildir ama `sensor_gecis_yili` uyarısı ve belirsizlik bandı taşır.

**Profil/sıralama:** medyan, Q1, Q3, min, maks; n<2 ise medyan boş, n<`min_yil_medyan` ise `az_yil`. Sıralama ölçütü medyan; olay serilerinde sensör bileşimi yıllara göre değiştiği için ay payı medyanı. Ayırt edilemez: komşu göreli fark < `ayirt_edilemez_tol` (top-3 içinde) + yıl bootstrap top-3 olasılığı (`top_olasilik`, B ve tohum config'te). Ham ve temiz sıralama farkı: `ranking_ham_temiz.parquet`.

**Mevcut ay (U-16):** son veri gününe kadar ayın ilk D günü, geçmiş yılların AYNI ilk D günüyle (oran, yüzdelik, z). Kısmi ay açıkça `ayin_ilk_gunleri` + `kismi_ay_ilk_D_gun` uyarısı taşır. Veri yetersizse (`yetersiz_yil`/`az_yil`) uyarı.

**Anomali (K4):** log1p ölçeğinde sağlam z = (x - medyan)/max(1.4826·MAD, taban); normal = normal yıllar, **test yılı hariç** (leave-one-year-out); olay serilerinde yalnız aynı sensör bileşimli yıllar (2024-2026 için yeterli yıl yok -> `yetersiz_veri`). Eşik |z| >= 2. Eşdeğer seride bant alt/üst için z hesaplanır; işaret bantta değişirse `belirsiz_bant`. Pencere: aynı takvim ayı; serbest aralıkta aynı takvim günleri (+ en az 15 gün genişletme). Minimum veri: `min_yil_medyan`.

**Serbest aralık (N-03):** `src/analytics/query.py -> aralik_analiz(v, birim, seri, bas, bit)`; `mevcut_ay`, `ay_karsilastir`. `v = Veri.yukle()` (`veri.py`).

**Etiket (K5):** sayımlar ölçüldü; eşdeğer, uydu-başına, anomali ve sıralama kararlılığı tahmini.
**Sınırlar:** VIIRS uydu-başına normalleştirme doğrusal varsayımdır; olay serisinde anomali yalnız aynı era içinde; il düzeyinde eşdeğer seri yok.
Eşikler: `src/config/esikler.json -> takvim`.
