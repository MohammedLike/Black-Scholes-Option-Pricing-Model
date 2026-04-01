"""
Visualization Pipeline.

Professional-grade plots for Greeks, sensitivity surfaces, Monte Carlo
paths, convergence, P&L diagrams, and volatility smiles.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from pathlib import Path

# Professional style
sns.set_theme(style="whitegrid", font_scale=1.1)
COLORS = {"call": "#2196F3", "put": "#F44336", "accent": "#4CAF50", "neutral": "#607D8B"}


class Visualizer:
    """Creates all plots for the option pricing pipeline."""

    def __init__(self, output_dir: Path = Path("outputs/plots")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save(self, fig, name):
        path = self.output_dir / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return path

    # ── Greeks vs Spot ──────────────────────────────────────────────
    def plot_greeks_vs_spot(self, df_call, df_put, base_K=100):
        """6-panel plot of all Greeks vs spot price for call and put."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("Option Greeks vs Spot Price", fontsize=16, fontweight="bold", y=1.02)

        greeks = ["price", "delta", "gamma", "theta", "vega", "rho"]
        titles = ["Option Price", "Delta (Δ)", "Gamma (Γ)",
                  "Theta (Θ) per day", "Vega (ν) per 1%", "Rho (ρ) per 1%"]

        for ax, greek, title in zip(axes.flat, greeks, titles):
            ax.plot(df_call["spot"], df_call[greek], color=COLORS["call"],
                    linewidth=2, label="Call")
            ax.plot(df_put["spot"], df_put[greek], color=COLORS["put"],
                    linewidth=2, label="Put")
            ax.axvline(x=base_K, color="gray", linestyle="--", alpha=0.5, label=f"K={base_K}")
            ax.set_title(title, fontweight="bold")
            ax.set_xlabel("Spot Price ($)")
            ax.legend(framealpha=0.9)
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        return self._save(fig, "greeks_vs_spot")

    # ── Greeks vs Time ──────────────────────────────────────────────
    def plot_greeks_vs_time(self, df_call, df_put):
        """Greeks as a function of time to expiry."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("Option Greeks vs Time to Expiry", fontsize=16, fontweight="bold", y=1.02)

        greeks = ["price", "delta", "gamma", "theta", "vega", "rho"]
        titles = ["Option Price", "Delta (Δ)", "Gamma (Γ)",
                  "Theta (Θ) per day", "Vega (ν) per 1%", "Rho (ρ) per 1%"]

        for ax, greek, title in zip(axes.flat, greeks, titles):
            ax.plot(df_call["time"], df_call[greek], color=COLORS["call"],
                    linewidth=2, label="Call")
            ax.plot(df_put["time"], df_put[greek], color=COLORS["put"],
                    linewidth=2, label="Put")
            ax.set_title(title, fontweight="bold")
            ax.set_xlabel("Time to Expiry (years)")
            ax.legend(framealpha=0.9)
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        return self._save(fig, "greeks_vs_time")

    # ── 3D Surface Plots ───────────────────────────────────────────
    def plot_3d_surface(self, X, Y, Z, xlabel, ylabel, zlabel, title, filename):
        """Generic 3D surface plot."""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection="3d")
        Xm, Ym = np.meshgrid(X, Y, indexing="ij")
        surf = ax.plot_surface(Xm, Ym, Z, cmap="viridis", alpha=0.85, edgecolor="none")
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_zlabel(zlabel, fontsize=11)
        ax.set_title(title, fontsize=14, fontweight="bold")
        fig.colorbar(surf, shrink=0.5, aspect=10, pad=0.1)
        return self._save(fig, filename)

    def plot_price_surface(self, spot_range, vol_range, price_grid):
        return self.plot_3d_surface(
            spot_range, vol_range, price_grid,
            "Spot Price ($)", "Volatility", "Option Price ($)",
            "Black-Scholes Price Surface (Call)", "price_surface_3d"
        )

    def plot_delta_surface(self, spot_range, time_range, delta_grid):
        return self.plot_3d_surface(
            spot_range, time_range, delta_grid,
            "Spot Price ($)", "Time to Expiry (yrs)", "Delta",
            "Delta Surface (Call)", "delta_surface_3d"
        )

    def plot_gamma_surface(self, spot_range, vol_range, gamma_grid):
        return self.plot_3d_surface(
            spot_range, vol_range, gamma_grid,
            "Spot Price ($)", "Volatility", "Gamma",
            "Gamma Surface", "gamma_surface_3d"
        )

    def plot_theta_surface(self, spot_range, time_range, theta_grid):
        return self.plot_3d_surface(
            spot_range, time_range, theta_grid,
            "Spot Price ($)", "Time to Expiry (yrs)", "Theta (per day)",
            "Theta Surface (Call)", "theta_surface_3d"
        )

    # ── Heatmaps ───────────────────────────────────────────────────
    def plot_scenario_heatmap(self, scenario_df, title="Scenario Analysis: Option Price"):
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(scenario_df.astype(float), annot=True, fmt=".2f",
                    cmap="RdYlGn", ax=ax, linewidths=0.5, cbar_kws={"label": "Option Price ($)"})
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Volatility", fontsize=12)
        ax.set_ylabel("Spot Price", fontsize=12)
        return self._save(fig, "scenario_heatmap")

    # ── P&L Diagram ────────────────────────────────────────────────
    def plot_pnl_diagram(self, pnl_call, pnl_put, K=100):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("P&L at Expiry", fontsize=16, fontweight="bold")

        for ax, df, opt_type, color in zip(
            axes, [pnl_call, pnl_put], ["Call", "Put"],
            [COLORS["call"], COLORS["put"]]
        ):
            ax.plot(df["spot"], df["pnl"], color=color, linewidth=2.5, label=f"Long {opt_type}")
            ax.fill_between(df["spot"], df["pnl"], 0,
                           where=df["pnl"] > 0, color=color, alpha=0.15)
            ax.fill_between(df["spot"], df["pnl"], 0,
                           where=df["pnl"] < 0, color="red", alpha=0.1)
            ax.axhline(y=0, color="black", linewidth=0.8)
            ax.axvline(x=K, color="gray", linestyle="--", alpha=0.5)
            ax.set_title(f"Long {opt_type}", fontweight="bold")
            ax.set_xlabel("Spot Price at Expiry ($)")
            ax.set_ylabel("P&L ($)")
            ax.legend()
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        return self._save(fig, "pnl_diagram")

    # ── Monte Carlo Paths ──────────────────────────────────────────
    def plot_mc_paths(self, paths, S0, K, T):
        fig, ax = plt.subplots(figsize=(14, 7))
        n_display = min(100, paths.shape[0])
        t_axis = np.linspace(0, T, paths.shape[1])

        for i in range(n_display):
            color = COLORS["call"] if paths[i, -1] > K else COLORS["put"]
            ax.plot(t_axis, paths[i], color=color, alpha=0.08, linewidth=0.5)

        ax.axhline(y=K, color="black", linestyle="--", linewidth=1.5, label=f"Strike K={K}")
        ax.axhline(y=S0, color=COLORS["accent"], linestyle="-.", linewidth=1.5,
                   label=f"Spot S₀={S0}")
        ax.set_title("Monte Carlo Simulated Price Paths (GBM)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Time (years)")
        ax.set_ylabel("Price ($)")
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        return self._save(fig, "mc_paths")

    # ── MC Terminal Distribution ───────────────────────────────────
    def plot_mc_distribution(self, terminal_prices, K, bs_price, mc_price):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Monte Carlo Terminal Price Analysis", fontsize=16, fontweight="bold")

        # Terminal price distribution
        ax = axes[0]
        ax.hist(terminal_prices, bins=100, density=True, color=COLORS["call"],
                alpha=0.6, edgecolor="white")
        ax.axvline(x=K, color="red", linestyle="--", linewidth=2, label=f"Strike K={K}")
        ax.axvline(x=np.mean(terminal_prices), color=COLORS["accent"],
                  linestyle="-.", linewidth=2, label=f"Mean={np.mean(terminal_prices):.2f}")
        ax.set_title("Terminal Price Distribution", fontweight="bold")
        ax.set_xlabel("Price ($)")
        ax.set_ylabel("Density")
        ax.legend()

        # Payoff distribution
        ax = axes[1]
        payoffs = np.maximum(terminal_prices - K, 0)
        ax.hist(payoffs[payoffs > 0], bins=80, density=True, color=COLORS["accent"],
                alpha=0.6, edgecolor="white")
        ax.axvline(x=bs_price, color="red", linestyle="--", linewidth=2,
                  label=f"BS Price={bs_price:.4f}")
        ax.axvline(x=mc_price, color=COLORS["call"], linestyle="-.",
                  linewidth=2, label=f"MC Price={mc_price:.4f}")
        ax.set_title("Call Payoff Distribution (non-zero)", fontweight="bold")
        ax.set_xlabel("Payoff ($)")
        ax.set_ylabel("Density")
        ax.legend()

        fig.tight_layout()
        return self._save(fig, "mc_distribution")

    # ── MC Convergence ─────────────────────────────────────────────
    def plot_mc_convergence(self, convergence_data, bs_benchmark):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Monte Carlo Convergence Analysis", fontsize=16, fontweight="bold")

        ns = [d["n_simulations"] for d in convergence_data]
        prices = [d["price"] for d in convergence_data]
        errors = [d["std_error"] for d in convergence_data]

        ax = axes[0]
        ax.plot(ns, prices, "o-", color=COLORS["call"], linewidth=2, markersize=6)
        ax.axhline(y=bs_benchmark, color="red", linestyle="--", linewidth=2,
                  label=f"BS Price={bs_benchmark:.4f}")
        ax.fill_between(ns, [p - 1.96 * e for p, e in zip(prices, errors)],
                       [p + 1.96 * e for p, e in zip(prices, errors)],
                       alpha=0.2, color=COLORS["call"])
        ax.set_xscale("log")
        ax.set_title("Price Convergence", fontweight="bold")
        ax.set_xlabel("Number of Simulations")
        ax.set_ylabel("Option Price ($)")
        ax.legend()

        ax = axes[1]
        ax.plot(ns, errors, "o-", color=COLORS["put"], linewidth=2, markersize=6)
        theoretical = [errors[0] * np.sqrt(ns[0]) / np.sqrt(n) for n in ns]
        ax.plot(ns, theoretical, "--", color="gray", linewidth=1.5, label="1/√n theoretical")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title("Standard Error Convergence", fontweight="bold")
        ax.set_xlabel("Number of Simulations")
        ax.set_ylabel("Standard Error ($)")
        ax.legend()

        fig.tight_layout()
        return self._save(fig, "mc_convergence")

    # ── Volatility Smile ───────────────────────────────────────────
    def plot_volatility_smile(self, smile_data):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Implied Volatility Analysis", fontsize=16, fontweight="bold")

        strikes = [d["strike"] for d in smile_data]
        ivs = [d["implied_vol"] for d in smile_data]
        moneyness = [d["moneyness"] for d in smile_data]

        ax = axes[0]
        ax.plot(strikes, ivs, "o-", color=COLORS["call"], linewidth=2, markersize=5)
        ax.set_title("Volatility Smile (IV vs Strike)", fontweight="bold")
        ax.set_xlabel("Strike Price ($)")
        ax.set_ylabel("Implied Volatility")
        ax.grid(True, alpha=0.3)

        ax = axes[1]
        ax.plot(moneyness, ivs, "o-", color=COLORS["put"], linewidth=2, markersize=5)
        ax.set_title("Volatility Smile (IV vs Moneyness)", fontweight="bold")
        ax.set_xlabel("Moneyness (S/K)")
        ax.set_ylabel("Implied Volatility")
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        return self._save(fig, "volatility_smile")

    # ── IV Newton-Raphson Convergence ──────────────────────────────
    def plot_iv_convergence(self, history, target_price):
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Implied Volatility Solver Convergence", fontsize=16, fontweight="bold")

        iters = [h["iteration"] for h in history]
        sigmas = [h["sigma"] for h in history]
        diffs = [abs(h["diff"]) for h in history]

        ax = axes[0]
        ax.plot(iters, sigmas, "o-", color=COLORS["call"], linewidth=2, markersize=6)
        ax.set_title("σ Convergence Path", fontweight="bold")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Implied Volatility (σ)")
        ax.grid(True, alpha=0.3)

        ax = axes[1]
        ax.semilogy(iters, diffs, "o-", color=COLORS["put"], linewidth=2, markersize=6)
        ax.set_title("Pricing Error Convergence", fontweight="bold")
        ax.set_xlabel("Iteration")
        ax.set_ylabel("|BS(σ) - Market Price|")
        ax.grid(True, alpha=0.3)

        fig.tight_layout()
        return self._save(fig, "iv_convergence")

    # ── Dashboard Summary ──────────────────────────────────────────
    def plot_dashboard(self, bs_call, bs_put, parity):
        """Single-page summary dashboard."""
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(3, 4, figure=fig, hspace=0.4, wspace=0.3)
        fig.suptitle("Options Pricing Dashboard", fontsize=18, fontweight="bold", y=0.98)

        # Pricing summary
        ax = fig.add_subplot(gs[0, :2])
        ax.axis("off")
        data = [
            ["Metric", "Call", "Put"],
            ["Price", f"${bs_call.price:.4f}", f"${bs_put.price:.4f}"],
            ["Delta", f"{bs_call.delta:.4f}", f"{bs_put.delta:.4f}"],
            ["Gamma", f"{bs_call.gamma:.6f}", f"{bs_put.gamma:.6f}"],
            ["Theta/day", f"{bs_call.theta:.4f}", f"{bs_put.theta:.4f}"],
            ["Vega/1%", f"{bs_call.vega:.4f}", f"{bs_put.vega:.4f}"],
            ["Rho/1%", f"{bs_call.rho:.4f}", f"{bs_put.rho:.4f}"],
        ]
        table = ax.table(cellText=data, cellLoc="center", loc="center",
                        colWidths=[0.3, 0.35, 0.35])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.5)
        for i in range(3):
            table[0, i].set_facecolor("#E3F2FD")
            table[0, i].set_text_props(fontweight="bold")
        ax.set_title("Greeks Summary", fontweight="bold", fontsize=13)

        # Put-Call Parity
        ax = fig.add_subplot(gs[0, 2:])
        ax.axis("off")
        parity_data = [
            ["Put-Call Parity Check", ""],
            ["C - P", f"${parity['C_minus_P']:.6f}"],
            ["S·e^(-qT) - K·e^(-rT)", f"${parity['S_exp_minus_K_exp']:.6f}"],
            ["Parity Error", f"${parity['parity_error']:.2e}"],
            ["Status", "PASS ✓" if parity["parity_holds"] else "FAIL ✗"],
        ]
        table2 = ax.table(cellText=parity_data, cellLoc="center", loc="center",
                         colWidths=[0.55, 0.45])
        table2.auto_set_font_size(False)
        table2.set_fontsize(11)
        table2.scale(1, 1.5)
        table2[0, 0].set_facecolor("#E8F5E9")
        table2[0, 0].set_text_props(fontweight="bold")
        table2[0, 1].set_facecolor("#E8F5E9")
        ax.set_title("Model Validation", fontweight="bold", fontsize=13)

        # Higher-order Greeks
        ax = fig.add_subplot(gs[1, :2])
        ax.axis("off")
        higher = [
            ["Higher-Order Greek", "Call", "Put"],
            ["Vanna", f"{bs_call.vanna:.6f}", f"{bs_put.vanna:.6f}"],
            ["Volga (Vomma)", f"{bs_call.volga:.6f}", f"{bs_put.volga:.6f}"],
            ["Charm/day", f"{bs_call.charm:.6f}", f"{bs_put.charm:.6f}"],
            ["Speed", f"{bs_call.speed:.8f}", f"{bs_put.speed:.8f}"],
        ]
        table3 = ax.table(cellText=higher, cellLoc="center", loc="center",
                         colWidths=[0.35, 0.325, 0.325])
        table3.auto_set_font_size(False)
        table3.set_fontsize(11)
        table3.scale(1, 1.5)
        for i in range(3):
            table3[0, i].set_facecolor("#FFF3E0")
            table3[0, i].set_text_props(fontweight="bold")
        ax.set_title("Higher-Order Greeks", fontweight="bold", fontsize=13)

        # d1, d2 info
        ax = fig.add_subplot(gs[1, 2:])
        ax.axis("off")
        d_data = [
            ["Parameter", "Value"],
            ["d₁", f"{bs_call.d1:.6f}"],
            ["d₂", f"{bs_call.d2:.6f}"],
            ["N(d₁)", f"{__import__('scipy').stats.norm.cdf(bs_call.d1):.6f}"],
            ["N(d₂)", f"{__import__('scipy').stats.norm.cdf(bs_call.d2):.6f}"],
        ]
        table4 = ax.table(cellText=d_data, cellLoc="center", loc="center",
                         colWidths=[0.45, 0.55])
        table4.auto_set_font_size(False)
        table4.set_fontsize(11)
        table4.scale(1, 1.5)
        table4[0, 0].set_facecolor("#F3E5F5")
        table4[0, 0].set_text_props(fontweight="bold")
        table4[0, 1].set_facecolor("#F3E5F5")
        table4[0, 1].set_text_props(fontweight="bold")
        ax.set_title("Black-Scholes Parameters", fontweight="bold", fontsize=13)

        return self._save(fig, "dashboard")
