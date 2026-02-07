from __future__ import annotations
import math
import time
from typing import Optional

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.base import BaseClassifier, ClassificationResult


class AlwMidClassifier(BaseClassifier):
    """
    Midpoint of longest path classification strategy.

    Repeatedly finds the longest active path, tests the midpoint,
    and prunes based on result. No binary search — just one test per
    path iteration.

    Port of MyClassProblemAlwMid.m.
    """

    def solve(self) -> ClassificationResult:
        t_start = time.time()

        while not self.graph.is_empty():
            path, path_len = self.graph.get_longest_path()
            if path_len == 0:
                break

            mid = math.ceil(len(path) / 2) - 1  # 0-indexed midpoint
            mid = max(0, min(mid, len(path) - 1))
            cur = path[mid]

            satisfied, result = self._test_node(cur)

            if satisfied:
                self.graph.eliminate_hold(cur, result)
            else:
                self.graph.eliminate_unhold(cur)

        time_class = time.time() - t_start
        return self._build_result(time_class)
