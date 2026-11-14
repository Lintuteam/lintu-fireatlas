# Çalışma Prensibi Raporu

Veri sürümü: {{meta.veri_surumu}} · Üretim tarihi: {{meta.uretim_tarihi}}
Denetim durumu: {{meta.denetim_durumu}}

> Bu rapor, uygulamanın nasıl çalıştığını **öğrenmek** içindir. Her kural iki katmanda anlatılır: önce **Basitçe** (benzetme), sonra **Teknik olarak** (tanım, formül, eşik, gerekçe, kodda nerede). Tüm sayılar `reports/metrics.json` dosyasından gelir; yanlarındaki parantez dürüstlük etiketidir: **ölçüldü** (veriden sayıldı/hesaplandı), **tahmini** (modele/kurala/çıkarıma dayanır), **doğrulanmadı** (bağımsız kanıt yok). "Aktivite" her yerde tarihsel hotspot yoğunluğu demektir; yangın riski veya tehlike tahmini değildir.

## 1. Uygulama ne yapar?

**Basitçe:** Elimizde iki farklı termometre var. Eski olan (MODIS, 2000'den beri) kaba, yeni olan (VIIRS, {{veri_ilk_viirs_yili}}'den beri) çok hassas. Yeni termometre geldiği yıl, "yangın sayısı" kâğıt üzerinde bir anda patlıyor; oysa yangınlar artmadı, yalnızca daha çok şey görmeye başladık. Bu uygulama (1) yangın olmayan sıcak yerleri (fabrika bacası, deniz, volkan) ayırır, (2) aynı yangının birçok fotoğrafını tek yangın sayar, (3) yeni termometrenin ölçümünü eski termometrenin diline çevirip 20+ yıllık karşılaştırılabilir bir seri yapar, (4) bunun üstünde yıl×ay yangın aktivite takvimi gösterir.

**Teknik olarak:** NASA FIRMS MODIS (Terra, Aqua) ve VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21) aktif yangın tespitleri Türkiye için {{veri_yil_bas}}–{{veri_yil_bit}} arasında {{veri_toplam_nokta|t}} satırdır (MODIS {{veri_modis_nokta|t}}, VIIRS {{veri_viirs_nokta|t}}; son gün {{veri_son_gun}}; {{veri_nrt_nokta|t}} nokta NRT, yani NASA `type` etiketi yok). Hat şudur:

`ham veri → ortak şema (points) → temizlik etiketi (status) → MODIS ayak izine eşleştirme (mcell) → olay kümeleme (events) → harmonizasyon (MODIS-eşdeğer seri) → takvim/anomali (agg) → arayüz`

Kurallar (CLAUDE.md): K1 sayılar betikle hesaplanır; K3 hiçbir nokta silinmez, etiketlenir; K4 kalibrasyon ve test ayrıdır (yıl dışarıda bırakma); K5 her iddia etiketlenir; K11 depolama UTC, gün TR (UTC+3), yıl kırpılmaz.

### Sözlük (Yusuf için)

| Terim | Basitçe | Teknik |
|---|---|---|
| Hotspot / tespit | Uydunun "burada sıcak bir şey var" dediği nokta; yangın olduğunu kanıtlamaz | Tek piksel tespiti (satır) |
| Olay | Aynı yangına ait tespitlerin toplandığı kutu | Kümeleme sonucu (`event_id`) |
| MODIS / VIIRS | Eski kaba / yeni hassas termometre | 1 km / 375 m piksel |
| FRP | Yangının gücü (megavat) | Fire Radiative Power, MW |
| NRT | Henüz "kesin" onaylanmamış hızlı veri | `type = -1`, NASA sınıf etiketi yok |
| LOYO | Bir yılı sakla, kalan yıllarla öğren, saklanan yılı tahmin et | Leave-one-year-out çapraz doğrulama (K4) |
| MAPE / WAPE | Ortalama yüzde hata | Mutlak yüzde hata (WAPE: ağırlıklı) |
| Efor | Kaç uydunun baktığı | Gözleyen uydu sayısı (2018'de 2., 2023'te 3. VIIRS) |

## 2. Veri hattı

**Basitçe:** {{veri_dosya_sayisi}} ayrı Excel dosyası tek bir temiz tabloya çevrilir: her satır bir tespit. Hangi satırın hangi dosyadan geldiği ve ham değerin kendisi saklanır; ham veriye dokunulmaz.

**Teknik olarak:** Şema `docs/04_VERI_SOZLESMESI_TASLAK.md` (kesin v1); `pid` kalıcı satır kimliğidir. Güven kodlaması tek yerdedir (K10): MODIS 0–100 sayısal (düşük 0–29, nominal 30–79, yüksek 80–100), VIIRS harf (l/n/h → düşük/nominal/yüksek); `src/config/esikler.json → guven`, okuyan `src/config/config.py`. Zaman `t_utc` olarak saklanır, `day_tr` sabit UTC+3 ile hesaplanır ve yıl kırpılmaz (C07). Bağımsız denetçi ham xlsx'i farklı bir yöntemle yeniden saydı: beklenen {{veri_toplam_nokta}} = bulunan, fark 0 (`audit/yeniden_hesap.json`, ölçüldü). Gözlem kapsamı (hangi uydu hangi gün çalıştı) NASA geçiş listesi değil, tespit sayılarından **çıkarımdır**; {{kapsam_kesinti_uydu_gunu|t}}. Kod: `src/pipeline/`.

## 3. Temizlik: satır silinmez, etiketlenir

**Basitçe:** Gelen sıcak noktaların hepsi orman yangını değil. Bacalar, deniz üstündeki gemiler/platformlar, volkanlar ve tarla yakmaları da var. Hiçbirini çöpe atmıyoruz; her birine "bu bir baca", "bu anız" gibi bir etiket yapıştırıyoruz. İsteyen etiketi kapatıp hepsini görebilir.

**Teknik olarak** (`docs/temizlik_yontemi.md`, `src/cleaning/`): sonuç etiketler (`points_status.parquet`):

{{huni.tablo}}

Temiz + anız noktalar ({{huni_kumeleme_girdi|t}}) kümelemeye girer; ham noktaların {{huni_nasa_etiket_pay|t}} NASA etiketiyle, {{huni_kural_etiket_pay|t}} kendi kuralımızla ayrılmıştır. Yöntem **kural tabanlıdır**; makine öğrenmesi kullanılmadı. Eşikler yıl dışarıda bırakma (LOYO) ile seçildi.

### 3.1 NASA etiketleri korunur (U-07)

**Basitçe:** NASA bazı noktalara zaten "volkan", "deniz", "sabit kara kaynağı" demiş. Ona güveniyoruz.
**Teknik olarak:** `type=1 → volkan`, `type=3 → deniz`, `type=2 → statik_nasa`. NRT'de bu etiket yok; arşivdeki komşu noktalardan miras alınır (`nasa_miras_payi`): {{temizlik_nrt_statik_mirasi|t}} nokta. NRT deniz telafisi zayıf ve doğrulanmadı.

### 3.2 Sanayi kuralı: yıllarca aynı yerde yanan baca (U-08)

**Basitçe:** Bir orman yangını beş farklı yılda, yılın sekiz ayında aynı 1 km'lik karede sürmez. Sürüyorsa orası fabrika, rafineri ya da meşaledir.
**Teknik olarak:** 0,01° hücrede, iki sensör birlikte: farklı yıl ≥ Y, farklı takvim ayı ≥ M, farklı gün ≥ N ve aktif yıllarda yıl içi ay sayısı medyanı ≥ S → `sanayi`. Eşikler (N, M, Y, S) LOYO'da NASA type=2'ye karşı F1 enbüyüklenerek seçildi (eşik tablosu §10). LOYO uyuşması: kesinlik {{temizlik_sanayi_loyo_precision|t}}, duyarlılık {{temizlik_sanayi_loyo_recall|t}}. **Dikkat:** NASA type=2 yer gerçeği değil bir maskedir; bu sayılar "uyuşma"dır. VIIRS döneminde kesinlik {{temizlik_sanayi_loyo_precision_viirs_donemi|t}}, MODIS döneminde {{temizlik_sanayi_loyo_precision_modis_donemi|t}}: referans seyrek olduğu için; kuralın 'sanayi' dediği MODIS noktalarının {{temizlik_modis_donemi_sanayi_tesis_payi|yuzde}} bilinen bir tesise yakın.

### 3.3 Kalıcı ısı kaynağı (belirsiz)

**Basitçe:** Düzenli ama bacadan farklı davranan yerler (kömür ocağı, çöplük). "Baca" demeden ayrı sepete koyarız: {{temizlik_status_kalici_belirsiz|t}} nokta.
**Teknik olarak:** Y ve M koşulunu sağlayan, N veya S'yi sağlamayan ve tespitlerinin en az `kalici_gece_payi` kadarı gece olan hücre (gece şartı: tarla yakması gündüz yoğundur).

### 3.4 Gerçek yangını silmeme: yangın koruması

**Basitçe:** Rafineri yanında gerçek orman yangını çıkarsa rafineri karesindeki noktaları da "baca" diye atmak yanlış olur. O gün çevrede normal karelerde de ateş varsa noktayı temiz bırakırız.
**Teknik olarak:** Kural-sanayi/kalıcı noktası, aynı TR gününde komşuluktaki kalıcı olmayan hücrelerde en az G tespit varsa `temiz` kalır: {{temizlik_yangin_korumasi_nokta|t}} nokta. Referans yangınlardaki noktaların {{temizlik_ref_yangin_koruma|yuzde}} kadarı korunur (tahmini; küçük set).

### 3.5 Anız takvimi (U-09)

**Basitçe:** Hasattan sonra tarlada sap yakılır; küçük, kısa, zayıf ateşlerdir ve her yıl aşağı yukarı aynı aylarda olur, ama bölgeden bölgeye değişir. Hangi bölgede hangi ayların "anız ayı" olduğunu 20 yıllık veriden öğreniyoruz. Hile olmasın diye bir yılın anız aylarını hep **o yıl hariç** öğreniyoruz.
**Teknik olarak** (`src/cleaning/aniz_takvim.py`, `olay_aniz.py`): küçük aday = FRP < F (MODIS ölçeğinde {{temizlik_F_modis_medyan|t}}; VIIRS eşdeğeri sabit oranla değil yüzdelik eşleştirmeyle {{temizlik_F_viirs_esdeger|t}}, K8) ve çevresinde az tespit. Profil: 7 bölge × ay payları. **Nihai karar olay düzeyindedir**: olay ≤ {{cfg:temizlik.aniz_olay_max_tespit}} tespit (MODIS ölçeğinde tekil eşleştirme birimi `n_mcell` sayılır, çünkü VIIRS aynı ateşi 3–4 nokta görür), ≤ {{cfg:temizlik.aniz_olay_max_sure_saat}} saat, düşük FRP ve olayın bölgesinin o yıl hariç öğrenilmiş anız ayında → olay `aniz`. Sonuç {{temizlik_status_aniz|t}} nokta. **Dürüst bulgu:** LOYO kaldıraç {{temizlik_aniz_loyo_kaldirac|t}}: "ay" tek başına küçük ateşi büyükten ayırmaz; ayırıcı olan büyüklük/süre/FRP koşuludur.

**Bağımsız doğrulama (döngüsellik önlemi):** (a) ESA WorldCover 2021 (veriden bağımsız arazi haritası): anız noktalarının {{temizlik_wc_aniz_ekili_alan_pay|yuzde}} ekili alanda; büyük temiz yangınların {{temizlik_wc_buyuk_temiz_ekili_alan_pay|yuzde}} ekili, {{temizlik_wc_buyuk_temiz_agac_pay|yuzde}} ağaçlı alanda; sanayi/kalıcı noktaların {{temizlik_wc_kural_kalici_yapilasmis_pay|yuzde}} yapılaşmış alanda. (b) Kaba ulusal hasat penceresiyle uyum {{temizlik_aniz_hasat_penceresi_payi|yuzde}} (tahmini). **Doğrulanmadı:** saha, yanmış alan veya resmi yangın kaydıyla karşılaştırma yok.

### 3.6 Referans (bağımsız) doğrulama (C13)

**Basitçe:** Kuralı, FIRMS'ten bağımsız bir listeyle sınadık: {{dogrulama_sanayi_tesis}} bilinen sanayi tesisi (OpenStreetMap) ve {{dogrulama_bilinen_yangin}} bilinen yangın. Tesis sayısı yangından çok olduğu için "her tesise ve her yangına eşit oy" verdik.
**Teknik olarak:** Dengeli kesinlik {{ref_precision|t}}, tesis yakalama (makro duyarlılık) {{ref_recall|t}}, tesis düzeyi {{temizlik_ref_site_recall|t}}, yangın başına yanlış işaret {{temizlik_ref_makro_yangin_fpr|t}}. Yani **bazı tesisler kaçıyor** (özellikle termik santraller). Static Thermal Anomalies maskesiyle karşılaştırma yapılamadı ({{temizlik_sta_maskesi_karsilastirma|t}}).

## 4. Eşleştirme: MODIS'in ayak izi (U-02)

**Basitçe:** MODIS'in bir pikseli yerde büyük bir kare; VIIRS aynı yere 3–4 küçük kare düşürür. "MODIS'te 1, VIIRS'te 4 yangın" sorunu bundandır. Çözüm: her VIIRS noktasını, kendisini kaplayan MODIS karesine bağlamak.
**Teknik olarak** (`src/harmonize/eslestirme.py`): ayak izi = MODIS merkezinde `scan × track` km dikdörtgen + yarım VIIRS pikseli tamponu ({{cfg:eslesme_tamponu_km}} km). Bir VIIRS noktası birden çok ize düşerse sırasıyla eşzamanlı iz, en küçük normalize uzaklık, en küçük zaman farkı, en küçük alan seçilir; nokta tek hücreye gider ve FRP bölünmez. İze düşmeyen VIIRS noktası (yalnız VIIRS) 0,01° ızgara yedeğine gider. Ölçüm: {{mcell_viirs_toplam|t}} VIIRS noktasının {{mcell_viirs_modis_izinde|t}} tanesi MODIS izinde; MODIS izi başına ortalama {{mcell_iz_basina_viirs|t}} VIIRS noktası; sabit ızgara aynı izi {{mcell_iz_basina_izgara|t}} hücreye bölerdi (bölünen iz oranı {{mcell_izgarada_bolunen_oran|yuzde}}).

## 5. Kümeleme: aynı yangını bir kez say (U-10, U-11, U-12)

**Basitçe:** Uydular aynı yangının birçok fotoğrafını çeker. İki fotoğraf yakın yerde ve yakın zamandaysa aynı yangındır; A–B yakın, B–C yakınsa üçü de aynıdır (zincir). MODIS ve VIIRS fotoğrafları **birlikte** değerlendirilir; böylece aynı yangın iki kez sayılmaz.
**Teknik olarak** (`src/clustering/`, `docs/kumeleme_yontemi.md`): olay = bağ grafiğinin bağlı bileşeni (union-find). Bağ: mesafe ≤ D **veya** MODIS–VIIRS çiftinde VIIRS merkezi MODIS ayak izinin içinde; ve zaman koşulu. D = {{cfg:D}} km, eşleştirme modu {{cfg:kumeleme.eslestirme_modu}}, boşluk kuralı {{cfg:kumeleme.bosluk_kurali}} (L = {{cfg:kumeleme.L}} geçiş penceresi, Hmax = {{cfg:kumeleme.Hmax}} saat; kaynak `src/config/esikler.json`).

**Boşluk kuralı (U-11), basitçe:** "14 saattir görmedim, söndü mü?" sorusunun cevabı uydunun o sürede gerçekten geçip geçmediğine bağlıdır. Boşluğu saatle değil **kaçırılan geçişle** sayarız: uydu geçti ve görmediyse "kaçırma", hiç geçmediyse beklenir. Teknik: |Δt| ≤ Hmax ve aradaki gözlenmiş geçiş penceresi ≤ L (eşik tablosu §10). Günlük geçiş saati ~3 saat kaydığı için sabit H=24 bir yangını gereksiz bölerdi; geçiş kuralı bunu düzeltir (swath verisi olmadığı için pencereler çıkarım, tahmini).

Sonuç: {{events_total|t}} olay; ortak kümeleme çakışma döneminde {{events_joint_overlap|t}} olay verir, sensörler ayrı kümelenseydi {{events_separate_overlap|t}} olurdu: **{{events_double_count_avoided|t}} çifte sayım önlenir**. Üçlü sınıf: ortak {{events_match_ortak|t}}, yalnız MODIS {{events_match_yalniz_modis|t}}, yalnız VIIRS {{events_match_yalniz_viirs|t}}, tek sensör dönemi {{events_match_tek_sensor_donemi|t}}. MODIS olaylarının VIIRS'te de görülme payı {{events_modis_seen_by_viirs_share|yuzde}}; ayak izi eşleştirmesi bunu sabit 1 km kuralına göre ({{events_modis_seen_by_viirs_share_sabit|yuzde}}) artırır ama asıl neden eşleştirme değil, Terra'nın sabah geçişinin VIIRS'le eşzamanlı olmamasıdır (Aqua ile eşzamanlıyken bile 1 km içinde VIIRS payı {{aqua_nearest_viirs_within_1km_share|yuzde}}).

**Zincirleme riski:** Bitişik bağımsız küçük yangınlar köprülenip dev olaya dönüşebilir. En büyük olay {{huni_en_buyuk_olay_tespit|t}} tespit (gerçek mega yangın, 2021 Manavgat); temiz olmayan nokta zincire köprü olamaz. Kümeleme algoritması, tam O(n²) kaba kuvvetle {{c03_karsilastirma|t}} karşılaştırmada, {{c03_fark_olan|t}} farkla birebir aynı sonucu verdi (C03).

## 6. Harmonizasyon: VIIRS'i MODIS'in diline çevirmek (U-01, U-04, U-05)

**Basitçe:** "MODIS bu ayı görseydi kaç sayardı?" sorusunu cevaplıyoruz. Hassas termometrenin ölçümünü eski termometrenin diline çeviriyoruz; hassas ölçüm de çöpe gitmiyor, yanında ayrı bir katman olarak duruyor (iki çıktı: karşılaştırma için eşdeğer seri, ayrıntı için ham VIIRS).

**Soru 3 bilimsel seri kararı (`docs/01_ISTEKLER.md` §E):** Çok yıllı karşılaştırma, yıl×ay matrisi, trend ve anomalide varsayılan ana seri **MODIS-eşdeğer seri** (`olay_esdeger` / `modis_esdeger` + LOYO %95 belirsizlik bandı) olarak belirlenmiştir; çünkü 2000–2011 döneminde VIIRS yoktu ve sensör geçişlerinden doğan sıçramalar gerçek yangın eğilimiyle karıştırılmamalıdır. Buna karşılık 375 m ham VIIRS noktaları ve üçlü sınıf (`ortak`, `yalniz_viirs`, `yalniz_modis`) katmanları harita, laboratuvar ve müfettişte yan yana eksiksiz sunulur. Kullanıcı üst bardaki `#sciModeBtn` düğmesinden ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya gelişmiş süzgeçlerdeki `#seriesSel` menüsünden (`src/app/main.js` `S.aggSeries`) bu seçimi tek tıkla değiştirebilir.

**Teknik olarak** (`src/harmonize/`, `docs/harmonizasyon_yontemi.md`):

1. **Gözlem eforu.** VIIRS toplamı, o gün gözleyen VIIRS uydu sayısına bölünür (2018'de N20, 2023'te N21 eklendi). Etkisi: N20 geçişinde ham VIIRS {{jump_n20_2018_ham_pct|t}}, eforlu {{jump_n20_2018_eforlu_pct|t}}, gerçek MODIS {{jump_n20_2018_modis_pct|t}}.
2. **MODIS etkin tespit sınırı (FRP50).** Aqua'nın bir VIIRS hücresini yarı olasılıkla gördüğü toplam FRP: genel {{modis_frp50_genel_mw|t}}, gündüz {{modis_frp50_gunduz_mw|t}}, gece {{modis_frp50_gece_mw|t}} (etkin sınır; fiziksel algılama sınırından büyüktür, tahmini).
3. **Güven sınıfı çevirisi (S1).** Aynı yangına aynı anda bakan Aqua–VIIRS {{guven_cift_sayisi|t}} çiftiyle VIIRS düşük/nominal/yüksek payları MODIS yüzdesine eşlendi: öğrenilen MODIS sınırları {{guven_ogrenilen_sinirlar|t}} (FIRMS'in kendi cetveline yakın), yıl dışarıda bırakmada çok kararlı ({{guven_loyo_c1_aralik|t}} ve {{guven_loyo_c2_aralik|t}}). Ama iki uydunun tek yangındaki güveni zayıf ilişkili (Spearman {{guven_spearman|t}}) ve öğrenilmiş eşleme FIRMS'i geçemedi (kappa {{guven_loyo_kappa_ogrenilen|t}} karşı {{guven_loyo_kappa_firms|t}}). Bu yüzden arayüzde varsayılan ham FIRMS sınıfıdır.
4. **Yöntem yarışı (K8, sabit oran tuzağı).** Üç yöntem LOYO ile yarıştı (hedef: gerçek MODIS tespiti, ay×bölge): (i0) tek sabit oran, efor yok (WAPE {{harm_i0_ay_bolge_wape|t}}, yıllık MAPE {{harm_i0_yillik_mape|t}}, R² {{harm_i0_yillik_r2|t}}); (i) tek sabit oran, eforlu (WAPE {{harm_i_ay_bolge_wape|t}}, MAPE {{harm_i_yillik_mape|t}}); (ii) bölge×mevsim×FRP büyüklüğü oranı, eforlu (WAPE {{harm_ii_ay_bolge_wape|t}}, MAPE {{harm_ii_yillik_mape|t}}); (iii) FRP eşik eğrisi (WAPE {{harm_iii_ay_bolge_wape|t}}). **Dürüst okuma:** asıl kazanç efor düzeltmesidir; (ii) ile (i) ay×bölgede ayırt edilemez (fark %95 aralığı {{harm_ii_eksi_i_wape_ci95|t}}). (ii) uygulamanın birimi (ay×bölge) için seçildi, üstünlük iddiası değildir. Kazanan: {{harm_kazanan_yontem|t}}.
5. **Belirsizlik bandı.** LOYO artıklarının yüzdeliklerinden: aylık ülke toplamı için %95 hata bandı {{equiv_overlap_band|t}}; bant gerçek MODIS'i ay×ülkede {{equiv_band_kapsama_ay_tr|yuzde}}, ay×bölgede {{equiv_band_kapsama_ay_bolge|yuzde}} oranında kapsadı. Eski dönem (2000–Temmuz 2002, yalnız Terra) düzeltilmez, düşük güven bayraklıdır.
6. **Sıçrama ölçütü.** Sıçrama = geçiş sonrası {{cfg:harmonizasyon.sicrama_pencere_yil}} yıl ortalaması / geçiş öncesi {{cfg:harmonizasyon.sicrama_pencere_yil}} yıl ortalaması − 1. Ham {{jump_raw_pct|t}}; harmonize {{jump_harm_pct|t}}; aynı pencerede gerçek MODIS {{jump_modis_gercek_pct|t}}; harmonizasyonun eklediği fark {{jump_resid_pct|t}}. 2012 sonrası harmonize değerler LOYO tahminleridir (o yıl öğrenmede yoktu).
7. **Yörünge kayması.** Aqua öğle geçişi {{aqua_gunduz_gecis_utc_2015|t}} (2015) → {{aqua_gunduz_gecis_utc_2026|t}} (2026) kaydı; Aqua–VIIRS eşzamanlı çift payı {{aqua_viirs_esz_cift_payi_2015|yuzde}} → {{aqua_viirs_esz_cift_payi_2026|yuzde}}. Bu yüzden **2026 eşdeğer değerleri eğitim rejiminin dışındadır**, düşük güven bayraklıdır (bant kapsaması {{harm_2026_bant_kapsama|yuzde}}, doğrulanmadı).

## 7. Takvim ve anomali (U-16, N-05, N-06, N-07)

**Basitçe:** Her ilin her günü için "kaç sıcak nokta / kaç olay" defteri tutulur, yanına "o gün uydular gerçekten bakabildi mi?" yazılır. Bakılamayan gün "sıfır yangın" demek değildir. "En yoğun ay", geçmiş yılların o ayının **medyanı** en yüksek olan aydır; iki ay birbirine çok yakınsa "ayırt edilemez" denir. Anomali: bir yılın bir ayı, o yıl hariç diğer yılların aynı ayıyla kıyaslanır.

**Teknik olarak** (`docs/takvim_yontemi.md`, `src/analytics/`): aylık sayım, kesinti günleri paydadan düşülerek ölçeklenir (C06); ay yarımsa veya neredeyse hiç bakılamadıysa hücre boş kalır, sıfır yazılmaz. Birim: {{takvim_birim_sayisi|t}} (ülke, bölge, il). Medyan ve sıralama; ayırt edilemezlik için komşu ay göreli fark eşiği + yıl bootstrap'ı. Anomali: log1p ölçeğinde sağlam z = (x − medyan)/max(1,4826·MAD, taban), normal yıllar ve test yılı hariç, |z| ≥ {{cfg:takvim.z_esik}}. Sonuçlar: MODIS ham serisinde ilk üç ay {{takvim_top3_ay_modis_ham_TR|ay,e}}, temiz serisinde {{takvim_top3_ay_modis_temiz_TR|ay,e}}, MODIS-eşdeğer seride {{takvim_top3_ay_modis_esdeger_TR|ay,e}}, olay serisinde {{takvim_top3_ay_olay_TR|ay,e}}. Temizliğin etkisi: ham ve temiz sıralamalar il düzeyinde ilk üç ayın {{takvim_ham_temiz_top3_degisen_il_payi|t}} oranında değişiyor. Mevcut ay, geçmiş yılların **aynı ilk günleriyle** kıyaslanır (kısmi ay açıkça yazılır): son veri günü {{takvim_son_gun}}, kısmi gün {{takvim_mevcut_ay_kismi_gun_TR|t}}, NRT payı {{takvim_mevcut_ay_nrt_payi_TR|t}}, MODIS oranı {{takvim_mevcut_ay_oran_modis_temiz_TR|t}}, VIIRS oranı {{takvim_mevcut_ay_oran_viirs_temiz_ub_TR|t}}; MODIS'e özgü ek düşüşün nedeni {{takvim_mevcut_ay_ayrisma_yorum_TR|t,yorum}}. Eşdeğer serilerde anomali işaretlerinin {{takvim_anomali_belirsiz_bant_payi_esdeger|t}} oranı belirsiz banda düşer.

## 8. Arayüz

**Basitçe:** Tek sayfalık, internetsiz açılan bir uygulama: harita, takvim, sıçrama grafiği, birleştirme laboratuvarı, piksel büyümesi ve dışa aktarma.
**Teknik olarak** (`src/app/`): kütüphaneler yerelde (C21); ekrandaki her sayı `metrics.json` veya agg tablolarından gelir (C14), sabit metrik/`Math.random` yoktur (C15); TR/EN (C18); CSV UTF-8 BOM ile (C17). Varsayılan takvim/trend serisi `olay_esdeger`dir (Soru 3 bilimsel kararı); üst bardaki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya gelişmiş süzgeçlerdeki `#seriesSel` menüsü (`src/app/main.js` `S.aggSeries`) üzerinden tek tıkla değiştirilebilir, ayrıca `#quickExportBtn` ile süzülmüş olaylar anında CSV indirilir. Performans: eşik değişince tüm görünümler {{perf_esik_degisimi_sn|t}} içinde yeniden çizilir ({{perf_olay_sayisi|t}} olay; tek ölçüm, bu makine). Erişilebilirlik: klavye {{a11y_klavye_oran|yuzde}}, adlı öğe {{a11y_aria_adli_oran|yuzde}}, en düşük kontrast {{a11y_kontrast_min|t}}; ekran okuyucu testi yapılmadı (doğrulanmadı). Stil: `referans/STIL_NOTU.md`.

## 9. Duyarlılık: eşikler değişirse sonuç ne kadar oynar? (C12)

**Basitçe:** Cetveli biraz kaydırınca cevap ne kadar kayıyor? Çok kayıyorsa o sayıyı kuralıyla birlikte söylemek zorundayız.
**Teknik olarak:** Her eşik için en az üç değer denendi.

{{duyarlilik.kumeleme}}

{{duyarlilik.temizlik}}

Okuma: olay sayısı D ve H'ye güçlü bağlıdır; bu yüzden "olay sayısı" her zaman kuralıyla birlikte verilmelidir.

## 10. Eşik tablosu (K9: tek yapılandırma dosyası)

{{esik.tablosu}}

## 11. Sınırlar ve yapılmayanlar

{{sinirlar.liste}}

## 12. Kodda nerede?

{{kod.harita}}

## 13. Yusuf için on cümlelik özet

1. Veri {{veri_toplam_nokta}} sıcak noktadır; bunların hepsi yangın değildir, hiçbiri silinmez.
2. Önce temizlik: deniz/volkan/sanayi/anız etiketlenir, gerçek yangın korunur.
3. Aynı yangının fotoğrafları kümelenerek {{events_total}} olaya iner.
4. VIIRS, MODIS'in ayak izine bağlanır; böylece 1'e 4 sorunu aynı hücrede toplanır.
5. Uydu sayısı değişince (efor) sayılar değişir; önce buna göre düzeltilir.
6. Harmonizasyon, hassas VIIRS'i eski MODIS diline çevirir; yöntem bir yılı saklayıp tahmin ederek (LOYO) sınanır.
7. Sıçrama {{jump_raw_pct|t}} iken harmonize seri gerçek MODIS düşüşünü {{jump_resid_pct|t}} farkla izler; "çözdük" denmez.
8. Takvim medyan ve anomaliyle çalışır; yakın aylar "ayırt edilemez" denir.
9. Her sayının yanında etiket vardır: ölçüldü / tahmini / doğrulanmadı.
10. Doğrulanmayanlar (2026 eşdeğer, anız yer doğrulaması, ekran okuyucu, swath) açıkça yazılıdır.
