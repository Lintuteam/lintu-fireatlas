"""C06 için anlamlı kanıt: kesinti günleri payda/medyandan çıkarılıyor mu? (çıkış 0 = geçti)

Basitçe: Uydu bakamadığı günlerde "0 yangın" yazmak yanlıştır. Bu betik üç şeyi sayarak gösterir:
(1) kapsam dışı günde tespit yok, (2) kesinti günü olan aylarda düzeltmeli değer >= düzeltmesiz,
(3) kısmi/aşırı kesintili ay hücreleri sıfır değil BOŞ. Çıktı: audit/c06_takvim_kanit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main() -> int:
    k = pd.read_parquet(C.KAPSAM)
    d = pd.read_parquet(C.DAILY)
    m = pd.read_parquet(C.MONTHLY)
    m = m[m.birim == "TR"]
    gun_ham = d.merge(k, on="day_tr")
    kapsamsiz = gun_ham[(gun_ham.n_op_modis > 0) & (gun_ham.n_obs_modis == 0)]
    kes_mod = m[m.kesinti_pay_modis > 0]
    ok2 = bool((kes_mod["modis_ham_kk"].dropna() >= kes_mod.loc[kes_mod["modis_ham_kk"].notna(), "modis_ham"] - 1e-9).all())
    bos = m[(m.modis_ham.notna()) & m.modis_ham_kk.isna()]
    sifir_yanlis = int(((m.modis_ham_kk == 0) & (m.kesinti_pay_modis > C.t("kesinti_pay_max"))).sum())
    out = {"modis_kesinti_gunu_olan_ay": int(len(kes_mod)),
           "duzeltmeli_ge_duzeltmesiz": ok2,
           "tamamen_kapsamsiz_gunlerde_modis_tespit": int(kapsamsiz["modis_ham"].sum()),
           "bos_birakilan_ay_hucresi_TR": int(len(bos)),
           "kesintisi_cok_ve_sifir_yazilan": sifir_yanlis,
           "ornek": kes_mod[["yil", "ay", "kesinti_pay_modis", "modis_ham", "modis_ham_kk"]].head(5).to_dict("records")}
    ok = ok2 and sifir_yanlis == 0
    out["sonuc"] = "GECTI" if ok else "KALDI"
    p = C.ROOT / "audit" / "c06_takvim_kanit.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, default=float))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
