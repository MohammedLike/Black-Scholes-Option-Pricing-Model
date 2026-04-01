"""
Tests for implied volatility solver.
"""
import pytest
import numpy as np
from src.implied_volatility import ImpliedVolatilitySolver
from src.black_scholes import BlackScholesEngine


class TestImpliedVolSolver:
    S, K, T, r = 100, 100, 1.0, 0.05

    def test_recovers_known_vol(self):
        true_vol = 0.25
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, true_vol, option_type="call")
        result = ImpliedVolatilitySolver.solve(price, self.S, self.K, self.T, self.r, option_type="call")
        assert result["converged"]
        assert abs(result["implied_volatility"] - true_vol) < 1e-6

    def test_recovers_low_vol(self):
        true_vol = 0.05
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, true_vol, option_type="call")
        result = ImpliedVolatilitySolver.solve(price, self.S, self.K, self.T, self.r, option_type="call")
        assert result["converged"]
        assert abs(result["implied_volatility"] - true_vol) < 1e-4

    def test_recovers_high_vol(self):
        true_vol = 0.80
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, true_vol, option_type="call")
        result = ImpliedVolatilitySolver.solve(price, self.S, self.K, self.T, self.r, option_type="call")
        assert result["converged"]
        assert abs(result["implied_volatility"] - true_vol) < 1e-4

    def test_put_iv(self):
        true_vol = 0.30
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, true_vol, option_type="put")
        result = ImpliedVolatilitySolver.solve(price, self.S, self.K, self.T, self.r, option_type="put")
        assert result["converged"]
        assert abs(result["implied_volatility"] - true_vol) < 1e-5

    def test_otm_option(self):
        true_vol = 0.20
        price = BlackScholesEngine.price(100, 120, self.T, self.r, true_vol, option_type="call")
        result = ImpliedVolatilitySolver.solve(price, 100, 120, self.T, self.r, option_type="call")
        assert result["converged"]
        assert abs(result["implied_volatility"] - true_vol) < 1e-4

    def test_volatility_smile(self):
        market_data = []
        for K in [80, 90, 100, 110, 120]:
            # Simulate a smile with vol depending on moneyness
            vol = 0.2 + 0.1 * ((K / 100 - 1) ** 2)
            price = BlackScholesEngine.price(100, K, 0.5, 0.05, vol, option_type="call")
            market_data.append({"strike": K, "market_price": price})

        results = ImpliedVolatilitySolver.volatility_smile(100, 0.5, 0.05, 0.0, market_data)
        assert len(results) == 5
        assert all(r["converged"] for r in results)
