"""
Black-Scholes Option Pricing Engine.

Implements the Black-Scholes-Merton (1973) closed-form solution for European
options with continuous dividend yield, plus all first- and second-order Greeks.
"""
import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
from typing import Literal

OptionType = Literal["call", "put"]


@dataclass
class BSResult:
    """Container for Black-Scholes pricing results."""
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    vanna: float        # d(delta)/d(sigma)
    volga: float        # d(vega)/d(sigma), aka vomma
    charm: float        # d(delta)/d(t)
    speed: float        # d(gamma)/d(S)
    option_type: str
    d1: float
    d2: float


class BlackScholesEngine:
    """
    Black-Scholes-Merton pricing engine for European options.

    Supports continuous dividend yield (Merton extension).
    All Greeks are computed analytically (no finite-difference approximation).
    """

    @staticmethod
    def _d1d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0):
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2

    @classmethod
    def price(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> float:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        if option_type == "call":
            return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    @classmethod
    def delta(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> float:
        d1, _ = cls._d1d2(S, K, T, r, sigma, q)
        if option_type == "call":
            return np.exp(-q * T) * norm.cdf(d1)
        else:
            return np.exp(-q * T) * (norm.cdf(d1) - 1)

    @classmethod
    def gamma(cls, S, K, T, r, sigma, q=0.0, **kwargs) -> float:
        d1, _ = cls._d1d2(S, K, T, r, sigma, q)
        return np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @classmethod
    def theta(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> float:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        common = -(S * sigma * np.exp(-q * T) * norm.pdf(d1)) / (2 * np.sqrt(T))
        if option_type == "call":
            return (common
                    + q * S * np.exp(-q * T) * norm.cdf(d1)
                    - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365.0
        else:
            return (common
                    - q * S * np.exp(-q * T) * norm.cdf(-d1)
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365.0

    @classmethod
    def vega(cls, S, K, T, r, sigma, q=0.0, **kwargs) -> float:
        d1, _ = cls._d1d2(S, K, T, r, sigma, q)
        return S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100.0

    @classmethod
    def rho(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> float:
        _, d2 = cls._d1d2(S, K, T, r, sigma, q)
        if option_type == "call":
            return K * T * np.exp(-r * T) * norm.cdf(d2) / 100.0
        else:
            return -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100.0

    @classmethod
    def vanna(cls, S, K, T, r, sigma, q=0.0, **kwargs) -> float:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        return -np.exp(-q * T) * norm.pdf(d1) * d2 / sigma

    @classmethod
    def volga(cls, S, K, T, r, sigma, q=0.0, **kwargs) -> float:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        return S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) * d1 * d2 / sigma

    @classmethod
    def charm(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> float:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        charm_common = q * np.exp(-q * T) * norm.cdf(d1) - np.exp(-q * T) * norm.pdf(d1) * (
            2 * (r - q) * T - d2 * sigma * np.sqrt(T)
        ) / (2 * T * sigma * np.sqrt(T))
        if option_type == "call":
            return charm_common / 365.0
        else:
            return (charm_common - q * np.exp(-q * T)) / 365.0

    @classmethod
    def speed(cls, S, K, T, r, sigma, q=0.0, **kwargs) -> float:
        d1, _ = cls._d1d2(S, K, T, r, sigma, q)
        g = cls.gamma(S, K, T, r, sigma, q)
        return -g / S * (d1 / (sigma * np.sqrt(T)) + 1)

    @classmethod
    def compute_all(cls, S, K, T, r, sigma, q=0.0, option_type: OptionType = "call") -> BSResult:
        d1, d2 = cls._d1d2(S, K, T, r, sigma, q)
        return BSResult(
            price=cls.price(S, K, T, r, sigma, q, option_type),
            delta=cls.delta(S, K, T, r, sigma, q, option_type),
            gamma=cls.gamma(S, K, T, r, sigma, q),
            theta=cls.theta(S, K, T, r, sigma, q, option_type),
            vega=cls.vega(S, K, T, r, sigma, q),
            rho=cls.rho(S, K, T, r, sigma, q, option_type),
            vanna=cls.vanna(S, K, T, r, sigma, q),
            volga=cls.volga(S, K, T, r, sigma, q),
            charm=cls.charm(S, K, T, r, sigma, q, option_type),
            speed=cls.speed(S, K, T, r, sigma, q),
            option_type=option_type,
            d1=d1,
            d2=d2,
        )

    @classmethod
    def put_call_parity_check(cls, S, K, T, r, sigma, q=0.0) -> dict:
        """Verify put-call parity: C - P = S*e^(-qT) - K*e^(-rT)."""
        call = cls.price(S, K, T, r, sigma, q, "call")
        put = cls.price(S, K, T, r, sigma, q, "put")
        lhs = call - put
        rhs = S * np.exp(-q * T) - K * np.exp(-r * T)
        return {
            "call_price": call,
            "put_price": put,
            "C_minus_P": lhs,
            "S_exp_minus_K_exp": rhs,
            "parity_error": abs(lhs - rhs),
            "parity_holds": abs(lhs - rhs) < 1e-10,
        }
