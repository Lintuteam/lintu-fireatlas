# tools/

Ortak araçlar. Bu dosyadaki sözleşmeyi ajanlar uygular.

- `check_all.py` — `docs/03_KABUL_KRITERLERI.md` içindeki C01–C25 kontrollerini çalıştırır. Çıktı: `audit/check_results.json` (kimlik, durum PASS/FAIL/ATLANDI, ölçülen değer, süre). Çıkış kodu: tüm yüksek seviyeli kontroller geçmediyse sıfırdan farklı.
- `build_metrics.py` — gerçek veriden tüm sayıları hesaplayıp `reports/metrics.json` yazar. Her metrik: değer, birim, tanım, betik, veri sürümü, etiket (ölçüldü/tahmini/doğrulanmadı).
- `build_reports.py` — `reports/SABLON_*.md` içindeki `{{...}}` yer tutucularını doldurur. Çözülmemiş yer tutucu varsa hata verir. Üretir: `calisma_prensibi.md`, `dogruluk_raporu.md`, `sunum_raporu.md` (+ html/pdf).

Sıra: `check_all.py` → denetçi onayı → `build_metrics.py` → `build_reports.py`.
