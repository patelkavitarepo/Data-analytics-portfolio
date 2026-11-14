"""Close-to-close price analytics on the shared observed trading dates."""
import numpy as np
import pandas as pd


def analyze(rows, window=21):
    prices = rows.pivot(index='date', columns='symbol', values='close').sort_index().dropna()
    if len(prices) < 3:
        raise ValueError('Choose a period with at least three shared trading observations')
    returns = prices.pct_change(fill_method=None).iloc[1:]
    growth = prices.div(prices.iloc[0])
    drawdown = prices.div(prices.cummax()).sub(1)
    years = (prices.index[-1] - prices.index[0]).days / 365.25
    summary = pd.DataFrame({
        'Price return': growth.iloc[-1] - 1,
        'Annualized return': growth.iloc[-1] ** (1 / years) - 1,
        'Annualized volatility': returns.std(ddof=1) * np.sqrt(252),
        'Max drawdown': drawdown.min(),
        'Observations': len(prices),
    })
    return dict(prices=prices, returns=returns, growth=growth, drawdown=drawdown,
                rolling_volatility=returns.rolling(window).std(ddof=1) * np.sqrt(252),
                correlation=returns.corr(), summary=summary)
