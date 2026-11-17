## S1
**Basitçe:** Evet, ve bunu "sınav sorusunu önceden görmeden" sınadık: her yılı sırayla saklayıp kalan yıllardan öğrendik.
**Kanıt:** Yıllık MAPE {{loyo_mape|t}}, R² {{loyo_r2|t}}, sapma {{loyo_bias|t}}. Efor düzeltmesi olmayan tek oran aynı testte MAPE {{harm_i0_yillik_mape|t}}, R² {{harm_i0_yillik_r2|t}} verdi. Yıllık %95 hata aralığı {{loyo_ci95|t}}: yani tek bir yılın tahmini yine de yaklaşık bu aralıkta şaşabilir.

## S2
**Basitçe:** Büyük ölçüde sensör: yeni termometre geldi, aktivite aslında azalmıştı.
**Kanıt:** Ham seri geçişte {{jump_raw_pct|t}} sıçrıyor. Gerçek MODIS aynı pencerede {{jump_modis_gercek_pct|t}}; harmonize seri {{jump_harm_pct|t}}; fark {{jump_resid_pct|t}}, LOYO aralığı {{loyo_ci95|t}} içinde. Bu, "artış sensör eklenmesindendir" demek için güçlü ama kesin olmayan kanıttır; 2012'de ek bir iklim/yangın etkisini ayırt edemeyiz.

## S3
**Basitçe:** Hayır, "kayboldu" demek dürüst olmaz; ölçütü sonuç görüldükten sonra inceltmek zorunda kaldık ve bunu açıkça söylüyoruz.
**Kanıt:** İlk ölçüt (harmonize sıçrama doğal aralıkta olmalı) sağlanmadı çünkü gerçek MODIS de aralığın dışındaydı ({{jump_null_ci95|t}}; harmonize aralıkta mı: {{jump_harm_dogal_aralikta|t}}). Ölçüt "artık sıçrama LOYO hata aralığında" olarak değiştirildi (`audit/degisim_gunlugu.md`). Doğru cümle: harmonize seri gerçek MODIS düşüşünü {{jump_resid_pct|t}} farkla izliyor. Bağımsız denetçi, 3+3 yıllık pencerelerle ayrıca sınadı ve sonucu ölçüt seçiminden bağımsız buldu (`audit/bulgular.md` F2-07).

## S4
**Basitçe:** Tek oran, bazı ayları fazla bazılarını az sayar; asıl düzeltilmesi gereken şey kaç uydunun baktığıdır.
**Kanıt:** Efor düzeltmesiz tek oran ay×bölge WAPE {{harm_i0_ay_bolge_wape|t}}; eforlu sabit oran (i) {{harm_i_ay_bolge_wape|t}}; bölge×mevsim×büyüklük oranı (ii) {{harm_ii_ay_bolge_wape|t}}. (i) ile (ii) ayırt edilemez (fark %95 aralığı {{harm_ii_eksi_i_wape_ci95|t}}); yani (ii)'nin üstün olduğunu iddia etmiyoruz, asıl kazanç efor. (ii), uygulamanın birimi ay×bölge olduğu için seçildi.

## S5
**Basitçe:** Kontrol ettik: olay sayısı hiçbir bölge ve ayda tespit sayısını aşmıyor; aşan hücreler kırpılıyor.
**Kanıt:** Kırpılan hücre sayısı ay×bölge {{olay_tespitle_kirpilan_temiz_ay_bolge|t}}, ay×ülke {{olay_tespitle_kirpilan_temiz_ay_TR|t}}, yıl×ülke {{olay_tespitle_kirpilan_temiz_yil_TR|t}}; denetçinin bağımsız sorgusu olay eşdeğeri > tespit eşdeğeri ihlali bulmadı (`audit/bulgular.md` F2-01 kapanışı).

## S6
**Basitçe:** Sayıyoruz ama bir kez: yakın yerde yakın zamanda gelen noktalar aynı yangındır, MODIS'ten de VIIRS'ten de gelse.
**Kanıt:** Çakışma döneminde ortak kümeleme {{events_joint_overlap|t}} olay verir; sensörler ayrı kümelenseydi {{events_separate_overlap|t}} olurdu: {{events_double_count_avoided|t}} çifte sayım önlenir. MODIS izi başına ortalama {{mcell_iz_basina_viirs|t}} VIIRS noktası düşer; sabit ızgara aynı izi {{mcell_iz_basina_izgara|t}} parçaya bölerdi.

## S7
**Basitçe:** Çünkü iki uydu aynı anda bakmıyor; MODIS'in gördüğü kısa ömürlü yangını VIIRS'in geçişi kaçırabiliyor.
**Kanıt:** MODIS olaylarının VIIRS'te de görülme payı {{events_modis_seen_by_viirs_share|yuzde}}. Ayak izi eşleştirmesi bunu sabit 1 km kuralına göre ({{events_modis_seen_by_viirs_share_sabit|yuzde}}) biraz artırır ama asıl neden değildir. Eşzamanlı Aqua geçişinde bile en yakın VIIRS 1 km içinde olanların payı {{aqua_nearest_viirs_within_1km_share|yuzde}}. (Yalnız-MODIS olayların çoğunun sabah Terra geçişinden gelmesi `docs/kumeleme_yontemi.md` §1'de tespit düzeyinde ölçülmüştür.)

## S8
**Basitçe:** VIIRS küçük yangınları da görür; bu yüzden ham sayısı artar. Onu MODIS'in görebileceği ölçeğe çevirince artış kayboluyor.
**Kanıt:** Ham yalnız-VIIRS geçişi {{jump_raw_viirs_only_pct|t}}. VIIRS'ten türetilen MODIS-eşdeğer seri, çakışma döneminde gerçek MODIS'le toplamda {{equiv_overlap_bias|t}} sapmayla uyumlu. Artış küçük yangınların görünür olmasındandır; aktivitenin arttığı anlamına gelmez.

## S9
**Basitçe:** Anızı küçük, kısa, zayıf ve belli aylarda olan ateş olarak tanımlıyoruz; bu kural tabanlıdır ve doğrulaması yalnız dolaylıdır.
**Kanıt:** Bölgeye özgü anız ayları yıl dışarıda bırakmayla öğrenilir; olay düzeyinde karar verilir (`n_mcell` ile). Bağımsız arazi haritası (ESA WorldCover): anız noktalarının {{temizlik_wc_aniz_ekili_alan_pay|yuzde}} ekili alanda; büyük temiz yangınların {{temizlik_wc_buyuk_temiz_ekili_alan_pay|yuzde}} ekili, {{temizlik_wc_buyuk_temiz_agac_pay|yuzde}} ağaçlı alanda. Dürüst sınır: ay tek başına ayırmıyor (LOYO kaldıraç {{temizlik_aniz_loyo_kaldirac|t}}). **Saha veya yanmış alan doğrulaması yok.**

## S10
**Basitçe:** Hiçbir noktayı silmedik, etiketledik; gerçek yangını korumak için özel bir koruma kuralı var. Ama bazı tesisler kaçıyor ve bunu saklamıyoruz.
**Kanıt:** Referans setinde dengeli kesinlik {{ref_precision|t}}; gerçek yangın noktalarının {{temizlik_ref_yangin_koruma|yuzde}} korunuyor, yangın başına yanlış işaret {{temizlik_ref_makro_yangin_fpr|t}}. Tesis yakalama {{ref_recall|t}} (tesis düzeyinde {{temizlik_ref_site_recall|t}}): bazı tesisler kaçıyor. Set küçük ({{dogrulama_sanayi_tesis}} tesis, {{dogrulama_bilinen_yangin}} yangın). Nokta düzeyi kesinlik ({{temizlik_ref_nokta_precision|t}}) sınıf dengesizliğinden şişkindir, sunumda kullanılmaz.

## S11
**Basitçe:** O dönemde NASA'nın kendi "sanayi" etiketi çok seyrek, bu yüzden bizim kuralımız yeni bulduğu yerleri "yanlış" sayılıyor; bu uyuşma ölçüsüdür, doğruluk değil.
**Kanıt:** MODIS döneminde NASA type=2 ile kesinlik {{temizlik_sanayi_loyo_precision_modis_donemi|t}}, VIIRS döneminde {{temizlik_sanayi_loyo_precision_viirs_donemi|t}}. Kuralın 'sanayi' dediği MODIS noktalarının {{temizlik_modis_donemi_sanayi_tesis_payi|yuzde}} bilinen bir tesise yakın.

## S12
**Basitçe:** Seri VIIRS'ten MODIS-eşdeğere çevrilerek sürer; ama bu kısmın doğruluğunu gösteremiyoruz, çünkü kıyaslanacak MODIS kalmayacak.
**Kanıt:** Aqua öğle geçişi {{aqua_gunduz_gecis_utc_2015|t}} (2015) → {{aqua_gunduz_gecis_utc_2026|t}} (2026) kaydı; Aqua–VIIRS eşzamanlı çift payı {{aqua_viirs_esz_cift_payi_2015|yuzde}} → {{aqua_viirs_esz_cift_payi_2026|yuzde}}. 2026'da eşdeğer bandı gerçek MODIS'i {{harm_2026_bant_kapsama|yuzde}} oranında kapsıyor (LOYO döneminde {{equiv_band_kapsama_ay_tr|yuzde}}). Yörünge kaymasını gidermeyen kalibrasyon varyantı ölçülmedi. **Eksik: MODIS sonrası dönem için bağımsız doğrulama yok.**

## S13
**Basitçe:** Kısmen gerçek (iki sensör de düşük), kısmen belirsiz (MODIS'in ek düşüşünün nedenini bilmiyoruz).
**Kanıt:** Son veri günü {{veri_son_gun}}; mevcut ay {{takvim_mevcut_ay_kismi_gun_TR|t}} kısmi, NRT payı {{takvim_mevcut_ay_nrt_payi_TR|t}}. Geçmiş medyana oran: MODIS {{takvim_mevcut_ay_oran_modis_temiz_TR|t}}, VIIRS {{takvim_mevcut_ay_oran_viirs_temiz_ub_TR|t}}. MODIS'e özgü ek düşüşün nedeni (sensör ömrü sonu, NRT, yörünge kayması): {{takvim_mevcut_ay_ayrisma_yorum_TR|t,yorum}}. Son tam ayda eşdeğer seri oranı {{takvim_son_tam_ay_oran_modis_esdeger_TR|t}} ama iki sensörün kendi oranları {{takvim_son_tam_ay_oran_modis_temiz_TR|t}} ve {{takvim_son_tam_ay_oran_viirs_temiz_ub_TR|t}}; bu yüzden eşdeğer güvenilmez işaretlenir ({{takvim_son_tam_ay_guvenilmez_modis_esdeger_TR|t}}).

## S14
**Basitçe:** Yaz sonu ve sonbahar; ama ağustos ile eylül birbirinden istatistiksel olarak ayrılamıyor.
**Kanıt:** Türkiye MODIS temiz serisinde ilk üç ay {{takvim_top3_ay_modis_temiz_TR|ay,e}}; MODIS-eşdeğer seride {{takvim_top3_ay_modis_esdeger_TR|ay,e}}; olay serisinde {{takvim_top3_ay_olay_TR|ay,e}}. Ayırt edilemezlik bayrağı {{takvim_ayirt_edilemez_modis_temiz_TR|t}} (1 = evet). Temizlik, il düzeyinde ilk üç ayın {{takvim_ham_temiz_top3_degisen_il_payi|t}} oranında değiştirir.

## S15
**Basitçe:** Hayır. Uygulama tarihsel hotspot yoğunluğunu gösterir; gelecekteki yangın riskini veya tehlikesini tahmin etmez.
**Kanıt:** Arayüz alt başlığı "tarihsel yangın aktivitesi (yangın riski değildir)" (`src/app/i18n/tr.json`, `app.sub`). {{veri_toplam_nokta|t}} nokta {{huni_olay_sayisi|t}} olaya iner; nokta sayısı yangın sayısı değildir.

## S16
**Basitçe:** Hayır; ekrandaki sayılar betikle üretilmiş dosyalardan okunur, ayrıca denetçi örnekleme ile ekranı veriyle karşılaştırdı.
**Kanıt:** C14 (ekran = hesap) ve C15 (rastgele/sabit metrik taraması) geçti; denetçinin çalışma anı karşılaştırmasında fark 0 (`audit/bulgular.md` F4). Bağımsız yeniden hesapta {{yh_girdi|t}} girdinin {{yh_fark_sifir}} tanesinde fark 0.

## S17
**Basitçe:** Hayır; uydunun bakmadığı günler "gözlem yok" ayrı renkle gösterilir ve aylık hesapta paydadan düşülür. Ama kesinti günlerini NASA'nın geçiş listesinden değil, tespit sayılarından çıkardık.
**Kanıt:** Çıkarımla kesinti işaretli uydu-günü: {{kapsam_kesinti_uydu_gunu|t}} (`coverage.parquet`, etiket tahmini); C06 geçti.

## S18
**Basitçe:** Belirsizlik küçük değil; bunu bant olarak gösteriyoruz.
**Kanıt:** Aylık ülke toplamı için %95 hata bandı {{equiv_overlap_band|t}}; bu bant gerçek MODIS'i LOYO'da ay×ülkede {{equiv_band_kapsama_ay_tr|yuzde}} oranında kapsadı. Yıllıkta {{loyo_ci95|t}}.

## S19
**Basitçe:** İki farklı ihtiyacı ayırdık: 25 yıllık zaman karşılaştırması için eski ve yeni termometreyi aynı dile çeviren MODIS-eşdeğer seriyi başa koyduk; ayrıntıyı görmek isteyen için ise hassas 375 m VIIRS verisini haritada ve tek düğmede yan yana açık bıraktık.
**Kanıt:** Kullanıcı onayıyla bilimsel standart (S3 kararı, `docs/01_ISTEKLER.md` §E): takvim/trend varsayılanı `olay_esdeger` / `modis_esdeger` (yıllık LOYO MAPE {{loyo_mape|t}}); aynı anda yalnız VIIRS katmanı ({{events_match_yalniz_viirs|t}} olay) harita ve laboratuvarda korunur. Üst bardaki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya `#seriesSel` ile tek tıkla değiştirilir.

## S20
**Basitçe:** Uygulama bir klasörü çift tıklayıp internet kesikken bile açılacak kadar bağımsızdır; filtre değiştiğinde saniyenin dörtte birinde yeniden hesaplar.
**Kanıt:** Dış CDN bağlantısı sıfırdır (C21); 27 yıllık {{perf_olay_sayisi|t}} temiz olayda eşik değişimi ortalama {{perf_esik_degisimi_sn|t}} sürer (C20); minimum WCAG kontrast {{a11y_kontrast_min|t}} ve renk körlüğü dE en az 14,0 (C19). **Doğrulanmayan:** Ekran okuyucuyla elle tarayıcı testi yapılmadı (`doğrulanmadı`).
