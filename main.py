import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import OptionPricingPipeline
from src.config import PipelineConfig, ModelConfig, MonteCarloConfig


def parse_args():
    parser = argparse.ArgumentParser(description="Option Pricing Model Pipeline")
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker symbol")
    parser.add_argument("--spot", type=float, default=None, help="Spot price (overrides market data)")
    parser.add_argument("--strike", type=float, default=None, help="Strike price")
    parser.add_argument("--expiry", type=float, default=1.0, help="Time to expiry in years")
    parser.add_argument("--rate", type=float, default=0.05, help="Risk-free rate")
    parser.add_argument("--vol", type=float, default=None, help="Volatility (overrides historical)")
    parser.add_argument("--dividend", type=float, default=0.0, help="Continuous dividend yield")
    parser.add_argument("--mc-sims", type=int, default=100_000, help="Monte Carlo simulations")
    return parser.parse_args()


def main():
    args = parse_args()

    model = ModelConfig(
        S=args.spot or 100.0,
        K=args.strike or (args.spot or 100.0),
        T=args.expiry,
        r=args.rate,
        sigma=args.vol or 0.2,
        q=args.dividend,
    )

    mc = MonteCarloConfig(n_simulations=args.mc_sims)

    config = PipelineConfig(
        model=model,
        monte_carlo=mc,
        ticker=args.ticker,
    )

    pipeline = OptionPricingPipeline(config)
    results = pipeline.run()

    print("\n" + "=" * 60)
    print("KEY RESULTS")
    print("=" * 60)
    s = results["summary"]
    print(f"  Spot: ${s['model_params']['spot']:.2f}  |  Strike: ${s['model_params']['strike']:.2f}")
    print(f"  Volatility: {s['model_params']['volatility']:.2%}  |  Rate: {s['model_params']['rate']:.2%}")
    print(f"  BS Call: ${s['bs_call_price']:.4f}  |  BS Put: ${s['bs_put_price']:.4f}")
    print(f"  MC Call: ${s['mc_call_price']:.4f}  |  MC Error: ${s['mc_call_std_error']:.6f}")
    print(f"  Put-Call Parity: {'PASS' if s['put_call_parity_holds'] else 'FAIL'}")
    print(f"  IV Recovery: {s['implied_vol_recovered']:.6f} (converged: {s['iv_converged']})")
    print(f"  Plots Generated: {s['n_plots_generated']}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    main()
