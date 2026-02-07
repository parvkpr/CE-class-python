from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union
from copy import deepcopy


@dataclass
class STLNode:
    """
    Introspectable STL formula tree node.

    Used internally for parsing and lattice construction. Converted to
    stlcgpp formulas (via converter.py) only when robustness computation
    is needed.
    """

    node_type: str  # 'predicate', 'and', 'or', 'not', 'always', 'eventually', 'true', 'false'
    id: str
    children: list[STLNode] = field(default_factory=list)
    # Temporal interval: (start, end) where each can be float or str (parametric)
    interval: Optional[tuple[Union[str, float], Union[str, float]]] = None
    # Predicate leaf fields
    predicate_name: Optional[str] = None
    predicate_op: Optional[str] = None  # '<' or '>'
    predicate_threshold: Optional[float] = None
    signal_index: Optional[int] = None

    # --- Factory methods ---

    @staticmethod
    def predicate(name: str, op: str, threshold: float, signal_index: int,
                  node_id: Optional[str] = None) -> STLNode:
        if node_id is None:
            node_id = f"{name}_{op}_{threshold}"
        return STLNode(
            node_type='predicate', id=node_id,
            predicate_name=name, predicate_op=op,
            predicate_threshold=threshold, signal_index=signal_index,
        )

    @staticmethod
    def true_node() -> STLNode:
        return STLNode(node_type='true', id='TRUE')

    @staticmethod
    def false_node() -> STLNode:
        return STLNode(node_type='false', id='FALSE')

    @staticmethod
    def not_node(child: STLNode, node_id: str) -> STLNode:
        return STLNode(node_type='not', id=node_id, children=[child])

    @staticmethod
    def and_node(left: STLNode, right: STLNode, node_id: str) -> STLNode:
        return STLNode(node_type='and', id=node_id, children=[left, right])

    @staticmethod
    def or_node(left: STLNode, right: STLNode, node_id: str) -> STLNode:
        return STLNode(node_type='or', id=node_id, children=[left, right])

    @staticmethod
    def always_node(child: STLNode, interval: tuple, node_id: str) -> STLNode:
        return STLNode(node_type='always', id=node_id, children=[child], interval=interval)

    @staticmethod
    def eventually_node(child: STLNode, interval: tuple, node_id: str) -> STLNode:
        return STLNode(node_type='eventually', id=node_id, children=[child], interval=interval)

    @staticmethod
    def nary_and(children: list[STLNode], node_id: str) -> STLNode:
        """Create n-ary AND by chaining binary ANDs (matches MATLAB 'aand')."""
        if len(children) == 0:
            return STLNode.true_node()
        if len(children) == 1:
            return children[0]
        result = children[0]
        for i in range(1, len(children)):
            result = STLNode.and_node(result, children[i], node_id if i == len(children) - 1 else f"{node_id}__partial{i}")
        return result

    @staticmethod
    def nary_or(children: list[STLNode], node_id: str) -> STLNode:
        """Create n-ary OR by chaining binary ORs (matches MATLAB 'oor')."""
        if len(children) == 0:
            return STLNode.false_node()
        if len(children) == 1:
            return children[0]
        result = children[0]
        for i in range(1, len(children)):
            result = STLNode.or_node(result, children[i], node_id if i == len(children) - 1 else f"{node_id}__partial{i}")
        return result

    # --- Negation ---

    @staticmethod
    def negate(node: STLNode) -> STLNode:
        """Create the negation of a formula (push negation to leaves via NNF)."""
        if node.node_type == 'true':
            return STLNode.false_node()
        elif node.node_type == 'false':
            return STLNode.true_node()
        elif node.node_type == 'not':
            return node.children[0]
        else:
            return STLNode.not_node(node, f"neg_{node.id}")

    # --- Parameter extraction ---

    def get_param_names(self) -> list[str]:
        """Collect all symbolic (str) interval boundary names in this subtree."""
        params = []
        if self.interval is not None:
            for bound in self.interval:
                if isinstance(bound, str):
                    params.append(bound)
        for child in self.children:
            params.extend(child.get_param_names())
        return list(dict.fromkeys(params))  # deduplicate preserving order

    def get_param_bounds(self, interval_dict: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
        """
        Map symbolic param names to their numeric bounds.

        interval_dict maps parent formula IDs to their original numeric intervals,
        so we can derive bounds for the symbolic split points.
        """
        bounds = {}
        if self.interval is not None:
            for bound in self.interval:
                if isinstance(bound, str) and bound in interval_dict:
                    bounds[bound] = interval_dict[bound]
        for child in self.children:
            bounds.update(child.get_param_bounds(interval_dict))
        return bounds

    # --- Display ---

    def __str__(self) -> str:
        if self.node_type == 'predicate':
            return f"{self.predicate_name} {self.predicate_op} {self.predicate_threshold}"
        elif self.node_type == 'true':
            return "TRUE"
        elif self.node_type == 'false':
            return "FALSE"
        elif self.node_type == 'not':
            return f"not({self.children[0]})"
        elif self.node_type == 'and':
            return f"({self.children[0]}) and ({self.children[1]})"
        elif self.node_type == 'or':
            return f"({self.children[0]}) or ({self.children[1]})"
        elif self.node_type == 'always':
            a, b = self.interval
            return f"alw_[{a},{b}]({self.children[0]})"
        elif self.node_type == 'eventually':
            a, b = self.interval
            return f"ev_[{a},{b}]({self.children[0]})"
        return f"STLNode({self.node_type}, {self.id})"

    def __repr__(self) -> str:
        return f"STLNode(type={self.node_type}, id={self.id})"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, STLNode):
            return False
        return self.id == other.id
