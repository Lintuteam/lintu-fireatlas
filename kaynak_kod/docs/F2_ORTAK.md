# F2 ortak kuralları (koordinatör, 2026-11-13)

Üç ajan (`harmonizasyon`, `temizlik`, `kumeleme`) paralel çalışır. Önce `CLAUDE.md`, `docs/04_VERI_SOZLESMESI_TASLAK.md` (KESİN v1) ve kendi ajan tanımını oku; `docs/01`, `docs/03`'ten yalnız ilgili kimlikleri.

## Girdiler (F1, denetlendi)
- `data/processed/points.parquet` — 1.414.674 satır, `pid` anahtarı, `bolge`, `il`, `day_tr`, `conf_cls`, `scan/track/area`, `type` (-1 = NRT'de yok).
- `data/processed/coverage.parquet` — sat × day_tr, `observed`, `source`, `etiket=tahmini`.
- `src/config/esikler.json` + `src/config/config.py` — eşikler ve güven eşlemesinin TEK yeri (K9/K10). Yeni eşik gerekiyorsa **kendi bölümüne** ekle (`harmonizasyon.*`, `temizlik.*`, `kumeleme.*`), gerekçe + kaynakla. Başka ajanın bölümünü değiştirme. Kodda sabit eşik yazma (C08 tarar: `conf... >= NN` deseni yasak, config.py'yi kullan).

## Sahiplik (aynı dosyaya iki ajan yazmaz)
| Ajan | Kod | Yan tablo / çıktı |
|---|---|---|
| temizlik | `src/cleaning/` | `data/processed/points_status.parquet` (`pid, status, status_neden`), `audit/dogrulama_seti.csv` |
| kumeleme | `src/clustering/` | `data/processed/points_event.parquet` (`pid, event_id`), `data/processed/events.parquet`, `src/clustering/bruteforce_check.py` (C03; başarıda çıkış 0) |
| harmonizasyon | `src/harmonize/` | `data/processed/points_mcell.parquet` (`pid, mcell`), `data/processed/agg/harmonized.parquet` |

Ortak metrikler: her ajan **yalnız** `reports/metrics_parts/<ajan>.json` yazar. Biçim:
```json
{"metrics": {"anahtar": {"value": 0, "unit": "", "tanim": "", "betik": "src/...", "veri_surumu": "points v1", "etiket": "ölçüldü|tahmini|doğrulanmadı"}},
 "sensitivity": {"D": [{"deger": 0.5, "olay": 0, "...": 0}]}}
```
Sonra `python tools/build_metrics.py` → `reports/metrics.json` (uyuşmazlık varsa hata verir). `tools/`, `data/raw`, `../demo`, `.claude/` değişmez.

## check_all'ın beklediği anahtarlar
- kumeleme: `events_joint_overlap`, `events_separate_overlap` (C04); `sensitivity.D`, `sensitivity.H` (≥3 değer, C12); `events.parquet` sütunları `event_id, match_class` (C05).
- harmonizasyon: `loyo_mape`, `loyo_r2`, `loyo_bias`, `loyo_ci95` ([alt, üst]), `loyo_method` ("leave-one-year-out ..."), `jump_raw_pct`, `jump_harm_pct`, `jump_null_ci95` ([alt, üst]), `equiv_overlap_bias`, `equiv_overlap_band` (C09–C11).
- temizlik: `sensitivity.N`, `sensitivity.M`, `sensitivity.F` (C12); `ref_precision`, `ref_recall` (C13, referans yoksa yazma — C13 ATLANDI olur ve iddia "doğrulanmadı").

## Bağımlılık çözümü (paralellik için)
- **kumeleme**, temizliği beklemez: `type ∈ {1,3}` (volkan/deniz) dışındaki **tüm** noktaları kümeler. Olayın durumu sonradan noktaların `status`'undan türetilir. Eşleştirme birimi sözleşme §5 (MODIS piksel ayak izi + VIIRS yarım piksel tamponu); kumeleme bunu kendi uygular, `mcell`'i beklemez.
- **temizlik** nokta düzeyi etiketleri (deniz, volkan, statik_nasa, sanayi, dusuk_guven, kalici_belirsiz) yazar ve anız **takvimini** (bölge × ay, yıl dışarıda bırakmayla) öğrenir. Olay düzeyindeki son "aniz" etiketi `events.parquet` hazır olunca ikinci adımda verilir (koordinatör tetikler). İlk teslimde anız adayları `status_neden`'de işaretli, `status='temiz'` olabilir.
- **harmonizasyon** tespit/hücre düzeyinde çalışır (güven yüzdelik eşleştirmesi, FRP tespit eşiği, eşdeğer seri, LOYO, sıçrama). Olay düzeyindeki harmonize seri ikinci adımda.

## Performans
1,4 M satır. Vektörel pandas/numpy; gerekirse `scipy.spatial.cKDTree` (kurulu değilse `python -m pip install scipy`). Tek koşu birkaç dakikayı geçmesin; süreyi ölç ve yaz.

## Dönüş (≤25 satır)
Ne yapıldı, yazılan dosyalar, çalıştırılan kontroller ve çıktıları (`python tools/check_all.py <ilgili kodlar>`), ölçülen sayılar (etiketli), açık sorular. Kendi işini onaylama (K13) — denetçi ayrı çalışır.
