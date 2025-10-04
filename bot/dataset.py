from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset, DataLoader, random_split

from .config import get_settings
from .utils import ensure_dir


@dataclass
class PreparedData:
    X_scaled: np.ndarray
    Y: np.ndarray
    scaler: StandardScaler


def prepare_tensors(X: pd.DataFrame, Y: pd.DataFrame) -> PreparedData:
    settings = get_settings()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values.astype(np.float32))
    ensure_dir(settings.models_dir)
    joblib.dump(scaler, str(Path(settings.models_dir) / "scaler.pkl"))
    return PreparedData(X_scaled=X_scaled.astype(np.float32), Y=Y.values.astype(np.float32), scaler=scaler)


class TimeSeriesWindowDataset(Dataset):
    def __init__(self, X: np.ndarray, Y: np.ndarray, seq_len: int) -> None:
        assert len(X) == len(Y)
        self.X = X
        self.Y = Y
        self.seq_len = seq_len

    def __len__(self) -> int:
        return max(0, len(self.X) - self.seq_len)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x_window = self.X[idx : idx + self.seq_len]
        y_target = self.Y[idx + self.seq_len - 1]  # align on last observed time
        return torch.from_numpy(x_window), torch.from_numpy(y_target)


def build_dataloaders(X: pd.DataFrame, Y: pd.DataFrame):
    settings = get_settings()
    pdata = prepare_tensors(X, Y)
    dataset = TimeSeriesWindowDataset(pdata.X_scaled, pdata.Y, settings.sequence_length)
    n_valid = int(len(dataset) * settings.valid_split)
    n_train = len(dataset) - n_valid
    train_ds, valid_ds = random_split(dataset, [n_train, n_valid])
    train_loader = DataLoader(train_ds, batch_size=settings.batch_size, shuffle=True, drop_last=True)
    valid_loader = DataLoader(valid_ds, batch_size=settings.batch_size, shuffle=False, drop_last=False)
    return train_loader, valid_loader
