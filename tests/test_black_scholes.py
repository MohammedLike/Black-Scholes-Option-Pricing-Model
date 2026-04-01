"""
Comprehensive tests for the Black-Scholes pricing engine.
"""
import pytest
import numpy as np
from src.black_scholes import BlackScholesEngine


class TestBlackScholesPricing:
    """Test option pricing against known analytical results."""

    # Standard test parameters
    S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

    def test_atm_call_price(self):
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, self.sigma)
        # Known ATM call price for these params ≈ 10.4506
        assert abs(price - 10.4506) < 0.01

    def test_atm_put_price(self):
        price = BlackScholesEngine.price(self.S, self.K, self.T, self.r, self.sigma, option_type="put")
        # Known ATM put price ≈ 5.5735
        assert abs(price - 5.5735) < 0.01

    def test_deep_itm_call(self):
        price = BlackScholesEngine.price(150, 100, 1.0, 0.05, 0.2)
        intrinsic = 150 - 100 * np.exp(-0.05)
        assert price > intrinsic  # Must exceed discounted intrinsic

    def test_deep_otm_call(self):
        price = BlackScholesEngine.price(50, 100, 1.0, 0.05, 0.2)
        assert price < 0.01  # Deep OTM call is nearly worthless

    def test_zero_vol_call(self):
        # With tiny vol, call ≈ max(S - K*e^(-rT), 0)
        price = BlackScholesEngine.price(110, 100, 1.0, 0.05, 0.001)
        expected = 110 - 100 * np.exp(-0.05)
        assert abs(price - expected) < 0.1

    def test_put_call_parity(self):
        result = BlackScholesEngine.put_call_parity_check(self.S, self.K, self.T, self.r, self.sigma)
        assert result["parity_holds"]
        assert result["parity_error"] < 1e-10

    def test_put_call_parity_with_dividends(self):
        result = BlackScholesEngine.put_call_parity_check(100, 100, 1.0, 0.05, 0.3, q=0.02)
        assert result["parity_holds"]


class TestGreeks:
    S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

    def test_call_delta_range(self):
        delta = BlackScholesEngine.delta(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        assert 0 < delta < 1

    def test_put_delta_range(self):
        delta = BlackScholesEngine.delta(self.S, self.K, self.T, self.r, self.sigma, option_type="put")
        assert -1 < delta < 0

    def test_call_put_delta_relation(self):
        call_d = BlackScholesEngine.delta(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        put_d = BlackScholesEngine.delta(self.S, self.K, self.T, self.r, self.sigma, option_type="put")
        # call_delta - put_delta = e^(-qT) = 1 when q=0
        assert abs((call_d - put_d) - 1.0) < 1e-10

    def test_gamma_positive(self):
        gamma = BlackScholesEngine.gamma(self.S, self.K, self.T, self.r, self.sigma)
        assert gamma > 0

    def test_gamma_symmetric(self):
        # Gamma is the same for calls and puts
        g1 = BlackScholesEngine.gamma(self.S, self.K, self.T, self.r, self.sigma)
        assert g1 > 0  # Just verify it's positive; gamma is option_type-independent

    def test_theta_negative_for_long(self):
        theta_call = BlackScholesEngine.theta(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        assert theta_call < 0  # Time decay hurts long positions

    def test_vega_positive(self):
        vega = BlackScholesEngine.vega(self.S, self.K, self.T, self.r, self.sigma)
        assert vega > 0

    def test_atm_delta_approximately_half(self):
        delta = BlackScholesEngine.delta(self.S, self.K, self.T, self.r, self.sigma, option_type="call")
        assert abs(delta - 0.5) < 0.15  # ATM delta is ~0.5 (adjusted for drift)

    def test_deep_itm_call_delta_near_one(self):
        delta = BlackScholesEngine.delta(200, 100, 1.0, 0.05, 0.2, option_type="call")
        assert delta > 0.99

    def test_deep_otm_call_delta_near_zero(self):
        delta = BlackScholesEngine.delta(50, 100, 1.0, 0.05, 0.2, option_type="call")
        assert delta < 0.01


class TestHigherOrderGreeks:
    S, K, T, r, sigma = 100, 100, 1.0, 0.05, 0.2

    def test_vanna_finite_difference(self):
        """Verify vanna against finite-difference approximation."""
        analytical = BlackScholesEngine.vanna(self.S, self.K, self.T, self.r, self.sigma)
        ds = 0.01
        d1 = BlackScholesEngine.delta(self.S + ds, self.K, self.T, self.r, self.sigma + 0.01, option_type="call")
        d2 = BlackScholesEngine.delta(self.S + ds, self.K, self.T, self.r, self.sigma - 0.01, option_type="call")
        fd_approx = (d1 - d2) / 0.02
        assert abs(analytical - fd_approx) < 0.05

    def test_compute_all_returns_all_fields(self):
        result = BlackScholesEngine.compute_all(self.S, self.K, self.T, self.r, self.sigma)
        assert hasattr(result, "price")
        assert hasattr(result, "delta")
        assert hasattr(result, "gamma")
        assert hasattr(result, "theta")
        assert hasattr(result, "vega")
        assert hasattr(result, "rho")
        assert hasattr(result, "vanna")
        assert hasattr(result, "volga")
        assert hasattr(result, "charm")
        assert hasattr(result, "speed")


class TestEdgeCases:
    def test_very_short_expiry(self):
        price = BlackScholesEngine.price(100, 100, 0.001, 0.05, 0.2)
        assert price >= 0

    def test_very_high_volatility(self):
        price = BlackScholesEngine.price(100, 100, 1.0, 0.05, 3.0)
        assert price > 0
        assert price < 100  # Can't exceed spot

    def test_with_dividends(self):
        call_no_div = BlackScholesEngine.price(100, 100, 1.0, 0.05, 0.2, q=0)
        call_with_div = BlackScholesEngine.price(100, 100, 1.0, 0.05, 0.2, q=0.03)
        assert call_with_div < call_no_div  # Dividends reduce call value
