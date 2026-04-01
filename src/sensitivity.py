"""
Sensitivity Analysis Module.

Computes option price and Greek sensitivities across parameter ranges,
generating data for heatmaps, surface plots, and scenario analysis.
"""
import numpy as np
import pandas as pd
from itertools import product

from src.black_scholes import BlackScholesEngine


class SensitivityAnalyzer:
    """
    Performs multi-dimensional sensitivity analysis on Black-Scholes outputs.
    Generates data for surface plots, heatmaps, and scenario tables.
    """

    def __init__(self, base_S=100, base_K=100, base_T=1.0,
                 base_r=0.05, base_sigma=0.2, base_q=0.0):
        self.base = dict(S=base_S, K=base_K, T=base_T,
                         r=base_r, sigma=base_sigma, q=base_q)

    def _compute_grid(self, param1_name, param1_values,
                      param2_name, param2_values,
                      output_func, option_type="call"):
        """Compute a 2D grid of outputs over two parameter ranges."""
        grid = np.zeros((len(param1_values), len(param2_values)))
        for i, v1 in enumerate(param1_values):
            for j, v2 in enumerate(param2_values):
                params = dict(self.base)
                params[param1_name] = v1
                params[param2_name] = v2
                grid[i, j] = output_func(**params, option_type=option_type)
        return grid

    def price_surface(self, spot_range, vol_range, option_type="call"):
        """Price as a function of spot and volatility."""
        return self._compute_grid("S", spot_range, "sigma", vol_range,
                                  BlackScholesEngine.price, option_type)

    def delta_surface(self, spot_range, time_range, option_type="call"):
        """Delta as a function of spot and time to expiry."""
        return self._compute_grid("S", spot_range, "T", time_range,
                                  BlackScholesEngine.delta, option_type)

    def gamma_surface(self, spot_range, vol_range):
        """Gamma as a function of spot and volatility."""
        grid = np.zeros((len(spot_range), len(vol_range)))
        for i, s in enumerate(spot_range):
            for j, v in enumerate(vol_range):
                params = dict(self.base)
                params["S"] = s
                params["sigma"] = v
                grid[i, j] = BlackScholesEngine.gamma(**params)
        return grid

    def theta_surface(self, spot_range, time_range, option_type="call"):
        """Theta as a function of spot and time."""
        return self._compute_grid("S", spot_range, "T", time_range,
                                  BlackScholesEngine.theta, option_type)

    def vega_surface(self, spot_range, time_range):
        """Vega as a function of spot and time."""
        grid = np.zeros((len(spot_range), len(time_range)))
        for i, s in enumerate(spot_range):
            for j, t in enumerate(time_range):
                params = dict(self.base)
                params["S"] = s
                params["T"] = t
                grid[i, j] = BlackScholesEngine.vega(**params)
        return grid

    def greeks_vs_spot(self, spot_range, option_type="call"):
        """All Greeks as a function of spot price."""
        results = {
            "spot": spot_range,
            "price": [], "delta": [], "gamma": [],
            "theta": [], "vega": [], "rho": [],
        }
        for s in spot_range:
            params = dict(self.base)
            params["S"] = s
            results["price"].append(BlackScholesEngine.price(**params, option_type=option_type))
            results["delta"].append(BlackScholesEngine.delta(**params, option_type=option_type))
            results["gamma"].append(BlackScholesEngine.gamma(**params))
            results["theta"].append(BlackScholesEngine.theta(**params, option_type=option_type))
            results["vega"].append(BlackScholesEngine.vega(**params))
            results["rho"].append(BlackScholesEngine.rho(**params, option_type=option_type))
        return pd.DataFrame(results)

    def greeks_vs_time(self, time_range, option_type="call"):
        """All Greeks as a function of time to expiry."""
        results = {
            "time": time_range,
            "price": [], "delta": [], "gamma": [],
            "theta": [], "vega": [], "rho": [],
        }
        for t in time_range:
            params = dict(self.base)
            params["T"] = t
            results["price"].append(BlackScholesEngine.price(**params, option_type=option_type))
            results["delta"].append(BlackScholesEngine.delta(**params, option_type=option_type))
            results["gamma"].append(BlackScholesEngine.gamma(**params))
            results["theta"].append(BlackScholesEngine.theta(**params, option_type=option_type))
            results["vega"].append(BlackScholesEngine.vega(**params))
            results["rho"].append(BlackScholesEngine.rho(**params, option_type=option_type))
        return pd.DataFrame(results)

    def pnl_at_expiry(self, spot_range, premium_paid, option_type="call"):
        """P&L diagram at expiry for a long option position."""
        K = self.base["K"]
        if option_type == "call":
            payoff = np.maximum(spot_range - K, 0)
        else:
            payoff = np.maximum(K - spot_range, 0)
        pnl = payoff - premium_paid
        return pd.DataFrame({"spot": spot_range, "payoff": payoff, "pnl": pnl})

    def scenario_matrix(self, spot_scenarios, vol_scenarios, option_type="call"):
        """
        Scenario analysis matrix: price for each (spot, vol) combination.
        Returns a DataFrame with spot as index and vol as columns.
        """
        matrix = np.zeros((len(spot_scenarios), len(vol_scenarios)))
        for i, s in enumerate(spot_scenarios):
            for j, v in enumerate(vol_scenarios):
                params = dict(self.base)
                params["S"] = s
                params["sigma"] = v
                matrix[i, j] = BlackScholesEngine.price(**params, option_type=option_type)

        return pd.DataFrame(
            matrix,
            index=[f"S={s:.0f}" for s in spot_scenarios],
            columns=[f"σ={v:.0%}" for v in vol_scenarios],
        )
