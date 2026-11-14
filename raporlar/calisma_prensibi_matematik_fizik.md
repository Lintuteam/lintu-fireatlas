# Uygulama Nasıl Çalışır? Matematiksel ve Fiziksel Çalışma Prensibi

NASA Space Apps 2026 · MODIS–VIIRS Türkiye Yangın Aktivite Takvimi (v2.2) · Üretim tarihi: 2026-11-13

> **Okuma kılavuzu.** Bu rapor, uygulamanın arkasındaki fiziği ve matematiği formüllerle anlatır. Sayıların kaynağı `belgeler_ve_denetim/yontem_ozeti.md`, `arayuz/data/metrics.json` (`metrics` anahtarı) ve `belgeler_ve_denetim/gercek_dogrulama.{md,json}` dosyalarıdır; her sayının yanında dürüstlük etiketi ve (varsa) `metrics.json` anahtarı yazılıdır: **ölçüldü** (veriden sayıldı/hesaplandı), **tahmini** (modele, kurala veya çıkarıma dayanır), **doğrulanmadı** (bağımsız kanıt yok). Formüller okunabilir Unicode ile yazılmıştır. Belgelerde olmayan bir şey **"belgede yok"** diye açıkça belirtilir; dış kaynaklara dayanan bilgiler **"literatürden"** diye işaretlenir ve §11'de künyesi verilir.
>
> "Aktivite" her yerde *tarihsel sıcak nokta (hotspot) yoğunluğu* demektir; yangın riski veya tehlike tahmini değildir.
>
> **Bu oturumda ölçülen yeni sayılar** (2009–11 ve 2012–14 penceresi, temiz status, Türkiye; yıllık değerler ve kümeleme aşaması) `metrics.json` içinde henüz anahtar olarak yer almaz; bu raporda "(ölçüldü, bu oturum)" veya "(tahmini, bu oturum)" diye anılır. "Orman yangını adayı" sayıları da aynı durumdadır.

---

## 1. Fiziksel temel

### 1.1 Uydu yangını değil, sıcaklığı görür

Aktif yangın ürünleri (MODIS, VIIRS) termal kızılötesi ölçümden türetilir. Sıcak bir yüzey Planck yasasına göre ışıma yapar; yanma sıcaklığındaki (kabaca 800–1200 K, *literatürden*) bir yüzey, ~300 K'lik arka plana göre orta dalga kızılötesinde (MIR, ~4 µm) kat kat parlaktır. Algoritma, bir pikselin 4 µm parlaklık sıcaklığını çevre piksellerin istatistiğiyle karşılaştırır; belirgin biçimde sıcaksa o pikseli "sıcak nokta" (hotspot) ilan eder (*literatürden*: Kaufman vd. 1998; Giglio vd. 2016; Schroeder vd. 2014). Algoritmanın iç eşikleri (bağlamsal test değerleri) proje belgelerinde türetilmemiştir (belgede yok).

### 1.2 Yangın ışınım gücü (FRP): Stefan–Boltzmann

FRP (Fire Radiative Power, megavat, MW), yangının anlık yaydığı ışınım gücüdür. Kara cisim yaklaşımıyla (*literatürden*; uygulamanın bilim sekmesindeki ifadeyle aynıdır):

```
FRP = ε · σ · A_yangın · (T_yangın⁴ − T_arka⁴)
```

- ε: yayıcılık (0–1), σ = 5,67×10⁻⁸ W m⁻² K⁻⁴ (Stefan–Boltzmann sabiti), A_yangın: yanan alan (m²), T: mutlak sıcaklık (K).
- Gücün sıcaklığın **4. kuvvetiyle** artması, küçük ama çok sıcak bir alanın büyük ama serin bir alandan fazla ışıma yapabilmesinin sebebidir.
- Uyduda A_yangın ve T_yangın ayrı ayrı bilinmez; tek bir pikselde bunlar aynı anda çözülemez (iki bilinmeyen, bir ölçüm kanalı). Bu yüzden pratikte aşağıdaki MIR yöntemi kullanılır.

### 1.3 MIR radyans yöntemi

Wooster vd. (2003) yaklaşımında 4 µm bandındaki spektral radyans, yangın sıcaklık aralığında yaklaşık olarak sıcaklığın 4. kuvvetiyle orantılıdır: L_MIR ≈ a·T⁴. Buradan, yangın pikselindeki fazla radyans ile FRP doğrudan ilişkilendirilir (*literatürden*; uygulamanın bilim sekmesiyle aynı biçim):

```
L_4µm − L_4µm,arka ≈ a · (T_yangın⁴ − T_arka⁴)
FRP_MIR ≈ (A_piksel · σ / a) · (L_4µm − L_4µm,arka)
a ≈ 3,0×10⁻⁹ W m⁻² sr⁻¹ µm⁻¹ K⁻⁴
```

- A_piksel: piksel alanı (m²), L: 4 µm spektral radyans (W m⁻² sr⁻¹ µm⁻¹), L_arka: yangın olmayan komşu piksellerin ortalaması.
- Birinci satırı ikinciye taşımak: ε·σ·A_yangın·(T⁴ − T_arka⁴) ifadesinde (T⁴ − T_arka⁴) = (L − L_arka)/a yazılır ve ε·A_yangın yerine tüm piksel alanı kullanıldığında kalan terim A_piksel·σ/a olur (yazarın cebirsel aktarımı; sabit değeri *literatürden*; projede **türetilmedi**, FIRMS'in verdiği FRP olduğu gibi kullanılır).
- Sabit a'nın değeri (≈ 3,0×10⁻⁹) uygulamadaki bilim sekmesinde de yazılıdır (`arayuz/i18n/sci_tr.json`); MODIS ve VIIRS için bandın tam spektral tepkisine göre küçük farkları olabilir (belgede yok).

**Projede FRP nerede kullanılır** (yontem_ozeti §4): (a) anız eşiği F (MODIS 15 MW, VIIRS 4,4 MW); (b) MODIS-hücrede VIIRS noktalarının **ΣFRP**'si (FRP bölünmez, çift sayılmaz); (c) etkin tespit sınırı FRP50; (d) yöntem (ii)'nin büyüklük sınıfı sınırları [10, 50] MW; (e) enerji serisi ve olay başına toplam FRP (en büyük yangını sıralama ölçütü).

### 1.4 Piksel geometrisi

| Sensör | Nadir (tam alt) | Tarama kenarı | Kaynak / etiket |
|---|---|---|---|
| MODIS (Terra, Aqua) | ≈ 1 km | **4,8 km**'ye kadar büyür (scan yönü) | belgelerdeki sayı: `kumeleme_yontemi.md` §1, `harmonizasyon_yontemi.md`; piksel büyümesi *literatürden* de bilinen bir olgudur |
| VIIRS (SNPP, NOAA-20, NOAA-21) | **375 m** | belgede yalnız "375 m" yazar; arayüz bilim sekmesi kenarda "yaklaşık 0,8 km" der (*literatürden*) | `gercek_dogrulama.json` genel b; `sci_tr.json` |

- Kümeleme ve eşleştirme, her noktanın `scan` (doğu–batı) ve `track` (kuzey–güney) boyutlarını **tablodan okur**; yani piksel büyümesi, tarama açısından analitik hesaplanmaz, nokta başına kayıtlıdır. Üst-çeyrek "kenar piksel" tanımı: scan ≥ 1,6 km.
- **Belgede yok:** scan/track'in tarama açısına göre analitik formülü, kenarda track boyutu ve VIIRS kenar büyümesinin projedeki kaydı.
- Bir MODIS pikseline ortalama **3,349** VIIRS noktası düşer (ölçüldü, `mcell_iz_basina_viirs`). Bu yüzden VIIRS aynı yangını daha çok noktayla ve MODIS'in göremediği küçük yangınları da görür.

### 1.5 Tespit olasılığı ve FRP50

Bir yangının tespit edilme olasılığı gücüyle artar (*literatürden*: Giglio vd. 2016; Schroeder vd. 2014; küçük, kısa yangınlar kaçırılır). Projede bu ilişki **veriden** ölçülür: aynı yörünge geçişinde (`gecis_ayirma_dk` = 45 dk) 1 km ile zincirlenen VIIRS noktaları bir "hücre" oluşturur; hücrenin toplam FRP'si ΣFRP ise, eşzamanlı Aqua'nın bu hücreyi görme olasılığı lojistik regresyonla modellenir:

```
P(Aqua görür | ΣFRP) = 1 / (1 + exp(−(β₀ + β₁ · log₁₀ ΣFRP)))
FRP50 :  P = 0,5   ⇔   log₁₀ FRP50 = −β₀ / β₁   ⇔   FRP50 = 10^(−β₀/β₁)
```

(β₀, β₁ gösterimi yazara aittir; belgeler yalnız "log10 ΣFRP üzerinde lojistik regresyonda 0,5 noktası" der.)

| Ölçü | Değer | Anahtar / etiket |
|---|---|---|
| FRP50 genel | 64,88 MW | `modis_frp50_genel_mw` (tahmini) |
| FRP50 gündüz | 73,98 MW | `modis_frp50_gunduz_mw` (tahmini) |
| FRP50 gece | 20,54 MW | `modis_frp50_gece_mw` (tahmini) |

- Gece düşüktür: soğuk arka plan, yüksek kontrast ("fiziksel olarak beklenen yönde", belge). Bölgeye göre: Karadeniz 16,6; Ege 23,0; Doğu Anadolu 26,1; Marmara 31,3; İç Anadolu 67,5; Akdeniz 61,3; Güneydoğu 101,9 MW (tahmini).
- Bu bir **etkin** sınırdır: tarama açısını, ≤ 60 dk zaman farkını ve bulut kaymasını da içerir; MODIS'in saf fiziksel algılama sınırından büyüktür (belge).

---

## 2. Veri modeli

### 2.1 Nokta şeması

Hammaddeler: NASA FIRMS MODIS Collection 6.1 (Terra, Aqua) ve VIIRS 375 m (SNPP, N20, N21) aktif yangın dosyaları; Türkiye kutusu, 2000–2026, son gün 2026-11-12 (`veri_yil_bas`, `veri_yil_bit`, `veri_son_gun`); 27 xlsx dosyası (içinde 59 kaynak CSV).

| Küme | Sayı | Anahtar / etiket |
|---|---|---|
| Toplam nokta | 1.414.674 | `veri_toplam_nokta` (ölçüldü) |
| MODIS / VIIRS | 259.707 / 1.154.967 | `veri_modis_nokta`, `veri_viirs_nokta` (ölçüldü) |
| NRT (gerçek zamanlı) | 61.147 | `veri_nrt_nokta` (ölçüldü) |

Belgelerde adı geçen nokta öznitelikleri (tam sütun listesi bu raporun kaynaklarında **belgede yok**; "veri şeması v1" anılır): konum (enlem φ, boylam λ), UTC zamanı, uydu/sensör, `FRP`, `scan`, `track`, `conf_cls` (FIRMS güven sınıfı), NASA `type`, `day_tr`, `status`, `status_neden`, `event_id`, `match_class`, MODIS-hücre kimliği (`mcell`).

- **Güven eşlemesi** (`conf_cls`): MODIS 0–100 sayısal: düşük 0–29, nominal 30–79, yüksek 80–100; VIIRS harf: l/n/h. Öğrenilmiş alternatif eşleme (MODIS 0–35 / 36–82 / 83–100) FIRMS'i geçemedi (doğru sınıf oranı 0,6457 / 0,6485; Cohen κ 0,1765 / 0,1918; ölçüldü), bu yüzden varsayılan ham FIRMS'tir. `dusuk_guven` etiketi status'a yazılmaz, yalnız bayraktır.
- **NASA `type` alanı:** 1 = volkan, 2 = statik kara kaynağı, 3 = deniz; NRT noktalarında `type = −1` (NASA etiketi yok). `type = 0`'ın açık tanımı belgede yok.
- **Hiçbir nokta silinmez:** her nokta tam bir `status` alır; sıralama/süzme yalnız görünümde yapılır.

### 2.2 Türkiye saati

Depolama UTC'dir. Takvim günü sabit UTC+3 ile hesaplanır, tüm yıllara aynı kural uygulanır:

```
day_TR(p) = ⌊ (t_UTC(p) + 3 sa) / 24 sa ⌋        (yıl kırpılmaz)
```

2016 öncesi kış dönemi UTC+2 etkisi: 21:00–21:59Z için 88 satır (bilinen küçük sınır; `bulgular.md` F1-05).

### 2.3 Kapsam: gözlenen ve gözlenmeyen gün

Bir uydunun bir gün veri üretmemesi "yangın yok" demek değildir. Her (uydu u, gün d) için bir gösterge tanımlanır:

```
observed(u, d) ∈ {0, 1}
```

`observed` bir **çıkarımdır**, NASA geçiş listesi değildir (tahmini). Aday kesinti kuralı (belgelerden):

```
(u, d..d+2) kesintidir  ⇔  u en az G=3 ardışık gün Türkiye'de 0 tespit verir
                           ∧  aynı günlerde aynı sensör ailesindeki kardeş uydular toplamda ≥ K=50 tespit verir
```

Sonuç: 129 uydu-gün (`kapsam_kesinti_uydu_gunu`, tahmini); SNPP 2022-07-26…08-11'de 17 günün 15'i yakalandı. Arayüzde "gözlem yok" ayrı renkle gösterilir. Aksi halde sıfır, yangınsızlık sayılır.

---

## 3. Temizlik: hangi sıcak nokta yangın değildir?

Yöntem **kural tabanlıdır**, makine öğrenmesi yoktur. Eşikler yıl dışarıda bırakma (LOYO, §5.4) ile seçilir; eşiklerin tek kaynağı `src/config/esikler.json`'dır. Gösterim: P = tüm noktalar kümesi, c(p) = noktanın 0,01° (~1 km) hücresi, `type(p)` = NASA tipi.

**Hücre özellikleri** (iki sensör birlikte, type 1/3 hariç): n_y(c) = hücrede tespit görülen farklı yıl sayısı; n_d(c) = farklı TR günü sayısı; n_ay(c) = farklı takvim ayı sayısı (1–12, yıllar birleşik); m(c) = aktif yıllarda yıl içi farklı ay sayısının medyanı; g(c) = gece tespiti payı.

| status | Formal kural | Sayı (anahtar, etiket) |
|---|---|---|
| `volkan` | type(p) = 1 | 5 (`temizlik_status_volkan`, ölçüldü) |
| `deniz` | type(p) = 3 | 8.848 (`temizlik_status_deniz`, ölçüldü) |
| `statik_nasa` | type(p) = 2 | 328.379 (`temizlik_status_statik_nasa`, ölçüldü) |
| NRT mirası | type(p) = −1 ∧ \|{q ∈ c(p): type(q)=2}\| / \|{q ∈ c(p) arşiv}\| ≥ 0,5 ⇒ `statik_nasa` | 12.940 (`temizlik_nrt_statik_mirasi`, ölçüldü) |
| `sanayi` | p ∈ S ⇔ n_y(c(p)) ≥ 5 ∧ n_ay(c(p)) ≥ 8 ∧ n_d(c(p)) ≥ 40 ∧ m(c(p)) ≥ 4 | 27.012 (`temizlik_status_sanayi`, ölçüldü) |
| `kalici_belirsiz` | n_y ≥ 5 ∧ n_ay ≥ 8 ∧ ¬(n_d ≥ 40 ∧ m ≥ 4) ∧ g(c) ≥ 0,5 | 6.208 (`temizlik_status_kalici_belirsiz`, ölçüldü) |
| yangın koruması | p ∈ S ∪ KB ∧ \|{q: gün(q)=gün(p), q ∈ 5×5 komşu hücrede kalıcı olmayan}\| ≥ 2 ⇒ `temiz` | 1.748 nokta (`temizlik_yangin_korumasi_nokta`, ölçüldü) |
| `aniz` | olay düzeyi kural (aşağıda) | 217.179 nokta / 169.115 olay (`temizlik_status_aniz`, `temizlik_olay_aniz_olay`, ölçüldü) |
| `temiz` | yukarıdakilerin hiçbiri | 827.043 (`temizlik_status_temiz`, ölçüldü) |

Toplam: 827.043 + 217.179 + 328.379 + 27.012 + 8.848 + 6.208 + 5 = 1.414.674. `dusuk_guven` status olarak yazılmaz (0). Kuralların birbirine göre öncelik sırası belgede tek satırda yazılı değildir (belgede yok); her nokta tam bir status alır. Sanayi eşik değerleri N = 40 gün, M = 8 ay, Y = 5 yıl, S = 4 ay/yıl'dır; ızgara N ∈ {5, 10, 20, 40, 80}, M ∈ {4, 6, 8, 10, 12}, Y ∈ {2, 3, 5, 8}, S ∈ {1, 2, 3, 4, 6, 8} üzerinde, her test yılı dışarıda bırakılarak, NASA type=2'ye karşı F1'i en büyük yapan nokta seçilir; config değeri katların en sık seçtiği kombinasyondur (20/27 kat = 0,7407, `temizlik_sanayi_loyo_kat_kararliligi`, ölçüldü).

**Sanayi kuralının uyuşması** (LOYO, type=2'ye karşı; type=2 bir maskedir, "doğruluk" değil "uyuşma"):

```
kesinlik = TP / (TP + FP) = 0,9199        (temizlik_sanayi_loyo_precision, ölçüldü)
duyarlılık = TP / (TP + FN) = 0,9712      (temizlik_sanayi_loyo_recall, ölçüldü)
```

VIIRS döneminde 0,9240 / 0,9722; MODIS döneminde (2000–2011) 0,2278 / 0,5679 (ölçüldü). MODIS dönemi düşüktür çünkü referans seyrektir: kuralın "sanayi" dediği 1.477 MODIS noktasının %66,6'sı bilinen bir tesise ≤ 3 km (`temizlik_modis_donemi_sanayi_tesis_payi`, ölçüldü).

**Anız.** Nokta düzeyinde yalnız aday bayrağı (FRP < F_sensör ∧ aynı gün 3×3 hücrede ≤ 3 tespit; 247.112 nokta, ölçüldü). Nihai karar **olay düzeyindedir** (E bir olay, P(E) olayın noktaları):

```
aniz(E)  ⇔  n_mcell(E) ≤ 3  ∧  süre(E) ≤ 12 sa
            ∧  ∀ p ∈ P(E): FRP(p) < F_sensör(p)
            ∧  ay_TR(başlangıç(E)) ∈ A_bölge(E) \ {yıl(E)}
```

- F: MODIS 15 MW (MODIS arşiv type=0 FRP medyanı, `temizlik_F_modis_medyan`, ölçüldü); VIIRS eşdeğeri 4,4 MW (`temizlik_F_viirs_esdeger`, ölçüldü), sabit oranla değil **yüzdelik eşleştirmeyle** (F = 15 için yüzdelik 0,4993).
- n_mcell: olaydaki tekil MODIS-ayak izi eşleştirme birimi sayısı (VIIRS öncesi/sonrası anız payı farkını en küçük yapan sayım: 0,3803 / 0,3546; ölçüldü).
- A_bölge: 7 coğrafi bölge × ay profilinde yıl içi payı **1/12'yi aşan** aylar; her yıl için o yıl hariç öğrenilir (LOYO).
- Doğrulama: anız noktalarının WorldCover 2021'de ekili alan payı 0,7935 (`temizlik_wc_aniz_ekili_alan_pay`, ölçüldü); öğrenilen ayların kaba hasat penceresine (ay 6–10) düşme payı 0,7419 (`temizlik_aniz_hasat_penceresi_payi`, tahmini). **Saha/yanmış alan doğrulaması yoktur (doğrulanmadı).**
- **Dürüst bulgu:** LOYO kaldıracı = kapsama / taban = 0,7490 / 0,8071 = **0,928** (`temizlik_aniz_loyo_kaldirac`, ölçüldü). Kaldıraç ≈ 1 olduğundan "ay" tek başına küçük ateşi büyükten ayırmaz; ayırıcı olan büyüklük, süre ve FRP'dir; ay şartı yalnız mevsim dışını eler.

**Referans doğrulama** (FIRMS'ten bağımsız, küçük set: OSM'den 26 tesis, haberlerden 8 yangın; tahmini): dengeli kesinlik `ref_precision` 0,9711; makro tesis yakalama `ref_recall` 0,4777 (termik santraller kaçıyor); yangın noktalarının kalıcı etiket ALMAMA payı 0,9982 (`temizlik_ref_yangin_koruma`); yangın başına yanlış işaret 0,0142. Nokta düzeyi kesinlik 0,9999 sınıf dengesizliğinden şişkindir ve kullanılmaz. Static Thermal Anomalies (STA) maskesi karşılaştırması yapılmadı (`temizlik_sta_maskesi_karsilastirma`, **doğrulanmadı**).

---

## 4. Kümeleme: olay = bağ grafiğinin bağlı bileşeni

### 4.1 Grafik formülasyonu

Girdi: status ∈ {temiz, aniz} noktalar, |V| = 1.044.222 (= 827.043 + 217.179; `huni_kumeleme_girdi`, ölçüldü). Temiz olmayan noktalar `event_id = −1` alır ve zincire **köprü olamaz**. Anız olay düzeyi bir etikettir, olay yapısını değiştirmez (döngü yok).

```
G = (V, E_bağ),    E_bağ = { {p, q} : bağ(p, q) }
olaylar = G'nin bağlı bileşenleri          (union-find ile)
```

### 4.2 Bağlantı kuralı

İki nokta **uzay** koşulunu **ve** **zaman** koşulunu sağlıyorsa bağlıdır:

```
bağ(p, q)  ⇔  uzay(p, q)  ∧  zaman(p, q)

uzay(p, q) ⇔  d(p, q) ≤ D                                  (D = 1 km)
              ∨  ayak_izi(p, q)

d(p, q)    =  √( dx² + dy² ),   dy = Δφ · 111,   dx = Δλ · 111 · cos(φ̄)     (φ̄ = ortalama enlem; ±180° sarmalı)

zaman(p, q) ⇔  |t_p − t_q| ≤ H_max  (72 sa)
              ∧  W(p, q) ≤ L                                  (L = 3)
```

**Ayak izi testi** (yalnız MODIS–VIIRS çiftlerinde; `ayakizi_capraz`): VIIRS noktası v, MODIS noktası m için, m'nin merkezinde `scan × track` dikdörtgeni ve tampon b = 0,375 km (`eslesme_tamponu_km`) ile:

```
ayak_izi(m, v)  ⇔  |dx(m, v)| ≤ scan(m)/2 + b   ∧   |dy(m, v)| ≤ track(m)/2 + b
```

Dikdörtgen kuzey–güney yönlü varsayılır; gerçek ~10° yörünge eğimi ihmal edilmiştir (tahmini). `ayakizi_tum` modu MODIS–MODIS örtüşmesini de ekler (varsayılan değil; dönemler arası tutarlılığı bozar).

**Geçiş (overpass) kuralı.** W(p, q), iki tespit arasında **tamamen kalan** ve *gözlenmiş* sayılan uydu geçiş penceresi sayısıdır. Türkiye'de günde 4 pencere vardır: Terra gündüz (~06–09 UTC), Aqua+VIIRS gündüz (~09–12), Terra gece (~17–20), Aqua+VIIRS gece (~22–01). Aqua ve üç VIIRS aynı ~13:30 yörüngesinde olduğundan VIIRS yeni pencere eklemez. Pencere sınırı, yıl × uydu grubu için tespit saatlerinin 1. ve 99. yüzdeliğidir (swath verisi yok; tahmini). Gruptan en az bir uydu `observed = 1` ise pencere "gözlenmiş" sayılır. Mantık: bir yangın, ardışık 3 gözlenmiş geçişte görünmediyse sönmüş sayılır; aynı yerde 72 saatten kısa bir boşluk 3'ten fazla gözlenmiş geçiş içeriyorsa zincir kopar. Eski sabit kural (|Δt| ≤ 24 sa) gizli bir hata taşıyordu: gündüz geçiş saati günden güne ~3 sa kaydığından her gün görülen yangın 25 saatlik boşlukla ikiye bölünüyordu (16.434 olay → 7.401 olayda birleşti; ölçüldü).

**Geçiş kuralının etkisi** (D = 1 km, `ayakizi_capraz`; ölçüldü): sabit H = 24 → 481.008 olay; **`gecis` L = 3, H_max = 72 → 471.978 olay** (`events_total`, ölçüldü; süre p99 37,7 sa); L = 2 → 499.277; L = 4 → 468.214. D = 0,5 / 1 / 2 / 3 km → 541.338 / 471.978 / 383.640 / 341.799 olay. "Olay sayısı" daima kuralıyla birlikte verilmelidir. Sınırlama (doğrulanmadı): MODIS'in bir pencerede yangını görmemesi sönme kanıtı değildir; gece pencereleri zayıf kanıttır.

### 4.3 Ortak mı, ayrı mı kümeleme?

MODIS ve VIIRS **birlikte** kümelenir. Çakışma döneminde:

```
ortak kümeleme:   380.975 olay      (events_joint_overlap, ölçüldü)
ayrı kümeleme:    440.176 olay      (events_separate_overlap, ölçüldü)
önlenen çifte sayım = 440.176 − 380.975 = 59.201     (events_double_count_avoided, ölçüldü)
```

Anız tarafında: ortak kümeleme anız nokta sayısını 320.995'ten 290.799'a düşürür (30.196 nokta, %9,4; tahmini); bu yüzden anız büyüklüğü `n_mcell` ile sayılır. MODIS-hücre ataması: VIIRS noktası, zaman |Δt| ≤ 4 sa ve ayak izi içinde olduğu MODIS izine **tek** hücre olarak atanır (birden çok ize düşerse sırayla: eşzamanlı iz, en küçük normalize uzaklık, en küçük |Δt|, en küçük alan); FRP bölünmez. 174.203 VIIRS noktası bir MODIS izine düşer; iz başına 3,349 VIIRS noktası (ölçüldü).

### 4.4 Üçlü eşleşme sınıfı

Çakışma = olayın başladığı TR gününde iki sensör ailesinden en az birer uydunun `observed = 1` olması. Çakışma dönemindeki her olay E için:

```
match_class(E) = ortak         ⇔  n_MODIS(E) > 0 ∧ n_VIIRS(E) > 0
               = yalniz_modis  ⇔  n_MODIS(E) > 0 ∧ n_VIIRS(E) = 0
               = yalniz_viirs  ⇔  n_MODIS(E) = 0 ∧ n_VIIRS(E) > 0
               = tek_sensor_donemi   (çakışma dışı; sınıf anlamsız)
```

| Sınıf | Olay | Anahtar / etiket |
|---|---|---|
| ortak | 35.651 | `events_match_ortak` (ölçüldü) |
| yalnız MODIS | 57.543 | `events_match_yalniz_modis` (ölçüldü) |
| yalnız VIIRS | 287.781 | `events_match_yalniz_viirs` (ölçüldü) |
| tek sensör dönemi | 91.003 | `events_match_*` (ölçüldü) |
| toplam | 471.978 | `events_total` (ölçüldü) |

MODIS olaylarının yalnız 0,3825'ini VIIRS de görür (`events_modis_seen_by_viirs_share`, ölçüldü). Bu, eşleştirme hatasından çok gözlem farkıdır: yalnız-MODIS olayların ~%64'ü yalnız Terra'dandır (10:30 geçişi; VIIRS 13:30). Sonuç: "her MODIS tespitinin VIIRS karşılığı vardır" varsayımı yapılmamalıdır.

### 4.5 Gayriresmî sözde-algoritma ve karmaşıklık

```
girdi:  noktalar P (status ∈ {temiz, aniz}), coverage[uydu, gün]
1.  P'yi zamana göre sırala; her noktaya union-find'da tek eleman ata
2.  gözlenmiş geçiş pencereleri listesini kur (yıl × uydu grubu yüzdelikleri, observed)
3.  her p için, zaman penceresi [t_p − 72 sa, t_p] içindeki ve 
    uzayda yakın adayları q bul (ızgara/hücre indeksi ile)
4.     eğer uzay(p, q) ve zaman(p, q) ise   birleştir(p, q)
5.  her kökü bir event_id'ye eşle; temiz olmayanlara event_id = −1
6.  olay içinde n_MODIS, n_VIIRS, n_mcell, süre, ΣFRP hesapla; match_class ata
7.  olay düzeyinde anız kuralını uygula (etiket; yapıyı değiştirmez)
```

- **Karmaşıklık (yazarın çözümlemesi; belgede yok):** union-find ile eklemeli birleştirme n noktada n·α(n) (α: ters Ackermann) düzeyindedir; komşu adayları bulma, yoğun bölgelerde aday sayısı k olmak üzere O(n·k) olur; ızgara indeksi yoksa en kötü durum O(n²) olur. Uygulamanın kullandığı veri yapısı bu raporun kaynaklarında yazılı değildir.
- **Ölçülen:** çalışma süresi 3,32 s, bellek 676 MB (`clustering_runtime_s`, `clustering_rss_mb`, ölçüldü).
- **Doğruluk (C03):** 12 örneklemde (21.509 nokta, 7 kural çeşidi), her n² çift için bağımsız yüklemle karşılaştırma: 88 karşılaştırmada 0 fark; mutasyon testi 12/12 yakalandı (ölçüldü).
- **Zincirleme riski:** 312.936 tek tespitli olay; en büyük olay 6.740 tespit (Manavgat 2021-07-28; gerçek mega yangın). Açık: kapsamı ≥ 10 km, statik nokta içermeyen 152 olaydan 34'ü "tarım zinciri" tanımında (9.484 tespit, %0,9; tahmini, sahada doğrulanmadı).

---

## 5. Harmonizasyon: VIIRS'i MODIS diline çevirmek

> **Dürüstlük notu.** Belgelerde yöntemin cebirsel formülü tek satırda **verilmemiştir**; yöntem sözel tanımlıdır. Bu bölümdeki formüller sözel tanımın **yazar tarafından yapılmış bir aktarımıdır (transkripsiyon)**. Özellikle yöntem (ii)'deki oranın tam ifadesi (ör. "MODIS tespiti / eforlu VIIRS tespiti") ve kodda hangi sütunların bölündüğü belgede yoktur.

### 5.1 Efor normalizasyonu

2018'de 2., 2023'te 3. VIIRS uydusu eklendi; daha çok uydu daha çok nokta demektir. Her gün için VIIRS toplamı, o gün `observed = 1` olan VIIRS uydu sayısına bölünür (`seri.efor_normalize`):

```
V*(d) = V(d) / n_VIIRS(d),      n_VIIRS(d) = Σ_u∈VIIRS observed(u, d)
V*(ay) = Σ_d V*(d)   (gözlemsiz günler ay içi ortalamayla ölçeklenir)
```

### 5.2 Oran modeli: bölge × mevsim × FRP sınıfı

Hedef: Terra+Aqua tespiti (ay × bölge, status = temiz). Mevsimler: Ara–Şub kış, Mar–May ilkbahar, Haz–Ağu yaz, Eyl–Kas sonbahar; 7 geleneksel coğrafi bölge. Büyüklük sınıfları `frp_sinif_sinirlari_mw` = [10, 50] MW (küçük < 10, orta 10–50, büyük ≥ 50; hücre toplam FRP veya MODIS tespit FRP).

```
M̂(b, a) = Σ_s  r(b, mevsim(a), s) · V*(b, a, s)

r(b, ms, s) = (çakışma yıllarında) MODIS tespiti(b, ms, s) / eforlu VIIRS tespiti(b, ms, s)       [aktarım; belgede yok]
```

b: bölge, a: ay, s: FRP sınıfı. Az örnekli tabakada (`min_ornek` = 200 hücre) mevsim × büyüklüğe, sonra gündüz/gece'ye düşülür (hiyerarşik geri çekilme). Olay biriminde: gerçek = n_MODIS > 0 olaylar (ortak + yalnız MODIS); VIIRS özelliği = olaydaki VIIRS ΣFRP'nin sınıfı; oran bölge × mevsim × sınıf, artı yalnız-MODIS olay payı (bölge × mevsim). Olay eşdeğeri tespit eşdeğerini aşamaz (aşan hücreler kırpılır).

### 5.3 Yöntem yarışı: (i0), (i), (ii), (iii)

- **(i0)** tek sabit oran, efor yok (yalnız kıyas; "B-04 tuzağı").
- **(i)** tek sabit oran, eforlu.
- **(ii) ana yöntem:** bölge × mevsim × FRP sınıfı oranı, eforlu.
- **(iii)** FRP eşik eğrisi g(ΣFRP) = hücre başına beklenen Aqua tespiti (12 log-FRP kutusu; bölge × mevsim × gündüz/gece, hiyerarşik) + yalnız-MODIS payı f_u (uydu × gündüz/gece × mevsim) + Terra payı k_TA (bölge × mevsim × gündüz/gece), eforlu.

| Yöntem | Ay×bölge WAPE % | Yıllık MAPE % | Yıllık R² | Yıllık sapma % | Yıllık %95 hata aralığı | Anahtar |
|---|---|---|---|---|---|---|
| (i0) | 52,68 | 42,12 | −1,7204 | 5,03 | [−46,83; 86,91] | `harm_i0_*` |
| (i) | 30,64 | 4,83 | 0,9675 | 0,15 | [−7,81; 9,46] | `harm_i_*` |
| **(ii)** | **30,63** | **8,33** | **0,8716** | **0,55** | **[−23,49; 9,51]** | `harm_ii_*`; `loyo_mape`, `loyo_r2`, `loyo_bias` (ölçüldü), `loyo_ci95` (tahmini) |
| (iii) | 31,91 | 10,91 | 0,7644 | 3,76 | [−13,0; 31,69] | `harm_iii_*` |

Seçim ölçütü: en düşük ay × bölge WAPE (uygulamanın birimi). **Dürüst okuma:** (ii) ile (i) ay × bölgede **ayırt edilemez** (fark −0,01 yp, `harm_ii_eksi_i_wape`; yıl bootstrap'ı %95 [−2,97; 4,26] yp, tahmini). Yıllıkta (i) daha iyidir; asıl kazanç **efor normalizasyonudur** (i0 → i: WAPE 52,68 → 30,64). (ii), üstünlük iddiası olmaksızın uygulama birimi nedeniyle ana yöntem kaldı. Ölçütün sonuçlardan önce yazıldığı kayıtlı olmadığından **doğrulanamaz**; kazananın hatası seçim etkisiyle hafif iyimser olabilir.

### 5.4 LOYO tanımı

```
Y = {2012, 2013, …, 2025}   (14 test yılı; loyo_test_yillari)
∀ y ∈ Y :   model_y ← eğit( Y \ {y} ),    Ŷ_y ← tahmin( model_y, y )
```

Her yıl modelden saklanıp o yıl tahmin edilir. 2026 kısmi + NRT olduğundan testte yoktur ("düşük güven"). Eski dönem 2000–Temmuz 2002 (yalnız Terra): nokta değer düzeltilmez (`bayrak = eski_donem_yalniz_terra`); bu yıllar sonrakilerle doğrudan karşılaştırılamaz (yaklaşık yarı efor).

### 5.5 Hata ölçüleri

Yıllık: Y_y gerçek (MODIS), Ŷ_y tahmin; ay × bölge: x_i gerçek, x̂_i tahmin (i hücre indeksi). Aşağıdaki tanımlar standart tanımlardır; belgeler yalnız ölçü adlarını verir, tam formül belgede yok:

```
MAPE = (100 / |Y|) · Σ_y |Ŷ_y − Y_y| / Y_y
R²   = 1 − Σ_y (Y_y − Ŷ_y)² / Σ_y (Y_y − Ȳ)²        (tahmin ortalamadan kötüyse R² < 0 olur: (i0) için −1,7204)
bias = (100 / |Y|) · Σ_y (Ŷ_y − Y_y) / Y_y           (yönlü; sapma %)
WAPE = 100 · Σ_i |x̂_i − x_i| / Σ_i x_i               (ay × bölge hücreleri)
```

### 5.6 Belirsizlik bandı

LOYO artıkları log-oran olarak tutulur ve her kutuda yüzdeliklerle bant kurulur:

```
e = ln( (gerçek + 1) / (tahmin + 1) )
bant = [ (tahmin + 1)·exp(q₂,₅) − 1 ,  (tahmin + 1)·exp(q₉₇,₅) − 1 ]
```

(q_p: e'nin p. yüzdeliği; tahmin büyüklüğüne göre 3 kutu; ay × bölge ve ay × ülke ayrı. Bandın exp(·)−1 ters dönüşümü yazarın aktarımıdır; belgeler yalnız "log((gerçek+1)/(tahmin+1)) yüzdelikleri" der.) Kapsama "dürüsttür": her yılın bandı **diğer yılların** artıklarından kurulur ve o yılda sınanır.

| Ölçü | Değer | Anahtar / etiket |
|---|---|---|
| Aylık ülke toplamı bandı | [−59,57; +74,99] % | `equiv_overlap_band` (tahmini) |
| Kapsama, ay × bölge | 0,9557 | `equiv_band_kapsama_ay_bolge` (ölçüldü) |
| Kapsama, ay × ülke | 0,9226 | `equiv_band_kapsama_ay_tr` (ölçüldü) |
| Çakışma toplam sapması | −%0,52 | `equiv_overlap_bias` (tahmini) |
| Olay birimi: yıllık MAPE / R² / ay×bölge WAPE / ay×il WAPE | 7,51 / 0,8443 / 32,8 / 46,27 | `olay_temiz_*` (ölçüldü) |

İl düzeyinde eşdeğer seri ayrıca doğrulanmamıştır.

---

## 6. Sıçrama analizi (2012)

### 6.1 Tanım

```
sıçrama = ort(2012–2014) / ort(2009–2011) − 1        (sicrama_pencere_yil = 3)
```

2012 sonrası harmonize değerler LOYO tahminleridir (tahmini). Pencere: 2009–11 (yalnız MODIS) ve 2012–14 (MODIS + VIIRS dönemi). Türkiye, status = temiz.

### 6.2 Üç aşamalı sonuç

Aşağıdaki aşama sayıları bu oturumda ölçülmüştür (2009–11 → 2012–14):

| Aşama | Değişim | Anahtar / etiket |
|---|---|---|
| 1. Ham tespit (MODIS → MODIS+VIIRS) | **+%143** (+143,13) | `jump_raw_pct` (ölçüldü) |
| 2. Kümelenmiş olay | **+%31** | (ölçüldü, bu oturum) |
| 3. Düzeltilmiş (MODIS-eşdeğer) | **−%41** (−41,35) | `jump_harm_pct` (tahmini) |
| Gerçek MODIS (aynı pencere) | **−%45** (−44,9) | `jump_modis_gercek_pct` (ölçüldü) |

Yıllık değerler (Türkiye, temiz; yıllık sayılar bu oturumda ölçülmüştür):

| Yıl | Ham tespit | Kümelenmiş olay | Düzeltilmiş (MODIS-eşdeğer) |
|---|---|---|---|
| 2011 | 12.045 | 8.786 | 12.045 (gerçek MODIS; düzeltme yok) |
| 2012 | 25.028 | 10.524 | 6.144 (tahmini) |
| 2013 | 38.140 | 13.855 | 8.993 (tahmini) |

2011 → 2012 adım değişimi (yazarın aritmetiği, yukarıdaki sayılardan): ham yaklaşık +%108, kümelenmiş olay yaklaşık +%20, düzeltilmiş yaklaşık −%49.

**Mesaj.** Kümeleme sıçramanın **çoğunu** ortadan kaldırır (+143'ten +31'e) ama **tamamını** değil; kalanı harmonizasyon giderir. Bu yüzden "kümeleme 2012 sıçramasını ortadan kaldırdı" **denmez**: aynı yangının çok noktasını tek olayda toplamak sensör farkının büyük bölümünü sönümler, geri kalanı (VIIRS'in MODIS'in göremediği küçük yangınları ayrı olay olarak görmesi, ek uydu eforu) ancak oran modeliyle düzeltilir.

**Veri notu.** `metrics.json`'daki "olay / temiz" varyantı farklı bir tanımla ham +%51,72, harmonize −%54,23, gerçek MODIS −%53,45 verir (`olay_temiz_jump_raw_pct`, `olay_temiz_jump_harm_pct`, `olay_temiz_jump_modis_gercek_pct`; artık −0,78 yp). Farkın nedeni ölçüldü: varyanttaki "ham" olay sayısı, iki uydunun olaylarının **ayrı ayrı kümelenip toplanmasıdır** (harmonized.json, `modis_gercek + viirs_ham`): 2009–11 ortalaması 8.563, 2012–14 ortalaması 12.993 → +%51,72. Bu oturumdaki +%31 ise **ortak kümeleme** sonucudur (her olay bir kez; aynı yangını iki uydu görse de tek olay). Aradaki 21 puanlık fark, ortak kümelemenin önlediği çift sayımdır (bkz. `events_double_count_avoided`). Böylece sıçramanın aşamaları: ham tespit +%143 → ayrı kümeleme +%52 → ortak kümeleme +%31 → harmonizasyon −%41 (tespit birimi; olay biriminde −%54,23, gerçek MODIS −%53,45).

**Uyarı: 2009–11 tabanı olağandışı yüksektir.** 2009–2011, MODIS'in kendi kaydında da yüksek yıllardır; "%45 azaldı" bir iklim eğilimi iddiası **değildir**. İddia yalnız şudur: düzeltilmiş seri, aynı penceredeki gerçek MODIS değişimini küçük bir farkla izler ve ham +%143 sensör eklenmesinden gelir.

### 6.3 Artık, doğal değişim aralığı

```
jump_resid = jump_harm − jump_MODIS_gerçek = (−41,35) − (−44,9) = 3,55 yp        (jump_resid_pct, tahmini)
```

- **Doğal değişim aralığı:** MODIS serisinde geçiş dışı 17 adet 3+3 yıllık pencerenin %2,5–%97,5 yüzdeliği **[−39,3; +92,61] %** (`jump_null_ci95`, tahmini). Harmonize sıçrama (−41,35) bu aralığın **dışındadır** (`jump_harm_dogal_aralikta` = hayır); gerçek MODIS (−44,9) de dışındadır.
- **Uydu eklenişleri** (efor etkisi; ölçüldü): N20 2018 (3+3): ham +%24,34, eforlu −%37,31, gerçek MODIS −%41,59; N21 2023 (2+2): ham +%110,19, eforlu +%44,29, gerçek MODIS +%31,01.

### 6.4 Ölçüt değişikliği (post-hoc) ve denetçi penceresi

Eski C10 ölçütü "harmonize sıçrama doğal aralıkta olmalı" idi. Sonuç görüldükten sonra, gerçek MODIS de aynı aralığın dışında kaldığı için (kusursuz bir harmonizasyon da reddedilirdi), ana ölçüt **koordinatör kararıyla** şuna çevrildi: artık sıçrama, yıllık LOYO %95 hata aralığı `loyo_ci95` = [−23,49; +9,51] içinde olmalı (3,55 → sağlanıyor). Bu değişiklik **post-hoc'tur** ve yeni ölçüt gevşektir (büyük ölçüde C09'un tekrarıdır). Bağımsız denetçi aynı tanımla 2013–2023 tüm 3+3 pencerelerin artık dağılımını hesapladı: [−10,43; +4,62]; 2012 değeri (3,55) bu aralıktadır ("sonuç sağlam", denetçi). Önerilen dil: "sıçrama kayboldu" değil, "harmonize seri 2012'deki gerçek MODIS düşüşünü 3,6 puan farkla izliyor".

---

## 7. Takvim matematiği

**Aylık değer ve kesinti ağırlıkları (C06).** w_d = gözlem yapan uydu sayısı / işleyen uydu sayısı (gün d için). Yıl y, ay m, ay uzunluğu L_m için:

```
x(y, m) = [ Σ_{d: w_d > 0} sayım(d) / Σ_d w_d ] × L_m
```

Hücre **BOŞ** bırakılır (sıfır yazılmaz): işleyen gün < ay uzunluğu (sensör başlangıcı/bitişi, kısmi ay, veri sonu) ya da kesinti payı > 0,5 (`takvim.kesinti_pay_max`); sensör hiç işlemiyorsa (VIIRS < 2012) NaN. Serbest tarih aralığında gözlenen gün ağırlığı / istenen gün < 0,5 ise değer boştur.

**Medyan profil.** Normal yıl: tam yıl, aynı sensör bileşimi (MODIS Terra+Aqua için 2003–2025 = 23 yıl); geçiş yılları (2012, 2018, 2023) ve 2026 hariç. Her ay için medyan, Q1, Q3, min, maks; n < 2 ise medyan boş; n < 5 ise `az_yil`. Olay serilerinde sensör bileşimi değiştiğinden **ay payı medyanı** kullanılır.

**Ayırt edilemez (≈) kuralı.** Ölçüt ay medyanıdır; en yoğun 3 ay (`top_n` = 3). Top-3 içindeki komşu iki ayın medyanı arasındaki göreli fark < 0,1 (`ayirt_edilemez_tol`) ise "ayırt edilemez" (arayüzde ≈):

```
|med(a) − med(b)| / [payda]  <  0,1       →  a ≈ b        (payda tanımı belgede yok)
```

Ek olarak yıl bootstrap'ı top-3 olasılığı (B = 300, tohum 20260101). TR için sonuçlar: `modis_ham` [6, 9, 10] ve `modis_temiz` [6, 9, 8] (ölçüldü); `modis_esdeger` [8, 9, 6] ve `olay` [9, 8, 10] (tahmini); hepsinde ayırt edilemez bayrağı = 1: Ağustos–Eylül medyanları istatistiksel olarak ayırt edilemez.

**Sağlam z anomalisi.** log1p ölçeğinde, normal yıllara göre **test yılı hariç** (LOYO):

```
z = ( log(1 + x) − medyan ) / max( 1,4826 · MAD , 0,05 )          işaret:  |z| ≥ 2
```

MAD = medyan mutlak sapma; 0,05 = `olcek_taban`; pencere aynı takvim ayı. Eşdeğer seride bant alt/üst için z hesaplanır; işaret bantta değişirse `belirsiz_bant`: anomali işaretlerinin %33,53'ü belirsiz banda düşer (`takvim_anomali_belirsiz_bant_payi_esdeger`, tahmini); işaretli hücre payı %8,96 (`takvim_anomali_isaret_orani_esdeger`, tahmini). "Son tam ay normalin %170'i" gibi yüzde = x / ilgili ay medyanı.

---

## 8. "Orman yangını adayı" (heuristik, tahmini)

Arayüzdeki "Yangın türü" seçeneklerinden biridir (tümü / anız hariç / yalnız anız / orman yangını adayları). Her olay E için:

```
orman_adayi(E)  ⇔  ( süre(E) ≥ 12 sa  ∨  ΣFRP(E) ≥ 200 MW )
                   ∧  n_tespit(E) ≥ 5
                   ∧  ∀ F ≠ E, yıl(F) ≠ yıl(E) :  hücre_0,01°(E) ∩ hücre_0,01°(F) = ∅
```

Sonuç: **2.063 olay** (tahmini, bu oturum). Bu modda en yoğun aylar **Ağustos > Eylül > Temmuz**'dur (tahmini, bu oturum).

**Gerekçe.** (1) Anız kuralı (§3) küçük (≤ 3 birim), kısa (≤ 12 sa) ve zayıf (FRP < F) olayları hedefler; adaylık koşulu büyük/uzun/güçlü olayları seçer. (2) "Başka yılda aynı ~1 km hücrede olay yok" şartı, her yıl aynı tarlada ya da tesiste tekrarlayan yanmaları eler; ormanlar bir yangından sonra aynı yıl bölgesinde tekrar yanmaz. (3) Dolaylı kanıt: FRP toplamına göre ilk 10 yangının tümü belgelenmiş yangındır (§9; #1 Manavgat 2021-07-28, 6.740 tespit, 384.683 MW, 218,6 sa).

**Sınırlar.** **Arazi örtüsü verisi kullanılmaz**; bu bir orman sınıflaması değil, davranış tabanlı tahmindir. Aday kümesinin WorldCover ile ayrıca ölçümü belgede yok. Büyük temiz olay grubunda (n_mcell ≥ 10) ekili alan payı 0,503, ağaç payı 0,321'dir (`temizlik_wc_buyuk_temiz_ekili_alan_pay`, `temizlik_wc_buyuk_temiz_agac_pay`, ölçüldü): büyük olaylar yalnız ormandan ibaret değildir. Bu nedenle sınıf "orman yangını **adayı**" diye adlandırılır, kesin orman yangını diye yorumlanmaz. Adana 2012 olayı (§9) türünden büyük ova olayları aday kümesine girebilir (bu olayın adaylık durumu belgede yok).

---

## 9. Gerçek dünya doğrulaması

FIRMS'ten bağımsız kaynaklarla (OGM, İTÜ UHUZAM ve GTÜ uydu analizleri, haber ajansları; künyeler `gercek_dogrulama.json`'da) **toplam FRP'ye göre en büyük 20 olay** belgelenmiş yangınlarla tarih ve konum olarak karşılaştırıldı. Hiçbir resmî bilgi modele girmedi.

**Sayım:** 20 olay → **16 eşleşiyor**, **3 kısmen**, **1 bulunamadı** (`gercek_dogrulama.json`; etiket: tarih/yer eşleşmesi, el ile yapılan karşılaştırma; ölçüldü değil, gözleme dayalı).

| # | Olay | İl | Başlangıç (TR) | Süre (sa) | ΣFRP (MW) | Belgelenmiş yangın | Eşleşme |
|---|---|---|---|---|---|---|---|
| 1 | 307626 | Antalya | 2021-07-28 12:00 | 218,6 | 384.683 | Manavgat | eşleşiyor |
| 2 | 307807 | Muğla | 2021-07-31 23:34 | 171,8 | 103.176 | Milas–Bodrum | eşleşiyor |
| 3 | 307718 | Antalya | 2021-07-29 12:53 | 193,7 | 75.470 | Manavgat kompleksi doğu kolu / Gündoğmuş | kısmen |
| 4 | 428217 | Bilecik | 2025-07-20 22:04 | 88,9 | 75.410 | Geyve → Osmaneli | eşleşiyor |
| 5 | 426373 | İzmir | 2025-06-28 14:46 | 61,4 | 73.305 | Seferihisar–Menderes | eşleşiyor |
| 6 | 307866 | Muğla | 2021-08-02 23:22 | 124,0 | 68.286 | Kavaklıdere–Yatağan | kısmen |
| 7 | 427937 | Çanakkale | 2025-07-15 13:37 | 37,3 | 65.550 | Şarköy → Gelibolu | eşleşiyor |
| 8 | 426211 | Bilecik | 2025-06-27 13:25 | 38,1 | 63.733 | Taraklı → Gölpazarı | eşleşiyor |
| 9 | 426891 | İzmir | 2025-07-02 13:31 | 71,9 | 57.830 | Çeşme (Ildır) | eşleşiyor |
| 10 | 454809 | Muğla | 2026-07-29 09:52 | 24,6 | 45.041 | Seydikemer (Bayır) | eşleşiyor |
| 11 | 307723 | Muğla | 2021-07-29 13:43 | 157,8 | 43.759 | Marmaris | eşleşiyor |
| 12 | 307744 | Muğla | 2021-07-29 23:47 | 315,2 | 41.700 | Köyceğiz | eşleşiyor |
| 13 | 429406 | Mersin | 2025-08-13 12:52 | 168,8 | 36.124 | Silifke | eşleşiyor |
| 14 | 426343 | Manisa | 2025-06-28 13:06 | 72,7 | 35.001 | Akhisar (Karaköy) | eşleşiyor |
| 15 | 324714 | Muğla | 2022-06-21 23:45 | 51,7 | 34.523 | Marmaris (Bördübet/Hisarönü) | eşleşiyor |
| 16 | 307650 | Mersin | 2021-07-28 13:42 | 85,4 | 32.535 | Mersin yangınları (Aydıncık/Silifke/Gülnar) | kısmen |
| 17 | 428617 | Bursa | 2025-07-27 12:49 | 49,0 | 32.112 | Orhaneli–Harmancık | eşleşiyor |
| 18 | 99294 | Adana | 2012-08-24 11:39 | 290,3 | 30.268 | (belgelenmiş yangın bulunamadı) | **bulunamadı** |
| 19 | 426617 | Hatay | 2025-06-30 10:58 | 28,3 | 30.019 | Antakya (Karaali) | eşleşiyor |
| 20 | 459190 | Antalya | 2026-09-07 20:43 | 43,8 | 29.895 | Aksu–Kepez (Karaöz) | eşleşiyor |

**Okuma.**
- İlk 10 olayın tümü belgelenmiş yangın dalgalarına denk gelir (8 eşleşiyor, 2 kısmen; ikisi de aynı gerçek yangın kompleksinin parçası olabilir).
- Aynı gerçek yangın dalgası birden çok olay olarak görünebilir (2021 Antalya: Manavgat + Gündoğmuş kolu; 2021 Muğla: Milas–Bodrum, Marmaris, Köyceğiz, Yatağan farklı ateşlemeler).
- Kısmen eşleşenler: 307718 (ayrı ateşleme tarihi doğrulanamadı), 307866 (alan rakamları tutarsız), 307650 (tek bir adlandırılmış yangınla eşlenemedi).
- **Bulunamadı:** 99294 (Adana, 2012-08-24, 290,3 sa, 30.268 MW). Adlandırılmış/belgelenmiş büyük bir orman yangını bulunamadı; düşük tepe FRP (236 MW), 290 saatlik süre ve ova konumu (Ceyhan/İmamoğlu çevresi) anız/tarımsal yakma ya da sanayi kaynaklı olabilir; **doğrulanmadı**.

**Uyarılar (neyi göstermiyor).**
1. Örneklem **bizim ürettiğimiz** olaylardan seçilen en büyük 20'dir; tersi (belgelenmiş her büyük yangını bulduk mu?) test edilmemiştir: yani **duyarlılık/yakalama oranı ölçülmedi**.
2. Eşleşme ölçütü tarih ve konum örtüşmesidir (sözel, tek tek değerlendirme); eşik değeri yok.
3. Kaynaklar çoğunlukla haber ajansları ve il/bakan açıklamalarıdır; resmî nihai hektar çoğu olay için **bulunamadı** (2025 olayları). Alan rakamları kaynaklar arasında büyük farklar gösterir (Köyceğiz 1.629–12.001 ha; Marmaris 2021 9.052–13.600 ha); bunlar aralık olarak anılır ve model değerlendirmesine alınmaz.
4. EFFIS Advance Report 2021 sertifika hatası nedeniyle açılamadı; EFFIS rakamı **doğrulanmadı**. 2026 olaylarının alanları ilk tespittir.
5. Yangınların başlangıç tarihleri ±1 gün içinde uyuşur (ör. 426373'te bizim tespit ~22 saat önce görünüyor); bitiş zamanı son sıcak noktaya bağlı olduğundan resmî kontrol zamanıyla birebir örtüşmez.
6. 2021 genel toplamı (2.793 yangında 139.503 ha, OGM) bağlam içindir; olay düzeyinde bir karşılaştırma değildir.

---

## 10. Bilinen eleştiriler ve cevaplarımız (v2.3)

Bu bölüm, hakem gözüyle bulunan dört zayıf noktayı ve her biri için ne yaptığımızı anlatır. Ölçümler bu oturumda yapıldı; ayrıntılar `belgeler_ve_denetim/recall_olcumu.md` dosyasında ve uygulamada.

### 10.1 Şanlıurfa tarımsal yakma sızıntısı

**Eleştiri:** 471.978 olayın %14,4'ü (67.937) Şanlıurfa'da. "Temiz" olayların ise %15,4'ü (46.490 / 302.863, ölçüldü) bu ilde. İki neden tasarım kararımızdan geliyor:
- ulusal FRP eşikleri (VIIRS 4,4 MW, MODIS 15 MW) Harran tarlaları için düşük kalıyor;
- `yillik_tekrar` bayrağı etiketi değiştirmiyor.

**Yaptığımız:** uygulamaya bir duyarlılık filtresi ekledik: "Tekrarlayan yakmaları çıkar" (sol panel, varsayılanı kapalı).
- **Kural:** aynı 0,01° (≈1 km) karede 3 veya daha fazla farklı yılda olay görüldüyse "tekrarlayan yakma şüphesi". Gerekçe: tarla yakması her yıl aynı yerde tekrarlar, orman yangını tekrarlamaz.
- **Etkisi** (ölçüldü, bu oturum):
  - "temiz" olayların %69,8'i (211.387) çıkıyor;
  - Şanlıurfa'da %90,1 (41.878 / 46.490) çıkıyor;
  - kalan olaylarda Şanlıurfa payı %15,4'ten %5,0'a iniyor;
  - en yoğun aylar "Eyl ≈ Ağu > Haz"dan "Ağu > Eyl > Tem"e dönüyor.
- **Özgüllük kontrolü:** belgelenmiş gerçek yangınlarla eşleşen 19 olayın hiçbiri bu filtreye takılmıyor (hepsi 1–2 yıllık karelerde). Enerjisi en büyük 100 olayın 18'i takılıyor; bunlar büyük tarla ya da tekrar eden makilik yangınları olabilir, ayrıca doğrulanmadı.
- **Dürüst sınır:** filtre tarımı tamamen temizlemiyor. Filtreden sonra en çok olaylı iller Konya, Ankara ve Şanlıurfa; 1–2 yıl yanan tarlalar filtreden kaçıyor. Resmî sayılarımız filtre kapalıyken geçerlidir. Kalıcı düzeltme veri hattında bölgesel (il ya da bölge medyanı) FRP eşiği ve tekrar bayrağının etikete bağlanmasıdır; bu paket klasöründe yapılmadı.

### 10.2 Model seçimi: (ii) ile (i)

**Eleştiri:** Seçilen yöntem (ii), en basit eforlu oran (i) ile ay × bölgede ayırt edilemiyor: WAPE 30,63'e karşı 30,64; fark %95 [−2,97, 4,26] yp (tahmini). Yıllıkta ise (i) daha iyi: MAPE %4,83'e karşı %8,33, R² 0,9675'e karşı 0,8716 (ölçüldü).

**Cevabımız:** Bu doğru ve saklamıyoruz. Asıl kazanç efor düzeltmesinden, yani günlük VIIRS sayısını o gün bakan VIIRS uydu sayısına bölmekten geliyor:
- (i0) eforsuz: ay × bölge WAPE 52,68;
- (i) eforlu: 30,64.

(ii)'nin bölge × mevsim × FRP sınıfı katmanları ek kazanç getirmedi. (ii) "üstün" olduğu için değil, uygulama birimi (ay × bölge, olay birimi) için ana yöntem kaldı. Jüriye mesajımız şu: basit, fiziğe dayalı bir düzeltme işi görüyor. Yıllık Türkiye eğilimi için (i) de savunulabilir; (i) ile hesaplanmış sıçrama değeri belgelerde ayrıca raporlanmadığı için burada verilmiyor (belgede yok).

### 10.3 2026 Aqua yörünge kayması

**Eleştiri:**
- Aqua'nın gündüz geçiş medyanı 10,70 UTC'den (2015) 12,65 UTC'ye (2026) kaydı.
- Eşzamanlı Aqua–VIIRS çift payı %18,2'ye, 2026 bant kapsaması %54,5'e düştü (ölçüldü).
- Kaymasız dönemle (2012–2023) kalibrasyon varyantı test edilmedi.

**Cevabımız:**
- Uygulama 2026 düzeltilmiş serisini "güvenilmez" diye işaretliyor ve kartta ölçülen seriye düşüyor.
- Sunumda 2026 düzeltilmiş değerini hiçbir slaytta kullanmıyoruz.
- Kaymasız kalibrasyon testi veri hattı gerektiriyor ve yapılmadı (doğrulanmadı).
- NASA'ya göre bilim görevlerinin sonu Terra için Şubat 2027, Aqua için Eylül 2027. Bu tarihten sonra MODIS'le bağımsız doğrulama imkânı kalmayacak; çalışmanın amacı tam bu geçişe hazırlanmak.

### 10.4 Doğrulama ve paket eksikleri

**Duyarlılık (recall) artık ölçüldü** (bu oturum):
- **Referans:** basın ve OGM verisine dayanan kaynaklardan derlenen 2021 ve 2025 büyük yangın listesi (29 yangın, 28'i değerlendirilebilir).
- **Katı ölçüt:** ilçe merkezine ≤ 30 km ve resmî başlangıç −1/+3 gün. Sonuç **26/28 (%93)**; yalnız tarihli kayıtlarda 20/22. Kapsam: liste eksik ve çoğunlukla büyük yangınlar; 6 kayıt tarihsiz (yaz penceresiyle eşleşti); sonuç eşleştirme mesafesine duyarlı (15 km: 16/28, 30 km: 26/28, 50 km: 28/28). Genel bir tespit oranı değildir.
- **Kaçan iki kayıt** elle incelemede de yakalanmış çıktı:
  - Akseki: Manavgat olayının parçası;
  - Seyitgazi: İhsaniye'ye taşan olay, 34 km.
- **Mesafeye duyarlılık:** 15 km'de 16/28, 50 km'de 28/28. Bunun nedeni ilçe merkezi koordinatlarının kaba olması.
- Yakalanan olayların hepsi "temiz" etiketli; hiçbir büyük orman yangını anız ya da sanayi diye ayrılmamış.
- **Sınırlar:**
  - liste eksik (OGM'ye göre 2021'de ≥500 ha 28 yangın vardı, listede yaklaşık yarısı var);
  - küçük yangınlarda duyarlılık ölçülmedi;
  - yanan alan (MCD64A1, OGM poligonu) ile alan bazında karşılaştırma yapılmadı.

**Tarım zinciri riski:** eşleşmeyen tek büyük olay (Adana 2012; 290 saat, düşük tepe FRP) bu riskin bir örneği. "34 olaylık tarım zinciri" sayısı bu oturumda ayrıca doğrulanmadı.

**İl × ay doğrulaması:** il düzeyinde ayrı LOYO yapılmadı. Uygulama il seçilince bunu "doğrulanmadı" uyarısıyla açıkça yazıyor; il kıyasları için ölçülen olay sayıları kullanılmalı.

**Kaynak kod:** artık pakette (`kaynak_kod/`: `src/`, `tools/check_all.py`, `audit/`, `docs/`; çalıştırma sırası `kaynak_kod/NASIL_CALISTIRILIR.md`). Ham FIRMS verisi (≈127 MB) boyut nedeniyle pakette değil; nereden indirileceği yazılı. Paket klasöründe veri hattı yeniden koşturulmadı.

## 11. Sınırlar

1. **Risk tahmini yoktur**; hotspot yangın sayısı değildir (1.414.674 nokta → 471.978 olay).
2. **2026 eşdeğer seri düşük güvenlidir**: Aqua gündüz geçiş medyanı 10,70 UTC (2015) → 11,92 (2025) → 12,65 (2026) (`aqua_gunduz_gecis_utc_*`); eşzamanlı Aqua–VIIRS çift payı 0,839 → 0,487 → 0,182 (`aqua_viirs_esz_cift_payi_*`); 2026 bandı gerçek MODIS'i ayların yalnız 0,545'inde kapsar (`harm_2026_bant_kapsama`; LOYO dönemi 0,9226) (ölçüldü). "Kaymasız" kalibrasyon varyantı ölçülmedi (doğrulanmadı).
3. **MODIS sonrası dönem** (Terra Şubat 2027, Aqua Eylül 2027; NASA Earth Observer 29 Aralık 2025, `gercek_dogrulama.json`) bağımsız doğrulanamaz; aylık ülke bandı geniştir (−59,57…+74,99 %).
4. **Sıçrama "çözüldü" denmez**: harmonize sıçrama doğal aralığın dışındadır; ölçüt post-hoc değişti; 2009–11 tabanı olağandışı yüksektir.
5. **(ii) ≈ (i)** ay × bölgede; yöntemin cebirsel biçimi belgede yok; seçim ölçütünün önceden sabitlendiği doğrulanamaz.
6. **Anız ve orman adayı**: kural tabanlı tahmindir; yer/arazi doğrulaması yok; ay tek başına ayırmaz (kaldıraç 0,928).
7. **Sanayi uyuşması** MODIS döneminde zayıf (0,2278; referans seyrek); referans seti küçük (26 tesis, 8 yangın); tesis yakalama 0,4777; STA maskesi karşılaştırılmadı.
8. **Gözlem kapsamı bir çıkarımdır** (129 uydu-gün); geçiş pencereleri yüzdeliklerden türetildi; ayak izi dikdörtgeni kuzey–güney varsayar.
9. **Tarım zinciri** vakaları (34 olay) açık.
10. **Güven eşlemesi** zayıf ilişkili (Spearman 0,2138); öğrenilmiş eşleme FIRMS'i geçemedi.
11. **İl düzeyinde eşdeğer seri** doğrulanmadı (ay × il WAPE 46,27 %).
12. **Mevcut ay** kısmi (12 gün) ve %100 NRT'dir (oran 0,127 MODIS, 0,243 VIIRS; MODIS'e özgü ek düşüşün nedeni doğrulanmadı).
13. **Zaman:** sabit UTC+3; 2016 öncesi kış etkisi 88 satır.
14. **Gerçek dünya doğrulaması:** yalnız en büyük 20 olay, yakalama oranı ölçülmedi, kaynaklar çoğunlukla ikincil (§9).
15. Ekran okuyucu testi yapılmadı (doğrulanmadı); FIRMS API çalıştırılmadı (arşiv elle indirildi).
16. Fizik (§1) literatür özetidir; sabitlerin ve algoritma eşiklerinin projede yeniden türetilmesi yapılmadı. Piksel geometrisinin analitik formülü belgede yok.

---

## 12. Kaynakça

**Literatürden** (bu raporun kaynakları arasındaki proje belgeleri yalnız yazar–yıl düzeyinde atıf verir; tam künyeler yazar belleğine dayanır ve yayımlamadan önce doğrulanmalıdır):

- Kaufman, Y. J., Justice, C. O., Flynn, L. P., ve ark. (1998). Potential global fire monitoring from EOS-MODIS. *Journal of Geophysical Research*, 103(D24), 32215–32238.
- Wooster, M. J., Zhukov, B., Oertel, D. (2003). Fire radiative energy for quantitative study of biomass burning: derivation from the BIRD experimental satellite and comparison to MODIS fire products. *Remote Sensing of Environment*, 86, 83–107.
- Giglio, L., Schroeder, W., Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. *Remote Sensing of Environment*, 178, 31–41.
- Schroeder, W., Oliva, P., Giglio, L., Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: algorithm description and initial assessment. *Remote Sensing of Environment*, 143, 85–96.

**Proje belgeleri:** `belgeler_ve_denetim/yontem_ozeti.md`; `belgeler_ve_denetim/{temizlik,kumeleme,harmonizasyon,takvim,arayuz}_yontemi.md` (yontem_ozeti üzerinden); `belgeler_ve_denetim/bulgular.md` (F2-07, F1-05, F2-09 ...); `belgeler_ve_denetim/gercek_dogrulama.md` ve `.json`; `arayuz/data/metrics.json`; `arayuz/i18n/sci_tr.json`; `raporlar/calisma_prensibi.md`; `raporlar/juri_sunum.md`.

**Bağımsız kaynaklar** (gerçek dünya doğrulaması; `gercek_dogrulama.json` genel bölümü):

- NASA FIRMS, MODIS/VIIRS aktif yangın öznitelikleri: <https://earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs>
- NASA Earthdata, MODIS/VIIRS sensör özellikleri blogu: <https://www.earthdata.nasa.gov/news/blog/characteristics-viirs-modis-oli-sensors-effects-spatial-extent-daily-active-fire-data>
- NASA, Terra: <https://science.nasa.gov/science-research/earth-science/terra-the-end-of-an-era> ve <https://science.nasa.gov/blogs/science-news/2026/02/12/terra-adjusts-instrument-operations-to-extend-mission-life>
- MODIS Land haberleri: <https://modis-land.gsfc.nasa.gov/news.html>
- bianet, güney/güneybatı 2021 yangın analizi (GTÜ): <https://bianet.org/english/environment/248673-study-83-000-hectares-of-forests-burned-in-turkey-s-south-and-southwest-in-two-weeks-of-fires>
- BirGün, OGM 2021 raporu: <https://www.birgun.net/haber/orman-genel-mudurlugu-raporu-yanan-orman-alani-onceki-yila-oranla-alti-kat-artti-378913>
- Olay başına kaynaklar (haber ve resmî açıklama bağlantıları) `belgeler_ve_denetim/gercek_dogrulama.md` tablosundadır.
