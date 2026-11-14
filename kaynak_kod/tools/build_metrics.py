"""Metrik parçalarını tek doğruluk kaynağına birleştirir (reports/metrics.json).

Basitçe: Her uzman ajan kendi ölçtüğü sayıları kendi "fişine" yazar
(reports/metrics_parts/<ajan>.json). Bu betik fişleri tek deftere geçirir.
Aynı metrik iki fişte farklı değerle görünürse durur: bu bir uyuşmazlıktır (U-19).

Teknik olarak: Parça biçimi
  {"metrics": {anahtar: {value, unit, tanim, betik, veri_surumu, etiket}},
   "sensitivity": {"D": [{param, ...sonuçlar}], ...}}
etiket ∈ {ölçüldü, tahmini, doğrulanmadı} (K5). Eksik alan veya geçersiz etiket hata verir.
rapor-yazari F5'te bu betiği genişletebilir; birleştirme kuralı değişmez.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "reports" / "metrics_parts"
OUT = ROOT / "reports" / "metrics.json"
FIELDS = ("value", "unit", "tanim", "betik", "veri_surumu", "etiket")
LABELS = {"ölçüldü", "tahmini", "doğrulanmadı"}


def main() -> int:
    metrics, sens, src, errors = {}, {}, {}, []
    for f in sorted(PARTS.glob("*.json")):
        part = json.loads(f.read_text(encoding="utf-8"))
        for k, v in part.get("metrics", {}).items():
            miss = [x for x in FIELDS if x not in v]
            if miss:
                errors.append(f"{f.name}:{k} eksik alan {miss}")
            if v.get("etiket") not in LABELS:
                errors.append(f"{f.name}:{k} geçersiz etiket {v.get('etiket')!r}")
            if k in metrics and metrics[k]["value"] != v.get("value"):
                errors.append(f"UYUŞMAZLIK {k}: {src[k]}={metrics[k]['value']} vs {f.name}={v.get('value')}")
            metrics[k], src[k] = v, f.name
        for p, rows in part.get("sensitivity", {}).items():
            if p in sens:
                errors.append(f"duyarlılık {p} iki parçada: {f.name}")
            sens[p] = rows
    if errors:
        print("\n".join(errors))
        return 1
    OUT.write_text(json.dumps({
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": sorted({*src.values()}), "metrics": metrics, "sensitivity": sens,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(metrics)} metrik, {len(sens)} duyarlılık tablosu -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
