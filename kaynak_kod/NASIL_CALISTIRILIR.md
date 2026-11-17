# Kaynak kod: veri hattını baştan çalıştırma

Bu klasör, `arayuz/` içindeki uygulamanın kullandığı her sayıyı ham NASA FIRMS verisinden üreten kodun tamamıdır. Herkes buradan tüm sonuçları yeniden üretebilir ve kabul testlerini (C01–C25) çalıştırabilir.

| Klasör | İçerik |
|---|---|
| `src/pipeline/` | Ham FIRMS → `points.parquet` (şema v1), gözlem kapsamı (`coverage.parquet`), FIRMS API çekici |
| `src/cleaning/` | Durum etiketleri (temiz / deniz / volkan / statik_nasa / sanayi / düşük güven / anız / kalıcı belirsiz), sanayi eşiklerinin LOYO kalibrasyonu, olay düzeyi anız, WorldCover doğrulaması |
| `src/clustering/` | Uzay–zaman kümeleme (olay tablosu), kaba kuvvet karşılaştırması (C03) |
| `src/harmonize/` | MODIS ayak izi eşleştirmesi, güven eşlemesi, MODIS-eşdeğer seri, yöntem yarışı, LOYO, sıçrama testi |
| `src/analytics/` | Günlük ve aylık tablolar, ay profili, anomali, takvim çıktıları |
| `src/config/` | Tüm eşikler (`esikler.json`, `config.py`); kodda sabit eşik yok |
| `tools/` | `check_all.py` (C01–C25 kabul testleri), `build_metrics.py` (`reports/metrics.json`), `build_reports.py` |
| `audit/` | Bağımsız yeniden hesap betikleri ve sonuçları, denetim bulguları, kalibrasyon çıktıları |
| `docs/` | Görev metni, istekler, kabul kriterleri, veri sözleşmesi, yöntem belgeleri |
| `reports/` | Rapor şablonları, metrik parçaları ve `metrics.json` |

Pakette olmayanlar (boyut nedeniyle):
- `data/raw/`: ham FIRMS dosyaları, yaklaşık 127 MB.
- `data/interim/` ve `data/processed/`: türetilmiş tablolar, yaklaşık 140 MB. Aşağıdaki adımlar bunları yeniden üretir.

Uygulamanın güncel hali bu klasörde değil, `../arayuz/` klasöründedir (v2.2). Uygulama verisini üreten betik `../arayuz/build_app_data.py` dosyasıdır.

## 1. Ortam

Python 3.11 veya üstü. Kodun içe aktardığı paketler: `pandas`, `numpy`, `pyarrow`, `scipy`, `openpyxl` (xlsx okuma). WorldCover doğrulaması için ayrıca `rasterio` gerekir; bu adım isteğe bağlıdır.

```
pip install pandas numpy pyarrow scipy openpyxl
```

## 2. Ham veri

NASA FIRMS arşivinden Türkiye için şu ürünleri indirip `data/raw/` klasörüne koyun:
- MODIS C6.1
- VIIRS 375 m (S-NPP, NOAA-20, NOAA-21)

Kaynak: https://firms.modaps.eosdis.nasa.gov/download/

Kullanılan dosyaların listesi ve sayıları `data/README.md` dosyasındadır: 27 yıl, 1.414.674 satır. Ham dosyalar salt okunurdur; hiçbir satır silinmez.

## 3. Çalıştırma sırası

Komutları bu klasörün kökünden çalıştırın. Sıra yöntem belgelerinden alınmıştır: `docs/04_VERI_SOZLESMESI_TASLAK.md`, `docs/temizlik_yontemi.md`, `docs/kumeleme_yontemi.md`, `docs/harmonizasyon_yontemi.md`, `docs/takvim_yontemi.md`.

```
python src/pipeline/build_points.py        # ham -> data/processed/points.parquet
python src/pipeline/build_coverage.py      # uydu x gün gözlem kapsamı (çıkarım)
python src/cleaning/kalibrasyon.py         # sanayi eşikleri, LOYO ile
python src/cleaning/build_status.py        # nokta durum etiketleri
python src/clustering/build_events.py      # olay tablosu (uzay-zaman kümeleme)
python src/cleaning/build_status.py        # ikinci koşu: olaylar artık var, olay düzeyi anız uygulanır
python src/harmonize/run_all.py            # eşleştirme -> güven -> MODIS-eşdeğer seri, LOYO, sıçrama
python src/analytics/run_all.py            # takvim tabloları, profil, anomali
python tools/build_metrics.py              # tüm metrik parçaları -> reports/metrics.json
python tools/check_all.py                  # kabul testleri C01-C25 -> audit/check_results.json
```

İsteğe bağlı adımlar:
- `python src/cleaning/worldcover.py`: ESA WorldCover ile bağımsız arazi örtüsü kontrolü. `rasterio` ve internet gerekir.
- `python src/cleaning/olay_aniz.py --yaz`: olay düzeyi anızı tek başına uygular. İdempotenttir.

Testler:
```
python src/pipeline/test_pipeline.py
python src/cleaning/test_cleaning.py
python src/clustering/bruteforce_check.py
python src/harmonize/test_harmonize.py
python src/analytics/test_analytics.py
```

Not: `build_status.py` önce, `build_events.py` sonra çalışır. `build_status.py`, `events.parquet` varsa olay düzeyi anızı kendisi uygular (`docs/temizlik_yontemi.md`). Kümeleme girdisi {temiz, anız} olduğu için anız yazmak olay yapısını değiştirmez. Bu nedenle ikinci `build_status.py` koşusu, olay düzeyi anızı yerleştirmek içindir.

## 4. Uygulama verisi

`../arayuz/build_app_data.py`, `data/processed/` tablolarını uygulamanın okuduğu `.bin` ve `.json` dosyalarına çevirir. Betik ilk yazıldığı düzende `src/app/` altında duruyordu; bu yüzden içindeki `ROOT`, `P` ve `OUT` yolları o düzene göredir (`ROOT = parents[2]`). Bu klasörden çalıştırmak için betiği `src/app/` altına kopyalayın ya da bu üç yolu düzenleyin.

## 5. Doğrulanmış durum

Asıl çalışma dizinindeki son koşu (2026-11-13) sonuçları:
- `check_all.py`: 25 geçti, 0 kaldı, 0 atlandı (`../belgeler_ve_denetim/denetim_gunlugu.md`).
- Bağımsız yeniden hesap (`audit/f1`, `audit/f2`): ölçülen sayım metriklerinde fark 0.

Bu paket klasöründe veri hattı yeniden koşturulmadı; ham veri pakette olmadığı için. Kod, çalıştırıldığı haliyle değiştirilmeden kopyalanmıştır.
