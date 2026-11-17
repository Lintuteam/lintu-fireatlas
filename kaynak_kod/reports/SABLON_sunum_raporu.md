# Sunum Raporu

Veri sürümü: {{meta.veri_surumu}} · Üretim tarihi: {{meta.uretim_tarihi}}
Denetim durumu: {{meta.denetim_durumu}}

> Bu rapor sunumda anlatım içindir. Konuşma metni önce **Basitçe** (benzetme), ardından **Teknik olarak** verilir. Her sayı `reports/metrics.json` kimliğiyle izlenir; yanındaki etiket **ölçüldü / tahmini / doğrulanmadı**dır (K5). Yapılmayanlar gizlenmez (§7, §9). "Aktivite" = tarihsel hotspot yoğunluğudur; hotspot yangın değildir, risk tahmini yapılmaz.

## 1. Tek cümle

"MODIS ve VIIRS aynı dili konuşmuyor; biz VIIRS'i MODIS'in diline çevirip hem yapay sıçramayı ({{jump_raw_pct|t}}) hem de yangın olmayan ısı kaynaklarını ayırdık, hiçbir noktayı silmeden ve neyi doğrulayamadığımızı açıkça yazarak."

## 2. Sorun

**Basitçe:** Ormanı iki gözcü izliyor: eski olan kaba görüyor, yeni olan çok ince görüyor. Yeni gözcü işe başlayınca "yangın sayısı" fırlıyor; oysa yangınlar artmadı, gözcü keskinleşti.
**Teknik olarak:** MODIS 2000'den, VIIRS {{veri_ilk_viirs_yili}}'den beri tespit üretiyor. VIIRS daha hassas olduğundan geçiş yılında ham seri {{jump_raw_pct|t}} sıçrıyor; aynı pencerede gerçek MODIS {{jump_modis_gercek_pct|t}} değişti (yani aktivite aslında azaldı). Harmonize seri {{jump_harm_pct|t}}; harmonizasyonun eklediği fark {{jump_resid_pct|t}}. **"Sorunu çözdük" demiyoruz**: harmonize seri gerçek MODIS düşüşünü bu farkla izliyor.

## 3. Anlatım akışı (5–7 dakika)

| Süre | Adım | Ne söylenir | Ekranda | Sayılar |
|---|---|---|---|---|
| 0:00–0:40 | 1. Sorun | Eski ve yeni gözcü; ham seride yapay sıçrama | Sıçrama sekmesi, ham çizgi | {{jump_raw_pct|t}}, {{jump_modis_gercek_pct|t}} |
| 0:40–1:30 | 2. Veri ve temizlik | {{veri_yil_bas}}–{{veri_yil_bit}}, {{veri_toplam_nokta}} nokta; hiçbiri silinmez, etiketlenir; kural tabanlı | Harita, durum süzgeci | {{huni_nasa_etiket_pay|t}}, {{huni_kural_etiket_pay|t}} |
| 1:30–2:30 | 3. Kümeleme ve birleştirme laboratuvarı | Aynı yangın bir kez sayılır; MODIS karesi + VIIRS noktaları | Laboratuvar sekmesi, 5 adım | {{events_total|t}}, {{events_double_count_avoided|t}} |
| 2:30–3:30 | 4. Üçlü sınıf | Ortak / yalnız MODIS / yalnız VIIRS; VIIRS ayrıntısı kaybolmaz | Harita katmanları | {{events_match_ortak|t}}, {{events_match_yalniz_viirs|t}} |
| 3:30–4:30 | 5. Harmonizasyon ve sıçrama | VIIRS'i MODIS diline çevirdik; bir yılı saklayıp tahmin ederek sınadık (Soru 3 kararı: çok yıllı kıyaslamada varsayılan `MODIS-eşdeğer` seri, üst bardaki `#sciModeBtn` ile anında ham seriye geçilebilir) | Sıçrama sekmesi, `#sciModeBtn` | {{loyo_mape|t}}, {{jump_resid_pct|t}} |
| 4:30–5:30 | 6. Takvim | En yoğun aylar, anomali, ayırt edilemezlik | Takvim sekmesi | {{takvim_top3_ay_modis_temiz_TR|ay,e}} |
| 5:30–6:30 | 7. Dürüst sınırlar | 2026 eşdeğer güvenilmez; tesis yakalama; anız yer doğrulaması yok | Bu raporun §7'si | {{harm_2026_bant_kapsama|t}}, {{ref_recall|t}} |
| 6:30–7:00 | 8. Kapanış | Aşağıdaki kapanış cümlesi | — | — |

**Üç dakikalık kısa sürüm:** 1 → 2 → 5 → 7 (sorun, temizlik, harmonizasyon sonucu, sınırlar); laboratuvar ve takvim sorulursa gösterilir.

## 4. Slayt iskeleti (10 slayt)

Her slaytın kullandığı sayılar `metrics.json` kimliğiyle verilmiştir.

{{sunum.slayt_iskeleti}}

## 5. Canlı demo senaryoları (gerçek veriden otomatik seçildi)

Hepsi gerçek veridendir; sahte veri yoktur ve sade modda "SİMÜLASYON" rozeti kapalıdır (C16). Seçim kuralları `tools/build_rapor_metrikleri.py` içinde olup veri değişirse kendiliğinden güncellenir. **Başlatma:** `src/app/baslat.bat` çalıştırılır (yerel sunucu, internet gerekmez); tarayıcı http://localhost:8765/index.html adresini açar. Üstteki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") Soru 3 kararı gereği varsayılan bilimsel seriyi tek tıkla ham olay serisiyle karşılaştırır; `#quickExportBtn` hızlı CSV indirir; "Sade mod" teknik ayrıntıları gizler; dil düğmesi TR/EN.

{{sunum.demo_senaryolari}}

## 6. NASA gereksinim eşlemesi (C25)

**Basitçe:** NASA'nın istediği maddeler (N-xx) ve Yusuf'un ek istekleri (U-xx) tek tabloda: ne yapıldı, ne kısmen, ne yapılmadı; kanıtı nerede.
**Teknik olarak:** Durum, kanıt dosyasının varlığına ve açık denetim bulgularına bağlanır; kanıt yolu yoksa üretim durur. Kaynak: `docs/01_ISTEKLER.md`, eşleme: `reports/gereksinim_eslemesi.json`.

{{gereksinim.tablo}}

## 7. Yapıldı / kısmen / yapılmadı

{{gereksinim.durum_tablosu}}

**Doğrulanmayanlar ve sınırlar (kısa liste; tamamı Doğruluk Raporu §9):**

{{sinirlar.liste}}

## 8. Muhtemel sorular ve kanıtlı cevaplar

Sorular `audit/soru_cevap.md` dosyasından (denetçi provası); cevaplar ve sayılar bu raporda `metrics.json`'dan yeniden çekilmiştir. Her cevabın sonunda kullanılan metrik kimlikleri ve denetçinin durum notu vardır.

{{sunum.soru_cevap}}

## 9. Cevaplanamayan sorular (eksikler)

Aşağıdakiler için elimizde yeterli kanıt yoktur; biri sorarsa "bunu doğrulayamadık" denmelidir.

{{sunum.cevaplanamayan}}

## 10. Kapanış

"Bu proje yangın sayısı üretmiyor; yangın verisine ne kadar güvenebileceğimizi ölçüyor. {{veri_toplam_nokta}} ham noktadan {{huni_olay_sayisi}} olay çıkardık, VIIRS'i MODIS diline çevirdik, bir yılı saklayıp tahmin ederek sınadık ({{loyo_mape|t}}); gerçek MODIS düşüşünü {{jump_resid_pct|t}} farkla izledik ve 2026 için eşdeğer serimize güvenmediğimizi, tesis yakalamamızın {{ref_recall|t}} olduğunu, anızı sahada doğrulayamadığımızı açıkça söylüyoruz. Sayıların her biri tek bir dosyadan, `metrics.json`'dan gelir; yanında dürüstlük etiketi vardır."
