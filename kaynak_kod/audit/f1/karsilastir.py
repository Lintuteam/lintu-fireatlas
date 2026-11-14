"""Denetçi (F1): openpyxl ile okunmuş ham (xlsx_all.parquet) ile points.parquet / belgeler karşılaştırması.
Polars + kendi güven eşlemesi + matplotlib.Path il testi. Yazan kod içe aktarılmaz.
Kullanım: python audit/f1/karsilastir.py <ROOT> <xlsx_all.parquet> <cikti.json>"""
import sys, json, re
from pathlib import Path
import numpy as np, polars as pl

ROOT = Path(sys.argv[1]); XL = sys.argv[2]
out = {}


def rec(k, beklenen, bulunan, acik):
    try:
        fark = bulunan - beklenen
    except Exception:
        fark = None
    out[k] = {"beklenen": beklenen, "bulunan": bulunan, "fark": fark, "aciklama": acik}


x = pl.read_parquet(XL)
inv = json.loads((ROOT / "data/processed/inventory.json").read_text(encoding="utf-8"))
P = pl.read_parquet(ROOT / "data/processed/points.parquet")
src = "inventory.json / data/README.md / docs/04"
rec("toplam_satir_xlsx", inv["raw_rows_total"], x.height, "openpyxl ile 27 xlsx ilk sayfa satırı vs inventory.raw_rows_total")
rec("toplam_satir_points", x.height, P.height, "points.parquet satırı vs bağımsız xlsx sayımı")
for s, n in inv["by_sensor"].items():
    rec(f"sensor_{s}", n, x.filter(pl.col("sensor") == s).height, src)
satmap = {"Terra": "Terra", "Aqua": "Aqua", "Suomi NPP": "SNPP", "NOAA-20": "N20", "NOAA-21": "N21"}
out["_ham_satellite_degerleri"] = x.group_by("satellite").len().sort("satellite").to_dicts()
out["_ham_satellite_raw_degerleri"] = x.group_by("satellite_raw").len().sort("satellite_raw").to_dicts()
x = x.with_columns(pl.col("satellite").replace_strict(satmap, default="BILINMEYEN").alias("sat"),
                   pl.col("_file").str.extract(r"(\d{4})").cast(pl.Int32).alias("yil"),
                   pl.col("version").str.contains("NRT").alias("nrt"))
for s, n in inv["by_sat"].items():
    rec(f"uydu_{s}", n, x.filter(pl.col("sat") == s).height, src)
rec("nrt_satir", inv["nrt_rows"], int(x["nrt"].sum()), "version içinde 'NRT'")
rec("nrt_VIIRS", 58465, x.filter(pl.col("nrt") & (pl.col("sensor") == "VIIRS")).height, "docs/04 §1")
rec("nrt_MODIS", 2682, x.filter(pl.col("nrt") & (pl.col("sensor") == "MODIS")).height, "docs/04 §1")
out["_nrt_ilk_gun"] = {r["sensor"]: r["ilk"] for r in x.filter(pl.col("nrt")).group_by("sensor").agg(pl.col("acq_datetime_utc").min().alias("ilk")).to_dicts()}
out["_arsiv_son_gun"] = {r["sensor"]: r["son"] for r in x.filter(~pl.col("nrt")).group_by("sensor").agg(pl.col("acq_datetime_utc").max().alias("son")).to_dicts()}
rec("bt_ornek_esleme_satir", 184902, x.filter(pl.col("bt_mir_band").str.ends_with("ornek_esleme") | pl.col("bt_tir_band").str.ends_with("ornek_esleme")).height, "docs/04 §1, README")
rec("type_bos_satir", 61147, x.filter(pl.col("type").is_null()).height, "ham type boş; belgeler 61.147")
rec("type_bos_ve_nrt_degil", 0, x.filter(pl.col("type").is_null() & ~pl.col("nrt")).height, "type boş ama NRT olmayan")
tdist = x.with_columns(pl.col("type").cast(pl.Float64).fill_null(-1).cast(pl.Int8)).group_by("type").len().sort("type")
doc_t = {-1: 61147, 0: 1029262, 1: 5, 2: 315439, 3: 8821}
for r in tdist.to_dicts():
    rec(f"type_{r['type']}", doc_t.get(r["type"]), r["len"], "data/README.md type dağılımı")
rec("tam_yinelenen", inv["dup_rows"], x.height - x.drop(["_file", "_row"]).unique().height, "20 sütunda tam yinelenen")
rec("yinelenen_zaman_konum_uydu", 0,
    x.height - x.select(["acq_datetime_utc", "latitude", "longitude", "satellite"]).unique().height, "docs/04 §1")
rec("tekil_source_file", None, x["source_file"].n_unique(), "bilgi: build_points docstring '59 ham kaynak dosyası' diyor")
md = (ROOT / "data/README.md").read_text(encoding="utf-8")
cols = ["Aqua", "N20", "N21", "SNPP", "Terra"]
yd = {(r["yil"], r["sat"]): r["len"] for r in x.group_by(["yil", "sat"]).len().to_dicts()}
bad_rows, n_rows = [], 0
for m in re.finditer(r"^\| (\d{4}) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \| ([\d,]+) \|", md, re.M):
    n_rows += 1
    y = int(m.group(1)); vals = [int(v.replace(",", "")) for v in m.groups()[1:]]
    found = [yd.get((y, c), 0) for c in cols] + [sum(yd.get((y, c), 0) for c in cols)]
    if vals != found:
        bad_rows.append({"yil": y, "belge": vals, "bulunan": found})
rec("readme_yil_uydu_tablosu_uyusmayan_satir", 0, len(bad_rows), f"README {n_rows} yıl satırı tarandı; uyuşmayanlar: {bad_rows}")
x = x.with_columns(pl.col("acq_datetime_utc").str.to_datetime("%Y-%m-%dT%H:%M:%SZ", time_zone="UTC", strict=False).alias("t"))
rec("tz_hatali_parse", 0, int(x["t"].is_null().sum()), "acq_datetime_utc biçim hatası")
rec("utc_yili_dosya_yilindan_farkli", 0, x.filter(pl.col("t").dt.year() != pl.col("yil")).height, "docs/04 §1 'fark 0'")
for s in ["Terra", "Aqua", "SNPP", "N20", "N21"]:
    d = x.filter(pl.col("sat") == s)
    out[f"_aralik_{s}"] = [str(d["t"].min()), str(d["t"].max())]
x = x.with_columns((pl.col("yil").cast(pl.Int64) * 10_000_000 + pl.col("_row")).alias("pid"))


def guv(sensor, raw):
    if sensor == "MODIS":
        v = float(raw)
        return "dusuk" if v < 30 else ("nominal" if v < 80 else "yuksek")
    return {"l": "dusuk", "n": "nominal", "h": "yuksek"}.get(raw.strip().lower(), "?")


j = P.select(["pid", "t_utc", "day_tr", "lat", "lon", "frp", "conf_cls", "sat", "sensor", "src_year", "src_product"]).with_columns(
    pl.col("sat").cast(pl.Utf8), pl.col("conf_cls").cast(pl.Utf8), pl.col("sensor").cast(pl.Utf8),
    pl.col("src_product").cast(pl.Utf8), pl.col("t_utc").dt.convert_time_zone("UTC")).join(
    x.select(["pid", "t", "latitude", "longitude", "frp_mw", "confidence_raw", "sensor", "sat", "nrt"]).rename(
        {"sensor": "sensor_x", "sat": "sat_x"}), on="pid", how="full", coalesce=True)
rec("pid_eslesmeyen", 0, j.filter(pl.col("t").is_null() | pl.col("t_utc").is_null()).height,
    "pid = yıl*1e7 + xlsx veri satırı no (openpyxl sırası)")
conds = {
    "t_utc": pl.col("t_utc") != pl.col("t"),
    "lat": (pl.col("lat") - pl.col("latitude").cast(pl.Float64)).abs() > 1e-9,
    "lon": (pl.col("lon") - pl.col("longitude").cast(pl.Float64)).abs() > 1e-9,
    "frp": (pl.col("frp") - pl.col("frp_mw").cast(pl.Float64)).abs() > 1e-3,
    "sat": pl.col("sat") != pl.col("sat_x"),
    "sensor": pl.col("sensor") != pl.col("sensor_x"),
    "src_product": (pl.col("src_product") == "nrt") != pl.col("nrt"),
    "day_tr": pl.col("day_tr") != (pl.col("t") + pl.duration(hours=3)).dt.date(),
    "src_year": pl.col("src_year").cast(pl.Int64) != (pl.col("pid") // 10_000_000),
}
rng = np.random.default_rng(20261113)
samp = j[rng.choice(j.height, 1000, replace=False)]
s_m = {k: samp.filter(c).height for k, c in conds.items()}
s_m["conf_cls"] = sum(1 for r in samp.iter_rows(named=True) if guv(r["sensor_x"], r["confidence_raw"]) != r["conf_cls"])
rec("orneklem_1000_uyusmayan_alan", 0, sum(s_m.values()), f"tohum 20261113, alan bazlı: {s_m}")
for k, c in conds.items():
    rec(f"tum_satirlar_uyusmayan_{k}", 0, j.filter(c).height, "1.414.674 satırın tamamı pid ile birleştirildi")
allc = j.select(["sensor_x", "confidence_raw", "conf_cls"]).unique()
rec("guven_eslemesi_uyusmayan_tekil_kombinasyon", 0,
    sum(1 for r in allc.iter_rows(named=True) if guv(r["sensor_x"], r["confidence_raw"]) != r["conf_cls"]),
    f"bağımsız FIRMS kuralı vs conf_cls, {allc.height} tekil (sensör, ham) kombinasyonu")
edge = j.filter((pl.col("t").dt.hour() == 21) & (pl.col("t").dt.minute() < 5)).head(2).select(["pid", "t", "day_tr"])
out["_gun_siniri_ornek_21Z"] = [{k: str(v) for k, v in r.items()} for r in edge.to_dicts()]
# Türkiye 2016 öncesi kış saati UTC+2: sabit +3 ile farklı güne düşen satır (bilgi)
pre = j.filter((pl.col("t").dt.year() < 2016) & (pl.col("t").dt.hour() == 21))
rec("pre2016_21Z_saatinde_tespit", None, pre.height, "bilgi: 2016 öncesi kışın yerel saat UTC+2 idi; 21:00-21:59Z tespitleri sabit +3 ile ertesi güne düşer")

# il ataması bağımsız (matplotlib.Path even-odd)
from matplotlib.path import Path as MP
feats = json.loads((ROOT.parent / "demo/pipeline/cache/tr-cities.json").read_text(encoding="utf-8"))["features"]
paths = []
for f in feats:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    verts, codes = [], []
    for poly in polys:
        for ring in poly:
            ring = np.asarray(ring, dtype=float)[:, :2]
            verts += ring.tolist(); codes += [MP.MOVETO] + [MP.LINETO] * (len(ring) - 2) + [MP.CLOSEPOLY]
    paths.append((f["properties"]["name"], MP(np.asarray(verts), codes)))
Pi = P.select(["pid", "lat", "lon", "il", "type", "sensor", "src_year"]).with_columns(pl.col("il").cast(pl.Utf8), pl.col("sensor").cast(pl.Utf8))
dis = Pi.filter(pl.col("il") == "(dışı)")
ic = Pi.filter(pl.col("il") != "(dışı)")
sd = dis[rng.choice(dis.height, min(1500, dis.height), replace=False)]
si = ic[rng.choice(ic.height, 1500, replace=False)]


def my_il(lat, lon):
    pts = np.c_[lon, lat]; res = np.full(len(lat), None, dtype=object)
    for name, mp in paths:
        hit = mp.contains_points(pts) & np.array([v is None for v in res])
        res[hit] = name
    return res


d_il = my_il(sd["lat"].to_numpy(), sd["lon"].to_numpy())
i_il = my_il(si["lat"].to_numpy(), si["lon"].to_numpy())
rec("il_disi_orneklem_bagimsiz_ile_icerde", 0, int(sum(v is not None for v in d_il)), "1500 (dışı) örneğinden bağımsız PIP'in bir ile koyduğu")
rec("il_atanmis_orneklem_bagimsiz_farkli", 0, int(sum(a != b for a, b in zip(i_il, si["il"].to_list()))), "1500 il atanmış örnek, ad karşılaştırması")
top = dis.with_columns((pl.col("lat") * 10).floor().alias("la"), (pl.col("lon") * 10).floor().alias("lo")).group_by(["la", "lo"]).len().sort("len", descending=True).head(10)
out["_il_disi_profil"] = {
    "satir": dis.height,
    "type": {str(r["type"]): r["len"] for r in dis.group_by("type").len().to_dicts()},
    "sensor": {r["sensor"]: r["len"] for r in dis.group_by("sensor").len().to_dicts()},
    "en_yogun_0.1_hucre": [{"lat": r["la"] / 10, "lon": r["lo"] / 10, "n": r["len"]} for r in top.to_dicts()],
}
rec("type3_deniz_ama_il_atanmis", None, Pi.filter((pl.col("type") == 3) & (pl.col("il") != "(dışı)")).height, "bilgi")
rec("type3_deniz_toplam", None, Pi.filter(pl.col("type") == 3).height, "bilgi")
C = pl.read_parquet(ROOT / "data/processed/coverage.parquet")
out["_coverage"] = {"satir": C.height, "sutunlar": C.columns, "source": C["source"].unique().to_list(),
                    "observed_false": int((~C["observed"]).sum()), "n_overpass_dolu": int(C["n_overpass"].is_not_null().sum())}
dd = P.with_columns(pl.col("sat").cast(pl.Utf8)).group_by("sat").agg(
    pl.col("day_tr").n_unique().alias("tespitli_gun"), pl.col("day_tr").min().alias("ilk"), pl.col("day_tr").max().alias("son"))
cc = C.with_columns(pl.col("sat").cast(pl.Utf8)).group_by("sat").agg(pl.len().alias("cov_gun"))
out["_coverage_vs_tespitli_gun"] = [{k: str(v) for k, v in r.items()} for r in dd.join(cc, on="sat").to_dicts()]
Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
for k, v in out.items():
    print(k, "=>", (v["fark"], v["bulunan"]) if isinstance(v, dict) and "fark" in v else v)
