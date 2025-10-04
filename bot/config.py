from __future__ import annotations

from functools import lru_cache
from pydantic import BaseSettings, Field
from typing import List


class Settings(BaseSettings):
    # Binance API
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", env="BINANCE_API_SECRET")
    binance_testnet: bool = Field(default=True, env="BINANCE_TESTNET")

    # Symbols and intervals
    symbols: List[str] = Field(
        default_factory=lambda: ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
    )
    base_symbol: str = Field(default="BTCUSDT")
    intervals: List[str] = Field(default_factory=lambda: ["1m", "5m", "1h", "1d"])

    # Data and model
    data_dir: str = Field(default="data")
    models_dir: str = Field(default="models")
    logs_dir: str = Field(default="logs")
    db_path: str = Field(default="bot/trading.db")

    random_seed: int = 42

    # Modeling
    forecast_horizon: int = 60
    sequence_length: int = 360  # 6 hours of 1m bars

    # Training
    batch_size: int = 64
    num_epochs: int = 20
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    valid_split: float = 0.2

    # Transformer architecture
    d_model: int = 128
    nhead: int = 8
    num_layers: int = 4
    dim_feedforward: int = 256
    dropout: float = 0.1

    # Trading / risk
    quote_currency: str = "USDT"
    max_position_usdt: float = 1000.0
    max_position_fraction: float = 0.2
    stop_loss_pct: float = 0.01
    take_profit_pct: float = 0.02
    min_expected_return_pct: float = 0.002
    min_risk_reward: float = 1.5
    slippage_pct: float = 0.0005
    enable_live_trading: bool = False

    # Scheduler
    run_interval_seconds: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore
