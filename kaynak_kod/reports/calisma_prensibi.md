# Çalışma Prensibi Raporu

Veri sürümü: FIRMS MODIS C6.1 + VIIRS 375 m, 2000–2026 (son gün 2026-11-12), 1.414.674 nokta, veri şeması v1, `reports/metrics.json` üretimi 2026-11-13T09:07:17Z · Üretim tarihi: 2026-11-13 09:42 UTC
Denetim durumu: check_all: 25 geçti, 0 kaldı, 0 atlandı; denetçi bulguları: açık yüksek 0, açık orta 0, açık düşük 5 — denetçi kapısı açık yüksek bulgu içermiyor

> Bu rapor, uygulamanın nasıl çalıştığını **öğrenmek** içindir. Her kural iki katmanda anlatılır: önce **Basitçe** (benzetme), sonra **Teknik olarak** (tanım, formül, eşik, gerekçe, kodda nerede). Tüm sayılar `reports/metrics.json` dosyasından gelir; yanlarındaki parantez dürüstlük etiketidir: **ölçüldü** (veriden sayıldı/hesaplandı), **tahmini** (modele/kurala/çıkarıma dayanır), **doğrulanmadı** (bağımsız kanıt yok). "Aktivite" her yerde tarihsel hotspot yoğunluğu demektir; yangın riski veya tehlike tahmini değildir.

## 1. Uygulama ne yapar?

**Basitçe:** Elimizde iki farklı termometre var. Eski olan (MODIS, 2000'den beri) kaba, yeni olan (VIIRS, 2012'den beri) çok hassas. Yeni termometre geldiği yıl, "yangın sayısı" kâğıt üzerinde bir anda patlıyor; oysa yangınlar artmadı, yalnızca daha çok şey görmeye başladık. Bu uygulama (1) yangın olmayan sıcak yerleri (fabrika bacası, deniz, volkan) ayırır, (2) aynı yangının birçok fotoğrafını tek yangın sayar, (3) yeni termometrenin ölçümünü eski termometrenin diline çevirip 20+ yıllık karşılaştırılabilir bir seri yapar, (4) bunun üstünde yıl×ay yangın aktivite takvimi gösterir.

**Teknik olarak:** NASA FIRMS MODIS (Terra, Aqua) ve VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21) aktif yangın tespitleri Türkiye için 2000–2026 arasında 1.414.674 nokta (ölçüldü) satırdır (MODIS 259.707 nokta (ölçüldü), VIIRS 1.154.967 nokta (ölçüldü); son gün 2026-11-12; 61.147 (ölçüldü) nokta NRT, yani NASA `type` etiketi yok). Hat şudur:

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

**Basitçe:** 27 ayrı Excel dosyası tek bir temiz tabloya çevrilir: her satır bir tespit. Hangi satırın hangi dosyadan geldiği ve ham değerin kendisi saklanır; ham veriye dokunulmaz.

**Teknik olarak:** Şema `docs/04_VERI_SOZLESMESI_TASLAK.md` (kesin v1); `pid` kalıcı satır kimliğidir. Güven kodlaması tek yerdedir (K10): MODIS 0–100 sayısal (düşük 0–29, nominal 30–79, yüksek 80–100), VIIRS harf (l/n/h → düşük/nominal/yüksek); `src/config/esikler.json → guven`, okuyan `src/config/config.py`. Zaman `t_utc` olarak saklanır, `day_tr` sabit UTC+3 ile hesaplanır ve yıl kırpılmaz (C07). Bağımsız denetçi ham xlsx'i farklı bir yöntemle yeniden saydı: beklenen 1.414.674 = bulunan, fark 0 (`audit/yeniden_hesap.json`, ölçüldü). Gözlem kapsamı (hangi uydu hangi gün çalıştı) NASA geçiş listesi değil, tespit sayılarından **çıkarımdır**; 129 uydu-gün (tahmini). Kod: `src/pipeline/`.

## 3. Temizlik: satır silinmez, etiketlenir

**Basitçe:** Gelen sıcak noktaların hepsi orman yangını değil. Bacalar, deniz üstündeki gemiler/platformlar, volkanlar ve tarla yakmaları da var. Hiçbirini çöpe atmıyoruz; her birine "bu bir baca", "bu anız" gibi bir etiket yapıştırıyoruz. İsteyen etiketi kapatıp hepsini görebilir.

**Teknik olarak** (`docs/temizlik_yontemi.md`, `src/cleaning/`): sonuç etiketler (`points_status.parquet`):

| Etiket | Nokta | Etiket durumu |
|---|---|---|
| **Ham toplam** | 1.414.674 | ölçüldü |
| temiz (yangın olarak sayılır) | 827.043 | ölçüldü |
| anız (olay düzeyinde etiket) | 217.179 | ölçüldü |
| NASA statik kaynak (type=2) | 328.379 | ölçüldü |
| deniz (type=3) | 8.848 | ölçüldü |
| volkan (type=1) | 5 | ölçüldü |
| sanayi (bizim kural) | 27.012 | ölçüldü |
| kalıcı ısı kaynağı, belirsiz | 6.208 | ölçüldü |

Temiz + anız noktalar (1.044.222 nokta (ölçüldü)) kümelemeye girer; ham noktaların 23,8 % (ölçüldü) NASA etiketiyle, 2,3 % (ölçüldü) kendi kuralımızla ayrılmıştır. Yöntem **kural tabanlıdır**; makine öğrenmesi kullanılmadı. Eşikler yıl dışarıda bırakma (LOYO) ile seçildi.

### 3.1 NASA etiketleri korunur (U-07)

**Basitçe:** NASA bazı noktalara zaten "volkan", "deniz", "sabit kara kaynağı" demiş. Ona güveniyoruz.
**Teknik olarak:** `type=1 → volkan`, `type=3 → deniz`, `type=2 → statik_nasa`. NRT'de bu etiket yok; arşivdeki komşu noktalardan miras alınır (`nasa_miras_payi`): 12.940 (ölçüldü) nokta. NRT deniz telafisi zayıf ve doğrulanmadı.

### 3.2 Sanayi kuralı: yıllarca aynı yerde yanan baca (U-08)

**Basitçe:** Bir orman yangını beş farklı yılda, yılın sekiz ayında aynı 1 km'lik karede sürmez. Sürüyorsa orası fabrika, rafineri ya da meşaledir.
**Teknik olarak:** 0,01° hücrede, iki sensör birlikte: farklı yıl ≥ Y, farklı takvim ayı ≥ M, farklı gün ≥ N ve aktif yıllarda yıl içi ay sayısı medyanı ≥ S → `sanayi`. Eşikler (N, M, Y, S) LOYO'da NASA type=2'ye karşı F1 enbüyüklenerek seçildi (eşik tablosu §10). LOYO uyuşması: kesinlik 0,9199 (ölçüldü), duyarlılık 0,9712 (ölçüldü). **Dikkat:** NASA type=2 yer gerçeği değil bir maskedir; bu sayılar "uyuşma"dır. VIIRS döneminde kesinlik 0,924 (ölçüldü), MODIS döneminde 0,2278 (ölçüldü): referans seyrek olduğu için; kuralın 'sanayi' dediği MODIS noktalarının %66,6 bilinen bir tesise yakın.

### 3.3 Kalıcı ısı kaynağı (belirsiz)

**Basitçe:** Düzenli ama bacadan farklı davranan yerler (kömür ocağı, çöplük). "Baca" demeden ayrı sepete koyarız: 6.208 (ölçüldü) nokta.
**Teknik olarak:** Y ve M koşulunu sağlayan, N veya S'yi sağlamayan ve tespitlerinin en az `kalici_gece_payi` kadarı gece olan hücre (gece şartı: tarla yakması gündüz yoğundur).

### 3.4 Gerçek yangını silmeme: yangın koruması

**Basitçe:** Rafineri yanında gerçek orman yangını çıkarsa rafineri karesindeki noktaları da "baca" diye atmak yanlış olur. O gün çevrede normal karelerde de ateş varsa noktayı temiz bırakırız.
**Teknik olarak:** Kural-sanayi/kalıcı noktası, aynı TR gününde komşuluktaki kalıcı olmayan hücrelerde en az G tespit varsa `temiz` kalır: 1.748 (ölçüldü) nokta. Referans yangınlardaki noktaların %99,8 kadarı korunur (tahmini; küçük set).

### 3.5 Anız takvimi (U-09)

**Basitçe:** Hasattan sonra tarlada sap yakılır; küçük, kısa, zayıf ateşlerdir ve her yıl aşağı yukarı aynı aylarda olur, ama bölgeden bölgeye değişir. Hangi bölgede hangi ayların "anız ayı" olduğunu 20 yıllık veriden öğreniyoruz. Hile olmasın diye bir yılın anız aylarını hep **o yıl hariç** öğreniyoruz.
**Teknik olarak** (`src/cleaning/aniz_takvim.py`, `olay_aniz.py`): küçük aday = FRP < F (MODIS ölçeğinde 15 MW (ölçüldü); VIIRS eşdeğeri sabit oranla değil yüzdelik eşleştirmeyle 4,4 MW (ölçüldü), K8) ve çevresinde az tespit. Profil: 7 bölge × ay payları. **Nihai karar olay düzeyindedir**: olay ≤ 3 tespit (MODIS ölçeğinde tekil eşleştirme birimi `n_mcell` sayılır, çünkü VIIRS aynı ateşi 3–4 nokta görür), ≤ 12 saat, düşük FRP ve olayın bölgesinin o yıl hariç öğrenilmiş anız ayında → olay `aniz`. Sonuç 217.179 (ölçüldü) nokta. **Dürüst bulgu:** LOYO kaldıraç 0,928 (ölçüldü): "ay" tek başına küçük ateşi büyükten ayırmaz; ayırıcı olan büyüklük/süre/FRP koşuludur.

**Bağımsız doğrulama (döngüsellik önlemi):** (a) ESA WorldCover 2021 (veriden bağımsız arazi haritası): anız noktalarının %79,3 ekili alanda; büyük temiz yangınların %50,3 ekili, %32,1 ağaçlı alanda; sanayi/kalıcı noktaların %56 yapılaşmış alanda. (b) Kaba ulusal hasat penceresiyle uyum %74,2 (tahmini). **Doğrulanmadı:** saha, yanmış alan veya resmi yangın kaydıyla karşılaştırma yok.

### 3.6 Referans (bağımsız) doğrulama (C13)

**Basitçe:** Kuralı, FIRMS'ten bağımsız bir listeyle sınadık: 26 bilinen sanayi tesisi (OpenStreetMap) ve 8 bilinen yangın. Tesis sayısı yangından çok olduğu için "her tesise ve her yangına eşit oy" verdik.
**Teknik olarak:** Dengeli kesinlik 0,9711 (tahmini), tesis yakalama (makro duyarlılık) 0,4777 (tahmini), tesis düzeyi 0,4783 (tahmini), yangın başına yanlış işaret 0,0142 (tahmini). Yani **bazı tesisler kaçıyor** (özellikle termik santraller). Static Thermal Anomalies maskesiyle karşılaştırma yapılamadı (yok (doğrulanmadı)).

## 4. Eşleştirme: MODIS'in ayak izi (U-02)

**Basitçe:** MODIS'in bir pikseli yerde büyük bir kare; VIIRS aynı yere 3–4 küçük kare düşürür. "MODIS'te 1, VIIRS'te 4 yangın" sorunu bundandır. Çözüm: her VIIRS noktasını, kendisini kaplayan MODIS karesine bağlamak.
**Teknik olarak** (`src/harmonize/eslestirme.py`): ayak izi = MODIS merkezinde `scan × track` km dikdörtgen + yarım VIIRS pikseli tamponu (0,375 km). Bir VIIRS noktası birden çok ize düşerse sırasıyla eşzamanlı iz, en küçük normalize uzaklık, en küçük zaman farkı, en küçük alan seçilir; nokta tek hücreye gider ve FRP bölünmez. İze düşmeyen VIIRS noktası (yalnız VIIRS) 0,01° ızgara yedeğine gider. Ölçüm: 1.154.967 nokta (ölçüldü) VIIRS noktasının 174.203 nokta (ölçüldü) tanesi MODIS izinde; MODIS izi başına ortalama 3,349 nokta (ölçüldü) VIIRS noktası; sabit ızgara aynı izi 1,764 (ölçüldü) hücreye bölerdi (bölünen iz oranı %46,6).

## 5. Kümeleme: aynı yangını bir kez say (U-10, U-11, U-12)

**Basitçe:** Uydular aynı yangının birçok fotoğrafını çeker. İki fotoğraf yakın yerde ve yakın zamandaysa aynı yangındır; A–B yakın, B–C yakınsa üçü de aynıdır (zincir). MODIS ve VIIRS fotoğrafları **birlikte** değerlendirilir; böylece aynı yangın iki kez sayılmaz.
**Teknik olarak** (`src/clustering/`, `docs/kumeleme_yontemi.md`): olay = bağ grafiğinin bağlı bileşeni (union-find). Bağ: mesafe ≤ D **veya** MODIS–VIIRS çiftinde VIIRS merkezi MODIS ayak izinin içinde; ve zaman koşulu. D = 1 km, eşleştirme modu ayakizi_capraz, boşluk kuralı gecis (L = 3 geçiş penceresi, Hmax = 72 saat; kaynak `src/config/esikler.json`).

**Boşluk kuralı (U-11), basitçe:** "14 saattir görmedim, söndü mü?" sorusunun cevabı uydunun o sürede gerçekten geçip geçmediğine bağlıdır. Boşluğu saatle değil **kaçırılan geçişle** sayarız: uydu geçti ve görmediyse "kaçırma", hiç geçmediyse beklenir. Teknik: |Δt| ≤ Hmax ve aradaki gözlenmiş geçiş penceresi ≤ L (eşik tablosu §10). Günlük geçiş saati ~3 saat kaydığı için sabit H=24 bir yangını gereksiz bölerdi; geçiş kuralı bunu düzeltir (swath verisi olmadığı için pencereler çıkarım, tahmini).

Sonuç: 471.978 (ölçüldü) olay; ortak kümeleme çakışma döneminde 380.975 (ölçüldü) olay verir, sensörler ayrı kümelenseydi 440.176 olay (ölçüldü) olurdu: **59.201 olay (ölçüldü) çifte sayım önlenir**. Üçlü sınıf: ortak 35.651 olay (ölçüldü), yalnız MODIS 57.543 olay (ölçüldü), yalnız VIIRS 287.781 olay (ölçüldü), tek sensör dönemi 91.003 olay (ölçüldü). MODIS olaylarının VIIRS'te de görülme payı %38,2; ayak izi eşleştirmesi bunu sabit 1 km kuralına göre (%35,5) artırır ama asıl neden eşleştirme değil, Terra'nın sabah geçişinin VIIRS'le eşzamanlı olmamasıdır (Aqua ile eşzamanlıyken bile 1 km içinde VIIRS payı %53,1).

**Zincirleme riski:** Bitişik bağımsız küçük yangınlar köprülenip dev olaya dönüşebilir. En büyük olay 6.740 (ölçüldü) tespit (gerçek mega yangın, 2021 Manavgat); temiz olmayan nokta zincire köprü olamaz. Kümeleme algoritması, tam O(n²) kaba kuvvetle 88 (ölçüldü) karşılaştırmada, 0 karşılaştırma (ölçüldü) farkla birebir aynı sonucu verdi (C03).

## 6. Harmonizasyon: VIIRS'i MODIS'in diline çevirmek (U-01, U-04, U-05)

**Basitçe:** "MODIS bu ayı görseydi kaç sayardı?" sorusunu cevaplıyoruz. Hassas termometrenin ölçümünü eski termometrenin diline çeviriyoruz; hassas ölçüm de çöpe gitmiyor, yanında ayrı bir katman olarak duruyor (iki çıktı: karşılaştırma için eşdeğer seri, ayrıntı için ham VIIRS).

**Soru 3 bilimsel seri kararı (`docs/01_ISTEKLER.md` §E):** Çok yıllı karşılaştırma, yıl×ay matrisi, trend ve anomalide varsayılan ana seri **MODIS-eşdeğer seri** (`olay_esdeger` / `modis_esdeger` + LOYO %95 belirsizlik bandı) olarak belirlenmiştir; çünkü 2000–2011 döneminde VIIRS yoktu ve sensör geçişlerinden doğan sıçramalar gerçek yangın eğilimiyle karıştırılmamalıdır. Buna karşılık 375 m ham VIIRS noktaları ve üçlü sınıf (`ortak`, `yalniz_viirs`, `yalniz_modis`) katmanları harita, laboratuvar ve müfettişte yan yana eksiksiz sunulur. Kullanıcı üst bardaki `#sciModeBtn` düğmesinden ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya gelişmiş süzgeçlerdeki `#seriesSel` menüsünden (`src/app/main.js` `S.aggSeries`) bu seçimi tek tıkla değiştirebilir.

**Teknik olarak** (`src/harmonize/`, `docs/harmonizasyon_yontemi.md`):

1. **Gözlem eforu.** VIIRS toplamı, o gün gözleyen VIIRS uydu sayısına bölünür (2018'de N20, 2023'te N21 eklendi). Etkisi: N20 geçişinde ham VIIRS 24,34 % (ölçüldü), eforlu −37,31 % (ölçüldü), gerçek MODIS −41,59 % (ölçüldü).
2. **MODIS etkin tespit sınırı (FRP50).** Aqua'nın bir VIIRS hücresini yarı olasılıkla gördüğü toplam FRP: genel 64,88 MW (tahmini), gündüz 73,98 MW (tahmini), gece 20,54 MW (tahmini) (etkin sınır; fiziksel algılama sınırından büyüktür, tahmini).
3. **Güven sınıfı çevirisi (S1).** Aynı yangına aynı anda bakan Aqua–VIIRS 40.368 (ölçüldü) çiftiyle VIIRS düşük/nominal/yüksek payları MODIS yüzdesine eşlendi: öğrenilen MODIS sınırları [35 ; 82] MODIS % (tahmini) (FIRMS'in kendi cetveline yakın), yıl dışarıda bırakmada çok kararlı ([34 ; 36] MODIS % (ölçüldü) ve [81 ; 82] MODIS % (ölçüldü)). Ama iki uydunun tek yangındaki güveni zayıf ilişkili (Spearman 0,2138 (ölçüldü)) ve öğrenilmiş eşleme FIRMS'i geçemedi (kappa 0,1765 (ölçüldü) karşı 0,1918 (ölçüldü)). Bu yüzden arayüzde varsayılan ham FIRMS sınıfıdır.
4. **Yöntem yarışı (K8, sabit oran tuzağı).** Üç yöntem LOYO ile yarıştı (hedef: gerçek MODIS tespiti, ay×bölge): (i0) tek sabit oran, efor yok (WAPE 52,68 % (ölçüldü), yıllık MAPE 42,12 % (ölçüldü), R² −1,7204 (ölçüldü)); (i) tek sabit oran, eforlu (WAPE 30,64 % (ölçüldü), MAPE 4,83 % (ölçüldü)); (ii) bölge×mevsim×FRP büyüklüğü oranı, eforlu (WAPE 30,63 % (ölçüldü), MAPE 8,33 % (ölçüldü)); (iii) FRP eşik eğrisi (WAPE 31,91 % (ölçüldü)). **Dürüst okuma:** asıl kazanç efor düzeltmesidir; (ii) ile (i) ay×bölgede ayırt edilemez (fark %95 aralığı [−2,97 ; 4,26] yüzde puan (tahmini)). (ii) uygulamanın birimi (ay×bölge) için seçildi, üstünlük iddiası değildir. Kazanan: (ii) bölge × mevsim × FRP büyüklüğü oranı, eforlu (tahmini).
5. **Belirsizlik bandı.** LOYO artıklarının yüzdeliklerinden: aylık ülke toplamı için %95 hata bandı [−59,57 ; 74,99] % (tahmini); bant gerçek MODIS'i ay×ülkede %92,3, ay×bölgede %95,6 oranında kapsadı. Eski dönem (2000–Temmuz 2002, yalnız Terra) düzeltilmez, düşük güven bayraklıdır.
6. **Sıçrama ölçütü.** Sıçrama = geçiş sonrası 3 yıl ortalaması / geçiş öncesi 3 yıl ortalaması − 1. Ham 143,13 % (ölçüldü); harmonize −41,35 % (tahmini); aynı pencerede gerçek MODIS −44,9 % (ölçüldü); harmonizasyonun eklediği fark 3,55 yüzde puan (tahmini). 2012 sonrası harmonize değerler LOYO tahminleridir (o yıl öğrenmede yoktu).
7. **Yörünge kayması.** Aqua öğle geçişi 10,7 saat (UTC) (ölçüldü) (2015) → 12,65 saat (UTC) (ölçüldü) (2026) kaydı; Aqua–VIIRS eşzamanlı çift payı %83,9 → %18,2. Bu yüzden **2026 eşdeğer değerleri eğitim rejiminin dışındadır**, düşük güven bayraklıdır (bant kapsaması %54,5, doğrulanmadı).

## 7. Takvim ve anomali (U-16, N-05, N-06, N-07)

**Basitçe:** Her ilin her günü için "kaç sıcak nokta / kaç olay" defteri tutulur, yanına "o gün uydular gerçekten bakabildi mi?" yazılır. Bakılamayan gün "sıfır yangın" demek değildir. "En yoğun ay", geçmiş yılların o ayının **medyanı** en yüksek olan aydır; iki ay birbirine çok yakınsa "ayırt edilemez" denir. Anomali: bir yılın bir ayı, o yıl hariç diğer yılların aynı ayıyla kıyaslanır.

**Teknik olarak** (`docs/takvim_yontemi.md`, `src/analytics/`): aylık sayım, kesinti günleri paydadan düşülerek ölçeklenir (C06); ay yarımsa veya neredeyse hiç bakılamadıysa hücre boş kalır, sıfır yazılmaz. Birim: 89 birim (ölçüldü) (ülke, bölge, il). Medyan ve sıralama; ayırt edilemezlik için komşu ay göreli fark eşiği + yıl bootstrap'ı. Anomali: log1p ölçeğinde sağlam z = (x − medyan)/max(1,4826·MAD, taban), normal yıllar ve test yılı hariç, |z| ≥ 2. Sonuçlar: MODIS ham serisinde ilk üç ay Haz > Eyl > Eki (ölçüldü), temiz serisinde Haz > Eyl > Ağu (ölçüldü), MODIS-eşdeğer seride Ağu > Eyl > Haz (tahmini), olay serisinde Eyl > Ağu > Eki (tahmini). Temizliğin etkisi: ham ve temiz sıralamalar il düzeyinde ilk üç ayın 79 % (tahmini) oranında değişiyor. Mevcut ay, geçmiş yılların **aynı ilk günleriyle** kıyaslanır (kısmi ay açıkça yazılır): son veri günü 2026-11-12, kısmi gün 12 gün (ölçüldü), NRT payı 100 % (ölçüldü), MODIS oranı 0,127 kat (tahmini), VIIRS oranı 0,243 kat (tahmini); MODIS'e özgü ek düşüşün nedeni MODIS'e özgü ek düşüş: sensör ömrü sonu, NRT veya yörünge kayması şüphesi (doğrulanmadı). Eşdeğer serilerde anomali işaretlerinin 33,53 % (tahmini) oranı belirsiz banda düşer.

## 8. Arayüz

**Basitçe:** Tek sayfalık, internetsiz açılan bir uygulama: harita, takvim, sıçrama grafiği, birleştirme laboratuvarı, piksel büyümesi ve dışa aktarma.
**Teknik olarak** (`src/app/`): kütüphaneler yerelde (C21); ekrandaki her sayı `metrics.json` veya agg tablolarından gelir (C14), sabit metrik/`Math.random` yoktur (C15); TR/EN (C18); CSV UTF-8 BOM ile (C17). Varsayılan takvim/trend serisi `olay_esdeger`dir (Soru 3 bilimsel kararı); üst bardaki `#sciModeBtn` ("MODİS-Eşdeğer (Bilimsel)" ↔ "Ham Olay Serisi") veya gelişmiş süzgeçlerdeki `#seriesSel` menüsü (`src/app/main.js` `S.aggSeries`) üzerinden tek tıkla değiştirilebilir, ayrıca `#quickExportBtn` ile süzülmüş olaylar anında CSV indirilir. Performans: eşik değişince tüm görünümler 0,253 s (ölçüldü) içinde yeniden çizilir (302.863 (ölçüldü) olay; tek ölçüm, bu makine). Erişilebilirlik: klavye %88,4, adlı öğe %100, en düşük kontrast 4,59 (ölçüldü); ekran okuyucu testi yapılmadı (doğrulanmadı). Stil: `referans/STIL_NOTU.md`.

## 9. Duyarlılık: eşikler değişirse sonuç ne kadar oynar? (C12)

**Basitçe:** Cetveli biraz kaydırınca cevap ne kadar kayıyor? Çok kayıyorsa o sayıyı kuralıyla birlikte söylemek zorundayız.
**Teknik olarak:** Her eşik için en az üç değer denendi.

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


**N** (en az 4 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma | loyo_precision_type2 | loyo_recall_type2 |
|---|---|---|---|---|---|---|---|---|---|
| 10 | 27.090 | 6.130 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9699 |
| 20 | 27.090 | 6.130 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9699 |
| 40 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9698 |
| 80 | 26.769 | 6.360 | 1.044.313 | 1.747 | 0,9711 | 0,4777 | 0,9982 | 0,9229 | 0,9689 |

**M** (en az 5 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma | loyo_precision_type2 | loyo_recall_type2 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 28.840 | 37.727 | 1.010.875 | 26.738 | 0,9715 | 0,4853 | 0,9982 | 0,9173 | 0,9728 |
| 6 | 28.717 | 14.151 | 1.034.574 | 8.772 | 0,9714 | 0,4836 | 0,9982 | 0,9177 | 0,9728 |
| 8 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9698 |
| 10 | 26.096 | 3.402 | 1.047.944 | 727 | 0,9701 | 0,461 | 0,9982 | 0,9242 | 0,9667 |
| 12 | 22.387 | 1.530 | 1.053.525 | 1.080 | 0,9645 | 0,3869 | 0,9982 | 0,9318 | 0,9528 |

**Y** (en az 4 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma | loyo_precision_type2 | loyo_recall_type2 |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 28.962 | 6.918 | 1.041.562 | 1.813 | 0,9727 | 0,5079 | 0,9982 | 0,9185 | 0,9732 |
| 3 | 28.625 | 6.856 | 1.041.961 | 1.848 | 0,9712 | 0,4794 | 0,9982 | 0,9196 | 0,9727 |
| 5 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9698 |
| 8 | 24.823 | 5.234 | 1.047.385 | 1.892 | 0,9711 | 0,4774 | 0,9982 | 0,9279 | 0,9487 |

**S** (en az 4 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma | loyo_precision_type2 | loyo_recall_type2 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 33.441 | 2.271 | 1.041.730 | 4.723 | 0,9715 | 0,4847 | 0,9982 | 0,9033 | 0,9753 |
| 2 | 32.247 | 2.741 | 1.042.454 | 3.631 | 0,9711 | 0,4777 | 0,9982 | 0,9062 | 0,9747 |
| 4 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 | 0,9221 | 0,9698 |
| 6 | 22.682 | 9.773 | 1.044.987 | 1.739 | 0,9711 | 0,4777 | 0,9982 | 0,9329 | 0,9486 |

**F** (en az 5 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | F_viirs_esdeger | yuzdelik | aniz_adayi | kucuk_temiz | loyo_kapsama | loyo_kaldirac |
|---|---|---|---|---|---|---|
| 5 | 0,67 | 0,0443 | 21.071 | 28.682 | 0,7219 | 0,9655 |
| 10 | 2,75 | 0,3102 | 138.679 | 199.649 | 0,7049 | 0,903 |
| 15 | 4,4 | 0,4993 | 247.112 | 336.943 | 0,749 | 0,928 |
| 20 | 5,79 | 0,6152 | 306.266 | 414.117 | 0,7589 | 0,917 |
| 30 | 8,41 | 0,7495 | 369.564 | 494.731 | 0,7714 | 0,9126 |

**koruma_G** (en az 5 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma |
|---|---|---|---|---|---|---|---|
| 1 | 26.259 | 5.399 | 1.045.784 | 3.310 | 0,9704 | 0,4672 | 0,9982 |
| 2 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 |
| 3 | 27.161 | 6.542 | 1.043.739 | 1.265 | 0,9711 | 0,4785 | 0,9982 |
| 5 | 27.286 | 6.911 | 1.043.245 | 771 | 0,9712 | 0,4799 | 0,9982 |
| 10 | 27.321 | 7.248 | 1.042.873 | 399 | 0,9712 | 0,4801 | 0,9982 |

**kalici_gece** (en az 3 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | sanayi | kalici_belirsiz | temiz | yangin_korumasi | ref_precision | ref_recall | yangin_koruma |
|---|---|---|---|---|---|---|---|
| 0,3 | 27.020 | 9.574 | 1.040.848 | 5.184 | 0,9715 | 0,4847 | 0,9982 |
| 0,5 | 27.012 | 6.208 | 1.044.222 | 1.748 | 0,9711 | 0,4777 | 0,9982 |
| 0,7 | 26.925 | 4.823 | 1.045.694 | 912 | 0,9711 | 0,4776 | 0,9982 |

**aniz_olay_max_tespit** (en az 5 değer; ölçüldü, `ref_*` sütunları tahmini)

| deger | olay_n_mcell | nokta_n_mcell | olay_sensor_max | nokta_sensor_max | olay_toplam | nokta_toplam |
|---|---|---|---|---|---|---|
| 1 | 154.841 | 175.406 | 141.104 | 142.768 | 139.440 | 139.440 |
| 2 | 167.540 | 209.564 | 160.706 | 182.937 | 159.838 | 180.236 |
| 3 | 169.115 | 217.179 | 165.347 | 197.172 | 164.997 | 195.713 |
| 5 | 169.464 | 219.864 | 168.170 | 209.575 | 168.092 | 209.093 |
| 10 | 169.475 | 220.032 | 169.322 | 217.908 | 169.311 | 217.780 |


Okuma: olay sayısı D ve H'ye güçlü bağlıdır; bu yüzden "olay sayısı" her zaman kuralıyla birlikte verilmelidir.

## 10. Eşik tablosu (K9: tek yapılandırma dosyası)

| Eşik | Değer | Birim | Gerekçe (`src/config/esikler.json`) |
|---|---|---|---|
| N | 40 | farklı gün (tüm yıllar) | Sanayi kuralı: 0,01° hücrede tüm yıllar boyunca en az N farklı TR gününde tespit. Demo 10 (13 aylık veri) idi; 20 yılla LOYO seçimi (27 katın 20'si aynı (N,M,Y,S)'yi seçti) |
| M | 8 | farklı takvim ayı (1-12) | Sanayi kuralı: hücrede tespit görülen farklı TAKVİM ayı sayısı (yıllar birleşik; 'kaç farklı mevsimde'). Demo M=4 (yıl-ay) idi; anlam 20 yıl için takvim ayına çevrildi |
| F | 15 | MW (MODIS ölçeği) | Anız adayı: FRP bu değerin altında (küçük ateş). 15 MW = MODIS arşiv type=0 FRP medyanı (ölçüldü, metrics: temizlik_F_modis_medyan). VIIRS eşdeğeri sabit oranla değil yüzdelik eşleştirmeyle hesaplanır (K8) |
| D | 1 | km | Olay kümeleme mesafesi |
| H | 24 | saat | Olay kümeleme zaman boşluğu |
| aniz_aylari | [8 ; 9 ; 10 ; 11 ; 12] |  | Demo'nun tek, ülke çapı anız mevsimi (Ağustos–Aralık). v2'de etkin anız ayları bölgeye göre veriden öğrenilir (temizlik.aniz_ay_kurali; çıktı audit/aniz_takvimi.json, yıl dışarıda bırakmalı). Bu değer yalnız duyarlılık karşılaştır… |
| eslesme_tamponu_km | 0,375 | km | VIIRS yarım piksel (375 m / 2 ≈ 0,19 km; 375 m tam piksel tampon olarak başlangıç) |
| G | 3 | gün | Kesinti tespiti: bir uydu Türkiye'de ardışık en az G gün sıfır tespit verirse aday kesinti. Türkiye'de gündüz tespiti yapan uydunun 3 gün üst üste sıfır vermesi, tek bir geçişin kaçmasından (1-2 gün) uzun; duyarlılık G=2/3/5 cover… |
| K | 50 | tespit | Kesinti tespiti: aynı günlerde aynı sensör ailesindeki kardeş uydular toplamda en az K tespit verdiyse bölgede yangın vardı, sıfır tespit yangınsızlık değil uydu kesintisidir |
| B | 5 | km | Kıyı tamponu: il çokgeni dışındaki tespit Türkiye sınırına en çok B km ise 'kiyi' (il = en yakın il). MODIS piksel yarı genişliği (~0,5-2 km) + kaba il çokgeni + kıyı sanayisi (İzmit, Aliağa, İskenderun) |
| temizlik.hucre_derece | 0,01 | derece | Kalıcılık hücresi ~1,1 km × ~0,85 km: MODIS nadir pikseli (1 km) ölçeğinde, VIIRS 375 m konum saçılımını tek hücrede toplar |
| temizlik.Y | 5 | farklı yıl | Sanayi kuralı: hücrede tespit olan en az Y farklı takvim yılı (bir yangın yıllarca sürmez, U-08) |
| temizlik.S | 4 | ay/yıl (medyan) | Sanayi kuralı: aktif yıllarda yıl içi farklı ay sayısının medyanı en az S (aynı yıl içinde süreklilik; mevsimlik tarım yakmasını ayırır) |
| temizlik.koruma_yanlis_pay | 0,01 | oran | koruma_G seçimi: NASA type=2 çoğunluklu kalıcı hücrelerdeki noktaların en çok bu payı 'yangın koruması' alacak şekilde en küçük G |
| temizlik.hasat_penceresi | [6 ; 7 ; 8 ; 9 ; 10] | ay | Bağımsız kaba kontrol: hasat sonrası anız penceresi. Hububat hasadı Mayıs sonu başlar (TMO alımları 21 Mayıs 2026), kışlık buğday/arpa hasadı Eylül başında bitmiş (FAO GIEWS, 7 Eylül 2026), mısır hasadı Ağustos ortasında başlar (F… |
| temizlik.nasa_miras_payi | 0,5 | oran | NRT (type yok) noktası, hücresindeki arşiv noktalarının en az bu payı NASA type=2 ise statik_nasa mirası alır (çoğunluk kuralı) |
| temizlik.kalici_gece_payi | 0,5 | oran | kalici_belirsiz: sanayi kuralının Y (yıl) ve M (takvim ayı) koşulunu sağlayıp N veya S koşulunu sağlamayan hücre, tespitlerinin en az bu payı gece ise (çoğunluk gece). Tarla yakması gündüz yoğun; baca/maden/çöplük gece de görülür |
| temizlik.kalici_alfa | 0,001 | olasılık | YALNIZ BAYRAK (status değişmez): hücrenin aktif yıl sayısı, ilin yıllık aktif-hücre oranından kurulan Poisson-binom rastlantı modeline göre P(X>=gözlenen) < alfa ise status_neden'e 'yillik_tekrar' yazılır |
| temizlik.kalici_min_yil | 3 | farklı yıl | yillik_tekrar bayrağı için alt sınır: tek/iki yılda tekrar 'yıllar boyu' sayılmaz |
| temizlik.koruma_komsu_k | 2 | hücre | Yangın koruması komşuluğu: (2k+1)^2 hücre (~5 km) içinde aynı gün kalıcı olmayan hücrelerdeki tespit |
| temizlik.koruma_G | 2 | tespit | Yangın koruması: aynı gün komşulukta kalıcı olmayan hücrelerde en az G tespit varsa kalıcı hücredeki nokta gerçek yangın olabilir, temiz kalır. G, NASA-statik ∩ kural-sanayi hücrelerinde yanlış koruma payı <= koruma_yanlis_pay ola… |
| temizlik.aniz_kucuk_komsu | 3 | tespit | Nokta düzeyi anız adayı: aynı gün 3x3 hücre komşuluğunda en çok bu kadar tespit (demo olay kuralı <=3 tespit ile aynı) |
| temizlik.aniz_olay_max_tespit | 3 | tespit | Olay düzeyi anız: olaydaki temiz tespit sayısı en çok bu (küçük) |
| temizlik.aniz_olay_max_sure_saat | 12 | saat | Olay düzeyi anız: ilk-son tespit arası en çok bu (kısa) |
| temizlik.aniz_olay_sayim | n_mcell |  | aniz_olay_max_tespit hangi büyüklükle sayılır: n_mcell (MODIS ölçeğinde eşleştirme birimi sayısı; sözleşme §5). İki sensörü toplamak (n) VIIRS döneminde aynı ateşi 'büyük' gösterir; sensor_max = max(n_modis, n_viirs) VIIRS'in 375 … |
| temizlik.aniz_ay_kurali | uniform_ustu |  | Bölge × ay profilinde payı 1/12'den büyük aylar anız ayıdır (ortalamanın üstü) |
| temizlik.dusuk_guven_etiketle | hayır |  | Demo varsayılanı 'Güven: Tümü': düşük güven nokta etiketi status'a yazılmaz, status_neden'de bayrak olarak durur (arayüz süzebilir) |
| temizlik.wc_ornek_sayisi | 2.000 | nokta/grup | WorldCover doğrulama örneklemi (statik_nasa grubu bunun dörtte biri) |
| temizlik.wc_tohum | 20.261.113 |  | Örneklem seçimi tekrar üretilebilsin (rastgelelik yalnız seçimde, veri üretmez) |
| temizlik.wc_overview_duzey | 1 |  | COG iç genel görünüm düzeyi 1 = 4× küçültme (~37 m piksel); VIIRS 375 m pikselinden çok ince, okunacak blok sayısını ~16 kat azaltır |
| temizlik.wc_pencere_px | 3 | piksel | Nokta çevresinde ±3 genel görünüm pikseli (~±110 m) pencerede en sık sınıf (konum belirsizliği) |
| temizlik.wc_trafik_mb | 200 | MB | Toplam okuma trafiği üst sınırı; aşılacaksa okuma durur |
| temizlik.wc_buyuk_olay_mcell | 10 | eşleştirme birimi | Doğrulama karşı grubu 'büyük temiz olay': n_mcell en az bu (anız sınırının açıkça üstü) |
| temizlik.viirs_baslangic_yili | 2.012 | yıl | Temizlik dönem kırılımı: bu yıldan önce yalnız MODIS (SNPP VIIRS ilk tespit 2012-01-20). Anız sayım karşılaştırmasında bu geçiş yılı dışarıda bırakılır |
| temizlik.modis_donemi_tesis_km | 3 | km | F2-09 bağımsız kontrol: VIIRS öncesi 'sanayi' MODIS noktasının doğrulama setindeki bir tesise uzaklık sınırı (MODIS pikseli ~1-4,8 km + tesis yarıçapı) |
| harmonizasyon.mcell_zaman_penceresi_saat | 4 | saat | VIIRS noktası, bu süre içindeki bir MODIS (Terra veya Aqua) tespitinin ayak izine düşerse o MODIS hücresine bağlanır. Terra gündüz ~08:30 UTC, VIIRS ~10:35 UTC; Terra gece ~19:25 UTC, VIIRS ~23:00 UTC (veride ölçülen medyanlar) ->… |
| harmonizasyon.kalibrasyon_zaman_penceresi_dk | 60 | dakika | Kalibrasyon çiftleri yalnız Aqua (13:30) ile VIIRS (13:30) eşzamanlı geçişlerinden kurulur; /Δt/ bu değerden küçük olmalı (yangın bu sürede az değişir). Ölçülen Aqua-VIIRS /Δt/ dağılımı yontem belgesinde |
| harmonizasyon.izgara_derece | 0,01 | derece | MODIS izine düşmeyen (yalnız VIIRS) noktalar için yedek ve karşılaştırma ızgarası (~1 km) |
| harmonizasyon.hucre_baglanti_km | 1 | km | Aynı geçişteki VIIRS noktaları bu mesafeyle zincirlenince 'MODIS büyüklüğünde sözde hücre' olur (MODIS nadir pikseli ~1 km) |
| harmonizasyon.frp_sinif_sinirlari_mw | [10 ; 50] | MW | Yöntem (ii) için büyüklük sınıfları: küçük <10, orta 10-50, büyük >=50 MW (hücre toplam FRP / MODIS tespit FRP) |
| harmonizasyon.frp_egri_kutu_sayisi | 12 | kutu | Yöntem (iii) beklenen MODIS tespiti eğrisi log10(FRP) eşit-sayılı kutularla öğrenilir |
| harmonizasyon.min_ornek | 200 | hücre | Bir tabaka (bölge × mevsim × gündüz/gece) bundan az örnekle öğrenilirse üst tabakaya (mevsim × gündüz/gece, sonra gündüz/gece) düşülür |
| harmonizasyon.loyo_test_yillari | [2.012 ; 2.025] | yıl aralığı | Çakışma dönemi (MODIS + VIIRS) tam yılları. 2026 kısmi yıl ve NRT (type yok) olduğu için testte değil, ayrı ve 'düşük güven' etiketli |
| harmonizasyon.eski_donem_yillari | [2.000 ; 2.002] | yıl aralığı | Yalnız Terra (Aqua 2002-07-04'te başlar). Çarpanla düzeltilmez; bayrak + genişletilmiş belirsizlik |
| harmonizasyon.sicrama_pencere_yil | 3 | yıl | C10: geçiş öncesi 3 yıl ile sonrası 3 yıl ortalaması |
| harmonizasyon.gecis_ayirma_dk | 45 | dakika | Aynı uydunun ardışık tespitleri arasında bundan uzun boşluk varsa yeni yörünge geçişi başlar. Türkiye'yi tek geçiş birkaç dakikada tarar; ardışık yörüngeler ~100 dk arayla gelir |
| kumeleme.km_derece | 111 | km/derece | Enlem derecesi başına km (demo ile aynı yaklaşık değer; boylamda cos(ortalama enlem) ile çarpılır) |
| kumeleme.eslestirme_modu | ayakizi_capraz |  | sabit: yalnız mesafe <= D. ayakizi_capraz: ayrıca MODIS–VIIRS çiftinde VIIRS merkezi, MODIS piksel dikdörtgeni (scan x track) + eslesme_tamponu_km içindeyse aynı yangın (sözleşme §5). ayakizi_tum: ayrıca iki MODIS pikselinin dikdö… |
| kumeleme.bosluk_kurali | gecis |  | sabit: iki tespit arası <= H saat. gecis: arada kaçırılan GÖZLENMİŞ geçiş penceresi sayısı <= L ve süre <= Hmax (uydu geçmediyse bekle). gecis seçildi: sabit H=24, ertesi gün geçişi birkaç saat geç gelince her gün görülen yangını … |
| kumeleme.L | 3 | geçiş penceresi | gecis kuralında yangın, arada en çok L gözlenmiş geçiş penceresi boş geçtiyse sürüyor sayılır. 2002-07 sonrası günde 4 pencere var (Terra gündüz/gece, Aqua+VIIRS gündüz/gece); öğle geçişinden ertesi öğle geçişine arada 3 pencere k… |
| kumeleme.Hmax | 72 | saat | gecis kuralında uydu hiç geçmese de bu süreden uzun boşluk birleştirilmez (sonsuz bekleme olmasın) |
| kumeleme.gecis_pencere_yuzdelik | [1 ; 99] | yüzdelik | Geçiş penceresinin başı/sonu: o yıl o uydu grubunun (Terra / Aqua+VIIRS) gündüz veya gece tespit saatlerinin 1. ve 99. yüzdeliği (UTC dakika) |
| kumeleme.demo_donemi_yillari | [2.025 ; 2.026] | yıl aralığı | Duyarlılık tablosunda demo (../demo, 2025–2026 verisi) ile kıyas sütunu; olay başlangıcının TR yılı |
| takvim.min_yil_medyan | 5 | yıl | Ay medyanı ve anomali normali için en az bu kadar tam, sensör-tutarlı yıl gerekir; altında medyan 'yetersiz' etiketli. 5 yıl: çeyrekler ve MAD için en küçük anlamlı örnek (kural, ölçüm değil) |
| takvim.kesinti_pay_max | 0,5 | oran | Bir ayda gözlem kesintisi (observed=false) payı bunu aşarsa o ay hücresi boş (NaN) bırakılır; altında kesinti günleri paydan çıkarılıp ay uzunluğuna ölçeklenir (C06) |
| takvim.min_kapsam_orani | 0,5 | oran | Serbest aralık sorgusunda gözlenen gün ağırlığı / istenen gün bunun altındaysa değer boş |
| takvim.pencere_min_gun | 15 | gün | Kısa aralıkta (1 gün gibi) yıllar arası gürültü büyük; tarihsel pencere en az bu uzunluğa, aralığın merkezi çevresinde simetrik genişletilir |
| takvim.z_esik | 2 | sapma | Anomali işareti için /z/ eşiği (sağlam z: medyan/MAD, log1p ölçeğinde) |
| takvim.olcek_taban | 0,05 | log1p birimi | MAD'in sıfıra yakın olduğu hücrelerde z'nin patlamasını önleyen alt ölçek |
| takvim.ayirt_edilemez_tol | 0,1 | oran | Sıradaki iki ayın medyanı arasındaki göreli fark bundan küçükse 'ayırt edilemez' uyarısı (ek olarak bootstrap top-3 olasılığı) |
| takvim.bootstrap_B | 300 | yineleme | Yıl yeniden örnekleme sayısı (top-3 kararlılığı) |
| takvim.bootstrap_tohum | 20.260.101 |  | Tekrarlanabilirlik için sabit tohum (analiz yeniden örneklemesi; veri simülasyonu değil) |
| takvim.top_n | 3 | ay | Raporlanan en yoğun ay sayısı |
| takvim.ayrisma_oran_esigi | 1,5 | kat | MODIS oranı VIIRS oranının bu katı kadar daha düşükse düşüş 'MODIS'e özgü' (sensör/yörünge kayması/NRT şüphesi) diye işaretlenir; bu yorum doğrulanmamıştır |
| takvim.dusuk_oran_esigi | 0,5 | kat | Mevcut ay oranı bunun altındaysa 'düşük aktivite' yorumu üretilir (iki sensörde birlikte mi ayrı mı diye bakılır) |
| takvim.yorunge_kaymasi_bayragi | aqua_yorunge_kaymasi |  | harmonized.parquet bayrak sözcüğü; takvim bunu aylık hücrelere ve mevcut-ay satırına taşır |
| takvim.esdeger_sapma_esigi | 0,25 | göreli | Eşdeğer seri oranı, ölçülmüş MODIS-temiz VE VIIRS-uydu-başına oranlarının İKİSİNDEN de bu göreli farktan fazla sapıyorsa seri güvenilmez sayılır ve birincil gösterim ölçülmüş seriye düşer (F4-01: Ekim 2026'da eşdeğer ölçümlerle çe… |

## 11. Sınırlar ve yapılmayanlar

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

## 12. Kodda nerede?

| Konu | Kod | Belge |
|---|---|---|
| Veri hattı, şema, kapsam | src/pipeline/build_points.py, build_coverage.py, timeutil.py | docs/04_VERI_SOZLESMESI_TASLAK.md |
| Eşikler ve güven kodlaması (K9, K10) | src/config/esikler.json, src/config/config.py | — |
| Temizlik (sanayi, anız, NASA etiketi) | src/cleaning/kalibrasyon.py, build_status.py, olay_aniz.py, worldcover.py | docs/temizlik_yontemi.md |
| Kümeleme (olay) | src/clustering/core.py, build_events.py, bruteforce_check.py | docs/kumeleme_yontemi.md |
| Harmonizasyon | src/harmonize/eslestirme.py, guven_esleme.py, seri.py, olay.py | docs/harmonizasyon_yontemi.md |
| Takvim ve anomali | src/analytics/build_monthly.py, analiz.py, query.py | docs/takvim_yontemi.md |
| Arayüz | src/app/index.html, main.js, core.js, mapview.js, lab.js, charts.js, csv.js | referans/STIL_NOTU.md |
| Metrik ve rapor üretimi | tools/build_metrics.py, build_rapor_metrikleri.py, build_reports.py | reports/metrics.json |
| Kontroller | tools/check_all.py, audit/f1/, audit/f2/ | docs/03_KABUL_KRITERLERI.md |

## 13. Yusuf için on cümlelik özet

1. Veri 1.414.674 sıcak noktadır; bunların hepsi yangın değildir, hiçbiri silinmez.
2. Önce temizlik: deniz/volkan/sanayi/anız etiketlenir, gerçek yangın korunur.
3. Aynı yangının fotoğrafları kümelenerek 471.978 olaya iner.
4. VIIRS, MODIS'in ayak izine bağlanır; böylece 1'e 4 sorunu aynı hücrede toplanır.
5. Uydu sayısı değişince (efor) sayılar değişir; önce buna göre düzeltilir.
6. Harmonizasyon, hassas VIIRS'i eski MODIS diline çevirir; yöntem bir yılı saklayıp tahmin ederek (LOYO) sınanır.
7. Sıçrama 143,13 % (ölçüldü) iken harmonize seri gerçek MODIS düşüşünü 3,55 yüzde puan (tahmini) farkla izler; "çözdük" denmez.
8. Takvim medyan ve anomaliyle çalışır; yakın aylar "ayırt edilemez" denir.
9. Her sayının yanında etiket vardır: ölçüldü / tahmini / doğrulanmadı.
10. Doğrulanmayanlar (2026 eşdeğer, anız yer doğrulaması, ekran okuyucu, swath) açıkça yazılıdır.
