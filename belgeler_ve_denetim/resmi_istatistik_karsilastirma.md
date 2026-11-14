# Resmi istatistikle bagimsiz karsilastirma: OGM orman yangini serisi ve bizim uydu olay serimiz

Uretim: 2026-11-14. Makine-okunur karsiligi: `resmi_istatistik_karsilastirma.json`; grafik verisi: `resmi_istatistik_karsilastirma_grafik.csv`.

## Ozet (juri icin)

- Bizim HAM temiz olay sayisi (tarla dahil) OGM orman yangini sayisiyla/alaniyla anlamli uyusmuyor; bunu saklamiyoruz. Uyumlastirilmis MODIS-esdeger olay sayisi OGM sayisiyla r = -0,06 (n=22) verir. Ham MODIS+VIIRS sayisinin r = 0,70 gorunen uyumu zamandaki artis egilimi ve 2012 VIIRS kirilimindan gelir; 2001-2011 (yalniz MODIS donemi) r = -0,21.
- Bizim seri ile OGM yanan alani arasindaki en iyi uyum, **orman-benzeri arazide (WorldCover agac+calilik >= %50) MODIS-yalniz FRP toplamidir**: n=25 yil (2001-2025), Pearson 0,99, Spearman 0,76; 2021 haric Pearson 0,96, Spearman 0,73; yalniz MODIS donemi 2001-2011 (n=11) Pearson 0,84, Spearman 0,66. En buyuk 5 yil bizde 2021, 2025, 2008, 2007, 2024; OGM'de 2021, 2025, 2008, 2024, 2020: dortu ortak.
- Bu, "yanan alan" olcusunun degil, "buyuk yangin yogunlugu" olcusunun uyumudur; FRP yanan hektar degildir. Pearson degeri 2021 (139.503 ha) tek noktasina cok bagli; guvenilir olan sira korelasyonu (0,73-0,76) ve log-log r = 0,84'tur.
- Yanan alan icin dogrudan es deger: yok. Yangin SAYISI icin uydu seri zayif (orman-benzeri seri r~0,05-0,3), cunku OGM sayisi 1-5 ha'lik kucuk yanginlari de sayar, MODIS (1 km) bunlari gormez.

## 1. Resmi veriler (OGM yillik orman yangini) ve kaynaklar

OGM'nin yillik tablosu "Ormancilik Istatistikleri" zip paketlerinde (indirilemedi, bkz. bolum 6). Acik web'de yil yil tablo tek sayfada yok; deger bir cok ikincil kaynaktan (TMMOB Yangin Dosyasi Tablo 1 = OGM 2025a, Kaggle OGM derlemesi, akademik makaleler, haber siteleri) toplandi. Her yilin kaynagi JSON'da. Durum etiketleri: `dogrudan` = acilan sayfada gordum; `ara_ozeti` = arama motoru ozetinde (PDF'i acmadim); `turetilmis` = baska resmi rakamdan hesaplandi (dusuk guven).

**Ic tutarlilik kontrolleri (ara ozeti degerlerine guveni artiran):**
- OGM 2002-2011 toplami 19.739 yangin / 83.638 ha (EMO, ara ozeti): tablodaki 2002-2011 toplami birebir tutuyor.
- OGM 2000-2010 toplami 22.769 yangin / 113.773 ha: tabloyla birebir tutuyor.
- OGM 2009-2018 toplam 23.878 yangin (Diken/bianet): tabloyla birebir tutuyor. Ayni kaynagin 58.333 ha toplami tutmuyor (tablo 66.647 ha); alan toplami hatali/farkli tanimli kabul edildi.
- 2010-2019 yillik ortalama 7.330 ha (TMMOB): tabloyla birebir tutuyor (73.300 ha).
- 2014-2023 toplam 25.690 yangin / 232.290 ha (OGM 2023b) ve 2015-2024 toplam 27.332 / 257.622: 2019/2022/2023 disindaki yillarla tutarli (2015-2024 alan toplami %0,4 icinde).

Bu kontroller 2000-2018 serisinin yillik degerlerinin birbirini tuttugunu gosteriyor. 2019, 2022 ve 2023 icin daha zayif: 2019 ve 2023 sayilari ile 2023 alani turetildi (2022 ve 2023 sayilari duyarlilik analizinde hesaba katilmadi; asil sayi korelasyonu yalnizca kaynakli 22 yilla yapildi).

| Yil | OGM yangin | OGM ha | Durum (sayi/ha) | orman-benzeri MODIS FRP (MW) | orman-benzeri buyuk olay (>=5 MODIS) | harm. temiz olay | Kaynak notu |
|---|---|---|---|---|---|---|---|
| 2000 | 2.353 | 26.353 | ara_ozeti/ara_ozeti | 247 | 0 | 86 | Bizde 2000 yalniz Terra ve yilin sonu; kiyas disi |
| 2001 | 2.631 | 7.394 | ara_ozeti/ara_ozeti | 3.769 | 2 | 2.689 |  |
| 2002 | 1.471 | 8.514 | dogrudan/dogrudan | 13.675 | 3 | 3.386 |  |
| 2003 | 2.177 | 6.644 | ara_ozeti/ara_ozeti | 28.680 | 7 | 3.919 | BirGun 1.978/6.246 veriyor; 2002-2011 toplamiyla uyusan TMMOB degeri secildi |
| 2004 | 1.762 | 4.876 | ara_ozeti/ara_ozeti | 13.877 | 6 | 3.902 |  |
| 2005 | 1.530 | 2.821 | dogrudan/dogrudan | 13.582 | 4 | 4.169 | EFFIS tabanli BirGun/Erdonmez de ayni degeri verir |
| 2006 | 2.227 | 7.762 | ara_ozeti/ara_ozeti | 28.040 | 7 | 4.923 |  |
| 2007 | 2.829 | 11.664 | dogrudan_sayi/ara_ozeti | 52.879 | 15 | 4.689 |  |
| 2008 | 2.135 | 29.749 | ara_ozeti/dogrudan | 63.301 | 21 | 2.916 | Antalya yangini dahil buyuk yil |
| 2009 | 1.793 | 4.679 | ara_ozeti/ara_ozeti | 11.778 | 1 | 9.903 |  |
| 2010 | 1.861 | 3.317 | dogrudan/dogrudan | 5.744 | 3 | 7.001 |  |
| 2011 | 1.954 | 3.612 | ara_ozeti/ara_ozeti | 11.506 | 1 | 8.786 |  |
| 2012 | 2.450 | 10.454 | ara_ozeti/ara_ozeti | 24.795 | 11 | 3.621 |  |
| 2013 | 3.755 | 11.456 | ara_ozeti/ara_ozeti | 33.546 | 9 | 4.941 |  |
| 2014 | 2.149 | 3.117 | ara_ozeti/ara_ozeti | 8.995 | 8 | 3.196 |  |
| 2015 | 2.150 | 3.219 | ara_ozeti/ara_ozeti | 6.089 | 9 | 6.468 |  |
| 2016 | 3.188 | 9.156 | ara_ozeti/ara_ozeti | 14.270 | 10 | 5.780 |  |
| 2017 | 2.411 | 11.993 | ara_ozeti/ara_ozeti | 23.090 | 12 | 4.096 |  |
| 2018 | 2.167 | 5.644 | ara_ozeti/ara_ozeti | 7.477 | 6 | 3.748 |  |
| 2019 | 2.687 | 11.332 | turetilmis/dogrudan | 3.273 | 2 | 4.200 | Sayi: 2020 sayisinin "gecen yila gore %26.5 artis" ifadesinden turetildi |
| 2020 | 3.399 | 20.971 | dogrudan/dogrudan | 25.525 | 11 | 4.754 | sol.org 20.917 yaziyor (yazim farki) |
| 2021 | 2.793 | 139.503 | dogrudan/dogrudan | 453.318 | 28 | 3.175 | JRC/EFFIS Advance Report 2021 resmi bildirim olarak ayni degerleri verir |
| 2022 | 2.360 | 12.799 | turetilmis/ara_ozeti | 34.598 | 8 | 2.647 | Yanan alan: OGM 2022 istatistikleri (haber ozeti). Sayi: 2014-2023 toplamindan turetilmis. dusuk guven |
| 2023 | 2.386 | 14.556 | turetilmis/turetilmis | 24.199 | 10 | 5.310 | Alan: 2014-2023 toplami (232.290) eksi diger yillar; Daily Sabah ~15.000 ile uyumlu. Sayi: 6.1 ha/yangin ile turetildi |
| 2024 | 3.797 | 27.485 | dogrudan/dogrudan | 51.222 | 24 | 6.259 |  |
| 2025 | 3.224 | 81.473 | dogrudan/dogrudan | 286.536 | 48 | 4.172 |  |

2026 (kismi, 5 Kasim'a kadar): 2.111 yangin, 24.527 ha (CNBC-e, Bakan aciklamasi). Bizim 2026 de yil sonuna kadar degil; ikisi de karsilastirmaya alinmadi.

**EFFIS:** yillik Turkiye EFFIS serisi (yanan alan, >=30 ha yangin sayisi) acilabilir bir web sayfasinda bulunamadi (EFFIS portali dinamik); korelasyon hesaplanmadi. EFFIS'e atfedilen tek tek degerler OGM ile ayni cikti (2005: 1.530/2.821; 2021: 2.793/139.503 JRC Advance Report'ta resmi bildirim olarak; 2024: 3.797/27.485), yani bagimsiz bir ikinci kaynak degil, ayni ulusal bildirim.

**Il duzeyi:** il/OBM tablosu zip icinde; acilamadi. Yalnizca 2009-2018 yanan alanda ilk 3 il (Hatay 7.042, Izmir 6.321, Antalya 6.211 ha, OGM/bianet) bulundu. Bizim orman-benzeri MODIS olay sayimiz 2009-2018 icin Adana 236, Izmir 126, Antalya 93, Hatay 85, Mersin 71, Mugla 67: OGM'nin ilk 3'u bizim ilk 4'te. Bu n=3 bir tutarlilik gozlemidir, rank korelasyonu degildir. UYARI: tum temiz olaylarda en cok olayli iller Sanliurfa, Mardin, Diyarbakir, Konya (tarla/aniz); ham seri il duzeyinde orman yanginiyla uyusmaz, il karsilastirmasi icin mutlaka orman-benzeri alt kume kullanilmali.

## 2. Bizim serimiz (nasil hesaplandi)

- Veri: `arayuz/data/events_<yil>.bin` (olay sutunlari: lat, lon, tmin, frp_sum, frp_max, n_modis, n_viirs, il, st ...), `points_<yil>.bin` (tespit duzeyi; sat, frp), `aniz_il_<yil>.bin` (aniz bayragi), `arazi_<yil>.bin` (WorldCover 2021 yuzdeleri), `harmonized.json` (yillik uyumlastirilmis MODIS-esdeger seri).
- `temiz` = durum 0 (deniz, volkan, sabit NASA, sanayi vb. elenmis). Bunlardan `aniz_il` bayragi olanlar disarida tutuldu (ham sayi yine de tarla agirlikli kaldi: temiz olayin ortalama %72,7'si tarla).
- MODIS-yalniz seriler yalniz Terra+Aqua tespitlerinden turetildi, boylece 2012 VIIRS kirilimi (olay sayisi 2011'de 7.174 -> 2013'te 11.694) etkisiz.
- Orman-benzeri = olay merkezi +-250 m'de agac+calilik >= %50. WorldCover 2021'e dayali sabit harita; yangin sonrasi harita/arazi degisimi yok sayilir. Bu kume tum temiz olaylarin yalnizca %2-6'sidir.
- Buyuk olay: >=5 (veya >=10) MODIS tespiti ya da MODIS tepe FRP >= 100 MW. VIIRS-bagimli esikler (ham >=10 tespit, ham frp_max>=100) sensor kirilimindan etkilenir, bu yuzden kullanilmadi.
- Yillik tum seriler CSV'de. Orman sezonu: Haziran-Eylul (JJAS).

## 3. Korelasyonlar (Pearson / Spearman)

| Seri | OGM yangin sayisi (n=22, kaynakli) | OGM yanan alan (n=25) | log yanan alan (n=25) | yanan alan, 2008 ve 2021 haric (n=23) | yangin sayisi 2001-2011 (n=11) | yanan alan 2012-2025 (n=14) |
|---|---|---|---|---|---|---|
| `harm_olay_temiz` | -0.06 / 0.07 | -0.24 / -0.23 | -0.32 / -0.23 | -0.12 / -0.05 | -0.22 / -0.06 | -0.27 / -0.06 |
| `temiz_ham_olay` | 0.70 / 0.62 | 0.29 / 0.40 | 0.34 / 0.40 | 0.54 / 0.55 | -0.21 / -0.06 | 0.12 / 0.43 |
| `modis_olay` | -0.05 / 0.11 | -0.22 / -0.22 | -0.32 / -0.22 | -0.12 / -0.05 | -0.21 / -0.06 | -0.27 / -0.09 |
| `modis_olay_JJAS` | -0.26 / -0.26 | -0.38 / -0.53 | -0.58 / -0.53 | -0.30 / -0.44 | -0.18 / -0.08 | -0.41 / -0.41 |
| `modis_frp_JJAS` | 0.08 / 0.20 | 0.49 / 0.01 | 0.17 / 0.01 | 0.18 / -0.14 | -0.12 / 0.13 | 0.70 / 0.23 |
| `modis_buyuk_frpmax100` | -0.24 / -0.13 | -0.27 / -0.42 | -0.45 / -0.42 | -0.24 / -0.38 | -0.11 / 0.09 | -0.26 / -0.30 |
| `modis_buyuk_n10` | 0.42 / 0.50 | 0.25 / 0.31 | 0.31 / 0.30 | 0.25 / 0.29 | -0.22 / -0.12 | 0.07 / -0.02 |
| `orman_modis_olay` | 0.05 / 0.08 | 0.13 / 0.23 | 0.22 / 0.23 | 0.28 / 0.13 | 0.39 / 0.19 | 0.48 / 0.51 |
| `orman_modis_olay_JJAS` | 0.02 / -0.06 | 0.11 / 0.10 | 0.19 / 0.10 | 0.28 / 0.04 | 0.42 / 0.19 | 0.43 / 0.39 |
| `orman_modis_frp` | 0.30 / 0.54 | 0.99 / 0.76 | 0.83 / 0.76 | 0.96 / 0.69 | 0.45 / 0.24 | 0.99 / 0.84 |
| `orman_modis_buyuk_n5` | 0.54 / 0.68 | 0.76 / 0.75 | 0.71 / 0.75 | 0.94 / 0.68 | 0.43 / 0.37 | 0.75 / 0.71 |
| `orman_modis_buyuk_frp100` | 0.28 / 0.34 | 0.37 / 0.43 | 0.45 / 0.43 | 0.59 / 0.30 | 0.50 / 0.42 | 0.58 / 0.63 |

`_ogm_ic_tutarlilik`: OGM'nin kendi yangin sayisi ile yanan alani arasinda (n=25) Pearson 0,35, Spearman 0,69. Yani resmi seriler birbiriyle de zayif/orta uyumlu; yangin sayisi ile alan farkli seyler olcer.

## 4. Aykiri yillar

- **2021:** OGM 139.503 ha (rekor, sayi ise 2.793 ile ortalama). Bizde ham olay sayisi yuksek degil (13.342), ama orman-benzeri MODIS FRP toplamimiz tum yillarin en buyugu (~453 bin MW). Yani buyuk yangin buyuklugunu FRP yakaliyor, olay sayisi yakalamiyor. Tek nokta Pearson'u sisirir; bu nedenle 2021 haric de rapor edildi.
- **2008:** OGM 29.749 ha (Antalya/Izmir buyuk yangin yili) ama OGM sayisi dusuk (2.135). Bizde ham olay sayisi yilin en dusuklerinden (2.916; Terra+Aqua donemi, ). Orman-benzeri FRP serisi 2008'i ilk 3'e koyuyor.
- **2009, 2011:** bizde ham olay sayisinin rekor MODIS yillari (9.903 ve 8.786) ama OGM yangin sayisi/alani dusuk (1.793/4.679; 1.954/3.612); olasi neden tarla/aniz yanginlari (test edilmedi).
- **2019:** orman-benzeri FRP serisinin en buyuk sira sapmasi (bizde dusuk, OGM 11.332 ha orta); 2014-2015: orman-benzeri buyuk olay sayisi OGM'ye gore yuksek sirali.
- **2000 ve 2026:** kismi, kiyas disi.

## 5. Hangi serimiz neyle uyuyor, dogru okuma

1. Ham/uyumlastirilmis **temiz olay sayisi**: OGM yangin sayisiyla uyum YOK. Neden: (a) bizim seri agirlikla tarla/aniz, OGM yalniz orman; (b) MODIS yalniz >=1 km'lik piksel ve yangin sayisi OGM'de 1-5 ha'lik yanginlari da kapsar. Ham MODIS+VIIRS toplaminin gorunen r=0,70'i sensor degisimi (2012) ve ortak artis egiliminin eseridir (2001-2011 icinde r negatif).
2. **Orman-benzeri MODIS FRP toplami**: yanan alanla guclu uyum (Spearman 0,76, tum yillar); yalniz MODIS doneminde de (n=11) 0,84/0,66. Bu bizim "buyuk orman yangini" gostergemizin bagimsiz resmi dogrulamasidir, ancak FRP yanan hektar olcmez ve niceliksel donusum (hektar tahmini) iddia edilmez.
3. **Orman-benzeri buyuk olay sayisi (>=5 MODIS tespiti)**: yanan alanla r=0,76, rho=0,75 (2021 haric r=0,94).
4. Mevsim kisiti (JJAS) tek basina yardimci olmadi (JJAS MODIS olay sayisi OGM sayisiyla negatif); tarla/aniz yanginlari da yazin yogun oldugu icin mevsim orman ayrimini saglamaz (bu neden yorumdur, ayrica test edilmedi).

## 6. Sinirlar ve durustluk notlari

- **Kapsam farki:** OGM yalniz orman yangini (devletin sorumlu oldugu orman alani) sayar; tarla, anız, cop yangini, ormandisi alan yangini OGM tablosunda yok (OGM ayrica "kirsal yangin" sayar: 2025'te 4.285; ormanla birlikte 7.509; bu seriyle de kiyas yapilmadi).
- **Resmi seri sorunlari:** yillik degerlerin cogu ikincil kaynaktan; 2019/2022/2023 degerleri kismen turetilmis. Kaynaklar arasi kucuk farklar var (2003: 1.978 vs 2.177; 2005 alan 2.821 vs 2.871; 2020 alan 20.971 vs 20.917). OGM'nin kendi zip paketleri okunabilirse bu degerler birebir dogrulanmali.
- **Coklu karsilastirma:** 12 seri x 7 alt-kume denendi; en iyi seri sonradan secildi (orman esigi tek deger, OGM'ye bakilmadan secildi ama seri secimi veriye bakilarak yapildi). p-degerleri bu yuzden iyimser; sonuc "dogrulandi" degil "tutarli ve gucu, 25 yil icin" diye ifade edilmeli.
- **Tek yillik arazi haritasi (2021) ve +-250 m pencere:** buyuk yangin ortasinda dogru sinif olmayabilir.
- **EFFIS:** yillik sayfa bulunamadi; EFFIS'le korelasyon yok. **Il duzeyi:** resmi il tablosu bulunamadi; il korelasyonu yok.
- **n=25 yil, trend:** hem OGM sayisi hem uydu ham sayisi zamanla artar; sira korelasyonu trendden etkilenir.

## 7. Indirme izni gerektiren dosyalar (indirilmedi)

- OGM Ormancilik Istatistikleri yillik zip paketleri (2013-2025; "12 ORMAN YANGINLARI" kategorisi 8 dosya/yil, il ve OBM tablolari muhtemelen burada): https://www.ogm.gov.tr/tr/e-kutuphane/kitaplik/Ormancilik-istatistikleri . Boyut sayfada yazmiyor.
- 2010 yilligi PDF: https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/Istatistikler/Ormanc%C4%B1l%C4%B1k%20%C4%B0statistikleri/Ormanc%C4%B1l%C4%B1k%20%C4%B0statistikleri%202010.pdf
- TMMOB Yangin Dosyasi (Tablo 1, 1990-2024, OGM 2025a): https://tmmob.org.tr/sites/default/files/orta-sayfa-26-ocak.pdf (ve cilt1_1.pdf)
- EFFIS Advance Report 2021: https://effis.jrc.ec.europa.eu/effis/reports-and-publications/effis-related-publications/Advance_Report_2021_JRC128678.pdf
- Kaggle veri seti (CSV): https://www.kaggle.com/datasets/ozlerhakan/forest-fires-dataset-in-turkey
