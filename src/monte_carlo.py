"""
Monte Carlo Option Pricing Engine.

Implements Geometric Brownian Motion simulation with variance reduction
techniques (antithetic variates, control variates) for European option pricing.
"""
import numpy as np
from dataclasses import dataclass
from typing import Literal

from src.black_scholes import BlackScholesEngine

OptionType = Literal["call", "put"]


@dataclass
class MCResult:
    """Container for Monte Carlo simulation results."""
    price: float
    std_error: float
    confidence_interval_95: tuple
    n_simulations: int
    paths: np.ndarray          # Sample of simulated paths for plotting
    terminal_prices: np.ndarray
    bs_benchmark: float
    pricing_error: float       # MC price - BS price


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for European option pricing.

    Features:
    - Geometric Brownian Motion path simulation
    - Antithetic variates for variance reduction
    - Control variate using delta hedging
    - Convergence analysis
    """

    def __init__(self, n_simulations=100_000, n_steps=252, seed=42,
                 antithetic=True, control_variate=True):
        self.n_simulations = n_simulations
        self.n_steps = n_steps
        self.seed = seed
        self.antithetic = antithetic
        self.control_variate = control_variate

    def simulate_paths(self, S, T, r, sigma, q=0.0) -> np.ndarray:
        """Simulate GBM price paths. Returns array of shape (n_sims, n_steps+1)."""
        rng = np.random.default_rng(self.seed)
        dt = T / self.n_steps
        n_sims = self.n_simulations // 2 if self.antithetic else self.n_simulations

        Z = rng.standard_normal((n_sims, self.n_steps))

        if self.antithetic:
            Z = np.vstack([Z, -Z])

        drift = (r - q - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt)

        log_returns = drift + diffusion * Z
        log_paths = np.cumsum(log_returns, axis=1)
        log_paths = np.hstack([np.zeros((log_paths.shape[0], 1)), log_paths])
        paths = S * np.exp(log_paths)

        return paths

    def price_option(self, S, K, T, r, sigma, q=0.0,
                     option_type: OptionType = "call") -> MCResult:
        """Price a European option via Monte Carlo simulation."""
        paths = self.simulate_paths(S, T, r, sigma, q)
        terminal = paths[:, -1]

        if option_type == "call":
            payoffs = np.maximum(terminal - K, 0)
        else:
            payoffs = np.maximum(K - terminal, 0)

        discount = np.exp(-r * T)

        if self.control_variate:
            # Use the underlying asset as control variate
            # E[S_T] = S * exp((r-q)*T) under risk-neutral measure
            expected_terminal = S * np.exp((r - q) * T)
            cov_matrix = np.cov(payoffs, terminal)
            if cov_matrix[1, 1] > 0:
                beta = cov_matrix[0, 1] / cov_matrix[1, 1]
                payoffs_adjusted = payoffs - beta * (terminal - expected_terminal)
            else:
                payoffs_adjusted = payoffs
        else:
            payoffs_adjusted = payoffs

        discounted = discount * payoffs_adjusted
        price = np.mean(discounted)
        std_error = np.std(discounted) / np.sqrt(len(discounted))

        bs_price = BlackScholesEngine.price(S, K, T, r, sigma, q, option_type)

        return MCResult(
            price=price,
            std_error=std_error,
            confidence_interval_95=(price - 1.96 * std_error, price + 1.96 * std_error),
            n_simulations=len(terminal),
            paths=paths[:200],  # Store subset for plotting
            terminal_prices=terminal,
            bs_benchmark=bs_price,
            pricing_error=price - bs_price,
        )

    def convergence_analysis(self, S, K, T, r, sigma, q=0.0,
                             option_type: OptionType = "call",
                             sim_counts=None) -> dict:
        """Analyze how MC price converges as simulation count increases."""
        if sim_counts is None:
            sim_counts = [100, 500, 1000, 5000, 10000, 50000, 100000]

        results = []
        original_n = self.n_simulations
        for n in sim_counts:
            self.n_simulations = n
            result = self.price_option(S, K, T, r, sigma, q, option_type)
            results.append({
                "n_simulations": n,
                "price": result.price,
                "std_error": result.std_error,
                "error_vs_bs": result.pricing_error,
            })
        self.n_simulations = original_n

        return {
            "convergence_data": results,
            "bs_benchmark": BlackScholesEngine.price(S, K, T, r, sigma, q, option_type),
        }
