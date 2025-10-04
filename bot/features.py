from __future__ import annotations

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .config import get_settings

logger = logging.getLogger(__name__)


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=series.index).rolling(period, min_periods=period).mean()
    roll_down = pd.Series(down, index=series.index).rolling(period, min_periods=period).mean()
    rs = roll_up / (roll_down + 1e-12)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def engineer_features(data: Dict[Tuple[str, str], pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = get_settings()

    # Anchor on BTC 1m index
    key_btc_1m = (settings.base_symbol, "1m")
    if key_btc_1m not in data:
        raise ValueError("BTC 1m data is required to engineer features")
    btc_1m = data[key_btc_1m].copy()

    # Ensure proper dtypes
    for df in data.values():
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

    # Base 1m grid
    base_index = btc_1m.index

    feature_frames = []

    # Per symbol/timeframe engineered features
    for (symbol, interval), df in data.items():
        # Prepare reindexed to 1m grid
        if interval != "1m":
            df = df.reindex(df.index.union(base_index)).sort_index().ffill()
            df = df.reindex(base_index)
        else:
            df = df.reindex(base_index).ffill()

        # Price-based features
        close = df["close"]
        ret_1 = close.pct_change().fillna(0.0)
        vol_30 = close.pct_change().rolling(30, min_periods=10).std().fillna(0.0)
        rsi_14 = _rsi(close, 14)

        cols = pd.DataFrame(
            {
                f"{symbol}_{interval}_ret1": ret_1,
                f"{symbol}_{interval}_vol30": vol_30,
                f"{symbol}_{interval}_rsi14": rsi_14,
                f"{symbol}_{interval}_volume": df["volume"].fillna(0.0),
            },
            index=base_index,
        )
        feature_frames.append(cols)

    # Cross-asset correlations on 1m
    for sym_other in [s for s in settings.symbols if s != settings.base_symbol]:
        ret_btc = data[(settings.base_symbol, "1m")]["close"].pct_change()
        ret_other = data[(sym_other, "1m")]["close"].pct_change().reindex(base_index).fillna(0.0)
        corr_60 = (
            pd.concat([ret_btc, ret_other], axis=1)
            .rolling(60, min_periods=30)
            .corr()
            .unstack()
            .iloc[:, 1]
            .reindex(base_index)
            .fillna(0.0)
        )
        feature_frames.append(pd.DataFrame({f"corr60_{sym_other}": corr_60}, index=base_index))

    X = pd.concat(feature_frames, axis=1).fillna(method="ffill").fillna(0.0)

    # Targets: next 60 1m log-returns for BTC; we will convert to price later
    btc_close = btc_1m["close"].reindex(base_index).ffill()
    y_cols = {}
    for k in range(1, settings.forecast_horizon + 1):
        future = btc_close.shift(-k)
        y_cols[f"y_ret_{k}"] = (future / btc_close).apply(lambda v: np.log(v + 1e-12))
    Y = pd.DataFrame(y_cols, index=base_index).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    # Align and drop initial NaNs
    df_all = X.join(Y, how="inner").dropna()
    X_final = df_all[X.columns]
    Y_final = df_all[[c for c in df_all.columns if c.startswith("y_ret_")]]

    logger.info("Engineered features: %d features, %d samples", X_final.shape[1], X_final.shape[0])
    return X_final, Y_final
