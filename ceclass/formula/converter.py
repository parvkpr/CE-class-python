from __future__ import annotations
from typing import Optional, Union

import torch
from stlcgpp.formula import (
    Predicate, LessThan, GreaterThan,
    And, Or, Negation, Always, Eventually,
)

from ceclass.formula.stl_node import STLNode


def _resolve(value: Union[str, float], params: dict[str, float]) -> float:
    """Resolve an interval bound: return float directly or look up in params dict."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        if value in params:
            return float(params[value])
        raise KeyError(f"Parametric interval bound '{value}' not found in params: {list(params.keys())}")
    raise TypeError(f"Unexpected interval bound type: {type(value)}")


def to_stlcgpp(
    node: STLNode,
    params: dict[str, float],
    device: Optional[torch.device] = None,
    dt: float = 1.0,
) -> torch.nn.Module:
    """
    Recursively convert an STLNode tree to a stlcgpp formula.

    Args:
        node: The STLNode to convert.
        params: Maps symbolic interval boundary names to concrete float values.
        device: Torch device (cpu/cuda) for the formula.
        dt: Timestep duration for converting continuous time to discrete indices.

    Returns:
        A stlcgpp formula (torch.nn.Module) ready for robustness computation.
    """
    if node.node_type == 'predicate':
        idx = node.signal_index
        pred = Predicate(node.predicate_name, lambda s, _idx=idx: s[:, _idx])
        if node.predicate_op == '<':
            formula = LessThan(pred, node.predicate_threshold)
        elif node.predicate_op == '>':
            formula = GreaterThan(pred, node.predicate_threshold)
        else:
            raise ValueError(f"Unknown predicate op: {node.predicate_op}")
        return formula.to(device) if device else formula

    elif node.node_type == 'true':
        # TRUE: always satisfied. Use a predicate that's always positive.
        pred = Predicate("TRUE", lambda s: torch.ones(s.shape[0], device=s.device) * 1e6)
        formula = GreaterThan(pred, 0.0)
        return formula.to(device) if device else formula

    elif node.node_type == 'false':
        # FALSE: never satisfied. Use a predicate that's always negative.
        pred = Predicate("FALSE", lambda s: torch.ones(s.shape[0], device=s.device) * (-1e6))
        formula = GreaterThan(pred, 0.0)
        return formula.to(device) if device else formula

    elif node.node_type == 'not':
        child = to_stlcgpp(node.children[0], params, device, dt)
        formula = Negation(child)
        return formula.to(device) if device else formula

    elif node.node_type == 'and':
        left = to_stlcgpp(node.children[0], params, device, dt)
        right = to_stlcgpp(node.children[1], params, device, dt)
        formula = And(left, right)
        return formula.to(device) if device else formula

    elif node.node_type == 'or':
        left = to_stlcgpp(node.children[0], params, device, dt)
        right = to_stlcgpp(node.children[1], params, device, dt)
        formula = Or(left, right)
        return formula.to(device) if device else formula

    elif node.node_type == 'always':
        a = _resolve(node.interval[0], params)
        b = _resolve(node.interval[1], params)
        child = to_stlcgpp(node.children[0], params, device, dt)
        # Convert continuous time to discrete timestep indices
        interval = [int(round(a / dt)), int(round(b / dt))]
        formula = Always(child, interval=interval)
        return formula.to(device) if device else formula

    elif node.node_type == 'eventually':
        a = _resolve(node.interval[0], params)
        b = _resolve(node.interval[1], params)
        child = to_stlcgpp(node.children[0], params, device, dt)
        interval = [int(round(a / dt)), int(round(b / dt))]
        formula = Eventually(child, interval=interval)
        return formula.to(device) if device else formula

    else:
        raise ValueError(f"Unknown STLNode type: {node.node_type}")
