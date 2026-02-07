from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch

try:
    import cma
except ImportError:
    cma = None

from ceclass.formula.stl_node import STLNode
from ceclass.formula.converter import to_stlcgpp


@dataclass
class SynthResult:
    """Result of a parameter synthesis run."""
    satisfied: bool                        # True if robustness < 0 was found
    obj_best: float                        # Best objective value (min of -robustness)
    params_best: Optional[dict[str, float]] = None  # Best parameter values
    num_evals: int = 0
    time_spent: float = 0.0


class ParamSynthesis:
    """
    CMA-ES parameter synthesis with GPU-batched robustness evaluation.

    Searches for temporal parameter values (interval boundaries) that make
    the negation of a formula satisfiable (robustness < 0).

    Port of MyParamSynthProblem.m with stlcgpp replacing Breach.
    """

    def __init__(
        self,
        formula: STLNode,
        traces: torch.Tensor,
        param_names: list[str],
        param_bounds: dict[str, tuple[float, float]],
        device: Optional[torch.device] = None,
        dt: float = 1.0,
        max_time: float = 60.0,
        max_evals: int = 500,
        pop_size: Optional[int] = None,
    ):
        self.formula = formula
        self.traces = traces          # (num_traces, timesteps, dims)
        self.param_names = param_names
        self.param_bounds = param_bounds
        self.device = device
        self.dt = dt
        self.max_time = max_time
        self.max_evals = max_evals
        self.pop_size = pop_size

        # Compute initial guess and bounds
        self.lb = np.array([param_bounds[p][0] for p in param_names])
        self.ub = np.array([param_bounds[p][1] for p in param_names])
        self.x0 = (self.lb + self.ub) / 2.0
        self.sigma0 = np.mean((self.ub - self.lb) / 4.0)

    def solve(self) -> SynthResult:
        """
        Run CMA-ES to find params where negated formula has robustness < 0.

        For single-parameter problems, falls back to scipy's minimize_scalar
        since CMA-ES requires dimension >= 2.
        """
        if cma is None:
            raise ImportError("cma package required. Install with: pip install cma")

        neg_formula = STLNode.negate(self.formula)
        start_time = time.time()
        num_evals = 0
        n_params = len(self.param_names)

        if n_params == 1:
            return self._solve_1d(neg_formula)

        opts = {
            'bounds': [self.lb.tolist(), self.ub.tolist()],
            'maxfevals': self.max_evals,
            'timeout': self.max_time,
            'verbose': -9,  # Suppress output
        }
        if self.pop_size is not None:
            opts['popsize'] = self.pop_size

        sigma0 = float(self.sigma0) if self.sigma0 > 0 else 1.0
        es = cma.CMAEvolutionStrategy(self.x0.tolist(), sigma0, opts)

        while not es.stop():
            if time.time() - start_time >= self.max_time:
                break

            candidates = es.ask()
            fitnesses = self._batch_evaluate(candidates, neg_formula)
            num_evals += len(candidates)
            es.tell(candidates, fitnesses)

            # Early termination: found satisfying params
            if es.result.fbest < 0:
                break

        elapsed = time.time() - start_time
        best_x = es.result.xbest
        best_params = dict(zip(self.param_names, best_x)) if best_x is not None else None

        return SynthResult(
            satisfied=es.result.fbest < 0,
            obj_best=es.result.fbest,
            params_best=best_params,
            num_evals=num_evals,
            time_spent=elapsed,
        )

    def _solve_1d(self, neg_formula: STLNode) -> SynthResult:
        """Solve single-parameter synthesis using grid search + refinement."""
        start_time = time.time()
        lb, ub = float(self.lb[0]), float(self.ub[0])
        best_obj = float('inf')
        best_x = None
        num_evals = 0

        # Grid search with 20 points
        n_grid = min(20, self.max_evals)
        for val in np.linspace(lb, ub, n_grid):
            params = {self.param_names[0]: float(val)}
            try:
                stl_formula = to_stlcgpp(neg_formula, params, self.device, self.dt)
                with torch.no_grad():
                    rob = torch.vmap(stl_formula)(self.traces)
                    min_rob = rob.min().item()
                obj = -min_rob
            except Exception:
                obj = 1e9
            num_evals += 1

            if obj < best_obj:
                best_obj = obj
                best_x = float(val)

            if best_obj < 0:
                break

            if time.time() - start_time >= self.max_time:
                break

        elapsed = time.time() - start_time
        best_params = {self.param_names[0]: best_x} if best_x is not None else None

        return SynthResult(
            satisfied=best_obj < 0,
            obj_best=best_obj,
            params_best=best_params,
            num_evals=num_evals,
            time_spent=elapsed,
        )

    def _batch_evaluate(self, candidates: list, neg_formula: STLNode) -> list[float]:
        """
        Evaluate all CMA-ES candidates. Each candidate is a parameter vector.
        For each candidate, compute robustness across ALL traces on GPU.
        """
        fitnesses = []
        for candidate in candidates:
            params = dict(zip(self.param_names, candidate))
            try:
                stl_formula = to_stlcgpp(neg_formula, params, self.device, self.dt)
                with torch.no_grad():
                    rob = torch.vmap(stl_formula)(self.traces)  # (num_traces, timesteps)
                    min_rob = rob.min().item()
                fitnesses.append(-min_rob)  # Objective: minimize -robustness
            except Exception:
                fitnesses.append(1e9)  # Invalid params → large penalty
        return fitnesses

    def evaluate_direct(self, formula: STLNode) -> float:
        """
        Direct robustness evaluation (no parameters to search).
        Returns min robustness across all traces.
        """
        neg_formula = STLNode.negate(formula)
        stl_formula = to_stlcgpp(neg_formula, {}, self.device, self.dt)
        with torch.no_grad():
            rob = torch.vmap(stl_formula)(self.traces)
            return rob.min().item()
