from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import typer

from .config import get_settings
from .data import get_all_data, fetch_and_cache
from .features import engineer_features
from .inference import predict_next_hour
from .report import daily_summary
from .signals import generate_signal
from .execution import execute_signal
from .storage import Db
from .utils import setup_logging

app = typer.Typer(add_completion=False)


@app.command()
def fetch(days: int = typer.Option(90, help="Number of days to fetch")):
    setup_logging()
    get_all_data(days=days)


@app.command()
def train(days: int = typer.Option(120, help="Days of history to train on")):
    setup_logging()
    from .train import train_model

    data = get_all_data(days=days)
    X, Y = engineer_features(data)
    train_model(X, Y)


@app.command()
def once(live: bool = typer.Option(False, help="Execute trades if true")):
    setup_logging()
    settings = get_settings()

    # Refresh latest data (short lookback for speed)
    for sym in settings.symbols:
        for itv in settings.intervals:
            fetch_and_cache(sym, itv, days=5)

    from .data import load_cached

    data = {(sym, itv): load_cached(sym, itv) for sym in settings.symbols for itv in settings.intervals}
    X, Y = engineer_features(data)

    preds = predict_next_hour(X)
    log_returns = preds["log_returns"]

    # Build signal
    sig = generate_signal(log_returns)

    # Save prediction
    db = Db()
    db.log_prediction(settings.base_symbol, settings.forecast_horizon, sig.expected_return, sig.action, returns=log_returns.tolist())

    typer.echo(f"Signal: {sig.action} (ER={sig.expected_return:.4%}, conf={sig.confidence:.2f})")

    if live and settings.enable_live_trading:
        res = execute_signal(settings.base_symbol, sig.action)
        status = "OK" if res.success else "FAIL"
        typer.echo(f"Execution: {status} - {res.message}")
    else:
        typer.echo("Live trading disabled or not requested -- running in paper mode.")


@app.command()
def report():
    setup_logging()
    text = daily_summary()
    print(text)


if __name__ == "__main__":
    app()
