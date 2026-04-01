"""
Configuration module for the Option Pricing Model pipeline.
"""
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np


@dataclass
class ModelConfig:
    """Parameters for a single option contract."""
    S: float = 100.0        # Spot price
    K: float = 100.0        # Strike price
    T: float = 1.0          # Time to expiration (years)
    r: float = 0.05         # Risk-free rate
    sigma: float = 0.2      # Volatility
    q: float = 0.0          # Continuous dividend yield

    def validate(self):
        assert self.S > 0, "Spot price must be positive"
        assert self.K > 0, "Strike price must be positive"
        assert self.T > 0, "Time to expiration must be positive"
        assert self.sigma > 0, "Volatility must be positive"
        assert 0 <= self.r < 1, "Risk-free rate must be in [0, 1)"


@dataclass
class MonteCarloConfig:
    """Parameters for Monte Carlo simulation."""
    n_simulations: int = 100_000
    n_steps: int = 252          # Trading days in a year
    seed: int = 42
    antithetic: bool = True     # Variance reduction
    control_variate: bool = True


@dataclass
class SensitivityConfig:
    """Ranges for sensitivity analysis."""
    spot_range: np.ndarray = field(default_factory=lambda: np.linspace(50, 150, 100))
    vol_range: np.ndarray = field(default_factory=lambda: np.linspace(0.05, 0.80, 100))
    time_range: np.ndarray = field(default_factory=lambda: np.linspace(0.01, 2.0, 100))
    rate_range: np.ndarray = field(default_factory=lambda: np.linspace(0.0, 0.15, 100))
    strike_range: np.ndarray = field(default_factory=lambda: np.linspace(70, 130, 100))


@dataclass
class PipelineConfig:
    """Top-level pipeline configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    monte_carlo: MonteCarloConfig = field(default_factory=MonteCarloConfig)
    sensitivity: SensitivityConfig = field(default_factory=SensitivityConfig)
    output_dir: Path = Path("outputs")
    plot_dir: Path = Path("outputs/plots")
    report_dir: Path = Path("outputs/reports")
    ticker: str = "AAPL"       # Default ticker for market data

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plot_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
