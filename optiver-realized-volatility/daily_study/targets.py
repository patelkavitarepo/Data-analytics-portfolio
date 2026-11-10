"""Explicit exchange-session returns, provisional targets, and purged date splits."""
import numpy as np
import pandas as pd


def session_returns(close, blocked_returns=None):
    """Input is a session-reindexed date x ticker matrix, never a compressed row list."""
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError('Expected unique sorted session index')
    if close.columns.duplicated().any():
        raise ValueError('Duplicate tickers')
    prices = close.where(np.isfinite(close) & (close > 0))
    returns = np.log(prices).diff()
    if blocked_returns is not None:
        if not blocked_returns.index.equals(close.index) or not blocked_returns.columns.equals(close.columns):
            raise ValueError('Return exclusions must exactly match the session panel')
        returns = returns.mask(blocked_returns)
    return returns


def forward_rv(returns, horizon=5):
    """At origin t use returns t+1,...,t+h; any missing return invalidates target.

    No centering, division by horizon, annualization, or imputation is performed.
    These are offline audit values, never feature inputs.
    """
    if type(horizon) is not int or horizon < 1:
        raise ValueError('Positive integer horizon required')
    total = returns.pow(2).shift(-1)
    for step in range(2, horizon+1):
        total = total + returns.pow(2).shift(-step)
    return np.sqrt(total)


def backward_rv(returns, lookback=20):
    """Optional audit sensitivity: 20 returns through t, not an approved feature set."""
    return returns.pow(2).rolling(lookback, min_periods=lookback).sum().pow(.5)


def purged_training_mask(origins, target_ends, validation_start):
    """Strict whole-date policy: fit only labels ending before first validation origin."""
    origins, ends = pd.to_datetime(origins), pd.to_datetime(target_ends)
    start = pd.Timestamp(validation_start)
    return (origins < start) & (ends < start) & ~pd.isna(ends)
