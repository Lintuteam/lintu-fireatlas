"""FIRMS Area API çekici (MAP_KEY ortam değişkeninden).

Basitçe: NASA'nın veri vitrininden belirli bir bölge ve tarih aralığını, "dakikada çok sık sorma"
kuralına uyarak, parça parça indirir. Anahtar koda yazılmaz.

Teknik olarak (resmî sayfa https://firms.modaps.eosdis.nasa.gov/api/area/ ile doğrulandı, 2026-11-13):
- URL: /api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{DAY_RANGE}/{YYYY-MM-DD}
- DAY_RANGE: 1–5 gün (doğrulandı). Tarih verilmezse en yeni veri.
- Kota: 10 dakikada 5000 işlem (doğrulandı); büyük isteklerin birden çok işlem sayılabileceği belirtiliyor.
- Kaynaklar: MODIS_NRT, MODIS_SP, VIIRS_SNPP_NRT/_SP, VIIRS_NOAA20_NRT/_SP, VIIRS_NOAA21_NRT/_SP.
- Veri bulunurluk aralığı kaynak başına /api/data_availability/ ile sorulur. DOĞRULANMADI: SP
  (standart işleme) için en eski tarih; kaynak başına farklı olabilir, çağrıdan önce sorgulayın.
Çalıştırma örneği (anahtar gerekir):
  set FIRMS_MAP_KEY=...  &  python src/pipeline/firms_api.py --source VIIRS_NOAA21_NRT --start 2026-11-01 --end 2026-11-12 --out data/interim/api
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
TR_BBOX = "25.5,35.7,44.9,42.2"   # west,south,east,north (veri kapsam kutusu + pay)
MAX_DAYS = 5                      # resmî sınır (doğrulandı)
QUOTA, WINDOW_S = 5000, 600       # 10 dakikada 5000 işlem (doğrulandı)
SAFETY = 0.8                      # kotanın %80'ini aşma


class RateLimiter:
    def __init__(self, quota=int(QUOTA * SAFETY), window=WINDOW_S):
        self.q, self.w, self.t = quota, window, collections.deque()

    def wait(self):
        now = time.monotonic()
        while self.t and now - self.t[0] > self.w:
            self.t.popleft()
        if len(self.t) >= self.q:
            time.sleep(self.w - (now - self.t[0]) + 1)
        self.t.append(time.monotonic())


def fetch(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(min(2 ** i * 5, 120))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if i == tries - 1:
                raise
            time.sleep(min(2 ** i * 5, 120))


def chunks(start: dt.date, end: dt.date):
    d = start
    while d <= end:
        n = min(MAX_DAYS, (end - d).days + 1)
        yield d, n
        d += dt.timedelta(days=n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--bbox", default=TR_BBOX)
    ap.add_argument("--out", default="data/interim/api")
    a = ap.parse_args(argv)
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        sys.exit("FIRMS_MAP_KEY ortam değişkeni yok (anahtar çalışması yapılmadı; doğrulanmadı).")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rl = RateLimiter()
    for d, n in chunks(dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)):
        f = out / f"{a.source}_{d.isoformat()}_{n}d.csv"
        if f.exists():
            continue  # devam edilebilir
        rl.wait()
        f.write_text(fetch(f"{BASE}/{key}/{a.source}/{a.bbox}/{n}/{d.isoformat()}"), encoding="utf-8")
        print("ok", f.name)


if __name__ == "__main__":
    main()
