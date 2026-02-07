from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from ceclass.formula.stl_node import STLNode


@dataclass
class PhiNode:
    """
    Node in the refinement lattice (formula graph).

    Each node represents a refined STL formula. Edges represent logical
    implication: if A is in greater_all of B, then A holding implies B holds.
    """

    formula: STLNode
    greater_all: list[PhiNode] = field(default_factory=list)
    smaller_all: list[PhiNode] = field(default_factory=list)
    greater_imme: list[PhiNode] = field(default_factory=list)
    smaller_imme: list[PhiNode] = field(default_factory=list)
    active: bool = True
    results: list[Any] = field(default_factory=list)  # Witnessing traces/systems

    @property
    def id(self) -> str:
        return self.formula.id

    def add_to_greater_all(self, node: PhiNode):
        if node not in self.greater_all and node is not self:
            self.greater_all.append(node)

    def add_to_smaller_all(self, node: PhiNode):
        if node not in self.smaller_all and node is not self:
            self.smaller_all.append(node)

    def add_to_greater_imme(self, node: PhiNode):
        if node not in self.greater_imme and node is not self:
            self.greater_imme.append(node)

    def add_to_smaller_imme(self, node: PhiNode):
        if node not in self.smaller_imme and node is not self:
            self.smaller_imme.append(node)

    def add_to_results(self, result: Any):
        self.results.append(result)

    def __hash__(self) -> int:
        return hash(self.formula.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, PhiNode):
            return False
        return self.formula.id == other.formula.id

    def __repr__(self) -> str:
        return f"PhiNode(id={self.formula.id}, active={self.active})"
