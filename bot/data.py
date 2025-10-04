from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .binance_client import BinanceClient
from .config import get_settings
from .utils import ensure_dir

logger = logging.getLogger(__name__)


def _data_path(symbol: str, interval: str) -> Path:
    settings = get_settings()
    ensure_dir(settings.data_dir)
    return Path(settings.data_dir) / f"{symbol}_{interval}.csv"


def _merge_and_save(path: Path, df_new: pd.DataFrame) -> pd.DataFrame:
    if path.exists():
        df_old = pd.read_csv(path, parse_dates=["datetime"], index_col="datetime")
    else:
        df_old = pd.DataFrame(columns=df_new.columns)
    df = pd.concat([df_old, df_new]).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df.to_csv(path, index_label="datetime")
    return df


def fetch_and_cache(symbol: str, interval: str, days: int = 90) -> pd.DataFrame:
    client = BinanceClient()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%d %H:%M:%S")

    df = client.fetch_klines(symbol, interval, start_str=start_str)
    df = df.rename_axis("datetime")
    path = _data_path(symbol, interval)
    df_saved = _merge_and_save(path, df)
    logger.info("Fetched %s %s: %d rows (cached: %s)", symbol, interval, len(df), path)
    return df_saved


def load_cached(symbol: str, interval: str) -> pd.DataFrame:
    path = _data_path(symbol, interval)
    if not path.exists():
        raise FileNotFoundError(f"No cached data for {symbol} {interval} at {path}")
    return pd.read_csv(path, parse_dates=["datetime"], index_col="datetime")


def get_all_data(days: int = 90) -> Dict[Tuple[str, str], pd.DataFrame]:
    settings = get_settings()
    data: Dict[Tuple[str, str], pd.DataFrame] = {}
    for sym in settings.symbols:
        for itv in settings.intervals:
            data[(sym, itv)] = fetch_and_cache(sym, itv, days=days)
    return data
