#!/usr/bin/env python3
"""
Publication-style figures from CEClass paper experiment CSV.

Outputs (default directory: paper_figures/):
  1. time_comparison.png       — Per-benchmark subplots: 3 strategies
  2. speedup_vs_k.png          — Speedup ratio (NoPrune / strategy) vs k
  3. synth_calls_comparison.png — Synthesis calls: all benchmarks, 3 strategies
  4. coverage_comparison.png   — Coverage fraction: 3 strategies side-by-side
  5. summary_table.png         — Comprehensive table with all strategies

Usage:
  python plot_paper_results.py
  python plot_paper_results.py --csv results_100/summary.csv --out paper_figures
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


BENCH_ORDER = ["AT1", "AT2", "AT3", "AT5", "AFC1", "Robot"]
BENCH_LABELS = {
    "AT1": r"$\varphi_1^{AT}$",
    "AT2": r"$\varphi_2^{AT}$",
    "AT3": r"$\varphi_3^{AT}$",
    "AT5": r"$\varphi_5^{AT}$",
    "AFC1": r"$\varphi_1^{AFC}$",
    "Robot": r"$\varphi^{Rob}$",
}
K_ORDER = [1, 2, 3, 4]

STRATEGIES = ["no_prune", "alw_mid", "long_bs"]
STRAT_LABELS = {
    "no_prune": "NoPrune (Baseline)",
    "alw_mid":  "AlwMid",
    "long_bs":  "LongBS (Proposed)",
}
STRAT_COLORS = {
    "no_prune": "#2E7D32",
    "alw_mid":  "#1565C0",
    "long_bs":  "#D84315",
}


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            rows.append(row)
    return rows


def get_val(rows: list[dict], bench: str, k: int, strategy: str, key: str) -> float | None:
    for r in rows:
        if r["bench"] == bench and int(r["k"]) == k and r["strategy"] == strategy:
            return float(r[key])
    return None


def get_int(rows: list[dict], bench: str, k: int, strategy: str, key: str) -> int | None:
    for r in rows:
        if r["bench"] == bench and int(r["k"]) == k and r["strategy"] == strategy:
            return int(r[key])
    return None


# ── Figure 1: Per-benchmark time comparison ──────────────────────────────

def plot_time_comparison(rows: list[dict], out: Path) -> None:
    n_strat = len(STRATEGIES)
    fig, axes = plt.subplots(1, 6, figsize=(24, 4.5), dpi=150, sharey=False)

    x = np.arange(len(K_ORDER))
    w = 0.25

    for ax, bench in zip(axes, BENCH_ORDER):
        for si, strat in enumerate(STRATEGIES):
            vals = []
            for k in K_ORDER:
                v = get_val(rows, bench, k, strat, "time_class")
                vals.append(v if v is not None else 0)
            offset = (si - (n_strat - 1) / 2) * w
            bars = ax.bar(x + offset, vals, w,
                          label=STRAT_LABELS[strat], color=STRAT_COLORS[strat], alpha=0.85)
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            f"{val:.1f}", ha="center", va="bottom", fontsize=5.5,
                            color=STRAT_COLORS[strat])

        ax.set_xticks(x)
        ax.set_xticklabels([str(k) for k in K_ORDER])
        ax.set_xlabel("$k$", fontsize=11)
        ax.set_title(f"{bench}  ({BENCH_LABELS[bench]})", fontsize=11, fontweight="bold")
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.get_major_formatter().set_scientific(False)
        ax.grid(True, axis="y", alpha=0.3, which="both")

    axes[0].set_ylabel("Classification time (s, log scale)", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=n_strat, fontsize=10,
               bbox_to_anchor=(0.5, 1.08), frameon=True, edgecolor="gray")
    fig.suptitle("Classification Time Comparison Across Strategies",
                 fontsize=14, fontweight="bold", y=1.14)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ── Figure 2: Speedup ratio vs k ─────────────────────────────────────────

def plot_speedup_vs_k(rows: list[dict], out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=150)
    cmap = plt.cm.Set1(np.linspace(0, 0.8, len(BENCH_ORDER)))
    markers = ["o", "s", "D", "^", "v", "P"]

    for ax, strat, title in zip(axes,
                                 ["alw_mid", "long_bs"],
                                 ["AlwMid Speedup", "LongBS (Proposed) Speedup"]):
        for i, bench in enumerate(BENCH_ORDER):
            ks_plot, speedups = [], []
            for k in K_ORDER:
                np_t = get_val(rows, bench, k, "no_prune", "time_class")
                s_t = get_val(rows, bench, k, strat, "time_class")
                if np_t is not None and s_t is not None and s_t > 0:
                    ks_plot.append(k)
                    speedups.append(np_t / s_t)
            if ks_plot:
                ax.plot(ks_plot, speedups, f"{markers[i]}-", linewidth=2.2, markersize=8,
                        label=f"{bench} ({BENCH_LABELS[bench]})", color=cmap[i])

        ax.axhline(y=1, color="gray", linestyle=":", alpha=0.5, linewidth=1)
        ax.set_xlabel("Hierarchy depth $k$", fontsize=12)
        ax.set_ylabel("Speedup (NoPrune time / strategy time)", fontsize=11)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xticks(K_ORDER)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

    fig.suptitle("Speedup vs Hierarchy Depth", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ── Figure 3: Synthesis calls comparison ──────────────────────────────────

def plot_synth_calls(rows: list[dict], out: Path) -> None:
    n_strat = len(STRATEGIES)
    fig, axes = plt.subplots(1, 6, figsize=(24, 4.5), dpi=150, sharey=False)

    x = np.arange(len(K_ORDER))
    w = 0.25

    for ax, bench in zip(axes, BENCH_ORDER):
        synth_vals = {}
        for strat in STRATEGIES:
            synth_vals[strat] = [get_int(rows, bench, k, strat, "num_synth") or 0
                                 for k in K_ORDER]

        for si, strat in enumerate(STRATEGIES):
            offset = (si - (n_strat - 1) / 2) * w
            ax.bar(x + offset, synth_vals[strat], w,
                   label=STRAT_LABELS[strat], color=STRAT_COLORS[strat], alpha=0.85)

        for j, k in enumerate(K_ORDER):
            np_val = synth_vals["no_prune"][j]
            lb_val = synth_vals["long_bs"][j]
            if np_val > 0 and lb_val < np_val:
                pct = 100 * (np_val - lb_val) / np_val
                ax.text(x[j], max(synth_vals["no_prune"][j],
                                  synth_vals["alw_mid"][j],
                                  synth_vals["long_bs"][j]) * 1.02,
                        f"\u2212{pct:.0f}%", ha="center", va="bottom",
                        fontsize=6.5, color="#B71C1C", fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels([str(k) for k in K_ORDER])
        ax.set_xlabel("$k$", fontsize=11)
        ax.set_title(f"{bench}  ({BENCH_LABELS[bench]})", fontsize=11, fontweight="bold")
        ax.grid(True, axis="y", alpha=0.3)

    axes[0].set_ylabel("Synthesis calls (membership queries)", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=n_strat, fontsize=10,
               bbox_to_anchor=(0.5, 1.08), frameon=True, edgecolor="gray")
    fig.suptitle("Membership Queries: LongBS (Proposed) Saves the Most via Binary Search on Longest Path",
                 fontsize=13, fontweight="bold", y=1.14)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ── Figure 4: Coverage comparison ─────────────────────────────────────────

def plot_coverage_comparison(rows: list[dict], out: Path) -> None:
    n_strat = len(STRATEGIES)
    fig, axes = plt.subplots(1, 6, figsize=(24, 4), dpi=150, sharey=True)

    x = np.arange(len(K_ORDER))
    w = 0.25

    for ax, bench in zip(axes, BENCH_ORDER):
        for si, strat in enumerate(STRATEGIES):
            covs = []
            for k in K_ORDER:
                nc = get_int(rows, bench, k, strat, "num_covered")
                cl = get_int(rows, bench, k, strat, "num_classes")
                covs.append(nc / cl if nc and cl else 0)
            offset = (si - (n_strat - 1) / 2) * w
            ax.bar(x + offset, covs, w,
                   label=STRAT_LABELS[strat], color=STRAT_COLORS[strat], alpha=0.85)

        ax.set_xticks(x)
        ax.set_xticklabels([str(k) for k in K_ORDER])
        ax.set_xlabel("$k$", fontsize=11)
        ax.set_title(f"{bench}  ({BENCH_LABELS[bench]})", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.12)
        ax.grid(True, axis="y", alpha=0.3)

    axes[0].set_ylabel("Coverage (covered / classes)", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=n_strat, fontsize=10,
               bbox_to_anchor=(0.5, 1.08), frameon=True, edgecolor="gray")
    fig.suptitle("Coverage Is Preserved: All Strategies Achieve the Same Coverage",
                 fontsize=13, fontweight="bold", y=1.14)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ── Figure 5: Comprehensive summary table ────────────────────────────────

def plot_summary_table(rows: list[dict], out: Path) -> None:
    header = ["Bench", "$k$", "Classes",
              "Cov\nNP", "Cov\nAM", "Cov\nLB",
              "Time NP\n(s)", "Time AM\n(s)", "Time LB\n(s)",
              "Spdup\nAM", "Spdup\nLB",
              "Synth\nNP", "Synth\nAM", "Synth\nLB",
              "Synth\nSaved"]
    cells = []
    cell_colors = []

    for bench in BENCH_ORDER:
        for k in K_ORDER:
            cl = get_int(rows, bench, k, "no_prune", "num_classes")
            nc_np = get_int(rows, bench, k, "no_prune", "num_covered")
            nc_am = get_int(rows, bench, k, "alw_mid", "num_covered")
            nc_lb = get_int(rows, bench, k, "long_bs", "num_covered")
            t_np = get_val(rows, bench, k, "no_prune", "time_class")
            t_am = get_val(rows, bench, k, "alw_mid", "time_class")
            t_lb = get_val(rows, bench, k, "long_bs", "time_class")
            s_np = get_int(rows, bench, k, "no_prune", "num_synth")
            s_am = get_int(rows, bench, k, "alw_mid", "num_synth")
            s_lb = get_int(rows, bench, k, "long_bs", "num_synth")

            sp_am = t_np / t_am if t_np and t_am and t_am > 0 else 0
            sp_lb = t_np / t_lb if t_np and t_lb and t_lb > 0 else 0
            synth_saved = f"{100 * (1 - s_lb / s_np):.0f}%" if s_np and s_lb else "\u2014"

            row = [
                bench, str(k), str(cl or "\u2014"),
                f"{nc_np}/{cl}" if nc_np is not None else "\u2014",
                f"{nc_am}/{cl}" if nc_am is not None else "\u2014",
                f"{nc_lb}/{cl}" if nc_lb is not None else "\u2014",
                f"{t_np:.2f}" if t_np is not None else "\u2014",
                f"{t_am:.2f}" if t_am is not None else "\u2014",
                f"{t_lb:.2f}" if t_lb is not None else "\u2014",
                f"{sp_am:.1f}\u00d7" if sp_am > 0 else "\u2014",
                f"{sp_lb:.1f}\u00d7" if sp_lb > 0 else "\u2014",
                str(s_np) if s_np is not None else "\u2014",
                str(s_am) if s_am is not None else "\u2014",
                str(s_lb) if s_lb is not None else "\u2014",
                synth_saved,
            ]
            cells.append(row)

            base = "#F5F5F5" if BENCH_ORDER.index(bench) % 2 == 0 else "#FFFFFF"
            cell_colors.append([base] * len(header))

    nrows = len(cells)
    fig_h = 1.5 + nrows * 0.38
    fig, ax = plt.subplots(figsize=(18, fig_h), dpi=150)
    ax.axis("off")

    table = ax.table(
        cellText=cells,
        colLabels=header,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1.0, 1.55)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(fontweight="bold", fontsize=7)
            cell.set_facecolor("#37474F")
            cell.set_text_props(color="white", fontweight="bold", fontsize=7)
        cell.set_edgecolor("#BDBDBD")

    ax.set_title("Classification Results Summary — NoPrune vs AlwMid vs LongBS (Proposed)",
                 fontsize=13, fontweight="bold", pad=16)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Plot paper figures from summary CSV")
    ap.add_argument("--csv", type=Path, default=Path("results_100/summary.csv"))
    ap.add_argument("--out", type=Path, default=Path("paper_figures"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = load_rows(args.csv)
    if not rows:
        raise SystemExit(f"No rows in {args.csv}")

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titlesize": 12,
        "axes.labelsize": 11,
    })

    plot_time_comparison(rows, args.out / "time_comparison.png")
    plot_speedup_vs_k(rows, args.out / "speedup_vs_k.png")
    plot_synth_calls(rows, args.out / "synth_calls_comparison.png")
    plot_coverage_comparison(rows, args.out / "coverage_comparison.png")
    plot_summary_table(rows, args.out / "summary_table.png")


if __name__ == "__main__":
    main()
