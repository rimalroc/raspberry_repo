from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .config import get_settings


@dataclass
class Signal:
    action: str  # 'buy', 'sell', 'hold'
    expected_return: float
    confidence: float
    position_usdt: float = 0.0


def generate_signal(predicted_log_returns: np.ndarray) -> Signal:
    settings = get_settings()
    # Aggregate metrics
    cum_ret = float(np.exp(predicted_log_returns.sum()) - 1.0)
    pos_ratio = float((predicted_log_returns > 0).mean())
    dd = float(np.exp(np.minimum.accumulate(predicted_log_returns.cumsum())) - 1.0)

    confidence = pos_ratio

    # Simple rules
    if cum_ret > settings.min_expected_return_pct and confidence >= 0.55:
        return Signal(action="buy", expected_return=cum_ret, confidence=confidence)
    elif cum_ret < -settings.min_expected_return_pct and confidence <= 0.45:
        # For spot, we do not short; treat as 'hold' or 'exit'
        return Signal(action="sell", expected_return=cum_ret, confidence=confidence)
    else:
        return Signal(action="hold", expected_return=cum_ret, confidence=confidence)
