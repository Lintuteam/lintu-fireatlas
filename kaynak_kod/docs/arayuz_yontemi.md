# Arayüz ve Harita Yöntemi (Fütüristik NASA Veri Arayüzü)

Bu belge, NASA Space Apps 2026 MODIS–VIIRS Harmonize Yangın Aktivite Takvimi projesinin kullanıcı arayüzü mimarisini, görsel tasarım dilini, bilimsel kararlarını ve erişilebilirlik yapısını açıklar. Proje sahibi Yusuf'un sunumlarda rahatça anlatabilmesi için her bölüm önce **Basitçe** (benzetmeyle), ardından **Teknik olarak** (uzman ayrıntısıyla) sunulmuştur.

---

## 1. Giriş ve Temel Amaç

### Basitçe
Eski analog televizyon yayını (2000'deki MODIS) ile günümüzün 4K dijital yayını (2012'deki VIIRS) aynı sahneyi çektiğinde, 4K kameranın daha çok ayrıntı görmesi "dünyada aniden 4 kat fazla yangın çıktı" anlamına gelmez. Eğer iki kameranın verisini körü körüne alt alta koyarsanız 2012 yılında devasa yapay bir sıçrama görürsünüz. Bu arayüzün temel amacı, uyduların çözünürlük farkını gidererek kullanıcının 20 yıllık yangın aktivitesini tek ve tutarlı bir zaman çizgisinde görmesini sağlamaktır.

> [!IMPORTANT]
> **Yangın Riski Değil, Yangın Aktivitesi (K14 Kuralı):**
> Bu arayüz geleceğe yönelik bir "yangın riski" veya "tahmin" haritası değildir. Uyduların termal kızılötesi kanallarıyla gerçekten tespit ettiği geçmiş **yangın aktivitesidir**.

### Teknik olarak
Sistem FIRMS MODIS (Terra/Aqua, 1 km piksel) ve VIIRS (SNPP/NOAA-20/NOAA-21, 375 m piksel) hotspot arşivini birleştirir. Ham birleşimde 2012 sonrasında %143,13'e varan yapay bir geçiş sıçraması (`jump_raw_pct`) görülür. Harmonizasyon boru hattı, uzamsal-zamansal kümeleme (`D=1 km`, geçiş kuralı `L=3` pencere ve `Hmax=72 saat`), MODIS ayak izi hücresinde FRP toplamı ve lojistik tespit eşiği kalibrasyonu ile bu sıçramayı gerçek MODIS referansının değişimine yakınsar (`jump_harm_pct = -41,35%`, gerçek MODIS `-44,9%`, artık sıçrama `jump_resid_pct = +3,55` yüzde puan; LOYO %95 hata bandı `[-23,49%, +9,51%]`). Arayüz (`src/app/`), bu harmonize zaman serisini ve altında yatan ham veriyi etkileşimli bir web uygulamasında sunar.

---

## 2. Görsel Dil: Fütüristik NASA Arayüzü

### Basitçe
Arayüz, bir uzay üssünün veya NASA kontrol merkezinin telemetri ekranı gibi hissettirir. Zifiri karanlık uzay zemini (`#070b10`), gölgesiz keskin veri panelleri (`#0d141b`), dikkat çekmesi gereken tek kritik göstergeler için neon turkuaz ışıklar (`#5eead4`) ve karmaşık sayılar yerine bir bakışta durumu anlatan HUD göstergeleri kullanılmıştır.

### Teknik olarak
Tasarım dili `referans/STIL_NOTU.md` dosyasındaki Figma Make spesifikasyonuna dayanır:
- **Renk Paleti:**
  - Ana Zemin: `#070b10` (Koyu lacivert-siyah, derin uzay tonu)
  - Kart Zeminleri: `#0d141b` (1 ton açık koyu mavi, gölgesiz düz yüzey)
  - Kenarlıklar: `#1b2630` (1 px ince yapısal ayrım)
  - Metin / Önplan: `#e6edf3` (Yüksek kontrastlı beyazımsı gri, WCAG 15.69:1)
  - Soluk Metin: `#a3afbc` (Monospace etiketler ve ikincil bilgiler, WCAG 8.85:1)
  - Birincil Vurgu: `#5eead4` (Camgöbeği/Turkuaz, butonlar, aktif sekme, canlı telemetri)
  - İkincil Vurgu: `#a99cff` / `#8b7cf6` (Mor, kümelenmiş olay çizgisi ve ikincil özet kart vurgu şeridi)
  - Uyarı Tonu: `#f5b455` (Kehribar/Altın, NRT dönemi, kısmi ay ve geçiş bayrakları)
- **Düzen Mimarisi (`.top`, `.cards`, `.layout`, `.tabs`):**
  - Üst başlıkta (`.top`) uygulama adı, Bilimsel Seri Hızlı Anahtarı (`#sciModeBtn`), Hızlı CSV İndirme düğmesi (`#quickExportBtn`), Veri ve Yöntem paneli (`#infoBtn`), Sade Mod (`#sadeBtn`) ve TR/EN dil değiştirici (`#langBtn`) yer alır.
  - 4 adet telemetri özet kartı (`.cards` / `.kart` — üst vurgu şeritli ve `tabular-nums` tipografisiyle):
    1. `Toplam yangın olayı` (`#cTotal`)
    2. `En yoğun aylar` (`#cTop`)
    3. `Son tam ay, normale göre` (`#cCur`)
    4. `Uydu geçişindeki sıçrama` (`#cJump`)
  - Sol yapışkan süzgeç paneli (`.filters` + `<details id="adv">` gelişmiş süzgeçler) ve 4 erişilebilir sekme (`Takvim`, `Harita`, `Uydular nasıl birleştirildi`, `İndir`).

---

## 3. Bilimsel Seri Seçimi ve Kararı (Yusuf'un Soru 3 Cevabı)

### Basitçe
Biri size "Ekranda hangi seriyi gösteriyorsunuz? MODIS mi, VIIRS mi?" diye sorduğunda cevabınız şudur:
> *"Bilimsel standartlara uygun olarak iki farklı ihtiyacı tek ekranda buluşturduk: 20 yıllık tarihsel karşılaştırmalar, trendler ve anomali tespiti için **MODIS-Eşdeğer Seri** varsayılandır. Çünkü 2000–2011 arasında gökyüzünde VIIRS yoktu; geçmişle bugünü ancak eşdeğer tabanda kıyaslayabiliriz. Fakat son yılların ayrıntılı uzamsal detayını ve küçük yangınları incelemek isteyen uzmanlar için **Ham VIIRS ve Üçlü Sınıf Katmanları** haritada ve ayarlarda anında açılabilir."*

### Teknik olarak
Arayüz üst başlığındaki **Bilimsel Seri Hızlı Anahtarı** (`#sciModeBtn`) ve filtre panelindeki `#seriesSel` bu hiyerarşiyi yönetir:
1. **MODIS-Eşdeğer Seri (`olay_esdeger` / `modis_esdeger` - Varsayılan):**
   - VIIRS tespitleri MODIS 1 km hücrelerine atanır, toplam FRP eşik lojistiğinden geçirilir ve MODIS ölçeğine kalibre edilmiş eşdeğer olay serisi üretilir.
   - Sıçrama etkisi giderilmiştir; 2000–2026 arası kesintisiz homojen trend sağlar.
   - Hücre bazında `[alt, üst]` belirsizlik bantları taşır (`etiket: tahmini`).
2. **Ölçülen Ham Olay Serisi (`olay` / `modis_temiz`):**
   - Uyduların gördüğü ham tespitlerin birleşimidir (`etiket: ölçüldü`).
   - 2012'de sensör geçiş sıçraması içerir.
3. **Harita Üçlü Sınıf Katmanları (`match_class`):**
   - Haritada her olay 4 renkle ve farklı geometrik şekillerle kodlanır:
     - **Ortak (Sarı daire ●):** Her iki sensör de aynı anda gördü (en yüksek güven).
     - **Yalnız MODIS (Mavi kare ■):** Yalnızca MODIS gördü.
     - **Yalnız VIIRS (Turuncu üçgen ▲):** VIIRS'in 375m çözünürlüğü sayesinde yakalanan küçük yangınlar.
     - **Tek Sensör Dönemi (Mor baklava ◆):** 2012 öncesi (Aqua/Terra yalnızlığı).
   - Kullanıcı bu katmanları yan paneldeki kutucuklardan bağımsız olarak açıp kapatabilir.

---

## 4. Hücre Müfettişi (Parent–Child Olay İnceleme)

### Basitçe
Müfettiş bir "büyüteç" gibidir. Haritadaki tek bir yangın olayına tıkladığınızda, o olayın bir dosya klasörü gibi içine girer: "Bu olay aslında sabah 10:15'te Terra'nın gördüğü 1 nokta ile öğlen 13:30'da SNPP'nin gördüğü 3 noktanın birleşimidir" diye delilleriyle listeler.

### Teknik olarak
- Tıklanan olayın `event_id`, sınıfı, durumu (`temiz`, `anız`, `sanayi`, vb.), toplam ve pik FRP enerjisi, başlangıç zamanı (UTC ve TR saati) ve bağlı olduğu il gösterilir.
- Altındaki tüm ham bileşenler listelenir: Uydu adı, UTC/TR saati, FRP, piksel alanı (`scan × track`) ve güven skoru.
- Olay tablosu ile ham nokta tablosu anlık karşılaştırılır: Sayımlar tam eşleşiyorsa yeşil "olay tablosuyla birebir aynı (kayıp yok)" rozeti gösterilir; böylece K3 (silme yok) kuralı doğrulanır.
- MODIS tespitinin yaklaşık eliptik ayak izi (`scan × track`) harita üzerinde vektörel dikdörtgen olarak çizilir.

---

## 5. Birleştirme Laboratuvarı (Merge Lab)

### Basitçe
Laboratuvar, uyduların nasıl anlaştığını adım adım gösteren 5 karelik bir çizgi roman gibidir:
1. **Adım 1:** Uzaydan düşen ham noktalar (kırmızı ve mavi noktalar).
2. **Adım 2:** MODIS uydusunun dev ayak izi karesi çizilir; içine düşen VIIRS noktaları yakalanır, dışarıdakiler elenir.
3. **Adım 3:** Karenin içindeki tüm küçük yangınların enerjisi (FRP) toplanır.
4. **Adım 4:** Karar anı: Bu toplam enerji MODIS'in tahmini %50 tespit eşiğini (`modis_frp50_genel_mw = 64,88 MW`) aşıyor mu? Aşıyorsa MODIS de görür, aşmıyorsa yalnız VIIRS görür.
5. **Adım 5:** Tek bir resmi yangın olayına dönüştürülür.

### Teknik olarak
Laboratuvar (`src/app/lab.js`), ön-işlenmiş ikili yıl parçaları (`points_<yıl>.bin`) ile `D.lab` (`src/app/data/lab_examples.json` içindeki örnek hücre vakaları) verisini yükler:
- Vektörel SVG üzerinde piksel eksenleri yerel koordinatta (`km`) çizilir.
- `points_mcell.parquet` tablosundan aktarılan gerçek piksel geometrisi (`scan × track` yaklaşık eksen-hizalı dikdörtgen) kullanılır.
- Eşik kararı `reports/metrics.json` içindeki `modis_frp50_genel_mw` değerine göre verilir.
- Sayfada hiçbir sabit sayı yoktur; tüm metinler ve koordinatlar gerçek veriden dinamik hesaplanır.

---

## 6. Erişilebilirlik (A11y) ve WCAG Standartları

### Basitçe
Arayüzü ister fareyle, ister sadece klavyeyle, ister ekran okuyucuyla, isterseniz renk körlüğü gözlüğüyle kullanın; hiçbir bilgi kaybolmaz. Renk körü olan biri sarı ve kırmızıyı ayırt edemese bile daire ile üçgen şekil farkından yangının türünü hemen anlar.

### Teknik olarak
- **Klavye Erişilebilirliği (WCAG 2.1.1 & 2.1.2):**
  - Tab tuşu ile tüm kontrollere sıra ile erişilir (`.skip` atlama bağlantısı mevcuttur).
  - Sekmeler ve 20 yıllık yıl×ay matrisi **roving tabindex** yapısındadır: Ok tuşlarıyla (Yukarı/Aşağı/Sağ/Sol) hücreler arasında hızlıca dolaşılabilir.
  - Odak göstergesi (`:focus-visible`) neon turkuaz 2 px halka ile belirgindir.
- **Renk Körlüğü Güvencesi (WCAG 1.4.1 & C19):**
  - Tüm harita sınıfları hem renkle hem de şekille (● daire, ■ kare, ▲ üçgen, ◆ baklava) kodlanmıştır.
  - Harita ve matris paletleri (Viridis, Cividis, YlOrRd) bilimsel algısal-tekdüze rampalardır; Machado 2009 renk körlüğü simülasyonunda minimum CIE76 renk farkı `dE ≥ 14.0` olarak ölçülmüştür.
  - Canlı SVG renk körlüğü filtreleri (`#f-protan`, `#f-deutan`, `#f-tritan`) tek tıkla tüm arayüzde simüle edilebilir.
- **Kontrast Oranları (WCAG 1.4.3):**
  - Tüm arayüz metinleri WCAG AA eşiği olan `4.5:1` oranını aşar:
    - Normal metin zemin üzerinde: `15.69:1`
    - Turkuaz buton üstü koyu metin (`#04201c` on `#5eead4`): `11.56:1`
    - Soluk etiket metni zemin üzerinde: `8.85:1`
    - Matris hücre metinleri minimum: `4.59:1`

---

## 7. Çevrimdışı Çalışma (Offline-First) ve Güvenlik (C21)

### Basitçe
Uygulamayı bir USB belleğe atıp interneti olmayan bir orman gözetleme kulesine veya sığınağa gitseniz bile çift tıklayıp tarayıcıda eksiksiz çalıştırabilirsiniz. Dışarıdan hiçbir sunucuya bağlanmaya çalışmaz.

### Teknik olarak
- `index.html` içinde dış CDN bağlantısı (`http://`, `https://`, `//`) içeren hiçbir `<script>` veya `<link>` etiketi bulunmaz.
- Harita motoru Leaflet (`vendor/leaflet.js`, `vendor/leaflet.css`) yerel olarak barındırılır.
- Çevrimdışı modda harita altlığı olarak Türkiye il sınırları vektörel GeoJSON üzerinden çizilir.
- İsteğe bağlı çevrimiçi uydu haritası karoları açıldığında arayüz kullanıcıyı uyarır (`tileWarn`), ancak internet yoksa bile hiçbir veri katmanı veya analitik bundan etkilenmez.

---

## 8. Veri Bütünlüğü ve Değişmez Kurallar Özeti

| Kural | Tanım | Arayüzdeki Karşılığı |
|---|---|---|
| **C14** | Ekranda sabit sayı yasaktır | HTML içinde 3+ basamaklı sayı yoktur. HUD ve sayaçlar çalışma anında `D.man`, `D.metrics` ve `D.ev` üzerinden hesaplanır. |
| **C15** | Yasak kalıplar | `Math.random`, sahte R², tırnak içinde yüzde literal metinleri kodda yer almaz. |
| **C18** | TR/EN tam simetri | `tr.json` ve `en.json` dosyaları tüm anahtarlarıyla (279 anahtar) birebir eşleşir. |
| **C19** | Erişilebilirlik | Kontrast `≥ 4.5`, renk körlüğü `dE ≥ 14`, klavye odak halkaları eksiksizdir. |
| **C21** | Çevrimdışı çalışma | Dış CDN bağımlılığı sıfırdır. |
