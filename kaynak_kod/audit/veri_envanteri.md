# Veri envanteri (veri-hatti)

## Ölçülen envanter (2026-11-13; kaynak: `data/processed/inventory.json`, `points.meta.json`)

**Basitçe:** 27 yıllık dosyada (2000–2026) toplam 1.414.674 yangın tespiti var. Hiçbiri atılmadı; her biri tabloda tam bir satır.

**Teknik olarak:**
- Ham satır: 1.414.674 (MODIS 259.707, VIIRS 1.154.967); points.parquet satırı: 1.414.674.
- Uydu: Aqua 123.081, N20 360.942, N21 156.430, SNPP 637.595, Terra 136.626.
- NRT satırı: 61.147 (type boş = -1: 61.147). Yinelenen satır: 0.
- type: -1=61.147, 0=1.029.262, 1=5, 2=315.439, 3=8.821.
- Bilinmeyen uydu kodlu satır: 0; bilinmeyen güven değeri: 0; ham sınıfla çelişen güven eşlemesi: 0.
- Bölge (`bolge`, il çokgenleri birleşimi = Türkiye sınırı; il sınırı demodan, cihadturhan/tr-geojson, lisansı doğrulanmadı): il içi 1.400.632, kıyı (çokgen dışı ama sınıra ≤ B=5 km; il = en yakın il) 14.042, yurt dışı 0. Çokgen dışı noktaların sınıra en büyük uzaklığı 3,68 km, medyan 0,39 km: veri zaten ülke sınırıyla kırpılmış, "komşu ülke karışımı" ölçülmedi (0 satır). Kocaeli kıyısı (İzmit Körfezi) 3.747 satır `kiyi` + Kocaeli. İlişki: NASA `type=3` (açık deniz) 8.821 satırın 6.336'sı il içi, 2.485'i kıyı; yani type=3 çokgenin kaba olmasından dolayı denize taşan noktaları da içerir, ikisi birbirinin yerine kullanılamaz.
- Parlaklık kanalı tahmini (`bt_estimated`): 184.902 VIIRS satırı.
- Yıl × uydu satır sayısı:

| Yıl | Aqua | N20 | N21 | SNPP | Terra | Toplam |
|---|---|---|---|---|---|---|
| 2000 | 0 | 0 | 0 | 0 | 496 | 496 |
| 2001 | 0 | 0 | 0 | 0 | 5.162 | 5.162 |
| 2002 | 2.412 | 0 | 0 | 0 | 4.474 | 6.886 |
| 2003 | 3.671 | 0 | 0 | 0 | 4.062 | 7.733 |
| 2004 | 3.734 | 0 | 0 | 0 | 4.167 | 7.901 |
| 2005 | 3.966 | 0 | 0 | 0 | 4.337 | 8.303 |
| 2006 | 4.389 | 0 | 0 | 0 | 5.070 | 9.459 |
| 2007 | 4.049 | 0 | 0 | 0 | 4.742 | 8.791 |
| 2008 | 3.040 | 0 | 0 | 0 | 3.124 | 6.164 |
| 2009 | 9.386 | 0 | 0 | 0 | 10.593 | 19.979 |
| 2010 | 6.486 | 0 | 0 | 0 | 7.167 | 13.653 |
| 2011 | 9.186 | 0 | 0 | 0 | 9.279 | 18.465 |
| 2012 | 3.443 | 0 | 0 | 35.462 | 3.672 | 42.577 |
| 2013 | 5.776 | 0 | 0 | 52.089 | 5.745 | 63.610 |
| 2014 | 3.351 | 0 | 0 | 33.276 | 3.474 | 40.101 |
| 2015 | 8.520 | 0 | 0 | 66.801 | 9.569 | 84.890 |
| 2016 | 6.550 | 0 | 0 | 57.581 | 7.041 | 71.172 |
| 2017 | 4.605 | 0 | 0 | 43.688 | 4.991 | 53.284 |
| 2018 | 3.855 | 34.719 | 0 | 37.316 | 4.232 | 80.122 |
| 2019 | 4.328 | 40.329 | 0 | 39.859 | 4.019 | 88.535 |
| 2020 | 4.187 | 43.688 | 0 | 44.396 | 4.647 | 96.918 |
| 2021 | 4.913 | 45.019 | 0 | 42.993 | 5.122 | 98.047 |
| 2022 | 3.056 | 29.290 | 0 | 26.567 | 2.633 | 61.546 |
| 2023 | 5.109 | 39.847 | 34.134 | 39.155 | 3.942 | 122.187 |
| 2024 | 6.030 | 52.071 | 49.193 | 47.005 | 6.060 | 160.359 |
| 2025 | 5.346 | 40.408 | 39.085 | 39.421 | 4.153 | 128.413 |
| 2026 | 3.693 | 35.571 | 34.018 | 31.986 | 4.653 | 109.921 |

- Ölçüm (build_points.py, bu makine): okuma 0.11 s, dönüşüm+il 12.44 s, yazma 1.24 s, toplam 13.78 s; zirve bellek 2060.7 MB; çıktı 38.7 MB (zstd, yıl bazlı row group).

Boşluk/örtüşme ayrıntısı: `docs/04_VERI_SOZLESMESI_TASLAK.md` §1 (boş ay yok, NRT-arşiv örtüşmesi yok; ölçüldü).


Gözlem kapsamı (kesinti çıkarımı, G=3, K=50, tahmini): 28.308 uydu-gün, 129 kesinti günü (18 çalışma), 2.873 kardeşsiz gün. SNPP 2022-07-27..08-10 yakalandı. Ayrıntı ve G=2/3/5 duyarlılığı: data/README.md.
