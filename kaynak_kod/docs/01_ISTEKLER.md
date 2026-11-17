# Eksiksiz İstek Listesi (bağlayıcı)

Her istek bir kimlik taşır. Raporlarda ve denetimde kimlikle anılır. "Durum" sütunu mevcut demodaki (`../demo`) hâli gösterir.

## A. NASA görevinin istedikleri (kaynak: `00_NASA_GOREV_METNI.txt`)

| Kimlik | İstek | Durum |
|---|---|---|
| N-01 | MODIS ve VIIRS hotspot'larını harmonize et; sensör kökeni önemsizleşsin, örüntü ve anomali öne çıksın | Eksik (yalnız gösteriliyor, giderilmiyor) |
| N-02 | Erken 2000'lerden bugüne yangın aktivite takvimi | Eksik (veri yalnız 2025–2026) |
| N-03 | Kullanıcı bölge ve belirli tarih aralığı seçsin | Kısmen (il, çokgen, daire, enlem/boylam var; serbest başlangıç–bitiş yok) |
| N-04 | Analitik ve görselleri indirebilsin | Kısmen (CSV var, grafik dışa aktarma yok) |
| N-05 | Mevcut ayı seçilen alan için tarihsel medyanla karşılaştır | Eksik (yalnız önceki 30 gün) |
| N-06 | Çok yıllı ortalamalara göre anomali | Eksik |
| N-07 | Hangi ay ve yılların en yoğun olduğunu göster | Kısmen |
| N-08 | Erişilebilir renk rampaları | Kısmen (test yapılmadı) |
| N-09 | Aramada bulunan hotspot'ları CSV indir | Var |
| N-10 | Etkileşimli harita: alan çiz, enlem/boylam gir | Var |
| N-11 | TR/EN dil düğmesi | Var |
| N-12 | Tespit edilen yangın sayısı | Var (tespit ve olay) |

Yönergedeki (`../yönerge (1).txt`) ek beklentiler: FIRMS API'ye 10 dakikada 5.000 istek sınırına uygun veri çekme döngüsü; Geopandas/Rasterio ile uzamsal işleme; anızı orman yangınından ayırmak için zaman serisi ve makine öğrenmesi; çok yıllı ortalamalara karşı anomali grafikleri.

## B. Yusuf'un fikirleri ve istekleri

### Harmonizasyon
- **U-01** Elimdeki çok yıllı (hedef 20 yıl) MODIS ve VIIRS verisinden gerçek bir örüntü ve orantı çıkar; farklı güven değerlerini (MODIS 0–100, VIIRS l/n/h) ve yüzdelikleri **gerçek veriye göre** belirle (yüzdelik eşleştirme).
- **U-02** MODIS ve VIIRS'i aynı ızgarada düşün; **MODIS ızgarasına göre hareket et**. MODIS'te 1 yangın, VIIRS'te 4 farklı yangın görünmesi sorunu çözülsün. VIIRS'in çözünürlüğünü kaybetme.
- **U-03** **Ekstra katman:** MODIS'in ölçmediği ama VIIRS'in ölçtüğü yangınlar ("yalnız VIIRS"). Üçlü sınıf: ortak / yalnız VIIRS / yalnız MODIS.
- **U-04** VIIRS verisi durmalı, ayrıntı kaybolmamalı; yanında MODIS değerine yaklaşan bir **eşdeğer seri** üretilmeli (iki çıktı: karşılaştırma için eşdeğer seri, ayrıntı için ham VIIRS).
- **U-05** FRP'yi hücre içinde toplayıp MODIS'in tespit sınırına göre değerlendir. Güven sınıflarını ortak dile çevir.
- **U-06** Çerçeve: proje yalnız veri toplamıyor, **hataları düzeltiyor** (Faz 1a temizlik). Ancak NASA'nın istediği harmonizasyon da yapılacak (Faz 1b). İkisi birlikte teslim edilir.

### Temizlik ve sınıflandırma
- **U-07** NASA'nın zaten `type` ile etiketlediği noktalar (volkan, statik kara kaynağı, açık deniz) çıkarılmaya devam etsin.
- **U-08** Bir yangın 365 gün hatta yıllarca sürmez. Belirli bir süreden sonra aynı yerde tekrar eden sıcak nokta, **NASA sınıflandırması dışında**, sanayi tesisi, petrol/gaz yakım alanı veya sanayi bölgesi olarak işaretlensin. Çok yıllı veriyle yapılsın.
- **U-09** Anız yangınları iklime ve bölgeye göre **tekrar eden periyotlar** öğrenilerek ayrılsın. Periyodu öğrenen kuralla etiketleme döngüsel olmasın, arazi örtüsüyle bağımsız doğrulansın.

### Kümeleme
- **U-10** İki sensörün gördüğü yangın **mesafe ve zaman örtüşmesiyle** aynı olay sayılsın.
- **U-11** "14 saat yangın görmedim ama sönmedi" durumu akıllıca yönetilsin: boşluk kuralı uydunun gerçekten geçip görmediği bilgisine bağlansın.
- **U-12** Aynı yerde sabah ve akşam ayrı yangın çıkması nadir olabilir ama ihmal edilmesin; **D ve H duyarlılığı** raporlansın. Birleştirmenin anız kuralını bozup bozmadığı (olay büyüyüp anız kuralından çıkması) ölçülsün.

### Görselleştirme ve arayüz
- **U-13** **Birleştirme Laboratuvarı:** MODIS ve VIIRS'in nasıl birleştirildiği gerçek veriyle adım adım görülsün (ham noktalar → MODIS hücresine atama → FRP toplamı → karar).
- **U-14** Haritada seçenekler: **ortak tespit / yalnız VIIRS / yalnız MODIS** katmanları açılıp kapanabilsin.
- **U-15** **Sıçrama (pik) grafiği:** sensör geçişindeki sıçrama harmonizasyon öncesi ve sonrası görülsün, büyüklüğü bir metrikle yazılsın. Harmonizasyon sonrası sıçrama çok daha küçük olmalı, ama bu **bağımsız testle** kanıtlanmalı.
- **U-16** **Takvim:** yıllar ve aylar birleştirilip karşılaştırılsın; **en çok hangi ayda yangın aktivitesi var** sorusuna bölge bazında cevap veren bir ay sıralaması olsun. Yangın ayları belirgin olsun. Mevcut ay, o ayın tarihsel medyanıyla kıyaslansın.
- **U-17** Görsel taslaktan (`referans/`) güçlü yanlar alınsın: parent–child hücre müfettişi, üç harita modu, üç çizgili trend grafiği (ham → kümelenmiş → harmonize), yıl×ay matrisi ve anomali anahtarı, FRP enerji modu, erişilebilir palet seçici (Viridis, Cividis, YlOrRd), piksel büyümesi grafiği (gerçek `scan × track` verisinden), "2000–2002 yalnız Terra" bayrağı (çarpan değil uyarı), gün×hafta ızgarası ve "gözlem yok" durumu (gerçek uydu geçiş şeridiyle).

### Veri
- **U-18** FIRMS'in verdiği veri yetmeyebilir. FIRMS API ile otomatik çekme ve **ek veri kaynaklarını** değerlendir: uydu geçiş şeridi (swath outlines), Static Thermal Anomalies maskesi, arazi örtüsü (ör. ESA WorldCover), gerekirse hava verisi, yanmış alan/yangın kaydı. Her kaynağın lisansını ve erişim koşulunu yaz.

### Güvence
- **U-19** Ajanlar sık sık kontrol yapsın; **veride ve belgelerde uyuşmazlık** olup olmadığı sürekli denetlensin. Tek doğruluk kaynağı: `reports/metrics.json`.
- **U-20** Ekranda sabit yazılmış metrik, rastgele üretilmiş veri (ör. sahte bulut) ve aynı veriyle kalibre edip test etme yasaktır.

### Yeni istek: işlem sonu raporları
- **U-21** İş bittiğinde sistem **otomatik olarak üç rapor** üretsin:
  1. **Çalışma prensibi raporu:** uygulama nasıl çalışıyor, her kural ve yöntem (Yusuf'un öğrenmesi için, "Basitçe / Teknik olarak").
  2. **Doğruluk raporu:** ne kadar doğru, bağımsız yeniden hesap, kalibrasyon dışı doğrulama, sıçrama metriği, duyarlılık, referans karşılaştırma, hangi kontroller geçti, nelerin doğrulanmadığı.
  3. **Sunum raporu:** anlatım akışı, demo senaryoları, NASA gereksinim eşlemesi, yapılan/yapılmayan dürüst tablo, beklenen sorular ve cevapları.
  Raporlar şablondan üretilir, sayıları `metrics.json`'dan alır, çözülmemiş yer tutucu varsa üretim başarısız olur.

## C. Bilinen eksikler (mevcut durumdan çıkarıldı)

- Gözlem eforu (hangi uydu günde kaç kez geçti) normalizasyonu yok.
- `scan × track` piksel alanı veride var ama hiçbir hesaba girmiyor.
- NRT (hızlı veri) ile arşiv ürünü farkı: NRT'de `type` etiketi yok.
- Mevsimsel normal yok (yalnız önceki 30 gün).
- Erişilebilirlik testi (ekran okuyucu, klavye, renk körlüğü) yapılmadı.
- Doğrulama verisi (AFAD/OGM, yanmış alan, bilinen sanayi koordinatları) yok.
- 20 yıllık veri için mimari (tek JS dosyası) yetmeyebilir; ölçek testi yok.

## D. Yapılmayacaklar

- Ölçek katsayısını tüm yıl ve mevsimlere sabit uygulamak.
- Sahte bulut, sahte R², sahte oran.
- Silinen nokta (yalnız etiket).
- "Yapay zekayla temizlendi" iddiası: kural tabanlı ise "kural tabanlı" denir. Makine öğrenmesi gerçekten kullanılırsa yöntemi ve doğrulaması yazılır.

## E. Senin cevapların (Yusuf doldursun, boşsa Claude Code soracak)

1. Elimdeki 20 yıllık veri hangi sensörleri, hangi yılları, hangi sütunları içeriyor (`type`, `scan`, `track` var mı)?
   - Cevap:Kontrol et bana ne birde aralarındaki dengeyi bul biri Low ya mesela diğer uyduda yüzde kaça tekabül ediyor low ve medium aynı yerden geçen uydularla bulmaya çalış tamamen doğru olmasada yüzdelikleri sınıflandır kontrol edip örn. 0-45 low 45-70 normal 70-100 high
2. Kapsam yalnız Türkiye mi, dünya mı?
   - Cevap:Türkiye şu anlık
3. Ana seri MODIS-eşdeğer mi olsun, ham VIIRS ile yan yana mı gösterilsin?
   - Cevap: Bilimsele uygun şekilde: Yıllar arası karşılaştırma, trend ve anomali için ana seri MODIS-eşdeğer seri (belirsizlik bandıyla) varsayılan olsun; uzamsal ayrıntı ve yakınlaştırma için ham VIIRS serisi ve ortak / yalnız VIIRS / yalnız MODIS katmanları yan yana seçilebilir olsun (rapora kaydedilsin, beğenilmezse arayüzden/config'den değiştirilebilir).
4. Yarışma teslim tarihi ve sunum süresi?
   - Cevap:Bugün bitirelim
5. Doğrulama için erişebildiğin referans (AFAD, OGM, yanmış alan, bilinen yangınlar)?
   - Cevap:İstediğine eriş doğru olsunda internetten 
6. Eklemek istediğin başka istek?
   - Cevap:yok
