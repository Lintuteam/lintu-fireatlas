# Kümeleme yöntemi (olay = yangın)

> Sahibi: `kumeleme` ajanı (F2). Kod: `src/clustering/`. Eşikler: `src/config/esikler.json` → `D`, `H`, `eslesme_tamponu_km`, `kumeleme.*`.
> Bu belgedeki her sayı `python src/clustering/build_events.py` çıktısından alındı:
> `reports/metrics_parts/kumeleme.json` (metrikler, duyarlılık) ve `data/interim/kumeleme_analiz.json` (ayrıntılı tablolar).
> Kod yeniden çalışınca sayılar oradan okunmalıdır (K1). Etiketler: **ölçüldü**, **tahmini**, **doğrulanmadı** (K5).
> **Girdi (F2 ikinci adım, koordinatör kararı):** `points_status.parquet`'te `status ∈ {'temiz','aniz'}` olan 1.044.222 nokta (`core.CLUSTER_STATUSES`). Anız olay düzeyinde bir etikettir, olay yapısını değiştirmez. Temiz olmayan noktalar olay almaz (`event_id = -1`, sözleşme §2) ve zincire köprü olamaz. İlk adımda `type ∉ {1,3}` olan 1.405.848 nokta kümelenmişti (534.919 olay). Temiz girdiyle sonuç **471.978 olay**.

## 0. Ne yapıyor?

**Basitçe:** Uydular aynı yangının birçok "fotoğrafını" çeker. İki fotoğraf birbirine yakın yerde ve yakın zamanda çekildiyse aynı yangındır. A, B'ye ve B, C'ye yakınsa üçü de aynı yangındır (zincir). MODIS ve VIIRS fotoğrafları birlikte değerlendirilir; böylece aynı yangın "MODIS'te bir, VIIRS'te bir" diye iki kez sayılmaz.

**Teknik olarak:** İki nokta arasında bağ olması için *uzay koşulu* ve *zaman koşulu* birlikte sağlanmalı. Olay, bağ grafiğinin bağlı bileşenidir (union-find; demo `cluster()` ile aynı anlam). Varsayılan kural: **D = 1 km, eşleştirme `ayakizi_capraz`, boşluk kuralı `gecis` (L = 3, Hmax = 72 sa)**.

| Koşul | Kural |
|---|---|
| Uzay | `d ≤ D` (dy = Δenlem·111, dx = Δboylam·111·cos(ortalama enlem), ±180° sarmalı) **veya** MODIS–VIIRS çiftinde VIIRS merkezi MODIS piksel dikdörtgeni içinde: \|dx\| ≤ scan/2 + b, \|dy\| ≤ track/2 + b (b = 0,375 km) |
| Zaman (`gecis`) | \|Δt\| ≤ Hmax **ve** iki tespit arasında tamamen kalan *gözlenmiş* geçiş penceresi sayısı ≤ L |
| Zaman (`sabit`, karşılaştırma) | \|Δt\| ≤ H |

Olay kimliği kanoniktir: olaylar ilk tespitlerinin (t_utc, pid) sırasına göre 0, 1, 2 … numaralanır. Numara yöntemden bağımsızdır.

## 1. Sensör duyarlı eşleştirme: "%37" şüphesi (U-10)

**Basitçe:** Demoda, iki sensörün birlikte gözlediği dönemde MODIS'in gördüğü yangınların yalnızca ~%37'sini VIIRS de görüyordu. Şüphe şuydu: MODIS pikseli kenarda büyüyor (4,8 km'ye kadar), bu yüzden MODIS'in "yangın burada" dediği nokta VIIRS'inkinden 1 km'den uzağa düşüyor ve aynı yangın ikiye bölünüyor. Ölçtük. **Sonuç: şüphe kısmen doğru ama asıl neden bu değil.** Piksel ayak izine göre eşleştirme oranı yalnız birkaç puan artırıyor. Asıl neden şu: MODIS olaylarının çoğu Terra'nın sabah geçişinden geliyor ve o saatte hiçbir VIIRS uydusu geçmiyor. Ayrıca aynı saatte geçtiklerinde bile, Aqua'nın gördüğü tespitlerin ~%28'inde VIIRS 8 km içinde hiçbir şey görmüyor.

**Teknik olarak** (temiz girdi, çakışma dönemi = iki sensör ailesinin de gözlediği TR günleri; H = 24 sabit, D = 1, yalnız eşleştirme modu değişiyor; **ölçüldü**):

| Eşleştirme modu | Toplam olay | Çakışmada yalnız MODIS | MODIS olaylarının VIIRS'te de görülme oranı | Aqua içeren MODIS olaylarında oran |
|---|---|---|---|---|
| `sabit` (yalnız d ≤ 1 km, demo) | 487.863 | 63.310 | 0,355 | 0,512 |
| `ayakizi_capraz` (sözleşme §5) | 481.008 | 58.998 (−%6,8) | 0,377 | 0,545 |
| `ayakizi_tum` (+ MODIS–MODIS piksel örtüşmesi) | 446.976 | 47.399 | 0,424 | 0,590 |

Tespit düzeyinde tanı (temiz Aqua MODIS tespiti, ±60 dk içindeki VIIRS tespitleri, 2012 sonrası 69.122 Aqua tespiti; **ölçüldü**. Ayak izi dikdörtgeninin kuzey-güney yönlü olduğu varsayıldığı için ayak izi satırları **tahmini**):

| Gösterge | Değer |
|---|---|
| 8 km içinde herhangi bir VIIRS tespiti olan | 0,718 |
| En yakın VIIRS ≤ 1 km | 0,532 |
| En yakın VIIRS ≤ 2 km | 0,627 |
| VIIRS, MODIS ayak izi + tampon içinde | 0,602 |
| Kenar pikseller (scan ≥ 1,6 km, üst çeyrek): ≤ 1 km / ayak izi içinde | 0,491 / 0,657 |
| Merkez pikseller: ≤ 1 km / ayak izi içinde | 0,547 / 0,580 |

Yorum:
- Hipotezin doğru kısmı: kenar piksellerde 1 km kuralı eşleşmeyi gerçekten kaçırıyor (ayak iziyle 0,491 → 0,657).
- Ama genel tabloyu değiştiren bu değil. Çakışmadaki yalnız-MODIS olayların ~%64'ü (varsayılan kuralla 57.543 içinden 36.679) **yalnız Terra** tespitinden oluşuyor. Terra 10:30, VIIRS 13:30 yörüngesinde; kısa ömürlü bir yangını yalnız biri görebilir. Bu bir eşleştirme hatası değil, gerçek gözlem farkı.
- `ayakizi_tum` oranı daha çok artırıyor, ama bunu MODIS–MODIS çiftlerini de birleştirerek yapıyor. Bu, yalnız-MODIS döneminde (2000–2011) de olay sayısını değiştirir ve dönemler arası tutarlılığı bozar. Bu yüzden varsayılan **`ayakizi_capraz`** (sözleşme §5 ile aynı).
- **Harmonizasyon ajanı için (koordinatör üzerinden):** Eşleştirme birimi ortak: MODIS ayak izi + 0,375 km. Aqua ile eşzamanlı geçişte bile VIIRS eşleşme oranı ~%55. "Her MODIS tespitinin bir VIIRS karşılığı vardır" varsayımı yapılmamalı.

## 2. Geçişe bağlı boşluk kuralı (U-11)

**Basitçe:** "14 saattir görmedim, yangın söndü mü?" sorusunun cevabı, bu sürede uydunun gerçekten geçip geçmediğine bağlı. Sabit kural (24 saat) bunu bilmez. Yeni kural boşluğu saatle değil **kaçırılan geçişle** sayar. Uydu geçti ve yangını görmediyse bu bir "kaçırma"dır. Uydu hiç geçmediyse (kesinti) bekleriz. Arada en çok 3 boş geçiş varsa yangın sürüyor sayılır.

**Teknik olarak:**
- Türkiye'de günde 4 geçiş penceresi var: Terra gündüz (~06–09 UTC), Aqua+VIIRS gündüz (~09–12), Terra gece (~17–20), Aqua+VIIRS gece (~22–01). Aqua ile üç VIIRS uydusu aynı ~13:30 yörüngesinde olduğu için VIIRS yeni pencere eklemiyor. Böylece 2002-07'den sonra pencere sayısı **dönemden bağımsız**. Pencere sınırları her yıl ve her uydu grubu için tespit saatlerinin 1. ve 99. yüzdeliği (**tahmini**, swath verisi yok). Gruptaki en az bir uydu `coverage.parquet`'te o gün `observed=True` ise pencere "gözlenmiş" sayılır.
- İki tespit arasında bağ olması için \|Δt\| ≤ Hmax ve aralarında tamamen kalan gözlenmiş pencere sayısı ≤ L olmalı. L = 3, normal bir günde "öğle geçişinden ertesi öğle geçişine" demektir (arada Terra gece, Aqua/VIIRS gece ve Terra gündüz pencereleri kalır).

Etki (temiz girdi, D = 1, `ayakizi_capraz`; **ölçüldü**):

| Kural | Olay | Süre p90 (sa) | Süre p99 (sa) | 2000–02 / 2002–12 / 2012+ |
|---|---|---|---|---|
| sabit H = 24 | 481.008 | 1,07 | 25,4 | 5.948 / 85.858 / 389.202 |
| sabit H = 27 | 470.117 | 1,63 | 39,3 | 5.911 / 84.658 / 379.548 |
| **gecis L = 3, Hmax = 72** | **471.978** | 1,57 | 37,7 | 5.777 / 85.226 / 380.975 |
| gecis L = 2 | 499.277 | 0,85 | 23,2 | |
| gecis L = 4 | 468.214 | 1,65 | 47,4 | |
| gecis L = 3, Hmax = 48 / 120 | 472.021 / 471.978 | | | |

Bulgular:
1. **Sabit H = 24'ün gizli hatası:** Gündüz geçiş saati günden güne ~3 saate kadar kayıyor (09–12 UTC). Her gün görülen bir yangın, ertesi günün geçişi 1 saat geç gelince 25 saatlik boşluk yüzünden ikiye bölünüyor. `gecis` kuralı bu durumu düzeltiyor: H = 24'teki 16.434 olay 7.401 olayda birleşti, ters yönde yalnız 3 olay bölündü. H = 27 bu etkiyi büyük ölçüde taklit ediyor (470.117). Yani farkın ana kaynağı geçiş saatindeki oynama.
2. **Kesinti bilgisinin katkısı küçük:** Tüm günler "gözlendi" sayılınca 472.098 olay çıkıyor, `coverage.observed` ile 471.978 (212 olay 92 olayda birleşti). Bunun nedeni `coverage.parquet`'te yalnız 129 uydu-gün kesinti olması ve kardeş uyduların pencereyi çoğu zaman doldurması. Kural doğru çalışıyor ama bu veride etkisi sınırlı. Hmax'ın 48, 72 ya da 120 saat olması sonucu neredeyse değiştirmiyor.
3. L = 2 ile L = 3 arasındaki sıçrama beklenen bir durum: L = 2, her gün görülen yangını her gün bölüyor.
4. Sınırlama (**doğrulanmadı**): MODIS'in bir pencerede küçük bir yangını görememesi, yangının söndüğüne kanıt değildir. Gece pencereleri de küçük tarım yangınları için zayıf kanıttır. Kural, gözlenmiş her pencereyi aynı ağırlıkta sayıyor.

## 3. D / H / L duyarlılığı (C12, U-12)

D ve L tabloları varsayılan kuralla, H tablosu sabit H kuralıyla (`ayakizi_capraz`, D = 1) hesaplandı. Girdi temiz noktalar. Tam tablo: `reports/metrics_parts/kumeleme.json → sensitivity.D / .H / .L` (**ölçüldü**).

| D (km) | Olay | En büyük olay (tespit) | Tek tespitli olay oranı | 2025–26 olay (TR yılı, `demo_donemi_yillari`) | MODIS→VIIRS oranı |
|---|---|---|---|---|---|
| 0,5 | 541.338 | 6.736 | 0,731 | 64.429 | 0,363 |
| 1 | 471.978 | 6.740 | 0,663 | 56.263 | 0,383 |
| 2 | 383.640 | 6.754 | 0,583 | 47.803 | 0,462 |
| 3 | 341.799 | 6.755 | 0,575 | 42.731 | 0,477 |

| H (sa) | Olay | En büyük olay | Tek tespitli oranı |
|---|---|---|---|
| 6 | 525.841 | 1.385 | 0,666 |
| 12 | 512.109 | 6.658 | 0,668 |
| 24 | 481.008 | 6.740 | 0,666 |
| 48 | 451.483 | 6.742 | 0,657 |

| L | Olay | Tek tespitli oranı |
|---|---|---|
| 1 / 2 / 3 / 4 / 6 | 506.842 / 499.277 / 471.978 / 468.214 / 460.759 | 0,669 / 0,666 / 0,663 / 0,661 / 0,659 |

- D 0,5 km'den 2 km'ye çıkınca olay sayısı %29 düşüyor. Demoda (2025–26) bu oynama ~%30'du (12.065 → 8.504); 20 yılda da aynı büyüklükte. Mutlak sayılar demoyla doğrudan kıyaslanamaz, çünkü burada anız adayları hâlâ olaylara dahil.
- Olay sayısı D'ye ve H'ye güçlü biçimde bağlı. Raporlarda "olay sayısı" her zaman kuralıyla birlikte verilmeli (**ölçüldü**).

## 4. Zincirleme riski (U-12)

**Basitçe:** Zincir kuralının bir zayıflığı var: yan yana yanan bağımsız küçük yangınlar aralarında 1–3 km'lik "köprüler" kurarak tek dev olaya dönüşebilir.

**Teknik olarak** (varsayılan kural, temiz girdi; **ölçüldü**):
- Olay boyutu dağılımı: 312.936 tek tespitli, 422.275 olay ≤ 3 tespit, 471.745 olay ≤ 100 tespit; 15 olay > 1.000 tespit.
- En büyük olaylar gerçek mega yangınlar: Antalya/Manavgat 2021-07-28 (6.740 tespit, 10 gün, 53 km kapsam), Muğla 2021-07/08 olayları. Bunlar zincirleme hatası değil.
- **Sanayi zinciri (birinci adımda ölçüldü, şimdi kapandı):** Tüm noktalar kümelendiğinde 7.887 olay statik kaynakla karışıktı, İzmir/Aliağa olayları ~4 ay sürüyordu ve 7 günden uzun 2.776 olay vardı. Temiz girdiyle karışık olay sayısı 0, 7 günden uzun olay 103, süre p99 97 → 38 sa (**kesme kuralı: temiz olmayan nokta zincire köprü olamaz**, uygulandı).
- **Tarım zinciri vakaları (açık):** Statik nokta içermeyen ve kapsamı ≥ 10 km olan 152 olay var: 64.932 tespit, kümelenen tespitlerin %6,2'si. Bunların **34'ü** tarım zinciri tanımına uyuyor: olay ortalama FRP'si < F, başlangıç **TR ayı** Temmuz–Ekim (`kumeleme.tarim_zinciri`). Bu 34 olay 9.484 tespit içeriyor (%0,9); dağılım Osmaniye 14, Adana 5, Diyarbakır 5. Tanımı sağlayan örnekler (TR başlangıç günü): Osmaniye 2026-08-31 (1.934 tespit, 10 gün, 46,3 km, ortalama FRP 11,0 MW), Osmaniye 2015-08-30 (974 tespit, 36,1 km, 14,8 MW), Osmaniye 2019-08-24 (699 tespit, 27,6 km, 11,5 MW), Mardin 2019-08-03 (438 tespit, 20,2 km, 7,7 MW). Bu olaylarda tek bir bağ en çok ~2,8 km (ayak izi), ama zincir 20–46 km'ye uzanıyor. Bu durum hasat sonu yakmalarının zincirlenmesiyle tutarlı (**tahmini**, sahada doğrulanmadı). Sınırlama: tek F (MODIS ölçeği) karışık sensörlü olayın ortalamasına uygulanıyor. Öneri: kuralı değiştirmek yerine bu olaylar arayüzde "zincir şüphesi" bayrağıyla gösterilsin.

## 5. Anız etkileşimi (U-12)

**Basitçe:** Anız kuralı "küçük olay" arar (≤ 3 tespit, ≤ 12 saat, düşük FRP, anız ayı). Birleştirme olayları büyüttüğü için bazı gerçek anız yakmaları "büyük olay"a dönüşüp kuraldan çıkabilir. Ölçtük: evet, çıkıyor, ~%9.

**Teknik olarak** (temiz girdi, `type ∈ {0,-1}`; demo anız olay kuralı, F ve anız ayları `esikler.json`'dan; karşılaştırma amaçlı, **tahmini**):

| Kümeleme | Anız sayılan nokta | MODIS / VIIRS | Ayrı sensöre göre kaybedilen |
|---|---|---|---|
| Nokta düzeyi (kümeleme yok, üst sınır) | 567.871 | 79.271 / 488.600 | – |
| Sensörler ayrı kümelenir | 320.995 | 70.685 / 250.310 | (referans) |
| Ortak, sabit D = 1, H = 24 | 303.684 | 59.624 / 244.060 | 25.333 |
| Ortak, ayak izi, H = 24 | 300.643 | 58.836 / 241.807 | 28.178 |
| **Ortak, varsayılan (ayak izi + gecis)** | **290.799** | 57.605 / 233.194 | **30.196 (−%9,4)** |

- En çok MODIS tarafı etkileniyor (70.685 → 57.605, −%18,5). Küçük bir MODIS tespiti çoğu zaman aynı yangının VIIRS tespitleriyle birleşiyor ve 3 tespit sınırını aşıyor.
- **Temizlik ajanı için (koordinatör üzerinden):** Ortak olaylarda "≤ 3 tespit" sınırı iki sensörü birlikte saymamalı. `events.parquet` artık `n_modis`, `n_viirs` ve olaydaki tekil eşleştirme birimi sayısını (`n_mcell`, harmonizasyon `points_mcell.parquet`) taşıyor. Sınır sensör başına ya da `n_mcell` ile uygulanabilir. Karar temizlik ajanının.

## 6. Üçlü sınıf ve çifte sayım (C04, C05)

`events.parquet → match_class` (**ölçüldü**, varsayılan kural, temiz girdi):

| Sınıf | Olay |
|---|---|
| `ortak` (çakışmada iki sensör de gördü) | 35.651 |
| `yalniz_modis` | 57.543 |
| `yalniz_viirs` | 287.781 |
| `tek_sensor_donemi` (çakışma dışı; sınıf anlamsız) | 91.003 |
| Toplam | 471.978 |

Çakışma: olayın başladığı TR gününde iki sensör ailesinden en az birer uydunun `coverage.observed=True` olması.
C04: çakışma döneminde ortak kümeleme 380.975 olay veriyor; sensörler ayrı kümelenince 440.176 olay çıkıyor. Ortak kümeleme 59.201 olayın çifte sayılmasını önlüyor.

## 7. Doğruluk testi (C03)

`python src/clustering/bruteforce_check.py` (çıkış 0 = geçti):
- Örneklemler: üç dönemden il × ay pencereleri (yalnız Terra, Terra+Aqua, MODIS+VIIRS; dönem sınırları veriden, ilk Aqua ve ilk VIIRS tespiti) ve en yoğun 0,5° × 10 gün kareleri. Toplam 12 örneklem, 21.509 nokta.
- 7 kural çeşidi denendi (sabit / ayak izi / ayak izi tüm × sabit H / gecis, D = 0,5–2). Her örneklemde tüm n² çift, bağımsız yazılmış bir yüklemle değerlendirildi. **88 karşılaştırmanın hepsinde fark 0.**
- 20 yıllık tam koşunun etiketleri, olay-kapalı örneklemlerde kaba kuvvetle aynı. Parça büyüklüğü sonucu değiştirmiyor.
- Mutasyon testi: ızgara hücresi kasten küçültülmüş hatalı yöntem 12/12 örneklemde yakalandı, yani testin gücü var.

## 8. Ölçek

Yöntem: ızgara (hücre = en büyük bağ mesafesi; Türkiye için ±180° sarması gerekmiyor, geniş alanda assert ile durur) + hücre içinde zamana göre ikili arama + `scipy.sparse.csgraph.connected_components`. Varsayılan kural 20 yılda **~3–5 saniye** sürüyor, süreç belleği ~0,7 GB (bu makine; **ölçüldü**: `clustering_runtime_s`, `clustering_rss_mb`). Tüm duyarlılık ölçümleriyle betik ~5,5 dakika. Yıl veya bölge parçalarına bölmeye gerek kalmadı. Sonuç parça büyüklüğünden bağımsız (C03).

## 9. Çıktılar

| Dosya | İçerik |
|---|---|
| `data/processed/points_event.parquet` | `pid, event_id` (1.414.674 satır; temiz olmayan → −1; 1.044.222 nokta olaylı) |
| `data/processed/events.parquet` | Sözleşme §3 sütunları + `n, n_type2, sure_saat, kapsam_km, cakisma, n_mcell, status_karisik`. `status` = olay noktalarının en sık `points_status` etiketi (girdi temiz olduğu için şimdilik hep `temiz`). Olay düzeyindeki son anız etiketi temizlik ajanının adımı |
| `reports/metrics_parts/kumeleme.json` | Metrikler + `sensitivity.D/H/L` |
| `data/interim/kumeleme_analiz.json` | Bu belgedeki tablolar |

## 10. Açık noktalar
- Ayak izi dikdörtgeni kuzey-güney yönlü varsayıldı. Gerçekte tarama yönü yörünge eğimi kadar (~10°) dönük (**tahmini**, etkisi küçük).
- Geçiş pencereleri tespit saatlerinden çıkarıldı, swath verisi yok (**tahmini**).
- Kümeleme girdisi `status ∈ {'temiz','aniz'}` (`core.CLUSTER_STATUSES`). Anız olay düzeyinde bir etikettir ve olay yapısını değiştirmez; anız noktaları olaylarda kalır, `events.status` olay etiketini taşır. Bu karar, kümeleme ile anız etiketi arasında bir döngü oluşmasını önler.
