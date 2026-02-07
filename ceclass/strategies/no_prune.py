from __future__ import annotations
import time
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.base import BaseClassifier, ClassificationResult


class NoPruneClassifier(BaseClassifier):
    """
    Exhaustive classification strategy with no pruning (baseline).

    Tests every node in the lattice, regardless of results.
    This is the baseline for comparison — worst case O(n).

    Port of MyClassProblemNoPrune.m.
    """

    def solve(self) -> ClassificationResult:
        t_start = time.time()

        for cur in self.graph.nodes:
            satisfied, result = self._test_node(cur)
            if satisfied:
                cur.add_to_results(result)

        time_class = time.time() - t_start
        return self._build_result(time_class)
