from __future__ import annotations
import math
import time
from typing import Optional

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.base import BaseClassifier, ClassificationResult


class LongBSClassifier(BaseClassifier):
    """
    Binary search on longest path classification strategy (PROPOSED).

    Repeatedly finds the longest path in the active graph, then performs
    binary search on it. At each midpoint:
    - If satisfied: eliminate_hold (prune ancestors), search upper half
    - If failed: eliminate_unhold (prune descendants), search lower half

    Expected complexity: O(log n) node tests per path.

    Port of MyClassProblemLongBS.m.
    """

    def solve(self) -> ClassificationResult:
        t_start = time.time()

        while not self.graph.is_empty():
            path, path_len = self.graph.get_longest_path()
            if path_len == 0:
                break

            istart = 0
            iend = len(path) - 1

            while istart <= iend:
                mid = math.ceil((istart + iend) / 2)
                if mid >= len(path):
                    break
                cur = path[mid]

                satisfied, result = self._test_node(cur)

                if satisfied:
                    self.graph.eliminate_hold(cur, result)
                    istart = mid + 1
                else:
                    self.graph.eliminate_unhold(cur)
                    iend = mid - 1

        time_class = time.time() - t_start
        return self._build_result(time_class)
