# İl bazlı FRP eşiğiyle anız çıkarma: simülasyon analizi (salt okunur)

Veri: `arayuz/data` events/points 2000-2026 (471.978 olay, 1.044.222 olay noktası). Betikler: scratchpad `aniz\*.py`. Etiket: tümü "ölçüldü" (simülasyon sayımı); kuralın doğruluğu "doğrulanmadı".

## 0. Önemli bulgu
- Ulusal eşikler = ülke geneli **type=0 tespitlerinin** FRP medyanı (MODIS 15,0; VIIRS 4,4 MW). Şanlıurfa için aynı tanım (type=0 medyanı) **16,5 / 4,73 MW** verir, yani ulusalın yalnız %10 üstü. Raporda geçen 22,5 / 5,82 MW, **kalan temiz (st=0) noktaların** medyanıdır; bu anız ayıklandıktan sonra kalan yüksek-FRP kuyruğudur (dairesel). Bu yüzden "il medyanı" tek başına Şanlıurfa'yı çözmez.
- Kural "olaydaki TÜM noktalar < medyan" olduğundan, 2-3 pikselli bir olayın medyanı aşma olasılığı doğal olarak yüksektir; sorun medyanın düzeyinden çok "tümü < medyan" koşuludur.
- Şanlıurfa'nın temiz payı hiçbir eşik varyantıyla anlamlı düşmüyor (aşağıda): tarım illeri birlikte aniz alıyor, pay sabit kalıyor.

## 1. İl × sensör medyanı (type=0, `P.tip==0`)
- n(il,sensör) ≥ 300 yoksa bölge medyanına, o da yoksa ulusal değere düşülür. Yetersiz veri: MODIS 15 il, VIIRS 5 il (Ardahan, Artvin, Giresun, Rize, Yalova); T varyantında 34 (il,sensör) çifti bölgeye düşer.
- Kararlılık (LOYO, yıl dışarıda): medyan sapması ortanca %2,8 (M) / %3,5 (V); %10'u aşan: Antalya (%39), Bilecik, Karabük, Bolu, Kilis, Kütahya, İzmir (%17), Muğla (%21), Çanakkale, Kastamonu, Bartın, Düzce, Isparta, Rize. Şanlıurfa çok kararlı (M %1,8; V %1,3). Yıllar arası değişim katsayısı Şanlıurfa M 0,16, V 0,09.
- Orman illeri (Muğla 33,3/6,48; Antalya 26,6/6,15) medyanı gerçek yangınlar yükseltiyor: il medyanı orman illerinde güvenli bir "anız yoğunluğu" göstergesi değildir (yangın FRP'si anız eşiğine karışır).

## 2. Ulusal kuralın yeniden üretimi
Kural: n_mcell ≤ 3, süre ≤ 12 sa, tüm noktalar FRP < F, TR başlangıç ayı bölgenin o yıl hariç anız aylarında. Uygulama verisinde `n_mcell` yok; vekil: `max(n_modis, ceil(n_viirs/4))`. Süre = `dur`/60, ay = (`tmin`+180 dk) epoch 2000-01-01.
- Gerçek `st=6` (169.115 olay) ile uyum: **%99,94** (471.978 olaydan 298 yanlış-pozitif, 0 yanlış-negatif). Tüm koşullar (FRP/süre/ay) gerçek etiketle %100 örtüşüyor; tek fark n_mcell vekili. Toplam n kullanılırsa uyum %99,13 (4.118 kaçak), `sensor_max` %99,19.
- Simülasyonda mevcut aniz olaylar "boyut koşulunu sağlıyor" varsayıldı (kayıp 0), yalnız temiz olaylar için vekil kullanıldı.

## 3. Varyantlar (yalnız ek anız; mevcut 169.115 hiç kaybolmaz; eşik tabanı = ulusal)
| Varyant | Şanlıurfa eşik (M/V) | Yeni aniz olay | Temiz payı Urfa (%15,35 →) | Anız payı öncesi/sonrası 2012 (eski 0,380/0,355) |
|---|---|---|---|---|
| A: il type=0 medyanı | 16,5 / 4,73 | 12.076 (%4,0 temiz) | %15,37 | 0,417 / 0,378 |
| T: il temiz medyanı | 22,5 / 5,82 | 42.992 (%14,2) | %15,19 | 0,502 / 0,439 |
| T + tavan 1,5×ulusal (**önerilen**) | 22,5 / 5,82 | 41.395 (%13,7) | **%15,10** | 0,490 / 0,437 |
| Q75 type=0, tavan 2× | 30,0 / 8,80 | 80.639 (%26,6) | %14,67 | 0,570 / 0,522 |
- Önerilen varyantta Şanlıurfa temiz olayı 46.490 → 39.476 (-7.014), ama ulusal temiz da düştüğü için **pay yalnız %15,35 → %15,10**. Adana, Diyarbakır, Konya, Mardin benzer oranda düşer. Yani Şanlıurfa "şişmesi" gerçekte Şanlıurfa'ya özgü değil, tarım ovası olgusu; eşikle ~%15'in altına inmez (Q75'te bile %14,7).
- İl bazında yeni aniz en çok (T): Şanlıurfa 7.014, Adana 5.926, Diyarbakır 3.674, Konya 3.594, Mardin 3.383, Osmaniye 1.605, Yozgat 1.199, Adıyaman 1.185, K.Maraş 1.088, Hatay 1.036, Mersin 1.015, Gaziantep 1.005, Sivas 719, Batman 646, Kırşehir 619. (A için sıra: Adana 2.959, Şanlıurfa 1.802, Mardin 1.528, Konya 1.102, Diyarbakır 1.073...)
- Ay: yalnız mevcut anız aylarında (Haz-Ara) etki var; T önerilen: Haz 5.952, Tem 2.610, Ağu 4.372, Eyl 11.399, Eki 9.755, Kas 6.222, Ara 1.085; Oca-May 0.
- Yıl: T için anız payı yıllık 0,34-0,54 (eski 0,28-0,41), her yıl +%7-13 puan; **2012 sonrası/öncesi farkı büyüyor**: eski 0,380 → 0,355 (fark 2,5 puan), T için 0,490 → 0,437 (5,3 puan). Yani yapay sensör sıçraması olmasa da VIIRS döneminde yeni kural göreli daha az anız yakalıyor (VIIRS'in 375 m pikseli tek ateşte daha yüksek tepe FRP veriyor; VIIRS eşiği 5,82 MW sabit). A varyantında fark 3,9 puan. Dikkat: 2000 yılı (kısmi) eski 0,80.
- Şanlıurfa'da T sonrası kalan 39.476 temiz olayın: %39'u anız ayı dışında, %12'si >12 sa, %3'ü n>3; 20.040'ı yalnız FRP yüzünden kalıyor (VIIRS tepe FRP ortanca ≈10 MW, ulusal-il eşiğin üstünde). Bunları da kaldırmak P90'a yakın eşik ister (aşırı agresif).

## 4. Güvenlik
- Belgelenmiş 33 olay (gercek_dogrulama 20 + recall yakalanan): anıza çevrilen **0** (A, T, Q75, T-tavan hepsi). Büyük olaylar (frp_max ≥300, n ≥20, süre >24 sa; 141 olay): **0**. Yeni anız olayın en büyüğü: n ≤15, frp_max ≤36,5 MW (T), ≤22,4 MW (T-tavan); yapısal olarak büyük yangınlar boyut/süre koşulunda elenemez.
- Dolaylı: belgelenmiş yangın olaylarının ~30 km ve ±7 gün çevresinde yeni aniz olay: A 28, T 51, Q75 80 (kısa, küçük yan olaylar; yangının kendisi değil). Orman illerinde (Muğla/Antalya) tavan 1,5× bunları sınırlıyor.

## 5. Resmî görünümle tutarlılık
Projede il bazlı OGM yangın istatistiği **yok** (yalnız ulusal toplam, 2021 Tablo 16-17 ve birkaç il toplamı: ör. İzmir 26.260 ha). Bu yüzden il sıra korelasyonu OGM'ye karşı **hesaplanamadı**. Yalnız iç tutarlılık: il temiz olay sayısı sıra korelasyonu (Spearman) önce/sonra: A 0,9995; T 0,9972; Q75 0,994; yani sıralama pratik olarak değişmiyor.

## 6. Öneri
- Varsayılan bilimsel kural değişmez; opsiyonel anahtar "Anızı çıkar (il bazlı eşik)" = **T + tavan**: F_il,sensör = clamp( medyan(il temiz FRP, sensör); ulusal; 1,5×ulusal ), n(il,sensör) ≥ 300 değilse bölge medyanı, o da yoksa ulusal. Ulusal 15,0/4,4 aynı kalır; diğer koşullar (n_mcell ≤3, ≤12 sa, bölge/yıl anız ayı) aynı. Dairesellik yüzünden eşikleri tek tur (başlangıç temiz/aniz durumundan) ve LOYO ile hesaplamak, pipeline'da `olay_aniz.py` içinde yapılmalı (uygulama verisinde n_mcell yok; vekil %99,94).
- Dosya: `arayuz/data/aniz_il_<y>.bin`, olay sırasıyla uint8 (0 = değişmedi, 1 = yalnız il-bazlı kuralla anız); uygulama "il bazlı" açıkken `st==0 && aniz_il==1` olayları anız sayar (nokta düzeyi: evid üzerinden). Boyut ≈ 472 KB toplam. Eşik tablosu (il×sensör, kaynak: il/bölge/ulusal) manifest'e yazılsın.
- Kullanıcıya not: Şanlıurfa payı bu anahtarla ~%15,1'e iner (≈ -7.000 olay), %15'in altına inmez; ilçe (Harran) bazı yok, il düzeyindedir.
