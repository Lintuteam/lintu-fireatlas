# Yöntem özeti (teknik, tek dosya)

> Kaynak: `belgeler_ve_denetim/{temizlik,kumeleme,harmonizasyon,takvim,arayuz}_yontemi.md`, `bulgular.md`, `raporlar/calisma_prensibi.md` ve `arayuz/data/metrics.json` (`metrics` anahtarı; her kayıtta `value, unit, etiket, tanim`).
> Gösterim: `anahtar` = metrics.json anahtarı; etiket = **ölçüldü / tahmini / doğrulanmadı** (metrics.json'daki etiket, değer o dosyadan okundu). Belgelerde olmayan bir eşik uydurulmadı; belgede olmayan şey "belgede yok" diye açıkça yazıldı. Eşiklerin tek kaynağı `src/config/esikler.json`'dır; yöntem belgeleri yalnız eşik adını verir, değerleri `raporlar/calisma_prensibi.md` §10 eşik tablosu ve metrics.json'dan alındı.
> "Aktivite" = tarihsel hotspot aktivitesi; yangın riski/tehlike tahmini değildir (K14).

---

## 1. Veri

| Öğe | Değer | Anahtar / etiket |
|---|---|---|
| Ürünler | NASA FIRMS MODIS Collection 6.1 (Terra, Aqua; 1 km piksel) ve VIIRS 375 m aktif yangın (SNPP, NOAA-20 "N20", NOAA-21 "N21") | `calisma_prensibi.md` §1; `arayuz_yontemi.md` §1 |
| Alan / dönem | Türkiye kutusu (bbox), 2000 – 2026; son gün 2026-11-12 (TR günü) | `veri_yil_bas` 2000, `veri_yil_bit` 2026, `veri_son_gun` 2026-11-12 (ölçüldü) |
| Toplam nokta | 1.414.674 | `veri_toplam_nokta` (ölçüldü) |
| MODIS / VIIRS | 259.707 / 1.154.967 | `veri_modis_nokta`, `veri_viirs_nokta` (ölçüldü) |
| NRT | 61.147 nokta (VIIRS 58.465 + MODIS 2.682, `bulgular.md` F1) | `veri_nrt_nokta` (ölçüldü) |
| Ham dosya | 27 xlsx (içinde 59 kaynak CSV) | `veri_dosya_sayisi` 27 (ölçüldü) |
| İlk VIIRS | 2012 (SNPP ilk tespit 2012-01-20) | `veri_ilk_viirs_yili` 2012 (ölçüldü); tarih `esikler.json` `viirs_baslangic_yili` açıklamasında |
| Uydu eklenişleri | Aqua 2002-07-04; N20 2018; N21 2023 | Aqua tarihi `esikler.json` `eski_donem_yillari` açıklaması; N20/N21 yılları `harmonizasyon_yontemi.md` §4 |
| Kesinti (çıkarım) | 129 uydu-gün | `kapsam_kesinti_uydu_gunu` (tahmini) |

**Güven eşlemesi (FIRMS ham sınıf, `conf_cls`; tek yerde, K10):** MODIS 0–100 sayısal: düşük 0–29, nominal 30–79, yüksek 80–100. VIIRS harf: l/n/h → düşük/nominal/yüksek. (`calisma_prensibi.md` §2; `harmonizasyon_yontemi.md` §2: "FIRMS cetveli 0–29/30–79/80–100".) Ayrıca *öğrenilmiş* eşleme (`conf_cls_ogr`): MODIS düşük 0–35, nominal 36–82, yüksek 83–100; `guven_ogrenilen_sinirlar` [35, 82] (tahmini), 40.368 Aqua–VIIRS çiftiyle (`guven_cift_sayisi`, ölçüldü), yıl dışarıda bırakmada c1 ∈ [34, 36], c2 ∈ [81, 82] (`guven_loyo_c1_aralik`, `guven_loyo_c2_aralik`, ölçüldü). Bu eşleme FIRMS'i geçemedi: doğru sınıf oranı 0,6457 (öğrenilmiş) / 0,6485 (FIRMS), Cohen kappa 0,1765 / 0,1918 (`guven_loyo_kappa_ogrenilen`, `guven_loyo_kappa_firms`, ölçüldü); Spearman 0,2138 (`guven_spearman`, ölçüldü). Arayüz varsayılanı ham FIRMS sınıfıdır. `dusuk_guven` etiketi status'a yazılmaz (`temizlik.dusuk_guven_etiketle = hayır`; `temizlik_status_dusuk_guven` 0, ölçüldü); yalnız bayrak.

**NRT ve arşiv:** NASA `type` alanı (belgelerdeki kullanım): 1 = volkan, 2 = statik kara kaynağı, 3 = deniz; `type=0` belgede yalnız "MODIS type=0 FRP medyanı" ve "normal" olarak geçer, açık tanımı belgede yok; alan arşivde bulunur. NRT noktalarında `type = -1`, yani NASA sınıf etiketi **yok** (`temizlik_yontemi.md` §1). NRT noktalarında NASA etiketi, 0,01° hücredeki arşiv komşularından miras alınarak telafi edilir (§2). Mevcut ay %100 NRT'dir (`takvim_mevcut_ay_nrt_payi_TR` 100 %, ölçüldü).

**Zaman (K11):** depolama UTC; "gün" `day_tr` = UTC+3 sabit, tüm yıllara (2016 öncesi kış UTC+2 etkisi 21:00–21:59Z için 88 satır; `bulgular.md` F1-05). Yıl kırpılmaz. Hiçbir nokta silinmez (K3), her nokta tam bir `status` etiketi alır.

Belgede yok / belirsiz: "SP" (Standard Processing) ürününün adı geçmez; ayrım yalnız `type=-1` (NRT) ile `type∈{0,1,2,3}` (arşiv) üzerinden anlatılır.

---

## 2. Temizlik (status sınıfları)

Yöntem **kural tabanlıdır**; makine öğrenmesi yok. Eşikler yıl dışarıda bırakma (LOYO) ile seçilir. Sonuçlar `points_status.parquet`; toplam 1.414.674 = temiz 827.043 + anız 217.179 + statik_nasa 328.379 + sanayi 27.012 + deniz 8.848 + kalıcı_belirsiz 6.208 + volkan 5 (`temizlik_status_*`, ölçüldü; `dusuk_guven` 0).

Bölme: **NASA etiketi** = NASA'nın kendi `type` alanı (volkan, deniz, statik_nasa) ve NRT'deki mirası. **Proje kuralı** = sanayi, kalıcı_belirsiz, yangın koruması, anız. Etiket rolleri aşağıda satır satır yazıldı.

| status | Kural (tam) | Kaynak | Sayı (anahtar, etiket) |
|---|---|---|---|
| `volkan` | `type = 1` | **NASA etiketi** | 5 (`temizlik_status_volkan`, ölçüldü) |
| `deniz` | `type = 3` | **NASA etiketi** | 8.848 (`temizlik_status_deniz`, ölçüldü) |
| `statik_nasa` | `type = 2` | **NASA etiketi** | 328.379 (`temizlik_status_statik_nasa`, ölçüldü) |
| NRT mirası | NRT (`type=-1`) noktasının 0,01° hücresindeki arşiv noktalarının en az `temizlik.nasa_miras_payi` = 0,5'i `type=2` ise `statik_nasa` (`status_neden = nrt_nasa_statik_mirasi`); type 1/3 için aynı miras kuralı | Proje kuralı (NASA etiketinden türetilmiş) | 12.940 (`temizlik_nrt_statik_mirasi`, ölçüldü) |
| `sanayi` | 0,01° hücre (`hucre_derece`), iki sensör birlikte, type 1/3 hariç. Hücre özellikleri: `ny` farklı yıl, `nd` farklı TR günü (tüm yıllar), `nmon` farklı takvim ayı (1–12, yıllar birleşik), `medm` aktif yıllarda yıl içi farklı ay sayısının medyanı, `gece` gece tespiti payı. **`ny ≥ Y` ve `nmon ≥ M` ve `nd ≥ N` ve `medm ≥ S`** (`status_neden = kural_sanayi`) | Proje kuralı | 27.012 (`temizlik_status_sanayi`, ölçüldü) |
| `kalici_belirsiz` | Sanayi kuralının `Y` ve `M` koşulunu sağlayıp `N` veya `S`'yi sağlamayan ve tespitlerinin en az `kalici_gece_payi` = 0,5'i gece olan hücre | Proje kuralı | 6.208 (`temizlik_status_kalici_belirsiz`, ölçüldü) |
| yangın koruması (istisna) | Kural-sanayi veya kalıcı-belirsiz noktası, aynı TR gününde (2k+1)² hücre komşuluğunda (`koruma_komsu_k` = 2 → 5×5 hücre, ~5 km) kalıcı **olmayan** hücrelerde en az `koruma_G` = 2 tespit varsa `temiz` kalır (`status_neden = yangin_korumasi`). NASA'nın `statik_nasa` etiketine koruma uygulanmaz | Proje kuralı | 1.748 (`temizlik_yangin_korumasi_nokta`, ölçüldü); G = 2 (`temizlik_koruma_G_veriden`, ölçüldü) |
| `dusuk_guven` | Etiket olarak yazılmaz; yalnız `status_neden` bayrağı (koordinatör kararı) | Proje kararı | 0 (`temizlik_status_dusuk_guven`, ölçüldü) |
| `aniz` | Olay düzeyinde (aşağıda) | Proje kuralı | 217.179 nokta / 169.115 olay (`temizlik_status_aniz`, `temizlik_olay_aniz_olay`, ölçüldü) |
| `temiz` | Yukarıdakilerin hiçbiri | – | 827.043 (`temizlik_status_temiz`, ölçüldü) |

**Sanayi eşik değerleri (config'te):** N = 40 gün, M = 8 takvim ayı, Y = 5 yıl, S = 4 ay/yıl (medyan); `hucre_derece` = 0,01°. Seçim: her yıl Y için hücre özellikleri yalnız Y dışındaki yıllardan kurulur; eşikler eğitim yıllarında NASA `type=2`'ye karşı F1'i en büyük yapan ızgara noktasıdır (N ∈ {5,10,20,40,80}, M ∈ {4,6,8,10,12}, Y ∈ {2,3,5,8}, S ∈ {1,2,3,4,6,8}); config değeri katların en sık seçtiği kombinasyondur: 20/27 kat = 0,7407 (`temizlik_sanayi_loyo_kat_kararliligi`, ölçüldü). *Not:* `temizlik_yontemi.md` yalnız eşik adlarını verir; sayısal N/M/Y/S `calisma_prensibi.md` §10 tablosundadır.

**Sanayi kuralının uyuşması (LOYO, NASA type=2'ye karşı; "uyuşma", doğruluk değil, çünkü type=2 bir maskedir):** kesinlik 0,9199 (`temizlik_sanayi_loyo_precision`), duyarlılık 0,9712 (`temizlik_sanayi_loyo_recall`) (ölçüldü). VIIRS döneminde 0,9240 / 0,9722; MODIS dönemi (2000–2011) kesinlik 0,2278, duyarlılık 0,5679 (`..._viirs_donemi`, `..._modis_donemi`, ölçüldü). MODIS döneminin düşüklüğü büyük ölçüde referansın seyrekliğinden: kuralın 'sanayi' dediği 1.477 MODIS noktasının %66,6'sı bilinen bir tesise ≤ `modis_donemi_tesis_km` = 3 km (`temizlik_modis_donemi_sanayi_tesis_payi`, ölçüldü; `bulgular.md` F2-09). NRT telafisi (hücre mirası ∪ sanayi kuralı; NASA etiketi gizlenen yılda): kesinlik 0,9136, duyarlılık 0,9806 (`temizlik_nrt_telafi_precision`, `_recall`, ölçüldü).

**Reddedilen tanım:** il bazlı Poisson-binom "rastlantı" modeli (`kalici_alfa` = 0,001) tarım ovalarında on binlerce noktayı işaretledi; bu yüzden status'a değil yalnız `status_neden = yillik_tekrar` bayrağına bağlı: status=temiz olup bayraklı 230.775 nokta (`temizlik_yillik_tekrar_bayrakli_temiz`, ölçüldü; alt sınır `kalici_min_yil` = 3). Statüye çevrilip çevrilmeyeceği koordinatör kararıdır (açık).

**Anız (iki aşama):**

1. *Nokta düzeyi aday (yalnız bayrak, `status_neden = aniz_adayi`):* FRP < F_sensör **ve** aynı gün 3×3 hücre komşuluğunda ≤ `aniz_kucuk_komsu` = 3 tespit. **F (MODIS ölçeği) = 15 MW** = MODIS arşiv `type=0` FRP medyanı (`temizlik_F_modis_medyan` 15,0 MW, ölçüldü). **VIIRS eşdeğeri = 4,4 MW** (`temizlik_F_viirs_esdeger` 4,4 MW, ölçüldü): sabit oranla değil **yüzdelik eşleştirmeyle** (K8); duyarlılık tablosunda F = 15 için yüzdelik 0,4993 (`calisma_prensibi.md` §9, F tablosu). Aday sayısı 247.112 (`temizlik_aniz_adayi_nokta`, ölçüldü).
2. *Nihai karar olay düzeyinde* (`olay_aniz.py`, kısmi etiket yok): **olay büyüklüğü ≤ `aniz_olay_max_tespit` = 3**, **`sure_saat` ≤ `aniz_olay_max_sure_saat` = 12**, **olaydaki tüm noktalarda FRP < F_sensör** (MODIS 15 MW, VIIRS 4,4 MW) ve **olayın TR başlangıç ayı, olayın bölgesinin "o yıl hariç" öğrenilmiş anız aylarında** → olayın tüm noktaları `status = aniz` (`status_neden += olay_aniz`).
   - *Büyüklük sayımı* (`aniz_olay_sayim`): `toplam` (n), `sensor_max` = max(n_modis, n_viirs), `n_mcell` = olaydaki tekil MODIS-ayak izi eşleştirme birimi. Seçilen **`n_mcell`** (VIIRS öncesi/sonrası anız olay payı farkı en küçük: 0,3803 ve 0,3546 `temizlik_pay_viirs_oncesi_n_mcell`, `temizlik_pay_viirs_sonrasi_n_mcell`, ölçüldü; `sensor_max` 0,3445, `toplam` 0,3436). Sabit "VIIRS eşdeğeri oranı" kullanılmadı (K8). Eşik duyarlılığı (olay sayısı, `n_mcell`): 1→154.841, 2→167.540, **3→169.115**, 5→169.464, 10→169.475 (`sensitivity.aniz_olay_max_tespit`, ölçüldü).
   - *Etkileşim:* nokta düzeyinde aday olup olayı da anız olan pay 0,7752 (`temizlik_aday_olayda_aniz_pay`, ölçüldü); kayıp nedenleri (çakışabilir): olay büyüdü 12.556, süre 30.533, FRP 46.568, ay 170 nokta (`temizlik_kayip_nedeni_n/_sure/_frp/_ay`, ölçüldü). Kümeleme–anız tutarsızlığı 0 (`temizlik_tutarsiz_nokta`).
   - *Ay takvimi:* 7 coğrafi bölge × ay profili, yıl içi payların yıllar arası ortalaması; **anız ayı = payı 1/12'yi aşan ay** (`aniz_ay_kurali = uniform_ustu`); her yıl için o yıl hariç öğrenilir (LOYO). Öğrenilen aylar (`sensitivity.aniz_aylari`, `uniform_ustu`): Akdeniz 6,8,9,10,11; Doğu Anadolu 7,8,9,10,11; Ege 6,9,10,11; Güneydoğu 6,7,9,10,11,12; Karadeniz 8,9,10,11; Marmara 9,10,11; İç Anadolu 8,9,10,11. Demo'nun tek ülke çapı takvimi Ağustos–Aralık [8–12] yalnız duyarlılık karşılaştırması içindir.
   - *LOYO ölçüleri:* küçük adayların o yıl hariç öğrenilen aylara düşme payı (kapsama) 0,7490, büyük tespitlerin aynı aylara düşme payı (taban) 0,8071, kaldıraç = kapsama/taban = **0,928** (`temizlik_aniz_loyo_kapsama/_taban/_kaldirac`, ölçüldü). **Dürüst bulgu:** kaldıraç ≈ 1 → "ay" tek başına küçük ateşi büyükten ayırmıyor; ayırıcı olan büyüklük/süre/FRP; ay şartı yalnız mevsim dışını eler.
   - *Bağımsız doğrulamalar:* (a) kaba ulusal hasat penceresi `temizlik.hasat_penceresi` = ay 6–10 (TMO, FAO GIEWS); öğrenilen ayların pencereye düşme payı 0,7419 (`temizlik_aniz_hasat_penceresi_payi`, **tahmini**; ulusal ve kaba). (b) ESA WorldCover 2021 (CC BY 4.0; 2.000 nokta/grup; ±3 piksel ≈ ±110 m penceresinde en sık sınıf): anız noktalarının ekili alan payı 0,7935 (`temizlik_wc_aniz_ekili_alan_pay`, `temizlik_aniz_arazi_ortusu`, ölçüldü); büyük temiz olay (`n_mcell ≥ 10`) grubunda ekili 0,503, ağaç 0,321 (`temizlik_wc_buyuk_temiz_*`); sanayi+kalıcı grubunda yapılaşmış 0,5595; statik_nasa grubunda (n=500) yapılaşmış 0,812. Saha/yanmış alan doğrulaması **yok** (doğrulanmadı).

**Referans doğrulama (C13; hepsi tahmini; küçük set):** FIRMS'ten bağımsız set: OSM'den sanayi tesisleri (28 → ayıklama sonrası 26) ve haberlerden bilinen yangınlar (9 → 8); S02, S21, Y02 ayıklandı, Y06 yarıçapı 15 → 7 km. Dengeli kesinlik = makro tesis yakalama / (makro tesis yakalama + makro yangın yanlış-işaret): `ref_precision` 0,9711 (tahmini), makro tesis yakalama `ref_recall` 0,4777, tesis düzeyi yakalama (≥%50 noktası kalıcı etiketli) `temizlik_ref_site_recall` 0,4783, yangın başına yanlış işaret `temizlik_ref_makro_yangin_fpr` 0,0142, yangın noktalarının kalıcı etiket ALMAMA payı `temizlik_ref_yangin_koruma` 0,9982 (hepsi tahmini). Nokta düzeyi kesinlik 0,9999 sınıf dengesizliği nedeniyle şişkin, sunumda kullanılmaz. Katkı: yalnız kural (NRT senaryosu) makro tesis yakalama 0,3829, yalnız NASA statik 0,2911 (`temizlik_ref_kural_makro_recall`, `temizlik_ref_nasa_makro_recall`, tahmini); bilinen yangınlarda kalıcı etiket alan noktaların tamamı NASA type=2'dir. Static Thermal Anomalies (STA) maskesi karşılaştırması yapılmadı: `temizlik_sta_maskesi_karsilastirma` **doğrulanmadı**.

---

## 3. Kümeleme (olay = yangın)

**Girdi:** `status ∈ {temiz, aniz}` noktalar = 1.044.222 (= 827.043 + 217.179). Temiz olmayan noktalar `event_id = -1` alır ve zincire **köprü olamaz**. Anız olay düzeyi etikettir, olay yapısını değiştirmez (döngü yok). **Çıktı:** 471.978 olay (`events_total`, ölçüldü).

**Bağlantı kuralı** (olay = bağ grafiğinin bağlı bileşeni, union-find; varsayılan **D = 1 km, `ayakizi_capraz`, `gecis` L = 3, Hmax = 72 sa**):

- **Uzay:** `d ≤ D` (dy = Δenlem·111, dx = Δboylam·111·cos(ortalama enlem), ±180° sarmalı; `km_derece` = 111) **veya** MODIS–VIIRS çiftinde VIIRS merkezi MODIS piksel dikdörtgeninin içinde: |dx| ≤ scan/2 + b ve |dy| ≤ track/2 + b, **b = 0,375 km** (`eslesme_tamponu_km`). Dikdörtgen kuzey–güney yönlü varsayılır; gerçek ~10° yörünge eğimi ihmal edilmiştir (**tahmini**).
- **Zaman (`gecis`):** |Δt| ≤ Hmax **ve** iki tespit arasında tamamen kalan *gözlenmiş* geçiş penceresi sayısı ≤ L. Karşılaştırma kuralı `sabit`: |Δt| ≤ H.
- **Geçiş pencereleri:** Türkiye'de günde 4 pencere: Terra gündüz (~06–09 UTC), Aqua+VIIRS gündüz (~09–12), Terra gece (~17–20), Aqua+VIIRS gece (~22–01). Aqua ve üç VIIRS aynı ~13:30 yörüngesinde olduğundan VIIRS yeni pencere eklemez. Pencere sınırı: yıl × uydu grubu için tespit saatlerinin 1. ve 99. yüzdeliği (`gecis_pencere_yuzdelik`; swath verisi yok, **tahmini**). Gruptan ≥ 1 uydu `coverage.observed = True` ise pencere "gözlenmiş" sayılır.
- **MODIS 1 km piksel ayak izi ile VIIRS noktası nasıl birleşir:** MODIS tespiti = merkezinde `scan` (doğu–batı) × `track` (kuzey–güney) km dikdörtgen; VIIRS noktası bu dikdörtgen + b içine düşerse (ve zaman koşulu sağlanırsa) aynı yangına bağlanır. `ayakizi_capraz` yalnız **MODIS–VIIRS çiftlerini** ayak iziyle bağlar; `ayakizi_tum` MODIS–MODIS örtüşmesini de ekler (varsayılan değil; 2000–2011 olay sayısını değiştirir, dönemler arası tutarlılığı bozar).

**Ayak izi modu karşılaştırması** (çakışma dönemi, H = 24, D = 1; ölçüldü): `sabit` 487.863 olay, MODIS olaylarının VIIRS'te görülme oranı 0,3547 (`events_modis_seen_by_viirs_share_sabit`); `ayakizi_capraz` 481.008, 0,3767; `ayakizi_tum` 446.976, 0,4242. Varsayılan kuralla oran 0,3825 (`events_modis_seen_by_viirs_share`). "%37 şüphesi": kenar pikselde 1 km kuralı eşleşmeyi gerçekten kaçırıyor (scan ≥ 1,6 km üst çeyrek: ≤ 1 km 0,491, ayak izi içinde 0,657; merkez piksel 0,547 / 0,580 — ayak izi satırları **tahmini**), ama asıl neden eşleştirme değil: çakışmadaki yalnız-MODIS olayların ~%64'ü (57.543'ün 36.679'u) yalnız Terra'dan (10:30 vs VIIRS 13:30); Aqua tespitlerinde bile 8 km içinde VIIRS yok oranı ~%28 (0,718 var), ±60 dk içinde 1 km'de VIIRS payı 0,5315 (`aqua_nearest_viirs_within_1km_share`, ölçüldü), ayak izi içinde 0,6017 (`aqua_viirs_in_footprint_share`, tahmini). Sonuç: "her MODIS tespitinin VIIRS karşılığı vardır" varsayımı yapılmamalı.

**Ortak mı ayrı mı?** MODIS ve VIIRS **birlikte** kümelenir. Çakışma döneminde ortak: 380.975 olay (`events_joint_overlap`); ayrı kümelense 440.176 (`events_separate_overlap`) → **59.201 çifte sayım önlenir** (`events_double_count_avoided`) (hepsi ölçüldü). Ayrıca anız tarafında: ayrı kümelemeye göre ortak kümelemede 30.196 (%9,4) nokta anız sayımından düşer (320.995 → 290.799; `aniz_points_separate`, `aniz_points_joint`, **tahmini**; MODIS tarafı −%18,5), bu yüzden anız büyüklüğü `n_mcell` ile sayılır.

**Üçlü sınıf** (`match_class`; çakışma = olayın başladığı TR gününde iki sensör ailesinden en az birer uydunun `observed=True` olması): `ortak` 35.651; `yalniz_modis` 57.543; `yalniz_viirs` 287.781; `tek_sensor_donemi` (çakışma dışı, sınıf anlamsız) 91.003; toplam 471.978 (`events_match_*`, ölçüldü).

**MODIS-hücre (`mcell`) ataması** (`points_mcell.parquet`, eşleştirme birimi; harmonizasyon ve anız sayımı kullanır): ayak izi = MODIS merkezinde scan × track dikdörtgen + her yöne 0,375 km; zaman |Δt| ≤ `mcell_zaman_penceresi_saat` = 4 sa (Terra–VIIRS 2–3,6 sa farkı dahil). Bir VIIRS noktası birden çok ize düşerse sırayla: (1) eşzamanlı (|Δt| ≤ kalibrasyon penceresi) iz, (2) en küçük normalize uzaklık d = max(|dx|/(scan/2+tampon), |dy|/(track/2+tampon)), (3) en küçük |Δt|, (4) en küçük alan. Nokta **tek** hücreye gider, FRP bölünmez. İze düşmeyen VIIRS (yalnız VIIRS) → yedek sabit 0,01° ızgara hücresi. Nokta sayıları: 174.203 VIIRS noktası MODIS izinde (1.154.967'den), 81.418 noktası çoklu ize düşüp tek hücreye indirildi, iz başına 3,349 VIIRS noktası; sabit ızgara aynı izi 1,764 hücreye bölerdi, bölünen iz oranı 0,4655 (`mcell_*`, ölçüldü).

**Gecis kuralının etkisi** (D = 1, `ayakizi_capraz`; ölçüldü): sabit H = 24 → 481.008 olay (süre p99 25,4 sa); H = 27 → 470.117; `gecis` L = 3, Hmax = 72 → **471.978** (p99 37,7 sa); L = 2 → 499.277; L = 4 → 468.214; Hmax = 48/120 → 472.021/471.978. Sabit 24 sa'in gizli hatası: gündüz geçiş saati günden güne ~3 sa kayar, her gün görülen yangın 25 saatlik boşlukla ikiye bölünür (16.434 olay → 7.401 olayda birleşti). Kesinti bilgisinin (129 uydu-gün) katkısı küçük: 472.098 → 471.978. Sınırlama (**doğrulanmadı**): MODIS'in bir pencerede yangını görmemesi sönme kanıtı değildir; gece pencereleri zayıf kanıt.

**Duyarlılık** (`sensitivity.D/.H/.L`, ölçüldü): D = 0,5/1/2/3 km → 541.338 / 471.978 / 383.640 / 341.799 olay (0,5→2 km: −%29). H = 6/12/24/48 → 525.841 / 512.109 / 481.008 / 451.483 (sabit kuralla). L = 1/2/3/4/6 → 506.842 / 499.277 / 471.978 / 468.214 / 460.759. "Olay sayısı" daima kuralıyla birlikte verilmelidir.

**Zincirleme riski:** 312.936 tek tespitli olay, en büyük olay 6.740 tespit (Manavgat 2021-07-28, gerçek mega yangın). Sanayi zinciri kapandı (temiz girdi: karışık olay 0; >7 gün olay 2.776 → 103). **Açık:** statik nokta içermeyen, kapsamı ≥ 10 km olan 152 olaydan 34'ü "tarım zinciri" tanımında (ortalama FRP < F ve TR başlangıç ayı Temmuz–Ekim, `kumeleme.tarim_zinciri`): 9.484 tespit (%0,9), Osmaniye 14, Adana 5, Diyarbakır 5; **tahmini**, sahada doğrulanmadı; öneri: arayüzde "zincir şüphesi" bayrağı. Tek F (MODIS ölçeği) karışık sensörlü olay ortalamasına uygulanıyor (sınırlama).

**Doğruluk (C03):** 12 örneklem, 21.509 nokta, 7 kural çeşidi, her n² çift bağımsız yüklemle; 88 karşılaştırmada 0 fark; mutasyon testi 12/12 yakalandı (`c03_*`, ölçüldü). Çalışma süresi 3,32 s, bellek 676 MB (`clustering_runtime_s`, `clustering_rss_mb`, ölçüldü).

---

## 4. Fizik

**FRP (Fire Radiative Power):** yangının yaydığı ışınım gücü, **MW** cinsinden (`calisma_prensibi.md` sözlük). Belgelerde kullanımı: (a) anız eşiği (FRP < F, MODIS 15 MW; VIIRS 4,4 MW); (b) MODIS-hücre içinde VIIRS noktalarının **FRP toplamı** (ΣFRP; FRP bölünmez, çift sayılmaz); (c) MODIS etkin tespit sınırı FRP50 (aşağıda); (d) yöntem (ii)'nin büyüklük sınıfı `frp_sinif_sinirlari_mw` = [10, 50] MW (küçük < 10, orta 10–50, büyük ≥ 50; hücre toplam FRP veya MODIS tespit FRP); (e) enerji serisi (`frp_modis_mw`, `frp_viirs_uydu_basina_mw`).

**FRP50 (MODIS etkin tespit sınırı)** = P(Aqua hücreyi görür | log10 ΣFRP) lojistik regresyonunda 0,5 noktası; hücre = aynı yörünge geçişinde (`gecis_ayirma_dk` = 45 dk) `hucre_baglanti_km` = 1 km ile zincirlenen VIIRS noktaları; yalnız Aqua ile eşzamanlı geçiş × bölge kullanılır. Genel **64,88 MW** (`modis_frp50_genel_mw`), gündüz 73,98 MW (`modis_frp50_gunduz_mw`), gece 20,54 MW (`modis_frp50_gece_mw`) (tahmini). Bu "etkin" sınırdır (tarama açısı, ≤ 60 dk zaman farkı, bulut kayması dahil); MODIS'in fiziksel algılama sınırından büyüktür. Gece düşük (soğuk arka plan, yüksek kontrast: "fiziksel olarak beklenen yönde"). Bölgeye göre: Karadeniz 16,6; Ege 23,0; Doğu Anadolu 26,1; Marmara 31,3; İç Anadolu 67,5; Akdeniz 61,3; Güneydoğu 101,9 MW (`harmonizasyon_yontemi.md` §9; tahmini).

**Piksel büyümesi (belgelerdeki sayılar):** MODIS nadir piksel ≈ **1 km**, tarama kenarında **4,8 km**'ye kadar (`kumeleme_yontemi.md` §1, `arayuz_yontemi.md`; harmonizasyon belgesi "kenara doğru dikdörtgen büyür (4,8 km'ye kadar)"). Üst-çeyrek kenar piksel tanımı: scan ≥ 1,6 km. VIIRS piksel **375 m** (`calisma_prensibi.md` §10: 375 m/2 ≈ 0,19 km). Kümeleme ve eşleştirme `scan × track` değerlerini nokta başına tablodan okur (`scan`, `track` sütunları). **Belgede yok:** scan/track ve ağırlık işlevinin tarama açısına göre analitik formülü; kenarda track boyutu; VIIRS kenar büyümesi (VIIRS için belgede yalnız "375 m" yazar).

**Neden VIIRS daha çok küçük yangın görür (belgelerdeki gerekçe):** (1) 375 m piksel MODIS 1 km pikselinden çok daha ince: bir MODIS pikseline ortalama 3,349 VIIRS noktası düşer (`mcell_iz_basina_viirs`, ölçüldü); (2) ham sıçrama VIIRS'in "daha çok gördüğünü" gösterir: ham MODIS→MODIS+VIIRS +%143,13, MODIS→yalnız VIIRS +%88,03 (`jump_raw_pct`, `jump_raw_viirs_only_pct`, ölçüldü); (3) MODIS'in görme eşiği veriden **FRP50 = 64,88 MW** (hücre toplamı); küçük ateşler VIIRS'te görülür, MODIS'te yalnız hücre toplamı eşiği aşınca görülür; MODIS'e göre yalnız-VIIRS olay 287.781 (`events_match_yalniz_viirs`, ölçüldü). Aynı gerekçe belgelerde "daha hassas termometre" benzetmesiyle verilir; fiziksel türetme belgelerde yoktur.

### Literatürden (belgede yok)

Belgelerde türetimi veya kaynağı olmayan, atıf gerektirecek konular:

- FRP'nin fiziksel tanımı: MIR kanalı radyans farkından FRP (Wooster ve ark. yaklaşımı), MODIS (MOD14/MYD14) ve VIIRS 375 m (VNP14IMG) algoritmaları ve tespit eşikleri.
- MODIS piksel boyutunun tarama açısıyla büyümesi: nadir 1 × 1 km, kenarda yaklaşık 2 km (track) × 4,8 km (scan) ve "bow-tie" etkisi; VIIRS 375 m piksel büyümesi (nadir 375 m, kenarda yaklaşık 800 m'ye kadar). Belgelerde yalnız "1 km → 4,8 km (MODIS)" vardır.
- FIRMS güven alanı: MODIS `confidence` 0–100 (düşük/nominal/yüksek eşikleri 30 ve 80); VIIRS l/n/h nasıl üretilir (bağlam ve parlaklık sıcaklığı eşikleri).
- FIRMS `type` alanı (0, 1, 2, 3) tanımı ve Static Thermal Anomalies (STA) maskesi (belgede yalnız "deneysel katman" denir).
- Terra (~10:30) ve Aqua/VIIRS (~13:30) yerel geçiş saatleri; Aqua'nın yörünge kayması (yakıt tükenmesi, serbest sürüklenme); Terra/Aqua ömrü sonu (belge: Terra 2027, Aqua ~2027; Terra'nın 2026 durumu doğrulanmadı, `calisma_prensibi.md` §11 madde 16).
- MODIS ve VIIRS tespit ihtimalinin FRP ile ilişkisi (lojistik eğri, kısa süreli/küçük yangınlarda kaçırma).
- Anız yakma takvimi ve hasat zamanları (TMO alım başlangıcı, FAO GIEWS; belgede yalnız `hasat_penceresi` config açıklamasında).
- ESA WorldCover v200 2021 sınıflandırma doğruluğu (belgede "ölçülmedi").
- LOYO çapraz doğrulama, MAPE/WAPE, sağlam z-skoru (MAD, 1,4826), yıl bootstrap'ı: yöntem atıfları.

---

## 5. Harmonizasyon (VIIRS → MODIS-eşdeğer)

**İki çıktı (U-04):** (a) **MODIS-eşdeğer seri**: 2012 öncesi gerçek MODIS (Terra+Aqua), 2012 sonrası VIIRS'ten türetilmiş MODIS-eşdeğer tespit/olay sayısı (tamsayı + %95 bant); (b) ham VIIRS serisi ve nokta düzeyinde `match_nokta` (ortak/yalnız MODIS/yalnız VIIRS). Birim: tespit (ay × 7 bölge) ve olay (ay × il); küme: `temiz` (varsayılan, anız hariç) ve `temiz_aniz`. Seviye: **bölge × mevsim (× büyüklük)**, ay × bölge; mevsimler Ara–Şub kış, Mar–May ilkbahar, Haz–Ağu yaz, Eyl–Kas sonbahar; 7 bölge = geleneksel coğrafi bölgeler (`ortak.BOLGE7`).

**Model (belgelerin verdiği tam biçim).** Belgelerde cebirsel bir formül tek satırda verilmemiştir; yöntem sözel tanımlıdır, aşağıdaki biçim bu tanımın aktarımıdır. Hedef: Terra+Aqua tespiti (ay × bölge, `status = temiz`).

- **Efor (uydu sayısı) normalizasyonu** (`seri.efor_normalize`): her gün VIIRS toplamı, o gün `coverage.observed = True` olan VIIRS uydu sayısına bölünür; gözlemsiz günler ay içi ortalamayla ölçeklenir. Gerekçe: 2018'de 2., 2023'te 3. VIIRS uydusu eklendi.
- **(i0)** tek sabit oran, efor yok (yalnız kıyas; B-04 tuzağı). **(i)** tek sabit oran, eforlu. **(ii) ana yöntem:** bölge × mevsim × FRP büyüklük sınıfı ([10, 50] MW) oranı, eforlu; az örnekli tabakada (`min_ornek` = 200 hücre) mevsim × büyüklüğe, sonra gündüz/gece'ye düşülür. **(iii)** FRP eşik eğrisi g(ΣFRP) = hücre başına beklenen Aqua tespiti (12 log-FRP kutusu; bölge × mevsim × gündüz/gece, hiyerarşik) + yalnız-MODIS payı f_u (uydu × gündüz/gece × mevsim) + Terra payı k_TA (bölge × mevsim × gündüz/gece), eforlu.
- **Belgede yok:** (ii)'nin oranının tam cebirsel ifadesi (ör. "MODIS tespiti / eforlu VIIRS tespiti") ve kodda hangi sütunların bölündüğü; yalnız "oran" ve "eforlu" denir. Olay birimi: gerçek = `n_modis > 0` olaylar (ortak + yalnız MODIS); VIIRS özelliği = olaydaki VIIRS FRP toplamının sınıfı; (ii) = bölge × mevsim × VIIRS FRP sınıfı oranı + yalnız-MODIS olay payı (bölge × mevsim); olay eşdeğeri tespit eşdeğerini aşamaz (aşan hücreler kırpılır; 98 + 6 hücre temiz, 93 + 6 temiz_aniz).
- **Kalibrasyon / test dönemi:** LOYO test yılları **2012–2025** (`loyo_test_yillari`, 14 yıl): her test yılı için öğrenme = 2012–2025 ∖ o yıl. 2026 kısmi + NRT olduğundan testte değil, "düşük güven". Eski dönem 2000–Temmuz 2002 (yalnız Terra): nokta değer **düzeltilmez**, `bayrak = eski_donem_yalniz_terra`, üst bant 2003–2011 ülke × mevsim Aqua/Terra oranının %97,5'iyle genişletilir; bu yıllar sonrakilerle doğrudan karşılaştırılamaz (yaklaşık yarı efor).

**Yöntem yarışı** (LOYO 2012–2025; ölçüldü): 

| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Yıllık sapma (bias) % | Yıllık %95 hata aralığı (tahmini) | Anahtar |
|---|---|---|---|---|---|---|
| (i0) | 52,68 | 42,12 | −1,7204 | 5,03 | [−46,83, 86,91] | `harm_i0_*` |
| (i) | 30,64 | 4,83 | 0,9675 | 0,15 | [−7,81, 9,46] | `harm_i_*` |
| **(ii)** | **30,63** | **8,33** | **0,8716** | **0,55** | **[−23,49, 9,51]** | `harm_ii_*`; `loyo_mape` 8,33, `loyo_r2` 0,8716, `loyo_bias` 0,55 (ölçüldü), `loyo_ci95` (tahmini) |
| (iii) | 31,91 | 10,91 | 0,7644 | 3,76 | [−13,0, 31,69] | `harm_iii_*` |

Seçim ölçütü: en düşük ay × bölge WAPE (uygulama birimi). **Dürüst okuma:** (ii) ile (i) ay × bölgede **ayırt edilemez** (fark −0,01 yp, `harm_ii_eksi_i_wape`; yıl bootstrap'ı %95 [−2,97, 4,26] yp, `harm_ii_eksi_i_wape_ci95`, tahmini); yıllıkta (i) daha iyi; asıl kazanç efor normalizasyonudur. (ii) "üstünlük iddiası" olmaksızın uygulama birimi nedeniyle (koordinatör kararı, F2-03) ana yöntem kaldı. Ölçütün sonuçlardan önce yazıldığı git kaydı olmadığı için **doğrulanamaz**; kazananın hatası seçim etkisiyle hafif iyimser olabilir.

**Belirsizlik bandı:** LOYO artıklarının log((gerçek+1)/(tahmin+1)) değerinin %2,5–%97,5 yüzdelikleri; tahmin büyüklüğüne göre 3 kutu; ay × bölge ve ay × ülke ayrı. Kapsama "dürüst": her yılın bandı diğer yılların artıklarından kurulup o yılda sınanır. Aylık ülke toplamı bandı **[−59,57, +74,99] %** (`equiv_overlap_band`, tahmini); kapsama ay × bölge 0,9557, ay × ülke 0,9226 (`equiv_band_kapsama_ay_bolge`, `equiv_band_kapsama_ay_tr`, ölçüldü). Çakışma toplam sapması −%0,52 (`equiv_overlap_bias`, tahmini). Olay biriminde: yıllık MAPE 7,51, R² 0,8443, ay × bölge WAPE 32,8, ay × il WAPE 46,27 (`olay_temiz_*`, ölçüldü); il düzeyinde bant yalnız il × ay artıklarından, il düzeyi eşdeğer seri ayrıca doğrulanmadı.

**Sıçrama testi (C10):** sıçrama = (2012–2014 ortalaması) / (2009–2011 ortalaması) − 1 (`sicrama_pencere_yil` = 3). 2012 sonrası harmonize değerler LOYO tahminleridir. Sonuçlar (tespit, temiz): ham MODIS→MODIS+VIIRS **+143,13 %** (`jump_raw_pct`, ölçüldü); ham yalnız VIIRS +88,03 %; harmonize **−41,35 %** (`jump_harm_pct`, tahmini); aynı pencerede gerçek MODIS **−44,9 %** (`jump_modis_gercek_pct`, ölçüldü); harmonizasyonun eklediği 3,55 yp (`jump_harm_eksi_modis_pct`, `jump_resid_pct`, tahmini). Doğal değişim aralığı: MODIS serisinde geçiş dışı 17 adet 3+3 yıllık pencerenin %2,5–%97,5 yüzdeliği **[−39,3, +92,61] %** (`jump_null_ci95`, tahmini); harmonize sıçrama bu aralıkta **değil** (`jump_harm_dogal_aralikta` = False; çünkü −41,35 < −39,3), gerçek MODIS (−44,9) de bu aralığın dışında. Uydu eklenişleri (efor etkisi): N20 2018 (3+3): ham VIIRS +24,34 %, eforlu −37,31 %, gerçek MODIS −41,59 %; N21 2023 (2+2): ham +110,19 %, eforlu +44,29 %, gerçek MODIS +31,01 % (`jump_n20_2018_*`, `jump_n21_2023_*`, ölçüldü).

**Ölçüt değişikliği (post-hoc; `bulgular.md` F2-07):** Eski C10 ölçütü "harmonize sıçrama doğal değişim aralığında olmalı" idi; sonuç görüldükten sonra, gerçek MODIS de aynı aralığın dışında kaldığı için (kusursuz bir harmonizasyon da reddedilirdi), **ana ölçüt koordinatör kararıyla** şuna çevrildi: artık sıçrama `jump_resid_pct` = harmonize sıçrama − aynı penceredeki gerçek MODIS değişimi (`jump_modis_real_pct`) yıllık LOYO %95 hata aralığı `loyo_ci95` içinde olmalı. Değer 3,55 yp, aralık [−23,49, +9,51] → sağlanıyor. Denetçi notları: değişiklik post-hoc'tur; yeni ölçüt büyük ölçüde C09'un tekrarıdır (3 yıllık ortalama yıllık %95 aralığıyla kıyaslanıyor, gevşek); ancak aynı tanımla 2013–2023 tüm 3+3 pencerelerin artık dağılımı [−10,43, +4,62] ve 2012 değeri (3,55) bu aralıkta ("sonuç sağlam", denetçi). Önerilen ifade: "sıçrama kayboldu" değil, "harmonize seri 2012'deki gerçek MODIS düşüşünü 3,6 puan farkla izliyor"; ham +143 % sensör eklenmesinden. `audit/degisim_gunlugu.md` ilk-teslim sayılarını taşıyor (ham +116,2, harmonize −49,6, MODIS −51,5, aralık [−40,2, 94,0]); güncel değerler yukarıdaki gibidir (not eklendi). *Not:* `degisim_gunlugu.md` bu klasörde okunmadı; sayılar `bulgular.md` F2-07'den.

**Varyantlar** (tahmini jump, ölçüldü hata; `<birim>_<küme>_*`): tespit/temiz_aniz artık 3,12 yp; olay/temiz −0,78; olay/temiz_aniz 0,36.

**2026 rejimi (düşük güven):** Aqua gündüz geçiş medyanı 10,70 UTC (2015, `aqua_gunduz_gecis_utc_2015`) → 11,92 (2025) → **12,65 (2026)**; Terra 8,55 → 7,33. Aqua–VIIRS |Δt| ≤ 60 dk (`kalibrasyon_zaman_penceresi_dk`) eşzamanlı çift payı 0,839 (2015) → 0,487 (2025) → **0,182 (2026)** (`aqua_viirs_esz_cift_payi_*`, ölçüldü). 2026 eşdeğer bandı gerçek MODIS'i ayların 0,545'inde kapsıyor (`harm_2026_bant_kapsama`, ölçüldü; LOYO dönemi 0,9226). `bayrak = kismi_yil_nrt;aqua_yorunge_kaymasi`. Kayma modellenmedi; "kaymasız" kalibrasyon varyantı (2012–2023) ölçülmedi (doğrulanmadı). MODIS sonrası serinin bağımsız doğrulaması yok.

---

## 6. Takvim (yıl × ay aktivite)

**Zaman:** ay/yıl `day_tr` (UTC+3) ile; yıl kırpılmaz. **Veri:** il × gün defteri + `coverage` (gözlem yapan/işleyen uydu).

**Aylık matris:** satır = yıl, sütun = ay (89 birim: TR + 7 bölge + 81 il, `takvim_birim_sayisi` ölçüldü; il toplamı = TR). Varsayılan seri `olay_esdeger` (MODIS-eşdeğer olay; bant `[alt, üst]` taşır), alternatifler `olay`, `modis_temiz`, `modis_ham`, `modis_esdeger`, `viirs_*_ub`.

**Kesinti düzeltmesi (C06):** ay değeri = `Σ sayım(w>0) / Σ w × ay_uzunluğu`, w = gözlem yapan uydu / işleyen uydu. Hücre **BOŞ** (sıfır yazılmaz): işleyen gün < ay uzunluğu (sensör başlangıcı/bitişi, kısmi ay, veri sonu: 2026-11 gibi) veya kesinti payı > `takvim.kesinti_pay_max` = 0,5; sensör hiç işlemiyorsa (VIIRS < 2012) NaN. TR MODIS'te kesinti düzeltmesi uygulanan 12 ay hücresi, 1 hücre kısmi/kesinti nedeniyle boş (`takvim_kesintili_ay_hucresi`, `takvim_bos_hucre_kismi_ay`, ölçüldü).

**Gözlenen / gözlenmeyen gün:** `observed` bir **çıkarımdır**, NASA geçiş listesi değil (**tahmini**). Kural: bir uydu Türkiye'de ardışık en az G = 3 gün sıfır tespit verir ve aynı günlerde aynı sensör ailesindeki kardeş uydular toplamda ≥ K = 50 tespit verirse aday kesinti (aksi halde sıfır = yangınsızlık). Sonuç 129 uydu-gün (`kapsam_kesinti_uydu_gunu`, tahmini); SNPP 2022-07-26…08-11'de 17 günün 15'i yakalandı. Arayüzde "gözlem yok" ayrı renkte.

**Normal yıl / medyan profil:** tam yıl, sensör bileşimi referansla aynı (MODIS Terra+Aqua → 2003–2025 = 23 yıl; 2000–2002 hariç), geçiş yılları (2012, 2018, 2023) ve 2026 hariç (VIIRS ve olay serileri için). Profil: ay başına medyan, Q1, Q3, min, maks; n < 2 → medyan boş; n < `min_yil_medyan` = 5 → `az_yil`. Eşdeğer seri geçiş yıllarında dahildir ama `sensor_gecis_yili` uyarısı ve bant taşır. Olay serilerinde sensör bileşimi değiştiğinden **ay payı medyanı** kullanılır.

**Sıralama / top-3 / "ayırt edilemez" (≈):** ölçüt = ay medyanı; en yoğun 3 ay (`top_n` = 3). **Ayırt edilemez:** top-3 içinde komşu iki ayın medyanı arasındaki göreli fark < `ayirt_edilemez_tol` = 0,1 → "ayırt edilemez" uyarısı; ek olarak yıl bootstrap'ı top-3 olasılığı (B = `bootstrap_B` = 300, tohum 20260101). Arayüz bunu "≈" ile gösterir. Sonuçlar (TR, ay no): `modis_ham` [6, 9, 10] (ölçüldü); `modis_temiz` [6, 9, 8] (ölçüldü); `modis_esdeger` [8, 9, 6] (tahmini); `viirs_temiz_ub` [8, 9, 10]; `olay` [9, 8, 10] (tahmini); hepsinde ayırt edilemez bayrağı = 1. Ağustos–Eylül medyanları istatistiksel olarak ayırt edilemez. Temizliğin etkisi: ham ve temiz top-3 il düzeyinde %79 oranında değişir (`takvim_ham_temiz_top3_degisen_il_payi`, tahmini).

**Anomali:** log1p ölçeğinde sağlam z = (x − medyan) / max(1,4826·MAD, `olcek_taban` = 0,05); normal = normal yıllar, **test yılı hariç** (LOYO); olay serilerinde yalnız aynı sensör bileşimli yıllar (2024–2026 için yeterli yıl yok → `yetersiz_veri`); işaret eşiği **|z| ≥ `z_esik` = 2**; pencere aynı takvim ayı (serbest aralıkta aynı takvim günleri, en az `pencere_min_gun` = 15 gün genişletme). Eşdeğer seride bant alt/üst için z; işaret bantta değişirse `belirsiz_bant`: anomali işaretlerinin %33,53'ü belirsiz banda düşer (`takvim_anomali_belirsiz_bant_payi_esdeger`, tahmini); işaretli hücre payı %8,96 (`takvim_anomali_isaret_orani_esdeger`, tahmini). Yüzde gösterimi = oran (örn. "son tam ay normalin %170'i" = x / ilgili ay medyanı).

**"Son tam ay" ve mevcut ay (U-16):** son tam ay = 2026-10 (veri sonu 2026-11-12). TR `modis_temiz` oranı 507/579 = **0,876** (`takvim_son_tam_ay_oran_modis_temiz_TR`, ölçüldü); VIIRS uydu başına 0,944 (tahmini); `modis_esdeger` oranı 903/532 = **1,697** (`takvim_son_tam_ay_oran_modis_esdeger_TR`, tahmini), `olay_esdeger` 1,85 (tahmini). Eşdeğer oran, iki ölçülmüş orandan (MODIS temiz, VIIRS uydu başına) `esdeger_sapma_esigi` = 0,25 göreli farktan fazla sapıyorsa **güvenilmez** sayılır ve birincil gösterim ölçülmüş seriye (`modis_temiz`) düşer (`takvim_son_tam_ay_guvenilmez_modis_esdeger_TR` = 1, doğrulanmadı). Mevcut (kısmi) ay: ayın ilk D günü (12 gün, `takvim_mevcut_ay_kismi_gun_TR`, ölçüldü) geçmiş yılların AYNI ilk D günüyle; MODIS oranı 0,127 kat, VIIRS 0,243 kat (tahmini); NRT payı %100 (ölçüldü); `ayrisma_oran_esigi` = 1,5 kat, `dusuk_oran_esigi` = 0,5 kat; MODIS'e özgü ek düşüşün nedeni (sensör ömrü sonu/NRT/yörünge kayması) **doğrulanmadı**. Kısmi ay `kismi_ay_ilk_D_gun` uyarısı taşır.

**Serbest aralık:** gözlenen gün ağırlığı / istenen gün < `min_kapsam_orani` = 0,5 ise değer boş.

**Etiket (K5):** sayımlar ölçüldü; eşdeğer, uydu başına, anomali ve sıralama kararlılığı tahmini. VIIRS uydu-başına normalleştirme doğrusal varsayımdır; il düzeyinde eşdeğer seri yok.

**Arayüz kuralları** (`arayuz_yontemi.md`): varsayılan seri MODIS-eşdeğer (`olay_esdeger`); `#sciModeBtn` ile ham olaya geçiş; ekranda sabit sayı yok (C14); TR/EN anahtar simetrisi (279 anahtar; `bulgular.md` F4 bölümünde eski ölçüm 224 yazılıdır, F3'te 279; belgeler arası fark kronolojik); çevrimdışı çalışır (C21).

---

## 7. Bilinen sınırlar ve açık bulgular

**Açık denetim bulguları (düşük):** F2-10 sabit yıl/saat sabitleri (`seri.py:207` `between(2003, 2025)`, K9/K11'e aykırı, hesabı bozmaz); F2-11 `harmonizasyon_yontemi.md` §9 tablolarında EN ondalık ("30.63"); F2-12 `check_all.py` C09/C23 zayıf (`fark_aciklamasi`, `loyo_folds` yok); F5-03 türetilmiş sonucun etiketi ("jump_harm_dogal_aralikta" ölçüldü yazıyor, girdisi tahmini; metrics.json'da şu an `tahmini`); F4-04 kısmi (kalıntılar F5-04'te kapandı). Açık yüksek 0, açık orta 0.

**Yöntem sınırları (belgeler):**
1. **2026 eşdeğer seri güvenilmez** (doğrulanmadı): Aqua yörünge kayması, çift payı 0,182, bant kapsama 0,545; "kaymasız" varyant ölçülmedi.
2. **MODIS sonrası dönem** (Terra 2027, Aqua ~2027) bağımsız doğrulanamaz; aylık ülke hata bandı geniştir (−59,57…+74,99 %).
3. **Sıçrama "çözüldü" iddiası yok:** harmonize sıçrama doğal aralığın dışında; ölçüt post-hoc değişti.
4. **(ii) ≈ (i) ay × bölgede** (ayırt edilemez); kazanan hatası iyimser olabilir; ölçüt önceden sabitlendi iddiası doğrulanamaz.
5. **Anız yer-doğrulaması yok:** yalnız WorldCover (%79,35 ekili) ve kaba hasat penceresi (%74,2). Ay tek başına ayırmaz (kaldıraç 0,928). Anız etiketi nokta veya olay "tahmini" kural çıktısıdır (`temizlik_status_aniz` metrics'te ölçüldü etiketli; bkz. aşağıdaki tutarsızlıklar).
6. **Sanayi kuralı uyuşması MODIS döneminde zayıf** (0,2278; referans seyrek); `type=2` maske, yer gerçeği değil. Referans seti küçük (26 tesis, 8 yangın); tesis yakalama 0,4777 (termik santraller kaçıyor); nokta düzeyi kesinlik sunumda kullanılmaz.
7. **STA maskesi karşılaştırılmadı**; NRT deniz telafisi zayıf ve doğrulanmadı.
8. **Gözlem kapsamı çıkarım**: swath/geçiş listesi yok, 129 uydu-gün tahmini; geçiş pencereleri yüzdeliklerden türetildi; kesintinin (küçük yangını görmeme) sönme kanıtı olmaması.
9. **Tarım zinciri vakaları (34 olay)** açık; zincirleme riski kalan.
10. **Güven eşlemesi zayıf ilişkili** (Spearman 0,2138); öğrenilmiş eşleme FIRMS'i geçemedi; varsayılan ham FIRMS.
11. **İl düzeyinde eşdeğer seri doğrulanmadı** (ay × il WAPE 46,27 % olay biriminde); yalnız ülke/bölge LOYO.
12. **Mevcut ay** kısmi (12 gün) ve %100 NRT; oran 0,127/0,243; MODIS'e özgü düşüş nedeni doğrulanmadı.
13. **Zaman:** sabit UTC+3 (2016 öncesi kış 88 satır etkisi); Türkiye kutusu (bbox) yurt dışı 0, kıyı 14.042 nokta (il poligonu dışı ≤ 5 km tampon).
14. **WorldCover** tek yıl (2021), örneklem; kendi hatası ölçülmedi; konum belirsizliği (VIIRS 375 m, MODIS ~1 km) pencereden büyük olabilir.
15. **Ekran okuyucu testi yapılmadı** (doğrulanmadı); FIRMS API çalıştırılmadı (veri elle indirilmiş arşiv).
16. **Kümeleme:** ayak izi dikdörtgeni kuzey–güney varsayımı (~10° eğim ihmal); olay yöntemi (iii) denenmedi; tek F, karışık sensörlü olaya uygulanıyor.
17. Hotspot sayısı yangın sayısı değildir (1.414.674 nokta → 471.978 olay); risk tahmini yoktur.

**Belgeler arası farklar / belirsizlikler (dosya adlarıyla):**
- **Tampon değeri:** `kumeleme_yontemi.md` b = 0,375 km kullanır; `harmonizasyon_yontemi.md` aynı değeri "yarım piksel" diye adlandırır; `esikler.json` açıklaması (`calisma_prensibi.md` §10) yarım piksel ≈ 0,19 km, 0,375 km'nin "tam piksel tampon olarak başlangıç" olduğunu söyler. Kullanılan sayı 0,375 km; "yarım piksel" etiketi belgeler arasında tutarsız.
- **WorldCover anız ekili payı:** `metrics.json` 0,7935; `calisma_prensibi.md` §3.5 "%79,3"; soru-cevap provası S9 "%79,4"; 0,7935 yuvarlaması %79,35 olduğundan her iki yuvarlama tutarlıdır ama ikisi farklı yazılmış.
- **Anız etiketi:** `bulgular.md` F2-05 anız sayılarının "tahmini" olmasını önerdi ve kapandı diyor ("iki anahtar aynı etiket"); `metrics.json`'da her iki anahtar (`temizlik_status_aniz`, `temizlik_olay_aniz_nokta`) **ölçüldü** etiketli ve `temizlik_yontemi.md` etiket kuralı da "sayımlar ölçüldü" diyor. Bu fark çözülmemiş görünüyor (tutarlı ama öneriden farklı).
- **Referans set boyutu:** `temizlik_yontemi.md` §8 "28 tesis / 9 yangın" yazar, ardından 3 kaydın ayıklandığını anlatır; `calisma_prensibi.md` ve metrics.json 26/8'i verir (ayıklama sonrası).
- **`ref_precision`:** `bulgular.md` F2-06 ilk gözlem 0,9997 (nokta düzeyi); düzeltilmiş dengeli değer 0,971; soru-cevap provası "%99,97 kullanılmamalı" der.
- **Sıçrama doğal aralığı:** eski (`degisim_gunlugu` ilk teslim) [−40,2, 94,0] ↔ güncel [−39,3, 92,61]; hangisinin geçerli olduğu güncel metrics.json'dur.
- **Kümeleme girdisi:** `kumeleme_yontemi.md:7` ilk adımda "type ∉ {1,3}" 1.405.848 nokta / 534.919 olay; şu an temiz+anız 1.044.222 / 471.978 (eski sayılar geçersiz). `bulgular.md` F2-11 `status == 'temiz'` diye yazılmış eski ifadenin düzeldiğini kaydeder.
- **Arayüz anahtar sayısı:** `bulgular.md` F4 "224 anahtar", F3 ve `arayuz_yontemi.md` "279 anahtar" (F3-01 ile düzeltildi).
- **Anız ay takvimi:** `temizlik_yontemi.md` öğrenilen ayları yazmaz (`audit/aniz_takvimi.json` bu klasörde yok); yukarıdaki aylar `metrics.json → sensitivity.aniz_aylari` kaynaklıdır.
- **Harmonizasyon cebirsel formülü** ve MODIS/VIIRS kenar piksel formülleri belgelerde yok (bkz. §4 ve §5).
