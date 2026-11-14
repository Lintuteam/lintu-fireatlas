"""Denetçi (F1): ham xlsx'leri openpyxl ile (pandas.read_excel / raw_all önbelleği KULLANMADAN) okur,
dosya+satır no ile polars parquet'e yazar (scratch). Bağımsız yeniden hesap girdisi."""
import sys, glob, os, time
import openpyxl, polars as pl
raw_dir, out = sys.argv[1], sys.argv[2]
frames = []
t0 = time.time()
for p in sorted(glob.glob(os.path.join(raw_dir, "FIRMS_Turkiye_*.xlsx"))):
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    hdr = next(it)
    cols = {h: [] for h in hdr}
    n = 0
    for r in it:
        if r is None or all(v is None for v in r):
            continue
        for h, v in zip(hdr, r):
            cols[h].append(None if v is None else str(v))
        n += 1
    wb.close()
    d = pl.DataFrame(cols, schema={h: pl.Utf8 for h in hdr}).with_columns(
        pl.lit(os.path.basename(p)).alias("_file"), pl.int_range(0, n).alias("_row"))
    frames.append(d)
    print(os.path.basename(p), n, round(time.time() - t0, 1), flush=True)
pl.concat(frames).write_parquet(out)
