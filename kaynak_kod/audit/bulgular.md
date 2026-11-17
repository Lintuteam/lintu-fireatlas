# Denetçi bulguları

Biçim: kimlik · seviye · nerede · gözlem (komut/çıktı) · neden önemli · öneri · sorumlu. Yüksek bulgu kapanmadan faz bitmez.

## F1 (veri hattı) — 2026-11-13

Bağımsız yeniden hesap: `audit/f1/xlsx_oku.py` (27 xlsx openpyxl ile, `raw_all.parquet` ve `pandas.read_excel` kullanılmadan) + `audit/f1/karsilastir.py` (polars, kendi güven kuralı, matplotlib.Path ile il testi). Sonuç `audit/yeniden_hesap.json`: **ölçülen tüm sayım metriklerinde fark 0** (toplam 1.414.674; sensör, uydu, yıl×uydu tablosu 27/27 satır, NRT 61.147 = VIIRS 58.465 + MODIS 2.682, type dağılımı, `bt_estimated` 184.902, yinelenen 0). 1.414.674 satırın **tamamı** pid ile ham satıra birleştirildi: t_utc/lat/lon/frp/sat/sensor/src_product/day_tr/src_year uyuşmazlığı 0; 1000 örneklemde (tohum 20261113) conf_cls dahil 0; güven eşlemesi 0 uyuşmazlık.

### F1-01 · YÜKSEK · `data/processed/coverage.parquet`, `src/pipeline/build_coverage.py`, `tools/check_all.py` C06 — **KAPANDI (F4)**
- **Gözlem:** coverage her uydu için [ilk tespit, son tespit] aralığındaki **her güne** `observed=True` yazıyor (28.308 satır, `observed_false=0`, `n_overpass` tamamen boş). Oysa SNPP 2022-07-26 → 2022-08-11 arası 16 gün hiç tespit yok, aynı pencerede N20 1.112, Terra 54, Aqua 42 tespit var (yaz yangın mevsimi; bilinen SNPP kesintisiyle tutarlı). coverage bu günleri `SNPP, 2022-08-01, observed=True` olarak veriyor. Tespitli gün / coverage gün: SNPP 5.304/5.401, N20 3.126/3.148, N21 1.344/1.353.
- **Neden önemli:** Kesinti günleri "gözlendi, yangın 0" diye takvim/anomali/harmonizasyon oranına girer (Temmuz–Ağustos 2022'de yapay düşüş). C06 ise aynı points'ten türetilen aralığa göre test ettiği için totolojik: her zaman GEÇER. `observed` adı kanıtsız bir iddia (K5); `tahmini` etiketi tabloda yok, yalnız docstring/README'de.
- **Öneri:** `observed` → `operasyonel_tahmini` (veya `observed` = NA/bilinmiyor); tabloya `etiket='tahmini'` sütunu; aynı sensör ailesindeki diğer uydular tespit verirken ≥k gün sıfır olan aralıkları `olasi_kesinti` işaretle (k config'te, K9); C06'yı coverage'ın points'ten bağımsız bir sinyale (ör. diğer uydu ile çapraz kesinti testi) göre sına.
- **Sorumlu:** veri-hatti (coverage); C06 testi koordinatör (`tools/`).

### F1-02 · ORTA · `points.parquet` `il`, `data/README.md`, `audit/veri_envanteri.md` — **KAPANDI (F4)**
- **Gözlem:** il="(dışı)" 14.042 satır (bağımsız PIP 1500 örnekte 0 farklı → atama demoyla tutarlı). Ama en yoğun 0,1° hücreler: 40,7N 29,5E (2.181) ve 40,7N 29,7E (1.561) = İzmit Körfezi sanayi kıyısı; 38,7N 26,9E (1.008) = Aliağa; 36,7N 36,1E (804) = İskenderun. Bunlar Türkiye karasındaki tesisler; il poligonu kaba olduğu için dışarıda kalıyor. Öte yandan 35,8N 36,0E (536+253, Suriye), 37,0N 44,2E (Irak), 39,7N 44,6E (İran/Ermenistan) gerçekten yurt dışı. Ayrıca NASA `type=3` (açık deniz) 8.821 satırın 6.336'sı bir ile atanmış → poligon kıyıda denize taşıyor.
- **Neden önemli:** (a) En büyük sanayi kaynakları il filtresinde kaybolur; (b) "Türkiye 1.414.674 tespit" sayısı komşu ülke tespitlerini içeriyor (veri bir bbox, ülke sınırı değil); README'deki "kıyı/sınır dışı" açıklaması bu karışımı gizliyor.
- **Öneri:** `(dışı)` ikiye ayrılsın: `yurt_disi` (ülke sınırı ile) ve `kiyi_tampon` (en yakın ile ≤X km, X config'te); belgelerde "Türkiye kutusu (bbox)" ifadesi; il poligonunun çözünürlüğü/lisansı yazılsın. Yurt dışı satır sayısı ölçülüp raporlansın (bu denetimde ülke sınırı yok → **doğrulanamadı**).
- **Sorumlu:** veri-hatti.

### F1-03 · ORTA · `tools/check_all.py` C07 — **KAPANDI (F4)**
- **Gözlem:** C07 yalnız `timeutil.tr_day` fonksiyonunu test ediyor; `points.parquet` içindeki `day_tr` sütununu t_utc+3h ile karşılaştırmıyor ve `dosya_yili_ile_utc_yili_farkli` değerini ölçüp FAIL koşuluna bağlamıyor. `build_points.py` `day_tr`'yi timeutil'i değil kendi `pd.Timedelta(hours=3)` ifadesini kullanarak üretiyor (bkz. F1-04), yani C07 üretimde kullanılan yolu test etmiyor. (Bu denetimde tüm satırlar bağımsız olarak doğru bulundu: 0 uyuşmazlık.)
- **Öneri:** C07'ye veri üzerinde `day_tr == (t_utc+3h).date` ve `mixed==0` koşulları eklensin.
- **Sorumlu:** koordinatör (`tools/` işçilere kapalı).

### F1-04 · DÜŞÜK · `src/pipeline/build_points.py:129`, `:116` — **KAPANDI (F4)**
- **Gözlem:** `day_tr` için sabit `pd.Timedelta(hours=3)`; `timeutil.TR_OFFSET_HOURS` tek tanımı kullanılmıyor (K11 tek tanım ilkesi). Satır 116'da ikinci bir etiket eşlemesi (`low→dusuk…`; yalnız tutarlılık denetimi için, sonuca girmiyor). C08 deseni bunların hiçbirini yakalamıyor.
- **Öneri:** `timeutil.tr_day` çağrılsın; 116 yorumla "denetim amaçlı" kalabilir.
- **Sorumlu:** veri-hatti.

### F1-05 · DÜŞÜK · `src/pipeline/timeutil.py`, `docs/04` §2 — **KAPANDI (F4)**
- **Gözlem:** Sabit UTC+3 tüm yıllara uygulanıyor; Türkiye 2016 öncesi kışın UTC+2 idi. 2016 öncesi 21:00–21:59Z tespiti 88 satır (etki çok küçük).
- **Öneri:** docs/04 §2'ye "tüm yıllar için sabit UTC+3 (bilinçli karar; 2016 öncesi kış saatleri 1 saat kayık)" notu.
- **Sorumlu:** veri-hatti / koordinatör (docs/04).

### F1-06 · DÜŞÜK · belgeler — **KAPANDI (F4)**
- **Gözlem:** `data/README.md` ve `audit/veri_envanteri.md` binlik ayırıcıyı "1,414,674" (EN), `docs/04` "1.414.674" (TR) yazıyor. `build_points.py` docstring'i "59 ham kaynak dosyası" diyor (59 = tekil `source_file`, xlsx sayısı 27); belirsiz.
- **Neden önemli:** C22 belge-sayı taraması iki biçimi de ayrıştırmalı; okuyucuya "59 dosya mı 27 mi" sorusu.
- **Öneri:** Tek biçim (TR) ve "27 xlsx, içinde 59 kaynak CSV" ifadesi.
- **Sorumlu:** veri-hatti.

### F1-07 · DÜŞÜK · `src/pipeline/test_pipeline.py` — **KAPANDI (F4)**
- **Gözlem:** `pid = yıl×10⁷ + raw_all.parquet içindeki dosya-içi sıra`. Bugün openpyxl satır sırasıyla birebir (0 uyuşmazlık), ama hiçbir test pid'in ham xlsx satırına karşılık geldiğini doğrulamıyor; önbellek farklı sırayla yeniden üretilirse pid'ler sessizce kayar.
- **Öneri:** Birkaç sabit pid için xlsx satırıyla karşılaştıran test (ör. her yılın ilk/son satırı).
- **Sorumlu:** veri-hatti.

Kontroller: `python tools/check_all.py` → GEÇTİ 3 (C06, C07, C08), KALDI 0, ATLANDI 22 (F2+ girdileri henüz yok; gerekçeler uygun). C06 geçişi F1-01 nedeniyle anlamsız. `python src/pipeline/test_pipeline.py` → 6/6 geçti.


## F2 (temizlik, kumeleme, harmonizasyon, takvim-analiz) — 2026-11-13

Kapsam: `src/{cleaning,clustering,harmonize,analytics}`, `data/processed/{points_status,points_event,points_mcell,events}.parquet`, `agg/*`, `reports/metrics.json`, yöntem belgeleri, `audit/dogrulama_seti.csv`, `esikler.json`. Arayüz kapsam dışı (F4).

**Bağımsız yeniden hesap (C23):** `audit/f2/yeniden_hesap_f2.py` (yalnız pandas/numpy, `src/` import edilmez; yıl/ay `t_utc+3h`'ten bağımsız türetildi) → `audit/yeniden_hesap.json` `f2_*` (76 girdi, F1 girdileri korundu). **Tüm karşılaştırmalarda fark 0:** huni (1.414.674 = temiz 827.043 + aniz 217.179 + statik_nasa 328.379 + sanayi 27.012 + deniz 8.848 + kalici_belirsiz 6.208 + volkan 5; status boş 0); kümelenen nokta 1.044.222 = temiz+aniz, temiz/aniz dışı olaya giren 0; olay 471.978; `n_modis/n_viirs/day_tr_start` satır farkı 0; match_class (kendi çakışma günü hesabımla) ortak 35.651 / yalnız MODIS 57.543 / yalnız VIIRS 287.781 / tek sensör 91.003, satır bazında fark 0; C05 toplamı 380.975; TR yıllık temiz tespit (monthly.parquet) |fark| 0; tüm il×yıl×ay temiz olay |fark| 0 (örnek: Muğla 2021-08 = 32, Şanlıurfa 2019-06 = 328); TR modis_temiz ay medyanları 12/12 aynı; sıçrama: gerçek MODIS −44,9, ham M+V +143,13, ham yalnız VIIRS +88,03, harmonize −41,35, doğal aralık [−39,3, 92,61]; (i0) LOYO yıllık MAPE 42,12; (ii) yıllık MAPE (parquet'ten) 8,33.

**K4 iz sürme (kodda):** `seri.loyo` eğitim = 2012–2025 ∖ test yılı; (ii) oranları ve (iii) Terra payı test yılı hariç; `kalibrasyon.loyo_grid` hücre özellikleri `haric_yil` ile, eşik eğitim yıllarında F1 ile seçiliyor; `aniz_takvim.profil(haric_yil)`; `analiz.py:122` anomali normali `ym != yr`. Doğrudan sızıntı bulunmadı. Kalan ikinci derece etkiler F2-03'te.

### F2-01 · YÜKSEK · `data/processed/agg/harmonized.parquet`, `monthly.parquet` (olay eşdeğeri vs tespit eşdeğeri) — K8 — **KAPANDI (F4)**
- **Gözlem:** Olay eşdeğeri = "en az bir MODIS tespiti içeren olay" (`olay.py` docstring); tanım gereği ≤ MODIS tespit eşdeğeri. 2012–2025'te `birim=olay, duzey=ay_il` bölgeye toplanınca `birim=tespit, duzey=ay_bolge` değerini **98/1.252 bölge×ay hücresinde aşıyor** (temiz_aniz: 93), en fazla +8, oran en çok 2,0 (ör. 2017-07 İç Anadolu olay 46 > tespit 40; 2024-04 İç Anadolu 86 > 84). TR düzeyinde 6 ay (2014-04: 129 > 125; 2026-04, 2026-05 dahil). Gerçek MODIS tarafında aynı karşılaştırma 0 ihlal (sağlama). Kanıt: `audit/f2/yeniden_hesap_f2.py` (`f2_k8_*`) + ayrı pandas sorgusu (harmonized.parquet `ana_seri`, 2012–2025 tamamı `viirs_modis_esdeger`).
- **Neden önemli:** Yayımlanan iki seri birlikte okunduğunda mantıksız sayı (olay > tespit) — sabit oran tuzağıyla (B-04) aynı sınıf; okuyucu yan yana görürse modeli sorgular.
- **Öneri:** Olay eşdeğerini tespit eşdeğeriyle tutarlı kıl (ör. olay = min(olay_tahmin, tespit_tahmin) + bayrak, ya da olay/tespit oranını modelleyip tespit eşdeğerinden türet); kontrolü `test_harmonize.py`'a ekle (ihlal 0).
- **Sorumlu:** harmonizasyon.

### F2-02 · ORTA · `src/config/esikler.json → harmonizasyon.ogrenilen_guven_esleme` — **KAPANDI (F4)**
- **Gözlem:** Elle yazılmış anlatı alanı `n_cift: 40439`, "VIIRS payları … n 71,1%"; hesap çıktısı (`data/interim/harmonize/guven_esleme.json`, `metrics.guven_cift_sayisi`, belge §9) **40.368**, n payı 0,7102. `grep 40439` yalnız config'te.
- **Neden önemli:** K1 (sayı yazılmaz, hesaplanır) ve K10 (güven eşlemesinin tek yeri bu blok): tek doğruluk kaynağı olması gereken dosyada eski sayı. Arayüz/rapor bu bloğu okursa yüksek'e çıkar.
- **Öneri:** Bloktaki sayısal anlatıyı sil, `guven_esleme.json`/metrics anahtarına referans ver; yalnız sınırlar (35/82) config'te kalsın.
- **Sorumlu:** harmonizasyon.

### F2-03 · ORTA · Yöntem seçimi (ii) vs (i) — `src/harmonize/seri.py:main`, `docs/harmonizasyon_yontemi.md §5, §9` — **KAPANDI (F4)**
- **Gözlem:** Kazanan (ii) ay×bölge WAPE 30,63; (i) sabit oran+efor 30,64 (fark 0,01 puan). Diğer tüm ölçütlerde (i) daha iyi: yıllık MAPE 4,83 vs 8,33, R² 0,9675 vs 0,8716, %95 [−7,81, 9,46] vs [−23,49, 9,51]. "Önceden belirlenen ölçüt" yalnız ajanın kendi docstring'inde ve belgesinde; ajan tanımı (`.claude/agents/harmonizasyon.md:16`) ölçüt belirtmiyor; klasör git'te izlenmiyor → ölçütün sonuçtan önce sabitlendiği **doğrulanamadı**. Seçim LOYO test sonuçları üzerinde yapıldığı için kazananın raporlanan hatası hafif iyimser (seçim etkisi). İkinci derece: temizlik `status`'u (sanayi eşikleri, anız ayları) tüm yıllardan öğrenilmiş haliyle harmonizasyon LOYO'suna girer.
- **Neden önemli:** Belge "(ii) sabit oran tuzağını (K8) yener" izlenimi veriyor; veri bunu desteklemiyor: efor normalizasyonlu tek oran ay×bölgede eşit, yıllıkta daha iyi. Seçim (ii)'yi tercih ettiği için başlık sayıları daha kötü (iyimser değil), ama iddia dürüst değil (K5).
- **Öneri:** Belgeye "(i) ve (ii) ay×bölge düzeyinde ayırt edilemez (yıl bootstrap'ıyla WAPE farkı ve %95 aralığı)" satırı; seçim kuralına eşitlik toleransı (eşitse daha basit model). Bu bir ölçüt değişikliğidir: koordinatör kararı ve `degisim_gunlugu` kaydı gerekir. C10 artığı her iki yöntem için raporlansın.
- **Sorumlu:** harmonizasyon (koordinatör onayı).

### F2-04 · ORTA · 2026 rejimi ve "mevcut ay 0,127" — `agg/current_month.parquet`, `monthly.parquet`, `docs/harmonizasyon_yontemi.md §4` — **KAPANDI (F5)** — uyarılar F4'te kapandı; 2026 eşdeğer sapmasının arayüz kısmı F4-01 ile F5'te kapandı (tek durum; aşağıdaki "F1–F2 Kapanış" tablosu da bununla uyumlu).
- **Gözlem:** (a) Kasım 2026 ilk 12 gün MODIS ham 67 (Aqua 43, Terra 24) vs 2019–2025 aynı günler 485–945. Düşüş iki sensörde birlikte (VIIRS uydu-başına oran 0,243; N20/N21 günlük sayıları 26 Ekim'den itibaren aynı anda düşüyor) → kısmen gerçek (hava) etkisi; MODIS'in ek ~2 kat düşüklüğü sensöre bağlı görünüyor. Aqua gündüz geçiş medyanı 10,70 UTC (2015) → 11,92 (2025) → **12,65 (2026)**; Terra 8,55 → 7,33. Aqua–VIIRS |Δt| ≤ 60 dk kalibrasyon çifti payı 2012–2023 ~%85 → 2025 %49 → **2026 %18**. 2026'da eşdeğer seri gerçek MODIS'ten çok sapıyor: E/M 0,13–3,39; gerçek MODIS bant dışında **4/10 ay** (2026-01: 18 < 34; 04: 339 > 215; 05: 489 > 186; 10: 507 < 566). LOYO bant kapsaması 0,92 iddiasına karşı 2026'da ~0,6. (b) `current_month.parquet` TR satırlarının `uyari` alanı yalnız `sensor_gecis_yili`; `kismi_ay_ilk_D_gun` yalnız sorgu anında (`query.py:111`) ekleniyor, **NRT ve yörünge kayması uyarısı hiçbir yerde yok**. Etiket `tahmini` doğru. Belge kaymayı "2020 sonrası, modellenmedi" diye geçiyor; asıl hızlanma 2024+.
- **Neden önemli:** "Kasım 2026 tarihsel medyanın 0,127 katı (yüzdelik 4,3)" okuyucuya olağandışı düşük aktivite diye okunur; büyük kısmı sensör ömrü sonu + NRT etkisi olabilir. MODIS bitince (Terra 2027-01, Aqua ~2027-09; docs/02) seri tamamen bu kalibrasyona dayanacak.
- **Öneri:** current_month'a kalıcı `nrt`, `modis_yorunge_kaymasi` (geçiş saati eşiği config'te) ve `kismi_ay` uyarıları; 2026 için eşdeğer–gerçek MODIS bant uyumu metriği (`harm_2026_bant_kapsama`); belgeye yıllık geçiş saati tablosu ve çift payı düşüşü. MODIS-sonrası için kalibrasyon yıllarını 2012–2023 ile sınırlayan varyant sınansın.
- **Sorumlu:** takvim-analiz (uyarılar), harmonizasyon (2026 bant, kayma), veri-hatti (NRT bayrağı).

### F2-05 · ORTA · Dürüstlük etiketleri — `reports/metrics.json` (K5) — **KAPANDI (F4)**
- **Gözlem:** (1) `jump_harm_pct`, `jump_harm_eksi_modis_pct`/`jump_resid_pct`, `olay_temiz_jump_harm_pct`, `equiv_overlap_bias`, `harm_kazanan_yontem` "ölçüldü"; ama model tahmininden türetilmiş değerler (eşdeğer seri kendisi `tahmini`; takvim de eşdeğeri `tahmini` etiketliyor) → modüller arası etiket tutarsızlığı. (2) Aynı büyüklük iki etiketle: `temizlik_status_aniz` = 217.179 **ölçüldü**, `temizlik_olay_aniz_nokta` = 217.179 **tahmini**. (3) `temizlik_olay_*` birimi "nokta/olay" (hangisi olduğu belirsiz).
- **Öneri:** Kural: hesap girdisinde `tahmini` bir seri varsa sonuç `tahmini` (LOYO hata ölçüleri "ölçüldü" kalabilir: gerçek MODIS'e karşı ölçülen hata). Anız sayıları tek etiket (`tahmini`, kural tabanlı). Birimleri ayır.
- **Sorumlu:** harmonizasyon, temizlik; build_metrics'e etiket tutarlılık kontrolü koordinatör.

### F2-06 · ORTA · Referans doğrulama — `audit/dogrulama_seti.csv`, `ref_precision` 0,9997 (C13) — **KAPANDI (F4)**
- **Gözlem:** Kesinlik 125.982 tesis noktasına karşı yalnız 9.696 yangın noktasıyla hesaplanıyor → değer sınıf dengesizliğinden "mükemmele" yakın; asıl bilgi `yangin_koruma` 0,996 ve `site_recall` 0,48. Set içinde çakışmalar: S01 ve S02 (Tüpraş İzmit A/B, 2 km yarıçap) aynı noktaları sayıyor (ikisi de statik 3.196 + sanayi 487); Y02 "Milas Kemerköy yangını" merkezi S18 Kemerköy santraliyle **aynı koordinat** (15 km); Y06 Dörtyol (15 km) S08 İsdemir'i (~9,7 km) içine alıyor. Sistem recall'ının büyük kısmı NASA type=2'den (S06'da 36.068 statik), ekibin kuralından değil.
- **Öneri:** Kesinliği dengeli raporla (tesis başına / yangın başına makro ortalama ya da eşit örneklem); çakışan siteleri birleştir, yangın alanlarından tesis tamponunu çıkar; "kural tek başına" ve "NASA mirası" katkısını ayrı tabloda ver. Mevcut değer "tahmini" etiketli (doğru), ama sunumda "%99,97" diye kullanılmamalı.
- **Sorumlu:** temizlik.

### F2-07 · DÜŞÜK · C10 inceltmesi (koordinatör kararı) — `docs/03` C10, `audit/degisim_gunlugu.md` — **KAPANDI (F4)**
- **Gözlem:** Gerekçe geçerli: gerçek MODIS (−44,9) de eski doğal aralığın [−39,3, 92,61] dışında; eski ölçüt kusursuz bir harmonizasyonu da reddederdi. Ama değişiklik sonuç görüldükten sonra yapıldı (post-hoc) ve yeni ölçüt büyük ölçüde C09'un tekrarıdır: artık = (2012–14 LOYO tahmin − gerçek)/2009–11 ort. ≈ 0,55 × 2012–14 ortalama yıllık hata (9,28; 5,05; 5,69 → 3,6). Ayrıca 3 yıllık ortalama, yıllık %95 aralıkla kıyaslanıyor (gevşek). Benim eşdeğer testim: aynı tanımla 2013–2023 tüm 3+3 pencerelerin artık dağılımı [−10,43, +4,62]; 2012 değeri 3,55 bu aralıkta → **sonuç sağlam**. `degisim_gunlugu`ndaki sayılar (ham +116,2, harmonize −49,6, MODIS −51,5, aralık [−40,2, 94,0]) ilk teslim (type 0/−1) sayılarıdır; bugünkü metrics'ten farklı ve bu not edilmemiş.
- **Öneri:** C10 karşılaştırma aralığı = 3 yıllık pencere artık dağılımı; günlüğe "sayılar ilk teslimden, güncel: …" notu; önerilen ifade: "sıçrama kayboldu" değil, "harmonize seri 2012'deki gerçek MODIS düşüşünü 3,6 puan farkla izliyor; ham seri +143 % sensör eklenmesinden".
- **Sorumlu:** koordinatör.

### F2-08 · DÜŞÜK · Tarım zinciri "33 olay" — `docs/kumeleme_yontemi.md:110`, `src/clustering/build_events.py:458` — **KAPANDI (F4)**
- **Gözlem:** Bağımsız sayım (TR ayı ile) **34 olay / 9.484 tespit**; kod `t_start_utc.dt.month` (UTC ayı) kullandığı için 33 / 9.338 (K11: arayüz günleri TR). Belgedeki örnekler Osmaniye 2018-08-11 (ort. FRP 18,6 MW) ve Adana 2013-08-23 (19,5 MW) kendi "ortalama FRP < F = 15" tanımını **sağlamıyor** (bunlar kapsam sıralı `chain_cases` listesinden). "Tespitlerin ~%6'sı" 152 olaya (64.932) ait; 33/34 olay tespitlerin ~%0,9'u. F MODIS ölçeğinde, karışık sensörlü olay ortalamasına uygulanıyor. 152 olayın tamamı `status=temiz`.
- **Öneri:** Ay TR gününden; örnekleri tanımı sağlayan olaylardan seç (Osmaniye 2026-08-31, 2015-08-30, 2019-08-24); yüzdeleri ayır; F'yi sensöre göre uygula.
- **Sorumlu:** kumeleme.

### F2-09 · DÜŞÜK · Temizlik MODIS dönemi kesinlik 0,228 — `metrics.temizlik_sanayi_loyo_precision_modis_donemi` — **KAPANDI (F4)**
- **Gözlem:** Referans (NASA type=2) MODIS'te 2000–2011'de çok seyrek: MODIS type=2 payı 2011 öncesi %0,69, sonrası %5,04. Bağımsız kontrol: 2000–2011 `sanayi` etiketli 1.477 MODIS noktasının **984'ü (%67)** dogrulama_seti tesislerine ≤ 3 km. Düşük kesinlik büyük ölçüde referansın eksikliğinden; kural hatası değil.
- **Öneri:** Metrik yanına tesis-tabanlı kesinlik ve "referans seyrek" notu; tanım "NASA type=2 ile uyuşma, doğruluk değil".
- **Sorumlu:** temizlik.

### F2-10 · DÜŞÜK · Sabit yıl/saat sabitleri (K9, K11) — **AÇIK (F4)**
- **Gözlem:** `seri.py:207` (2003, 2025), `seri.sicrama_paketi` null aralığı 2003/2025 ve geçiş 2012 sabit; `build_events.py:139` "2012-01-20", `:207` `Timedelta(hours=3)` (F1-04 ile aynı tür), `:458` UTC ayı; `build_status.py:329` 2011/2012; `olay_aniz.py:90`; `run_all.py:39` 2003–2011. Config'te `loyo_test_yillari`, `eski_donem_yillari` var ama bu satırlarda kullanılmıyor.
- **Öneri:** Yılları config/yil_bilgi'den, TR günü timeutil'den al. **Sorumlu:** harmonizasyon, kumeleme, temizlik.

### F2-11 · DÜŞÜK · Belge tutarsızlıkları — **AÇIK (F4)**
- **Gözlem:** `kumeleme_yontemi.md:7` "status == 'temiz' olan 1.044.222 nokta"; oysa 1.044.222 = temiz 827.043 + aniz 217.179 (kod: `status∈{temiz,aniz}`). `harmonizasyon_yontemi.md §9` otomatik tablolar EN ondalık ("8.33", "0.8716"); diğer belgeler TR (F1-06 ile aynı).
- **Sorumlu:** kumeleme, harmonizasyon.

### F2-12 · DÜŞÜK · Kontrol zayıflıkları — `tools/check_all.py` — **AÇIK (F4)**
- **Gözlem:** C09 yalnız `loyo_method` metninde "leave-one-year-out" arıyor; C23 `fark≠0` olsa da `aciklama` alanı varsa geçiriyor (F1 girdilerinde `aciklama` tanım olarak kullanılmış, fark açıklamasıyla karışıyor). F2 girdilerinde tanım `tanim` alanında; `aciklama` yalnız fark açıklaması.
- **Öneri:** C23 ayrı `fark_aciklamasi` alanı istesin; C09 eğitim/test yılı listelerini metrics'te (`loyo_folds`) doğrulasın. **Sorumlu:** koordinatör.

**Şüpheliler sonucu:** (a) 0,127 → kısmen gerçek düşük aktivite (VIIRS de 0,243), kısmen MODIS ömrü sonu/NRT; uyarı eksik (F2-04). (b) 0,01 puan → ayırt edilemez, önceden sabitleme doğrulanamadı (F2-03). (c) 0,228 → referans seyrekliği (F2-09). (d) 33 → 34 (UTC/TR ay), örnekler tanım dışı (F2-08). Anız takvimi kaldıracı 0,93 belgede dürüstçe "ay tek başına ayırmıyor" diye yazılmış; WorldCover desteği (anız %79 ekili alan, büyük temiz %50) ölçüldü.

Kontroller: `python tools/check_all.py` → GEÇTİ 22, KALDI 0, ATLANDI 3 (C22, C24, C25: raporlar F5'te üretilecek; gerekçe uygun). Süre 1 dk 30 sn. C09/C10 geçişleri F2-07/F2-12 ile birlikte okunmalı.


## F4 (tam denetim: kapanışlar + arayüz `src/app`) — 2026-11-13

### Kapanış doğrulaması (F1/F2) — kanıt benim komutlarımdan
| Kimlik | Durum | Kanıt |
|---|---|---|
| F1-01 | kapandı | coverage `observed=False` 129 gün (`source=çıkarım_kesinti`), `etiket=tahmini` tüm 28.308 satır; SNPP 2022-07-26…08-11: 15/17 gün kesinti. C06 artık kesinti düzeltmesini sınıyor. |
| F1-02 | kapandı | `bolge`: il 1.400.632 / kiyi 14.042 / yurt dışı 0; README sınıra uzaklık (maks 3,68 km) ile ölçmüş. type=3'ün kıyı ilişkisi belgelendi. |
| F1-03 | kapandı | `check_all.py:206-215` veri üzerinde `dosya_yili_ile_utc_yili_farkli` ve gün kontrolü FAIL koşulunda. |
| F1-04 | kapandı | `build_points.py:199` `timeutil.tr_day`. |
| F1-05 | kapandı | `docs/04` §2 satır 44 sabit UTC+3 + 88 satır notu. |
| F1-06 | kapandı | `1,414,674` biçimi grep 0; docstring "27 xlsx (59 kaynak CSV)". |
| F1-07 | kapandı | `test_pipeline.py:86 test_pid_ham_xlsx_satirina_karsilik_gelir`. |
| F2-01 | kapandı | harmonized: ay_bolge olay>tespit ihlali 0/2.350, ay_TR 0. |
| F2-02 | kapandı | `grep 40439 src/config docs` → 0. |
| F2-03 | kapandı | `harmonizasyon_yontemi.md:182` "ayırt edilemez", bootstrap [−2,97, 4,26]; `harm_ii_eksi_i_wape_ci95`. |
| F2-04 | kısmen (F4) → **kapandı (F5)** | Uyarılar (`kismi_ay`, `nrt_donemi`, `aqua_yorunge_kaymasi`) ve `harm_2026_bant_kapsama`=0,545 eklendi. 2026 eşdeğer sapması arayüzde → F4-01, F5'te kapandı. |
| F2-05 | kapandı | `jump_*`, `equiv_overlap_bias`, `harm_kazanan_yontem` artık tahmini; anız iki anahtar aynı etiket. |
| F2-06 | kapandı | `ref_precision` 0,971 dengeli (makro), nokta değeri ayrı anahtarda; 3 çakışan kayıt ayıklandı. |
| F2-07 | kapandı | `degisim_gunlugu.md` F2 denetimi sonrası notu. |
| F2-08 | kapandı | belge 34 olay, `build_events.py:468` TR ayı. |
| F2-09 | kapandı | metrik tanımında "UYUŞMA, doğruluk değil" + `temizlik_modis_donemi_sanayi_tesis_payi` 0,666. |
| F2-10 | açık (düşük) | `seri.py:207` hâlâ `between(2003, 2025)`. |
| F2-11 | açık (düşük) | `kumeleme_yontemi.md:7` düzeldi; `harmonizasyon_yontemi.md` §9 EN ondalık ("30.63") sürüyor. |
| F2-12 | açık (düşük) | `check_all.py`'de `fark_aciklamasi` / `loyo_folds` yok. |

### Arayüz ekran = hesap (C14) — çalışma anı
`python -m http.server` + Claude Browser; ekran değerleri DOM'dan, karşılaştırma pandas ile `agg/*.parquet`, `events.parquet`. **Birebir eşleşenler (fark 0):** TR olay_esdeger matrisi 2003/2012/2019/2021/2025/2026 satırlarının 72 hücresi (`seri_aylik`); TR ay medyanları 12/12 ve n_yil 23 (`profile`); Muğla 6 satır×12 ay; TR son tam ay 903 / medyan 532 / %170 / yüzdelik 61 (`current_month` modis_esdeger); match_class (temiz) 32.619 / 33.482 / 180.349 / 56.413 ve status temiz 302.863 / anız 169.115 (`events` çapraz tablo); sıçrama tablosu 143,1 / −44,9 (metrics); metrik tablosu 12 anahtar; 2021-07-28 olay CSV 71 satır = events 71; Laboratuvar örneği Manisa 2018-01-07 (Terra 09:16Z FRP 22, 3 SNPP 9,09/5,72/5,72, 0,63×0,72) = points.parquet. Sahte veri yok (`manifest.simulated=False`, rozet gizli), `Math.random` yok, sabit metrik yok; CSV BOM (EF BB BF), formül öneki, t_utc+t_tr var; dış kaynak yok (OSM zemini isteğe bağlı, uyarılı); TR/EN 224 anahtar; "risk" yalnız alt başlıkta "risk değil" tanımıyla. Performans: benim ölçümüm eşik değişimi 188–266 ms (audit/performans.json 217–302 ms) → tutarlı. Erişilebilirlik JSON'u bağımsız yeniden ölçülmedi (yalnız aria-label ve roving tabindex gözlendi) → **doğrulanmadı**.

### F4-01 · YÜKSEK · TR "son tam ay" kutusu 2026'da eşdeğer seriyi gösteriyor, iki sensörün kendi verisiyle çelişiyor — `src/app/core.js:160`, `src/analytics/query.py:195-206` — **KAPANDI (F5)**
- **Gözlem:** TR açılışında mevcut ay kutusu `modis_esdeger` seçiyor: Ekim 2026 = 903, tarihsel medyanın **%170**'i. Aynı ay gerçek ölçümler: `modis_temiz` 507/579 = **0,876**, `viirs_temiz_ub` 0,944, `viirs_ham_ub` 0,875 (`current_month.parquet`). Bölgede daha uç: İç Anadolu eşdeğer 2,38×. Ayrışma yorumu (`ayrisma_yorum`) yalnız MODIS serileri için ve yalnız "MODIS düşük" yönünde çalışıyor; `modis_esdeger` satırında boş → ekranda uyarı yok. `harm_2026_bant_kapsama`=0,545 (eşdeğer bandı 2026'da gerçek MODIS'i ayların yarısında kaçırıyor) arayüzde hiç gösterilmiyor. Matris de aynı yönde (olay_esdeger Ekim 2026 705 vs medyan 381).
- **Neden önemli:** Kullanıcının ilk göreceği "bu ay" cümlesi, kalibrasyon dışı (Aqua kayması, çift payı 0,182) bir modelin ürettiği ve iki sensörün de doğrulamadığı "normalin 1,7 katı" iddiası. K5, şüpheli sonuç.
- **Öneri:** 2026 (veya `harm_2026_bant_kapsama` < `equiv_band_kapsama_ay_tr`) için mevcut ay kutusunda ölçülen seriyi (modis_temiz + viirs_temiz_ub) öne al, eşdeğeri ikincil ve "kalibrasyon dışı" rozetiyle göster; ayrışma yorumunu eşdeğer serisine ve iki yöne genişlet; 2026 satırına bant kapsama uyarısı.
- **Sorumlu:** takvim-analiz (query.py yorum), arayuz-harita (seri önceliği/rozet), harmonizasyon (2026 geçerlilik sınırı).

### F4-02 · ORTA · Mevcut ay kutusu matristeki seriyi izlemiyor — `core.js:160` — **KAPANDI (F5)**
- **Gözlem:** Matris `olay_esdeger` (olay) iken kutu TR'de `modis_esdeger` (tespit), Muğla'da `modis_temiz` gösteriyor (Muğla Ekim 2026: matris 1, kutu 0). `current_month.parquet`'te `olay_esdeger` hiç yok. Seri adı yazıyor, ama yan yana iki farklı birim/medyan (532 vs 381) okuyucuyu yanıltır.
- **Öneri:** current_month'a olay_esdeger eklensin ya da kutu başlığında "matristen farklı seri" uyarısı. **Sorumlu:** takvim-analiz, arayuz-harita.

### F4-03 · DÜŞÜK · Aynı büyüklük ekranda iki farklı değer — `main.js:230` — **KAPANDI (F5)**
- **Gözlem:** Sıçrama tablosunda harmonize değişim "tablodan" −41,3 %, "metrics.json" −41,4 % (aynı tanım, yuvarlama yolu farklı). C14 toleransı 0.
- **Öneri:** Tek kaynak (metrics) göster veya iki değeri aynı yuvarlamayla üret. **Sorumlu:** arayuz-harita.

### F4-04 · DÜŞÜK · Görüntü kusurları — **KISMEN (F5): (a) ve (d) kapandı; (b) ve (c) açık, bkz. F5-04**
- (a) Mevcut ay satırında ham değer "Aqua yörünge kayması (True)" (`main.js:130`). (b) Doğal aralık cümlesinde boş "[]" (`tr.json` `jump.natural` `{lab}` boş geçiliyor). (c) Ay medyanları tamsayıya yuvarlanıyor: Muğla Oca 0,5→"1", Haz/Eyl 1,5→"2"; sıralamada Mar(2, ★) ile Haz/Eyl ("2", ★ yok) eşit görünüyor. (d) Olay CSV'sinde koordinat float32 gürültüsü (36.841552734375 vs parquet 36.841554).
- **Sorumlu:** arayuz-harita (d: build_app_data).

**Kontroller:** `python tools/check_all.py` → GEÇTİ 22, KALDI 0, ATLANDI 3 (C22, C24, C25: raporlar F5'te; gerekçe uygun). C14 kontrolü kendi notunda "statik tarama" — çalışma anı karşılaştırması bu bölümde. **Faz kapısı:** F4-01 (yüksek) açık.

## F1–F2 Kapanış Doğrulaması — 2026-11-13

Faz 1 (veri hattı) ve Faz 2 (temizlik, kümeleme, harmonizasyon, takvim-analiz) aşamalarının tüm yüksek ve orta bulguları bağımsız denetimle incelenmiş, kod ve veri çıktılarındaki düzeltmeler doğrulanmıştır.

### 1. Yüksek ve Orta Bulguların Kapanış Kanıtları

| Kimlik | Seviye | Konu | Durum | Doğrulama Kanıtı |
|---|---|---|---|---|
| **F1-01** | **YÜKSEK** | Gözlem kapsamı (çıkarım kesinti) | **KAPANDI** | `src/pipeline/build_coverage.py`: G ve K eşikleriyle kardeş uydu kesinti çıkarımı eklendi. `coverage.parquet` içinde 129 gün `observed=False` (`source=çıkarım_kesinti`), tüm 28.308 satırda `etiket=tahmini`. SNPP 2022-07-26..08-11 kesintisi 15/17 gün başarıyla yakalandı. `check_all.py` C06 testi `GEÇTİ`. |
| **F1-02** | **ORTA** | İl / Kıyı / Bbox ayrımı | **KAPANDI** | `src/pipeline/build_points.py:180-192`: İl poligonu dışı noktalar B=5 km kıyı tamponu ile `kiyi` (14.042) olarak ayrıldı, yurt dışı 0 satır. `data/README.md` içinde sınıra en uzak mesafe 3,68 km (medyan 0,39 km) ve Kocaeli/İzmit Körfezi sanayisi (3.747 satır) belgelendi. |
| **F1-03** | **ORTA** | TR gün ve yıl kontrolü (C07) | **KAPANDI** | `tools/check_all.py:206-216`: C07 kontrolü `points.parquet` üzerinde `dosya_yili_ile_utc_yili_farkli` (0) ve `day_tr == timeutil.tr_day(t_utc)` (uyuşmazlık: 0) koşullarını doğrudan doğruluyor; C07 `GEÇTİ`. |
| **F2-01** | **YÜKSEK** | Olay eşdeğeri > Tespit eşdeğeri ihlali (K8) | **KAPANDI** | `src/harmonize/run_all.py:250-262`: Olay eşdeğerinin tespit eşdeğerini aştığı hücreler tespit tavanıyla kırpıldı (`lim[m].astype(int)`). `harmonized.parquet` üzerinde `ay_bolge` olay > tespit ihlali 0/2.350, `ay_TR` ihlali 0. `yeniden_hesap.json` `f2_k8_esdeger_bolge_olay_gt_tespit = 0`. |
| **F2-02** | **ORTA** | Config eski çift sayısı anlatısı | **KAPANDI** | `src/config/esikler.json:361-387`: Sabit `40439` sayısı ve anlatı kaldırıldı, hesaplanan değerler için `guven_esleme.json` ve `metrics.json`'a referans verildi (K1, K10). Sınırlar (35, 82) bırakıldı. |
| **F2-03** | **ORTA** | Harmonizasyon yöntem seçimi ((ii) vs (i)) | **KAPANDI** | `docs/harmonizasyon_yontemi.md:182` ve `metrics.json`: (ii) ile (i)'nin ay×bölge düzeyinde ayırt edilemez olduğu (bootstrap farkı %95 aralığı `[-2.97, 4.26]` yp) ve (i)'nin yıllıkta daha iyi olduğu dürüstçe belgelendi. Seçim gerekçesi (uygulama birimi ay×bölge) koordinatör kararıyla netleştirildi. |
| **F2-04** | **ORTA** | 2026 rejimi ve uyarı eksiklikleri | **KAPANDI** | `src/analytics/query.py:170-202`: `kismi_ay_gun`, `nrt_payi`, `aqua_yorunge_kaymasi`, `viirs_oran`, `modis_olculen_oran` ve `viirs_olculen_oran` alanları eklendi. `metrics.json`'a `harm_2026_bant_kapsama = 0.545` kaydedildi. (Arayüz sunumu F4-01 olarak izlenmektedir). |
| **F2-05** | **ORTA** | Dürüstlük etiketleri tutarlılığı (K5) | **KAPANDI** | `reports/metrics.json`: Model tahmininden türetilen metrikler (`jump_harm_pct`, `jump_harm_eksi_modis_pct`, `equiv_overlap_bias`, `harm_kazanan_yontem`, `loyo_ci95`) `tahmini` olarak etiketlendi. Anız metriklerinin birimleri ayrıldı (`nokta` / `olay`). |
| **F2-06** | **ORTA** | Referans doğrulama çakışmaları ve makro kesinlik (C13) | **KAPANDI** | `audit/dogrulama_seti.csv`: Çakışan tesisler (S02 Tüpraş B, S21 Soma B) ve yangın merkezi santralle aynı olan Y02 ayıklandı, Y06 yarıçapı 7 km'ye indirildi. `metrics.json`'da dengeli makro kesinlik `ref_precision = 0.971` raporlandı; C13 `GEÇTİ`. |

### 2. Düşük Seviyeli Bulguların Durumu

- **F1-04 (KAPANDI):** `src/pipeline/build_points.py:199` `timeutil.tr_day` kullanıyor.
- **F1-05 (KAPANDI):** `docs/04_VERI_SOZLESMESI_TASLAK.md:44` sabit UTC+3 ve 88 satırlık kış saati etkisi belgelendi.
- **F1-06 (KAPANDI):** `build_points.py` docstring'i "27 xlsx (59 kaynak CSV)" olarak netleştirildi, EN formatı ayıklandı.
- **F1-07 (KAPANDI):** `src/pipeline/test_pipeline.py:86` `test_pid_ham_xlsx_satirina_karsilik_gelir` testi eklendi ve doğrulandı.
- **F2-07 (KAPANDI):** `audit/degisim_gunlugu.md` F2 sonrası güncel sayılarla (`jump_resid_pct = 3.55`) güncellendi.
- **F2-08 (KAPANDI):** `src/clustering/build_events.py:468` TR ayı (`day_tr_start.dt.month`) kullanıyor, 34 tarım zinciri olayı belgelendi.
- **F2-09 (KAPANDI):** `metrics.json`'da MODIS dönemi için referans seyreklik notu ve `temizlik_modis_donemi_sanayi_tesis_payi = 0.666` eklendi.
- **F2-10 (AÇIK / DÜŞÜK; F5 denetçi düzeltmesi, F2 başlığıyla tek durum):** `src/harmonize/seri.py:207` hâlâ `between(2003, 2025)` (F5'te yeniden görüldü); hesaplamayı bozmuyor ama K9/K11'e aykırı.
- **F2-11 (AÇIK / DÜŞÜK; F5 denetçi düzeltmesi):** `docs/harmonizasyon_yontemi.md:177-179` tabloda EN ondalık (`30.63`, `[-23.49, 9.51]`) sürüyor.
- **F2-12 (AÇIK / DÜŞÜK; F5 denetçi düzeltmesi):** `grep -c "fark_aciklamasi\|loyo_folds" tools/check_all.py` → 0; C23 `aciklanmamis_fark: []` doğru ama check_all bu alanları sınamıyor.

### 3. Kabul Kriterleri ve Bağımsız Yeniden Hesaplama Özeti

- **`tools/check_all.py` (C01–C13, C23):** Tüm Faz 1 ve Faz 2 kontrolleri **GEÇTİ** (Toplam: 22 GEÇTİ, 0 KALDI, 3 ATLANDI [F5 raporları C22, C24, C25]).
- **`audit/yeniden_hesap.json` (C23 Bağımsız Hesap):** Bağımsız openpyxl/polars/pandas ile yapılan 100'ün üzerinde doğrulamada açıklanmamış **fark = 0** (Huni 1.414.674 = temiz 827.043 + anız 217.179 + statik 328.379 + sanayi 27.012 + deniz 8.848 + kalıcı belirsiz 6.208 + volkan 5; olay sayısı 471.978; C05 toplamı 380.975; LOYO MAPE 8.33%; artık sıçrama 3.55 pp).

### 4. Faz 1 & Faz 2 Kapanış Durumu

- **Açık yüksek:** 0
- **Açık orta:** 0
- **Açık düşük:** 3 (F2-10, F2-11, F2-12 kod kalitesi/belge inceltmesi, faz kapısını engellemez)
- **Sonuç:** Faz 1 ve Faz 2 veri ve çekirdek harmonizasyon gereksinimleri başarıyla tamamlanmış ve kapatılmıştır.


## F5 (F4 kapanışı + raporlar) — 2026-11-13

### F4 kapanış doğrulaması — kanıt benim komutlarımdan
- **F4-01 kapandı.** `current_month.parquet`: `esdeger_guvenilmez` (True 156 / False 1.780), `birincil_seri`, `guvensizlik_nedeni` eklendi; TR son tam ay `modis_esdeger` 903/532 = 1,70 ve `olay_esdeger` 705/381 = 1,85 → `esdeger_guvenilmez=True`, `birincil_seri=modis_temiz`. Uygulama (yerel `python -m http.server 8765`, Claude Browser, TR açılış): kutu "MODIS tespit (temiz) — Son tam ay 2026-10-01…31: 507; medyan 579; oran 88 yüzde"; altında "Eşdeğer güvenilmez: MODIS-eşdeğer olay oranı 185 yüzde … doğrulanmadı" ve "Ölçülen oranlar: MODIS 88, VIIRS 94". Sunucu ve sekme kapatıldı.
- **F4-02 kapandı.** Kutu matris serisini (olay_esdeger) izliyor, güvenilmezse birincil seriye düşüyor ve bunu yazıyor (`core.js:160-163`, `main.js:213-215`).
- **F4-03 kapandı.** Sıçrama tablosunda tek değer: "Harmonize … −41,4% (metrics.json)".
- **F4-04 kısmen.** (a) "(True)" yok, kapandı. (d) olay CSV'si `Math.round(x*1e5)/1e5` (`main.js:301`), kapandı. (b) ve (c) açık → F5-04.
- **F2-04** başlıkta ve "F1–F2 Kapanış" tablosunda tek durum: **kapandı (F5)**. Aynı bölümde F2-10/11/12 "BİLGİ" yazılmıştı, başlıklarla çelişiyordu; F5'te yeniden doğrulandı ve "AÇIK / DÜŞÜK" olarak düzeltildi (`seri.py:207 between(2003, 2025)`; `harmonizasyon_yontemi.md:177-179` EN ondalık; `check_all.py`'de `fark_aciklamasi|loyo_folds` 0 eşleşme).

### Raporlar
- **C22 (benim betiğim `audit/f5/c22_ornek.py`, tohum 2026):** raporlarda 460 etiketli sayı; rastgele 15'ten 14'ü `metrics.json` değeriyle eşleşti (`jump_raw_pct` 143,13; `loyo_mape` 8,33; `veri_toplam_nokta` 1.414.674; `events_total` 471.978; `guven_cift_sayisi` 40.368; `demo2_sanayi_nokta` 3.488; `takvim_mevcut_ay_oran_viirs_temiz_ub_TR` 0,243 …). Eşleşmeyen tek örnek sayı değil, bulgu tablosundaki "core.js:160" satır numarası (yanlış pozitif). Eski sayı (11.294, 10.088, 50.350, "R² = 0,95") 0 eşleşme.
- **Demo sayıları bağımsız (pandas, `events.parquet`/`points_status.parquet`):** 2021-07-28 75 olay (temiz 71 + anız 4), 8.568 tespit, en büyük Antalya 6.740 tespit 218,55 saat; İzmir sanayi 3.488 nokta = %5,27; olay 307.053 202 VIIRS / 0 MODIS / 270,68 MW; MODIS temiz ay medyanı Haz 1.214 > Eyl 1.104 > Ağu 998. Hepsi raporla aynı.
- **Abartı taraması:** "yapay zekâ" yalnız "yapay zekayla temizlendi değil" olumsuzlamasında; "risk" yalnız "risk değildir" tanımında; "hatasız/mükemmel" 0; "kusursuz" yalnız "kusursuz değil".
- **C25:** 33 kimliğin tamamı eşlenmiş (28 yapıldı, 5 kısmen); tüm kanıt yolları diskte var. N-05 ve U-16 F4-01 kapanınca `build_reports.py` ile "yapıldı" oldu; aşağıdaki F5-01/F5-02 bu kararı bozmuyor (özellik var, demo metni eksik).

### F5-01 · ORTA · Demo senaryoları 2 ve 5 uygulamada yazıldığı gibi yürümüyor — **KAPANDI** (`reports/demo_senaryolari.json`, `src/app/main.js`)
- **Gözlem ve kapanış:** `reports/demo_senaryolari.json` adımlarına `#dateResetBtn` (tarih sıfırlama), `#maxEvBtn` (en büyük olaya gitme) ve Senaryo 5 için `MODIS tespit (temiz)` seri seçimi eklendi; `src/app/main.js:378-381` içinde olayda bulunmayan bir durum (ör. `Sanayi`) seçilince ham nokta katmanı (`rawToggle`) kendiliğinden açılır ve `refreshRaw()` bölge/durum süzgeciyle çalışır.

### F5-02 · ORTA · Ham kod metni ve EN ondalık raporda ve ekranda — **KAPANDI** (`tools/build_reports.py`, `src/app/main.js:169-181`)
- **Gözlem ve kapanış:** `tools/build_reports.py:61-70` içinde `yorum_tr()` ve rapor şablonlarında `|t,yorum` değiştiricisiyle ham kod metinleri Türkçeye çevrildi; `src/app/main.js:169-174` içinde `humanYorum()` işlevi `i18n` sözlüğü ve `fmtN()` yerel ondalık biçimlendirmesiyle tüm alt çizgi/ASCII/nokta ondalık sorunlarını kapattı.

### F5-03 · DÜŞÜK · Etiket (C24) — türetilmiş sonuç "ölçüldü"
- **Gözlem:** `jump_harm_dogal_aralikta` = False, etiket **ölçüldü**; ama tahmini olan `jump_harm_pct` (−41,35, tahmini) üzerinden türetiliyor. Raporda "doğal aralıkta DEĞİL (hayır (ölçüldü))". "ayırt edilemezlik bayrağı 1 (ölçüldü)" bağlamsız. `check_all` C24 yalnız etiket varlığını sayıyor (not: "etiket içermeyen rapor"), yanlış etiketi yakalamıyor.
- **Öneri:** Tahmini girdiden türeyen bayraklar tahmini; C24'e "girdi etiketi ≥ çıktı etiketi" kuralı. **Sorumlu:** harmonizasyon/rapor-yazari; check_all koordinatör.

### F5-04 · DÜŞÜK · F4-04 kalıntıları — **KAPANDI** (`src/app/main.js:237-241`, `src/app/i18n/`)
- **Gözlem ve kapanış:** `renderRank()` içinde `fmtMed()` kullanımıyla ay sıralaması ile matris medyanları eşlendi ve eşitlenen yuvarlanmış değerler `≈` işaretini alıyor; `applyRegion()` haritayı seçili bölgeye yeniden odaklıyor (`MV.showRegion`).

**Kontroller (F5 kapanış güncellemesi):** **Açık yüksek: 0. Açık orta: 0.** Açık düşük: F2-10, F2-11, F2-12, F5-03.


## F3 — Arayüz ve Harita Denetimi (2026-11-13)

Kapsam: `src/app/` (`index.html`, `app.css`, `main.js`, `core.js`, `charts.js`, `mapview.js`, `lab.js`, `csv.js`, `i18n/tr.json`, `i18n/en.json`, `data/manifest.json`), `docs/arayuz_yontemi.md`, `audit/erisilebilirlik.json`, `audit/performans.json`, `referans/STIL_NOTU.md`, `docs/01_ISTEKLER.md` U-01..U-21.

### 1. Kabul Kriterleri Doğrulaması (C14–C21)
- **C14 (Ekran = hesap):** `GEÇTİ`. HTML içinde sabit yazılmış 3+ basamaklı sayı tespiti yok (`sabit_sayi_supheli: []`). Ekrandaki tüm metrikler `metrics.json` ve `data/` dosyalarından dinamik türetiliyor. F4'teki çalışma anı DOM karşılaştırmasında 72 matris hücresi, ay medyanları ve HUD değerleri `agg/metrics` ile fark 0 olarak doğrulanmıştı.
- **C15 (Yasak kalıp taraması):** `GEÇTİ`. 7 JS/HTML dosyası tarandı; `Math.random`, tohumlu rastgele, sabit R² veya tırnak içinde yüzde metni bulunmadı (`bulgular: []`).
- **C16 (Simülasyon izolasyonu):** `GEÇTİ`. Simüle veri dosyası yok (`manifest.json: "simulated": false`), arayüzde `#simBadge` varsayılan olarak gizli.
- **C17 (CSV kontrolleri):** `GEÇTİ`. `src/app/tests/csv_check.py` ve `src/app/csv.js` incelendi: UTF-8 BOM (`\ufeff`), formül enjeksiyon koruması (`'`, `=`, `@`, `+`, `-`), negatif sayıların korunumu ve `t_utc`/`t_tr` sütunları tam uyumlu.
- **C18 (TR/EN dil simetrisi):** `GEÇTİ`. `tr.json` ve `en.json` dosyalarının her ikisi de eksiksiz simetrik **279 anahtar** içeriyor (`yalniz_tr: []`, `yalniz_en: []`).
- **C19 (Erişilebilirlik):** `GEÇTİ`. `audit/erisilebilirlik.json` incelendi: etkileşimli öğeler, roving tabindex (sekme butonları ok tuşlarıyla gezinir, matris hücreleri roving tabindex), adsız etkileşimli 0 (oran 1.0), canlı bölgeler mevcut. Renk körlüğü (Machado 2009 simülasyonu) minimum CIE76 `dE = 14.0` (Viridis, Cividis, YlOrRd algısal rampalar, harita sınıfları hem renk hem şekille kodlu: ● daire, ■ kare, ▲ üçgen, ◆ baklava). Kontrast oranları WCAG AA eşiğini (4.5:1) aşıyor: zemin üstü metin 15.69:1, turkuaz buton üstü metin 11.56:1, matris hücresi minimum 4.59:1.
- **C20 (Performans):** `GEÇTİ`. `audit/performans.json` incelendi: 27 yıllık 302.863 temiz olay veri tabanında en düşük FRP eşik değişimi ortalama süresi **0.253 sn** (ölçümler: 301.6, 235.0, 262.6, 216.6, 247.6 ms). Hedef olan ≤ 5 sn kuralı fazlasıyla sağlanmıştır.
- **C21 (Çevrimdışı açılış):** `GEÇTİ`. Dış CDN (`http://`, `https://`, `//`) bağımlılığı sıfır (`dis_kaynak: []`). Leaflet ve yazı tipleri yerel dizinde. Harita çevrimdışı il sınırları GeoJSON ile çalışıyor; çevrimiçi uydu haritası açıldığında `#tileWarn` ile dürüst uyarı veriliyor.

### 2. Görsel Dil ve Kullanıcı İstekleri (U-01..U-21, STIL_NOTU.md)
- **Figma / NASA Koyu Tema:** `#070b10` ana zemin, `#0d141b` kart yüzeyleri, `#1b2630` ince kenarlıklar, `#5eead4` tek neon turkuaz vurgu, `#a99cff` / `#8b7cf6` ikincil mor vurgu, `#f5b455` uyarı rengi `app.css` içinde sade telemetri kartları (`.kart` üst vurgu şeritleri) ve üst başlıkla (`.top`) uygulanmıştır.
- **Düzen Mimarisi:** 4 telemetri özet kartı (`#cTotal`, `#cTop`, `#cCur`, `#cJump`), sol yapışkan süzgeç paneli (`.filters` + `<details id="adv">` gelişmiş süzgeçler), 4 erişilebilir sekme (`Takvim`, `Harita`, `Uydular nasıl birleştirildi`, `İndir`).
- **Bilimsel Seri Seçimi (Soru 3 Kararı):** `main.js:4` varsayılan olarak `S.aggSeries = "olay_esdeger"` seçilidir. `#sciModeBtn` üst başlıkta aktif MODİS-EŞDEĞER (BİLİMSEL) durumu gösterir, tıklandığında `toggleSciMode()` ile `#seriesSel` senkron biçimde `olay_esdeger` ↔ `olay` arasında geçiş yapar.
- **Hızlı CSV İndirme (`#quickExportBtn`):** Başlıkta turkuaz vurguyla konumlandırılmış; tıklandığında `exportEvents()` çağrılarak UTF-8 BOM, formül enjeksiyon kaçışı, `t_utc`, `t_tr`, `day_tr`, koordinat yuvarlama (float32 gürültüsüz) içeren CSV anında indirilir.
- **Veri Güvenilirliği:** Sabit yazılmış metrik, sahte R², `Math.random` veya sahte simülasyon verisi bulunmamaktadır.

### 3. Belge Doğrulaması (`docs/arayuz_yontemi.md` ↔ `metrics.json` / `esikler.json`)
- `jump_raw_pct`: `%143,13` = `143.13` (ölçüldü, tam uyumlu)
- `jump_harm_pct`: `-41,35%` = `-41.35` (tahmini, tam uyumlu)
- Gerçek MODIS sıçraması: `-44,9%` = `-44.9` (ölçüldü, tam uyumlu)
- `jump_resid_pct`: `+3,55` yp = `3.55` (tahmini, tam uyumlu)
- `loyo_ci95`: `[-23,49%, +9,51%]` = `[-23.49, 9.51]` (tahmini, tam uyumlu)
- `modis_frp50_genel_mw`: `64,88 MW` = `64.88` (tahmini, tam uyumlu)
- Kümeleme eşikleri: `D = 1 km`, `L = 3 pencere`, `Hmax = 72 saat` = `src/config/esikler.json` (tam uyumlu)
- Kontrast oranları (`15.69:1`, `11.56:1`, `8.85:1`, `4.59:1`) ve renk körlüğü `min_palet_dE = 14` = `audit/erisilebilirlik.json` (tam uyumlu)

---

### Faz 3 Bulguları

### F3-01 · DÜŞÜK · `docs/arayuz_yontemi.md:150` (C18 anahtar sayısı belge uyuşmazlığı) — **KAPANDI**
- **Gözlem:** `docs/arayuz_yontemi.md` Tablo 8 satır 150'de "251 anahtar" yazıyordu; gerçek sözlükle uyumlu olacak şekilde **279 anahtar** olarak düzeltildi.
- **Sorumlu:** arayuz-harita / koordinatör.

---

### Faz 3 Kapanış Özeti
- **Açık yüksek bulgu:** 0
- **Açık orta bulgu:** 0
- **Açık düşük bulgu:** 0 (F3-01 kapatıldı)
- **Sonuç:** Faz 3 (Arayüz ve Harita — `src/app/` ve `docs/arayuz_yontemi.md`) gereksinimleri, görsel dili, kabul kriterleri (C14–C21) ve bağımsız uyuşmazlık denetimleri başarıyla tamamlanmış ve **temiz kapanışla onaylanmıştır**.
