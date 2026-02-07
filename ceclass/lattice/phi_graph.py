from __future__ import annotations
import random
from ceclass.lattice.phi_node import PhiNode


class PhiGraph:
    """
    Directed acyclic graph of refined STL formulas.

    Edges represent logical implication: greater → smaller means
    "if greater holds, then smaller must hold".

    Supports pruning operations for classification algorithms.
    """

    def __init__(self, nodes: list[PhiNode]):
        self.nodes = nodes
        self.maxima: list[PhiNode] = []
        self._val_longest_path = 0
        self._seq_longest_path: list[PhiNode] = []

    # --- Graph construction ---

    def set_imme(self):
        """
        Compute immediate (transitive reduction) edges from transitive closure.

        Port of PhiGraph.m set_imme(). Works by iteratively processing minima
        (nodes with only self in smaller_all) and establishing immediate edges.
        """
        t_nodes = list(self.nodes)

        # Save original smaller_all for restoration
        saved_smaller_all = [list(nd.smaller_all) for nd in self.nodes]

        while True:
            # Find minima: nodes whose smaller_all has exactly 1 entry (themselves)
            minima = []
            min_idx = []
            for i, nd in enumerate(t_nodes):
                if len(nd.smaller_all) == 1:
                    minima.append(nd)
                    min_idx.append(i)

            # If no minima found among remaining nodes with smaller_all == 1,
            # also check for nodes with empty smaller_all (leaf nodes)
            if not minima:
                for i, nd in enumerate(t_nodes):
                    if len(nd.smaller_all) == 0:
                        minima.append(nd)
                        min_idx.append(i)

            # Remove minima from working set (in reverse order to preserve indices)
            for idx in sorted(min_idx, reverse=True):
                t_nodes.pop(idx)

            # For each minimum, check which remaining nodes should have it as immediate child
            for m in minima:
                for nn in t_nodes:
                    if m in nn.smaller_all:
                        # Check if there's an intermediate node between nn and m
                        flag = False
                        for sn in nn.smaller_all:
                            if sn is not nn and sn is not m and sn in m.greater_all:
                                flag = True
                                break

                        if not flag:
                            nn.add_to_smaller_imme(m)
                            m.add_to_greater_imme(nn)

                        # Remove m from nn.smaller_all
                        if m in nn.smaller_all:
                            nn.smaller_all.remove(m)

            if len(t_nodes) <= 1:
                break

        # Restore original smaller_all
        for i, nd in enumerate(self.nodes):
            nd.smaller_all = saved_smaller_all[i]

    def set_maxima(self):
        """Find root nodes (no immediate ancestors)."""
        self.maxima = [n for n in self.nodes if len(n.greater_imme) == 0]

    def set_active_maxima(self):
        """Recompute maxima among active nodes only."""
        self.maxima = []
        for n in self.nodes:
            if n.active:
                has_active_ancestor = any(gi.active for gi in n.greater_imme)
                if not has_active_ancestor:
                    self.maxima.append(n)

    # --- Path finding ---

    def get_longest_path(self) -> tuple[list[PhiNode], int]:
        """Find longest path in DAG via DFS from maxima. Returns (path, length)."""
        self._val_longest_path = 0
        self._seq_longest_path = []

        if self.maxima:
            for cur in self.maxima:
                if cur.active:
                    self._dfs([cur], cur, 1)

        return self._seq_longest_path, self._val_longest_path

    def _dfs(self, seq: list[PhiNode], node: PhiNode, val: int):
        """DFS helper for longest path computation."""
        if node.active:
            if val > self._val_longest_path:
                self._val_longest_path = val
                self._seq_longest_path = list(seq)

            for s in node.smaller_imme:
                if s.active:
                    self._dfs(seq + [s], s, val + 1)

    def get_random_path(self) -> tuple[list[PhiNode], int]:
        """Random walk from maxima downward. Returns (path, length)."""
        pool = list(self.maxima)
        path = []

        while True:
            active_pool = [m for m in pool if m.active]
            if not active_pool:
                break

            selected = random.choice(active_pool)
            path.append(selected)
            pool = list(selected.smaller_imme)

        return path, len(path)

    # --- Pruning operations ---

    def eliminate_hold(self, node: PhiNode, witness):
        """
        Node satisfies the spec → deactivate it and all ancestors.

        When a refined formula is satisfied, all weaker (greater/more general)
        formulas must also be satisfied.
        """
        if node.active:
            node.active = False
            node.add_to_results(witness)
            for g in node.greater_imme:
                self.eliminate_hold(g, witness)
            self.set_active_maxima()

    def eliminate_unhold(self, node: PhiNode):
        """
        Node fails the spec → deactivate it and all descendants.

        When a refined formula is NOT satisfied, all stronger (smaller/more specific)
        formulas cannot be satisfied either.
        """
        if node.active:
            node.active = False
            for s in node.smaller_imme:
                self.eliminate_unhold(s)

    # --- Query ---

    def is_empty(self) -> bool:
        """Check if any active nodes remain."""
        return not any(n.active for n in self.nodes)

    def get_active_nodes(self) -> list[PhiNode]:
        """Return all currently active nodes."""
        return [n for n in self.nodes if n.active]

    def get_covered_nodes(self) -> list[PhiNode]:
        """Return nodes that have at least one witnessing result."""
        return [n for n in self.nodes if len(n.results) > 0]

    # --- Visualization ---

    def to_dict(self) -> dict:
        """Export graph structure as a dictionary for visualization."""
        edges = []
        node_info = []
        for n in self.nodes:
            node_info.append({
                'id': n.formula.id,
                'formula': str(n.formula),
                'active': n.active,
                'has_results': len(n.results) > 0,
            })
            for s in n.smaller_imme:
                edges.append((n.formula.id, s.formula.id))
        return {'nodes': node_info, 'edges': edges}

    def __repr__(self) -> str:
        active = sum(1 for n in self.nodes if n.active)
        return f"PhiGraph(nodes={len(self.nodes)}, active={active}, maxima={len(self.maxima)})"
