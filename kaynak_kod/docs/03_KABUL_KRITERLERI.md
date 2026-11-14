# Kabul Kriterleri ve Uyuşmazlık Kontrolleri

`tools/check_all.py` bu dosyadaki her kontrol için bir işlev içerir, tablo basar, bir kontrol kalırsa çıkış kodu 1 verir ve sonucu `audit/check_results.json` dosyasına yazar. Bir kontrol uygulanamıyorsa **ATLANDI** olarak, gerekçesiyle listelenir. Sessizce geçilemez.

**Uyuşmazlık nedir?** Aynı büyüklüğün farklı yerlerde (kod, ekran, rapor, iki modül) farklı çıkması. Bu projede üç tür yaşandı: rapordaki eski sayılar, ekranda sabit yazılmış metrik, iki dosyada farklı güven kodlaması. Aşağıdaki kontroller bunları yakalamak içindir.

## Hesap doğruluğu

| Kod | Kontrol | Geçme ölçütü |
|---|---|---|
| C01 | Huni korunumu | Her adımda giren = kalan + silinen; her sensör ve bölge için |
| C02 | Toplam tutarlılığı | Tümü temiz tespit = MODIS + VIIRS temiz tespit |
| C03 | Kümeleme doğruluğu | Hızlı kümeleme, kaba kuvvet bölümlemesiyle birebir aynı (örneklemde fark 0) |
| C04 | Çifte sayım yok | Çakışma döneminde aynı yangın iki olay olmaz; ortak olay ≤ ayrı olay |
| C05 | Üçlü sınıf toplamı | ortak + yalnız MODIS + yalnız VIIRS = toplam olay |
| C06 | Veri kapsamı | Sensörün kapsamı dışındaki gün sayıma ve anomaliye girmez |
| C07 | Zaman | TR gün sınırı (20:59 UTC / 21:00 UTC farklı gün); depolama UTC; hiçbir yıl kırpılmaz |
| C08 | Şema ve kodlama tutarlılığı | Güven eşlemesi (MODIS 0–100, VIIRS l/n/h) tek tanım; tüm modüller aynı değerleri kullanır |

## Harmonizasyonun doğruluğu

| Kod | Kontrol | Geçme ölçütü |
|---|---|---|
| C09 | Kalibrasyon dışı doğrulama | Oran/eşik, yıl dışarıda bırakma (leave-one-year-out) ile sınanır. MAPE, R², ortalama sapma ve %95 aralık raporlanır. Kalibrasyon yıllarında yapılan test **geçerli sayılmaz** |
| C10 | Sıçrama metriği | Sensör geçişindeki sıçrama (geçiş öncesi 3 yıl ile sonrası 3 yıl ortalamasının farkı, %) ham ve harmonize seri için hesaplanır. **Geçme:** artık sıçrama (harmonize − aynı penceredeki gerçek MODIS değişimi) LOYO yıllık %95 hata aralığında. Bilgi için: harmonize sıçramanın geçiş dışı yıllık değişim dağılımındaki yeri (2026-11-13 inceltildi, bkz. degisim_gunlugu) |
| C11 | Eşdeğer seri doğruluğu | Çakışma döneminde VIIRS'ten türetilen MODIS-eşdeğer seri, gerçek MODIS ile karşılaştırılır; sapma ve belirsizlik bandı raporlanır |
| C12 | Duyarlılık | D, H, N, M, F için sonuçların ne kadar oynadığı tabloya yazılır (en az üç değer) |
| C13 | Referans karşılaştırması | Etiketli doğrulama seti (bilinen sanayi yerleri, bilinen yangınlar) ile kesinlik ve duyarlılık (precision/recall). Referans yoksa **ATLANDI** + "doğrulanmadı" |

## Arayüz ve veri bütünlüğü

| Kod | Kontrol | Geçme ölçütü |
|---|---|---|
| C14 | Ekran = hesap | Arayüzde görünen her sayı `reports/metrics.json` veya veri tablosundan gelen değerle birebir eşit (tolerans 0) |
| C15 | Yasak kalıp taraması | Arayüz kodunda `Math.random`, tohumlu rastgele, sabit yazılmış metrik (R², yüzde, oran) yok |
| C16 | Simülasyon izolasyonu | Simüle veri yalnızca `tests/` altında; ekranda "SİMÜLASYON" rozeti; jüri modunda kapalı |
| C17 | CSV | Sütunlar, UTF-8 BOM, formül enjeksiyonu önlemi, UTC ve TR zaman sütunları |
| C18 | TR/EN | İki sözlüğün anahtar kümesi aynı |
| C19 | Erişilebilirlik | Klavyeyle gezinme, `aria` etiketleri, renk körlüğü simülasyonuyla ayırt edilebilirlik, kontrast oranı ölçülür ve raporlanır |
| C20 | Performans | 20 yıllık veriyle etkileşim süresi ölçülür ve raporlanır (hedef: eşik değişince sonuç birkaç saniye içinde) |
| C21 | Çevrimdışı açılış | Harita/grafik kütüphaneleri yerelde; internet yokken uygulama açılır (harita zemini hariç, uyarıyla) |

## Belgelerle tutarlılık

| Kod | Kontrol | Geçme ölçütü |
|---|---|---|
| C22 | Belge sayıları | `reports/` altındaki her sayı `metrics.json`'dan gelir; çözülmemiş `{{yer tutucu}}` varsa üretim başarısız |
| C23 | Bağımsız yeniden hesap | `denetci`, ana sayıları farklı bir yöntemle (ör. pandas veya SQL) yeniden üretir; fark 0 ya da açıklanmış |
| C24 | Dürüstlük etiketi | Raporlardaki her iddia ölçüldü / tahmini / doğrulanmadı etiketi taşır |
| C25 | Gereksinim eşlemesi | `docs/01_ISTEKLER.md` içindeki her kimlik (N-xx, U-xx) için "yapıldı / kısmen / yapılmadı" durumu ve kanıt yolu var |

## Kontrol ritmi

- Her ajan görevi bitirince ilgili kontrolleri çalıştırır ve çıktıyı yapıştırır.
- Koordinatör her faz sonunda `python tools/check_all.py` çalıştırır.
- `denetci` her fazın sonunda bağımsız olarak çalışır (bkz. `.claude/agents/denetci.md`); bulguları `audit/bulgular.md` dosyasına yazar. Seviyeler: **yüksek** (yanlış sayı, uyuşmazlık, sahte veri), **orta**, **düşük**. Yüksek bulgu kapanmadan faz bitmez.
- Veri yenilenirse (yeni indirme, yeni yıl) anlık görüntü sayıları **bilinçli** güncellenir ve nedeni `audit/degisim_gunlugu.md`'ye yazılır.
