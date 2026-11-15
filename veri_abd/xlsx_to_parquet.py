# ABD FIRMS xlsx -> yıllık parquet (salt okunur kaynak; hiçbir satır silinmez)
import openpyxl, pyarrow as pa, pyarrow.parquet as pq, sys, time, os
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
wb = openpyxl.load_workbook(src, read_only=True)
for ws in wb.worksheets:
    if not ws.title.isdigit(): continue
    t = time.time(); it = ws.iter_rows(values_only=True); hdr = next(it)
    cols = {h: [] for h in hdr}
    for r in it:
        if r[0] is None: continue
        for h, v in zip(hdr, r): cols[h].append(v)
    for h in ('confidence_raw', 'version'): cols[h] = [None if v is None else str(v) for v in cols[h]]
    pq.write_table(pa.table(cols), f'{out}/firms_abd_{ws.title}.parquet')
    print(ws.title, len(cols[hdr[0]]), round(time.time() - t), 's', flush=True)
