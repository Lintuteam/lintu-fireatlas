"""Zaman yardımcıları (K11): depolama UTC, gün sınırı TR (UTC+3).

Basitçe: Uydu saati dünya saatiyle (UTC) kaydeder; Türkiye'de gün gece 00:00'da (UTC 21:00)
değişir. 20:59Z bir günde, 21:00Z ertesi günde sayılır.
"""
from __future__ import annotations

import pandas as pd

TR_OFFSET_HOURS = 3  # Türkiye sabit UTC+3 (2016'dan beri yaz saati yok)


def tr_day(ts):
    """Timestamp -> datetime.date; Series/DatetimeIndex -> date nesneli Series (UTC+3)."""
    if isinstance(ts, pd.Timestamp):
        t = ts.tz_localize("UTC") if ts.tzinfo is None else ts
        return (t + pd.Timedelta(hours=TR_OFFSET_HOURS)).date()
    s = pd.to_datetime(ts, utc=True)
    return (s + pd.Timedelta(hours=TR_OFFSET_HOURS)).dt.date
