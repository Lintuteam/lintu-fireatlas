# Harmonizasyon yöntemi (F2, `harmonizasyon` ajanı)

Kod: `src/harmonize/` (`python src/harmonize/run_all.py`, ardından `python tools/build_metrics.py`).
Eşikler: `src/config/esikler.json → harmonizasyon` (K9). Ölçülen her sayı: `reports/metrics.json`
(anahtarlar aşağıda). Bu belgedeki sonuç tablosu **betikle** doldurulur (K1); elle yazılmış metrik yoktur.

## 0. Bir bakışta

**Basitçe:** İki termometremiz var. Eskisi (MODIS) kaba, yenisi (VIIRS) çok hassas; hassas olan
küçük ateşleri de görüyor, bu yüzden aynı yaz için üç-dört kat daha fazla "yangın" sayıyor.
Yıllar boyunca karşılaştırma yapabilmek için hassas termometrenin ölçümünü eski termometrenin
diline çeviriyoruz ("MODIS görseydi kaç sayardı?"). Hassas ölçüm de çöpe gitmiyor: yanında
ayrı bir katman olarak duruyor.

**Teknik olarak:** İki çıktı (U-04): (a) **MODIS-eşdeğer seri** — 2012 öncesi gerçek MODIS
(Terra+Aqua), 2012 sonrası VIIRS'ten türetilmiş MODIS-eşdeğer tespit sayısı (tamsayı + %95 bant);
(b) **ham VIIRS** serisi ve nokta düzeyinde `match_nokta` (ortak / yalnız MODIS / yalnız VIIRS).
Enerji (toplam FRP) alternatif serisi aynı tabloda. İki birim üretilir: **tespit** (ay × 7 bölge) ve
**olay** (ay × il; `kumeleme` olayları, §10). Analiz kümesi temizlik ajanının `status` etiketidir:
varsayılan **temiz** (anız hariç), ikinci varyant **temiz_aniz**.

## 1. Eşleştirme birimi: MODIS ayak izi (U-02)

**Basitçe:** MODIS'in her pikseli yerde bir dikdörtgen kaplar; tarama kenarına doğru bu dikdörtgen
büyür (4,8 km'ye kadar). Her VIIRS noktasını, yakın zamanda geçmiş MODIS'in dikdörtgenine
bağlıyoruz. Böylece "MODIS'te 1, VIIRS'te 4 yangın" aynı hücrede toplanır.

**Teknik olarak** (`eslestirme.py`):
- Ayak izi = MODIS merkezinde `scan` (doğu-batı) × `track` (kuzey-güney) km dikdörtgen, her yöne
  `eslesme_tamponu_km` (VIIRS yarım pikseli payı) eklenir. Yörünge eğimi (~10°) ihmal edildi;
  tampon bu sapmayı da karşılar (sınırlama).
- Zaman: |Δt| ≤ `mcell_zaman_penceresi_saat` (Terra ile VIIRS arasındaki 2–3,6 saat farkı dahil).
- **Kenar / üst üste binme kuralı:** bir VIIRS noktası birden çok ize düşerse sırasıyla
  (1) eşzamanlı (|Δt| ≤ kalibrasyon penceresi) iz, (2) en küçük normalize uzaklık
  d = max(|dx|/(scan/2+tampon), |dy|/(track/2+tampon)), (3) en küçük |Δt|, (4) en küçük alan.
  Nokta her zaman **tek** hücreye gider; FRP bölünmez (çift sayım yok).
- **VIIRS pikselinin iki MODIS hücresine taşması:** nokta merkezi kuralı; tampon yarım piksel
  taşmayı yakalar.
- İze düşmeyen VIIRS noktası (yalnız VIIRS) → yedek **sabit 0,01° ızgara** hücresi. Her nokta
  ayrıca karşılaştırma için `mcell_izgara` alır.
- Çıktı: `data/processed/points_mcell.parquet` (`pid, mcell, mcell_tur, mcell_izgara, modis_pid,
  dt_dk, dnorm, n_aday_iz, match_nokta, conf_cls_ogr`), tüm 1.414.674 nokta (K3).
- Ayak izi ile sabit ızgara karşılaştırması: `mcell_iz_basina_viirs`, `mcell_iz_basina_izgara`,
  `mcell_izgarada_bolunen_oran` (sabit ızgara aynı MODIS pikselini kaç parçaya bölerdi).
- `kumeleme` ile uzlaşma: sözleşme §5 tanımı aynen uygulandı (ayak izi + yarım piksel tamponu,
  ızgara yedeği). `kumeleme` kendi eşleştirmesini aynı tanımla yapar; `mcell`'i beklemez.

## 2. Güven yüzdelik eşleştirmesi (U-01, U-05, Yusuf'un S1 isteği)

**Basitçe:** "VIIRS 'düşük' derken MODIS yüzde kaç diyor?" sorusunu, aynı yangına aynı anda bakan
uydu çiftleriyle cevapladık: Aqua (öğleden sonra 13:30) ve VIIRS uyduları (yine 13:30). Sonra
MODIS yüzdesini, VIIRS'in düşük/normal/yüksek paylarına denk gelecek yerlerden kestik.
**Sonuç dürüstçe:** sınırlar çok kararlı çıktı ve FIRMS'in kendi cetveline (0–29/30–79/80–100)
çok yakın; ama tek bir yangın düzeyinde iki uydunun güveni **zayıf ilişkili**. Yani "VIIRS düşük"
dediğinde MODIS'in de düşük demesini bekleyemeyiz: VIIRS'in "düşük"ü çoğu zaman zayıf yangın
değil, güneş yansıması / doygunluk gibi özel durumları işaretler (gündüz VIIRS 'l' noktalarının
FRP medyanı 'n'den yüksek; gece 'l' sınıfı neredeyse yok).

**Teknik olarak** (`guven_esleme.py`):
- Çift: Aqua tespiti + ayak izi içinde |Δt| ≤ `kalibrasyon_zaman_penceresi_dk` VIIRS noktaları,
  status ∈ {temiz, aniz} (gerçek yangın noktaları). Her Aqua tespitine izindeki VIIRS noktalarının **en yüksek** sınıfı (MODIS pikseli tüm
  alt pikselleri kapsar). Alternatif "en büyük FRP'li noktanın sınıfı" kuralı denendi; sıra ilişkisi
  daha zayıf çıktı (iki kuralın Spearman değerleri §9'da) — bu seçim veriye bakılarak yapıldı,
  şeffaflık için yazıyoruz.
- Eşit yüzdelik eşleme: VIIRS payları p_l, p_n; MODIS sınırları c1, c2 tamsayıları
  F_MODIS(c1) ≈ p_l, F_MODIS(c2) ≈ p_l + p_n.
- Kararlılık: her yıl dışarıda bırakılarak yeniden öğrenildi (aralık aşağıda).
- **Bağımsız sınama (K4):** dışarıda bırakılan yılda öğrenilmiş sınıf ile FIRMS sınıfının VIIRS
  sınıfıyla uyumu (doğru sınıf oranı, Cohen kappa). Öğrenilmiş eşleme FIRMS'i **geçmedi**.
- Yazıldığı yer (K10): `esikler.json → harmonizasyon.ogrenilen_guven_esleme`; uygulayan tek işlev
  `config.ogrenilen_guven_sinifi_seri`; sütun `points_mcell.conf_cls_ogr`. Ham sınıf `conf_cls`
  (FIRMS) değişmedi; ikisi karıştırılmaz. Etiket: **tahmini (düşük güven)**.
- Öneri: arayüzde varsayılan ham FIRMS sınıfı; öğrenilmiş eşleme "ortak dil" seçeneği olarak,
  yukarıdaki uyarıyla.

## 3. Hücre FRP toplamı ve MODIS tespit sınırı (U-05)

**Basitçe:** Aynı geçişte birbirine 1 km'den yakın VIIRS noktalarını birleştirip "MODIS büyüklüğünde
hücre" yapıyoruz ve hücredeki toplam yangın gücünü (FRP) topluyoruz. Sonra soruyoruz: hücrenin
gücü ne olunca Aqua onu yarı yarıya görüyor? Bu, MODIS'in "görme eşiği"dir ve veriden öğrenilir.

**Teknik olarak** (`seri.py: hucreler, frp50`):
- Hücre: aynı yörünge geçişinde (`gecis_ayirma_dk`) `hucre_baglanti_km` ile zincirlenen VIIRS
  noktaları (bağlı bileşenler).
- FRP50: P(Aqua hücreyi görür | log10 ΣFRP) lojistik regresyonunda 0,5 noktası. Yalnız Aqua ile
  eşzamanlı eşleşme veren geçiş × bölgeler kullanıldı (Aqua şeridi vekili; swath ürünü yok).
  Gündüz/gece, mevsim × gündüz/gece ve bölge için ayrı ayrı (`data/interim/harmonize/seri_olcum.json`).
- Yorum: bu bir **etkin** sınırdır (tarama açısı, ≤60 dk zaman farkı, bulut kayması dahil); MODIS'in
  fiziksel algılama sınırından büyüktür. Etiket **tahmini**. Gece sınırı gündüzden belirgin düşük
  (gece arka plan soğuk, kontrast yüksek) — fiziksel olarak beklenen yönde.

## 4. Gözlem eforu (uydu sayısı)

**Basitçe:** 2018'de ikinci, 2023'te üçüncü VIIRS uydusu eklendi. Üç göz bir gözden çok yangın
sayar; bu yangın arttı demek değildir. Bu yüzden VIIRS'i "gözleyen uydu başına" sayıyoruz.

**Teknik olarak** (`seri.efor_normalize`): her gün VIIRS toplamı, `coverage.parquet`'te o gün
`observed=True` olan VIIRS uydu sayısına bölünür; gözlemsiz günler ay içi ortalamayla ölçeklenir.
Etkisi ayrı ölçüldü: NOAA-20 (2018) ve NOAA-21 (2023) eklenişinde ham VIIRS toplamı ile eforlu
seri ve gerçek MODIS değişimi yan yana (aşağıda). **Yörünge kayması (F2-04):** Aqua'nın gündüz geçişi yıllar içinde geç saate kaydı
(`aqua_gunduz_gecis_utc_2015` → `aqua_gunduz_gecis_utc_2026`; Terra ters yönde erkene). Kayma 2024'ten
sonra hızlandı ve Aqua ile VIIRS (13:30) arasındaki zaman farkını büyüttü: |Δt| ≤ 60 dk eşzamanlı çift
payı (`aqua_viirs_esz_cift_payi_<yıl>`) 2025 ve özellikle 2026'da sert düştü (yıllık tablo §9'da, betikle
üretilir; sayılar orada). Kayma modellenmedi. Sonuç:
2026 eşdeğer değerleri eğitim rejiminin dışındadır, `bayrak = kismi_yil_nrt;aqua_yorunge_kaymasi`
ve etiket **tahmini (düşük güven)** taşır; 2026 bant kapsaması ayrı metriktir (`harm_2026_bant_kapsama`).
MODIS sona erince (Terra 2027, Aqua ~2027) seri tamamen 2012–2025 kalibrasyonuna dayanacaktır.

## 5. Üç yöntemin yarışı (K8)

**Basitçe:** Üç tarif denedik. Her yıl bir yılı sakladık, kalan yıllarla öğrenip saklanan yılı
tahmin ettik; gerçek MODIS ile karşılaştırdık. **Dürüst sonuç:** uydu sayısını düzeltmek (efor) asıl
kazançtır; bölge × mevsim × büyüklük oranı (ii), tek oranlı (i)'den ay × bölgede ayırt edilemez,
yıllık toplamda ise (i) daha iyidir. (ii) ana yöntem olarak kaldı çünkü uygulama ay × bölge takvimi
gösterir (koordinatör kararı, F2-03); bu bir üstünlük iddiası değildir.

**Teknik olarak** (hedef: Terra+Aqua tespiti, ay × 7 coğrafi bölge, status = temiz; temiz_aniz varyantı aynı yöntemle):
- (i0) tek sabit oran, efor yok — B-04 tuzağının kendisi, yalnız kıyas için.
- (i) tek sabit oran, eforlu.
- (ii) bölge × mevsim × FRP büyüklük sınıfı (`frp_sinif_sinirlari_mw`) oranı, eforlu; az örnekli
  tabakada (`min_ornek`) mevsim × büyüklüğe düşülür.
- (iii) FRP eşik eğrisi g(ΣFRP) = hücre başına beklenen Aqua tespiti (log-FRP kutuları; bölge ×
  mevsim × gündüz/gece, hiyerarşik), yalnız-MODIS payı f_u (uydu × gündüz/gece × mevsim) ve Terra
  payı k_TA (bölge × mevsim × gündüz/gece, MODIS'in kendi verisinden), eforlu.
- Test: 2012–2025 her yıl dışarıda (LOYO, `loyo_test_yillari`). 2026 kısmi yıl + NRT (`type` yok)
  olduğu için testte değil; tahmini **düşük güven** etiketli.
- **Seçim ölçütü:** en düşük ay × bölge WAPE (uygulamanın kullanım birimi). Gerekçe: tek oran tuzağı
  (B-04) yıllık toplamda saklanabilir, mevsim × bölge düzeyinde ortaya çıkar. Ölçüt sonuçlardan önce
  belgeye yazıldı ama klasör git'te izlenmediği için bu doğrulanamaz; seçim LOYO sonuçları üzerinde
  yapıldığından kazananın hatası hafif iyimser olabilir (seçim etkisi). (ii) ile (i) arasındaki fark
  yıl bootstrap'ıyla sınandı (`harm_ii_eksi_i_wape_ci95`); (i)'nin yıllık sonuçları da metrik olarak
  yayımlanır (`harm_i_*`). Tespit düzeyinde (ii)'nin (i)'yi yendiği söylenemez.
- 7 bölge: geleneksel coğrafi bölgeler (`ortak.BOLGE7`); mevsim: Ara–Şub kış, Mar–May ilkbahar,
  Haz–Ağu yaz, Eyl–Kas sonbahar.

## 6. Belirsizlik bandı, eski dönem, tamsayı

- Bant: LOYO artıklarının log((gerçek+1)/(tahmin+1)) %2,5–%97,5 yüzdelikleri, tahmin büyüklüğüne
  göre 3 kutu; ay × bölge ve ay × ülke düzeyi ayrı. Kapsama dürüst ölçüldü: her yılın bandı diğer
  yılların artıklarından kurulup o yılda sınandı. Yıllık bant: yıllık LOYO hata yüzdelikleri.
- **Eski dönem (2000 – Temmuz 2002, yalnız Terra):** nokta değer **düzeltilmez** (gerçek Terra
  sayısı), `bayrak = eski_donem_yalniz_terra`, etiket "tahmini (düşük güven)", üst bant 2003–2011
  ülke × mevsim Aqua/Terra oranının %97,5'iyle genişletilir. Bu yıllar sonrakilerle **doğrudan
  karşılaştırılamaz** (yaklaşık yarı efor).
- Tüm sayılar tamsayıdır (`ana_seri, ana_alt, ana_ust, modis_esdeger, ...`); enerji MW'dır.
- `data/processed/agg/harmonized.parquet` şeması §10'da.

## 7. Sıçrama (C10, U-15)

**Basitçe:** 2012'de VIIRS devreye girdiğinde ham seri bir anda fırlıyor. Harmonize seri bu yapay
sıçramayı yok etmeli, ama gerçek değişimi de saklamamalı.

**Teknik olarak:** sıçrama = (2012–2014 ortalaması) / (2009–2011 ortalaması) − 1. Harmonize seride
2012 sonrası değerler **LOYO tahminleridir** (o yıl öğrenmede yoktu). Doğal değişim dağılımı:
MODIS serisinde geçiş dışı tüm 3+3 yıllık pencereler (2003–2025). Ek olarak, gerçek MODIS'in aynı
penceredeki değişimi verilir: harmonizasyonun **eklediği** sıçrama = harmonize − gerçek MODIS.

## 8. Sınırlamalar

- Olay düzeyinde yalnız (i0), (i), (ii) koşuldu; (iii) tespit düzeyinde kaybettiği için olayda denenmedi.
- Olay il düzeyi bandı il × ay artıklarından; bölge düzeyinde olay bandı verilmez (bantlar toplanamaz).
- İlk teslim (type 0/−1 süzgeci) sayıları geçersizdir; şimdiki sayılar `status` kümesiyle üretildi.
- Swath/bulut verisi yok (gözlem kapsamı çıkarım, tahmini). Yörünge eğimi ihmal.
- %95 aralıklar 14 yıllık LOYO'dan; kaba (yüzdelikler uç değerlere yakın).
- "Yangın arttı/azaldı" iddiası bu seriden ancak bant dışına taşan değişimlerle ve "tahmini"
  etiketle yapılabilir.

## 9. Sonuçlar (otomatik)

<!-- OTOMATIK:BASLA -->
_Üretildi: 2026-11-13 06:53 — `src/harmonize/run_all.py`; değerler `reports/metrics.json` ile aynıdır._

**Yöntem yarışı (LOYO 2012–2025, hedef Terra+Aqua tespit):**

| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Yıllık sapma % | Yıllık %95 hata aralığı |
|---|---|---|---|---|---|
| (i0) sabit oran, efor yok | 52.68 | 42.12 | -1.7204 | 5.03 | [-46.83, 86.91] |
| (i) sabit oran, eforlu | 30.64 | 4.83 | 0.9675 | 0.15 | [-7.81, 9.46] |
| (ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu | 30.63 | 8.33 | 0.8716 | 0.55 | [-23.49, 9.51] |
| (iii) FRP eşik eğrisi + yalnız-MODIS payı + Terra payı, eforlu | 31.91 | 10.91 | 0.7644 | 3.76 | [-13.0, 31.69] |

Ana yöntem (en düşük ay × bölge WAPE): **(ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu**. **Dürüst okuma:** (ii) ile uydu-normalize sabit oran (i) ay × bölgede ayırt edilemez (WAPE 30.63 vs 30.64; yıl bootstrap'ıyla (ii)−(i) farkı %95 aralığı [-2.97, 4.26] puan); (i) yıllık toplamda daha iyi (MAPE 4.83 vs 8.33; %95 [-7.81, 9.46] vs [-23.49, 9.51]); ikisi de normalize edilmemiş tek orandan (i0) çok iyi (WAPE 52.68). (ii) uygulamanın kullanım birimi ay × bölge olduğu için ana yöntem bırakıldı (koordinatör kararı); bu bir üstünlük iddiası değildir. Ölçüt belgede sonuçlardan önce yazıldı ama git kaydı olmadığından bu doğrulanamaz; kazananın hatası seçim etkisiyle hafif iyimser olabilir. C10 artığı (i) ile: 1.24 yp.

**Eşdeğer seri (C11):** çakışma toplam sapması `equiv_overlap_bias` = -0.52 %; aylık ülke hata bandı `equiv_overlap_band` = [-59.57, 74.99] %; bant kapsaması (LOYO) ay×bölge 0.9557, ay×ülke 0.9226.

**Sıçrama (C10), geçiş 2012, 3+3 yıl:**

| Seri | Sıçrama % |
|---|---|
| Ham (MODIS → MODIS+VIIRS tüm tespit) | 143.13 |
| Ham (MODIS → yalnız VIIRS) | 88.03 |
| Harmonize (LOYO MODIS-eşdeğer) | -41.35 |
| Gerçek MODIS (aynı pencere) | -44.9 |
| Harmonizasyonun eklediği (harmonize − gerçek MODIS) | 3.55 yüzde puan |

Doğal değişim %95 aralığı (`jump_null_ci95`, 17 pencere): [-39.3, 92.61]. Harmonize sıçrama bu aralıkta mı: **HAYIR**.
Eski C10 ölçütü (bilgi amaçlı) **sağlanmıyor**: 2009–2011 MODIS'in kendi kayıtlarında olağan dışı yüksek yıllardır; gerçek MODIS de aynı pencerede doğal aralığın dışına düşüyor.

**C10 ANA ölçütü (koordinatör kararı):** artık sıçrama `jump_resid_pct` = harmonize sıçrama − aynı penceredeki gerçek MODIS değişimi (`jump_modis_real_pct`); yıllık LOYO %95 hata aralığı `loyo_ci95` içinde olmalı. Ana varyant: **birim = tespit, küme = temiz**.
Değer: 3.55 yüzde puan; aralık [-23.49, 9.51] → **SAĞLANIYOR**.

**Varyantlar (bilgi; aynı LOYO ve sıçrama tanımı):**

| Birim | Küme | Kazanan | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | loyo_ci95 | Ham sıçrama % | Harmonize % | Gerçek MODIS % | Artık (yp) |
|---|---|---|---|---|---|---|---|---|---|---|
| tespit | temiz | ii | 30.63 | 8.33 | 0.8716 | [-23.49, 9.51] | 143.13 | -41.35 | -44.9 | 3.55 |
| olay | temiz | ii | 32.8 | 7.51 | 0.8443 | [-15.36, 13.73] | 51.72 | -54.23 | -53.45 | -0.78 |
| tespit | temiz_aniz | ii | 30.88 | 8.27 | 0.8988 | [-20.95, 13.19] | 113.44 | -49.17 | -52.29 | 3.12 |
| olay | temiz_aniz | ii | 32.48 | 7.53 | 0.8718 | [-14.54, 18.05] | 42.1 | -58.65 | -59.01 | 0.36 |

**Yörünge kayması ve eşzamanlı çift payı (F2-04):** gündüz geçiş saati medyanı (UTC) ve Aqua-VIIRS aday çiftlerinde |Δt| ≤ kalibrasyon penceresi payı. Aqua'nın geç kayması kalibrasyon çiftlerini azaltır; 2026 değerleri düşük güven bayraklıdır (`kismi_yil_nrt;aqua_yorunge_kaymasi`). 2026 bant kapsaması: 0.545.

| Yıl | Terra | Aqua | SNPP | N20 | N21 | Aqua-VIIRS eşzamanlı çift payı |
|---|---|---|---|---|---|---|
| 2000 | 8.87 |  |  |  |  |  |
| 2001 | 8.73 |  |  |  |  |  |
| 2002 | 8.65 | 10.75 |  |  |  |  |
| 2003 | 8.65 | 10.77 |  |  |  |  |
| 2004 | 8.72 | 10.87 |  |  |  |  |
| 2005 | 8.63 | 10.75 |  |  |  |  |
| 2006 | 8.63 | 10.78 |  |  |  |  |
| 2007 | 8.65 | 10.8 |  |  |  |  |
| 2008 | 8.75 | 10.92 |  |  |  |  |
| 2009 | 8.65 | 10.85 |  |  |  |  |
| 2010 | 8.63 | 10.72 |  |  |  |  |
| 2011 | 8.73 | 10.8 |  |  |  |  |
| 2012 | 8.65 | 10.8 | 10.67 |  |  | 0.867 |
| 2013 | 8.63 | 10.72 | 10.6 |  |  | 0.858 |
| 2014 | 8.55 | 10.8 | 10.73 |  |  | 0.874 |
| 2015 | 8.55 | 10.7 | 10.6 |  |  | 0.839 |
| 2016 | 8.55 | 10.68 | 10.52 |  |  | 0.861 |
| 2017 | 8.55 | 10.68 | 10.6 |  |  | 0.872 |
| 2018 | 8.67 | 10.8 | 10.62 | 10.6 |  | 0.858 |
| 2019 | 8.63 | 10.7 | 10.52 | 10.6 |  | 0.825 |
| 2020 | 8.65 | 10.7 | 10.6 | 10.58 |  | 0.861 |
| 2021 | 8.6 | 10.7 | 10.62 | 10.6 |  | 0.812 |
| 2022 | 8.55 | 10.88 | 10.63 | 10.62 |  | 0.855 |
| 2023 | 8.28 | 10.98 | 10.62 | 10.6 | 10.57 | 0.854 |
| 2024 | 7.95 | 11.37 | 10.5 | 10.57 | 10.53 | 0.721 |
| 2025 | 7.82 | 11.92 | 10.67 | 10.6 | 10.62 | 0.487 |
| 2026 | 7.33 | 12.65 | 10.82 | 10.77 | 10.53 | 0.182 |

**Olay/tespit tutarlılığı (F2-01):** olay eşdeğeri tespit eşdeğerini aşamaz; aşan hücreler kırpıldı: temiz_ay_bolge 98, temiz_ay_TR 6, temiz_yil_TR 0, temiz_aniz_ay_bolge 93, temiz_aniz_ay_TR 6, temiz_aniz_yil_TR 0.

**VIIRS içi uydu eklenişleri (efor normalizasyonunun etkisi):**

| Geçiş | Ham VIIRS % | Eforlu VIIRS % | Gerçek MODIS % |
|---|---|---|---|
| NOAA-20 2018 (3+3) | 24.34 | -37.31 | -41.59 |
| NOAA-21 2023 (2+2) | 110.19 | 44.29 | 31.01 |

**Güven eşlemesi (S1):**

- Çift sayısı 40368; VIIRS payları {'p_dusuk': 0.0524, 'p_nominal': 0.7102, 'p_yuksek': 0.2374}.
- Öğrenilmiş MODIS sınırları: düşük 0–35, nominal 36–82, yüksek 83–100 (FIRMS: 0–29 / –79 / –100).
- LOYO kararlılığı: c1 [34, 36], c2 [81, 82] (15 yıl).
- Bağımsız sınama: doğru sınıf oranı öğrenilmiş 0.6457 / FIRMS 0.6485; kappa 0.1765 / 0.1918; öğrenilmiş daha iyi olduğu yıl 7/15.
- Sıra ilişkisi (Spearman): en yüksek sınıf kuralı 0.2138, en büyük FRP kuralı 0.006.
- Gündüz/gece ayrı: {'D': {'c1': 37, 'c2': 80, 'n': 35786, 'p_dusuk': 0.059, 'p_nominal': 0.702, 'p_yuksek': 0.239}, 'N': {'c1': 0, 'c2': 99, 'n': 4582, 'p_dusuk': 0.0, 'p_nominal': 0.777, 'p_yuksek': 0.223}}.

| VIIRS sınıfı | n | MODIS %5 | %25 | medyan | %75 | %95 |
|---|---|---|---|---|---|---|
| dusuk | 2116 | 39.0 | 61.0 | 72.0 | 82.0 | 98.0 |
| nominal | 28668 | 34.0 | 55.0 | 67.0 | 77.0 | 96.0 |
| yuksek | 9584 | 41.0 | 65.0 | 79.0 | 93.0 | 100.0 |

**MODIS (Aqua) etkin tespit sınırı FRP50 (tahmini):**

| Tabaka | FRP50 MW | eğim | hücre | tespit oranı |
|---|---|---|---|---|
| genel | 64.88 | 1.6 | 137801 | 0.233 |
| dn=D | 73.98 | 1.535 | 125994 | 0.2303 |
| dn=N | 20.54 | 2.371 | 11807 | 0.2615 |
| ilkbahar/D | 35.16 | 2.014 | 5186 | 0.2019 |
| ilkbahar/N | yetersiz örnek | | | |
| kis/D | 48.54 | 1.641 | 22304 | 0.2077 |
| kis/N | yetersiz örnek | | | |
| sonbahar/D | 80.26 | 1.457 | 67606 | 0.2257 |
| sonbahar/N | 12.65 | 3.211 | 2014 | 0.2498 |
| yaz/D | 75.15 | 1.829 | 30898 | 0.2616 |
| yaz/N | 22.85 | 2.267 | 9712 | 0.261 |
| bolge=Akdeniz | 61.32 | 1.732 | 26213 | 0.2412 |
| bolge=DoguAnadolu | 26.11 | 1.966 | 4243 | 0.3783 |
| bolge=Ege | 23.0 | 2.205 | 5772 | 0.3604 |
| bolge=Guneydogu | 101.89 | 1.419 | 67254 | 0.2055 |
| bolge=IcAnadolu | 67.45 | 1.617 | 23438 | 0.2176 |
| bolge=Karadeniz | 16.6 | 2.179 | 2467 | 0.3741 |
| bolge=Marmara | 31.28 | 1.801 | 8414 | 0.2684 |

**Eşleştirme birimi:** VIIRS noktası 1154967, MODIS izinde 174203, çoklu ize düşen (kural ile teke) 81418; iz başına VIIRS 3.349, aynı iz sabit ızgarada 1.764 hücreye dağılırdı (bölünen iz oranı 0.4655).
<!-- OTOMATIK:BITIR -->

## 10. Olay düzeyi seri ve `harmonized.parquet` şeması (takvim ve arayüz için)

**Basitçe:** Aynı yangını iki uydu ayrı ayrı "görse" de bir olay sayılır (`kumeleme`). Burada "MODIS bu
ayda bu ilde kaç yangın olayı görürdü?" sorusunu, VIIRS'in gördüğü olaylardan tahmin ediyoruz.

**Teknik olarak** (`olay.py`): gerçek = `n_modis > 0` olan olaylar (ortak + yalnız MODIS); VIIRS
özelliği = olaydaki VIIRS FRP toplamının sınıfı; efor = her VIIRS uydusunun gördüğü olay, o uydunun
olaydaki ilk gününde, gözleyen uydu başına. Yöntem (ii): bölge × mevsim × VIIRS FRP sınıfı oranı +
yalnız-MODIS olay payı (bölge × mevsim). Seçim ve LOYO tespit düzeyiyle aynı. Eski dönem üst bandı:
2003–2011'de yalnız Aqua'nın gördüğü olayların Terra'nın gördüklerine oranı (mevsim, %97,5).

**C10 ana ölçütü:** `jump_resid_pct` (birim = tespit, küme = temiz) `loyo_ci95` içinde. Diğer üç
varyantın değerleri `<birim>_<kume>_*` anahtarlarıyla bilgi amaçlıdır.

Tablo: `data/processed/agg/harmonized.parquet` — bir satır = (birim, küme, düzey, yer, yıl, ay).

| Sütun | Tip | Anlam |
|---|---|---|
| `birim` | str | `tespit` / `olay` |
| `kume` | str | `temiz` (varsayılan) / `temiz_aniz` |
| `duzey` | str | tespit: `ay_bolge`, `ay_TR`, `yil_TR`; olay: `ay_il`, `ay_TR`, `yil_TR` |
| `yil`, `ay` | int | TR günü yılı/ayı (K11); `yil_TR` satırlarında `ay = 0` |
| `bolge7` | str | 7 coğrafi bölge; ülke satırlarında `TR` |
| `il` | str | olay `ay_il` satırlarında il adı; ülke satırlarında `TR`; tespit bölge satırlarında boş |
| `ana_seri` | int | **Gösterilecek seri**: 2012 öncesi gerçek MODIS, sonrası VIIRS'ten MODIS-eşdeğer |
| `ana_alt`, `ana_ust` | int | %95 belirsizlik bandı (2003–2011 gerçek MODIS'te alt = üst = değer) |
| `ana_kaynak` | str | `modis_gercek` / `viirs_modis_esdeger` |
| `modis_gercek` | Int64 | Gerçek MODIS (Terra+Aqua) tespit/olay sayısı (karşılaştırma için, 2012 sonrası da) |
| `modis_terra`, `modis_aqua` | Int64 | Tespit biriminde uydu kırılımı; olayda boş |
| `modis_esdeger`, `esdeger_alt`, `esdeger_ust` | Int64 | 2012+ VIIRS'ten MODIS-eşdeğer (LOYO tahmini; 2026 tüm test yıllarıyla) ve bandı |
| `viirs_ham` | Int64 | Ham VIIRS tespit / olay sayısı (tüm uydular, ayrıntı katmanı U-04) |
| `viirs_uydu_basina` | Int64 | Gözleyen uydu başına (eforlu) VIIRS sayısı |
| `frp_modis_mw`, `frp_viirs_uydu_basina_mw` | float | Enerji serisi (yalnız tespit biriminde) |
| `bayrak` | str | `eski_donem_yalniz_terra` (2000–Tem 2002), `kismi_yil_nrt` (2026), boş |
| `etiket` | str | `ölçüldü` / `tahmini` / `tahmini (düşük güven)` (K5) |
| `yontem` | str | Kazanan yöntemin adı |

Kullanım: takvim/arayüz varsayılan olarak `birim='olay', kume='temiz'` ve `ana_seri` + bant gösterir;
ham VIIRS katmanı `viirs_ham`; olay düzeyindeki ortak / yalnız MODIS / yalnız VIIRS kırılımı
`events.parquet → match_class`'tadır. Tüm sayılar tamsayıdır; ondalık gösterilmez.
