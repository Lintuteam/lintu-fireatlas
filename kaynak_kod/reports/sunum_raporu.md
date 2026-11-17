# Sunum Raporu

Veri sürümü: FIRMS MODIS C6.1 + VIIRS 375 m, 2000–2026 (son gün 2026-11-12), 1.414.674 nokta, veri şeması v1, `reports/metrics.json` üretimi 2026-11-13T09:07:17Z · Üretim tarihi: 2026-11-13 09:42 UTC
Denetim durumu: check_all: 25 geçti, 0 kaldı, 0 atlandı; denetçi bulguları: açık yüksek 0, açık orta 0, açık düşük 5 — denetçi kapısı açık yüksek bulgu içermiyor

> Bu rapor sunumda anlatım içindir. Konuşma metni önce **Basitçe** (benzetme), ardından **Teknik olarak** verilir. Her sayı `reports/metrics.json` kimliğiyle izlenir; yanındaki etiket **ölçüldü / tahmini / doğrulanmadı**dır (K5). Yapılmayanlar gizlenmez (§7, §9). "Aktivite" = tarihsel hotspot yoğunluğudur; hotspot yangın değildir, risk tahmini yapılmaz.

## 1. Tek cümle

"MODIS ve VIIRS aynı dili konuşmuyor; biz VIIRS'i MODIS'in diline çevirip hem yapay sıçramayı (143,13 % (ölçüldü)) hem de yangın olmayan ısı kaynaklarını ayırdık, hiçbir noktayı silmeden ve neyi doğrulayamadığımızı açıkça yazarak."

## 2. Sorun

**Basitçe:** Ormanı iki gözcü izliyor: eski olan kaba görüyor, yeni olan çok ince görüyor. Yeni gözcü işe başlayınca "yangın sayısı" fırlıyor; oysa yangınlar artmadı, gözcü keskinleşti.
**Teknik olarak:** MODIS 2000'den, VIIRS 2012'den beri tespit üretiyor. VIIRS daha hassas olduğundan geçiş yılında ham seri 143,13 % (ölçüldü) sıçrıyor; aynı pencerede gerçek MODIS −44,9 % (ölçüldü) değişti (yani aktivite aslında azaldı). Harmonize seri −41,35 % (tahmini); harmonizasyonun eklediği fark 3,55 yüzde puan (tahmini). **"Sorunu çözdük" demiyoruz**: harmonize seri gerçek MODIS düşüşünü bu farkla izliyor.

## 3. Anlatım akışı (5–7 dakika)

| Süre | Adım | Ne söylenir | Ekranda | Sayılar |
|---|---|---|---|---|
| 0:00–0:40 | 1. Sorun | Eski ve yeni gözcü; ham seride yapay sıçrama | Sıçrama sekmesi, ham çizgi | 143,13 % (ölçüldü), −44,9 % (ölçüldü) |
| 0:40–1:30 | 2. Veri ve temizlik | 2000–2026, 1.414.674 nokta; hiçbiri silinmez, etiketlenir; kural tabanlı | Harita, durum süzgeci | 23,8 % (ölçüldü), 2,3 % (ölçüldü) |
| 1:30–2:30 | 3. Kümeleme ve birleştirme laboratuvarı | Aynı yangın bir kez sayılır; MODIS karesi + VIIRS noktaları | Laboratuvar sekmesi, 5 adım | 471.978 olay (ölçüldü), 59.201 olay (ölçüldü) |
| 2:30–3:30 | 4. Üçlü sınıf | Ortak / yalnız MODIS / yalnız VIIRS; VIIRS ayrıntısı kaybolmaz | Harita katmanları | 35.651 olay (ölçüldü), 287.781 olay (ölçüldü) |
| 3:30–4:30 | 5. Harmonizasyon ve sıçrama | VIIRS'i MODIS diline çevirdik; bir yılı saklayıp tahmin ederek sınadık (Soru 3 kararı: çok yıllı kıyaslamada varsayılan `MODIS-eşdeğer` seri, üst bardaki `#sciModeBtn` ile anında ham seriye geçilebilir) | Sıçrama sekmesi, `#sciModeBtn` | 8,33 % (ölçüldü), 3,55 yüzde puan (tahmini) |
| 4:30–5:30 | 6. Takvim | En yoğun aylar, anomali, ayırt edilemezlik | Takvim sekmesi | Haz > Eyl > Ağu (ölçüldü) |
| 5:30–6:30 | 7. Dürüst sınırlar | 2026 eşdeğer güvenilmez; tesis yakalama; anız yer doğrulaması yok | Bu raporun §7'si | 0,545 (ölçüldü), 0,4777 (tahmini) |
| 6:30–7:00 | 8. Kapanış | Aşağıdaki kapanış cümlesi | — | — |

**Üç dakikalık kısa sürüm:** 1 → 2 → 5 → 7 (sorun, temizlik, harmonizasyon sonucu, sınırlar); laboratuvar ve takvim sorulursa gösterilir.

## 4. Slayt iskeleti (10 slayt)

Her slaytın kullandığı sayılar `metrics.json` kimliğiyle verilmiştir.

| # | Slayt | Ana mesaj | Kullanılan sayılar (metrics.json kimliği = değer, etiket) |
|---|---|---|---|
| 1 | Sorun: iki sensör, bir yapay sıçrama | MODIS 2000'den, VIIRS 2012'den beri yangın tespit ediyor; VIIRS daha hassas, bu yüzden ham seri geçişte 143,13 % (ölçüldü) sıçrıyor. | `veri_ilk_viirs_yili` = 2.012 (ölçüldü); `jump_raw_pct` = 143,13 (ölçüldü); `jump_raw_viirs_only_pct` = 88,03 (ölçüldü) |
| 2 | Veri: çok yıllı Türkiye arşivi | 1.414.674 ham tespit, MODIS 259.707, VIIRS 1.154.967; hiçbir nokta silinmez, her nokta bir etiket alır. | `veri_toplam_nokta` = 1.414.674 (ölçüldü); `veri_modis_nokta` = 259.707 (ölçüldü); `veri_viirs_nokta` = 1.154.967 (ölçüldü); `veri_yil_bas` = 2.000 (ölçüldü); `veri_yil_bit` = 2.026 (ölçüldü); `veri_nrt_nokta` = 61.147 (ölçüldü) |
| 3 | Temizlik: yangın olmayan ısı kaynakları | Noktaların 23,8 % (ölçüldü) NASA etiketiyle, 2,3 % (ölçüldü) kendi kuralımızla (sanayi) ayrılır; anız olay düzeyinde etiketlenir. Kural tabanlıdır. | `temizlik_status_temiz` = 827.043 (ölçüldü); `temizlik_status_aniz` = 217.179 (ölçüldü); `temizlik_status_sanayi` = 27.012 (ölçüldü); `huni_nasa_etiket_pay` = 23,8 (ölçüldü); `huni_kural_etiket_pay` = 2,3 (ölçüldü); `temizlik_ref_yangin_koruma` = 0,9982 (tahmini) |
| 4 | Kümeleme: aynı yangını bir kez say | 1.044.222 noktadan 471.978 olay; ortak kümeleme çakışma döneminde 59.201 çifte sayımı önler. | `huni_kumeleme_girdi` = 1.044.222 (ölçüldü); `events_total` = 471.978 (ölçüldü); `events_double_count_avoided` = 59.201 (ölçüldü); `events_joint_overlap` = 380.975 (ölçüldü); `events_separate_overlap` = 440.176 (ölçüldü) |
| 5 | Üçlü sınıf: ortak / yalnız MODIS / yalnız VIIRS | VIIRS ayrıntısı korunur; MODIS olaylarının yalnız %38,2 kadarını VIIRS de görür (çoğu fark gerçek gözlem farkı). | `events_match_ortak` = 35.651 (ölçüldü); `events_match_yalniz_modis` = 57.543 (ölçüldü); `events_match_yalniz_viirs` = 287.781 (ölçüldü); `events_modis_seen_by_viirs_share` = 0,3825 (ölçüldü); `mcell_iz_basina_viirs` = 3,349 (ölçüldü) |
| 6 | Harmonizasyon: VIIRS'i MODIS'in diline çevir | Gözlem eforu (uydu sayısı) düzeltmesi asıl kazanç: ay×bölge hata 52,68 % (ölçüldü) → 30,63 % (ölçüldü); (i) ve (ii) ayırt edilemez. | `harm_i0_ay_bolge_wape` = 52,68 (ölçüldü); `harm_i_ay_bolge_wape` = 30,64 (ölçüldü); `harm_ii_ay_bolge_wape` = 30,63 (ölçüldü); `harm_ii_eksi_i_wape_ci95` = [−2,97 ; 4,26] (tahmini); `harm_kazanan_yontem` = (ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu (tahmini) |
| 7 | Sonuç: sıçrama gerçek MODIS düşüşünü izliyor | Ham 143,13 % (ölçüldü) → harmonize −41,35 % (tahmini); gerçek MODIS −44,9 % (ölçüldü); fark 3,55 yüzde puan (tahmini). 'Çözüldü' değil, 'izliyor'. | `jump_raw_pct` = 143,13 (ölçüldü); `jump_harm_pct` = −41,35 (tahmini); `jump_modis_gercek_pct` = −44,9 (ölçüldü); `jump_resid_pct` = 3,55 (tahmini); `loyo_ci95` = [−23,49 ; 9,51] (tahmini); `jump_harm_dogal_aralikta` = hayır (tahmini) |
| 8 | Doğrulama: bir yılı saklayıp tahmin etmek (LOYO) | Yıllık MAPE 8,33 % (ölçüldü), R² 0,8716 (ölçüldü); aylık ülke bandı ayların %92,3 kadarını kapsıyor; denetçi 97 sayıyı bağımsız yeniden hesapladı. | `loyo_mape` = 8,33 (ölçüldü); `loyo_r2` = 0,8716 (ölçüldü); `loyo_bias` = 0,55 (ölçüldü); `equiv_band_kapsama_ay_tr` = 0,9226 (ölçüldü); `yh_girdi` = 97 (ölçüldü); `yh_fark_sifir` = 93 (ölçüldü) |
| 9 | Takvim: en yoğun aylar ve anomali | MODIS temiz seride ilk üç ay Haz > Eyl > Ağu; aylar arasında ayırt edilemezlik bayrağı var. Aktivite = tarihsel hotspot yoğunluğu, tehlike tahmini değil. | `takvim_top3_ay_modis_temiz_TR` = Haz > Eyl > Ağu (ölçüldü); `takvim_top3_ay_modis_esdeger_TR` = Ağu > Eyl > Haz (tahmini); `takvim_ayirt_edilemez_modis_temiz_TR` = 1 (ölçüldü); `takvim_mevcut_ay_oran_modis_temiz_TR` = 0,127 (tahmini); `takvim_mevcut_ay_oran_viirs_temiz_ub_TR` = 0,243 (tahmini) |
| 10 | Dürüst sınırlar | 2026 eşdeğer bandı gerçek MODIS'i ayların yalnız %54,5 kadarında kapsıyor; tesis yakalama 0,4777 (tahmini); anız için yer doğrulaması yok; ekran okuyucu testi yok. | `harm_2026_bant_kapsama` = 0,545 (ölçüldü); `ref_recall` = 0,4777 (tahmini); `temizlik_aniz_loyo_kaldirac` = 0,928 (ölçüldü); `aqua_viirs_esz_cift_payi_2026` = 0,182 (ölçüldü); `a11y_klavye_oran` = 0,884 (ölçüldü); `temizlik_sta_maskesi_karsilastirma` = yok (doğrulanmadı) |

## 5. Canlı demo senaryoları (gerçek veriden otomatik seçildi)

Hepsi gerçek veridendir; sahte veri yoktur ve sade modda "SİMÜLASYON" rozeti kapalıdır (C16). Seçim kuralları `tools/build_rapor_metrikleri.py` içinde olup veri değişirse kendiliğinden güncellenir. **Başlatma:** `src/app/baslat.bat` çalıştırılır (yerel sunucu, internet gerekmez); tarayıcı http://localhost:8765/index.html adresini açar. Üstteki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") Soru 3 kararı gereği varsayılan bilimsel seriyi tek tıkla ham olay serisiyle karşılaştırır; `#quickExportBtn` hızlı CSV indirir; "Sade mod" teknik ayrıntıları gizler; dil düğmesi TR/EN.

### Senaryo 1 — Çok tespit, az olay günü (birleştirmenin değeri)

Seçim kuralı (`tools/build_rapor_metrikleri.py`): o gün başlayan olayların toplam tespit sayısının olay sayısına oranı en büyük gün (en az 500 tespit). Seçilen gün: **2021-07-28**.

Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):
1. `baslat.bat` ile uygulamayı aç; **Tarih aralığını sıfırla** düğmesine bas; Bölge listesinde 'Türkiye (tümü)' kalsın.
2. Başlangıç ve Bitiş alanlarına 2021-07-28 yaz.
3. Dahil edilen durumlarda 'temiz' ve 'anız' işaretli olsun (öteki durumlar kapalı).
4. Harita sekmesinde olay sayısını oku; **En büyük olaya git** düğmesine bas; Müfettiş'te olayın noktalarını göster.

Beklenen: O gün başlayan 75 olay (ölçüldü), bunların toplam tespiti 8.568 tespit (ölçüldü) (olay başına 114,2 tespit/olay (ölçüldü)); en büyük olay Antalya ilinde, 6.740 tespit (ölçüldü) içeriyor ve 218,6 saat (ölçüldü) sürüyor. Mesaj: yüzlerce nokta tek yangın olarak sayılır, nokta sayısı yangın sayısı değildir.

### Senaryo 2 — Sanayi bölgesi (silmeden etiketleme, ham noktalar)

Seçim kuralı: 'sanayi' etiketli nokta sayısı en çok olan il: **İzmir**.

Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):
1. **Tarih aralığını sıfırla** düğmesine bas (önceki senaryonun tarihi kalmasın).
2. Bölge listesinden İzmir ilini seç.
3. Dahil edilen durumlarda yalnız 'Sanayi' kutusunu işaretle. Sanayi noktaları olaya dönüştürülmediği için olay sayısı 0 görünür; bu beklenen davranıştır. Olaylarda olmayan durum seçildiği için ham nokta katmanı kendiliğinden açılır.
4. Ham noktalar (+) katmanındaki sayıyı oku (katman seçili durum, sensör ve bölgeye göre süzer); noktaların birkaç küçük hücrede yığıldığını göster.
5. Durumlara 'temiz'i ekle ve sayının değiştiğini göster: hiçbir nokta silinmedi, yalnız etiketlendi.

Beklenen: 3.488 nokta (ölçüldü) 'sanayi' etiketli ham nokta; 40 hücre (ölçüldü) ayrı 0,01° hücrede, 27 (ölçüldü) farklı yılda görülüyor; ildeki tüm noktaların 5,3 % (ölçüldü) kadarı. Bu bir kural etiketidir (kural tabanlı, 'yapay zekayla temizlendi' değil); referans setinde tesis yakalama 0,4777 (tahmini) olduğu için bazı tesisler kaçar.

### Senaryo 3 — Sensör geçiş yılı (sıçrama grafiği)

Seçim: ilk VIIRS tespitinin yılı = **2012** (veriden bulundu).

Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):
1. **Tarih aralığını sıfırla**; Sıçrama sekmesini aç.
2. Dört çizgiyi göster: ham, kümelenmiş (olay), harmonize (MODIS-eşdeğer), gerçek MODIS; gölgeli bant belirsizliktir.
3. 'Önceki 3 yıl ort. / Sonraki 3 yıl ort.' tablosunu oku; 'Doğal yıllık değişim aralığı' cümlesini ve DIŞINDA/İÇİNDE sonucunu olduğu gibi oku.
4. Altındaki metrik tablosunun metrics.json'dan geldiğini söyle (C14).

Beklenen: Ham sıçrama 143,13 % (ölçüldü); harmonize −41,35 % (tahmini); gerçek MODIS aynı pencerede −44,9 % (ölçüldü); fark 3,55 yüzde puan (tahmini); LOYO yıllık %95 hata aralığı [−23,49 ; 9,51] % (tahmini). Harmonize sıçrama doğal aralıkta içinde mi: hayır (tahmini) (hayır); gerçek MODIS'in de aralık dışında olduğunu açıkla.

### Senaryo 4 — Yalnız VIIRS örneği (U-03, U-13)

Seçim kuralı: 'yalnız VIIRS' sınıfında en çok VIIRS noktalı olay: **2021-07-11, Manisa** (olay 307.053).

Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):
1. **Tarih aralığını sıfırla**; Bölge: Manisa; Başlangıç ve Bitiş: 2021-07-11.
2. Harita katmanlarında yalnız 'yalnız VIIRS' sınıfını aç; olaya tıkla (veya **En büyük olaya git**) ve Müfettiş'te VIIRS noktalarını göster.
3. Birleştirme laboratuvarı sekmesinde 'Örnek hücre' listesinden bir örnek seç ve İleri ile beş adımı (ham noktalar, MODIS hücresine atama, FRP toplamı, tespit sınırı kararı, olay) gez.

Beklenen: Olay 307.053: 202 nokta (ölçüldü), MODIS noktası yok, toplam FRP 270,7 MW (ölçüldü). Mesaj: MODIS'in göremediği küçük yangınlar VIIRS katmanında kalır (ayrıntı kaybolmaz); MODIS izi başına ortalama 3,349 nokta (ölçüldü) VIIRS noktası düşer.

### Senaryo 5 — Takvim ve mevcut ay (dürüst sınırlar)

Seçim: Türkiye geneli, MODIS temiz serisi; sıralama ve mevcut ay `agg/ranking.parquet` ve `agg/current_month.parquet` dosyalarından okunur. Son veri günü **2026-11-12**.

Tıklama sırası (`src/app/baslat.bat`, tarayıcıda http://localhost:8765/index.html):
1. **Tarih aralığını sıfırla**; Bölge 'Türkiye (tümü)'; Seri listesinden MODIS temiz serisini seç; Takvim sekmesini aç.
2. Yıl×ay matrisinde 'Mutlak' ve 'Anomali (ay medyanına göre)' modları arasında geçiş yap.
3. Ay sıralamasındaki ★ işaretli ilk üç ayı oku; '≈' ile işaretli ayırt edilemez ayları belirt.
4. Mevcut ay ve son tam ay kutusundaki uyarıları (kısmi ay, NRT payı, eşdeğer güvenilmez ise nedeni) göster; 'bu ay düşük' cümlesinin neden temkinli olduğunu anlat.

Beklenen: ★ sırası (medyan): Haz > Eyl > Ağu (ölçüldü); medyanlar [1.214 ; 1.103 ; 998] (ölçüldü); ayırt edilemez (≈): Haz > Eyl > Ağu (ölçüldü). Mevcut ay 2026-11-01 … 2026-11-12 (12 gün (ölçüldü), kısmi, NRT payı 100 % (ölçüldü)): değer 26 tespit (ölçüldü), tarihsel medyan 204 tespit (ölçüldü), oran 0,127 kat (ölçüldü); VIIRS oranı 0,243 kat (ölçüldü). Son tam ay (2026-10-01): değer 507 tespit (ölçüldü), medyan 579 tespit (ölçüldü), oran 0,876 kat (ölçüldü). MODIS'e özgü ek düşüşün yorumu: MODIS'e özgü ek düşüş: sensör ömrü sonu, NRT veya yörünge kayması şüphesi (doğrulanmadı).


## 6. NASA gereksinim eşlemesi (C25)

**Basitçe:** NASA'nın istediği maddeler (N-xx) ve Yusuf'un ek istekleri (U-xx) tek tabloda: ne yapıldı, ne kısmen, ne yapılmadı; kanıtı nerede.
**Teknik olarak:** Durum, kanıt dosyasının varlığına ve açık denetim bulgularına bağlanır; kanıt yolu yoksa üretim durur. Kaynak: `docs/01_ISTEKLER.md`, eşleme: `reports/gereksinim_eslemesi.json`.

| Kimlik | İstek | Durum | Kanıt yolu | Not (etiketli) |
|---|---|---|---|---|
| N-01 | MODIS ve VIIRS hotspot'larını harmonize et; sensör kökeni önemsizleşsin, örüntü ve anomali öne çıksın | kısmen | `src/harmonize/seri.py`, `docs/harmonizasyon_yontemi.md`, `audit/bulgular.md` | Harmonizasyon yapıldı: harmonize sıçrama −41,35 % (tahmini), gerçek MODIS −44,9 % (ölçüldü), fark 3,55 yüzde puan (tahmini), LOYO aralığı [−23,49 ; 9,51] % (tahmini). Eski ölçüt (doğal aralık içinde mi): hayır (tahmini); 2026 eşdeğeri güvenilmez ve MODIS sonrası doğrulama yok. 'Sensör kökeni önemsiz' demek için kanıt yetersiz. |
| N-02 | Erken 2000'lerden bugüne yangın aktivite takvimi | yapıldı | `data/processed/points.parquet`, `src/pipeline/build_points.py`, `src/app/index.html` | 2000–2026, 1.414.674 nokta (ölçüldü). 2000–Temmuz 2002 yalnız Terra (düşük güven bayraklı, sonraki yıllarla doğrudan karşılaştırılamaz). |
| N-03 | Kullanıcı bölge ve belirli tarih aralığı seçsin | yapıldı | `src/app/index.html`, `src/analytics/query.py`, `src/app/main.js` | İl, çokgen, daire, enlem/boylam ve serbest başlangıç–bitiş tarihi (Başlangıç/Bitiş alanları) var; tarih aralığı analizi `aralik_analiz`. Etiket: ölçüldü (sayım), eşdeğer seri tahmini. |
| N-04 | Analitik ve görselleri indirebilsin | yapıldı | `src/app/csv.js`, `src/app/charts.js`, `src/app/tests/csv_check.py` | Olay CSV'si (UTF-8 BOM, UTC ve TR zaman sütunları) ile matris ve sıçrama grafiği PNG/SVG dışa aktarma (Dışa aktar sekmesi). CSV kontrolü C17. |
| N-05 | Mevcut ayı seçilen alan için tarihsel medyanla karşılaştır | yapıldı | `src/analytics/query.py`, `data/processed/agg/current_month.parquet`, `src/app/core.js` | Mevcut ay, seçili alan için geçmiş yılların aynı günleriyle karşılaştırılıyor (kısmi ay 12 gün (ölçüldü), NRT payı 100 % (ölçüldü)); oran MODIS 0,127 kat (tahmini), VIIRS 0,243 kat (tahmini). 2026 eşdeğer serisi için güvenilmezlik bayrağı: 1 (doğrulanmadı) (1 = güvenilmez); açık yüksek denetim bulgusu varsa durum 'kısmen' olur. |
| N-06 | Çok yıllı ortalamalara göre anomali | yapıldı | `src/analytics/analiz.py`, `data/processed/agg/anomaly_monthly.parquet`, `src/app/main.js` | Yıl hariç tutmalı (LOYO) sağlam z-skoru; eşik /z/ ≥ 2. Eşdeğer seride işaretlerin 33,53 % (tahmini) oranı belirsiz banda düşer; anomali tahminidir. |
| N-07 | Hangi ay ve yılların en yoğun olduğunu göster | yapıldı | `data/processed/agg/ranking.parquet`, `src/analytics/analiz.py`, `src/app/main.js` | Ay medyanı sıralaması: MODIS temiz TR ilk üç ay Haz > Eyl > Ağu (ölçüldü); ilk üç ay arasında istatistiksel ayırt edilemezlik bayrağı 1 (ölçüldü) (1 = ayırt edilemez), ekranda '≈' ile gösterilir. |
| N-08 | Erişilebilir renk rampaları | kısmen | `audit/erisilebilirlik.json`, `src/app/tests/olc_renk.js`, `src/app/tests/olc_klavye_aria.js` | Viridis/Cividis/YlOrRd + renk körlüğü simülasyonu; ölçüm: kontrast en az 4,59 (ölçüldü), palet ayırt edilebilirliği 14 CIE76 dE (ölçüldü), klavye %88,4. Ekran okuyucuyla elle test yapılmadı (doğrulanmadı). |
| N-09 | Aramada bulunan hotspot'ları CSV indir | yapıldı | `src/app/csv.js`, `tools/check_all.py` | Seçili süzgece uyan olaylar CSV olarak iner; sayı korunumu C17 ile denetlenir. Birim: olay (ham nokta CSV'si ayrı katmandan). |
| N-10 | Etkileşimli harita: alan çiz, enlem/boylam gir | yapıldı | `src/app/mapview.js`, `src/app/vendor`, `src/app/index.html` | Etkileşimli harita (yerel Leaflet), çokgen/daire çizimi, enlem-boylam girişi, üç harita katmanı. Harita zemini çevrimiçi isteğe bağlıdır; çevrimdışıyken il sınırları görünür. |
| N-11 | TR/EN dil düğmesi | yapıldı | `src/app/i18n/tr.json`, `src/app/i18n/en.json`, `tools/check_all.py` | TR/EN düğmesi; iki sözlüğün anahtar kümesi aynı (C18). |
| N-12 | Tespit edilen yangın sayısı | yapıldı | `data/processed/events.parquet`, `src/app/main.js` | Hem tespit (1.414.674 nokta (ölçüldü) ham) hem olay (471.978 olay (ölçüldü)) sayısı gösterilir; 'yangın sayısı' yerine kuralı belli 'olay sayısı' (duyarlılık: D ve H'ye bağlı). |
| U-01 | Elimdeki çok yıllı (hedef 20 yıl) MODIS ve VIIRS verisinden gerçek bir örüntü ve orantı çıkar; farklı güven... | yapıldı | `src/harmonize/guven_esleme.py`, `docs/harmonizasyon_yontemi.md`, `src/config/esikler.json` | Güven eşleme veriden (40.368 çift (ölçüldü) Aqua–VIIRS çifti) öğrenildi: sınırlar [35 ; 82] MODIS % (tahmini). Sonuç dürüstçe zayıf: Spearman 0,2138 (ölçüldü), öğrenilmiş eşleme FIRMS'i geçmedi. |
| U-02 | MODIS ve VIIRS'i aynı ızgarada düşün; MODIS ızgarasına göre hareket et. MODIS'te 1 yangın, VIIRS'te 4 farkl... | yapıldı | `src/harmonize/eslestirme.py`, `data/processed/points_mcell.parquet` | Eşleştirme birimi MODIS ayak izi; MODIS izi başına ortalama 3,349 nokta (ölçüldü) VIIRS noktası, sabit ızgara aynı izi 1,764 (ölçüldü) hücreye bölerdi. VIIRS ayrıntısı korunur. |
| U-03 | Ekstra katman: MODIS'in ölçmediği ama VIIRS'in ölçtüğü yangınlar ("yalnız VIIRS"). Üçlü sınıf: ortak / yaln... | yapıldı | `data/processed/events.parquet`, `src/clustering/build_events.py`, `src/app/mapview.js` | Üçlü sınıf: ortak 35.651 olay (ölçüldü), yalnız MODIS 57.543 olay (ölçüldü), yalnız VIIRS 287.781 olay (ölçüldü), tek sensör dönemi 91.003 olay (ölçüldü). |
| U-04 | VIIRS verisi durmalı, ayrıntı kaybolmamalı; yanında MODIS değerine yaklaşan bir eşdeğer seri üretilmeli (ik... | yapıldı | `data/processed/agg/harmonized.parquet`, `src/harmonize/seri.py` | İki çıktı: MODIS-eşdeğer seri (38.295 (ölçüldü) satır, bantlı) ve ham/eforlu VIIRS ayrıntısı. Eşdeğer seri tahmini. |
| U-05 | FRP'yi hücre içinde toplayıp MODIS'in tespit sınırına göre değerlendir. Güven sınıflarını ortak dile çevir. | yapıldı | `src/harmonize/seri.py`, `src/harmonize/guven_esleme.py` | Hücre FRP toplamı ve MODIS etkin tespit sınırı FRP50 genel 64,88 MW (tahmini), gündüz 73,98 MW (tahmini), gece 20,54 MW (tahmini) (etkin sınır, fiziksel sınır değil). |
| U-06 | Çerçeve: proje yalnız veri toplamıyor, hataları düzeltiyor (Faz 1a temizlik). Ancak NASA'nın istediği harmo... | yapıldı | `src/cleaning/build_status.py`, `src/harmonize/run_all.py`, `docs/temizlik_yontemi.md` | Temizlik (Faz 1a) ve harmonizasyon (Faz 1b) birlikte teslim edildi; hiçbir nokta silinmedi, 1.414.674 (ölçüldü) noktanın hepsi bir etiket taşır. |
| U-07 | NASA'nın zaten type ile etiketlediği noktalar (volkan, statik kara kaynağı, açık deniz) çıkarılmaya devam e... | yapıldı | `src/cleaning/build_status.py`, `docs/temizlik_yontemi.md` | NASA type etiketleri korunur: statik 328.379 nokta (ölçüldü), deniz 8.848 nokta (ölçüldü), volkan 5 nokta (ölçüldü). NRT'de type yok; telafi için miras kuralı (12.940 (ölçüldü) nokta); NRT deniz telafisi doğrulanmadı. |
| U-08 | Bir yangın 365 gün hatta yıllarca sürmez. Belirli bir süreden sonra aynı yerde tekrar eden sıcak nokta, NAS... | kısmen | `src/cleaning/kalibrasyon.py`, `audit/temizlik_kalibrasyon.json`, `audit/dogrulama_seti.csv` | Çok yıllı kalıcılık kuralı (eşikler: Çalışma Prensibi eşik tablosu) uygulandı: sanayi 27.012 (ölçüldü) nokta, kalıcı belirsiz 6.208 nokta (ölçüldü). LOYO uyuşma kesinlik 0,9199 (ölçüldü); referans seti küçük (tesis yakalama 0,4783 (tahmini)), STA maskesi karşılaştırılmadı, MODIS döneminde uyuşma düşük. |
| U-09 | Anız yangınları iklime ve bölgeye göre tekrar eden periyotlar öğrenilerek ayrılsın. Periyodu öğrenen kurall... | kısmen | `src/cleaning/aniz_takvim.py`, `src/cleaning/olay_aniz.py`, `src/cleaning/worldcover.py`, `audit/aniz_takvimi.json` | Bölge×ay anız takvimi yıl hariç öğrenilir (döngüsellik önlemi); WorldCover'da anız noktalarının %79,3 ekili alanda (ölçüldü). Ama saha/yanmış alan doğrulaması yok ve ay tek başına ayırmıyor (kaldıraç 0,928 (ölçüldü)). |
| U-10 | İki sensörün gördüğü yangın mesafe ve zaman örtüşmesiyle aynı olay sayılsın. | yapıldı | `src/clustering/core.py`, `src/clustering/build_events.py` | Mesafe + zaman + MODIS ayak izi örtüşmesiyle ortak olay; ortak kümeleme çakışma döneminde 59.201 (ölçüldü) olayın çifte sayılmasını önler. |
| U-11 | "14 saat yangın görmedim ama sönmedi" durumu akıllıca yönetilsin: boşluk kuralı uydunun gerçekten geçip gör... | yapıldı | `src/clustering/core.py`, `data/processed/coverage.parquet` | Boşluk kuralı kaçırılan geçiş sayısına bağlı (L, Hmax). Kesinti bilgisinin katkısı küçük çıktı; geçiş pencereleri swath değil çıkarım (tahmini). |
| U-12 | Aynı yerde sabah ve akşam ayrı yangın çıkması nadir olabilir ama ihmal edilmesin; D ve H duyarlılığı raporl... | yapıldı | `src/clustering/build_events.py`, `docs/kumeleme_yontemi.md`, `reports/metrics.json` | D/H/L duyarlılık tabloları raporlandı (Doğruluk Raporu §6); birleştirmenin anız kuralını bozması ölçüldü: ortak kümelemede anız sayılan nokta 290.799 nokta (tahmini) karşı ayrı sensörde 320.995 nokta (tahmini). |
| U-13 | Birleştirme Laboratuvarı: MODIS ve VIIRS'in nasıl birleştirildiği gerçek veriyle adım adım görülsün (ham no... | yapıldı | `src/app/lab.js`, `src/app/index.html` | Birleştirme laboratuvarı: ham noktalar, MODIS hücresine atama, FRP toplamı, tespit sınırı kararı, olay; gerçek veriden örnekler. |
| U-14 | Haritada seçenekler: ortak tespit / yalnız VIIRS / yalnız MODIS katmanları açılıp kapanabilsin. | yapıldı | `src/app/mapview.js`, `src/app/i18n/tr.json` | Harita katmanları ortak / yalnız VIIRS / yalnız MODIS (renk + şekil) açılıp kapanır. |
| U-15 | Sıçrama (pik) grafiği: sensör geçişindeki sıçrama harmonizasyon öncesi ve sonrası görülsün, büyüklüğü bir m... | yapıldı | `src/app/charts.js`, `src/app/main.js`, `reports/metrics.json` | Sıçrama grafiği: ham 143,13 % (ölçüldü), harmonize −41,35 % (tahmini), gerçek MODIS −44,9 % (ölçüldü). 'Daha küçük' sonuç, çıkışı önceden bilinen bir hedef olarak değil LOYO ile ölçüldü; sıçramanın tamamen yok olduğu iddia edilmez. |
| U-16 | Takvim: yıllar ve aylar birleştirilip karşılaştırılsın; en çok hangi ayda yangın aktivitesi var sorusuna bö... | yapıldı | `src/app/main.js`, `data/processed/agg/profile.parquet`, `data/processed/agg/ranking.parquet`, `src/analytics/query.py` | Yıl×ay matrisi, ay medyanı sıralaması, mevcut ay karşılaştırması bölge bazında; ilk üç ay Eyl > Ağu > Eki (tahmini). Mevcut ay kutusunun 2026 davranışı açık bir denetim bulgusuna bağlıdır; açıksa durum 'kısmen' olur. |
| U-17 | Görsel taslaktan (referans/) güçlü yanlar alınsın: parent–child hücre müfettişi, üç harita modu, üç çizgili... | yapıldı | `src/app/main.js`, `src/app/mapview.js`, `referans/STIL_NOTU.md` | Referans taslaktan yalnız fikirler alındı (hücre müfettişi, üç harita modu, ham→kümelenmiş→harmonize çizgiler, yıl×ay matrisi, anomali anahtarı); taslaktaki sayılar kullanılmadı. |
| U-18 | FIRMS'in verdiği veri yetmeyebilir. FIRMS API ile otomatik çekme ve ek veri kaynaklarını değerlendir: uydu ... | kısmen | `src/pipeline/firms_api.py`, `src/cleaning/worldcover.py`, `docs/ek_kaynaklar.md` | ESA WorldCover kullanıldı (ölçüldü). FIRMS API betiği hazır ama çalıştırılmadı; swath ve STA maskesi toplu olarak bulunamadı (kapsam çıkarım, STA yok (doğrulanmadı)); MCD64A1 kullanılmadı. |
| U-19 | Ajanlar sık sık kontrol yapsın; veride ve belgelerde uyuşmazlık olup olmadığı sürekli denetlensin. Tek doğr... | yapıldı | `tools/check_all.py`, `audit/bulgular.md`, `audit/yeniden_hesap.json`, `reports/metrics.json` | Bağımsız denetçi, 97 karşılaştırma (ölçüldü) girdiyi yeniden hesapladı (93 tanesinde fark 0); tek sayı kaynağı metrics.json. |
| U-20 | Ekranda sabit yazılmış metrik, rastgele üretilmiş veri (ör. sahte bulut) ve aynı veriyle kalibre edip test ... | yapıldı | `tools/check_all.py`, `src/app/tests/tutarlilik_check.py` | C14 (ekran = hesap), C15 (Math.random ve sabit metrik taraması), C16 (simülasyon izolasyonu) geçti; kalibrasyon ve test LOYO ile ayrıldı (C09). |
| U-21 | İş bittiğinde sistem otomatik olarak üç rapor üretsin: | yapıldı | `tools/build_reports.py`, `reports/SABLON_calisma_prensibi.md`, `reports/SABLON_dogruluk_raporu.md`, `reports/SABLON_sunum_raporu.md` | Üç rapor şablondan, metrics.json'dan üretilir; çözülmemiş yer tutucu varsa üretim durur (C22). HTML üretilir; PDF için tarayıcıdan yazdırma. |

## 7. Yapıldı / kısmen / yapılmadı

Toplam 33 istek: **yapıldı 28**, **kısmen 5**, **yapılmadı 0**. Durum değerlendirmesi kanıt dosyasının varlığına ve açık denetim bulgularına bağlanmıştır (kanıt yolu yoksa üretim durur).

| Durum | Kimlikler |
|---|---|
| yapıldı | N-02, N-03, N-04, N-05, N-06, N-07, N-09, N-10, N-11, N-12, U-01, U-02, U-03, U-04, U-05, U-06, U-07, U-10, U-11, U-12, U-13, U-14, U-15, U-16, U-17, U-19, U-20, U-21 |
| kısmen | N-01, N-08, U-08, U-09, U-18 |
| yapılmadı | — |

Yapılmayan veya kısmen kalanların nedeni:
- **N-01** (kısmen): Harmonizasyon yapıldı: harmonize sıçrama −41,35 % (tahmini), gerçek MODIS −44,9 % (ölçüldü), fark 3,55 yüzde puan (tahmini), LOYO aralığı [−23,49 ; 9,51] % (tahmini). Eski ölçüt (doğal aralık içinde mi): hayır (tahmini); 2026 eşdeğeri güvenilmez ve MODIS sonrası doğrulama yok. 'Sensör kökeni önemsiz' demek için kanıt yetersiz.
- **N-08** (kısmen): Viridis/Cividis/YlOrRd + renk körlüğü simülasyonu; ölçüm: kontrast en az 4,59 (ölçüldü), palet ayırt edilebilirliği 14 CIE76 dE (ölçüldü), klavye %88,4. Ekran okuyucuyla elle test yapılmadı (doğrulanmadı).
- **U-08** (kısmen): Çok yıllı kalıcılık kuralı (eşikler: Çalışma Prensibi eşik tablosu) uygulandı: sanayi 27.012 (ölçüldü) nokta, kalıcı belirsiz 6.208 nokta (ölçüldü). LOYO uyuşma kesinlik 0,9199 (ölçüldü); referans seti küçük (tesis yakalama 0,4783 (tahmini)), STA maskesi karşılaştırılmadı, MODIS döneminde uyuşma düşük.
- **U-09** (kısmen): Bölge×ay anız takvimi yıl hariç öğrenilir (döngüsellik önlemi); WorldCover'da anız noktalarının %79,3 ekili alanda (ölçüldü). Ama saha/yanmış alan doğrulaması yok ve ay tek başına ayırmıyor (kaldıraç 0,928 (ölçüldü)).
- **U-18** (kısmen): ESA WorldCover kullanıldı (ölçüldü). FIRMS API betiği hazır ama çalıştırılmadı; swath ve STA maskesi toplu olarak bulunamadı (kapsam çıkarım, STA yok (doğrulanmadı)); MCD64A1 kullanılmadı.

**Doğrulanmayanlar ve sınırlar (kısa liste; tamamı Doğruluk Raporu §9):**

1. **2026 için MODIS-eşdeğer seri güvenilmez** [doğrulanmadı]: Aqua öğle geçişi 10,7 UTC (2015) iken 12,65 UTC'ye (2026) kaydı; Aqua ile VIIRS'in eşzamanlı çift payı 0,839 iken 0,182 değerine düştü. Eşdeğer bandın 2026'da gerçek MODIS'i kapsama oranı 0,545 (ölçüldü); LOYO döneminde 0,9226 (ölçüldü). Son tam ayda eşdeğer seri oranı 1,697 kat (tahmini) verirken iki sensörün kendi ölçümü 0,876 kat (ölçüldü) (MODIS) ve 0,944 kat (tahmini) (VIIRS): çelişki. Yörünge kaymasını gidermeyen ('kaymasız') bir kalibrasyon varyantı ölçülmedi.
2. **MODIS bittikten sonra serinin doğruluğu** [doğrulanmadı]: Terra/Aqua sona erince seri yalnız 2012–2025 kalibrasyonuna dayanır. Bu rejimin bağımsız doğrulaması yoktur; çünkü karşılaştırılacak gerçek MODIS kalmayacak. Aylık ülke hata bandı [−59,57 ; 74,99] % (tahmini) geniştir.
3. **Sensör farkı çözüldü iddiası yok** [tahmini]: Harmonize seri, gerçek MODIS'in aynı penceredeki değişimini 3,55 yüzde puan (tahmini) farkla izliyor. Bu fark LOYO yıllık %95 hata aralığı [−23,49 ; 9,51] % (tahmini) içinde; ama harmonize sıçrama, geçiş dışı doğal yıllık değişim aralığı [−39,3 ; 92,61] % (tahmini) içinde değil (içinde mi: hayır (tahmini)), çünkü gerçek MODIS de bu aralığın dışında. C10 ölçütü ilk sonuç görüldükten sonra inceltildi (audit/degisim_gunlugu.md); bu bir yöntem seçimidir ve sonuca göre ayarlanmış olabileceği kabul edilir.
4. **(ii) ile (i) yöntemleri ayırt edilemez** [ölçüldü]: Ay×bölge WAPE: (i) 30,64 % (ölçüldü), (ii) 30,63 % (ölçüldü); fark %95 aralığı [−2,97 ; 4,26] yüzde puan (tahmini). Yıllık toplamda (i) daha iyi (MAPE 4,83 % (ölçüldü) karşı 8,33 % (ölçüldü)). Asıl kazanç gözlem eforu (uydu sayısı) normalizasyonudur; (ii)'nin (i)'den üstün olduğu iddia edilmez. Kazanan seçimi LOYO sonuçları üzerinde yapıldığı için hata hafif iyimser olabilir.
5. **Anız için yer doğrulaması yok** [doğrulanmadı]: Anız etiketi kural tabanlıdır ve yalnız dolaylı kanıtla sınandı: ESA WorldCover'da anız noktalarının %79,3 ekili alanda (ölçüldü), kaba ulusal hasat penceresiyle uyum %74,2 (tahmini). Saha, yanmış alan (MCD64A1) veya AFAD/OGM kaydıyla karşılaştırma yapılmadı. Ay tek başına anızı ayırmaz (LOYO kaldıraç 0,928 (ölçüldü)).
6. **Static Thermal Anomalies (STA) maskesi karşılaştırılmadı** [doğrulanmadı]: FIRMS STA maskesi için toplu indirme bulunamadı; karşılaştırma sonucu: yok (doğrulanmadı). Yerine NASA arşivindeki type=2 ile uyum ölçüldü; bu aynı şey değildir ve type=2 yer gerçeği değil bir maskedir.
7. **Sanayi kuralı MODIS döneminde zayıf uyuşuyor** [ölçüldü]: NASA type=2 ile uyuşma VIIRS döneminde kesinlik 0,924 (ölçüldü), MODIS döneminde 0,2278 (ölçüldü). Referans seyrek olduğu için; kuralın 'sanayi' dediği MODIS noktalarının %66,6 bilinen bir tesise yakın. Bu 'uyuşma' ölçüsüdür, doğruluk değil.
8. **Referans doğrulama seti küçük ve tesis yakalaması düşük** [tahmini]: Set: 26 sanayi tesisi (OpenStreetMap) ve 8 bilinen yangın (Wikipedia + ilçe merkezi); 3 kayıt çakışma nedeniyle ayıklandı. Dengeli kesinlik 0,9711 (tahmini), tesis yakalama 0,4777 (tahmini) (tesis düzeyinde 0,4783 (tahmini)): bazı tesisler (özellikle termik santraller) kaçıyor. Yangın pencereleri ve yarıçapları yaklaşık. Nokta düzeyi kesinlik (0,9999 (tahmini)) sınıf dengesizliğinden şişkindir ve sunumda kullanılmaz.
9. **Gözlem kapsamı (swath) çıkarımdır** [tahmini]: NASA uydu geçiş şeridi (swath) verisi toplu indirilemedi; kesinti günleri tespit sayılarından çıkarıldı (129 uydu-gün (tahmini)). Geçiş pencereleri tespit saatlerinin yüzdeliklerinden türetildi. Gerçek geçiş listesiyle doğrulanmadı.
10. **Ekran okuyucu testi yapılmadı** [doğrulanmadı]: Klavyeyle ulaşılabilir etkileşimli öğe payı %88,4, adı olan öğe payı %100, en düşük kontrast 4,59 (ölçüldü) (ölçüldü); renk körlüğü ayırt edilebilirliği ölçüldü. Ekran okuyucuyla elle sınama ve harita zemini/Leaflet iç kontrolleri ölçüm dışıdır.
11. **İl düzeyinde MODIS-eşdeğer seri yok** [doğrulanmadı]: Eşdeğer seri yalnız ülke ve 7 bölge düzeyinde LOYO ile doğrulandı (olay biriminde ay×il WAPE 46,27 % (ölçüldü) ile daha yüksek). İl düzeyi için ayrı bir doğrulama yoktur.
12. **Güven sınıfı eşlemesi zayıf ilişkili** [tahmini]: Öğrenilen MODIS eşiği [35 ; 82] MODIS % (tahmini) FIRMS cetveline yakın; ama iki uydunun tek yangındaki güveni zayıf ilişkili (Spearman 0,2138 (ölçüldü)) ve öğrenilmiş eşleme FIRMS'i geçmedi (kappa 0,1765 (ölçüldü) karşı 0,1918 (ölçüldü)). Arayüzde varsayılan ham FIRMS sınıfıdır.
13. **Anomali bandı geniştir** [tahmini]: Eşdeğer seride anomali işareti, belirsizlik bandı yüzünden 33,53 % (tahmini) oranında 'belirsiz'e düşüyor. Ağu–Eyl ay medyanları istatistiksel olarak ayırt edilemez (ayırt edilemez bayrağı: 1 (ölçüldü)).
14. **WorldCover tek yıl ve örneklem** [tahmini]: ESA WorldCover 2021 tek yıldır; 2000–2026 noktalarında arazi değişimi yok sayıldı, WorldCover'ın kendi sınıflandırma hatası ölçülmedi, örneklem tabanlıdır.
15. **FIRMS API ile otomatik çekme çalıştırılmadı** [doğrulanmadı]: `src/pipeline/firms_api.py` betiği hazır (kota 5000 işlem/10 dk'ya uygun) fakat API anahtarı yok ve çalıştırılmadı. Veri, elle indirilmiş 1.414.674 satırlık arşivden gelir; son gün 2026-11-12.
16. **Terra'nın 2026 durumu belirsiz** [doğrulanmadı]: Mevcut durum belgesindeki 'Mart 2026'da beklemeye alındı' iddiası doğrulanamadı; veride Terra tespiti son güne kadar sürüyor. Planlı bitiş tarihleri ikincil kaynaktan, doğrulanmadı.
17. **Zaman: sabit UTC+3** [tahmini]: TR günü her yıl için sabit UTC+3 alınır; 2016 öncesi kış saati (UTC+2) etkisi 21:00–21:59 UTC tespitlerini ertesi güne kaydırır, etkisi küçük kabul edildi (denetçi örneklemle ölçebilir).
18. **Mevcut ay kutusu ve 2026 kısmi yıl** [doğrulanmadı]: Son veri günü 2026-11-12; mevcut ay 12 gün (ölçüldü) kısmidir ve NRT payı 100 % (ölçüldü). Mevcut ay oranı MODIS 0,127 kat (tahmini), VIIRS 0,243 kat (tahmini); MODIS'in ek düşüşünün nedeni (sensör ömrü sonu, NRT, yörünge kayması) doğrulanmadı.
19. **Harita zemini çevrimiçi** [ölçüldü]: Uygulama internet olmadan açılır (C21, kütüphaneler yerelde); yalnız isteğe bağlı çevrimiçi harita zemini internet ister, yoksa il sınırları görünür.
20. **Hotspot yangın değildir; risk tahmini yoktur** [ölçüldü]: Gösterilen şey tarihsel hotspot/olay aktivitesidir. Gelecekteki yangın riski veya tehlikesi tahmin edilmez (K14). Nokta sayısı yangın sayısı değildir: 1.414.674 noktadan 471.978 olay çıkar.

Otomatik eklenenler (`audit/check_results.json` ve `audit/bulgular.md`; güzelleştirilemez):
- Açık denetim bulgusu **F2-10** (düşük, açık): Sabit yıl/saat sabitleri (K9, K11) (doğrulanmadı)
- Açık denetim bulgusu **F2-11** (düşük, açık): Belge tutarsızlıkları (doğrulanmadı)
- Açık denetim bulgusu **F2-12** (düşük, açık): Kontrol zayıflıkları — `tools/check_all.py` (doğrulanmadı)
- Açık denetim bulgusu **F4-04** (düşük, kısmen): Görüntü kusurları (doğrulanmadı)
- Açık denetim bulgusu **F5-03** (düşük, açık): Etiket (C24) — türetilmiş sonuç "ölçüldü" (doğrulanmadı)

## 8. Muhtemel sorular ve kanıtlı cevaplar

Sorular `audit/soru_cevap.md` dosyasından (denetçi provası); cevaplar ve sayılar bu raporda `metrics.json`'dan yeniden çekilmiştir. Her cevabın sonunda kullanılan metrik kimlikleri ve denetçinin durum notu vardır.

### Soru 1. Harmonizasyon gerçekten işe yarıyor mu?

**Basitçe:** Evet, ve bunu "sınav sorusunu önceden görmeden" sınadık: her yılı sırayla saklayıp kalan yıllardan öğrendik.
**Kanıt:** Yıllık MAPE 8,33 % (ölçüldü), R² 0,8716 (ölçüldü), sapma 0,55 % (ölçüldü). Efor düzeltmesi olmayan tek oran aynı testte MAPE 42,12 % (ölçüldü), R² −1,7204 (ölçüldü) verdi. Yıllık %95 hata aralığı [−23,49 ; 9,51] % (tahmini): yani tek bir yılın tahmini yine de yaklaşık bu aralıkta şaşabilir.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* loyo_mape, loyo_r2, loyo_bias, harm_i0_yillik_mape, harm_i0_yillik_r2, loyo_ci95

### Soru 2. 2012 sıçraması gerçek mi, sensör mü?

**Basitçe:** Büyük ölçüde sensör: yeni termometre geldi, aktivite aslında azalmıştı.
**Kanıt:** Ham seri geçişte 143,13 % (ölçüldü) sıçrıyor. Gerçek MODIS aynı pencerede −44,9 % (ölçüldü); harmonize seri −41,35 % (tahmini); fark 3,55 yüzde puan (tahmini), LOYO aralığı [−23,49 ; 9,51] % (tahmini) içinde. Bu, "artış sensör eklenmesindendir" demek için güçlü ama kesin olmayan kanıttır; 2012'de ek bir iklim/yangın etkisini ayırt edemeyiz.

*Denetçi durumu:* cevaplanabilir (bkz. 3). *metrics.json kimlikleri:* jump_raw_pct, jump_modis_gercek_pct, jump_harm_pct, jump_resid_pct, loyo_ci95

### Soru 3. "Sıçrama kayboldu" demek dürüst mü? Ölçütü sonuca göre değiştirmediniz mi?

**Basitçe:** Hayır, "kayboldu" demek dürüst olmaz; ölçütü sonuç görüldükten sonra inceltmek zorunda kaldık ve bunu açıkça söylüyoruz.
**Kanıt:** İlk ölçüt (harmonize sıçrama doğal aralıkta olmalı) sağlanmadı çünkü gerçek MODIS de aralığın dışındaydı ([−39,3 ; 92,61] % (tahmini); harmonize aralıkta mı: hayır (tahmini)). Ölçüt "artık sıçrama LOYO hata aralığında" olarak değiştirildi (`audit/degisim_gunlugu.md`). Doğru cümle: harmonize seri gerçek MODIS düşüşünü 3,55 yüzde puan (tahmini) farkla izliyor. Bağımsız denetçi, 3+3 yıllık pencerelerle ayrıca sınadı ve sonucu ölçüt seçiminden bağımsız buldu (`audit/bulgular.md` F2-07).

*Denetçi durumu:* cevaplanabilir, dürüstlük notuyla. *metrics.json kimlikleri:* jump_null_ci95, jump_harm_dogal_aralikta, jump_resid_pct

### Soru 4. Neden tek bir oran kullanmadınız?

**Basitçe:** Tek oran, bazı ayları fazla bazılarını az sayar; asıl düzeltilmesi gereken şey kaç uydunun baktığıdır.
**Kanıt:** Efor düzeltmesiz tek oran ay×bölge WAPE 52,68 % (ölçüldü); eforlu sabit oran (i) 30,64 % (ölçüldü); bölge×mevsim×büyüklük oranı (ii) 30,63 % (ölçüldü). (i) ile (ii) ayırt edilemez (fark %95 aralığı [−2,97 ; 4,26] yüzde puan (tahmini)); yani (ii)'nin üstün olduğunu iddia etmiyoruz, asıl kazanç efor. (ii), uygulamanın birimi ay×bölge olduğu için seçildi.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* harm_i0_ay_bolge_wape, harm_i_ay_bolge_wape, harm_ii_ay_bolge_wape, harm_ii_eksi_i_wape_ci95

### Soru 5. Sabit oran olay sayısını tespitten fazla gösterme hatası (B-04) burada var mı?

**Basitçe:** Kontrol ettik: olay sayısı hiçbir bölge ve ayda tespit sayısını aşmıyor; aşan hücreler kırpılıyor.
**Kanıt:** Kırpılan hücre sayısı ay×bölge 98 hücre (ölçüldü), ay×ülke 6 hücre (ölçüldü), yıl×ülke 0 hücre (ölçüldü); denetçinin bağımsız sorgusu olay eşdeğeri > tespit eşdeğeri ihlali bulmadı (`audit/bulgular.md` F2-01 kapanışı).

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* olay_tespitle_kirpilan_temiz_ay_bolge, olay_tespitle_kirpilan_temiz_ay_TR, olay_tespitle_kirpilan_temiz_yil_TR

### Soru 6. Bir MODIS pikseline 4 VIIRS düşüyor; çift saymıyor musunuz?

**Basitçe:** Sayıyoruz ama bir kez: yakın yerde yakın zamanda gelen noktalar aynı yangındır, MODIS'ten de VIIRS'ten de gelse.
**Kanıt:** Çakışma döneminde ortak kümeleme 380.975 (ölçüldü) olay verir; sensörler ayrı kümelenseydi 440.176 olay (ölçüldü) olurdu: 59.201 olay (ölçüldü) çifte sayım önlenir. MODIS izi başına ortalama 3,349 nokta (ölçüldü) VIIRS noktası düşer; sabit ızgara aynı izi 1,764 hücre (ölçüldü) parçaya bölerdi.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* events_joint_overlap, events_separate_overlap, events_double_count_avoided, mcell_iz_basina_viirs, mcell_iz_basina_izgara

### Soru 7. MODIS'in gördüğü yangınların çoğunu VIIRS neden görmüyor?

**Basitçe:** Çünkü iki uydu aynı anda bakmıyor; MODIS'in gördüğü kısa ömürlü yangını VIIRS'in geçişi kaçırabiliyor.
**Kanıt:** MODIS olaylarının VIIRS'te de görülme payı %38,2. Ayak izi eşleştirmesi bunu sabit 1 km kuralına göre (%35,5) biraz artırır ama asıl neden değildir. Eşzamanlı Aqua geçişinde bile en yakın VIIRS 1 km içinde olanların payı %53,1. (Yalnız-MODIS olayların çoğunun sabah Terra geçişinden gelmesi `docs/kumeleme_yontemi.md` §1'de tespit düzeyinde ölçülmüştür.)

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* events_modis_seen_by_viirs_share, events_modis_seen_by_viirs_share_sabit, aqua_nearest_viirs_within_1km_share

### Soru 8. VIIRS küçük yangınları sayınca neden artış yok?

**Basitçe:** VIIRS küçük yangınları da görür; bu yüzden ham sayısı artar. Onu MODIS'in görebileceği ölçeğe çevirince artış kayboluyor.
**Kanıt:** Ham yalnız-VIIRS geçişi 88,03 % (ölçüldü). VIIRS'ten türetilen MODIS-eşdeğer seri, çakışma döneminde gerçek MODIS'le toplamda −0,52 % (tahmini) sapmayla uyumlu. Artış küçük yangınların görünür olmasındandır; aktivitenin arttığı anlamına gelmez.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* jump_raw_viirs_only_pct, equiv_overlap_bias

### Soru 9. Anız ile orman yangınını nasıl ayırdınız?

**Basitçe:** Anızı küçük, kısa, zayıf ve belli aylarda olan ateş olarak tanımlıyoruz; bu kural tabanlıdır ve doğrulaması yalnız dolaylıdır.
**Kanıt:** Bölgeye özgü anız ayları yıl dışarıda bırakmayla öğrenilir; olay düzeyinde karar verilir (`n_mcell` ile). Bağımsız arazi haritası (ESA WorldCover): anız noktalarının %79,3 ekili alanda; büyük temiz yangınların %50,3 ekili, %32,1 ağaçlı alanda. Dürüst sınır: ay tek başına ayırmıyor (LOYO kaldıraç 0,928 (ölçüldü)). **Saha veya yanmış alan doğrulaması yok.**

*Denetçi durumu:* cevaplanabilir; anız için yer-doğrulama (saha/yanmış alan) **yok**. *metrics.json kimlikleri:* temizlik_wc_aniz_ekili_alan_pay, temizlik_wc_buyuk_temiz_ekili_alan_pay, temizlik_wc_buyuk_temiz_agac_pay, temizlik_aniz_loyo_kaldirac

### Soru 10. Sanayi bacalarını nasıl attınız, yanlışlıkla gerçek yangın sildiniz mi?

**Basitçe:** Hiçbir noktayı silmedik, etiketledik; gerçek yangını korumak için özel bir koruma kuralı var. Ama bazı tesisler kaçıyor ve bunu saklamıyoruz.
**Kanıt:** Referans setinde dengeli kesinlik 0,9711 (tahmini); gerçek yangın noktalarının %99,8 korunuyor, yangın başına yanlış işaret 0,0142 (tahmini). Tesis yakalama 0,4777 (tahmini) (tesis düzeyinde 0,4783 (tahmini)): bazı tesisler kaçıyor. Set küçük (26 tesis, 8 yangın). Nokta düzeyi kesinlik (0,9999 (tahmini)) sınıf dengesizliğinden şişkindir, sunumda kullanılmaz.

*Denetçi durumu:* cevaplanabilir; "%99,97" kullanılmamalı. *metrics.json kimlikleri:* ref_precision, temizlik_ref_yangin_koruma, temizlik_ref_makro_yangin_fpr, ref_recall, temizlik_ref_site_recall, dogrulama_sanayi_tesis, dogrulama_bilinen_yangin, temizlik_ref_nokta_precision

### Soru 11. 2000–2011 sanayi kesinliği neden %23?

**Basitçe:** O dönemde NASA'nın kendi "sanayi" etiketi çok seyrek, bu yüzden bizim kuralımız yeni bulduğu yerleri "yanlış" sayılıyor; bu uyuşma ölçüsüdür, doğruluk değil.
**Kanıt:** MODIS döneminde NASA type=2 ile kesinlik 0,2278 (ölçüldü), VIIRS döneminde 0,924 (ölçüldü). Kuralın 'sanayi' dediği MODIS noktalarının %66,6 bilinen bir tesise yakın.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* temizlik_sanayi_loyo_precision_modis_donemi, temizlik_sanayi_loyo_precision_viirs_donemi, temizlik_modis_donemi_sanayi_tesis_payi

### Soru 12. MODIS bittiğinde ne olacak?

**Basitçe:** Seri VIIRS'ten MODIS-eşdeğere çevrilerek sürer; ama bu kısmın doğruluğunu gösteremiyoruz, çünkü kıyaslanacak MODIS kalmayacak.
**Kanıt:** Aqua öğle geçişi 10,7 saat (UTC) (ölçüldü) (2015) → 12,65 saat (UTC) (ölçüldü) (2026) kaydı; Aqua–VIIRS eşzamanlı çift payı %83,9 → %18,2. 2026'da eşdeğer bandı gerçek MODIS'i %54,5 oranında kapsıyor (LOYO döneminde %92,3). Yörünge kaymasını gidermeyen kalibrasyon varyantı ölçülmedi. **Eksik: MODIS sonrası dönem için bağımsız doğrulama yok.**

*Denetçi durumu:* **kısmen eksik** (MODIS-sonrası doğrulama yok; F4-01). *metrics.json kimlikleri:* aqua_gunduz_gecis_utc_2015, aqua_gunduz_gecis_utc_2026, aqua_viirs_esz_cift_payi_2015, aqua_viirs_esz_cift_payi_2026, harm_2026_bant_kapsama, equiv_band_kapsama_ay_tr

### Soru 13. 2026 neden düşük?

**Basitçe:** Kısmen gerçek (iki sensör de düşük), kısmen belirsiz (MODIS'in ek düşüşünün nedenini bilmiyoruz).
**Kanıt:** Son veri günü 2026-11-12; mevcut ay 12 gün (ölçüldü) kısmi, NRT payı 100 % (ölçüldü). Geçmiş medyana oran: MODIS 0,127 kat (tahmini), VIIRS 0,243 kat (tahmini). MODIS'e özgü ek düşüşün nedeni (sensör ömrü sonu, NRT, yörünge kayması): MODIS'e özgü ek düşüş: sensör ömrü sonu, NRT veya yörünge kayması şüphesi (doğrulanmadı). Son tam ayda eşdeğer seri oranı 1,697 kat (tahmini) ama iki sensörün kendi oranları 0,876 kat (ölçüldü) ve 0,944 kat (tahmini); bu yüzden eşdeğer güvenilmez işaretlenir (1 (doğrulanmadı)).

*Denetçi durumu:* cevaplanabilir. Dikkat: ekrandaki "Ekim 2026 %170" (eşdeğer) iki sensörle çelişiyor → F4-01 düzelmeden gösterilmemeli. *metrics.json kimlikleri:* veri_son_gun, takvim_mevcut_ay_kismi_gun_TR, takvim_mevcut_ay_nrt_payi_TR, takvim_mevcut_ay_oran_modis_temiz_TR, takvim_mevcut_ay_oran_viirs_temiz_ub_TR, takvim_mevcut_ay_ayrisma_yorum_TR, takvim_son_tam_ay_oran_modis_esdeger_TR, takvim_son_tam_ay_oran_modis_temiz_TR, takvim_son_tam_ay_oran_viirs_temiz_ub_TR, takvim_son_tam_ay_guvenilmez_modis_esdeger_TR

### Soru 14. Hangi aylar en yoğun, sıralama güvenilir mi?

**Basitçe:** Yaz sonu ve sonbahar; ama ağustos ile eylül birbirinden istatistiksel olarak ayrılamıyor.
**Kanıt:** Türkiye MODIS temiz serisinde ilk üç ay Haz > Eyl > Ağu (ölçüldü); MODIS-eşdeğer seride Ağu > Eyl > Haz (tahmini); olay serisinde Eyl > Ağu > Eki (tahmini). Ayırt edilemezlik bayrağı 1 (ölçüldü) (1 = evet). Temizlik, il düzeyinde ilk üç ayın 79 % (tahmini) oranında değiştirir.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* takvim_top3_ay_modis_temiz_TR, takvim_top3_ay_modis_esdeger_TR, takvim_top3_ay_olay_TR, takvim_ayirt_edilemez_modis_temiz_TR, takvim_ham_temiz_top3_degisen_il_payi

### Soru 15. Hotspot sayısı yangın riski mi?

**Basitçe:** Hayır. Uygulama tarihsel hotspot yoğunluğunu gösterir; gelecekteki yangın riskini veya tehlikesini tahmin etmez.
**Kanıt:** Arayüz alt başlığı "tarihsel yangın aktivitesi (yangın riski değildir)" (`src/app/i18n/tr.json`, `app.sub`). 1.414.674 (ölçüldü) nokta 471.978 (ölçüldü) olaya iner; nokta sayısı yangın sayısı değildir.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* veri_toplam_nokta, huni_olay_sayisi

### Soru 16. Ekrandaki sayılar elle mi yazıldı?

**Basitçe:** Hayır; ekrandaki sayılar betikle üretilmiş dosyalardan okunur, ayrıca denetçi örnekleme ile ekranı veriyle karşılaştırdı.
**Kanıt:** C14 (ekran = hesap) ve C15 (rastgele/sabit metrik taraması) geçti; denetçinin çalışma anı karşılaştırmasında fark 0 (`audit/bulgular.md` F4). Bağımsız yeniden hesapta 97 karşılaştırma (ölçüldü) girdinin 93 tanesinde fark 0.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* yh_girdi, yh_fark_sifir

### Soru 17. Uydu kesintisi olan günler "yangın yok" mu sayılıyor?

**Basitçe:** Hayır; uydunun bakmadığı günler "gözlem yok" ayrı renkle gösterilir ve aylık hesapta paydadan düşülür. Ama kesinti günlerini NASA'nın geçiş listesinden değil, tespit sayılarından çıkardık.
**Kanıt:** Çıkarımla kesinti işaretli uydu-günü: 129 uydu-gün (tahmini) (`coverage.parquet`, etiket tahmini); C06 geçti.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* kapsam_kesinti_uydu_gunu

### Soru 18. Belirsizlik ne kadar?

**Basitçe:** Belirsizlik küçük değil; bunu bant olarak gösteriyoruz.
**Kanıt:** Aylık ülke toplamı için %95 hata bandı [−59,57 ; 74,99] % (tahmini); bu bant gerçek MODIS'i LOYO'da ay×ülkede %92,3 oranında kapsadı. Yıllıkta [−23,49 ; 9,51] % (tahmini).

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* equiv_overlap_band, equiv_band_kapsama_ay_tr, loyo_ci95

### Soru 19. Neden varsayılan ana seri olarak MODIS-eşdeğer seriyi seçtiniz; VIIRS'in 375 m ayrıntısı kaybolmuyor mu?

**Basitçe:** İki farklı ihtiyacı ayırdık: 25 yıllık zaman karşılaştırması için eski ve yeni termometreyi aynı dile çeviren MODIS-eşdeğer seriyi başa koyduk; ayrıntıyı görmek isteyen için ise hassas 375 m VIIRS verisini haritada ve tek düğmede yan yana açık bıraktık.
**Kanıt:** Kullanıcı onayıyla bilimsel standart (S3 kararı, `docs/01_ISTEKLER.md` §E): takvim/trend varsayılanı `olay_esdeger` / `modis_esdeger` (yıllık LOYO MAPE 8,33 % (ölçüldü)); aynı anda yalnız VIIRS katmanı (287.781 (ölçüldü) olay) harita ve laboratuvarda korunur. Üst bardaki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya `#seriesSel` ile tek tıkla değiştirilir.

*Denetçi durumu:* cevaplanabilir. *metrics.json kimlikleri:* loyo_mape, events_match_yalniz_viirs

### Soru 20. Uygulama internet ve dış kütüphane olmadan nasıl çalışıyor; performans ve erişilebilirlik sınırları neler?

**Basitçe:** Uygulama bir klasörü çift tıklayıp internet kesikken bile açılacak kadar bağımsızdır; filtre değiştiğinde saniyenin dörtte birinde yeniden hesaplar.
**Kanıt:** Dış CDN bağlantısı sıfırdır (C21); 27 yıllık 302.863 olay (ölçüldü) temiz olayda eşik değişimi ortalama 0,253 s (ölçüldü) sürer (C20); minimum WCAG kontrast 4,59 (ölçüldü) ve renk körlüğü dE en az 14,0 (C19). **Doğrulanmayan:** Ekran okuyucuyla elle tarayıcı testi yapılmadı (`doğrulanmadı`).

*Denetçi durumu:* cevaplanabilir (ekran okuyucu doğrulanmadı). *metrics.json kimlikleri:* perf_olay_sayisi, perf_esik_degisimi_sn, a11y_kontrast_min


## 9. Cevaplanamayan sorular (eksikler)

Aşağıdakiler için elimizde yeterli kanıt yoktur; biri sorarsa "bunu doğrulayamadık" denmelidir.

- Soru 12: MODIS bittiğinde ne olacak? — ****kısmen eksik** (MODIS-sonrası doğrulama yok; F4-01)**

Denetçinin eksik listesi: (12) MODIS-sonrası dönem için bağımsız doğrulama/kaymasız kalibrasyon varyantı; (9) anız için yer-doğrulama verisi; il düzeyinde eşdeğer serinin ayrı doğrulaması (yalnız ay×bölge/ülke düzeyinde LOYO var); (20) ekran okuyucuyla canlı sınama.

## 10. Kapanış

"Bu proje yangın sayısı üretmiyor; yangın verisine ne kadar güvenebileceğimizi ölçüyor. 1.414.674 ham noktadan 471.978 olay çıkardık, VIIRS'i MODIS diline çevirdik, bir yılı saklayıp tahmin ederek sınadık (8,33 % (ölçüldü)); gerçek MODIS düşüşünü 3,55 yüzde puan (tahmini) farkla izledik ve 2026 için eşdeğer serimize güvenmediğimizi, tesis yakalamamızın 0,4777 (tahmini) olduğunu, anızı sahada doğrulayamadığımızı açıkça söylüyoruz. Sayıların her biri tek bir dosyadan, `metrics.json`'dan gelir; yanında dürüstlük etiketi vardır."
