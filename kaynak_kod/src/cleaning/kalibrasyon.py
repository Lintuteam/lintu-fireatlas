"""Sanayi eşiklerinin (N, M, Y, S) yıl dışarıda bırakmayla (LOYO) seçimi ve NRT telafisinin testi.

Basitçe: NASA arşiv verisinde bazı noktaları zaten "statik kaynak" (type=2) diye işaretlemiş.
Bunu bir "cevap anahtarı" gibi kullanıyoruz ama hile yapmadan: bir yılı (ör. 2019) saklıyoruz,
kuralın eşiklerini kalan yıllardan seçiyoruz, sonra saklı yılda NASA'nın işaretiyle ne kadar
uyuştuğunu ölçüyoruz. Bunu her yıl için tekrarlıyoruz (K4). Böylece "type" bilgisi olmayan
NRT dönemi (2026-08 sonrası) için kuralın ne kadar iş göreceğini önceden ölçmüş oluyoruz.

Teknik olarak: Her kat (fold) Y için hücre özellikleri yalnız Y dışındaki yıllardan kurulur.
Eğitim amacı: eğitim yıllarındaki arşiv noktalarında (type∈{0,2}) NASA type=2'ye karşı F1 en
büyük olan (N, M, Y, S). Test: Y yılının noktaları, aynı özelliklerle. Hesap hücre düzeyinde
ağırlıklı yapılır (hücredeki nokta sayıları), nokta düzeyi sonuçla aynıdır.
Uyarı: NASA type=2 de bir maskedir, "yer gerçeği" değildir; uyuşma ölçülür, doğruluk değil.

Çalıştırma: python src/cleaning/kalibrasyon.py  -> audit/temizlik_kalibrasyon.json
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import persistence as P  # noqa: E402

GRID = {"N": [5, 10, 20, 40, 80], "M": [4, 6, 8, 10, 12], "Y": [2, 3, 5, 8], "S": [1, 2, 3, 4, 6, 8]}
OUT = C.AUDIT / "temizlik_kalibrasyon.json"


def _f1(tp, fp, fn):
    p = tp / np.maximum(tp + fp, 1); r = tp / np.maximum(tp + fn, 1)
    return np.where(p + r > 0, 2 * p * r / np.maximum(p + r, 1e-12), 0.0)


def loyo_grid(cy: pd.DataFrame) -> dict:
    combos = list(itertools.product(GRID["N"], GRID["M"], GRID["Y"], GRID["S"]))
    yrs = sorted(cy.loc[cy["na"] > 0, "yr"].unique())
    folds, test_tot = [], np.zeros((len(combos), 3))
    for y in yrs:
        f = P.features(cy, haric_yil=y)
        tr_t2 = f["t2"].to_numpy(); tr_neg = (f["na"] - f["t2"]).to_numpy()
        te = cy[cy["yr"] == y].set_index("cell")[["t2", "na"]].reindex(f.index).fillna(0)
        te_t2 = te["t2"].to_numpy(); te_neg = (te["na"] - te["t2"]).to_numpy()
        te_all_t2 = int(cy.loc[cy["yr"] == y, "t2"].sum())  # özelliği olmayan hücreler dahil
        ny, nm, nd, md = (f[c].to_numpy() for c in ("ny", "nmon", "nd", "medm"))
        tr_scores, te_rows = [], []
        for (N, M, Y, S) in combos:
            fl = (ny >= Y) & (nm >= M) & (nd >= N) & (md >= S)
            tp = tr_t2[fl].sum(); fp = tr_neg[fl].sum(); fn = tr_t2.sum() - tp
            tr_scores.append(float(_f1(tp, fp, fn)))
            ttp = te_t2[fl].sum(); tfp = te_neg[fl].sum(); tfn = te_all_t2 - ttp
            te_rows.append((ttp, tfp, tfn))
        te_rows = np.array(te_rows, dtype=float)
        test_tot += te_rows
        b = int(np.argmax(tr_scores))
        tp, fp, fn = te_rows[b]
        folds.append({"yil": int(y), "secilen": dict(zip("NMYS", combos[b])), "egitim_f1": tr_scores[b],
                      "test_tp": int(tp), "test_fp": int(fp), "test_fn": int(fn),
                      "test_precision": tp / (tp + fp) if tp + fp else None,
                      "test_recall": tp / (tp + fn) if tp + fn else None})
    # Katların seçtiği kombinasyonların test sonuçlarının toplamı (havuzlanmış LOYO)
    tp = sum(f["test_tp"] for f in folds); fp = sum(f["test_fp"] for f in folds); fn = sum(f["test_fn"] for f in folds)
    secimler = pd.Series([tuple(f["secilen"].values()) for f in folds]).value_counts()
    mod = secimler.index[0]
    return {"folds": folds, "havuz": {"tp": tp, "fp": fp, "fn": fn, "precision": tp / (tp + fp),
                                      "recall": tp / (tp + fn)},
            "secim_sikligi": {str(k): int(v) for k, v in secimler.items()},
            "mod_secim": dict(zip("NMYS", mod)),
            "sabit_kombinasyon_loyo": {",".join(map(str, c)): [int(x) for x in test_tot[i]]
                                       for i, c in enumerate(combos)},
            "grid": GRID}


def loyo_nrt_telafi(cy: pd.DataFrame, N, M, Y, S, pay) -> dict:
    """NRT telafisi: type bilgisi yokmuş gibi Y yılını sakla; (a) NASA hücre mirası, (b) kural,
    (c) ikisinin birleşimi NASA type=2'yi ne kadar yeniden üretiyor?"""
    res = {k: np.zeros(3) for k in ("miras", "kural", "birlesim")}
    for y in sorted(cy.loc[cy["na"] > 0, "yr"].unique()):
        f = P.features(cy, haric_yil=y)
        te = cy[cy["yr"] == y].set_index("cell")[["t2", "na"]]
        fl_m = P.nasa_mirasi(f, pay).reindex(te.index, fill_value=False).to_numpy()
        fl_k = P.sanayi_kurali(f, N, M, Y, S).reindex(te.index, fill_value=False).to_numpy()
        t2 = te["t2"].to_numpy(); neg = (te["na"] - te["t2"]).to_numpy()
        for k, fl in (("miras", fl_m), ("kural", fl_k), ("birlesim", fl_m | fl_k)):
            res[k] += (t2[fl].sum(), neg[fl].sum(), t2.sum() - t2[fl].sum())
    out = {}
    for k, (tp, fp, fn) in res.items():
        out[k] = {"tp": int(tp), "fp": int(fp), "fn": int(fn), "precision": tp / (tp + fp), "recall": tp / (tp + fn)}
    return out


def main():
    t0 = time.time()
    df = C.load_points()
    df = df[~df["type"].isin([1, 3])]
    cy = P.cell_year_table(df)
    g = loyo_grid(cy)
    m = g["mod_secim"]
    nrt = loyo_nrt_telafi(cy, m["N"], m["M"], m["Y"], m["S"], C.t("nasa_miras_payi"))
    out = {"betik": "src/cleaning/kalibrasyon.py", "veri_surumu": C.VERI_SURUMU,
           "yontem": "leave-one-year-out; ozellikler disarida birakilan yil haric kurulur; amac NASA type=2 F1",
           "sanayi_loyo": g, "nrt_telafi_loyo": nrt, "sure_sn": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("mod seçim", m, "sıklık", list(g["secim_sikligi"].items())[:4])
    print("havuz LOYO", {k: round(v, 4) if isinstance(v, float) else v for k, v in g["havuz"].items()})
    for k, v in nrt.items():
        print("NRT telafi", k, round(v["precision"], 4), round(v["recall"], 4))
    print("süre", out["sure_sn"], "sn")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
