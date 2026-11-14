# NASA Space Apps 2026 — MODIS–VIIRS Harmonizasyonu Jüri Değerlendirme Raporu

**Değerlendirilen Proje:** MODIS–VIIRS Türkiye Yangın Aktivite Takvimi (`NASA_Yangin_Takvimi_v2`)  
**Değerlendirme Rolü:** NASA Space Apps 2026 Jüri Paneli (MODIS & VIIRS Sensör Harmonizasyonu)  
**Değerlendirme Tarihi:** 2026-11-13  
**Genel Jüri Puanı:** **92 / 100** *(Global Finalist / Onur Derecesi Adayı)*

---

## 1. Yönetici Özeti ve Jüri Kararı

Proje, NASA'nın **Terra/Aqua MODIS** (1 km; tarama kenarında 4,8 km'ye kadar) ve **SNPP/NOAA-20/NOAA-21 VIIRS** (375 m) aktif yangın tespit arşivlerini (2000–2026-11-12; toplam **1.414.674** ham nokta) Türkiye ölçeğinde bilimsel tutarlılıkla tek bir tarihsel aktivite takviminde birleştirmektedir. Çoğu hackathon projesinin düştüğü "basit sabit oran çarpımı", "çifte sayım" ve "yanlış pozitif sızıntısı" tuzaklarından kaçınarak; fiziksel ayak izi (`scan × track`) eşleştirmesi, gözlem eforu normalizasyonu, birini-dışarıda-bırakma (LOYO) çapraz doğrulaması ve %100 çevrimdışı çalışan yüksek performanslı bir web arayüzü ortaya koymuştur.

Projeyi benzerlerinden ayıran en güçlü yönü **radikal bilimsel dürüstlüğüdür**: her metriğin yanında `ölçüldü`, `tahmini` veya `doğrulanmadı` etiketinin yer alması, post-hoc ölçüt değişikliğinin gizlenmeden raporlanması, 2026 yılındaki Aqua yörünge kaymasının model güvenini kırdığının açıkça uyarılması ve 100'ü aşkın metriğin bağımsız denetimle doğrulanmış olmasıdır. Buna karşın **Şanlıurfa ve Güneydoğu tarımsal yakmalarının ulusal FRP eşikleri nedeniyle %68,4 oranında `temiz` sınıfta kalması**, seçilen karmaşık harmonizasyon modeli `(ii)`'nin basit efor-normalize model `(i)`'den istatistiksel olarak ayırt edilememesi (hatta yıllık toplamda `(i)`'nin daha iyi olması), **2026 Aqua yörünge kaymasının** modellenmemiş olması ve **kaynak veri hattı (`src/`, `tools/`)** betiklerinin teslim paketinin dışında kalması puan kıran başlıca alanlardır.

---

## 2. Jüri Puanlama Özeti Tablosu

| Değerlendirme Kriteri | Ağırlık | Puan | Kısa Gerekçe |
| :--- | :---: | :---: | :--- |
| **1. Bilimsel Geçerlilik ve Harmonizasyon Metodolojisi** | 30 | **27 / 30** | Ayak izi (`scan × track`) eşleştirmesi, uydu eforu normalizasyonu ve 2012–2025 LOYO doğrulaması çok güçlü; ancak Yöntem `(ii)` ile `(i)` ayırt edilemez ve 2026 Aqua yörünge kayması açık modellenmemiş. |
| **2. Etki ve Gerçek Dünya Uygunluğu (Impact)** | 20 | **18 / 20** | MODIS'in 2027'de emekliye ayrılması öncesi 27 yıllık (1,41M nokta) seriyi kurtaran gerçek çözüm; fakat Şanlıurfa tarımsal yakmalarının %68,4'ünün `temiz` sınıfta kalması bölgesel haritayı domine ediyor. |
| **3. Teknik Uygulama, Mimari ve Denetim (Engineering)** | 20 | **18 / 20** | %100 çevrimdışı, ~253 ms tepki süreli ikili (`.bin`) veri mimarisi, C01–C25 otomatik testler ve bağımsız yeniden hesaplama (`fark = 0`); ancak kaynak pipeline (`src/`, `tools/`) paket dışında. |
| **4. Kullanıcı Deneyimi, Görselleştirme ve Erişilebilirlik** | 15 | **14 / 15** | 2012 Sıçrama Modu, Bilim Laboratuvarı, Lintu turu, renk körlüğü (`CIE76 dE ≥ 14,0`) ve TR/EN (279 anahtar) simetrisi mükemmel; ekran okuyucu canlı testi eksik. |
| **5. Hikâye Anlatımı, Şeffaflık ve Bilimsel Dürüstlük** | 15 | **15 / 15** | "Basitçe / Teknik olarak" çift katmanlı anlatım, her sayıda dürüstlük etiketi (`ölçüldü`/`tahmini`/`doğrulanmadı`) ve post-hoc değişikliklerin açıkça beyan edilmesi örnek düzeyde. |
| **GENEL TOPLAM** | **100** | **92 / 100** | **Global Finalist / Onur Derecesi Adayı** |

---

## 3. Güçlü Yönler (Artılar)

### 3.1. Fiziksel Ayak İzi (`scan × track`) Tabanlı Eşleştirme ve Ortak Kümeleme
- **Sabit Izgara Tuzağından Kaçınma:** Sabit 0,01° ızgara kullanılsaydı MODIS izlerinin **%46,55**'inin (`mcell_izgarada_bolunen_oran`) birden çok hücreye bölüneceği ölçülmüştür (`belgeler_ve_denetim/harmonizasyon_yontemi.md`, §1 ve §9). Bunun yerine MODIS tarama açısına göre büyüyen `scan × track` dikdörtgen ayak izi (+0,375 km VIIRS yarım piksel tamponu) kullanılmış ve birden fazla ize düşen VIIRS noktaları (81.418 nokta) öncelik sırasıyla tek bir MODIS hücresine atanarak FRP bölünmesi ve çift sayım önlenmiştir (`points_mcell.parquet`).
- **Ortak Uzamsal-Zamansal Kümeleme (Union-Find):** `temiz` (827.043) ve `aniz` (217.179) olmak üzere toplam **1.044.222** nokta, $D = 1\text{ km}$, $H_{\max} = 72\text{ saat}$, geçiş penceresi $L = 3$ ve ayak izi kesişimi kurallarıyla **471.978** tekil olaya indirgenmiştir (`belgeler_ve_denetim/kumeleme_yontemi.md`, `belgeler_ve_denetim/bulgular.md` satır 54). İki sensörün birlikte kümelenmesi sayesinde çakışma döneminde (ayrı kümelemede 440.176 vs ortak kümelemede 380.975 olay) **59.201 çifte sayım** önlenmiştir (`raporlar/juri_sunum_raporu_v2.md` satır 35, 243).

### 3.2. Gözlem Eforu Normalizasyonu ve 2012 Yapay Sıçramasının Çözümlenmesi
- **Uydu Sayısı (Efor) Düzeltmesi:** 2018'de NOAA-20 ve 2023'te NOAA-21 uydularının devreye girmesiyle ham VIIRS sayılarının sırasıyla **+%24,34** ve **+%110,19** sıçradığı gösterilmiştir (`belgeler_ve_denetim/harmonizasyon_yontemi.md` satır 247–250). Günlük VIIRS toplamlarının o gün `coverage.parquet` içinde `observed=True` olan aktif uydu sayısına bölünmesiyle ay×bölge WAPE hatası **%52,68**'den (`i0`) **%30,63–30,64** bandına (`i`/`ii`) düşürülmüştür.
- **Üç Aşamada 2012 Sıçraması Kanıtı:** 2009–2011 → 2012–2014 penceresinde ham tespitlerdeki **+%143,13** (`jump_raw_pct`, ölçüldü) yapay sıçrama; ayrı kümelemede **+%51,72**'ye, ortak kümelemede **+%31**'e, harmonizasyon sonrasında ise **−%41,35**'e (`jump_harm_pct`, tahmini) inmiştir (`raporlar/juri_sunum_raporu_v2.md` satır 46–67). Aynı pencerede gerçek MODIS değişimi **−%44,9** (`jump_modis_gercek_pct`, ölçüldü) olup harmonizasyonun eklediği artık yalnız **+3,55 yüzde puandır** (`jump_resid_pct`), bu değer yıllık LOYO %95 hata aralığı olan **[−%23,49, +%9,51]** içindedir.
- **MODIS Etkin Tespit Sınırı (`FRP50`):** Lojistik regresyonla hesaplanan etkin tespit eşiği genel **64,88 MW** (gündüz **73,98 MW**, gece **20,54 MW**) olarak fiziksel kontrast beklentisiyle uyumlu biçimde ölçülmüştür (`belgeler_ve_denetim/harmonizasyon_yontemi.md` satır 269–273).

### 3.3. Veri Silmeme İlkesi (K3) ve Kural Tabanlı Gürültü Ayrıştırma
- **Tam İzlenebilirlik:** 1.414.674 ham noktanın hiçbiri silinmemiş; her nokta `temiz` (827.043), `aniz` (217.179), `statik_nasa` (328.379), `sanayi` (27.012), `deniz` (8.848), `kalici_belirsiz` (6.208) ve `volkan` (5) sınıflarından birine deterministik kurallarla atanmıştır (`belgeler_ve_denetim/bulgular.md` satır 54).
- **Sanayi Kuralı Performansı:** LOYO doğrulamasında sanayi kuralı kesinliği **0,9199** / duyarlılığı **0,9712**, referans doğrulama setinde dengeli makro kesinlik (`ref_precision`) **0,971** ve gerçek yangın koruma oranı **0,998** (`temizlik_ref_yangin_koruma`) ölçülmüştür (`belgeler_ve_denetim/juri_sorulari.md` satır 16, `raporlar/juri_sunum_raporu_v2.md` satır 34).

### 3.4. Sıfır Uydurma Sayı (K1), Bağımsız Denetim (C23) ve Radikal Bilimsel Dürüstlük (K5)
- **Bağımsız Yeniden Hesaplama:** `belgeler_ve_denetim/bulgular.md` raporladığı üzere `openpyxl`, `polars` ve `pandas` kullanılarak ana pipeline kodundan tamamen bağımsız yapılan yeniden hesaplamada (C23) 100'ü aşkın metrikte **0 fark** elde edilmiştir (satır 7, 54, 206).
- **Kritik Hataların Denetimle Yakalanıp Kapatılması:**
  - `F1-01`: SNPP'nin 2022 Temmuz–Ağustos 16 günlük kesintisinin `observed=True` sayılması yakalanmış, `build_coverage.py` ile **129 uydu-günü** kesinti çıkarımı eklenerek kapatılmıştır (`bulgular.md` satır 10, 129, 180).
  - `F2-01`: Olay eşdeğerinin tespit eşdeğerini 98/1.252 bölge×ay hücresinde aşması tutarsızlığı tespit tavanı kırpmasıyla (0/2.350 ihlal) kapatılmıştır (`bulgular.md` satır 59, 136, 183).
  - `F4-01`: Ekim 2026'da `modis_esdeger` (%170) ve `olay_esdeger` (%185) değerlerinin iki sensörün kendi ölçümleriyle (MODIS %88, VIIRS %94) çelişmesi yakalanmış; arayüzde `esdeger_guvenilmez=True` bayrağı ve birincil ölçülen seriye düşme mekanizması eklenmiştir (`bulgular.md` satır 152–156, 219).
- **C22/C14 Ekran Tutarlılığı:** Arayüzde `Math.random` veya sabit kodlanmış sahte metrik bulunmadığı, ~100 ekran değerinin doğrudan `agg` ve `metrics.json` ile birebir (0 fark) eşleştiği denetlenmiştir (`bulgular.md` satır 150, 226, 252–253).

### 3.5. Üst Düzey Çevrimdışı Web Uygulaması ve Etkileşimli Eğitim Araçları
- **Hızlı ve Bağımsız Mimari:** `arayuz/` dizininde yer alan uygulama dış CDN bağımlılığı olmadan (`C21`) çalışmakta, `build_app_data.py` ile yıllık `.bin` parçalarına dönüştürülen **302.863 temiz olay** üzerinde en düşük FRP eşik değişimini ortalama **0,253 saniyede** (`C20`) hesaplamaktadır (`bulgular.md` satır 258–259).
- **Bilimsel Anlatım ve Kullanılabilirlik:** Üstteki "Ne yaptık? 4 adımda çözüm" şeridi, haritada sabit renk ölçekli **"📈 2012 sıçrama modu"**, **"🔬 Nasıl çalışıyor?"** bilim sekmesi, **Lintu** maskotuyla 14 adımlık ana tur + 6 adımlık bilimsel tur (`arayuz/tour.js`), **"🔥 En büyük yangına git"** (2021 Manavgat — 6.740 tespit, 384.683 MW, 218,6 saat) odaklanması ve formül enjeksiyon korumalı/BOM'lu CSV dışa aktarımı (`arayuz/csv.js`) jüri sunumu için olağanüstü etkilidir (`BENI_OKU.md`, `raporlar/juri_sunum_raporu_v2.md`).
- **Erişilebilirlik ve Çok Dillilik:** TR/EN sözlüklerinde tam simetrik **279 anahtar** (`C18`), WCAG AA üstü kontrastlar (15,69:1 / 11,56:1 / 4,59:1) ve Machado 2009 renk körlüğü simülasyonunda minimum `CIE76 dE = 14,0` değerine ulaşan şekil+renk kodlaması sağlanmıştır (`bulgular.md` satır 256–257).

---

## 4. Eksikler, Sınırlamalar ve Geliştirme Alanları (Eksiler)

### 4.1. Şanlıurfa ve Güneydoğu Tarımsal Yakma Sızıntısı
- `SANLIURFA_ANALIZI_VE_HARITA_TEST_RAPORU.md` raporundaki bulgulara göre Türkiye'deki 471.978 olayın **%14,4'ü (67.937 olay)** tek başına Şanlıurfa'dadır ve bunların **46.490'ı (%68,4) `temiz`** sınıfında kalmıştır (yalnız 21.447'si `aniz`).
- **Kök Nedenler (Ölçülmüş):**
  1. Ulusal medyan FRP eşiklerinin (`VIIRS < 4,4 MW`, `MODIS < 15,0 MW`) Harran/Viranşehir/Ceylanpınar tarlaları için düşük kalması (`temiz` olayların **%83,4**'ü — 38.775 olay — ≤ 3 tespit ve ≤ 12 saat olmasına rağmen en az bir piksel bu sınırı aştığı için `temiz` kalıyor; Urfa `temiz` medyanları VIIRS'te 5,82 MW, MODIS'te 22,5 MW).
  2. Aynı 1 km hücrede çoklu yılda tekrarlanan **27.780 noktanın** (`yillik_tekrar` bayrağı; `temiz` içinde 22.773 nokta / 9.678 olay, **%20,8**) tasarım kararı gereği statüyü değiştirmemesi.
  3. Geniş parsellerde `n_det > 3` sınırının aşılması (**%17,9**, 8.305 olay).
  4. Aralık, Ağustos ve Ocak–Şubat yakmalarının bölgesel anız takvimi dışında kalması (kaldı ki `temizlik_aniz_loyo_kaldirac = 0,928` ile ay bilgisinin tek başına zayıf kaldığı belgelenmiştir).
- **Jüri Önerisi:** FRP eşikleri il veya ekolojik bölge bazlı uyarlanmalı ve çoklu yıl aynı 1 km hücrede tekrarlanan düşük-orta FRP'li ova olayları için ayrı bir `olasi_tarimsal_tekrar` alt etiketi getirilmelidir.

### 4.2. Harmonizasyon Modeli Seçimi: Yöntem `(ii)` vs Basit Yöntem `(i)`
- `belgeler_ve_denetim/harmonizasyon_yontemi.md` §5 ve §9 sonuçlarına göre ana yöntem olarak seçilen `(ii)` (bölge × mevsim × FRP sınıfı, ay×bölge WAPE **%30,63**) ile efor-normalize tek sabit oran `(i)` (WAPE **%30,64**) arasındaki fark yalnız **0,01 puan** olup istatistiksel olarak ayırt edilemez (%95 bootstrap CI: **[−2,97, +4,26]** puan).
- Üstelik yıllık toplam performansında basit model `(i)` çok daha üstündür:
  - Yıllık MAPE: `(i)` **%4,83** vs `(ii)` **%8,33**
  - Yıllık $R^2$: `(i)` **0,9675** vs `(ii)` **0,8716**
  - Yıllık %95 hata aralığı: `(i)` **[−%7,81, +%9,46]** vs `(ii)` **[−%23,49, +%9,51]**
  - C10 sıçrama artığı: `(i)` **1,24 yp** vs `(ii)` **3,55 yp**
- Ayrıca ölçüt seçiminin Git geçmişi olmadığı için sonuç öncesi sabitlendiği doğrulanamamış ve seçim LOYO çıktıları üzerinden yapıldığı için hafif iyimserlik (selection bias) riski doğmuştur (`bulgular.md` F2-03, `harmonizasyon_yontemi.md` §5). Ockham'ın Usturası (parsimony) gereği yıllık metriklerde `(i)` esas alınmalı veya `(ii)` alt tabakalarına hiyerarşik büzülme (shrinkage) uygulanmalıdır.

### 4.3. 2026 Rejimi ve Aqua Yörünge Kaymasının Modellenmemesi
- `belgeler_ve_denetim/harmonizasyon_yontemi.md` §9 tablosuna göre Aqua gündüz geçiş medyanı **10,70 UTC (2015)** → **11,92 UTC (2025)** → **12,65 UTC (2026)** saatine kaymış; Terra ise **8,55 UTC**'den **7,33 UTC**'ye erkenleşmiştir.
- Bunun sonucunda Aqua–VIIRS eşzamanlı ($\le 60\text{ dk}$) kalibrasyon çifti payı 2012–2023 arasındaki ~**%85** bandından 2025'te **%48,7**'ye, 2026'da ise **%18,2**'ye çökmüştür. 2026'da eşdeğer bandı gerçek MODIS'i ayların yalnızca **%54,5**'inde (`harm_2026_bant_kapsama`) yakalayabilmektedir (LOYO döneminde %92,3).
- **Eksik:** Eğitim yılları 2012–2025 tümünü kapsadığı için 2024–2025 yörünge kayması parametreleri kirletmektedir; 2012–2023 "kaymasız dönem" kalibrasyon varyantı test edilmemiş ve geçiş saat farkı ($\Delta t_{\text{overpass}}$) modele kovaryat olarak dahil edilmemiştir (`bulgular.md` F2-04, `juri_sorulari.md` satır 18).

### 4.4. Gerçek Dünya Doğrulama Kapsamı, Tarım Zincirleri ve Post-Hoc Ölçüt
- **Yakalama Oranı (Recall) Ölçülmedi:** `gercek_dogrulama.json` en büyük 20 olayda (16 eşleşen, 3 kısmi, 1 eşleşmeyen — Adana 2012 #99294) yalnızca isabet (precision) yönünü kontrol etmektedir; OGM/EFFIS/MCD64A1 yanmış alan poligonlarına karşı "gerçek büyük yangınların yüzde kaçını yakaladık" sorusu yanıtlanmamıştır (`raporlar/juri_sunum_raporu_v2.md` satır 105).
- **Tarım Zinciri Sorunu:** Komşu parsellerin $1\text{ km}$ ve $72\text{ sa}$ kuralıyla zincirlenerek dev olay gibi görünmesine yol açan **34 olaylık** tarım zinciri riski (kapsam $\ge 10\text{ km}$, statik nokta yok; ör. Adana 2012 Olay #99294 — 290,3 saat, 30.268 MW) kümeleme katmanında henüz çözülmemiştir (`juri_sunum_raporu_v2.md` satır 235, `bulgular.md` F2-08).
- **Post-Hoc Ölçüt Değişikliği ve İl Düzeyi Doğrulama Eksikliği:** C10 başarım ölçütü ilk sonuçlar görüldükten sonra gevşetilmiştir (`bulgular.md` F2-07). Öte yandan arayüzdeki ana harita ve takvim birimi olan **il × ay** düzeyinde eşdeğer serinin ayrı bir LOYO hata ölçümü bulunmamaktadır; LOYO doğrulaması yalnız ay × bölge ve ay × ülke düzeyindedir (`juri_sorulari.md` satır 28).
- **MODIS Dönemi Sanayi Uyuşması ve Güven Eşlemesi:** 2000–2011 arası MODIS sanayi kesinliği NASA `type=2` referansının seyrekliği nedeniyle **0,2278**'dir (ancak tesis bazında ≤ 3 km eşleşmesi %66,6'dır). Öğrenilmiş güven eşlemesi (düşük 0–35 / nominal 36–82 / yüksek 83–100) ise FIRMS eşiklerini (kappa 0,1765 vs 0,1918) geçememiştir (`harmonizasyon_yontemi.md` satır 255–257).

### 4.5. Paket Yeniden Üretilebilirliği ve Açık Kalan Düşük Seviyeli Bulgular
- **Eksik Kaynak Pipeline:** `BENI_OKU.md` (satır 16, 40) belirttiği üzere `build_app_data.py` için gereken `data/processed` dosyaları, `src/` pipeline kodları ve `tools/check_all.py` doğrulama paketi bu teslim klasöründe yer almamakta, harici bir çalışma dizinine referans vermektedir.
- **Açık Kalan 4 Düşük Seviyeli Denetim Bulgusu (`belgeler_ve_denetim/bulgular.md` satır 244):**
  - `F2-10`: `src/harmonize/seri.py:207` içinde sabit `between(2003, 2025)` değeri (`K9`/`K11` ihlali).
  - `F2-11`: `harmonizasyon_yontemi.md` §9 tablosunda İngilizce nokta ondalık biçimi (`30.63`, `[-23.49, 9.51]`).
  - `F2-12`: `tools/check_all.py` içinde C23 `fark_aciklamasi` ve C09 `loyo_folds` alanlarının otomatik denetlenmemesi.
  - `F5-03`: Tahmini girdiden türetilen `jump_harm_dogal_aralikta` gibi boolean bayrakların `ölçüldü` etiketi taşıması.
- **Metrik Senkronizasyonu ve Erişilebilirlik:** `raporlar/juri_sunum_raporu_v2.md` (satır 5, 260) içindeki "(bu oturum)" metrikleri (kümelenmiş olay +%31 aşaması, 2.063 orman adayı) henüz `metrics.json` içine işlenmemiştir; ayrıca canlı ekran okuyucu (NVDA/JAWS) testi gerçekleştirilmemiştir (`juri_sorulari.md` satır 26).

---

## 5. Jüri Tavsiyeleri ve Sonraki Adımlar (Eylem Planı)

1. **MODIS Emekliliği İçin Kaymasız Kalibrasyon (Öncelik 1):** 2027'de Terra/Aqua kapandıktan sonra seri tamamen VIIRS'e dayanacağı için harmonizasyon modelinin **2012–2023** "yörünge kaymasız" döneminde sabitlenmiş bir varyantı çıkarılmalı ve yıllık raporlamada daha düşük hata veren `(i)` modeliyle hibrit/büzülme (shrinkage) kıyaslaması yapılmalıdır.
2. **Bölgesel/İl Bazlı Anız Eşiği ve Tarım Zinciri Freni (Öncelik 2):** Şanlıurfa gibi büyük parsel tarım illerinde ulusal FRP eşiği yerine bölgesel eşik ve `yillik_tekrar` statü ayrımı uygulanmalı; `t_start → t_end` süresince komşu parselleri birleştiren tarım zincirleri için yönlü yayılma/FRP yoğunluğu freni eklenmelidir.
3. **Yanmış Alan (Burned Area) Çapraz Doğrulaması (Öncelik 3):** MODIS MCD64A1 veya EFFIS/OGM poligonlarıyla eşleştirme yapılarak sistemin gerçek yangın yakalama oranı (recall) ölçülmelidir.
4. **Tam Paket Teslimi ve Küçük Denetim Kapanışları (Öncelik 4):** `src/`, `tools/check_all.py` ve `F2-10..F5-03` düşük seviyeli bulguları ile "(bu oturum)" metrikleri `metrics.json` içine dahil edilerek tek komutla yeniden üretilebilir (reproducible) hale getirilmelidir.

---

## 6. Kapanış Jüri Notu

> *"MODIS–VIIRS Türkiye Yangın Aktivite Takvimi, bir hackathon prototipinin çok ötesinde; sensör fiziğini anlayan, gözlem eforunu ayrıştıran, kendi hatalarını bağımsız bir denetçi gözüyle yakalayıp belgeleyen ve kullanıcıya sıfır internet bağımlılığıyla pürüzsüz bir bilimsel laboratuvar sunan olgun bir mühendislik eseridir. Eksiklerini gizlemek yerine en ön sayfaya yazan bu şeffaflık kültürü, projeyi NASA Space Apps 2026 jürisi nezdinde **92/100** puanla en üst sıraya taşımaktadır."*
