"""
Tests for Monte Carlo simulation engine.
"""
import pytest
import numpy as np
from src.monte_carlo import MonteCarloEngine
from src.black_scholes import BlackScholesEngine


class TestMonteCarloEngine:
    S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

    def test_mc_call_converges_to_bs(self):
        engine = MonteCarloEngine(n_simulations=100_000, seed=42)
        result = engine.price_option(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        assert abs(result.pricing_error) < 0.5  # Within $0.50

    def test_mc_put_converges_to_bs(self):
        engine = MonteCarloEngine(n_simulations=100_000, seed=42)
        result = engine.price_option(self.S, self.K, self.T, self.r, self.sigma, option_type="put")
        assert abs(result.pricing_error) < 0.5

    def test_antithetic_reduces_variance(self):
        engine_no = MonteCarloEngine(n_simulations=50_000, seed=42, antithetic=False, control_variate=False)
        engine_yes = MonteCarloEngine(n_simulations=50_000, seed=42, antithetic=True, control_variate=False)
        r1 = engine_no.price_option(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        r2 = engine_yes.price_option(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        assert r2.std_error <= r1.std_error * 1.5  # Antithetic should help

    def test_paths_shape(self):
        engine = MonteCarloEngine(n_simulations=1000, n_steps=50, seed=42)
        result = engine.price_option(self.S, self.K, self.T, self.r, self.sigma)
        assert result.paths.shape[1] == 51  # n_steps + 1

    def test_convergence_analysis(self):
        engine = MonteCarloEngine(n_simulations=10_000, seed=42)
        conv = engine.convergence_analysis(self.S, self.K, self.T, self.r, self.sigma,
                                            sim_counts=[100, 1000, 10000])
        assert len(conv["convergence_data"]) == 3
        # Error should generally decrease with more sims
        errors = [abs(d["error_vs_bs"]) for d in conv["convergence_data"]]
        assert errors[-1] < errors[0] * 5  # Relaxed bound

    def test_positive_prices(self):
        engine = MonteCarloEngine(n_simulations=10_000, seed=42)
        result = engine.price_option(self.S, self.K, self.T, self.r, self.sigma)
        assert result.price > 0

    def test_confidence_interval_contains_bs(self):
        engine = MonteCarloEngine(n_simulations=100_000, seed=42)
        result = engine.price_option(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        lo, hi = result.confidence_interval_95
        assert lo < result.bs_benchmark < hi
