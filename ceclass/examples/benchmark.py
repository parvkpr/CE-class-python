"""
Benchmark: sweep over k values and trace counts, collect results into CSV.

Usage:
    python -m ceclass.examples.benchmark
    python -m ceclass.examples.benchmark --device cuda --output results.csv
"""
from __future__ import annotations
import argparse
import csv
import time
from itertools import product as iterproduct

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.bfs import BFSClassifier
from ceclass.strategies.no_prune import NoPruneClassifier
from ceclass.strategies.alw_mid import AlwMidClassifier
from ceclass.strategies.bs_random import BSRandomClassifier
from ceclass.strategies.long_bs import LongBSClassifier


STRATEGIES = {
    'long_bs': LongBSClassifier,
    'bfs': BFSClassifier,
    'no_prune': NoPruneClassifier,
    'alw_mid': AlwMidClassifier,
    'bs_random': BSRandomClassifier,
}


def build_at_spec(k_val: int) -> tuple[STLNode, list]:
    """alw_[0,30]((speed < 90) and (RPM < 4000))"""
    speed = STLNode.predicate("speed", "<", 90.0, signal_index=0, node_id="speed_lt_90")
    rpm = STLNode.predicate("RPM", "<", 4000.0, signal_index=1, node_id="RPM_lt_4000")
    and_node = STLNode.and_node(speed, rpm, node_id="speed_and_RPM")
    formula = STLNode.always_node(and_node, interval=(0, 30), node_id="alw_0_30")
    k = [k_val, [1, [1], [1]]]
    return formula, k


def generate_traces(num_traces: int, timesteps: int = 50, device=None) -> torch.Tensor:
    """Generate synthetic falsifying traces for the AT spec."""
    traces = torch.zeros(num_traces, timesteps, 2, device=device)
    traces[:, :, 0] = 80 + 20 * torch.rand(num_traces, timesteps, device=device)
    traces[:, :, 1] = 3500 + 1000 * torch.rand(num_traces, timesteps, device=device)
    return traces


def run_single(
    strategy_name: str,
    k_val: int,
    num_traces: int,
    device,
    dt: float,
    max_time_per_node: float,
    max_evals_per_node: int,
) -> dict:
    formula, k = build_at_spec(k_val)
    traces = generate_traces(num_traces, timesteps=50, device=device)

    strategy_cls = STRATEGIES[strategy_name]
    classifier = strategy_cls(
        formula=formula,
        k=k,
        traces=traces,
        device=device,
        dt=dt,
        max_time_per_node=max_time_per_node,
        max_evals_per_node=max_evals_per_node,
    )

    result = classifier.solve()

    return {
        'strategy': strategy_name,
        'k': k_val,
        'num_traces': num_traces,
        'num_classes': result.num_classes,
        'num_covered': result.num_covered,
        'time_split': round(result.time_split, 4),
        'time_class': round(result.time_class, 4),
        'time_total': round(result.time_total, 4),
        'num_synth_calls': result.num_synth_calls,
    }


def main():
    parser = argparse.ArgumentParser(description="CEClass Benchmark")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--dt", type=float, default=1.0)
    parser.add_argument("--max-time", type=float, default=20.0, help="Max CMA-ES time per node")
    parser.add_argument("--max-evals", type=int, default=200, help="Max CMA-ES evals per node")
    parser.add_argument("--output", type=str, default="benchmark_results.csv")
    parser.add_argument("--strategies", nargs="+", default=list(STRATEGIES.keys()),
                        choices=list(STRATEGIES.keys()))
    args = parser.parse_args()

    device = torch.device(args.device)

    k_values = [1, 2, 3, 4, 5]
    trace_counts = [30, 50, 70, 100]
    strategies = args.strategies

    total_runs = len(strategies) * len(k_values) * len(trace_counts)
    print(f"Benchmark: {len(strategies)} strategies x {len(k_values)} k-values x {len(trace_counts)} trace counts = {total_runs} runs")
    print(f"Device: {device}")
    print(f"Output: {args.output}")
    print("=" * 80)

    fieldnames = [
        'strategy', 'k', 'num_traces', 'num_classes', 'num_covered',
        'time_split', 'time_class', 'time_total', 'num_synth_calls',
    ]

    rows = []
    run_idx = 0

    for strategy_name, k_val, num_traces in iterproduct(strategies, k_values, trace_counts):
        run_idx += 1
        print(f"[{run_idx}/{total_runs}] strategy={strategy_name}, k={k_val}, traces={num_traces} ... ", end="", flush=True)

        try:
            row = run_single(
                strategy_name=strategy_name,
                k_val=k_val,
                num_traces=num_traces,
                device=device,
                dt=args.dt,
                max_time_per_node=args.max_time,
                max_evals_per_node=args.max_evals,
            )
            rows.append(row)
            print(f"classes={row['num_classes']}, covered={row['num_covered']}, "
                  f"calls={row['num_synth_calls']}, time={row['time_total']:.3f}s")
        except Exception as e:
            print(f"FAILED: {e}")
            rows.append({
                'strategy': strategy_name, 'k': k_val, 'num_traces': num_traces,
                'num_classes': -1, 'num_covered': -1,
                'time_split': -1, 'time_class': -1, 'time_total': -1,
                'num_synth_calls': -1,
            })

    # Write CSV
    with open(args.output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 80)
    print(f"Done. Results written to {args.output}")


if __name__ == "__main__":
    main()
