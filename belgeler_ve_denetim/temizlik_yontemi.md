# Temizlik yöntemi (F2, `temizlik` ajanı)

> Kapsam: U-07, U-08, U-09, C12 (N/M/F), C13. Kod: `src/cleaning/`. Eşikler: `src/config/esikler.json` (`N`, `M`, `F`, `temizlik.*`).
> Bu belgedeki sayıların tek kaynağı `reports/metrics.json`dır; metinde yalnız anahtar adı verilir (K1).
> Etiket kuralı (K5, denetim F2-05): veriden yapılan **sayımlar ve oranlar** (status sayıları, anız olay/nokta sayıları, LOYO uyuşmaları, WorldCover payları) "ölçüldü"; bir kuralın **doğru olduğuna dair** değerler (referans setine karşı kesinlik/duyarlılık, hasat penceresi uyumu) "tahmini"; yapılamayanlar "doğrulanmadı". Aynı sayı iki anahtarda farklı etiket taşımaz.
> Yöntem **kural tabanlıdır**; makine öğrenmesi modeli kullanılmadı. Eşikler veriden, yıl dışarıda bırakmayla (LOYO) seçildi.

## 0. Ne üretilir?

| Dosya | İçerik |
|---|---|
| `data/processed/points_status.parquet` | `pid, status, status_neden` — her nokta tam bir etiket (K3: silme yok) |
| `audit/temizlik_kalibrasyon.json` | Sanayi eşiklerinin LOYO seçimi, kat kat sonuçlar, NRT telafi testi |
| `audit/aniz_takvimi.json` | Bölge × ay anız profili, öğrenilen aylar, her yıl için o yıl hariç öğrenilmiş aylar |
| `audit/dogrulama_seti.csv` | Bağımsız doğrulama seti (OSM sanayi tesisleri, haberlerden bilinen yangınlar; kaynak sütunlu) |
| `audit/temizlik_ozet.json` | Tesis tesis referans sonuçları, koruma eşiği seçimi |
| `reports/metrics_parts/temizlik.json` | Metrikler + duyarlılık tabloları (N, M, F, Y, S, anız ayları, kalici_gece, koruma_G, aniz_olay_max_tespit) |

| `audit/worldcover_ornek.csv`, `audit/worldcover_metrikler.json` | WorldCover 2021 örneklem doğrulaması (nokta, grup, arazi sınıfı) |

Sıra: `python src/cleaning/kalibrasyon.py` → `python src/cleaning/build_status.py` → `python src/cleaning/worldcover.py` → `python tools/build_metrics.py`. Test: `python src/cleaning/test_cleaning.py`.
**Boru hattı sağlamlığı:** `build_status.py` her koşuda status'u sıfırdan kurar; `events.parquet` ve `points_event.parquet` varsa sonunda olay düzeyi anızı (`olay_aniz.uygula`) kendisi uygular, WorldCover sonuçlarını (`audit/worldcover_metrikler.json`) metrik parçasına yeniden ekler. `olay_aniz.py --yaz` tek başına da çalışır; önceki `aniz` etiketlerini önce `temiz`e döndürdüğü için tekrar çalıştırmak aynı dosyayı üretir (idempotent; içerik özeti iki koşuda aynı ölçüldü). Kümeleme girdisi {temiz, aniz} olduğu için anız yazmak olay yapısını değiştirmez; uyuşmazlık varsa `temizlik_tutarsiz_nokta` > 0 olur ve uyarı basılır.

## 1. NASA etiketleri korunur (U-07)

**Basitçe:** NASA bazı noktalara zaten "bu volkan", "bu denizde", "bu sabit bir sanayi kaynağı" demiş. Bu etiketlere dokunmuyoruz.

**Teknik olarak:** `type=1 → volkan`, `type=3 → deniz`, `type=2 → statik_nasa` (demodaki `computeStatus` ile aynı). NRT döneminde (`type=-1`) bu bilgi yok. Telafi: NRT noktasının 0,01° hücresindeki **arşiv** noktalarının en az `temizlik.nasa_miras_payi` kadarı type=2 ise `statik_nasa` (`status_neden=nrt_nasa_statik_mirasi`); type 1/3 için de aynı miras kuralı. Mirasın ve kuralın birlikte ne kadar iş gördüğü, NASA etiketi gizlenen bir yıl üzerinde ölçüldü: `temizlik_nrt_telafi_precision`, `temizlik_nrt_telafi_recall` (LOYO).
Sınırlama: NRT'de deniz mirası alan nokta sayısı ölçüldü ve sıfıra yakın; kıyı hücrelerinde type 3 çoğunluk değil (ör. İzmit körfezi). Deniz telafisi **doğrulanmadı**.

## 2. Çok yıllı kalıcılık: sanayi kuralı (U-08)

**Basitçe:** Bir orman yangını yıllarca, yılın her ayında aynı yerde yanmaz. Bir 1 km'lik karede beş farklı yılda, yılın sekiz farklı ayında ve her aktif yılın içinde aylarca ısı görülüyorsa orası büyük olasılıkla baca, rafineri meşalesi veya fabrikadır. Tarla yakması da her yıl tekrar edebilir, ama yılda bir iki ay sürer; "yıl içinde aylarca" şartı onu ayırır.

**Teknik olarak:** 0,01° hücre (`temizlik.hucre_derece`), iki sensör birlikte, type 1/3 hariç. Hücre özellikleri:
`ny` farklı yıl, `nd` farklı TR günü (tüm yıllar), `nmon` farklı **takvim** ayı (1–12, yıllar birleşik), `medm` aktif yıllarda yıl içi farklı ay sayısının medyanı, `gece` gece tespiti payı.
Kural: `ny ≥ Y` ve `nmon ≥ M` ve `nd ≥ N` ve `medm ≥ S` → `sanayi` (status_neden `kural_sanayi`). Demo'daki `cellMonths` (yıl-ay) 20 yıllık veride anlamını yitirdiği için `M` takvim ayına çevrildi.

**Eşik seçimi (K4):** `src/cleaning/kalibrasyon.py`. Her yıl Y için hücre özellikleri yalnız Y **dışındaki** yıllardan kurulur; eşikler, eğitim yıllarında NASA type=2'ye karşı F1'i en büyük yapan ızgara noktası seçilir (N ∈ {5,10,20,40,80}, M ∈ {4,6,8,10,12}, Y ∈ {2,3,5,8}, S ∈ {1,2,3,4,6,8}); test Y yılında yapılır. Config'teki değerler katların en sık seçtiği kombinasyondur (`temizlik_sanayi_loyo_kat_kararliligi`).
Sonuçlar: `temizlik_sanayi_loyo_precision/recall` (havuz), dönem kırılımı `..._modis_donemi` (2000–2011) ve `..._viirs_donemi` (2012–2026).
Dikkat: NASA type=2 bir **maskedir, yer gerçeği değildir**; bu metrikler "uyuşma"dır, doğruluk değil. Dönem sınırı `temizlik.viirs_baslangic_yili`. MODIS döneminde uyuşma düşüktür (`temizlik_sanayi_loyo_precision_modis_donemi`). **Neden (denetim F2-09):** referans seyrek. O dönemde NASA MODIS type=2 çok nadir, oysa kuralın "sanayi" dediği MODIS noktalarının büyük kısmı doğrulama setindeki bilinen bir tesise `temizlik.modis_donemi_tesis_km` km'den yakın (`temizlik_modis_donemi_sanayi_tesis_payi`, ölçüldü). Yani düşük değer kural hatasından çok NASA bayrağının eksikliğinden geliyor.

## 3. Kalıcı ısı kaynağı (belirsiz)

**Basitçe:** Bazı yerler sanayi kadar düzenli değil ama yangın gibi de davranmıyor: kömür ocağı, çöplük, aralıklı yakan bir tesis. Bunları "sanayi" demeden ayrı bir sepete koyuyoruz.

**Teknik olarak:** `kalici_belirsiz` = sanayi kuralının `Y` ve `M` koşulunu sağlayan, `N` veya `S`'yi sağlamayan ve tespitlerinin en az `temizlik.kalici_gece_payi` kadarı gece olan hücre. Gece şartının nedeni: tarla yakması gündüz yoğun, sürekli ısı kaynakları gece de görülür.
**Reddedilen tanım (ölçüldü):** İl bazında yıllık aktif-hücre oranından kurulan Poisson-binom rastlantı modeli ("bu hücre rastlantıyla bu kadar çok yıl yanmaz"). Bu tanım tarım ovalarında (Mardin, Adana, Şanlıurfa…) on binlerce noktayı işaretledi; yani "her yıl aynı tarlada yakma"yı yakalıyor, sanayi değil. Bu nedenle status için kullanılmadı; yalnız `status_neden=yillik_tekrar` **bayrağı** olarak duruyor (`temizlik_yillik_tekrar_bayrakli_temiz`, duyarlılık `sensitivity.kalici_alfa`). Görevdeki "her yıl aynı yerde yanan otlak" durumu bu bayrakla görünür; statüye çevrilip çevrilmeyeceği koordinatör kararıdır (açık soru).

## 4. Gerçek yangını silmeme: yangın koruması

**Basitçe:** Bir rafinerinin yanındaki ormanda gerçek yangın çıkarsa, rafineri karesindeki noktaları da "sanayi" diye atmak yanlış olur. O gün çevredeki normal karelerde de ateş varsa noktayı temiz bırakıyoruz.

**Teknik olarak:** Kural-sanayi veya kalıcı-belirsiz noktası, aynı TR gününde (2k+1)² hücre komşuluğunda (`temizlik.koruma_komsu_k`) kalıcı **olmayan** hücrelerde en az `temizlik.koruma_G` tespit varsa `temiz` kalır (`status_neden=yangin_korumasi`). G veriden seçilir: NASA-statik ∩ kural-sanayi hücrelerinde (kesin baca) yanlışlıkla korunan nokta payı ≤ `temizlik.koruma_yanlis_pay` olan en küçük değer (`temizlik_koruma_G_veriden`). NASA'nın kendi etiketlerine (statik_nasa) koruma uygulanmaz (demo davranışı); bilinen yangınlarda kalıcı etiket alan az sayıdaki nokta bu nedenledir (`temizlik_ref_yangin_koruma`).

## 5. Static Thermal Anomalies karşılaştırması

FIRMS'in STA maskesi şu an harita arayüzünde **deneysel** katman; toplu indirme veya API bulunamadı (`docs/ek_kaynaklar.md`). Karşılaştırma yapılmadı: `temizlik_sta_maskesi_karsilastirma` = **doğrulanmadı**. Yerine NASA arşivindeki type=2 ile LOYO uyuşması ölçüldü (bölüm 2) — bu STA maskesi ile aynı şey değildir.

## 6. Anız iklim takvimi (U-09)

**Basitçe:** Hasattan sonra tarlada sap yakılır; bu küçük, kısa, zayıf ateşler her yıl aşağı yukarı aynı aylarda olur ama bölgeden bölgeye değişir. Her coğrafi bölge için "küçük ateşler hangi aylarda yoğun?" sorusunu 20 yıldan öğreniyoruz. Hile olmasın diye bir yılın anız aylarını hep **o yıl hariç** diğer yıllardan öğreniyoruz.

**Teknik olarak:**
- Küçük aday (olay öncesi vekil): FRP < F_sensör ve aynı gün 3×3 hücre komşuluğunda ≤ `temizlik.aniz_kucuk_komsu` tespit. `F` MODIS ölçeğinde MW; `temizlik_F_modis_medyan` ile aynıdır (MODIS type=0 medyanı). VIIRS eşdeğeri sabit oranla değil, **yüzdelik eşleştirmeyle** bulunur (`temizlik_F_viirs_esdeger`; K8).
- Profil: 7 coğrafi bölge × ay, yıl içi payların yıllar arası ortalaması. Anız ayı = payı 1/12'yi aşan ay (`temizlik.aniz_ay_kurali`).
- LOYO ölçüsü: bir yılın küçük adaylarının o yıl hariç öğrenilen aylara düşme payı (`temizlik_aniz_loyo_kapsama`), aynı aylara düşen büyük tespit payı (`temizlik_aniz_loyo_taban`), oranları (`temizlik_aniz_loyo_kaldirac`).
- **Dürüst bulgu:** kaldıraç 1'e yakın. Yani "ay" tek başına küçük ateşi büyük ateşten ayırmıyor; Türkiye'de büyük tespitlerin de çoğu aynı tarım mevsiminde. Ayırıcı olan büyüklük/süre/FRP koşulları; ay şartı yalnız mevsim dışını eler.

**Döngüsellik ve bağımsız doğrulama:** Periyot uydu verisinden öğreniliyor, bu yüzden bağımsız bir kaynakla karşılaştırıldı: web'den alınan **kaba ulusal hasat takvimi** (`temizlik.hasat_penceresi`, kaynaklar config'te: TMO alım başlangıcı, FAO GIEWS). Öğrenilen ayların bu pencereye düşme payı: `temizlik_aniz_hasat_penceresi_payi` (**tahmini**; ulusal ve kaba, bölgesel değil).

**Arazi örtüsü doğrulaması (ESA WorldCover 2021, `src/cleaning/worldcover.py`):**
- *Basitçe:* Avrupa Uzay Ajansı'nın 10 m'lik arazi haritasında, "anız" dediğimiz noktaların gerçekten tarlaya, "sanayi" dediklerimizin yapılaşmış alana düştüğüne bakıyoruz. Harita yangın verisinden tamamen bağımsız.
- *Teknik olarak:* Resmî AWS S3 açık veri COG karoları (`esa-worldcover/v200/2021/map`), lisans **CC BY 4.0** (esa-worldcover.org veri erişim sayfası ve karo meta verisinde doğrulandı). Atıf: "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium". Karo indirilmez; GDAL aralık istekleriyle yalnız örnek noktaların düştüğü bloklar, 4× genel görünüm düzeyinden (~37 m) okunur; nokta çevresinde ±3 piksel (~±110 m) pencerede en sık sınıf alınır. Trafik sınırı `temizlik.wc_trafik_mb`; tahmini trafik `temizlik_wc_trafik_mb`.
- Gruplar (sabit tohumla rastgele seçim): `aniz` (olay düzeyi anız), `kural_kalici` (sanayi + kalici_belirsiz), `statik_nasa`, `buyuk_temiz` (n_mcell ≥ `temizlik.wc_buyuk_olay_mcell`, anız olmayan temiz olay; çoğu orman/çalı yangını beklenir).
- Sonuçlar: `temizlik_wc_<grup>_<sınıf>_pay`; özet `temizlik_aniz_arazi_ortusu` (anız → ekili alan payı). Yorum için anız grubunun ekili alan payını büyük temiz olay grubununkiyle karşılaştır.
- Sınırlamalar: WorldCover tek yıl (2021), 2000–2026 noktalarında arazi değişimi yok sayıldı; WorldCover'ın kendi sınıflandırma hatası bu projede ölçülmedi; nokta konum belirsizliği (VIIRS 375 m, MODIS ~1 km) pencereden büyük olabilir. Etiket bu yüzden "kurala göre etiket"; arazi örtüsü uyumu ölçüldü, yer doğrulaması değil.

## 7. Olay düzeyinde karar ve birleşme–anız etkileşimi (U-12)

Nokta düzeyinde `status_neden=aniz_adayi` yalnız bir bayraktır. Nihai karar olay düzeyindedir (`src/cleaning/olay_aniz.py`, kısmi etiket yok): olay büyüklüğü ≤ `temizlik.aniz_olay_max_tespit`, `sure_saat` ≤ `temizlik.aniz_olay_max_sure_saat`, olaydaki tüm noktalarda FRP < F_sensör ve TR başlangıç ayı olayın bölgesinin o yıl hariç öğrenilmiş anız aylarında → olayın tüm noktaları `status='aniz'` (`status_neden` += `olay_aniz`).

**"≤ 3 tespit" nasıl sayılır? (`temizlik.aniz_olay_sayim`)**
- *Basitçe:* Aynı küçük tarla ateşini MODIS 1 noktayla, VIIRS 3–4 noktayla görebilir. İki uydunun noktalarını toplarsak 2012 sonrası (VIIRS dönemi) aynı ateş "büyük" sayılır ve anız sayısı yapay olarak düşer. Bu yüzden MODIS ölçeğinde "kaç ayrı kare" olduğunu sayıyoruz.
- *Teknik olarak:* Üç sayım ölçüldü: `toplam` = n (demo), `sensor_max` = max(n_modis, n_viirs), `n_mcell` = olaydaki tekil eşleştirme birimi (sözleşme §5, MODIS piksel ayak izi). Seçim **n_mcell**: sensör dönemi tutarlılığı en iyi olan (VIIRS öncesi ile sonrası anız olay payı farkı en küçük: `temizlik_pay_viirs_oncesi_*`, `temizlik_pay_viirs_sonrasi_*`; sınır `temizlik.viirs_baslangic_yili`, geçiş yılı dışarıda; VIIRS öncesi yalnız MODIS olduğundan üç sayım orada aynıdır). `sensor_max` VIIRS'in 375 m ayrıntısını MODIS pikseline eşitlemediği için VIIRS döneminde yine büyük sayar. Sabit bir "VIIRS eşdeğeri" oranı kullanılmadı (K8). Üç sayımın olay/nokta farkı: `sensitivity.aniz_olay_max_tespit` (her eşik için üç sütun).

**Etkileşim (U-12):** nokta düzeyinde aday olup olayı da anız olan pay `temizlik_aday_olayda_aniz_pay`; kaybın nedenleri (çakışabilir) `temizlik_kayip_nedeni_n` (olay büyüdü), `..._sure`, `..._frp` (olaya güçlü bir tespit katıldı), `..._ay`.

## 8. Doğrulama seti ve C13

`audit/dogrulama_seti.csv`: 28 sanayi tesisi (rafineri, demir-çelik, termik santral; koordinat **OpenStreetMap Nominatim** `landuse=industrial` alan merkezinden, OSM kimliği `kaynak_ref`'te) ve 9 bilinen yangın (Wikipedia "2021 Turkey wildfires" sayfasındaki tarih + OSM ilçe merkezi; çoğu bitiş tarihi kaynakta yok, pencere "başlangıç + 5–9 gün" **tahmini**). FIRMS'ten bağımsızdır, eşik seçiminde kullanılmadı (K4).
**Çakışma temizliği (denetim F2-06):** CSV'ye `durum` (kullan/ayikla) ve `ayiklama_nedeni` sütunları eklendi. S02 (S01 ile aynı rafineri) ve S21 (S20 ile aynı kompleks) ayıklandı; Y02 ayıklandı (merkezi Kemerköy santralinin koordinatı, yangının kendi konumu kaynakta yok); Y06 yarıçapı geometriyle 15 → 7 km'ye indirildi (İsdemir ve Atlas tamponlarıyla çakışmasın diye). Kodda her nokta **en fazla bir** referansa atanır: önce kapsayan en yakın tesis, sonra tesis tamponu dışındaki kapsayan en yakın yangın.

**Basitçe:** Tesis noktası, bilinen yangın noktasından on kat fazla. Nokta nokta sayınca "kesinlik" neredeyse kusursuz görünür, çünkü yangın tarafı çok küçüktür. Bu yüzden her tesise ve her yangına eşit oy veriyoruz.

**Teknik olarak** (hepsi **tahmini**; yangın pencereleri ve yarıçaplar yaklaşık, küçük set):
- `ref_recall` = makro tesis yakalama: tesis başına kalıcı etiketli (statik_nasa / sanayi / kalici_belirsiz) nokta payının ortalaması.
- `ref_precision` = dengeli kesinlik = makro tesis yakalama / (makro tesis yakalama + makro yangın yanlış-işaret oranı `temizlik_ref_makro_yangin_fpr`). Sınıflar eşit ağırlıklı.
- `temizlik_ref_site_recall`: tesis düzeyi yakalama (noktalarının ≥%50'si kalıcı etiketli tesis payı). Düşüktür: termik santrallerin çoğu FIRMS'te nadiren görünür ve kural onları kalıcı saymaz; büyük rafineri ve demir-çelik tesisleri neredeyse tamamen yakalanır (tesis tesis: `audit/temizlik_ozet.json`).
- `temizlik_ref_nokta_precision`, `temizlik_ref_nokta_recall`: nokta düzeyi; sınıf dengesizliği nedeniyle şişkin, sunumda kullanılmamalı.
- Katkı ayrımı: `temizlik_ref_kural_makro_recall` / `temizlik_ref_kural_dengeli_precision` (yalnız kural, NASA type'sız = NRT senaryosu) ve `temizlik_ref_nasa_makro_recall` (yalnız NASA statik etiketi). Bilinen yangınlarda kalıcı etiket alan noktaların tamamı NASA type=2'dir; kural tek başına bu yangınlarda hiçbir noktayı işaretlemedi (`audit/temizlik_ozet.json`).

## 9. Duyarlılık (C12)

`reports/metrics.json → sensitivity`: `N`, `M`, `Y`, `S` (sanayi/kalıcı/temiz nokta sayısı, LOYO type=2 uyuşması, referans kesinlik/duyarlılık, yangın koruması), `F` (VIIRS eşdeğeri, aday sayısı, LOYO kapsama), `aniz_aylari` (uniform_ustu / top3 / top5 / demo Ağu–Ara), `kalici_gece`, `kalici_alfa` (yalnız bayrak), `koruma_G`, `aniz_olay_max_tespit`.

## 10. Açık sorular / sınırlamalar

1. `yillik_tekrar` (her yıl aynı yerde yakma) bayrak olarak kalır (koordinatör kararı, `audit/degisim_gunlugu.md`).
2. WorldCover tek yıl (2021) ve örneklem tabanlı; arazi değişimi ve WorldCover'ın kendi hatası ölçülmedi.
3. `dusuk_guven` bayrak olarak kalır (koordinatör kararı; demo "Tümü" varsayılanı).
4. NRT deniz telafisi zayıf (bölüm 1).
5. MODIS döneminde (2000–2011) NASA type=2 ile uyuşma düşük; hangi tarafın haklı olduğu doğrulanmadı.
