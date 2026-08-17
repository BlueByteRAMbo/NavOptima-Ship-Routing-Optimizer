from typing import List, Dict, Optional
import json
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    is_port: bool

class Edge(BaseModel):
    id: str
    source_id: str
    target_id: str
    distance_nm: float
    base_congestion: float
    notes: Optional[str] = None  # Documentation field; not used in routing logic

class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

    # Pre-computed indices for faster lookup
    _node_map: Dict[str, Node] = {}
    _adjacency: Dict[str, List[Edge]] = {}

    def model_post_init(self, __context) -> None:
        # Populate private lookup caches after initialization
        self._node_map = {node.id: node for node in self.nodes}
        self._adjacency = {node.id: [] for node in self.nodes}
        for edge in self.edges:
            if edge.source_id in self._adjacency:
                self._adjacency[edge.source_id].append(edge)

    def get_node(self, node_id: str) -> Node:
        """Get a Node object by its ID."""
        if node_id not in self._node_map:
            raise KeyError(f"Node '{node_id}' not found in the graph.")
        return self._node_map[node_id]

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node."""
        return self._adjacency.get(node_id, [])

def load_graph(filepath: str) -> Graph:
    """Load a Graph instance from a JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return Graph(**data)
