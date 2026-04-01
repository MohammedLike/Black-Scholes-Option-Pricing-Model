"""
Implied Volatility Solver.

Implements Newton-Raphson method with Brenner-Subrahmanyam initial guess
for robust IV extraction from market prices.
"""
import numpy as np
from typing import Literal

from src.black_scholes import BlackScholesEngine

OptionType = Literal["call", "put"]


class ImpliedVolatilitySolver:
    """
    Extracts implied volatility from observed market prices using
    Newton-Raphson iteration with analytical vega.
    """

    MAX_ITERATIONS = 100
    TOLERANCE = 1e-8
    MIN_VOL = 1e-6
    MAX_VOL = 5.0

    @classmethod
    def _initial_guess(cls, S, K, T, r, market_price, option_type):
        """Brenner-Subrahmanyam (1988) approximation for ATM options."""
        # sigma_approx = sqrt(2*pi/T) * C/S
        approx = np.sqrt(2 * np.pi / T) * market_price / S
        return np.clip(approx, 0.01, 2.0)

    @classmethod
    def solve(cls, market_price: float, S: float, K: float, T: float,
              r: float, q: float = 0.0, option_type: OptionType = "call") -> dict:
        """
        Find implied volatility using Newton-Raphson.

        Returns dict with IV, convergence info, and iteration history.
        """
        sigma = cls._initial_guess(S, K, T, r, market_price, option_type)
        history = []

        for i in range(cls.MAX_ITERATIONS):
            bs_price = BlackScholesEngine.price(S, K, T, r, sigma, q, option_type)
            vega_raw = BlackScholesEngine.vega(S, K, T, r, sigma, q) * 100  # Undo /100 scaling
            diff = bs_price - market_price

            history.append({
                "iteration": i,
                "sigma": sigma,
                "bs_price": bs_price,
                "diff": diff,
                "vega": vega_raw,
            })

            if abs(diff) < cls.TOLERANCE:
                return {
                    "implied_volatility": sigma,
                    "converged": True,
                    "iterations": i + 1,
                    "final_error": diff,
                    "history": history,
                }

            if abs(vega_raw) < 1e-12:
                # Vega too small — switch to bisection fallback
                return cls._bisection_fallback(market_price, S, K, T, r, q, option_type)

            sigma -= diff / vega_raw
            sigma = np.clip(sigma, cls.MIN_VOL, cls.MAX_VOL)

        return {
            "implied_volatility": sigma,
            "converged": False,
            "iterations": cls.MAX_ITERATIONS,
            "final_error": diff,
            "history": history,
        }

    @classmethod
    def _bisection_fallback(cls, market_price, S, K, T, r, q, option_type):
        """Bisection method as fallback when Newton-Raphson fails."""
        low, high = cls.MIN_VOL, cls.MAX_VOL
        for i in range(200):
            mid = (low + high) / 2
            bs_price = BlackScholesEngine.price(S, K, T, r, mid, q, option_type)
            if bs_price > market_price:
                high = mid
            else:
                low = mid
            if high - low < cls.TOLERANCE:
                break
        return {
            "implied_volatility": mid,
            "converged": True,
            "iterations": i + 1,
            "final_error": bs_price - market_price,
            "method": "bisection",
            "history": [],
        }

    @classmethod
    def volatility_smile(cls, S, T, r, q, market_data: list,
                         option_type: OptionType = "call") -> list:
        """
        Compute IV across multiple strikes to construct volatility smile.

        market_data: list of dicts with keys 'strike' and 'market_price'
        """
        results = []
        for point in market_data:
            iv_result = cls.solve(
                point["market_price"], S, point["strike"], T, r, q, option_type
            )
            results.append({
                "strike": point["strike"],
                "market_price": point["market_price"],
                "implied_vol": iv_result["implied_volatility"],
                "converged": iv_result["converged"],
                "moneyness": S / point["strike"],
            })
        return results
