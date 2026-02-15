from typing import Any, Literal

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """A graph node representing a document or extracted entity."""

    id: str
    label: str
    node_type: Literal["document", "entity"]
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed relationship between two graph nodes."""

    id: str
    source: str
    target: str
    type: Literal["MATCH", "MISMATCH"]
    field_name: str
    explanation: str


class ConsistencyGraphResponse(BaseModel):
    """Consistency graph payload for a shipment."""

    shipment_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
