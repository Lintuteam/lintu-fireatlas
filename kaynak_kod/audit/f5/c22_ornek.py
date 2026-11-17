"""F5 denetçi: rapordaki etiketli sayılardan rastgele 15 tanesini metrics.json'daki
herhangi bir sayısal değerle (yuvarlama toleransıyla) eşleştirir. Yazan kodu kullanmaz."""
import json, re, random, sys, pathlib
R = pathlib.Path(__file__).resolve().parents[2]
m = json.load(open(R/'reports/metrics.json', encoding='utf-8'))['metrics']
vals = []
def walk(k, v):
    if isinstance(v, bool): return
    if isinstance(v, (int, float)): vals.append((k, float(v)))
    elif isinstance(v, (list, tuple)):
        for x in v: walk(k, x)
    elif isinstance(v, dict):
        for kk, x in v.items(): walk(f'{k}.{kk}', x)
for k, d in m.items(): walk(k, d.get('value'))
num = r'[−-]?\d{1,3}(?:\.\d{3})*(?:,\d+)?|[−-]?\d+(?:,\d+)?'
pat = re.compile(rf'({num})\s*(%|MW|nokta|olay|tespit|kat|saat|gün|yüzde puan|hücre|oran|km|yıl)?[^()\n]{{0,25}}\((ölçüldü|tahmini|doğrulanmadı)\)')
def parse(s):
    s = s.replace('−', '-').replace('.', '').replace(',', '.')
    return float(s)
items = []
for f in ['calisma_prensibi', 'dogruluk_raporu', 'sunum_raporu']:
    t = (R/f'reports/{f}.md').read_text(encoding='utf-8')
    for mt in pat.finditer(t):
        items.append((f, mt.group(1), mt.group(2) or '', mt.group(3), t[max(0, mt.start()-60):mt.end()].replace('\n', ' ')))
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 2026)
samp = random.sample(items, min(15, len(items)))
def match(x, unit):
    c = []
    dec = 0
    for k, v in vals:
        for cand in (v, v*100) if unit in ('%', 'yüzde puan') or True else (v,):
            tol = max(abs(x)*0.0051, 0.051 if x != int(x) else 0.51)
            if abs(cand - x) <= tol: c.append(k)
    return sorted(set(c))[:4]
print('toplam etiketli sayi:', len(items))
bad = 0
for f, s, u, lab, ctx in samp:
    x = parse(s); c = match(x, u)
    if not c: bad += 1
    print(f'{f:17s} {s:>10s} {u:6s} [{lab}] -> {c if c else "ESLESME YOK"} | ...{ctx[-110:]}')
print('eslesmeyen:', bad)
