from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
import torch

from .config import get_settings
from .model import TransformerRegressor
from .utils import ensure_dir

logger = logging.getLogger(__name__)


def load_model(feature_dim: int, horizon: int) -> TransformerRegressor:
    settings = get_settings()
    models_dir = Path(settings.models_dir)
    ckpt_path = models_dir / "transformer_btc_next60.pt"
    model = TransformerRegressor(
        feature_dim=feature_dim,
        horizon=horizon,
        d_model=settings.d_model,
        nhead=settings.nhead,
        num_layers=settings.num_layers,
        dim_feedforward=settings.dim_feedforward,
        dropout=settings.dropout,
    )
    if ckpt_path.exists():
        state = torch.load(ckpt_path, map_location="cpu")
        model.load_state_dict(state["model_state"])  # type: ignore
        logger.info("Loaded model from %s", ckpt_path)
    else:
        logger.warning("Model checkpoint not found at %s", ckpt_path)
    model.eval()
    return model


def predict_next_hour(X: pd.DataFrame) -> Dict[str, np.ndarray]:
    settings = get_settings()
    scaler = joblib.load(str(Path(settings.models_dir) / "scaler.pkl"))
    X_scaled = scaler.transform(X.values.astype(np.float32))

    model = load_model(feature_dim=X.shape[1], horizon=settings.forecast_horizon)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Take last sequence
    seq_len = settings.sequence_length
    window = X_scaled[-seq_len:]
    x_tensor = torch.from_numpy(window).unsqueeze(0).float().to(device)

    with torch.no_grad():
        y_ret = model(x_tensor).cpu().numpy()[0]

    # Convert cumulative log-returns to price path given last close
    # Note: caller must provide last close
    return {"log_returns": y_ret}
