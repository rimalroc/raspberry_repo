from __future__ import annotations

import logging
from dataclasses import dataclass

from .binance_client import BinanceClient
from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    message: str
    entry_price: float | None = None
    quantity: float | None = None


def compute_position_size_usdt(balance_usdt: float) -> float:
    settings = get_settings()
    raw = min(balance_usdt * settings.max_position_fraction, settings.max_position_usdt)
    return max(0.0, raw)


def execute_signal(symbol: str, signal_action: str) -> ExecutionResult:
    settings = get_settings()
    client = BinanceClient()

    try:
        balances = client.get_account_balances()
        balance_usdt = float(balances.get(settings.quote_currency, 0.0))
    except Exception as e:  # noqa: BLE001
        return ExecutionResult(success=False, message=f"Failed to get balances: {e}")

    if signal_action == "buy":
        pos_usdt = compute_position_size_usdt(balance_usdt)
        if pos_usdt <= 10.0:
            return ExecutionResult(success=False, message="Insufficient USDT for position")
        try:
            order = client.market_buy(symbol, quote_amount=pos_usdt)
            if not order:
                return ExecutionResult(success=False, message="Market buy failed")
            entry_price = client.get_price(symbol)
            # Create OCO bracket
            tp = entry_price * (1.0 + settings.take_profit_pct)
            sl = entry_price * (1.0 - settings.stop_loss_pct)
            sl_limit = sl * 0.999
            client.create_oco_sell(symbol, quantity=float(order.get('executedQty', 0.0) or 0.0), take_profit_price=tp, stop_price=sl, stop_limit_price=sl_limit)
            return ExecutionResult(success=True, message="Buy executed", entry_price=entry_price, quantity=float(order.get('executedQty', 0.0) or 0.0))
        except Exception as e:  # noqa: BLE001
            logger.exception("Execution failed: %s", e)
            return ExecutionResult(success=False, message=f"Execution failed: {e}")

    elif signal_action == "sell":
        # For spot, sell any existing base asset
        base_asset = symbol.replace(settings.quote_currency, "")
        try:
            balances = client.get_account_balances()
            qty = float(balances.get(base_asset, 0.0))
            if qty <= 0.0:
                return ExecutionResult(success=False, message="No position to sell")
            order = client.market_sell(symbol, quantity=qty)
            if not order:
                return ExecutionResult(success=False, message="Market sell failed")
            price = client.get_price(symbol)
            return ExecutionResult(success=True, message="Sell executed", entry_price=price, quantity=qty)
        except Exception as e:  # noqa: BLE001
            logger.exception("Sell failed: %s", e)
            return ExecutionResult(success=False, message=f"Sell failed: {e}")

    return ExecutionResult(success=False, message="No action taken")
