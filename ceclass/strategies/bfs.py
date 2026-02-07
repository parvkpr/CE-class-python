from __future__ import annotations
import time
from collections import deque
from typing import Optional

import torch

from ceclass.formula.stl_node import STLNode
from ceclass.strategies.base import BaseClassifier, ClassificationResult


class BFSClassifier(BaseClassifier):
    """
    BFS queue-based classification strategy (baseline).

    Starts with maxima nodes in a queue. For each node:
    - If satisfied: add immediate children to queue
    - If failed: deactivate all descendants

    Port of MyClassProblem.m.
    """

    def solve(self) -> ClassificationResult:
        t_start = time.time()

        queue = deque(self.graph.maxima)
        seen_ids = {n.formula.id for n in queue}

        while queue:
            cur = queue.popleft()

            if not cur.active:
                continue

            satisfied, result = self._test_node(cur)

            if satisfied:
                cur.add_to_results(result)
                # Add active immediate children to queue
                for nd in cur.smaller_imme:
                    if nd.active and nd.formula.id not in seen_ids:
                        queue.append(nd)
                        seen_ids.add(nd.formula.id)
            else:
                # Deactivate all descendants
                for nd in cur.smaller_all:
                    nd.active = False

        time_class = time.time() - t_start
        return self._build_result(time_class)
