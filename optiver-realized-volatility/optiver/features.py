"""Target-free, within-window microstructure measurements.

No tickers, cross-window ordering, or target values are inferred here.
"""
import numpy as np
import pandas as pd

BOOK = ['time_id', 'seconds_in_bucket', 'bid_price1', 'ask_price1',
        'bid_price2', 'ask_price2', 'bid_size1', 'ask_size1', 'bid_size2', 'ask_size2']
TRADE = ['time_id', 'seconds_in_bucket', 'price', 'size', 'order_count']


def _validate(frame, columns, prices, quantities):
    if not set(columns).issubset(frame):
        raise ValueError(f'Missing columns: {sorted(set(columns) - set(frame))}')
    data = frame[columns].copy()
    for col in columns:
        data[col] = pd.to_numeric(data[col], errors='raise')
    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError('Non-finite inputs: audit raw observations before proceeding')
    for col in ['time_id', 'seconds_in_bucket']:
        if (data[col] != np.floor(data[col])).any() or (data[col] < 0).any():
            raise ValueError('IDs and within-window seconds must be nonnegative integers')
    if (data.seconds_in_bucket >= 600).any():
        raise ValueError('Expected within-window seconds in [0,599]')
    if (data[prices] <= 0).any().any() or (data[quantities] < 0).any().any():
        raise ValueError('Prices must be positive; quantities must be nonnegative')
    if data.duplicated(['time_id', 'seconds_in_bucket']).any():
        raise ValueError('Duplicate time/second rows require explicit audit, not silent aggregation')
    return data.sort_values(['time_id', 'seconds_in_bucket'])


def realized_volatility(prices):
    """sqrt(sum(log(P_t/P_(t-1))**2)); undefined for fewer than two prices."""
    values = np.asarray(prices, dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('RV requires finite positive prices')
    return float(np.sqrt(np.square(np.diff(np.log(values))).sum())) if len(values) >= 2 else np.nan


def _weighted_mean(values, durations):
    good = np.isfinite(values) & (durations > 0)
    return float(np.average(values[good], weights=durations[good])) if good.any() else np.nan


def book_features(frame, stock_id):
    """One row per stock/window. Time weights assume quotes persist until next update.

    The last quote persists to second 600. No quote is backfilled before the first
    observation. Event-weighted RV remains sensitive to update frequency.
    """
    data = _validate(frame, BOOK, BOOK[2:6], BOOK[6:])
    if ((data.bid_price1 > data.ask_price1) | (data.bid_price2 > data.bid_price1) |
            (data.ask_price2 < data.ask_price1)).any():
        raise ValueError('Crossed or inconsistent book levels require a data-quality decision')
    records = []
    for time_id, group in data.groupby('time_id', sort=True):
        seconds = group.seconds_in_bucket.to_numpy(dtype=float)
        durations = np.diff(np.r_[seconds, 600.])
        mid = (group.bid_price1 + group.ask_price1) / 2
        depth1 = group.bid_size1 + group.ask_size1
        depth2 = depth1 + group.bid_size2 + group.ask_size2
        wap = ((group.bid_price1 * group.ask_size1 + group.ask_price1 * group.bid_size1)
               / depth1.replace(0, np.nan))
        imbalance = (group.bid_size1 - group.ask_size1) / depth1.replace(0, np.nan)
        relative_spread = (group.ask_price1 - group.bid_price1) / mid
        # Never bridge a zero-depth WAP gap; it would invent an unobserved path.
        wap_values = wap.to_numpy()
        valid = np.isfinite(wap_values)
        log_wap = np.full(len(wap_values), np.nan)
        log_wap[valid] = np.log(wap_values[valid])
        changes = np.diff(log_wap)
        finite_changes = changes[np.isfinite(changes)]
        wap_rv = float(np.sqrt(np.square(finite_changes).sum())) if len(finite_changes) else np.nan
        record = dict(stock_id=int(stock_id), time_id=int(time_id),
                      book_updates=len(group), observed_seconds=600-float(seconds[0]),
                      mean_gap_seconds=float(np.diff(seconds).mean()) if len(group)>1 else np.nan,
                      spread_mean=float(relative_spread.mean()),
                      spread_time_mean=_weighted_mean(relative_spread.to_numpy(), durations),
                      spread_p90=float(relative_spread.quantile(.9)),
                      depth_mean=float(depth2.mean()),
                      depth_time_mean=_weighted_mean(depth2.to_numpy(), durations),
                      abs_imbalance_mean=float(imbalance.abs().mean()),
                      signed_imbalance_mean=float(imbalance.mean()),
                      zero_depth_rows=int((depth1 == 0).sum()),
                      wap_rv=wap_rv, mid_rv=realized_volatility(mid),
                      max_abs_mid_log_return=float(np.abs(np.diff(np.log(mid))).max()) if len(group)>1 else np.nan)
        # Late-window RV uses returns whose two endpoints are both in the last 120s.
        record['late_mid_rv'] = realized_volatility(mid[group.seconds_in_bucket >= 480])
        records.append(record)
    return pd.DataFrame(records)


def trade_features(frame):
    data = _validate(frame, TRADE, ['price'], ['size', 'order_count'])
    if ((data.order_count == 0) & (data['size'] > 0)).any():
        raise ValueError('Positive share volume with zero orders requires audit')
    records = []
    for time_id, group in data.groupby('time_id', sort=True):
        total_orders = float(group.order_count.sum())
        records.append(dict(time_id=int(time_id), trade_seconds=len(group),
                            trade_volume=float(group['size'].sum()), order_count=total_orders,
                            mean_order_size=float(group['size'].sum()/total_orders) if total_orders else np.nan,
                            trade_rv=realized_volatility(group.price)))
    return pd.DataFrame(records)


def features_for_stock(book, trades, stock_id):
    features = book_features(book, stock_id)
    if features.empty:
        raise ValueError('No order-book observations in the requested discovery windows')
    trade = trade_features(trades)
    if trade.empty:
        trade = pd.DataFrame(columns=['time_id', 'trade_seconds', 'trade_volume',
                                     'order_count', 'mean_order_size', 'trade_rv'])
    features = features.merge(trade, on='time_id', how='left', validate='one_to_one')
    for col in ['trade_seconds', 'trade_volume', 'order_count']:
        features[col] = features[col].fillna(0)
    features['no_recorded_trades'] = (features.trade_seconds == 0).astype(int)
    return features
