# Jüri Sunum Raporu (v2.2)

NASA Space Apps 2026 · MODIS–VIIRS Türkiye Yangın Aktivite Takvimi · Üretim tarihi: 2026-11-13

> Bu rapor, jüriye anlatım içindir. Konuşma metni önce **Basitçe** (benzetme), ardından **Teknik olarak** verilir. Her sayının yanında dürüstlük etiketi vardır: **ölçüldü / tahmini / doğrulanmadı**; varsa `metrics.json` anahtarı da yazılıdır. Kaynaklar: `belgeler_ve_denetim/yontem_ozeti.md`, `arayuz/data/metrics.json`, `belgeler_ve_denetim/gercek_dogrulama.{md,json}`, `belgeler_ve_denetim/juri_sorulari.md`, `raporlar/juri_sunum.md` (v1). "Aktivite" = tarihsel hotspot yoğunluğudur; hotspot yangın değildir, risk tahmini yapılmaz. Bu oturumda ölçülen yeni sayılar (kümeleme aşaması, yıllık değerler, orman adayı) "(bu oturum)" diye işaretlidir; henüz `metrics.json` anahtarı yoktur.

---

## 1. Tek cümle

"MODIS ve VIIRS aynı dili konuşmuyor; biz VIIRS'i MODIS'in diline çevirip 2012'deki yapay sıçramayı (ham +%143 (ölçüldü)) üç aşamada açıkladık, yangın olmayan ısı kaynaklarını silmeden etiketledik, en büyük 20 yangının 16'sını belgelenmiş gerçek yangınlarla eşleştirdik ve neyi doğrulayamadığımızı açıkça yazdık."

---

## 2. Sorun

**Basitçe:** Ormanı iki gözcü izliyor: eski olan kaba görüyor, yeni olan çok ince görüyor. Yeni gözcü işe başlayınca "yangın sayısı" fırlıyor; oysa yangınlar artmadı, gözcü keskinleşti. Üstüne, her sıcak nokta yangın değil: fabrika bacası da, tarla yakması da parlıyor.

**Teknik olarak:**

- MODIS (1 km piksel; tarama kenarında 4,8 km'ye kadar) 2000'den, VIIRS (375 m) 2012'den beri tespit üretiyor. VIIRS küçük yangınları da gördüğü için, geçiş yılında ham seri **+%143,13** (ölçüldü, `jump_raw_pct`) sıçrıyor; aynı pencerede gerçek MODIS ise **−%44,9** (ölçüldü, `jump_modis_gercek_pct`) değişti.
- Elimizde 1.414.674 ham nokta var (`veri_toplam_nokta`, ölçüldü): 259.707 MODIS, 1.154.967 VIIRS. Bir büyük yangın iki uydudan günlerce yüzlerce noktayla görünür; noktayı saymak yangın sayısını şişirir.
- Zamana ve uzaya yayılmış bir arşivde "yangın sayısı" ancak (1) sensör farkı düzeltilir, (2) aynı yangın bir kez sayılır, (3) yangın olmayan ısı ayrılırsa anlamlı olur.

---

## 3. Çözüm: 4 adım

Uygulamanın üstündeki "Ne yaptık? 4 adımda çözüm" şeridi bu dört adımdır.

| Adım | Ne yaptık | Anahtar sayılar |
|---|---|---|
| 1. Ham tespit | NASA FIRMS MODIS C6.1 + VIIRS 375 m, 2000–2026 (son gün 2026-11-12); hiçbir nokta silinmez | 1.414.674 nokta (`veri_toplam_nokta`, ölçüldü) |
| 2. Temizlik | Her noktaya tam bir etiket: temiz 827.043, anız 217.179, statik NASA 328.379, sanayi 27.012, deniz 8.848, kalıcı belirsiz 6.208, volkan 5. Kural tabanlıdır, makine öğrenmesi yok | `temizlik_status_*` (ölçüldü); sanayi kuralı birini dışarıda bırakma testinde kesinlik 0,9199 / duyarlılık 0,9712 (ölçüldü) |
| 3. Tek olay | Yakın nokta ve zamanı bir bağ grafiğinde bağla; olay = bağlı bileşen. İki uydu birlikte kümelenir | 1.044.222 noktadan 471.978 olay (`events_total`, ölçüldü); 59.201 çifte sayım önlendi (`events_double_count_avoided`, ölçüldü) |
| 4. Uydu farkı düzeltmesi | VIIRS'i MODIS ölçeğine çevir: önce uydu sayısına böl (efor), sonra bölge × mevsim × yangın gücü oranıyla çarp | Yıllık MAPE %8,33 (ölçüldü, `loyo_mape`); düzeltilmiş sıçrama −%41,35 (tahmini) |

---

## 4. Kanıt

### 4.1 Üç aşamada 2012 sıçraması

Pencere: 2009–11 ortalaması → 2012–14 ortalaması, Türkiye, status = temiz.

| Aşama | Değişim | Etiket / anahtar |
|---|---|---|
| Ham tespit | **+%143** | ölçüldü, `jump_raw_pct` |
| Kümelenmiş olay | **+%31** | ölçüldü (bu oturum) |
| Düzeltilmiş (MODIS-eşdeğer) | **−%41** | tahmini, `jump_harm_pct` |
| Gerçek MODIS (aynı pencere) | **−%45** (−44,9) | ölçüldü, `jump_modis_gercek_pct` |

| Yıl | Ham tespit | Kümelenmiş olay | Düzeltilmiş |
|---|---|---|---|
| 2011 | 12.045 | 8.786 | 12.045 (gerçek MODIS) |
| 2012 | 25.028 | 10.524 | 6.144 (tahmini) |
| 2013 | 38.140 | 13.855 | 8.993 (tahmini) |

(Yıllık değerler: ölçüldü, bu oturum; düzeltilmiş 2012–13: tahmini.)

**Mesaj:** Kümeleme sıçramanın **çoğunu** giderir (+%143 → +%31), **tamamını** değil; kalanı harmonizasyon giderir. "Kümeleme 2012 sıçramasını ortadan kaldırdı" **demiyoruz**.

**Dürüst notlar (jüri sorarsa hazır):**
- Düzeltilmiş seri ile gerçek MODIS arasındaki fark **3,55 yüzde puan** (tahmini, `jump_resid_pct`); yıllık LOYO %95 hata aralığı [−23,49; +9,51] % içinde (tahmini, `loyo_ci95`). Doğru cümle: "sıçrama kayboldu" değil, "harmonize seri gerçek MODIS düşüşünü 3,6 puan farkla izliyor".
- 2009–11 tabanı MODIS'in kendi kaydında olağandışı yüksektir; "%45 azaldı" bir eğilim iddiası değildir.
- Harmonize sıçrama, MODIS serisinin doğal değişim aralığının [−39,3; +92,61] % (tahmini, `jump_null_ci95`) dışındadır; gerçek MODIS de dışındadır.
- `metrics.json`'daki "olay / temiz" ham sıçraması +%51,72 (`olay_temiz_jump_raw_pct`, ölçüldü), iki uydunun olaylarının **ayrı ayrı kümelenip toplanmasıyla** bulunur: 2009–11 ortalaması 8.563, 2012–14'te MODIS + VIIRS ayrı olay toplamlarının ortalaması 12.993 (harmonized.json, `modis_gercek + viirs_ham`). +%31 ise **ortak kümelemedir**; aynı yangını iki uydu görse de tek olay sayılır. Aradaki fark çift sayımın önlenmesidir. Tam sıra: ham tespit +%143 → ayrı kümeleme +%52 → ortak kümeleme +%31 → düzeltme −%41 (tespit birimi; olay biriminde harmonize −%54,23, gerçek MODIS −%53,45).

### 4.2 Birini dışarıda bırakma (LOYO)

Her yıl (2012–2025, 14 yıl) modelden saklanıp kalan yıllardan öğrenilen modelle tahmin edildi.

| Ölçü | Değer | Anahtar / etiket |
|---|---|---|
| Yıllık MAPE | %8,33 | `loyo_mape` (ölçüldü) |
| Yıllık R² | 0,8716 | `loyo_r2` (ölçüldü) |
| Yıllık sapma | +%0,55 | `loyo_bias` (ölçüldü) |
| Yıllık %95 hata aralığı | [−23,49; +9,51] % | `loyo_ci95` (tahmini) |
| Aylık ülke bandı kapsaması | 0,9226 | `equiv_band_kapsama_ay_tr` (ölçüldü) |
| Efor düzeltmesiz tek oran (i0) | MAPE %42,12, R² −1,7204 | `harm_i0_*` (ölçüldü) |

**Dürüst okuma:** (ii) ile eforlu tek oran (i) ay × bölgede **ayırt edilemez** (fark −0,01 yp; %95 [−2,97; +4,26] yp, tahmini); asıl kazanç uydu sayısı (efor) düzeltmesidir: ay × bölge WAPE %52,68 → %30,64 (ölçüldü).

### 4.3 Gerçek dünya doğrulaması: 16/20 eşleşti

Toplam FRP'ye göre en büyük 20 olay, FIRMS'ten bağımsız kaynaklarla (OGM, İTÜ UHUZAM, GTÜ, haber ajansları) tarih ve konum olarak karşılaştırıldı (`gercek_dogrulama.json`): **16 eşleşiyor, 3 kısmen, 1 bulunamadı.** (Bu yalnız en büyük 20 olayın kesinliğidir: seçilmiş örnek, genel tespit oranı değil.) Hiçbir resmî bilgi modele girmedi.

İlk 10 (toplam FRP sırasıyla):

| # | Olay | İl | Başlangıç | Süre (sa) | ΣFRP (MW) | Gerçek yangın | Eşleşme |
|---|---|---|---|---|---|---|---|
| 1 | 307626 | Antalya | 2021-07-28 | 218,6 | 384.683 | Manavgat | eşleşiyor |
| 2 | 307807 | Muğla | 2021-07-31 | 171,8 | 103.176 | Milas–Bodrum | eşleşiyor |
| 3 | 307718 | Antalya | 2021-07-29 | 193,7 | 75.470 | Manavgat kompleksi doğu kolu / Gündoğmuş | kısmen |
| 4 | 428217 | Bilecik | 2025-07-20 | 88,9 | 75.410 | Geyve → Osmaneli | eşleşiyor |
| 5 | 426373 | İzmir | 2025-06-28 | 61,4 | 73.305 | Seferihisar–Menderes | eşleşiyor |
| 6 | 307866 | Muğla | 2021-08-02 | 124,0 | 68.286 | Kavaklıdere–Yatağan | kısmen |
| 7 | 427937 | Çanakkale | 2025-07-15 | 37,3 | 65.550 | Şarköy → Gelibolu | eşleşiyor |
| 8 | 426211 | Bilecik | 2025-06-27 | 38,1 | 63.733 | Taraklı → Gölpazarı | eşleşiyor |
| 9 | 426891 | İzmir | 2025-07-02 | 71,9 | 57.830 | Çeşme (Ildır) | eşleşiyor |
| 10 | 454809 | Muğla | 2026-07-29 | 24,6 | 45.041 | Seydikemer (Bayır) | eşleşiyor |

İlk 10'un tümü belgelenmiş orman yangını dalgalarıdır (8 eşleşiyor, 2 kısmen; kısmenler aynı gerçek yangın kompleksinin parçası olabilir). En büyüğü, 2021-07-28 Manavgat: 6.740 tespit, 384.683 MW, 218,6 saat; resmî başlangıç 28 Temmuz, kontrol 6 Ağustos 2021.

**Eksikler (kendimiz söylüyoruz):** 20 olay bizim ürettiğimiz en büyük olaylardır; tersi (her büyük yangını bulduk mu) test edilmedi, yani yakalama oranı ölçülmedi. Eşleşme tarih+konum örtüşmesidir, eşik yok. Kaynaklar çoğunlukla ikincildir; birçok 2025 olayı için resmî hektar bulunamadı; EFFIS 2021 raporu açılamadı (doğrulanmadı). Eşleşmeyen: Adana 2012 (§7.8).

---

## 5. Demo senaryosu (5–7 dakika)

Her adımda: **ne tıklanır**, sonra **Basitçe / Teknik olarak**. Düğme adları `BENI_OKU.md` ve `sci_tr.json`'daki adlardır; sunumdan önce ekranda birebir doğrulayın.

| Süre | Adım | Tıklama |
|---|---|---|
| 0:00–0:50 | 1. Lintu turu | "Lintu ile tur" (14 adımlık tur; yalnız ilk 2–3 adımı göster, kalanı atla) |
| 0:50–1:40 | 2. "Ne yaptık?" şeridi | Üstteki 4 adımlık şeridi soldan sağa göster |
| 1:40–2:40 | 3. Takvim: Temmuz 2021 | Takvimde 2021 satırı × Temmuz hücresine tıkla |
| 2:40–3:40 | 4. En büyük yangın | Haritada "En büyük yangına git" |
| 3:40–4:30 | 5. Orman adayı modu | Yangın türü → "orman yangını adayları" |
| 4:30–5:40 | 6. 2012 sıçrama modu | "2012 sıçrama" modu, 3 aşamayı oynat |
| 5:40–6:40 | 7. Bilim sekmesi, 5. adım | "Nasıl çalışıyor?" → 5. adım "Doğrulama" tablosu |

### Adım 1: Lintu turu (0:00–0:50)

Tıkla: uygulama ilk açılışta turu kendiliğinden başlatır; yoksa üstteki "Lintu ile tur" düğmesi.

- **Basitçe:** "Bu kuş Lintu; uygulamayı adım adım gezdiriyor. Biz de ona yetişmeden önce asıl soruyu soralım: yangın sayısına ne kadar güvenebiliriz?"
- **Teknik olarak:** "Tur 14 adımdır; bilim sekmesinde ayrıca 6 adımlık bir bilim turu var. Uygulama çevrimdışı çalışır, dış kütüphane çağırmaz. Gösterdiğimiz şey tarihsel hotspot aktivitesidir, risk tahmini değildir."

### Adım 2: "Ne yaptık?" şeridi (0:50–1:40)

Tıkla/göster: üstteki "Ne yaptık? 4 adımda çözüm" şeridi: ham tespit → temizlik → tek olay → uydu farkı düzeltmesi.

- **Basitçe:** "Ham noktalar → gürültüyü ayır → aynı yangını bir kez say → yeni gözcüyü eski gözcünün diline çevir."
- **Teknik olarak:** "1.414.674 ham noktadan 1.044.222 temiz+anız nokta, onlardan 471.978 olay çıktı (ölçüldü). Hiçbir nokta silinmedi, her noktanın etiketi var. VIIRS'i MODIS ölçeğine çevirmek için önce uydu sayısına bölüyoruz, sonra bölge × mevsim × yangın gücü oranı uyguluyoruz."

### Adım 3: Takvimde Temmuz 2021'e tıkla (1:40–2:40)

Tıkla: takvim matrisinde 2021 yılı × Temmuz hücresi; açılan kutuda o ayın sayıları ve en büyük yangınlar görünür.

- **Basitçe:** "Takvimdeki her kutu bir ay; renk, o ayın aktivitesini gösterir. Temmuz 2021'in kutusuna tıklayınca o ayın sayılarını ve en büyük yangınları görüyoruz."
- **Teknik olarak:** "Aylık değer, uydu kesintilerine göre ağırlıklı düzeltilmiş sayımdır; veri olmayan günler 'gözlem yok' diye ayrı renktedir, sıfır yazılmaz. Kutunun içinde o ayın en büyük yangınları listelenir; birincisi Manavgat. Normal ay sıralamasında Ağustos–Eylül medyanları istatistiksel olarak ayırt edilemez ('≈')."

### Adım 4: "En büyük yangına git" → Manavgat (2:40–3:40)

Tıkla: harita sekmesinde "En büyük yangına git"; yangının noktalarını ve ayrıntı panelini göster. İsterseniz "En büyük 10 yangın" listesini aç.

- **Basitçe:** "Haritada sizi 28 Temmuz 2021 Manavgat yangınına götürdü. Yüzlerce kırmızı nokta aslında tek bir yangın."
- **Teknik olarak:** "6.740 tespit, tek olay: toplam 384.683 MW, 218,6 saat. Resmî kayıtlarda başlangıç 28 Temmuz, kontrol 6 Ağustos 2021: tarih ve yer birebir örtüşüyor. İki uydu birlikte kümelendiği için çakışma döneminde 59.201 olayı iki kez saymaktan kaçındık."

### Adım 5: Orman yangını adayı modu (3:40–4:30)

Tıkla: Yangın türü: "orman yangını adayları" (diğer seçenekler: tümü / anız hariç / yalnız anız).

- **Basitçe:** "Küçük, kısa ve zayıf ateşler çoğunlukla tarla yakması. Bu modda onları eleyip büyük, uzun, güçlü ve aynı yerde başka yıl tekrarlanmamış olanları bıraktık; haritada büyük yangın bölgeleri öne çıkıyor."
- **Teknik olarak:** "Aday = (süre ≥ 12 sa veya toplam FRP ≥ 200 MW) ve ≥ 5 tespit, ve aynı 0,01° (~1 km) hücrede başka bir yılda olay yok. 2.063 olay (tahmini, bu oturum); bu modda en yoğun aylar Ağustos > Eylül > Temmuz. Arazi örtüsü verisi kullanılmadı; bu yüzden 'aday' diyoruz, 'orman yangını' demiyoruz."

### Adım 6: 2012 sıçrama modu (4:30–5:40)

Tıkla: haritada "2012 sıçrama modu"; 3 aşamayı oynat (ham → kümelenmiş → düzeltilmiş). Renk ölçeği sabittir, aşamalar karşılaştırılabilir.

- **Basitçe:** "Aynı harita, aynı sabit renk ölçeği, üç aşama: ham sayı 2012'den sonra fırlıyor; kümelenince fırlama küçülüyor; eski gözcünün diline çevrilince 2012'den sonra aslında bir azalma görünüyor."
- **Teknik olarak:** "2009–11 → 2012–14: ham +%143 (ölçüldü); kümelenmiş olay +%31 (ölçüldü, bu oturum); düzeltilmiş −%41 (tahmini); gerçek MODIS −%45 (ölçüldü). Kümeleme sıçramanın çoğunu giderir ama tamamını değil, kalanı harmonizasyon giderir. Fark 3,55 puan. 2009–11 tabanı yüksek olduğu için 'azaldı' bir eğilim iddiası değildir."

### Adım 7: Bilim sekmesi, 5. adım: doğrulama tablosu (5:40–6:40)

Tıkla: "Nasıl çalışıyor?" sekmesi → bilim turunun 5. adımı "Doğrulama: model ve gerçek dünya" → doğrulama tablosu.

- **Basitçe:** "Modele iki sınav yaptırdık: bir yılı saklayıp tahmin ettirdik; sonra bulduğumuz en büyük yangınları gerçek kayıtlarla karşılaştırdık."
- **Teknik olarak:** "LOYO: yıllık MAPE %8,33, R² 0,8716. Gerçek dünya: en büyük 20 olaydan 16'sı belgelenmiş yangınla eşleşiyor, 3'ü kısmen, 1'i (Adana 2012) bulunamadı; tabloda kaynaklar var. Resmî bilgi modele girmedi. Eksiğimiz: yakalama oranını ölçmedik."

**Kapanışı bağla:** 15 saniyelik kapanış (§9). Sorulara geçmeden önce §8'i hatırla.

**3 dakikalık kısa sürüm:** Adım 2 → 6 → 7 (şerit, sıçrama aşamaları, doğrulama); Manavgat sorulursa gösterilir.

---

## 6. Slayt iskeleti (10 slayt)

| # | Slayt | Ana mesaj | Sayılar (etiket) |
|---|---|---|---|
| 1 | Sorun: iki gözcü, bir yapay sıçrama | MODIS 2000'den, VIIRS 2012'den; ham seri +%143 sıçrıyor | `jump_raw_pct` 143,13 (ölçüldü) |
| 2 | Veri | 1.414.674 ham nokta; hiçbiri silinmez, her biri etiketlenir | `veri_toplam_nokta` (ölçüldü); MODIS 259.707, VIIRS 1.154.967 |
| 3 | Fizik | Uydu sıcaklığı görür: FRP = ε·σ·A·(T⁴ − T_b⁴); MODIS 1 km (kenarda 4,8 km), VIIRS 375 m | bir MODIS pikseline ort. 3,349 VIIRS noktası (ölçüldü); FRP50 64,88 MW (tahmini) |
| 4 | Temizlik | Kural tabanlı etiketleme; sanayi kuralı LOYO'da kesinlik 0,92 / duyarlılık 0,97 | temiz 827.043; anız 217.179; sanayi 27.012 (ölçüldü) |
| 5 | Tek olay | Bağ grafiği, bağlı bileşen; iki uydu birlikte kümelenir | 471.978 olay; 59.201 çifte sayım önlendi (ölçüldü) |
| 6 | Üç aşamalı sıçrama | +%143 → +%31 → −%41; gerçek MODIS −%45 | ölçüldü / ölçüldü (bu oturum) / tahmini / ölçüldü |
| 7 | Harmonizasyon ve LOYO | Efor düzeltmesi asıl kazanç; yıllık MAPE %8,33, R² 0,8716 | `loyo_mape`, `loyo_r2` (ölçüldü); `loyo_ci95` (tahmini) |
| 8 | Gerçek dünya doğrulaması | En büyük 20: 16 eşleşti, 3 kısmen, 1 bulunamadı; #1 Manavgat | `gercek_dogrulama.json` |
| 9 | Uygulama: demo | Takvim, harita, orman adayı, 2012 sıçrama modu, bilim sekmesi | 2.063 aday olay (tahmini, bu oturum) |
| 10 | Dürüst sınırlar ve kapanış | Risk tahmini yok; 2026 düşük güven; anız/orman tahmin; MODIS bitiyor, VIIRS sürer | `harm_2026_bant_kapsama` 0,545 (ölçüldü); Terra Şubat 2027, Aqua Eylül 2027 (NASA) |

---

## 7. Zor jüri soruları ve dürüst cevaplar

### 7.1 2009–11 tabanı olağandışı yüksek değil mi? "%45 düşüş" bir eğilim mi?

**Basitçe:** Evet, taban yüksek; bu yüzden "azalıyor" demiyoruz.
**Teknik olarak:** 2009–11 yılları MODIS'in kendi kaydında da yüksektir. İddiamız eğilim değil, ölçekleme: ham +%143 (ölçüldü) sensör eklenmesindendir; düzeltilmiş seri (−%41, tahmini) gerçek MODIS'in aynı penceredeki değişimini (−%45, ölçüldü) 3,55 yüzde puan farkla izler. Farklı bir pencere seçilseydi sayı değişirdi; denetçinin 2013–2023 tüm 3+3 yıllık pencerelerinde artık [−10,43; +4,62] yp ve 2012 değeri bunun içindedir.

### 7.2 Kümeleme tek başına sıçramayı gidermiyor mu?

**Basitçe:** Kısmen: kümeleme çoğunu söndürür, ama hepsini değil.
**Teknik olarak:** Ham +%143 → kümelenmiş olay +%31 (ölçüldü, bu oturum); kalan fark, VIIRS'in MODIS'in göremediği küçük yangınları ayrı olay olarak görmesinden ve ek uydu eforundan gelir ve ancak oran modeliyle giderilir (düzeltilmiş −%41, tahmini). "Kümeleme sıçramayı kaldırdı" demiyoruz. Ek not: yıllık sayılar 2011 → 2012'de ham 12.045 → 25.028, olay 8.786 → 10.524, düzeltilmiş 6.144'tür (ölçüldü, bu oturum; düzeltilmiş tahmini).

### 7.3 Başarı ölçütünü sonuca bakıp değiştirmediniz mi? (post-hoc)

**Basitçe:** Değiştirdik ve bunu açıkça söylüyoruz.
**Teknik olarak:** Eski ölçüt "harmonize sıçrama doğal değişim aralığında olmalı"ydı. Sonuç görüldükten sonra, gerçek MODIS de aynı aralığın ([−39,3; +92,61] %) dışında kaldığı için (kusursuz bir harmonizasyon da reddedilirdi), ölçüt "artık sıçrama (3,55 yp) yıllık LOYO %95 aralığında ([−23,49; +9,51]) olmalı" olarak koordinatör kararıyla değişti. Bu post-hoc'tur ve yeni ölçüt gevşektir. Bağımsız denetçi, 3+3 yıllık tüm pencerelerle ayrıca sınadı: artık dağılımı [−10,43; +4,62], 2012 değeri içinde. "Çözüldü" demiyoruz; "izliyor" diyoruz.

### 7.4 Anız gerçek mi? Tarla yakmasını nasıl biliyorsunuz?

**Basitçe:** Biliyoruz demiyoruz; küçük, kısa, zayıf ve hasat mevsiminde olan ateşe "anız" etiketi veriyoruz.
**Teknik olarak:** Olay düzeyi kural: ≤ 3 MODIS-hücre, ≤ 12 saat, tüm noktalarda FRP < F (MODIS 15 MW, VIIRS 4,4 MW) ve olay bölgenin öğrenilmiş anız ayında (ölçüldü: 217.179 nokta, 169.115 olay). Bağımsız arazi örtüsüne (ESA WorldCover 2021) göre anız noktalarının %79,35'i ekili alandadır (ölçüldü); öğrenilen ayların %74,2'si ulusal hasat penceresine düşer (tahmini). Sınır: LOYO kaldıracı 0,928: "ay" tek başına küçük ateşi büyükten ayırmaz, ayırıcı büyüklük/süre/FRP'dir. **Saha veya yanmış alan doğrulaması yok (doğrulanmadı).** Etiket bir kural çıktısıdır, hiçbir nokta silinmez.

### 7.5 Arazi örtüsü kullanmadan "orman yangını adayı" nasıl denir?

**Basitçe:** Adı "aday"; kesin orman diyemiyoruz.
**Teknik olarak:** Kural davranışa dayanır: (süre ≥ 12 sa veya ΣFRP ≥ 200 MW) ve ≥ 5 tespit ve aynı ~1 km hücrede başka bir yılda olay yok. Büyük, uzun, güçlü ve tekrarlamayan yanma, anız kuralının tersi profildir. 2.063 olay (tahmini, bu oturum). Dolaylı kanıt: toplam FRP'ye göre ilk 10 yangının tümü belgelenmiş yangındır (8 eşleşiyor, 2 kısmen). Sınır: büyük temiz olayların (n_mcell ≥ 10) WorldCover'ında ekili alan %50,3, ağaç %32,1'dir (ölçüldü); yani büyük olaylar yalnız ormandan oluşmaz. Aday kümesinin kendi arazi örtüsü ölçümü belgede yok. Adana 2012 örneği (§7.8) ova olaylarının sızabileceğini gösterir.

### 7.6 2026 sonuçlarına güvenilir mi? Aqua kayması?

**Basitçe:** Hayır, 2026'daki düzeltmeye düşük güvenle bakıyoruz.
**Teknik olarak:** Aqua gündüz geçiş medyanı 10,70 UTC (2015) → 11,92 (2025) → 12,65 (2026); Aqua–VIIRS eşzamanlı çift payı 0,839 → 0,487 → 0,182 (ölçüldü). 2026'da eşdeğer bant gerçek MODIS'i ayların yalnız %54,5'inde kapsıyor (LOYO dönemi %92,3). 2026 kısmi yıl ve %100 NRT'dir. "Kaymasız" kalibrasyon varyantı ölçülmedi (doğrulanmadı). Seri bayrakları: `kismi_yil_nrt;aqua_yorunge_kaymasi`.

### 7.7 Neden doğrudan MODIS kullanmıyoruz? Zaten uzun bir kayıt var.

**Basitçe:** MODIS emekli oluyor; kaydı VIIRS devralmak zorunda, biz köprüyü kuruyoruz.
**Teknik olarak:** NASA Earth Observer (29 Aralık 2025) öngörüsüne göre bilim operasyonlarının sonu Terra için Şubat 2027, Aqua için Eylül 2027'dir (`gercek_dogrulama.json`, genel bölüm); Terra ve Aqua ayrıca yörünge sapmasına bırakıldı (Terra 10:30 → 10:15 MLT; Aqua'nın geçişi ~15:50'ye kayıyor), yani MODIS zaman serisi tutarlılığı zaten bozuluyor. VIIRS (JPSS) süreklilik sağlıyor, 375 m ile daha küçük yangınları da görüyor; ama ham haliyle 2000–2011 ile karşılaştırılamaz: +%143 sıçrama bunun kanıtı. Çözüm eski kaydı kaybetmeden VIIRS'i MODIS ölçeğine çevirmek. Sınır: MODIS sonrası dönem bağımsız doğrulanamaz, aylık ülke bandı geniştir (−%59,57…+%74,99, tahmini).

### 7.8 Doğrulamada Adana 2012 neden eşleşmedi?

**Basitçe:** O olay için belgelenmiş bir orman yangını bulamadık; bunu saklamıyoruz.
**Teknik olarak:** Olay 99294: 2012-08-24, 290,3 saat, 30.268 MW, Adana (Ceyhan/İmamoğlu ovası). Adlandırılmış bir orman yangını bulunamadı. Düşük tepe FRP (236 MW), 290 saatlik süre ve ova konumu anız/tarımsal yakma veya sanayi kaynağına işaret edebilir; **doğrulanmadı**. Belge ayrıca kümelemenin "tarım zinciri" riskini açık bırakır (kapsamı ≥ 10 km ve statik nokta içermeyen 152 olaydan 34'ü; tahmini). Yani 20 olayda bir yanlış-pozitif adayı var; 20 örneklem yakalama oranını (duyarlılığı) ölçmez.

### 7.9 (Ek) Sayılar elle mi yazıldı? Gerçekten çevrimdışı mı?

**Teknik olarak:** Ekran değerleri `metrics.json` ve agg tablolarından gelir; denetçi ~100 ekran değerini karşılaştırdı, fark 0. Uygulama çevrimdışı çalışır (Leaflet ve yazı tipleri yerelde, dış CDN 0). Sınır: ekran okuyucuyla elle test yapılmadı (doğrulanmadı).

### 7.10 (Ek) Çift sayım yok mu? Bir MODIS pikseline 3–4 VIIRS noktası düşüyor.

**Teknik olarak:** İki uydu birlikte kümelenir. Çakışma döneminde ortak kümeleme 380.975 olay, ayrı kümeleme 440.176 olay verir; 59.201 çifte sayım önlenir (ölçüldü). VIIRS noktası tek bir MODIS hücresine atanır, FRP bölünmez. MODIS olaylarının yalnız %38,25'ini VIIRS de görür; bunun büyük kısmı gerçek gözlem farkıdır (yalnız-MODIS olayların ~%64'ü yalnız Terra sabah geçişinden).

---

## 8. Bilinen eleştiriler ve cevaplarımız (v2.3)

Bu bölüm, hakem gözüyle bulunan dört zayıf noktayı ve her biri için ne yaptığımızı anlatır. Ölçümler bu oturumda yapıldı; ayrıntılar `belgeler_ve_denetim/recall_olcumu.md` dosyasında ve uygulamada.

### 8.1 Şanlıurfa tarımsal yakma sızıntısı

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

### 8.2 Model seçimi: (ii) ile (i)

**Eleştiri:** Seçilen yöntem (ii), en basit eforlu oran (i) ile ay × bölgede ayırt edilemiyor: WAPE 30,63'e karşı 30,64; fark %95 [−2,97, 4,26] yp (tahmini). Yıllıkta ise (i) daha iyi: MAPE %4,83'e karşı %8,33, R² 0,9675'e karşı 0,8716 (ölçüldü).

**Cevabımız:** Bu doğru ve saklamıyoruz. Asıl kazanç efor düzeltmesinden, yani günlük VIIRS sayısını o gün bakan VIIRS uydu sayısına bölmekten geliyor:
- (i0) eforsuz: ay × bölge WAPE 52,68;
- (i) eforlu: 30,64.

(ii)'nin bölge × mevsim × FRP sınıfı katmanları ek kazanç getirmedi. (ii) "üstün" olduğu için değil, uygulama birimi (ay × bölge, olay birimi) için ana yöntem kaldı. Jüriye mesajımız şu: basit, fiziğe dayalı bir düzeltme işi görüyor. Yıllık Türkiye eğilimi için (i) de savunulabilir; (i) ile hesaplanmış sıçrama değeri belgelerde ayrıca raporlanmadığı için burada verilmiyor (belgede yok).

### 8.3 2026 Aqua yörünge kayması

**Eleştiri:**
- Aqua'nın gündüz geçiş medyanı 10,70 UTC'den (2015) 12,65 UTC'ye (2026) kaydı.
- Eşzamanlı Aqua–VIIRS çift payı %18,2'ye, 2026 bant kapsaması %54,5'e düştü (ölçüldü).
- Kaymasız dönemle (2012–2023) kalibrasyon varyantı test edilmedi.

**Cevabımız:**
- Uygulama 2026 düzeltilmiş serisini "güvenilmez" diye işaretliyor ve kartta ölçülen seriye düşüyor.
- Sunumda 2026 düzeltilmiş değerini hiçbir slaytta kullanmıyoruz.
- Kaymasız kalibrasyon testi veri hattı gerektiriyor ve yapılmadı (doğrulanmadı).
- NASA'ya göre bilim görevlerinin sonu Terra için Şubat 2027, Aqua için Eylül 2027. Bu tarihten sonra MODIS'le bağımsız doğrulama imkânı kalmayacak; çalışmanın amacı tam bu geçişe hazırlanmak.

### 8.4 Doğrulama ve paket eksikleri

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

## 9. Dürüst sınırlar

- **Risk tahmini yok.** Hotspot yangın değildir; 1.414.674 nokta → 471.978 olay.
- **Sıçrama "çözüldü" değil, "izleniyor":** 3,55 yp fark; ölçüt post-hoc değişti; 2009–11 tabanı yüksek; harmonize sıçrama doğal aralığın dışında.
- **Kümeleme sıçramayı kısmen giderir** (+%143 → +%31), kalanı harmonizasyon düzeltir.
- **(ii) ≈ (i)** ay × bölgede; asıl kazanç efor düzeltmesi; seçim ölçütünün önceden sabitlendiği doğrulanamaz.
- **2026 düşük güven:** Aqua kayması, bant kapsaması 0,545; MODIS sonrası dönem bağımsız doğrulanamaz.
- **Anız ve orman adayı** kural tabanlı tahmindir; saha/arazi örtüsü doğrulaması yok; ay tek başına ayırmaz (kaldıraç 0,928).
- **Sanayi uyuşması** MODIS döneminde zayıf (0,2278); referans seti küçük (26 tesis, 8 yangın); tesis yakalama 0,4777; STA maskesi karşılaştırılmadı.
- **Gerçek dünya doğrulaması** yalnız en büyük 20 olayı kapsar; yakalama oranı ölçülmedi; kaynaklar çoğunlukla ikincil; Adana 2012 eşleşmedi.
- **Kapsam bir çıkarımdır:** 129 uydu-gün kesinti (tahmini); NASA geçiş listesi yok.
- **Tarım zinciri** vakaları (34 olay) açık.
- **Ekran okuyucu testi yapılmadı.**
- **`metrics.json`'da bu oturumun yeni sayıları** (kümelenmiş olay aşaması, yıllık değerler, 2.063 aday) henüz anahtar olarak yer almıyor.

---

## 10. Kapanış

"Bu proje yangın sayısı üretmiyor; yangın verisine ne kadar güvenebileceğimizi ölçüyor. 1.414.674 ham noktadan 471.978 olay çıkardık. 2012'de ham seri +%143 sıçradı; kümeleme bunun çoğunu, VIIRS'i MODIS ölçeğine çeviren düzeltme kalanını giderdi ve seri gerçek MODIS düşüşünü 3,6 puan farkla izledi. Bir yılı saklayıp tahmin ederek sınadık: yıllık hata %8,33. Bulduğumuz en büyük 20 yangının 16'sı belgelenmiş gerçek yangınlarla örtüşüyor; birincisi Manavgat. 2026 için düzeltmemize güvenmediğimizi, anızı sahada doğrulayamadığımızı ve MODIS biterken bu köprünün tam bu geçiş için kurulduğunu açıkça söylüyoruz. Her sayının yanında dürüstlük etiketi var."
