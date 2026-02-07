"""
Example: Counterexample classification for Automatic Transmission model.

Reproduces the experiments from the CEClass paper using the AT1 benchmark.
Specification: alw_[0,30]((speed < 90) and (RPM < 4000))

Usage:
    python -m ceclass.examples.autotrans --data test/data/AT1.mat --k 2 --strategy long_bs
"""
from __future__ import annotations
import argparse
import time

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.bfs import BFSClassifier
from ceclass.strategies.no_prune import NoPruneClassifier
from ceclass.strategies.alw_mid import AlwMidClassifier
from ceclass.strategies.bs_random import BSRandomClassifier
from ceclass.strategies.long_bs import LongBSClassifier
from ceclass.utils.data import load_traces


STRATEGIES = {
    'bfs': BFSClassifier,
    'no_prune': NoPruneClassifier,
    'alw_mid': AlwMidClassifier,
    'bs_random': BSRandomClassifier,
    'long_bs': LongBSClassifier,
}


def build_at_spec(k_val: int = 2) -> tuple[STLNode, list]:
    """
    Build the AT specification: alw_[0,30]((speed < 90) and (RPM < 4000))

    Returns (formula, k) where k is the hierarchy depth configuration.
    """
    # Signal mapping: speed=column 0, RPM=column 1
    speed_pred = STLNode.predicate("speed", "<", 90.0, signal_index=0, node_id="speed_lt_90")
    rpm_pred = STLNode.predicate("RPM", "<", 4000.0, signal_index=1, node_id="RPM_lt_4000")

    and_node = STLNode.and_node(speed_pred, rpm_pred, node_id="speed_and_RPM")
    formula = STLNode.always_node(and_node, interval=(0, 30), node_id="alw_0_30")

    # Hierarchy depth: k_val splits for always, 1 for each predicate child
    k = [k_val, [1, [1], [1]]]

    return formula, k


def build_afc_spec(k_val: int = 2) -> tuple[STLNode, list]:
    """
    Build the AFC specification: ev_[0,40](alw_[0,10](AF - AFref in [-0.05, 0.05]))

    Simplified as: ev_[0,40](alw_[0,10]((AF_err > -0.05) and (AF_err < 0.05)))
    where AF_err = AF - AFref is signal column 0.
    """
    af_lower = STLNode.predicate("AF_err", ">", -0.05, signal_index=0, node_id="AF_err_gt_neg005")
    af_upper = STLNode.predicate("AF_err", "<", 0.05, signal_index=0, node_id="AF_err_lt_005")

    and_node = STLNode.and_node(af_lower, af_upper, node_id="AF_in_range")
    always_node = STLNode.always_node(and_node, interval=(0, 10), node_id="alw_0_10_AF")
    formula = STLNode.eventually_node(always_node, interval=(0, 40), node_id="ev_0_40")

    k = [k_val, [k_val, [1, [1], [1]]]]

    return formula, k


def run_classification(
    traces: torch.Tensor,
    formula: STLNode,
    k: list,
    strategy_name: str = 'long_bs',
    device=None,
    dt: float = 1.0,
    max_time_per_node: float = 60.0,
):
    """Run classification and print results."""
    strategy_cls = STRATEGIES[strategy_name]

    print(f"Strategy: {strategy_name}")
    print(f"Formula: {formula}")
    print(f"Traces shape: {traces.shape}")
    print(f"Device: {device}")
    print("-" * 60)

    classifier = strategy_cls(
        formula=formula,
        k=k,
        traces=traces,
        device=device,
        dt=dt,
        max_time_per_node=max_time_per_node,
    )

    print(f"Lattice: {classifier.num_classes} refined formulas")
    print(f"Parse time: {classifier.time_split:.3f}s")
    print("-" * 60)

    result = classifier.solve()

    print(f"\nResults:")
    print(f"  Classes (total):     {result.num_classes}")
    print(f"  Classes (covered):   {result.num_covered}")
    print(f"  Parse time:          {result.time_split:.3f}s")
    print(f"  Classification time: {result.time_class:.3f}s")
    print(f"  Total time:          {result.time_total:.3f}s")
    print(f"  Synthesis calls:     {result.num_synth_calls}")

    # if result.covered_nodes:
    #     print(f"\nCovered formulas:")
    #     for node in result.covered_nodes:
    #         print(f"  - {node.formula}")

    return result


def main():
    parser = argparse.ArgumentParser(description="CEClass Autotrans Example")
    parser.add_argument("--data", type=str, help="Path to trace data (.mat/.npy)")
    parser.add_argument("--k", type=int, default=2, help="Hierarchy depth")
    parser.add_argument("--strategy", type=str, default="long_bs", choices=STRATEGIES.keys())
    parser.add_argument("--spec", type=str, default="at", choices=["at", "afc"])
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--dt", type=float, default=1.0)
    parser.add_argument("--max-time", type=float, default=60.0)
    args = parser.parse_args()

    device = torch.device(args.device)

    if args.spec == "at":
        formula, k = build_at_spec(args.k)
    else:
        formula, k = build_afc_spec(args.k)

    if args.data:
        traces = load_traces(args.data, device=device)
    else:
        # Generate synthetic traces for testing
        print("No data provided, generating synthetic traces...")
        num_traces = 30
        timesteps = 50
        traces = torch.randn(num_traces, timesteps, 2, device=device)
        # Make speed oscillate around 90, RPM around 4000
        traces[:, :, 0] = 80 + 20 * torch.rand(num_traces, timesteps, device=device)
        traces[:, :, 1] = 3500 + 1000 * torch.rand(num_traces, timesteps, device=device)

    run_classification(
        traces=traces,
        formula=formula,
        k=k,
        strategy_name=args.strategy,
        device=device,
        dt=args.dt,
        max_time_per_node=args.max_time,
    )


if __name__ == "__main__":
    main()
