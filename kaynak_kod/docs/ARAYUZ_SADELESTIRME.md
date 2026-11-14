# Arayüz sadeleştirme görevi (koordinatör, 2026-11-13)

Kullanıcı geri bildirimi: "Görüntü kötü, kafa karıştırıyor, açıklayıcı değil." Hedef kitle: jüri ve konuya yeni biri. Kural: **ilk 10 saniyede ne gördüğünü anlasın.** Veri, hesap ve sayı kaynakları DEĞİŞMEZ (K1, C14 — her sayı yine metrics.json / agg'den). Yalnız sunum.

## Koordinatörün gördüğü sorunlar (ekran görüntüsünden)
1. **Bozuk çeviri anahtarları ekranda:** `app.telemetry`, `btn.scimode_eq`, `btn.quick_export`, `hud.events`, `hud.unit_events`, `hud.joint`, `hud.jump`, `tab.map_short`… i18n'de karşılığı yok. Hiçbir ham anahtar ekrana çıkmamalı (bir test ekle: DOM'da `xxx.yyy` biçimli görünür metin = 0).
2. **Üstte teknik metin duvarı:** dosya adları (events.parquet…), sensör tarihleri, etiket notları, zemin uyarısı monospace satırlar hâlinde. → Tek satırlık sade alt başlık + "Veri ve yöntem ⓘ" açılır paneli.
3. **İki ayrı gezinme:** sol ikon çubuğu (etiketleri bozuk, tıklayınca çalışmıyor) + sekmeler. → Tek gezinme.
4. **Kontrol kalabalığı:** bölge, çokgen çiz/bitir, daire lat/lon/yarıçap, uygula, temizle, en büyük olaya git, tarih sıfırla, sensör, FRP, ölçü, seri, durum onay kutuları (12 adet, sayılarla) hepsi aynı anda. → Varsayılan görünümde yalnız **Bölge** ve **Tarih aralığı**; gerisi "Gelişmiş süzgeçler ▸" altında kapalı.
5. **Harita anlaşılmıyor:** zemin/il sınırı yok, renkli kare ızgara (yoğunluk) ne olduğu yazmıyor, renk açıklaması yok. → İl sınırları her zaman görünür; varsayılan katman **il bazında olay sayısı (koroplet)** + başlıklı lejant ("Seçili dönemde yangın olayı sayısı"); yakınlaşınca olay noktaları. Yoğunluk ızgarası kaldırılsın veya açık lejantla isteğe bağlı olsun.
6. **Takvim sayı duvarı:** yıl×ay matrisinde her hücrede sayı + ≈, ★ işaretleri, altında kod gibi "Kaynak: hazır takvim tablosu (agg: seri_aylik, …)" metni. → Isı haritası renkle okunsun, sayı hücrede küçük/soluk veya üzerine gelince; başlık: "Her ayda kaç yangın olayı oldu? (2000–2026)"; lejant başlıklı; ★ için tek cümle açıklama; kaynak bilgisi ⓘ içinde.
7. **Jargon:** "Tek sensör dönemi", "Kalıcı (belirsiz)", "MODIS-eşdeğer", "match_class", "FRP", "NRT", "HUD". → Ekranda sade Türkçe + ⓘ ipucunda teknik terim. Ör. "MODIS-eşdeğer" → "Uydu farkı giderilmiş sayı ⓘ"; "Yalnız VIIRS" → "Yalnız yeni uydu (VIIRS) gördü".

## İstenen yapı (sade, referans/STIL_NOTU.md diline uygun; abartı yok)
- **Üst şerit:** başlık "Türkiye Yangın Aktivite Takvimi (2000–2026)", bir cümle açıklama ("NASA'nın iki uydu sisteminin kayıtları birleştirilerek tutarlı hâle getirildi. Bu bir yangın riski haritası değildir; geçmiş yangın aktivitesini gösterir."), sağda TR/EN ve "Veri ve yöntem ⓘ".
- **3–4 özet kartı**, sade etiketle ve kısa alt yazıyla: "Toplam yangın olayı", "En yoğun aylar", "Son tam ay, normale göre" (birincil seri + güven rozeti), "Uydu geçişindeki sıçrama: önce +%143 → sonra −%41 (gerçek değişim −%45)" — sayılar yine metrics.json'dan.
- **Solda sabit süzgeç paneli** (Bölge, Tarih aralığı; "Gelişmiş" kapalı). Sağda içerik.
- **Sekmeler (sıra):** 1) Takvim (varsayılan — NASA'nın ana isteği), 2) Harita, 3) Uydular nasıl birleştirildi (sıçrama grafiği + Birleştirme Laboratuvarı tek sekmede, adım adım anlatımlı), 4) İndir (CSV/PNG). "Piksel büyümesi" bu üçüncü sekmenin içinde küçük bir kart olsun.
- **Her sekmenin üstünde 1 cümle "Bu ekran ne gösteriyor?"** ve okuma ipucu.
- **Jüri modu = sade mod:** gelişmiş süzgeçler ve teknik ayrıntılar gizli; kartlar ve takvim öne çıkar.
- Uyarılar (yalnız Terra 2000–2002, 2026 kısmi/NRT, eşdeğer güvenilmez) ilgili grafiğin yanında küçük, sarı, tek cümlelik not; üstte yığın hâlinde değil.
- Monospace yalnız küçük etiketlerde; açıklama metinleri normal yazı tipinde, okunur boyutta (≥14px).
- Erişilebilirlik korunur (klavye, aria, kontrast, palet seçici "Gelişmiş" içinde).

## Kabul
- Ekranda ham i18n anahtarı 0 (test), konsol hatası 0.
- `tutarlilik_check.py`, `csv_check.py` çıkış 0; `python tools/check_all.py C14 C15 C16 C17 C18 C19 C20 C21` GEÇTİ; performans yeniden ölçülür.
- Takvim, harita, birleştirme ve indir sekmelerinin 1280×800'de ekran görüntüsü `audit/ekran/` altına (önce/sonra karşılaştırması için).
