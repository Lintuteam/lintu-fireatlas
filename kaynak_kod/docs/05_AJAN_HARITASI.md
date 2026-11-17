# Ajan Haritası

Ana oturum **koordinatördür** ve alt ajanları `.claude/agents/` altından çağırır. Her ajan önce `CLAUDE.md` ve `docs/` dosyalarını okur.

| Ajan | Sorumluluk | İstekler | Yazdığı yer |
|---|---|---|---|
| `veri-hatti` | 20 yıllık veri, ortak şema, FIRMS API, ek veri kaynakları, gözlem kapsamı | U-18, N-02 | `src/pipeline/`, `data/` |
| `harmonizasyon` | MODIS ızgarasına toplama, FRP eşiği, yüzdelik eşleştirme, eşdeğer seri, sıçrama | U-01..U-06, U-15 | `src/harmonize/` |
| `temizlik` | Çok yıllı sanayi tespiti, anız iklim takvimi, arazi örtüsü doğrulaması | U-07..U-09 | `src/cleaning/` |
| `kumeleme` | Sensör duyarlı eşleştirme, geçişe bağlı boşluk kuralı, D/H duyarlılığı | U-10..U-12 | `src/clustering/` |
| `takvim-analiz` | Yıl×ay matrisi, ay medyanı, aktivite sıralaması, anomali, tarih aralığı | U-16, N-05..N-07 | `src/analytics/` |
| `arayuz-harita` | Harita katmanları, birleştirme laboratuvarı, müfettiş, sıçrama grafiği, erişilebilirlik | U-13, U-14, U-17 | `src/app/` |
| `denetci` | Bağımsız yeniden hesap, uyuşmazlık taraması, olası soru provası | U-19, U-20 | `audit/` |
| `rapor-yazari` | `metrics.json` ve üç rapor | U-21 | `tools/`, `reports/` |

## Sıra ve bağımlılık

```
F0 koordinatör: açık sorular, veri sözleşmesi, tools/check_all.py iskeleti
F1 veri-hatti            -> denetci (veri doğrulaması)
F2 harmonizasyon ┐
   temizlik      ├ paralel; kümeleme olay kimliklerini üretir, harmonizasyon bunları kullanır
   kumeleme      ┘        -> denetci (doğruluk testleri C01-C13)
F3 takvim-analiz ┐ paralel
   arayuz-harita ┘        -> denetci (C14-C21)
F4 denetci: tam denetim, olası soru provası
F5 rapor-yazari: metrics.json ve üç rapor -> denetci (C22-C25)
```

Not: `kumeleme` ile `harmonizasyon` birbirine bağlı (olay kimliği ve eşleştirme birimi). Koordinatör önce ortak bir **eşleştirme birimi tanımı** üzerinde bu iki ajanı uzlaştırır (MODIS piksel ayak izi mi, sabit ızgara mı), sonra paralel çalıştırır.

## Devir teslim kuralı
Her ajan işini bitirince koordinatöre şunu döndürür: (1) ne yaptı, (2) hangi dosyaları yazdı, (3) çalıştırdığı kontroller ve çıktıları, (4) ölçtüğü sayılar (etiketli), (5) karşılaşılan belirsizlik ve açık sorular. Başka ajanın alanındaki dosyayı koordinatörün onayı olmadan değiştirmez.

## Çakışma çözümü
İki belge veya iki ajan çelişirse: `docs/01_ISTEKLER.md` (kullanıcı isteği) > `docs/03_KABUL_KRITERLERI.md` > `docs/04_VERI_SOZLESMESI_TASLAK.md` > diğerleri. Çözülemezse Yusuf'a sor.
