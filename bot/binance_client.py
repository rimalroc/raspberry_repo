from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

from .config import get_settings
from .utils import ms_to_datetime

logger = logging.getLogger(__name__)


class BinanceClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = Client(settings.binance_api_key, settings.binance_api_secret)
        if settings.binance_testnet:
            # Spot testnet base URL
            self.client.API_URL = "https://testnet.binance.vision/api"
        self.recv_window = 60000

    def _safe_call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (BinanceAPIException, BinanceOrderException) as e:
            logger.error("Binance API error: %s", e)
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception("Unexpected error in Binance call: %s", e)
            raise

    def fetch_klines(self, symbol: str, interval: str, start_str: str, end_str: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        rows = self._safe_call(
            self.client.get_historical_klines,
            symbol,
            interval,
            start_str,
            end_str,
            limit=limit,
        )
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"]).astype(float)

        df = pd.DataFrame(rows, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])
        df["open_time"] = df["open_time"].astype("int64")
        df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df[["open", "high", "low", "close", "volume"]].sort_index()

    def get_price(self, symbol: str) -> float:
        data = self._safe_call(self.client.get_symbol_ticker, symbol=symbol)
        return float(data["price"])  # type: ignore[index]

    def get_account_balances(self) -> Dict[str, float]:
        info = self._safe_call(self.client.get_account, recvWindow=self.recv_window)
        balances = {}
        for b in info.get("balances", []):
            free = float(b.get("free", 0))
            locked = float(b.get("locked", 0))
            balances[b.get("asset")] = free + locked
        return balances

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        return self._safe_call(self.client.get_symbol_info, symbol)

    def _get_lot_step_and_notional(self, symbol: str):
        info = self.get_symbol_info(symbol)
        lot_step = 0.0
        min_notional = 0.0
        tick_size = 0.0
        if not info:
            return lot_step, min_notional, tick_size
        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                lot_step = float(f["stepSize"])
            if f["filterType"] == "MIN_NOTIONAL":
                min_notional = float(f.get("minNotional", 0.0))
            if f["filterType"] == "PRICE_FILTER":
                tick_size = float(f.get("tickSize", 0.0))
        return lot_step, min_notional, tick_size

    @staticmethod
    def _round_step(value: float, step: float) -> float:
        if step == 0:
            return value
        import math
        return math.floor(value / step) * step

    def market_buy(self, symbol: str, quote_amount: float) -> Optional[Dict[str, Any]]:
        price = self.get_price(symbol)
        lot_step, min_notional, _ = self._get_lot_step_and_notional(symbol)
        qty = quote_amount / price
        qty = self._round_step(qty, lot_step)
        if qty <= 0:
            logger.error("Computed quantity <= 0 for %s", symbol)
            return None
        if price * qty < min_notional:
            logger.error("Notional %f below min %f for %s", price * qty, min_notional, symbol)
            return None
        order = self._safe_call(
            self.client.order_market_buy,
            symbol=symbol,
            quantity=qty,
            recvWindow=self.recv_window,
        )
        return order

    def market_sell(self, symbol: str, quantity: float) -> Optional[Dict[str, Any]]:
        lot_step, _, _ = self._get_lot_step_and_notional(symbol)
        qty = self._round_step(quantity, lot_step)
        if qty <= 0:
            logger.error("Computed quantity <= 0 for %s", symbol)
            return None
        order = self._safe_call(
            self.client.order_market_sell,
            symbol=symbol,
            quantity=qty,
            recvWindow=self.recv_window,
        )
        return order

    def create_oco_sell(self, symbol: str, quantity: float, take_profit_price: float, stop_price: float, stop_limit_price: float) -> Optional[Dict[str, Any]]:
        lot_step, _, price_step = self._get_lot_step_and_notional(symbol)
        quantity = self._round_step(quantity, lot_step)
        take_profit_price = self._round_step(take_profit_price, price_step)
        stop_price = self._round_step(stop_price, price_step)
        stop_limit_price = self._round_step(stop_limit_price, price_step)
        try:
            oco = self._safe_call(
                self.client.create_oco_order,
                symbol=symbol,
                side=Client.SIDE_SELL,
                quantity=quantity,
                price=f"{take_profit_price:.8f}",
                stopPrice=f"{stop_price:.8f}",
                stopLimitPrice=f"{stop_limit_price:.8f}",
                stopLimitTimeInForce=Client.TIME_IN_FORCE_GTC,
                recvWindow=self.recv_window,
            )
            return oco
        except BinanceAPIException as e:
            logger.error("Failed to create OCO: %s", e)
            return None

