# Doğruluk Raporu

Veri sürümü: {{meta.veri_surumu}} · Üretim tarihi: {{meta.uretim_tarihi}}
Denetçi durumu: {{meta.denetim_durumu}}

> Bu rapor "ne kadar doğru, neyi doğrulayamadık" sorusunu cevaplar. Her sayı `reports/metrics.json` kimliğiyle izlenir; yanındaki etiket **ölçüldü** (veriden sayıldı), **tahmini** (model/kural/çıkarım) veya **doğrulanmadı** (bağımsız kanıt yok) anlamına gelir (K5). Her bölüm önce **Basitçe**, sonra **Teknik olarak** anlatır.

## 1. Özet

**Basitçe:** Sayıları iki kez saydık: bir kez üretim koduyla, bir kez de üretimi yazmayan bağımsız bir denetçiyle. Uyuştular. Yöntemi, test ettiği yılı hiç görmeden sınadık. Sonuç iyi ama kusursuz değil: 2026 için eşdeğer seriye güvenilmez, bazı tesisler kaçıyor ve bazı şeyleri hiç doğrulayamadık; hepsi §9'da açıkça yazılıdır.

**Teknik olarak:** Kabul kriterleri C01–C25: geçen {{kontrol.gecen}} / {{kontrol.toplam}}, kalan {{kontrol.kalan}}, atlanan {{kontrol.atlanan}} (§8). Bağımsız yeniden hesap (C23): {{kontrol.bagimsiz_sonuc}}. Açık bulgular: yüksek {{bulgu.acik_yuksek}}, orta {{bulgu.acik_orta}}, düşük {{bulgu.acik_dusuk}}; kapanan {{bulgu.kapanan}} (§10).

Ana sonuçlar (tamamı aşağıda ayrıntılı):

| Ölçü | Değer | Not |
|---|---|---|
| Yıllık MAPE (LOYO) | {{loyo_mape|t}} | kalibrasyon dışı yıllarda |
| Yıllık R² (LOYO) | {{loyo_r2|t}} | |
| Artık sıçrama (harmonize − gerçek MODIS) | {{jump_resid_pct|t}} | LOYO %95 aralığı {{loyo_ci95|t}} içinde |
| Bağımsız yeniden hesapta fark 0 olan girdi | {{yh_fark_sifir|t}} / {{yh_girdi}} | denetçi, farklı yöntem |
| Referans dengeli kesinlik | {{ref_precision|t}} | tesis yakalama {{ref_recall|t}} |

## 2. Doğrulama yöntemi: sınav sorusunu önceden görmemek (K4)

**Basitçe:** Öğrenciye sınav sorusunun cevabını verip aynı soruyla notlamak olmaz. Her yılı sırayla "saklıyoruz", kalan yıllardan oran öğreniyoruz, saklanan yılı tahmin edip gerçek MODIS ile karşılaştırıyoruz.
**Teknik olarak:** Test: {{loyo_method|t}}. Kalibrasyon yıllarında yapılan test geçerli sayılmaz (C09). Eşik seçimleri (sanayi N, M, Y, S) de LOYO ile yapıldı. 2026 kısmi yıl ve NRT olduğu için test dışıdır ve düşük güven etiketlidir.

## 3. Harmonizasyon doğruluğu (C09, C11)

**Basitçe:** Hassas termometrenin ölçümünü eski termometrenin diline çevirdik. "Eski termometre görseydi kaç sayardı?" tahminimiz, saklanan yıllarda gerçekle ortalama bu kadar yüzde sapıyor.

| Ölçü | Değer | Etiket |
|---|---|---|
| Dışarıdaki yıllarda yıllık MAPE | {{loyo_mape}} % | {{etiket:loyo_mape}} |
| Yıllık R² | {{loyo_r2}} | {{etiket:loyo_r2}} |
| Yıllık sapma (bias) | {{loyo_bias}} % | {{etiket:loyo_bias}} |
| Yıllık %95 hata aralığı | {{loyo_ci95}} % | {{etiket:loyo_ci95}} |
| Ay×bölge WAPE | {{loyo_ay_bolge_wape}} % | {{etiket:loyo_ay_bolge_wape}} |
| Ay×bölge R² | {{loyo_ay_bolge_r2}} | {{etiket:loyo_ay_bolge_r2}} |
| Çakışma döneminde toplam sapma (bias) | {{equiv_overlap_bias}} % | {{etiket:equiv_overlap_bias}} |
| Aylık ülke %95 hata bandı | {{equiv_overlap_band}} % | {{etiket:equiv_overlap_band}} |
| Bant kapsaması ay×bölge | {{equiv_band_kapsama_ay_bolge|yuzde}} | {{etiket:equiv_band_kapsama_ay_bolge}} |
| Bant kapsaması ay×ülke | {{equiv_band_kapsama_ay_tr|yuzde}} | {{etiket:equiv_band_kapsama_ay_tr}} |
| **2026** bant kapsaması | {{harm_2026_bant_kapsama|yuzde}} | {{etiket:harm_2026_bant_kapsama}} |

**Teknik olarak:** Yöntem yarışı (hedef: Terra+Aqua tespiti, LOYO 2012–2025):

| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Sapma % | Yıllık %95 aralık |
|---|---|---|---|---|---|
| (i0) tek sabit oran, efor yok (B-04 tuzağı, yalnız kıyas) | {{harm_i0_ay_bolge_wape}} | {{harm_i0_yillik_mape}} | {{harm_i0_yillik_r2}} | {{harm_i0_yillik_bias}} | {{harm_i0_yillik_ci95}} |
| (i) tek sabit oran, eforlu | {{harm_i_ay_bolge_wape}} | {{harm_i_yillik_mape}} | {{harm_i_yillik_r2}} | {{harm_i_yillik_bias}} | {{harm_i_yillik_ci95}} |
| (ii) bölge × mevsim × FRP büyüklüğü, eforlu (kazanan) | {{harm_ii_ay_bolge_wape}} | {{harm_ii_yillik_mape}} | {{harm_ii_yillik_r2}} | {{harm_ii_yillik_bias}} | {{harm_ii_yillik_ci95}} |
| (iii) FRP eşik eğrisi, eforlu | {{harm_iii_ay_bolge_wape}} | {{harm_iii_yillik_mape}} | {{harm_iii_yillik_r2}} | {{harm_iii_yillik_bias}} | {{harm_iii_yillik_ci95}} |

Tüm bu sayılar ölçüldü (aralıklar tahmini). **Dürüst okuma (K5):** (ii) ile (i) ay×bölgede **ayırt edilemez** (WAPE farkı %95 aralığı {{harm_ii_eksi_i_wape_ci95|t}}); yıllık toplamda (i) daha iyi. Yani asıl kazanç gözlem eforu (uydu sayısı) düzeltmesidir (WAPE {{harm_i0_ay_bolge_wape|t}} → {{harm_i_ay_bolge_wape|t}}), (ii)'nin (i)'den üstün olduğu iddia edilmez. (ii) uygulamanın birimi (ay×bölge) için seçildi; seçim LOYO sonuçları üzerinde yapıldığından hata hafif iyimser olabilir. Etiket: kazanan seçimi {{harm_kazanan_yontem|t}}.

Birim ve küme varyantları (aynı LOYO ve sıçrama tanımı):

| Varyant | Yıllık MAPE % | Yıllık R² | Ham sıçrama % | Harmonize % | Gerçek MODIS % | Artık (puan) |
|---|---|---|---|---|---|---|
| tespit, temiz (ana) | {{tespit_temiz_yillik_mape}} | {{tespit_temiz_yillik_r2}} | {{tespit_temiz_jump_raw_pct}} | {{tespit_temiz_jump_harm_pct}} | {{tespit_temiz_jump_modis_gercek_pct}} | {{tespit_temiz_jump_resid_pct}} |
| olay, temiz | {{olay_temiz_yillik_mape}} | {{olay_temiz_yillik_r2}} | {{olay_temiz_jump_raw_pct}} | {{olay_temiz_jump_harm_pct}} | {{olay_temiz_jump_modis_gercek_pct}} | {{olay_temiz_jump_resid_pct}} |
| tespit, temiz+anız | {{tespit_temiz_aniz_yillik_mape}} | {{tespit_temiz_aniz_yillik_r2}} | {{tespit_temiz_aniz_jump_raw_pct}} | {{tespit_temiz_aniz_jump_harm_pct}} | {{tespit_temiz_aniz_jump_modis_gercek_pct}} | {{tespit_temiz_aniz_jump_resid_pct}} |
| olay, temiz+anız | {{olay_temiz_aniz_yillik_mape}} | {{olay_temiz_aniz_yillik_r2}} | {{olay_temiz_aniz_jump_raw_pct}} | {{olay_temiz_aniz_jump_harm_pct}} | {{olay_temiz_aniz_jump_modis_gercek_pct}} | {{olay_temiz_aniz_jump_resid_pct}} |

(Hepsi ölçüldü; harmonize sütunu tahmini.) Olay eşdeğeri, tespit eşdeğerini aşamaz (K8, B-04 kontrolü): aşan hücreler kırpıldı (ay×bölge {{olay_tespitle_kirpilan_temiz_ay_bolge|t}}, ay×ülke {{olay_tespitle_kirpilan_temiz_ay_TR|t}}, yıl×ülke {{olay_tespitle_kirpilan_temiz_yil_TR|t}}).

## 4. Sıçrama metriği (C10, U-15)

**Basitçe:** 2012'de ham seri bir anda fırlıyor. Soru: harmonize seri bu yapay fırlamayı gideriyor mu, ama gerçek bir değişimi de saklamıyor mu? Cevap için "gerçek MODIS aynı pencerede ne yaptı?" ile kıyaslıyoruz.

| Seri (geçiş {{veri_ilk_viirs_yili}}, {{cfg:harmonizasyon.sicrama_pencere_yil}}+{{cfg:harmonizasyon.sicrama_pencere_yil}} yıl) | Sıçrama | Etiket |
|---|---|---|
| Ham (MODIS → MODIS+VIIRS) | {{jump_raw_pct}} % | {{etiket:jump_raw_pct}} |
| Ham (MODIS → yalnız VIIRS) | {{jump_raw_viirs_only_pct}} % | {{etiket:jump_raw_viirs_only_pct}} |
| Harmonize (LOYO MODIS-eşdeğer) | {{jump_harm_pct}} % | {{etiket:jump_harm_pct}} |
| **Gerçek MODIS (aynı pencere)** | {{jump_modis_gercek_pct}} % | {{etiket:jump_modis_gercek_pct}} |
| Harmonizasyonun eklediği (harmonize − gerçek MODIS) | {{jump_resid_pct}} puan | {{etiket:jump_resid_pct}} |
| NOAA-20 eklenişi 2018: ham / eforlu / gerçek MODIS | {{jump_n20_2018_ham_pct}} / {{jump_n20_2018_eforlu_pct}} / {{jump_n20_2018_modis_pct}} % | {{etiket:jump_n20_2018_ham_pct}} |
| NOAA-21 eklenişi 2023: ham / eforlu / gerçek MODIS | {{jump_n21_2023_ham_pct}} / {{jump_n21_2023_eforlu_pct}} / {{jump_n21_2023_modis_pct}} % | {{etiket:jump_n21_2023_ham_pct}} |

**Teknik olarak ve dürüstlük notu (C10 inceltildi):** Başlangıçtaki ölçüt "harmonize sıçrama, geçiş dışı yıllık değişimlerin %95 aralığında olmalı" idi. İlk sonuç görüldüğünde gerçek MODIS'in kendisi de bu doğal aralığın dışına düştüğü anlaşıldı (2009–2011 MODIS'te olağandışı yüksek yıllar): ölçüt, gerçek yangın değişimini sensör sıçramasından ayıramıyordu. Bu yüzden ana ölçüt **artık sıçrama** olarak değiştirildi: harmonize − aynı penceredeki gerçek MODIS değişimi, yıllık LOYO %95 hata aralığında olmalı. Bu değişiklik **sonuç görüldükten sonra** yapıldı (`audit/degisim_gunlugu.md`); bu nedenle ölçütün kendisi sonuca göre seçilmiş olabilir. Bağımsız denetçi, artık sıçramayı ayrıca 3+3 yıllık pencerelerle sınadı ve dağılımının {{jump_resid_pct}} puanlık artığı kapsadığını buldu (`audit/bulgular.md` F2-07), yani sonuç ölçüt seçiminden bağımsız olarak sağlam görünüyor.

Güncel sonuç: artık {{jump_resid_pct|t}}; LOYO aralığı {{loyo_ci95|t}}; C10 ana ölçütü: {{c10_ana_varyant|t}}. Eski ölçüt (bilgi): doğal değişim aralığı {{jump_null_ci95|t}}; harmonize sıçrama bu aralıkta mı: {{jump_harm_dogal_aralikta|t}} (gerçek MODIS {{jump_modis_gercek_pct|t}} de dışarıda).

**Sonuç (K5, dürüst dil):** "Sensör farkını çözdük" **denmez**. Doğru cümle: *harmonize seri, gerçek MODIS düşüşünü {{jump_resid_pct|t}} farkla izliyor; bu fark yıllık hata aralığı içinde, ama aralığın kendisi geniştir ({{loyo_ci95|t}}).* Aynı fark olay biriminde {{olay_temiz_jump_resid_pct|t}}.

## 5. Temizlik doğruluğu (C13)

**Basitçe:** Kuralımız "bu baca" dediğinde ne sıklıkla haklı, bilinen tesislerin ne kadarını yakalıyor ve gerçek yangını yanlışlıkla silmiyor mu? FIRMS'ten bağımsız bir listeyle sorduk. Anız içinse elimizde yalnız dolaylı kanıt var.

**Teknik olarak:** Doğrulama seti `audit/dogrulama_seti.csv`: {{dogrulama_sanayi_tesis|t}} sanayi tesisi (OpenStreetMap), {{dogrulama_bilinen_yangin|t}} bilinen yangın (Wikipedia + ilçe merkezi), {{dogrulama_ayiklanan|t}} kayıt çakışmadan ayıklandı. Sınıflar eşit ağırlıklı (her tesise ve her yangına eşit oy).

| Ölçü | Değer | Etiket |
|---|---|---|
| Dengeli kesinlik (precision) | {{ref_precision}} | {{etiket:ref_precision}} |
| Makro tesis yakalama (recall) | {{ref_recall}} | {{etiket:ref_recall}} |
| Tesis düzeyi yakalama | {{temizlik_ref_site_recall}} | {{etiket:temizlik_ref_site_recall}} |
| Yangın başına yanlış işaret | {{temizlik_ref_makro_yangin_fpr}} | {{etiket:temizlik_ref_makro_yangin_fpr}} |
| Gerçek yangın noktası korunması | {{temizlik_ref_yangin_koruma}} | {{etiket:temizlik_ref_yangin_koruma}} |
| Yalnız kural (NASA type'sız), makro yakalama | {{temizlik_ref_kural_makro_recall}} | {{etiket:temizlik_ref_kural_makro_recall}} |
| Yalnız NASA statik etiketi, makro yakalama | {{temizlik_ref_nasa_makro_recall}} | {{etiket:temizlik_ref_nasa_makro_recall}} |
| Nokta düzeyi kesinlik / yakalama (şişkin, sunumda kullanılmaz) | {{temizlik_ref_nokta_precision}} / {{temizlik_ref_nokta_recall}} | {{etiket:temizlik_ref_nokta_precision}} |
| Sanayi LOYO uyuşması (NASA type=2): kesinlik / duyarlılık | {{temizlik_sanayi_loyo_precision}} / {{temizlik_sanayi_loyo_recall}} | {{etiket:temizlik_sanayi_loyo_precision}} (uyuşma, doğruluk değil) |
| aynı, VIIRS dönemi: kesinlik / duyarlılık | {{temizlik_sanayi_loyo_precision_viirs_donemi}} / {{temizlik_sanayi_loyo_recall_viirs_donemi}} | {{etiket:temizlik_sanayi_loyo_precision_viirs_donemi}} |
| aynı, MODIS dönemi: kesinlik / duyarlılık | {{temizlik_sanayi_loyo_precision_modis_donemi}} / {{temizlik_sanayi_loyo_recall_modis_donemi}} | {{etiket:temizlik_sanayi_loyo_precision_modis_donemi}} |
| MODIS dönemi 'sanayi' noktalarının bilinen tesise yakınlığı | {{temizlik_modis_donemi_sanayi_tesis_payi|yuzde}} | {{etiket:temizlik_modis_donemi_sanayi_tesis_payi}} |
| Anız LOYO kapsama / taban / kaldıraç | {{temizlik_aniz_loyo_kapsama}} / {{temizlik_aniz_loyo_taban}} / {{temizlik_aniz_loyo_kaldirac}} | {{etiket:temizlik_aniz_loyo_kapsama}} |
| Anız ayları ile ulusal hasat penceresi uyumu | {{temizlik_aniz_hasat_penceresi_payi|yuzde}} | {{etiket:temizlik_aniz_hasat_penceresi_payi}} |

**WorldCover (bağımsız arazi örtüsü, 2021, örneklem):**

| Grup | Ekili alan | Yapılaşmış | Ağaç | Çayır |
|---|---|---|---|---|
| Anız | {{temizlik_wc_aniz_ekili_alan_pay|yuzde}} | {{temizlik_wc_aniz_yapilasmis_pay|yuzde}} | {{temizlik_wc_aniz_agac_pay|yuzde}} | {{temizlik_wc_aniz_cayir_pay|yuzde}} |
| Büyük temiz olaylar | {{temizlik_wc_buyuk_temiz_ekili_alan_pay|yuzde}} | {{temizlik_wc_buyuk_temiz_yapilasmis_pay|yuzde}} | {{temizlik_wc_buyuk_temiz_agac_pay|yuzde}} | {{temizlik_wc_buyuk_temiz_cayir_pay|yuzde}} |
| Sanayi + kalıcı (kural) | {{temizlik_wc_kural_kalici_ekili_alan_pay|yuzde}} | {{temizlik_wc_kural_kalici_yapilasmis_pay|yuzde}} | {{temizlik_wc_kural_kalici_agac_pay|yuzde}} | {{temizlik_wc_kural_kalici_cayir_pay|yuzde}} |
| NASA statik kaynak | {{temizlik_wc_statik_nasa_ekili_alan_pay|yuzde}} | {{temizlik_wc_statik_nasa_yapilasmis_pay|yuzde}} | {{temizlik_wc_statik_nasa_agac_pay|yuzde}} | {{temizlik_wc_statik_nasa_cayir_pay|yuzde}} |

(Hepsi ölçüldü; ama yalnız kural etiketiyle arazi örtüsü **uyumu**dur, yer doğrulaması değil.) Static Thermal Anomalies maskesi karşılaştırması: {{temizlik_sta_maskesi_karsilastirma|t}}. Anız takviminin saha/yanmış alan ile bağımsız doğrulaması: **yapılmadı (doğrulanmadı)**.

## 6. Kümeleme doğruluğu (C03, C04, C05, C12)

**Basitçe:** Kümelemeyi hızlı yapan kodun, çok yavaş ama kesin "her noktayı her noktayla karşılaştır" yöntemiyle aynı sonucu verdiğini gösterdik; ayrıca kasten bozuk bir yöntemi testin yakalayıp yakalayamadığına baktık.
**Teknik olarak:** Hızlı kümeleme = kaba kuvvet: {{c03_orneklem|t}} ({{c03_nokta}} nokta), {{c03_kural}} kural çeşidi, {{c03_karsilastirma}} karşılaştırmanın hepsinde fark {{c03_fark_olan|t}}; kasten hatalı yöntem {{c03_mutasyon_yakalanan}}/{{c03_mutasyon_toplam}} örneklemde yakalandı (C03, `src/clustering/bruteforce_check.py`). Çifte sayım: çakışma döneminde ortak {{events_joint_overlap|t}} ≤ ayrı {{events_separate_overlap|t}}; önlenen {{events_double_count_avoided|t}} (C04). Sınıf toplamı: ortak {{events_match_ortak|t}} + yalnız MODIS {{events_match_yalniz_modis|t}} + yalnız VIIRS {{events_match_yalniz_viirs|t}} + tek sensör dönemi {{events_match_tek_sensor_donemi|t}} = {{events_total|t}} (C05). Süre {{clustering_runtime_s|t}}, bellek {{clustering_rss_mb|t}} (ölçüldü). D/H/L duyarlılığı (olay sayısı kuralla birlikte okunmalı):

{{duyarlilik.kumeleme}}

Ayak izi eşleştirmesinin etkisi: yalnız-MODIS olay {{events_yalniz_modis_sabit|t}} (sabit 1 km) → {{events_yalniz_modis_ayakizi_capraz|t}} (ayak izi). Anız etkileşimi (tahmini): ortak kümelemede anız sayılan nokta {{aniz_points_joint|t}}, ayrı kümelemede {{aniz_points_separate|t}}.

## 7. Bağımsız yeniden hesap (C23)

**Basitçe:** Aşçı yemeğin tuzunu kendisi tadarsa körleşir; başka birine tattırdık. Denetçi, üretim kodunu kullanmadan sayıları yeniden üretti.
**Teknik olarak:** {{kontrol.bagimsiz_sonuc}}.

{{denetim.bagimsiz_tablo}}

## 8. Kabul kriterleri C01–C25

{{kontrol.tablo}}

C14 kontrolü kodda "statik tarama"dır; çalışma anı karşılaştırması denetçi tarafından arayüz üzerinde ayrıca yapıldı (örneklenen ekran değerleri agg tablolarıyla ve metrics.json ile birebir, fark 0; `audit/bulgular.md` F4). Performans: eşik değişimi {{perf_esik_degisimi_sn|t}} (tek ölçüm, bu makine). Erişilebilirlik: klavye {{a11y_klavye_oran|yuzde}}, adlı öğe {{a11y_aria_adli_oran|yuzde}}, en düşük kontrast {{a11y_kontrast_min|t}}.

## 9. Doğrulanmayanlar ve bilinen sınırlar

**Basitçe:** Burası "bilmediğimiz şeyler" listesidir; güzelleştirilmedi. Jüri sorarsa ilk önce buradan cevap verilir.

{{sinirlar.dogrulanmayan}}

## 10. Bulgular (denetçi)

Açık yüksek: {{bulgu.acik_yuksek}} · Açık orta: {{bulgu.acik_orta}} · Açık düşük: {{bulgu.acik_dusuk}} · Kapanan: {{bulgu.kapanan}} (kaynak: `audit/bulgular.md`).

{{bulgu.liste}}
