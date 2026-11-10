"""Competition metric; never silently clip invalid targets."""
import numpy as np


def rmspe(actual, predicted):
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if y.ndim != 1 or y.shape != p.shape or not y.size:
        raise ValueError('Expected equal nonempty one-dimensional arrays')
    if not np.isfinite(y).all() or not np.isfinite(p).all() or (y <= 0).any():
        raise ValueError('RMSPE requires positive finite targets and finite predictions')
    if (p < 0).any():
        raise ValueError('Volatility predictions must be nonnegative')
    return float(np.sqrt(np.mean(np.square((y-p)/y))))
