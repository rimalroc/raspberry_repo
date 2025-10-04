from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

Base = declarative_base()


class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    info = Column(JSON, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    symbol = Column(String, nullable=False)
    horizon = Column(Integer, nullable=False)
    expected_return = Column(Float, nullable=False)
    signal = Column(String, nullable=False)
    returns = Column(JSON, nullable=False)


class Db:
    def __init__(self) -> None:
        settings = get_settings()
        db_url = f"sqlite:///{Path(settings.db_path)}"
        Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(db_url, echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def log_trade(self, symbol: str, side: str, quantity: float, price: float, info: Optional[Dict[str, Any]] = None) -> None:
        with self.Session() as s:
            s.add(Trade(symbol=symbol, side=side, quantity=quantity, price=price, info=info))
            s.commit()

    def log_prediction(self, symbol: str, horizon: int, expected_return: float, signal: str, returns: Any) -> None:
        with self.Session() as s:
            s.add(Prediction(symbol=symbol, horizon=horizon, expected_return=expected_return, signal=signal, returns=returns))
            s.commit()
