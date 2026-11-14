# Doğruluk Raporu

Veri sürümü: FIRMS MODIS C6.1 + VIIRS 375 m, 2000–2026 (son gün 2026-11-12), 1.414.674 nokta, veri şeması v1, `reports/metrics.json` üretimi 2026-11-13T09:07:17Z · Üretim tarihi: 2026-11-13 09:42 UTC
Denetçi durumu: check_all: 25 geçti, 0 kaldı, 0 atlandı; denetçi bulguları: açık yüksek 0, açık orta 0, açık düşük 5 — denetçi kapısı açık yüksek bulgu içermiyor

> Bu rapor "ne kadar doğru, neyi doğrulayamadık" sorusunu cevaplar. Her sayı `reports/metrics.json` kimliğiyle izlenir; yanındaki etiket **ölçüldü** (veriden sayıldı), **tahmini** (model/kural/çıkarım) veya **doğrulanmadı** (bağımsız kanıt yok) anlamına gelir (K5). Her bölüm önce **Basitçe**, sonra **Teknik olarak** anlatır.

## 1. Özet

**Basitçe:** Sayıları iki kez saydık: bir kez üretim koduyla, bir kez de üretimi yazmayan bağımsız bir denetçiyle. Uyuştular. Yöntemi, test ettiği yılı hiç görmeden sınadık. Sonuç iyi ama kusursuz değil: 2026 için eşdeğer seriye güvenilmez, bazı tesisler kaçıyor ve bazı şeyleri hiç doğrulayamadık; hepsi §9'da açıkça yazılıdır.

**Teknik olarak:** Kabul kriterleri C01–C25: geçen 25 / 25, kalan 0, atlanan 0 (§8). Bağımsız yeniden hesap (C23): 97 (ölçüldü) karşılaştırmanın 93 tanesinde bağımsız yeniden hesapla fark 0; 4 girdi açıklamalı bilgi kaydıdır (fark değil). C23 sonucu: GEÇTİ. Açık bulgular: yüksek 0, orta 0, düşük 5; kapanan 23 (§10).

Ana sonuçlar (tamamı aşağıda ayrıntılı):

| Ölçü | Değer | Not |
|---|---|---|
| Yıllık MAPE (LOYO) | 8,33 % (ölçüldü) | kalibrasyon dışı yıllarda |
| Yıllık R² (LOYO) | 0,8716 (ölçüldü) | |
| Artık sıçrama (harmonize − gerçek MODIS) | 3,55 yüzde puan (tahmini) | LOYO %95 aralığı [−23,49 ; 9,51] % (tahmini) içinde |
| Bağımsız yeniden hesapta fark 0 olan girdi | 93 karşılaştırma (ölçüldü) / 97 | denetçi, farklı yöntem |
| Referans dengeli kesinlik | 0,9711 (tahmini) | tesis yakalama 0,4777 (tahmini) |

## 2. Doğrulama yöntemi: sınav sorusunu önceden görmemek (K4)

**Basitçe:** Öğrenciye sınav sorusunun cevabını verip aynı soruyla notlamak olmaz. Her yılı sırayla "saklıyoruz", kalan yıllardan oran öğreniyoruz, saklanan yılı tahmin edip gerçek MODIS ile karşılaştırıyoruz.
**Teknik olarak:** Test: leave-one-year-out (2012-2025, 14 yıl; kazanan (ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu) (ölçüldü). Kalibrasyon yıllarında yapılan test geçerli sayılmaz (C09). Eşik seçimleri (sanayi N, M, Y, S) de LOYO ile yapıldı. 2026 kısmi yıl ve NRT olduğu için test dışıdır ve düşük güven etiketlidir.

## 3. Harmonizasyon doğruluğu (C09, C11)

**Basitçe:** Hassas termometrenin ölçümünü eski termometrenin diline çevirdik. "Eski termometre görseydi kaç sayardı?" tahminimiz, saklanan yıllarda gerçekle ortalama bu kadar yüzde sapıyor.

| Ölçü | Değer | Etiket |
|---|---|---|
| Dışarıdaki yıllarda yıllık MAPE | 8,33 % | ölçüldü |
| Yıllık R² | 0,8716 | ölçüldü |
| Yıllık sapma (bias) | 0,55 % | ölçüldü |
| Yıllık %95 hata aralığı | [−23,49 ; 9,51] % | tahmini |
| Ay×bölge WAPE | 30,63 % | ölçüldü |
| Ay×bölge R² | 0,8607 | ölçüldü |
| Çakışma döneminde toplam sapma (bias) | −0,52 % | tahmini |
| Aylık ülke %95 hata bandı | [−59,57 ; 74,99] % | tahmini |
| Bant kapsaması ay×bölge | %95,6 | ölçüldü |
| Bant kapsaması ay×ülke | %92,3 | ölçüldü |
| **2026** bant kapsaması | %54,5 | ölçüldü |

**Teknik olarak:** Yöntem yarışı (hedef: Terra+Aqua tespiti, LOYO 2012–2025):

| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Sapma % | Yıllık %95 aralık |
|---|---|---|---|---|---|
| (i0) tek sabit oran, efor yok (B-04 tuzağı, yalnız kıyas) | 52,68 | 42,12 | −1,7204 | 5,03 | [−46,83 ; 86,91] |
| (i) tek sabit oran, eforlu | 30,64 | 4,83 | 0,9675 | 0,15 | [−7,81 ; 9,46] |
| (ii) bölge × mevsim × FRP büyüklüğü, eforlu (kazanan) | 30,63 | 8,33 | 0,8716 | 0,55 | [−23,49 ; 9,51] |
| (iii) FRP eşik eğrisi, eforlu | 31,91 | 10,91 | 0,7644 | 3,76 | [−13 ; 31,69] |

Tüm bu sayılar ölçüldü (aralıklar tahmini). **Dürüst okuma (K5):** (ii) ile (i) ay×bölgede **ayırt edilemez** (WAPE farkı %95 aralığı [−2,97 ; 4,26] yüzde puan (tahmini)); yıllık toplamda (i) daha iyi. Yani asıl kazanç gözlem eforu (uydu sayısı) düzeltmesidir (WAPE 52,68 % (ölçüldü) → 30,64 % (ölçüldü)), (ii)'nin (i)'den üstün olduğu iddia edilmez. (ii) uygulamanın birimi (ay×bölge) için seçildi; seçim LOYO sonuçları üzerinde yapıldığından hata hafif iyimser olabilir. Etiket: kazanan seçimi (ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu (tahmini).

Birim ve küme varyantları (aynı LOYO ve sıçrama tanımı):

| Varyant | Yıllık MAPE % | Yıllık R² | Ham sıçrama % | Harmonize % | Gerçek MODIS % | Artık (puan) |
|---|---|---|---|---|---|---|
| tespit, temiz (ana) | 8,33 | 0,8716 | 143,13 | −41,35 | −44,9 | 3,55 |
| olay, temiz | 7,51 | 0,8443 | 51,72 | −54,23 | −53,45 | −0,78 |
| tespit, temiz+anız | 8,27 | 0,8988 | 113,44 | −49,17 | −52,29 | 3,12 |
| olay, temiz+anız | 7,53 | 0,8718 | 42,1 | −58,65 | −59,01 | 0,36 |

(Hepsi ölçüldü; harmonize sütunu tahmini.) Olay eşdeğeri, tespit eşdeğerini aşamaz (K8, B-04 kontrolü): aşan hücreler kırpıldı (ay×bölge 98 hücre (ölçüldü), ay×ülke 6 hücre (ölçüldü), yıl×ülke 0 hücre (ölçüldü)).

## 4. Sıçrama metriği (C10, U-15)

**Basitçe:** 2012'de ham seri bir anda fırlıyor. Soru: harmonize seri bu yapay fırlamayı gideriyor mu, ama gerçek bir değişimi de saklamıyor mu? Cevap için "gerçek MODIS aynı pencerede ne yaptı?" ile kıyaslıyoruz.

| Seri (geçiş 2012, 3+3 yıl) | Sıçrama | Etiket |
|---|---|---|
| Ham (MODIS → MODIS+VIIRS) | 143,13 % | ölçüldü |
| Ham (MODIS → yalnız VIIRS) | 88,03 % | ölçüldü |
| Harmonize (LOYO MODIS-eşdeğer) | −41,35 % | tahmini |
| **Gerçek MODIS (aynı pencere)** | −44,9 % | ölçüldü |
| Harmonizasyonun eklediği (harmonize − gerçek MODIS) | 3,55 puan | tahmini |
| NOAA-20 eklenişi 2018: ham / eforlu / gerçek MODIS | 24,34 / −37,31 / −41,59 % | ölçüldü |
| NOAA-21 eklenişi 2023: ham / eforlu / gerçek MODIS | 110,19 / 44,29 / 31,01 % | ölçüldü |

**Teknik olarak ve dürüstlük notu (C10 inceltildi):** Başlangıçtaki ölçüt "harmonize sıçrama, geçiş dışı yıllık değişimlerin %95 aralığında olmalı" idi. İlk sonuç görüldüğünde gerçek MODIS'in kendisi de bu doğal aralığın dışına düştüğü anlaşıldı (2009–2011 MODIS'te olağandışı yüksek yıllar): ölçüt, gerçek yangın değişimini sensör sıçramasından ayıramıyordu. Bu yüzden ana ölçüt **artık sıçrama** olarak değiştirildi: harmonize − aynı penceredeki gerçek MODIS değişimi, yıllık LOYO %95 hata aralığında olmalı. Bu değişiklik **sonuç görüldükten sonra** yapıldı (`audit/degisim_gunlugu.md`); bu nedenle ölçütün kendisi sonuca göre seçilmiş olabilir. Bağımsız denetçi, artık sıçramayı ayrıca 3+3 yıllık pencerelerle sınadı ve dağılımının 3,55 puanlık artığı kapsadığını buldu (`audit/bulgular.md` F2-07), yani sonuç ölçüt seçiminden bağımsız olarak sağlam görünüyor.

Güncel sonuç: artık 3,55 yüzde puan (tahmini); LOYO aralığı [−23,49 ; 9,51] % (tahmini); C10 ana ölçütü: jump_resid_pct (birim=tespit, küme=temiz) loyo_ci95 içinde (ölçüldü). Eski ölçüt (bilgi): doğal değişim aralığı [−39,3 ; 92,61] % (tahmini); harmonize sıçrama bu aralıkta mı: hayır (tahmini) (gerçek MODIS −44,9 % (ölçüldü) de dışarıda).

**Sonuç (K5, dürüst dil):** "Sensör farkını çözdük" **denmez**. Doğru cümle: *harmonize seri, gerçek MODIS düşüşünü 3,55 yüzde puan (tahmini) farkla izliyor; bu fark yıllık hata aralığı içinde, ama aralığın kendisi geniştir ([−23,49 ; 9,51] % (tahmini)).* Aynı fark olay biriminde −0,78 yüzde puan (tahmini).

## 5. Temizlik doğruluğu (C13)

**Basitçe:** Kuralımız "bu baca" dediğinde ne sıklıkla haklı, bilinen tesislerin ne kadarını yakalıyor ve gerçek yangını yanlışlıkla silmiyor mu? FIRMS'ten bağımsız bir listeyle sorduk. Anız içinse elimizde yalnız dolaylı kanıt var.

**Teknik olarak:** Doğrulama seti `audit/dogrulama_seti.csv`: 26 tesis (ölçüldü) sanayi tesisi (OpenStreetMap), 8 yangın (ölçüldü) bilinen yangın (Wikipedia + ilçe merkezi), 3 (ölçüldü) kayıt çakışmadan ayıklandı. Sınıflar eşit ağırlıklı (her tesise ve her yangına eşit oy).

| Ölçü | Değer | Etiket |
|---|---|---|
| Dengeli kesinlik (precision) | 0,9711 | tahmini |
| Makro tesis yakalama (recall) | 0,4777 | tahmini |
| Tesis düzeyi yakalama | 0,4783 | tahmini |
| Yangın başına yanlış işaret | 0,0142 | tahmini |
| Gerçek yangın noktası korunması | 0,9982 | tahmini |
| Yalnız kural (NASA type'sız), makro yakalama | 0,3829 | tahmini |
| Yalnız NASA statik etiketi, makro yakalama | 0,2911 | tahmini |
| Nokta düzeyi kesinlik / yakalama (şişkin, sunumda kullanılmaz) | 0,9999 / 0,9848 | tahmini |
| Sanayi LOYO uyuşması (NASA type=2): kesinlik / duyarlılık | 0,9199 / 0,9712 | ölçüldü (uyuşma, doğruluk değil) |
| aynı, VIIRS dönemi: kesinlik / duyarlılık | 0,924 / 0,9722 | ölçüldü |
| aynı, MODIS dönemi: kesinlik / duyarlılık | 0,2278 / 0,5679 | ölçüldü |
| MODIS dönemi 'sanayi' noktalarının bilinen tesise yakınlığı | %66,6 | ölçüldü |
| Anız LOYO kapsama / taban / kaldıraç | 0,749 / 0,8071 / 0,928 | ölçüldü |
| Anız ayları ile ulusal hasat penceresi uyumu | %74,2 | tahmini |

**WorldCover (bağımsız arazi örtüsü, 2021, örneklem):**

| Grup | Ekili alan | Yapılaşmış | Ağaç | Çayır |
|---|---|---|---|---|
| Anız | %79,3 | %3 | %3,9 | %12,8 |
| Büyük temiz olaylar | %50,3 | %0,4 | %32,1 | %14,1 |
| Sanayi + kalıcı (kural) | %8,9 | %56 | %6,2 | %12 |
| NASA statik kaynak | %1,8 | %81,2 | %3 | %3,6 |

(Hepsi ölçüldü; ama yalnız kural etiketiyle arazi örtüsü **uyumu**dur, yer doğrulaması değil.) Static Thermal Anomalies maskesi karşılaştırması: yok (doğrulanmadı). Anız takviminin saha/yanmış alan ile bağımsız doğrulaması: **yapılmadı (doğrulanmadı)**.

## 6. Kümeleme doğruluğu (C03, C04, C05, C12)

**Basitçe:** Kümelemeyi hızlı yapan kodun, çok yavaş ama kesin "her noktayı her noktayla karşılaştır" yöntemiyle aynı sonucu verdiğini gösterdik; ayrıca kasten bozuk bir yöntemi testin yakalayıp yakalayamadığına baktık.
**Teknik olarak:** Hızlı kümeleme = kaba kuvvet: 12 örneklem (ölçüldü) (21.509 nokta), 7 kural çeşidi, 88 karşılaştırmanın hepsinde fark 0 karşılaştırma (ölçüldü); kasten hatalı yöntem 12/12 örneklemde yakalandı (C03, `src/clustering/bruteforce_check.py`). Çifte sayım: çakışma döneminde ortak 380.975 olay (ölçüldü) ≤ ayrı 440.176 olay (ölçüldü); önlenen 59.201 olay (ölçüldü) (C04). Sınıf toplamı: ortak 35.651 olay (ölçüldü) + yalnız MODIS 57.543 olay (ölçüldü) + yalnız VIIRS 287.781 olay (ölçüldü) + tek sensör dönemi 91.003 olay (ölçüldü) = 471.978 olay (ölçüldü) (C05). Süre 3,32 s (ölçüldü), bellek 676 MB (ölçüldü) (ölçüldü). D/H/L duyarlılığı (olay sayısı kuralla birlikte okunmalı):

**D** (en az 4 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | olay | en_buyuk_olay | tek_tespitli_oran | olay_demo_donemi | modis_viirste_gorulme |
|---|---|---|---|---|---|
| 0,5 | 541.338 | 6.736 | 0,7307 | 64.429 | 0,363 |
| 1 | 471.978 | 6.740 | 0,663 | 56.263 | 0,3825 |
| 2 | 383.640 | 6.754 | 0,5831 | 47.803 | 0,462 |
| 3 | 341.799 | 6.755 | 0,5745 | 42.731 | 0,4767 |

**H** (en az 4 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | olay | en_buyuk_olay | tek_tespitli_oran | olay_demo_donemi | modis_viirste_gorulme |
|---|---|---|---|---|---|
| 6 | 525.841 | 1.385 | 0,6659 | 63.473 | 0,3591 |
| 12 | 512.109 | 6.658 | 0,6684 | 61.575 | 0,3617 |
| 24 | 481.008 | 6.740 | 0,666 | 57.673 | 0,3767 |
| 48 | 451.483 | 6.742 | 0,6571 | 53.929 | 0,4015 |

**L** (en az 5 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | olay | en_buyuk_olay | tek_tespitli_oran | sure_saat_p90 | olay_demo_donemi | modis_viirste_gorulme |
|---|---|---|---|---|---|---|
| 1 | 506.842 | 6.665 | 0,6685 | 0,83 | 61.132 | 0,362 |
| 2 | 499.277 | 6.740 | 0,6664 | 0,85 | 60.595 | 0,3763 |
| 3 | 471.978 | 6.740 | 0,663 | 1,57 | 56.263 | 0,3825 |
| 4 | 468.214 | 6.740 | 0,6611 | 1,65 | 55.962 | 0,3929 |
| 6 | 460.759 | 6.740 | 0,6587 | 1,67 | 55.206 | 0,4017 |


Ayak izi eşleştirmesinin etkisi: yalnız-MODIS olay 63.310 olay (ölçüldü) (sabit 1 km) → 58.998 olay (ölçüldü) (ayak izi). Anız etkileşimi (tahmini): ortak kümelemede anız sayılan nokta 290.799 nokta (tahmini), ayrı kümelemede 320.995 nokta (tahmini).

## 7. Bağımsız yeniden hesap (C23)

**Basitçe:** Aşçı yemeğin tuzunu kendisi tadarsa körleşir; başka birine tattırdık. Denetçi, üretim kodunu kullanmadan sayıları yeniden üretti.
**Teknik olarak:** 97 (ölçüldü) karşılaştırmanın 93 tanesinde bağımsız yeniden hesapla fark 0; 4 girdi açıklamalı bilgi kaydıdır (fark değil). C23 sonucu: GEÇTİ.

Denetçi bu sayıları üretim kodundan bağımsız (openpyxl, polars, pandas) yeniden hesapladı (`audit/f1/`, `audit/f2/`). Aşağıda örnek satırlar; tamamı `audit/yeniden_hesap.json`. Etiket: ölçüldü.

| Girdi | Beklenen (üretim hattı) | Bulunan (bağımsız) | Fark |
|---|---|---|---|
| toplam_satir_xlsx | 1.414.674 | 1.414.674 | 0 |
| toplam_satir_points | 1.414.674 | 1.414.674 | 0 |
| sensor_MODIS | 259.707 | 259.707 | 0 |
| sensor_VIIRS | 1.154.967 | 1.154.967 | 0 |
| uydu_Terra | 136.626 | 136.626 | 0 |
| uydu_Aqua | 123.081 | 123.081 | 0 |
| uydu_SNPP | 637.595 | 637.595 | 0 |
| uydu_N20 | 360.942 | 360.942 | 0 |
| uydu_N21 | 156.430 | 156.430 | 0 |
| nrt_satir | 61.147 | 61.147 | 0 |
| f2_huni_ham | 1.414.674 | 1.414.674 | 0 |
| f2_huni_status_bos | 0 | 0 | 0 |
| f2_huni_status_temiz | 827.043 | 827.043 | 0 |
| f2_huni_status_deniz | 8.848 | 8.848 | 0 |
| f2_huni_status_volkan | 5 | 5 | 0 |
| f2_huni_status_statik_nasa | 328.379 | 328.379 | 0 |
| f2_huni_status_sanayi | 27.012 | 27.012 | 0 |
| f2_huni_status_kalici_belirsiz | 6.208 | 6.208 | 0 |
| f2_huni_status_dusuk_guven | 0 | 0 | 0 |
| f2_huni_status_aniz | 217.179 | 217.179 | 0 |

## 8. Kabul kriterleri C01–C25

| Kod | Kontrol | Durum | Not |
|---|---|---|---|
| C01 | Huni korunumu | GEÇTİ | her nokta tam bir etiket taşıyor |
| C02 | Toplam tutarlılığı | GEÇTİ |  |
| C03 | Kümeleme doğruluğu | GEÇTİ | mutasyon testi: hatalı yöntem 12/12 örneklemde yakalandı / örneklem=12 nokta=21509 kural=7 karşılaştırma=88 fark_olan=0 süre=108.2s / C03... |
| C04 | Çifte sayım yok | GEÇTİ |  |
| C05 | Üçlü sınıf toplamı | GEÇTİ |  |
| C06 | Veri kapsamı | GEÇTİ | kesinti düzeltmesi kanıtı: {"modis_kesinti_gunu_olan_ay": 12, "duzeltmeli_ge_duzeltmesiz": true, "tamamen_kapsamsiz_gunlerde_modis_tespit... |
| C07 | Zaman | GEÇTİ |  |
| C08 | Şema ve kodlama tutarlılığı | GEÇTİ |  |
| C09 | Kalibrasyon dışı doğrulama | GEÇTİ | yöntem yıl dışarıda bırakma olmalı |
| C10 | Sıçrama metriği | GEÇTİ | artık sıçrama LOYO %95 aralığında olmalı |
| C11 | Eşdeğer seri doğruluğu | GEÇTİ | sapma ve bant raporlandı |
| C12 | Duyarlılık | GEÇTİ |  |
| C13 | Referans karşılaştırması | GEÇTİ |  |
| C14 | Ekran = hesap | GEÇTİ | statik tarama; çalışma anı karşılaştırması denetçide |
| C15 | Yasak kalıp taraması | GEÇTİ |  |
| C16 | Simülasyon izolasyonu | GEÇTİ | simüle veri yalnız tests/ altında |
| C17 | CSV | GEÇTİ | csv_check OK: BOM, t_utc/t_tr, formül öneki, sayı korunumu |
| C18 | TR/EN | GEÇTİ | 279 anahtar |
| C19 | Erişilebilirlik | GEÇTİ |  |
| C20 | Performans | GEÇTİ | hedef ≤ 5 sn |
| C21 | Çevrimdışı açılış | GEÇTİ | dış CDN bağımlılığı olmamalı |
| C22 | Belge sayıları | GEÇTİ |  |
| C23 | Bağımsız yeniden hesap | GEÇTİ |  |
| C24 | Dürüstlük etiketi | GEÇTİ | etiket içermeyen rapor |
| C25 | Gereksinim eşlemesi | GEÇTİ |  |

C14 kontrolü kodda "statik tarama"dır; çalışma anı karşılaştırması denetçi tarafından arayüz üzerinde ayrıca yapıldı (örneklenen ekran değerleri agg tablolarıyla ve metrics.json ile birebir, fark 0; `audit/bulgular.md` F4). Performans: eşik değişimi 0,253 s (ölçüldü) (tek ölçüm, bu makine). Erişilebilirlik: klavye %88,4, adlı öğe %100, en düşük kontrast 4,59 (ölçüldü).

## 9. Doğrulanmayanlar ve bilinen sınırlar

**Basitçe:** Burası "bilmediğimiz şeyler" listesidir; güzelleştirilmedi. Jüri sorarsa ilk önce buradan cevap verilir.

| # | Konu | Etiket | Açıklama | Kaynak |
|---|---|---|---|---|
| 1 | 2026 için MODIS-eşdeğer seri güvenilmez | doğrulanmadı | Aqua öğle geçişi 10,7 UTC (2015) iken 12,65 UTC'ye (2026) kaydı; Aqua ile VIIRS'in eşzamanlı çift payı 0,839 iken 0,182 değerine düştü. Eşdeğer bandın 2026'da gerçek MODIS'i kapsama oranı 0,545 (ölçüldü); LOYO döneminde 0,9226 (ölçüldü). Son tam ayda eşdeğer seri oranı 1,697 kat (tahmini) verirken iki sensörün kendi ölçümü 0,876 kat (ölçüldü) (MODIS) ve 0,944 kat (tahmini) (VIIRS): çelişki. Yörünge kaymasını gidermeyen ('kaymasız') bir kalibrasyon varyantı ölçülmedi. | docs/harmonizasyon_yontemi.md §4; audit/bulgular.md F4-01 |
| 2 | MODIS bittikten sonra serinin doğruluğu | doğrulanmadı | Terra/Aqua sona erince seri yalnız 2012–2025 kalibrasyonuna dayanır. Bu rejimin bağımsız doğrulaması yoktur; çünkü karşılaştırılacak gerçek MODIS kalmayacak. Aylık ülke hata bandı [−59,57 ; 74,99] % (tahmini) geniştir. | audit/juri_sorulari.md soru 12 |
| 3 | Sensör farkı çözüldü iddiası yok | tahmini | Harmonize seri, gerçek MODIS'in aynı penceredeki değişimini 3,55 yüzde puan (tahmini) farkla izliyor. Bu fark LOYO yıllık %95 hata aralığı [−23,49 ; 9,51] % (tahmini) içinde; ama harmonize sıçrama, geçiş dışı doğal yıllık değişim aralığı [−39,3 ; 92,61] % (tahmini) içinde değil (içinde mi: hayır (tahmini)), çünkü gerçek MODIS de bu aralığın dışında. C10 ölçütü ilk sonuç görüldükten sonra inceltildi (audit/degisim_gunlugu.md); bu bir yöntem seçimidir ve sonuca göre ayarlanmış olabileceği kabul edilir. | docs/03_KABUL_KRITERLERI.md C10; audit/degisim_gunlugu.md; audit/bulgular.md F2-07 |
| 4 | (ii) ile (i) yöntemleri ayırt edilemez | ölçüldü | Ay×bölge WAPE: (i) 30,64 % (ölçüldü), (ii) 30,63 % (ölçüldü); fark %95 aralığı [−2,97 ; 4,26] yüzde puan (tahmini). Yıllık toplamda (i) daha iyi (MAPE 4,83 % (ölçüldü) karşı 8,33 % (ölçüldü)). Asıl kazanç gözlem eforu (uydu sayısı) normalizasyonudur; (ii)'nin (i)'den üstün olduğu iddia edilmez. Kazanan seçimi LOYO sonuçları üzerinde yapıldığı için hata hafif iyimser olabilir. | docs/harmonizasyon_yontemi.md §5 |
| 5 | Anız için yer doğrulaması yok | doğrulanmadı | Anız etiketi kural tabanlıdır ve yalnız dolaylı kanıtla sınandı: ESA WorldCover'da anız noktalarının %79,3 ekili alanda (ölçüldü), kaba ulusal hasat penceresiyle uyum %74,2 (tahmini). Saha, yanmış alan (MCD64A1) veya AFAD/OGM kaydıyla karşılaştırma yapılmadı. Ay tek başına anızı ayırmaz (LOYO kaldıraç 0,928 (ölçüldü)). | docs/temizlik_yontemi.md §6, §10 |
| 6 | Static Thermal Anomalies (STA) maskesi karşılaştırılmadı | doğrulanmadı | FIRMS STA maskesi için toplu indirme bulunamadı; karşılaştırma sonucu: yok (doğrulanmadı). Yerine NASA arşivindeki type=2 ile uyum ölçüldü; bu aynı şey değildir ve type=2 yer gerçeği değil bir maskedir. | docs/ek_kaynaklar.md; docs/temizlik_yontemi.md §5 |
| 7 | Sanayi kuralı MODIS döneminde zayıf uyuşuyor | ölçüldü | NASA type=2 ile uyuşma VIIRS döneminde kesinlik 0,924 (ölçüldü), MODIS döneminde 0,2278 (ölçüldü). Referans seyrek olduğu için; kuralın 'sanayi' dediği MODIS noktalarının %66,6 bilinen bir tesise yakın. Bu 'uyuşma' ölçüsüdür, doğruluk değil. | audit/bulgular.md F2-09 |
| 8 | Referans doğrulama seti küçük ve tesis yakalaması düşük | tahmini | Set: 26 sanayi tesisi (OpenStreetMap) ve 8 bilinen yangın (Wikipedia + ilçe merkezi); 3 kayıt çakışma nedeniyle ayıklandı. Dengeli kesinlik 0,9711 (tahmini), tesis yakalama 0,4777 (tahmini) (tesis düzeyinde 0,4783 (tahmini)): bazı tesisler (özellikle termik santraller) kaçıyor. Yangın pencereleri ve yarıçapları yaklaşık. Nokta düzeyi kesinlik (0,9999 (tahmini)) sınıf dengesizliğinden şişkindir ve sunumda kullanılmaz. | audit/dogrulama_seti.csv; docs/temizlik_yontemi.md §8 |
| 9 | Gözlem kapsamı (swath) çıkarımdır | tahmini | NASA uydu geçiş şeridi (swath) verisi toplu indirilemedi; kesinti günleri tespit sayılarından çıkarıldı (129 uydu-gün (tahmini)). Geçiş pencereleri tespit saatlerinin yüzdeliklerinden türetildi. Gerçek geçiş listesiyle doğrulanmadı. | docs/ek_kaynaklar.md; audit/bulgular.md F1-01 |
| 10 | Ekran okuyucu testi yapılmadı | doğrulanmadı | Klavyeyle ulaşılabilir etkileşimli öğe payı %88,4, adı olan öğe payı %100, en düşük kontrast 4,59 (ölçüldü) (ölçüldü); renk körlüğü ayırt edilebilirliği ölçüldü. Ekran okuyucuyla elle sınama ve harita zemini/Leaflet iç kontrolleri ölçüm dışıdır. | audit/erisilebilirlik.json (kapsam_notu) |
| 11 | İl düzeyinde MODIS-eşdeğer seri yok | doğrulanmadı | Eşdeğer seri yalnız ülke ve 7 bölge düzeyinde LOYO ile doğrulandı (olay biriminde ay×il WAPE 46,27 % (ölçüldü) ile daha yüksek). İl düzeyi için ayrı bir doğrulama yoktur. | docs/takvim_yontemi.md; docs/harmonizasyon_yontemi.md §8 |
| 12 | Güven sınıfı eşlemesi zayıf ilişkili | tahmini | Öğrenilen MODIS eşiği [35 ; 82] MODIS % (tahmini) FIRMS cetveline yakın; ama iki uydunun tek yangındaki güveni zayıf ilişkili (Spearman 0,2138 (ölçüldü)) ve öğrenilmiş eşleme FIRMS'i geçmedi (kappa 0,1765 (ölçüldü) karşı 0,1918 (ölçüldü)). Arayüzde varsayılan ham FIRMS sınıfıdır. | docs/harmonizasyon_yontemi.md §2 |
| 13 | Anomali bandı geniştir | tahmini | Eşdeğer seride anomali işareti, belirsizlik bandı yüzünden 33,53 % (tahmini) oranında 'belirsiz'e düşüyor. Ağu–Eyl ay medyanları istatistiksel olarak ayırt edilemez (ayırt edilemez bayrağı: 1 (ölçüldü)). | docs/takvim_yontemi.md |
| 14 | WorldCover tek yıl ve örneklem | tahmini | ESA WorldCover 2021 tek yıldır; 2000–2026 noktalarında arazi değişimi yok sayıldı, WorldCover'ın kendi sınıflandırma hatası ölçülmedi, örneklem tabanlıdır. | docs/temizlik_yontemi.md §6, §10 |
| 15 | FIRMS API ile otomatik çekme çalıştırılmadı | doğrulanmadı | `src/pipeline/firms_api.py` betiği hazır (kota 5000 işlem/10 dk'ya uygun) fakat API anahtarı yok ve çalıştırılmadı. Veri, elle indirilmiş 1.414.674 satırlık arşivden gelir; son gün 2026-11-12. | docs/ek_kaynaklar.md |
| 16 | Terra'nın 2026 durumu belirsiz | doğrulanmadı | Mevcut durum belgesindeki 'Mart 2026'da beklemeye alındı' iddiası doğrulanamadı; veride Terra tespiti son güne kadar sürüyor. Planlı bitiş tarihleri ikincil kaynaktan, doğrulanmadı. | docs/ek_kaynaklar.md |
| 17 | Zaman: sabit UTC+3 | tahmini | TR günü her yıl için sabit UTC+3 alınır; 2016 öncesi kış saati (UTC+2) etkisi 21:00–21:59 UTC tespitlerini ertesi güne kaydırır, etkisi küçük kabul edildi (denetçi örneklemle ölçebilir). | audit/degisim_gunlugu.md F1 |
| 18 | Mevcut ay kutusu ve 2026 kısmi yıl | doğrulanmadı | Son veri günü 2026-11-12; mevcut ay 12 gün (ölçüldü) kısmidir ve NRT payı 100 % (ölçüldü). Mevcut ay oranı MODIS 0,127 kat (tahmini), VIIRS 0,243 kat (tahmini); MODIS'in ek düşüşünün nedeni (sensör ömrü sonu, NRT, yörünge kayması) doğrulanmadı. | audit/juri_sorulari.md soru 13 |
| 19 | Harita zemini çevrimiçi | ölçüldü | Uygulama internet olmadan açılır (C21, kütüphaneler yerelde); yalnız isteğe bağlı çevrimiçi harita zemini internet ister, yoksa il sınırları görünür. | src/app/i18n/tr.json map.tilewarn; check_all C21 |
| 20 | Hotspot yangın değildir; risk tahmini yoktur | ölçüldü | Gösterilen şey tarihsel hotspot/olay aktivitesidir. Gelecekteki yangın riski veya tehlikesi tahmin edilmez (K14). Nokta sayısı yangın sayısı değildir: 1.414.674 noktadan 471.978 olay çıkar. | CLAUDE.md K14 |

`metrics.json` içinde **doğrulanmadı** etiketli 6 metrik var:

| Metrik kimliği | Değer | Tanım |
|---|---|---|
| takvim_mevcut_ay_ayrisma_yorum_TR | MODIS'e özgü ek düşüş: sensör ömrü sonu, NRT veya yörünge kayması şüphesi | MODIS ve VIIRS oranı yan yana: düşüş iki sensörde mi (hava/gerçek) yoksa yalnız MODIS'te mi (sensör şüphesi) |
| takvim_son_tam_ay_guvenilmez_modis_esdeger_TR | 1 | Eşdeğer oran iki ölçülmüş orandan (MODIS temiz, VIIRS uydu başına) eşikten fazla sapıyor mu |
| takvim_son_tam_ay_birincil_modis_esdeger_TR | modis temiz | Birincil gösterim serisi |
| takvim_son_tam_ay_guvenilmez_olay_esdeger_TR | 1 | Eşdeğer oran iki ölçülmüş orandan (MODIS temiz, VIIRS uydu başına) eşikten fazla sapıyor mu |
| takvim_son_tam_ay_birincil_olay_esdeger_TR | modis temiz | Birincil gösterim serisi |
| temizlik_sta_maskesi_karsilastirma | yok | FIRMS Static Thermal Anomalies maskesi deneysel; toplu indirme/API bulunamadı -> karşılaştırma yapılmadı |

Otomatik eklenenler:
- Açık denetim bulgusu **F2-10** (düşük, açık): Sabit yıl/saat sabitleri (K9, K11) (doğrulanmadı)
- Açık denetim bulgusu **F2-11** (düşük, açık): Belge tutarsızlıkları (doğrulanmadı)
- Açık denetim bulgusu **F2-12** (düşük, açık): Kontrol zayıflıkları — `tools/check_all.py` (doğrulanmadı)
- Açık denetim bulgusu **F4-04** (düşük, kısmen): Görüntü kusurları (doğrulanmadı)
- Açık denetim bulgusu **F5-03** (düşük, açık): Etiket (C24) — türetilmiş sonuç "ölçüldü" (doğrulanmadı)

## 10. Bulgular (denetçi)

Açık yüksek: 0 · Açık orta: 0 · Açık düşük: 5 · Kapanan: 23 (kaynak: `audit/bulgular.md`).

| Kimlik | Seviye | Durum | Başlık |
|---|---|---|---|
| F1-01 | yüksek | kapandı | `data/processed/coverage.parquet`, `src/pipeline/build_coverage.py`, `tools/check_all.py` C06 |
| F1-02 | orta | kapandı | `points.parquet` `il`, `data/README.md`, `audit/veri_envanteri.md` |
| F1-03 | orta | kapandı | `tools/check_all.py` C07 |
| F1-04 | düşük | kapandı | `src/pipeline/build_points.py:129`, `:116` |
| F1-05 | düşük | kapandı | `src/pipeline/timeutil.py`, `docs/04` §2 |
| F1-06 | düşük | kapandı | belgeler |
| F1-07 | düşük | kapandı | `src/pipeline/test_pipeline.py` |
| F2-01 | yüksek | kapandı | `data/processed/agg/harmonized.parquet`, `monthly.parquet` (olay eşdeğeri vs tespit eşdeğeri) — K8 |
| F2-02 | orta | kapandı | `src/config/esikler.json → harmonizasyon.ogrenilen_guven_esleme` |
| F2-03 | orta | kapandı | Yöntem seçimi (ii) vs (i) — `src/harmonize/seri.py:main`, `docs/harmonizasyon_yontemi.md §5, §9` |
| F2-04 | orta | kapandı | 2026 rejimi ve "mevcut ay 0,127" — `agg/current_month.parquet`, `monthly.parquet`, `docs/harmonizasyon_yontemi |
| F2-05 | orta | kapandı | Dürüstlük etiketleri — `reports/metrics.json` (K5) |
| F2-06 | orta | kapandı | Referans doğrulama — `audit/dogrulama_seti.csv`, `ref_precision` 0,9997 (C13) |
| F2-07 | düşük | kapandı | C10 inceltmesi (koordinatör kararı) — `docs/03` C10, `audit/degisim_gunlugu.md` |
| F2-08 | düşük | kapandı | Tarım zinciri "33 olay" — `docs/kumeleme_yontemi.md:110`, `src/clustering/build_events.py:458` |
| F2-09 | düşük | kapandı | Temizlik MODIS dönemi kesinlik 0,228 — `metrics.temizlik_sanayi_loyo_precision_modis_donemi` |
| F2-10 | düşük | açık | Sabit yıl/saat sabitleri (K9, K11) |
| F2-11 | düşük | açık | Belge tutarsızlıkları |
| F2-12 | düşük | açık | Kontrol zayıflıkları — `tools/check_all.py` |
| F4-01 | yüksek | kapandı | TR "son tam ay" kutusu 2026'da eşdeğer seriyi gösteriyor, iki sensörün kendi verisiyle çelişiyor — `src/app/co |
| F4-02 | orta | kapandı | Mevcut ay kutusu matristeki seriyi izlemiyor — `core.js:160` |
| F4-03 | düşük | kapandı | Aynı büyüklük ekranda iki farklı değer — `main.js:230` |
| F4-04 | düşük | kısmen | Görüntü kusurları |
| F5-01 | orta | kapandı | Jüri demo senaryoları 2 ve 5 uygulamada yazıldığı gibi yürümüyor |
| F5-02 | orta | kapandı | Ham kod metni ve EN ondalık raporda ve ekranda |
| F5-03 | düşük | açık | Etiket (C24) — türetilmiş sonuç "ölçüldü" |
| F5-04 | düşük | kapandı | F4-04 kalıntıları |
| F3-01 | düşük | kapandı | `docs/arayuz_yontemi.md:150` (C18 anahtar sayısı belge uyuşmazlığı) |
