from __future__ import annotations
from itertools import product as cartesian_product
from typing import Optional

from ceclass.formula.stl_node import STLNode
from ceclass.lattice.phi_node import PhiNode
from ceclass.lattice.phi_graph import PhiGraph


class _Edge:
    """Temporary edge representation used during parsing."""
    __slots__ = ('greater', 'smaller')

    def __init__(self, greater: str, smaller: str):
        self.greater = greater
        self.smaller = smaller

    def __repr__(self):
        return f"Edge({self.greater} -> {self.smaller})"


class Parser:
    """
    Parses an STL formula into a refinement lattice (PhiGraph).

    Port of Parser.m. Takes an STL formula (STLNode tree) and hierarchy depth k,
    generates all refined sub-formulas, builds implication edges, deduplicates,
    and returns a PhiGraph.

    Args:
        formula: Root STLNode of the specification.
        k: Hierarchy depth config. Nested list, e.g. [2, [1, [1], [1]]].
           k[0] = number of temporal segments for temporal operators.
           k[1] = k for first sub-formula.
           k[2] = k for second sub-formula (if binary operator).
    """

    def __init__(self, formula: STLNode, k: list):
        self.formula = formula
        self.k = k
        self.phi_graph: Optional[PhiGraph] = None
        self.simplify_dict: dict[str, str] = {}
        self.formula_dict: dict[str, STLNode] = {}
        self.simp_phi_dict: dict[str, PhiNode] = {}
        self.interval_dict: dict[str, tuple[float, float]] = {}

    def parse(self) -> PhiGraph:
        """Run the full parsing pipeline. Returns the constructed PhiGraph."""
        # 1. Generate refined formula nodes
        phi_nodes = self._parse_nodes_neg(self.formula, self.k)

        # 2. Deduplicate: keep only unique simplified formulas
        simp_phis = []
        seen_ids = set()
        for pn in phi_nodes:
            orig_id = pn.formula.id
            simp_id = self.simplify_dict[orig_id]
            if simp_id not in seen_ids:
                seen_ids.add(simp_id)
                formula = self.formula_dict[simp_id]
                simp_phis.append(PhiNode(formula=formula))

        for sp in simp_phis:
            self.simp_phi_dict[sp.formula.id] = sp

        # 3. Generate implication edges
        edges = self._parse_edges_neg(self.formula, self.k)

        # 4. Connect edges to deduplicated nodes
        for edge in edges:
            greater_simp_id = self.simplify_dict.get(edge.greater)
            smaller_simp_id = self.simplify_dict.get(edge.smaller)
            if greater_simp_id is None or smaller_simp_id is None:
                continue
            if greater_simp_id not in self.simp_phi_dict or smaller_simp_id not in self.simp_phi_dict:
                continue
            gn = self.simp_phi_dict[greater_simp_id]
            sn = self.simp_phi_dict[smaller_simp_id]
            gn.add_to_smaller_all(sn)
            sn.add_to_greater_all(gn)

        # 5. Build PhiGraph
        self.phi_graph = PhiGraph(simp_phis)
        self.phi_graph.set_imme()
        self.phi_graph.set_maxima()
        return self.phi_graph

    # ========================================================================
    # Node generation (positive polarity)
    # ========================================================================

    def _parse_nodes_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        if phi.node_type == 'predicate':
            return self._parse_predicate_pos(phi)
        elif phi.node_type == 'not':
            return self._parse_not_pos(phi, k)
        elif phi.node_type == 'and':
            return self._parse_and_pos(phi, k)
        elif phi.node_type == 'or':
            return self._parse_or_pos(phi, k)
        elif phi.node_type == 'always':
            return self._parse_always_pos(phi, k)
        elif phi.node_type == 'eventually':
            return self._parse_eventually_pos(phi, k)
        else:
            raise ValueError(f"Unsupported node type in parse_nodes_pos: {phi.node_type}")

    def _parse_predicate_pos(self, phi: STLNode) -> list[PhiNode]:
        self.simplify_dict[phi.id] = phi.id
        self.formula_dict[phi.id] = phi

        f_node = STLNode.false_node()
        self.simplify_dict['FALSE'] = 'FALSE'
        self.formula_dict['FALSE'] = f_node

        return [PhiNode(formula=phi), PhiNode(formula=f_node)]

    def _parse_not_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        # NOT in positive context: flip to negative for child
        child_nodes = self._parse_nodes_neg(phi.children[0], k[1])
        result = []
        for pn in child_nodes:
            p = pn.formula
            new_id = f"PosNot_{p.id}"
            new_formula = STLNode.not_node(p, new_id)
            result.append(PhiNode(formula=new_formula))

            p_simp_id = self.simplify_dict[p.id]
            if p_simp_id == 'FALSE':
                simplified_id = 'TRUE'
                self.formula_dict['TRUE'] = STLNode.true_node()
            elif p_simp_id == 'TRUE':
                simplified_id = 'FALSE'
                self.formula_dict['FALSE'] = STLNode.false_node()
            else:
                simplified_id = f"PosNot_{p_simp_id}"
                self.formula_dict[simplified_id] = STLNode.not_node(
                    self.formula_dict[p_simp_id], simplified_id
                )
            self.simplify_dict[new_id] = simplified_id
        return result

    def _parse_and_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        nodes1 = self._parse_nodes_pos(phi.children[0], k[1])
        nodes2 = self._parse_nodes_pos(phi.children[1], k[2])
        return self._combine_binary('PosAnd', 'and', nodes1, nodes2)

    def _parse_or_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        nodes1 = self._parse_nodes_pos(phi.children[0], k[1])
        nodes2 = self._parse_nodes_pos(phi.children[1], k[2])
        return self._combine_binary('PosOr', 'or', nodes1, nodes2)

    def _parse_always_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        return self._parse_temporal_pos(phi, k, 'always')

    def _parse_eventually_pos(self, phi: STLNode, k: list) -> list[PhiNode]:
        return self._parse_temporal_pos(phi, k, 'eventually')

    # ========================================================================
    # Node generation (negative polarity)
    # ========================================================================

    def _parse_nodes_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        if phi.node_type == 'predicate':
            return self._parse_predicate_neg(phi)
        elif phi.node_type == 'not':
            return self._parse_not_neg(phi, k)
        elif phi.node_type == 'and':
            return self._parse_and_neg(phi, k)
        elif phi.node_type == 'or':
            return self._parse_or_neg(phi, k)
        elif phi.node_type == 'always':
            return self._parse_always_neg(phi, k)
        elif phi.node_type == 'eventually':
            return self._parse_eventually_neg(phi, k)
        else:
            raise ValueError(f"Unsupported node type in parse_nodes_neg: {phi.node_type}")

    def _parse_predicate_neg(self, phi: STLNode) -> list[PhiNode]:
        self.simplify_dict[phi.id] = phi.id
        self.formula_dict[phi.id] = phi

        t_node = STLNode.true_node()
        self.simplify_dict['TRUE'] = 'TRUE'
        self.formula_dict['TRUE'] = t_node

        return [PhiNode(formula=phi), PhiNode(formula=t_node)]

    def _parse_not_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        # NOT in negative context: flip to positive for child
        child_nodes = self._parse_nodes_pos(phi.children[0], k[1])
        result = []
        for pn in child_nodes:
            p = pn.formula
            new_id = f"NegNot_{p.id}"
            new_formula = STLNode.not_node(p, new_id)
            result.append(PhiNode(formula=new_formula))

            p_simp_id = self.simplify_dict[p.id]
            if p_simp_id == 'FALSE':
                simplified_id = 'TRUE'
                self.formula_dict['TRUE'] = STLNode.true_node()
            elif p_simp_id == 'TRUE':
                simplified_id = 'FALSE'
                self.formula_dict['FALSE'] = STLNode.false_node()
            else:
                simplified_id = f"NegNot_{p_simp_id}"
                self.formula_dict[simplified_id] = STLNode.not_node(
                    self.formula_dict[p_simp_id], simplified_id
                )
            self.simplify_dict[new_id] = simplified_id
        return result

    def _parse_and_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        nodes1 = self._parse_nodes_neg(phi.children[0], k[1])
        nodes2 = self._parse_nodes_neg(phi.children[1], k[2])
        return self._combine_binary('NegAnd', 'and', nodes1, nodes2)

    def _parse_or_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        nodes1 = self._parse_nodes_neg(phi.children[0], k[1])
        nodes2 = self._parse_nodes_neg(phi.children[1], k[2])
        return self._combine_binary('NegOr', 'or', nodes1, nodes2)

    def _parse_always_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        return self._parse_temporal_neg(phi, k, 'always')

    def _parse_eventually_neg(self, phi: STLNode, k: list) -> list[PhiNode]:
        return self._parse_temporal_neg(phi, k, 'eventually')

    # ========================================================================
    # Shared binary combination (AND/OR)
    # ========================================================================

    def _combine_binary(self, prefix: str, op: str,
                        nodes1: list[PhiNode], nodes2: list[PhiNode]) -> list[PhiNode]:
        """Generate Cartesian product of two node lists with AND or OR semantics."""
        result = []
        for pn1 in nodes1:
            for pn2 in nodes2:
                p1, p2 = pn1.formula, pn2.formula
                new_id = f"{prefix}_{p1.id}{p2.id}"

                if op == 'and':
                    new_formula = STLNode.and_node(p1, p2, new_id)
                else:
                    new_formula = STLNode.or_node(p1, p2, new_id)
                result.append(PhiNode(formula=new_formula))

                p1_simp = self.simplify_dict[p1.id]
                p2_simp = self.simplify_dict[p2.id]

                if op == 'and':
                    simplified_id, simp_formula = self._simplify_and(
                        p1_simp, p2_simp, prefix
                    )
                else:
                    simplified_id, simp_formula = self._simplify_or(
                        p1_simp, p2_simp, prefix
                    )

                self.simplify_dict[new_id] = simplified_id
                self.formula_dict[simplified_id] = simp_formula
        return result

    def _simplify_and(self, p1_simp: str, p2_simp: str,
                      prefix: str) -> tuple[str, STLNode]:
        if p1_simp == 'FALSE' or p2_simp == 'FALSE':
            return 'FALSE', STLNode.false_node()
        elif p1_simp == 'TRUE' and p2_simp == 'TRUE':
            return 'TRUE', STLNode.true_node()
        elif p1_simp == 'TRUE':
            return p2_simp, self.formula_dict[p2_simp]
        elif p2_simp == 'TRUE':
            return p1_simp, self.formula_dict[p1_simp]
        else:
            sid = f"{prefix}_{p1_simp}{p2_simp}"
            formula = STLNode.and_node(
                self.formula_dict[p1_simp], self.formula_dict[p2_simp], sid
            )
            return sid, formula

    def _simplify_or(self, p1_simp: str, p2_simp: str,
                     prefix: str) -> tuple[str, STLNode]:
        if p1_simp == 'TRUE' or p2_simp == 'TRUE':
            return 'TRUE', STLNode.true_node()
        elif p1_simp == 'FALSE' and p2_simp == 'FALSE':
            return 'FALSE', STLNode.false_node()
        elif p1_simp == 'FALSE':
            return p2_simp, self.formula_dict[p2_simp]
        elif p2_simp == 'FALSE':
            return p1_simp, self.formula_dict[p1_simp]
        else:
            sid = f"{prefix}_{p1_simp}{p2_simp}"
            formula = STLNode.or_node(
                self.formula_dict[p1_simp], self.formula_dict[p2_simp], sid
            )
            return sid, formula

    # ========================================================================
    # Temporal operator handling (positive)
    # ========================================================================

    def _parse_temporal_pos(self, phi: STLNode, k: list,
                            temporal_type: str) -> list[PhiNode]:
        phi_id = phi.id
        k_num = k[0]
        child_nodes = self._parse_nodes_pos(phi.children[0], k[1])

        # Extract interval bounds
        t_start, t_end = phi.interval
        if isinstance(t_start, (int, float)) and isinstance(t_end, (int, float)):
            self.interval_dict[f"{phi_id}____"] = (float(t_start), float(t_end))

        # Build Cartesian product queue: child_nodes^k_num
        queue = [[cn] for cn in child_nodes]
        while len(queue[0]) < k_num:
            new_queue = []
            for row in queue:
                for cn in child_nodes:
                    new_queue.append(row + [cn])
            queue = new_queue

        if temporal_type == 'always':
            return self._build_always_nodes(queue, phi_id, t_start, t_end, 'Pos')
        else:
            return self._build_eventually_nodes(queue, phi_id, t_start, t_end, 'Pos')

    # ========================================================================
    # Temporal operator handling (negative)
    # ========================================================================

    def _parse_temporal_neg(self, phi: STLNode, k: list,
                            temporal_type: str) -> list[PhiNode]:
        phi_id = phi.id
        k_num = k[0]
        child_nodes = self._parse_nodes_neg(phi.children[0], k[1])

        t_start, t_end = phi.interval
        if isinstance(t_start, (int, float)) and isinstance(t_end, (int, float)):
            self.interval_dict[f"{phi_id}____"] = (float(t_start), float(t_end))

        queue = [[cn] for cn in child_nodes]
        while len(queue[0]) < k_num:
            new_queue = []
            for row in queue:
                for cn in child_nodes:
                    new_queue.append(row + [cn])
            queue = new_queue

        if temporal_type == 'always':
            return self._build_always_nodes(queue, phi_id, t_start, t_end, 'Neg')
        else:
            return self._build_eventually_nodes(queue, phi_id, t_start, t_end, 'Neg')

    # ========================================================================
    # Build temporal formula nodes
    # ========================================================================

    def _build_always_nodes(self, queue, phi_id, t_start, t_end,
                            polarity: str) -> list[PhiNode]:
        """Build always-refined formula nodes from the Cartesian product queue."""
        result = []
        col_size = len(queue[0])

        for row in queue:
            id_parts = [f"{polarity}Alw_"]
            simp_id_parts = [f"{polarity}Alw_"]
            simp_fixed_false = False
            simp_exist_nontrue = False
            phi_set = []
            simp_phi_set = []

            for j, pn in enumerate(row):
                p = pn.formula
                p_simp_id = self.simplify_dict[p.id]

                if p_simp_id == 'FALSE':
                    simp_fixed_false = True
                elif p_simp_id != 'TRUE':
                    simp_exist_nontrue = True

                # Determine interval boundaries for this segment
                tst = t_start if j == 0 else f"{phi_id}____t{j + 1}"
                ted = t_end if j == col_size - 1 else f"{phi_id}____t{j + 2}"

                # Store param bounds for symbolic boundaries
                if isinstance(tst, str) and tst not in self.interval_dict:
                    self._register_param_bound(tst, phi_id, t_start, t_end)
                if isinstance(ted, str) and ted not in self.interval_dict:
                    self._register_param_bound(ted, phi_id, t_start, t_end)

                alw_node = STLNode.always_node(p, interval=(tst, ted), node_id=f"Alw{p.id}")
                id_parts.append(p.id)
                phi_set.append(alw_node)

                if p_simp_id not in ('TRUE', 'FALSE'):
                    if j == 0:
                        simp_id_parts.append(f"st{p_simp_id}")
                    elif j == col_size - 1:
                        simp_id_parts.append(f"ed{p_simp_id}")
                    else:
                        simp_id_parts.append(p_simp_id)
                    simp_alw = STLNode.always_node(
                        self.formula_dict[p_simp_id],
                        interval=(tst, ted),
                        node_id=f"Alw{p_simp_id}"
                    )
                    simp_phi_set.append(simp_alw)

            full_id = "".join(id_parts)
            # Combine temporal segments with AND
            full_formula = self._chain_and(phi_set, full_id)
            result.append(PhiNode(formula=full_formula))

            # Simplification
            if simp_fixed_false:
                simplified_id = 'FALSE'
                self.formula_dict['FALSE'] = STLNode.false_node()
            elif not simp_exist_nontrue:
                simplified_id = 'TRUE'
                self.formula_dict['TRUE'] = STLNode.true_node()
            else:
                simplified_id = "".join(simp_id_parts)
                self.formula_dict[simplified_id] = self._chain_and(simp_phi_set, simplified_id)

            self.simplify_dict[full_id] = simplified_id

        return result

    def _build_eventually_nodes(self, queue, phi_id, t_start, t_end,
                                polarity: str) -> list[PhiNode]:
        """Build eventually-refined formula nodes from the Cartesian product queue."""
        result = []
        col_size = len(queue[0])

        for row in queue:
            id_parts = [f"{polarity}Ev_"]
            simp_id_parts = [f"{polarity}Ev_"]
            simp_fixed_true = False
            simp_exist_nonfalse = False
            phi_set = []
            simp_phi_set = []

            for j, pn in enumerate(row):
                p = pn.formula
                p_simp_id = self.simplify_dict[p.id]

                if p_simp_id == 'TRUE':
                    simp_fixed_true = True
                elif p_simp_id != 'FALSE':
                    simp_exist_nonfalse = True

                tst = t_start if j == 0 else f"{phi_id}____t{j + 1}"
                ted = t_end if j == col_size - 1 else f"{phi_id}____t{j + 2}"

                if isinstance(tst, str) and tst not in self.interval_dict:
                    self._register_param_bound(tst, phi_id, t_start, t_end)
                if isinstance(ted, str) and ted not in self.interval_dict:
                    self._register_param_bound(ted, phi_id, t_start, t_end)

                ev_node = STLNode.eventually_node(p, interval=(tst, ted), node_id=f"Ev{p.id}")
                id_parts.append(p.id)
                phi_set.append(ev_node)

                if p_simp_id not in ('TRUE', 'FALSE'):
                    if j == 0:
                        simp_id_parts.append(f"st{p_simp_id}")
                    elif j == col_size - 1:
                        simp_id_parts.append(f"ed{p_simp_id}")
                    else:
                        simp_id_parts.append(p_simp_id)
                    simp_ev = STLNode.eventually_node(
                        self.formula_dict[p_simp_id],
                        interval=(tst, ted),
                        node_id=f"Ev{p_simp_id}"
                    )
                    simp_phi_set.append(simp_ev)

            full_id = "".join(id_parts)
            # Combine temporal segments with OR
            full_formula = self._chain_or(phi_set, full_id)
            result.append(PhiNode(formula=full_formula))

            # Simplification
            if simp_fixed_true:
                simplified_id = 'TRUE'
                self.formula_dict['TRUE'] = STLNode.true_node()
            elif not simp_exist_nonfalse:
                simplified_id = 'FALSE'
                self.formula_dict['FALSE'] = STLNode.false_node()
            else:
                simplified_id = "".join(simp_id_parts)
                self.formula_dict[simplified_id] = self._chain_or(simp_phi_set, simplified_id)

            self.simplify_dict[full_id] = simplified_id

        return result

    # ========================================================================
    # Edge generation (positive polarity)
    # ========================================================================

    def _parse_edges_pos(self, phi: STLNode, k: list) -> list[_Edge]:
        if phi.node_type == 'predicate':
            pid = phi.id
            return [_Edge(pid, pid), _Edge(pid, 'FALSE'), _Edge('FALSE', 'FALSE')]

        elif phi.node_type == 'not':
            child_edges = self._parse_edges_neg(phi.children[0], k[1])
            return [_Edge(f"PosNot_{e.greater}", f"PosNot_{e.smaller}") for e in child_edges]

        elif phi.node_type == 'and':
            edges1 = self._parse_edges_pos(phi.children[0], k[1])
            edges2 = self._parse_edges_pos(phi.children[1], k[2])
            return [
                _Edge(f"PosAnd_{e1.greater}{e2.greater}", f"PosAnd_{e1.smaller}{e2.smaller}")
                for e1 in edges1 for e2 in edges2
            ]

        elif phi.node_type == 'or':
            edges1 = self._parse_edges_pos(phi.children[0], k[1])
            edges2 = self._parse_edges_pos(phi.children[1], k[2])
            return [
                _Edge(f"PosOr_{e1.greater}{e2.greater}", f"PosOr_{e1.smaller}{e2.smaller}")
                for e1 in edges1 for e2 in edges2
            ]

        elif phi.node_type == 'always':
            return self._parse_temporal_edges(phi, k, 'PosAlw')

        elif phi.node_type == 'eventually':
            return self._parse_temporal_edges(phi, k, 'PosEv')

        return []

    # ========================================================================
    # Edge generation (negative polarity)
    # ========================================================================

    def _parse_edges_neg(self, phi: STLNode, k: list) -> list[_Edge]:
        if phi.node_type == 'predicate':
            pid = phi.id
            return [_Edge(pid, pid), _Edge(pid, 'TRUE'), _Edge('TRUE', 'TRUE')]

        elif phi.node_type == 'not':
            child_edges = self._parse_edges_pos(phi.children[0], k[1])
            return [_Edge(f"NegNot_{e.greater}", f"NegNot_{e.smaller}") for e in child_edges]

        elif phi.node_type == 'and':
            edges1 = self._parse_edges_neg(phi.children[0], k[1])
            edges2 = self._parse_edges_neg(phi.children[1], k[2])
            return [
                _Edge(f"NegAnd_{e1.greater}{e2.greater}", f"NegAnd_{e1.smaller}{e2.smaller}")
                for e1 in edges1 for e2 in edges2
            ]

        elif phi.node_type == 'or':
            edges1 = self._parse_edges_neg(phi.children[0], k[1])
            edges2 = self._parse_edges_neg(phi.children[1], k[2])
            return [
                _Edge(f"NegOr_{e1.greater}{e2.greater}", f"NegOr_{e1.smaller}{e2.smaller}")
                for e1 in edges1 for e2 in edges2
            ]

        elif phi.node_type == 'always':
            return self._parse_temporal_edges(phi, k, 'NegAlw')

        elif phi.node_type == 'eventually':
            return self._parse_temporal_edges(phi, k, 'NegEv')

        return []

    # ========================================================================
    # Shared temporal edge generation
    # ========================================================================

    def _parse_temporal_edges(self, phi: STLNode, k: list, prefix: str) -> list[_Edge]:
        """Generate edges for temporal operators via Cartesian product of child edges."""
        k_num = k[0]

        # Determine which polarity to use for child edges
        if prefix.startswith('Pos'):
            child_edges = self._parse_edges_pos(phi.children[0], k[1])
        else:
            child_edges = self._parse_edges_neg(phi.children[0], k[1])

        # Cartesian product: child_edges^k_num
        queue = [[e] for e in child_edges]
        while len(queue[0]) < k_num:
            new_queue = []
            for row in queue:
                for e in child_edges:
                    new_queue.append(row + [e])
            queue = new_queue

        result = []
        for row in queue:
            id_1 = f"{prefix}_"
            id_2 = f"{prefix}_"
            for edge in row:
                id_1 += edge.greater
                id_2 += edge.smaller
            result.append(_Edge(id_1, id_2))
        return result

    # ========================================================================
    # Helpers
    # ========================================================================

    def _chain_and(self, nodes: list[STLNode], node_id: str) -> STLNode:
        """Chain a list of STLNodes into a binary AND tree."""
        if len(nodes) == 0:
            return STLNode.true_node()
        if len(nodes) == 1:
            # Preserve the single node but give it the target ID
            result = STLNode(
                node_type=nodes[0].node_type, id=node_id,
                children=nodes[0].children, interval=nodes[0].interval,
                predicate_name=nodes[0].predicate_name,
                predicate_op=nodes[0].predicate_op,
                predicate_threshold=nodes[0].predicate_threshold,
                signal_index=nodes[0].signal_index,
            )
            return result
        result = nodes[0]
        for i in range(1, len(nodes)):
            mid_id = node_id if i == len(nodes) - 1 else f"{node_id}__p{i}"
            result = STLNode.and_node(result, nodes[i], mid_id)
        return result

    def _chain_or(self, nodes: list[STLNode], node_id: str) -> STLNode:
        """Chain a list of STLNodes into a binary OR tree."""
        if len(nodes) == 0:
            return STLNode.false_node()
        if len(nodes) == 1:
            result = STLNode(
                node_type=nodes[0].node_type, id=node_id,
                children=nodes[0].children, interval=nodes[0].interval,
                predicate_name=nodes[0].predicate_name,
                predicate_op=nodes[0].predicate_op,
                predicate_threshold=nodes[0].predicate_threshold,
                signal_index=nodes[0].signal_index,
            )
            return result
        result = nodes[0]
        for i in range(1, len(nodes)):
            mid_id = node_id if i == len(nodes) - 1 else f"{node_id}__p{i}"
            result = STLNode.or_node(result, nodes[i], mid_id)
        return result

    def _register_param_bound(self, param_name: str, phi_id: str,
                              t_start, t_end):
        """Register a symbolic parameter bound derived from the parent interval."""
        base_key = f"{phi_id}____"
        if base_key in self.interval_dict:
            bounds = self.interval_dict[base_key]
            self.interval_dict[param_name] = bounds
        elif isinstance(t_start, (int, float)) and isinstance(t_end, (int, float)):
            self.interval_dict[param_name] = (float(t_start), float(t_end))

    def get_param_bounds_for_node(self, node: PhiNode) -> dict[str, tuple[float, float]]:
        """Get parameter bounds for all symbolic intervals in a node's formula."""
        param_names = node.formula.get_param_names()
        bounds = {}
        for name in param_names:
            if name in self.interval_dict:
                bounds[name] = self.interval_dict[name]
        return bounds
