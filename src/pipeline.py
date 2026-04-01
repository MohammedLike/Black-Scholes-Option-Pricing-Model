"""
Main Pipeline Orchestrator.

Runs the complete end-to-end option pricing analysis:
1. Data ingestion (market or synthetic)
2. Black-Scholes pricing + Greeks
3. Monte Carlo validation
4. Implied volatility extraction
5. Sensitivity analysis
6. Visualization generation
7. Report compilation
"""
import sys
import logging
import numpy as np
from pathlib import Path

from src.config import PipelineConfig, ModelConfig, MonteCarloConfig
from src.black_scholes import BlackScholesEngine
from src.monte_carlo import MonteCarloEngine
from src.implied_volatility import ImpliedVolatilitySolver
from src.sensitivity import SensitivityAnalyzer
from src.data_pipeline import MarketDataPipeline
from src.visualization import Visualizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


class OptionPricingPipeline:
    """End-to-end option pricing analysis pipeline."""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.data_pipeline = MarketDataPipeline(self.config.output_dir / "data")
        self.visualizer = Visualizer(self.config.plot_dir)
        self.results = {}

    def run(self):
        """Execute the full pipeline."""
        logger.info("=" * 60)
        logger.info("OPTION PRICING MODEL — FULL PIPELINE")
        logger.info("=" * 60)

        self._step1_data_ingestion()
        self._step2_black_scholes()
        self._step3_monte_carlo()
        self._step4_implied_volatility()
        self._step5_sensitivity_analysis()
        self._step6_visualizations()
        self._step7_summary()

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE — All outputs in %s", self.config.output_dir)
        logger.info("=" * 60)
        return self.results

    def _step1_data_ingestion(self):
        logger.info("─── Step 1: Data Ingestion ───")
        cfg = self.config

        df = self.data_pipeline.fetch_stock_data(cfg.ticker)
        stats = self.data_pipeline.summary_statistics(df)
        vol_df = self.data_pipeline.compute_historical_volatility(df)

        # Use market data to calibrate model if available
        spot = self.data_pipeline.get_current_spot(df)
        hist_vol = self.data_pipeline.get_annualized_vol(df)

        logger.info(f"  Ticker: {cfg.ticker}")
        logger.info(f"  Current Spot: ${spot:.2f}")
        logger.info(f"  Historical Vol (63d): {hist_vol:.2%}")
        logger.info(f"  Skewness: {stats['skewness']:.4f}")
        logger.info(f"  Kurtosis: {stats['kurtosis']:.4f}")

        # Update config with market data
        cfg.model.S = round(spot, 2)
        cfg.model.K = round(spot, 2)  # ATM
        cfg.model.sigma = round(hist_vol, 4)

        self.results["market_data"] = df
        self.results["market_stats"] = stats
        self.results["volatility_df"] = vol_df

    def _step2_black_scholes(self):
        logger.info("─── Step 2: Black-Scholes Pricing ───")
        m = self.config.model

        call = BlackScholesEngine.compute_all(m.S, m.K, m.T, m.r, m.sigma, m.q, "call")
        put = BlackScholesEngine.compute_all(m.S, m.K, m.T, m.r, m.sigma, m.q, "put")
        parity = BlackScholesEngine.put_call_parity_check(m.S, m.K, m.T, m.r, m.sigma, m.q)

        logger.info(f"  Call Price: ${call.price:.4f}")
        logger.info(f"  Put Price:  ${put.price:.4f}")
        logger.info(f"  Put-Call Parity Error: {parity['parity_error']:.2e}")
        logger.info(f"  Delta (Call/Put): {call.delta:.4f} / {put.delta:.4f}")
        logger.info(f"  Gamma: {call.gamma:.6f}")
        logger.info(f"  Theta/day (Call/Put): {call.theta:.4f} / {put.theta:.4f}")
        logger.info(f"  Vega/1%%: {call.vega:.4f}")

        self.results["bs_call"] = call
        self.results["bs_put"] = put
        self.results["parity"] = parity

    def _step3_monte_carlo(self):
        logger.info("─── Step 3: Monte Carlo Simulation ───")
        m = self.config.model
        mc_cfg = self.config.monte_carlo

        engine = MonteCarloEngine(
            n_simulations=mc_cfg.n_simulations,
            n_steps=mc_cfg.n_steps,
            seed=mc_cfg.seed,
            antithetic=mc_cfg.antithetic,
            control_variate=mc_cfg.control_variate,
        )

        mc_call = engine.price_option(m.S, m.K, m.T, m.r, m.sigma, m.q, "call")
        mc_put = engine.price_option(m.S, m.K, m.T, m.r, m.sigma, m.q, "put")

        logger.info(f"  MC Call Price: ${mc_call.price:.4f} (BS: ${mc_call.bs_benchmark:.4f})")
        logger.info(f"  MC Put Price:  ${mc_put.price:.4f} (BS: ${mc_put.bs_benchmark:.4f})")
        logger.info(f"  Call Std Error: ${mc_call.std_error:.6f}")
        logger.info(f"  95%% CI: [{mc_call.confidence_interval_95[0]:.4f}, "
                    f"{mc_call.confidence_interval_95[1]:.4f}]")

        convergence = engine.convergence_analysis(m.S, m.K, m.T, m.r, m.sigma, m.q, "call")

        self.results["mc_call"] = mc_call
        self.results["mc_put"] = mc_put
        self.results["mc_convergence"] = convergence

    def _step4_implied_volatility(self):
        logger.info("─── Step 4: Implied Volatility ───")
        m = self.config.model

        # Extract IV from our BS price (should recover input sigma)
        bs_price = self.results["bs_call"].price
        iv_result = ImpliedVolatilitySolver.solve(bs_price, m.S, m.K, m.T, m.r, m.q, "call")

        logger.info(f"  Input Volatility: {m.sigma:.4f}")
        logger.info(f"  Recovered IV: {iv_result['implied_volatility']:.4f}")
        logger.info(f"  Converged: {iv_result['converged']} in {iv_result['iterations']} iters")

        # Generate and solve volatility smile
        smile_data = self.data_pipeline.generate_synthetic_smile_data(m.S, m.K, m.sigma)
        smile_results = ImpliedVolatilitySolver.volatility_smile(
            m.S, m.T, m.r, m.q, smile_data, "call"
        )

        logger.info(f"  Smile: {len(smile_results)} strikes solved")

        self.results["iv_result"] = iv_result
        self.results["smile_results"] = smile_results

    def _step5_sensitivity_analysis(self):
        logger.info("─── Step 5: Sensitivity Analysis ───")
        m = self.config.model
        s_cfg = self.config.sensitivity

        analyzer = SensitivityAnalyzer(m.S, m.K, m.T, m.r, m.sigma, m.q)

        spot_range = np.linspace(m.S * 0.5, m.S * 1.5, 80)
        vol_range = np.linspace(0.05, 0.80, 60)
        time_range = np.linspace(0.01, 2.0, 80)

        # 1D Greeks
        greeks_spot_call = analyzer.greeks_vs_spot(spot_range, "call")
        greeks_spot_put = analyzer.greeks_vs_spot(spot_range, "put")
        greeks_time_call = analyzer.greeks_vs_time(time_range, "call")
        greeks_time_put = analyzer.greeks_vs_time(time_range, "put")

        # 2D surfaces
        price_surf = analyzer.price_surface(spot_range, vol_range, "call")
        delta_surf = analyzer.delta_surface(spot_range, time_range, "call")
        gamma_surf = analyzer.gamma_surface(spot_range, vol_range)
        theta_surf = analyzer.theta_surface(spot_range, time_range, "call")

        # Scenario matrix
        spot_scenarios = np.linspace(m.S * 0.7, m.S * 1.3, 9)
        vol_scenarios = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
        scenario_matrix = analyzer.scenario_matrix(spot_scenarios, vol_scenarios, "call")

        # P&L
        expiry_range = np.linspace(m.S * 0.5, m.S * 1.5, 200)
        pnl_call = analyzer.pnl_at_expiry(expiry_range, self.results["bs_call"].price, "call")
        pnl_put = analyzer.pnl_at_expiry(expiry_range, self.results["bs_put"].price, "put")

        logger.info("  Computed: Greeks vs Spot, Greeks vs Time")
        logger.info("  Computed: Price/Delta/Gamma/Theta surfaces")
        logger.info(f"  Scenario matrix: {scenario_matrix.shape}")

        self.results.update({
            "spot_range": spot_range, "vol_range": vol_range, "time_range": time_range,
            "greeks_spot_call": greeks_spot_call, "greeks_spot_put": greeks_spot_put,
            "greeks_time_call": greeks_time_call, "greeks_time_put": greeks_time_put,
            "price_surface": price_surf, "delta_surface": delta_surf,
            "gamma_surface": gamma_surf, "theta_surface": theta_surf,
            "scenario_matrix": scenario_matrix,
            "pnl_call": pnl_call, "pnl_put": pnl_put,
            "expiry_range": expiry_range,
        })

    def _step6_visualizations(self):
        logger.info("─── Step 6: Generating Visualizations ───")
        v = self.visualizer
        r = self.results
        m = self.config.model

        plots = []

        # Greeks plots
        plots.append(v.plot_greeks_vs_spot(r["greeks_spot_call"], r["greeks_spot_put"], m.K))
        plots.append(v.plot_greeks_vs_time(r["greeks_time_call"], r["greeks_time_put"]))

        # 3D surfaces
        plots.append(v.plot_price_surface(r["spot_range"], r["vol_range"], r["price_surface"]))
        plots.append(v.plot_delta_surface(r["spot_range"], r["time_range"], r["delta_surface"]))
        plots.append(v.plot_gamma_surface(r["spot_range"], r["vol_range"], r["gamma_surface"]))
        plots.append(v.plot_theta_surface(r["spot_range"], r["time_range"], r["theta_surface"]))

        # Scenario heatmap
        plots.append(v.plot_scenario_heatmap(r["scenario_matrix"]))

        # P&L
        plots.append(v.plot_pnl_diagram(r["pnl_call"], r["pnl_put"], m.K))

        # Monte Carlo
        plots.append(v.plot_mc_paths(r["mc_call"].paths, m.S, m.K, m.T))
        plots.append(v.plot_mc_distribution(
            r["mc_call"].terminal_prices, m.K,
            r["bs_call"].price, r["mc_call"].price
        ))
        plots.append(v.plot_mc_convergence(
            r["mc_convergence"]["convergence_data"],
            r["mc_convergence"]["bs_benchmark"]
        ))

        # IV
        if r["iv_result"].get("history"):
            plots.append(v.plot_iv_convergence(r["iv_result"]["history"], r["bs_call"].price))
        plots.append(v.plot_volatility_smile(r["smile_results"]))

        # Dashboard
        plots.append(v.plot_dashboard(r["bs_call"], r["bs_put"], r["parity"]))

        logger.info(f"  Generated {len(plots)} plots")
        self.results["plot_paths"] = plots

    def _step7_summary(self):
        logger.info("─── Step 7: Results Summary ───")
        m = self.config.model
        r = self.results

        summary = {
            "model_params": {
                "spot": m.S, "strike": m.K, "time": m.T,
                "rate": m.r, "volatility": m.sigma, "dividend": m.q,
            },
            "bs_call_price": r["bs_call"].price,
            "bs_put_price": r["bs_put"].price,
            "mc_call_price": r["mc_call"].price,
            "mc_call_std_error": r["mc_call"].std_error,
            "mc_vs_bs_error": r["mc_call"].pricing_error,
            "put_call_parity_holds": r["parity"]["parity_holds"],
            "implied_vol_recovered": r["iv_result"]["implied_volatility"],
            "iv_converged": r["iv_result"]["converged"],
            "n_plots_generated": len(r.get("plot_paths", [])),
        }

        self.results["summary"] = summary
        logger.info("  Summary: %s", summary)


def main():
    """CLI entry point."""
    config = PipelineConfig()
    pipeline = OptionPricingPipeline(config)
    results = pipeline.run()
    return results


if __name__ == "__main__":
    main()
