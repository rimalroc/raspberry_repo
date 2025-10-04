from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from sqlalchemy import func, select

from .storage import Db, Trade, Prediction


def daily_summary(day: Optional[date] = None) -> str:
    console = Console(record=True)
    db = Db()
    if day is None:
        day = datetime.now(timezone.utc).date()
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    with db.Session() as s:
        trades = s.execute(select(Trade).where(Trade.timestamp >= start, Trade.timestamp < end)).scalars().all()
        preds = s.execute(select(Prediction).where(Prediction.timestamp >= start, Prediction.timestamp < end)).scalars().all()

    table = Table(title=f"Daily Summary {day}")
    table.add_column("Metric")
    table.add_column("Value")

    realized = 0.0
    # Naive PnL: sum of sell - buy notional; real PnL tracking would track positions
    buys = [t for t in trades if t.side.lower() == "buy"]
    sells = [t for t in trades if t.side.lower() == "sell"]
    buy_notional = sum(t.price * t.quantity for t in buys)
    sell_notional = sum(t.price * t.quantity for t in sells)
    realized = sell_notional - buy_notional

    table.add_row("Trades", str(len(trades)))
    table.add_row("Predictions", str(len(preds)))
    table.add_row("Realized PnL (approx USDT)", f"{realized:.2f}")

    console.print(table)
    return console.export_text()
