from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from .config import get_settings
from .dataset import build_dataloaders
from .model import TransformerRegressor
from .utils import ensure_dir, set_random_seed

logger = logging.getLogger(__name__)


def train_model(X, Y) -> Path:
    settings = get_settings()
    set_random_seed(settings.random_seed)

    train_loader, valid_loader = build_dataloaders(X, Y)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TransformerRegressor(
        feature_dim=X.shape[1],
        horizon=Y.shape[1],
        d_model=settings.d_model,
        nhead=settings.nhead,
        num_layers=settings.num_layers,
        dim_feedforward=settings.dim_feedforward,
        dropout=settings.dropout,
    ).to(device)

    criterion = nn.MSELoss()
    optimizer = AdamW(model.parameters(), lr=settings.learning_rate, weight_decay=settings.weight_decay)

    best_val = float("inf")
    models_dir = Path(settings.models_dir)
    ensure_dir(models_dir)
    model_path = models_dir / "transformer_btc_next60.pt"

    for epoch in range(1, settings.num_epochs + 1):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:  # type: ignore
            xb = xb.float().to(device)
            yb = yb.float().to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item() * xb.size(0)
        train_loss /= max(1, len(train_loader.dataset))

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in valid_loader:  # type: ignore
                xb = xb.float().to(device)
                yb = yb.float().to(device)
                pred = model(xb)
                loss = criterion(pred, yb)
                val_loss += loss.item() * xb.size(0)
        val_loss /= max(1, len(valid_loader.dataset))

        logger.info("Epoch %d/%d - train %.6f - valid %.6f", epoch, settings.num_epochs, train_loss, val_loss)

        if val_loss < best_val:
            best_val = val_loss
            torch.save({"model_state": model.state_dict(), "val_loss": best_val}, model_path)
            logger.info("Saved best model to %s", model_path)

    return model_path
