"""
Market Data Pipeline.

Fetches real market data via yfinance, computes historical volatility,
and provides synthetic data generation for testing.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MarketDataPipeline:
    """
    Fetches and processes market data for option pricing.
    Falls back to synthetic data if market data is unavailable.
    """

    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical stock data. Falls back to synthetic if yfinance fails."""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty:
                raise ValueError(f"No data for {ticker}")
            df.to_csv(self.data_dir / f"{ticker}_historical.csv")
            logger.info(f"Fetched {len(df)} rows for {ticker}")
            return df
        except Exception as e:
            logger.warning(f"Could not fetch {ticker}: {e}. Using synthetic data.")
            return self._generate_synthetic_stock(ticker)

    def _generate_synthetic_stock(self, ticker: str, days=252) -> pd.DataFrame:
        """Generate synthetic stock data using GBM for testing."""
        rng = np.random.default_rng(42)
        S0 = 150.0
        mu = 0.08
        sigma = 0.25
        dt = 1 / 252

        prices = [S0]
        for _ in range(days - 1):
            dS = prices[-1] * (mu * dt + sigma * np.sqrt(dt) * rng.standard_normal())
            prices.append(max(prices[-1] + dS, 1.0))

        dates = pd.bdate_range(end=datetime.now(), periods=days)
        volumes = rng.integers(1_000_000, 50_000_000, size=days)

        df = pd.DataFrame({
            "Open": prices,
            "High": [p * (1 + abs(rng.normal(0, 0.01))) for p in prices],
            "Low": [p * (1 - abs(rng.normal(0, 0.01))) for p in prices],
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

        df.to_csv(self.data_dir / f"{ticker}_synthetic.csv")
        return df

    def compute_historical_volatility(self, df: pd.DataFrame, windows=None) -> pd.DataFrame:
        """Compute realized volatility at multiple windows."""
        if windows is None:
            windows = [21, 63, 126, 252]  # 1M, 3M, 6M, 1Y

        log_returns = np.log(df["Close"] / df["Close"].shift(1)).dropna()

        result = {"log_returns": log_returns}
        for w in windows:
            result[f"rv_{w}d"] = log_returns.rolling(w).std() * np.sqrt(252)

        return pd.DataFrame(result)

    def get_current_spot(self, df: pd.DataFrame) -> float:
        return float(df["Close"].iloc[-1])

    def get_annualized_vol(self, df: pd.DataFrame, window: int = 63) -> float:
        log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
        return float(log_ret.rolling(window).std().iloc[-1] * np.sqrt(252))

    def generate_synthetic_smile_data(self, S, K_center, sigma_base=0.2, n_strikes=15):
        """
        Generate synthetic market prices with a realistic volatility smile.
        Uses a quadratic skew model: sigma(K) = a + b*(K/S - 1) + c*(K/S - 1)^2
        """
        from src.black_scholes import BlackScholesEngine

        strikes = np.linspace(K_center * 0.7, K_center * 1.3, n_strikes)
        market_data = []

        a, b, c = sigma_base, -0.1, 0.3  # Skew parameters
        for K in strikes:
            moneyness = K / S - 1
            local_vol = a + b * moneyness + c * moneyness**2
            local_vol = max(local_vol, 0.05)
            price = BlackScholesEngine.price(S, K, 0.5, 0.05, local_vol, 0, "call")
            market_data.append({"strike": K, "market_price": price})

        return market_data

    def summary_statistics(self, df: pd.DataFrame) -> dict:
        """Compute summary statistics for the stock data."""
        log_ret = np.log(df["Close"] / df["Close"].shift(1)).dropna()
        return {
            "current_price": float(df["Close"].iloc[-1]),
            "period_return": float((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1),
            "annualized_vol": float(log_ret.std() * np.sqrt(252)),
            "daily_mean_return": float(log_ret.mean()),
            "daily_std_return": float(log_ret.std()),
            "skewness": float(log_ret.skew()),
            "kurtosis": float(log_ret.kurtosis()),
            "min_price": float(df["Close"].min()),
            "max_price": float(df["Close"].max()),
            "trading_days": len(df),
        }
