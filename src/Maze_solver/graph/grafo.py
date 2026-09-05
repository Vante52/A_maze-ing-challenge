"""Graph data structure and maze search algorithms."""

from collections import deque
from dataclasses import dataclass
from typing import Optional


Coordinate = tuple[int, int]


@dataclass
class SearchResult:
    """Store both the explored nodes and the final solution path."""

    visited: list[Coordinate]
    path: list[Coordinate]


class Grafo:
    """Represent a weighted graph with an adjacency list."""

    def __init__(self) -> None:
        """Create an empty graph."""
        self.lista_adyacencia: dict[Coordinate, set[Coordinate]] = {}
        self.pesos_aristas: dict[tuple[Coordinate, Coordinate], int] = {}

    def __repr__(self) -> str:
        """Return a readable representation of the adjacency list."""
        lines = []
        for node, neighbours in self.lista_adyacencia.items():
            weighted_neighbours = [
                (neighbour, self.obtener_peso(node, neighbour))
                for neighbour in sorted(neighbours)
            ]
            lines.append(f"{node} -> {weighted_neighbours}")
        return "\n".join(lines)

    def add_node(self, node: Coordinate) -> None:
        """Add a node if it is not already in the graph."""
        if node not in self.lista_adyacencia:
            self.lista_adyacencia[node] = set()

    def add_edge(
        self, from_node: Coordinate, to_node: Coordinate, weight: int = 1
    ) -> None:
        """Add a directed edge and its positive integer weight."""
        if weight <= 0:
            raise ValueError("Edge weights must be positive.")

        self.add_node(from_node)
        self.add_node(to_node)
        self.lista_adyacencia[from_node].add(to_node)
        edge = (from_node, to_node)
        self.pesos_aristas[edge] = min(
            weight, self.pesos_aristas.get(edge, weight)
        )

    def obtener_vecinos(self, node: Coordinate) -> set[Coordinate]:
        """Return the neighbours of a node."""
        return self.lista_adyacencia.get(node, set())

    def obtener_peso(self, from_node: Coordinate, to_node: Coordinate) -> int:
        """Return the weight of an existing directed edge."""
        return self.pesos_aristas[(from_node, to_node)]

    def h(self, current: Coordinate, goal: Coordinate) -> int:
        """Calculate Manhattan distance from a node to the goal."""
        return abs(current[0] - goal[0]) + abs(current[1] - goal[1])

    @staticmethod
    def _build_path(
        parents: dict[Coordinate, Optional[Coordinate]], goal: Coordinate
    ) -> list[Coordinate]:
        """Reconstruct a path by following each node's parent."""
        path = []
        current: Optional[Coordinate] = goal

        while current is not None:
            path.append(current)
            current = parents[current]

        path.reverse()
        return path

    def depth_first_search_details(
        self, start: Coordinate, goal: Coordinate
    ) -> SearchResult:
        """Run DFS and return its exploration order and solution path."""
        stack = [start]
        discovered = {start}
        parents: dict[Coordinate, Optional[Coordinate]] = {start: None}
        visited = []

        while stack:
            current = stack.pop()
            visited.append(current)

            if current == goal:
                return SearchResult(visited, self._build_path(parents, goal))

            # Reverse sorting keeps the visual result deterministic with a stack.
            for neighbour in sorted(self.obtener_vecinos(current), reverse=True):
                if neighbour not in discovered:
                    discovered.add(neighbour)
                    parents[neighbour] = current
                    stack.append(neighbour)

        return SearchResult(visited, [])

    def breadth_first_search_details(
        self, start: Coordinate, goal: Coordinate
    ) -> SearchResult:
        """Run BFS and return its exploration order and shortest path."""
        queue = deque([start])
        discovered = {start}
        parents: dict[Coordinate, Optional[Coordinate]] = {start: None}
        visited = []

        while queue:
            current = queue.popleft()
            visited.append(current)

            if current == goal:
                return SearchResult(visited, self._build_path(parents, goal))

            for neighbour in sorted(self.obtener_vecinos(current)):
                if neighbour not in discovered:
                    discovered.add(neighbour)
                    parents[neighbour] = current
                    queue.append(neighbour)

        return SearchResult(visited, [])

    def a_star_search_details(
        self, start: Coordinate, goal: Coordinate
    ) -> SearchResult:
        """Run A* using edge weights and Manhattan distance."""
        open_nodes = {start}
        closed_nodes: set[Coordinate] = set()
        parents: dict[Coordinate, Optional[Coordinate]] = {start: None}
        real_cost = {start: 0}
        visited = []

        while open_nodes:
            # The coordinate is a tie-breaker, so repeated runs look the same.
            current = min(
                open_nodes,
                key=lambda node: (real_cost[node] + self.h(node, goal), node),
            )
            open_nodes.remove(current)
            visited.append(current)

            if current == goal:
                return SearchResult(visited, self._build_path(parents, goal))

            closed_nodes.add(current)

            for neighbour in sorted(self.obtener_vecinos(current)):
                if neighbour in closed_nodes:
                    continue

                new_cost = real_cost[current] + self.obtener_peso(
                    current, neighbour
                )
                if neighbour not in real_cost or new_cost < real_cost[neighbour]:
                    real_cost[neighbour] = new_cost
                    parents[neighbour] = current
                    open_nodes.add(neighbour)

        return SearchResult(visited, [])

    def primero_profundidad(
        self, nodo_inicio: Coordinate, nodo_final: Coordinate
    ) -> list[Coordinate]:
        """Return the path found with depth-first search."""
        return self.depth_first_search_details(nodo_inicio, nodo_final).path

    def primero_anchura(
        self, nodo_inicio: Coordinate, nodo_final: Coordinate
    ) -> list[Coordinate]:
        """Return the shortest path found with breadth-first search."""
        return self.breadth_first_search_details(nodo_inicio, nodo_final).path

    def a_estrella(
        self, nodo_inicio: Coordinate, nodo_final: Coordinate
    ) -> list[Coordinate]:
        """Return the shortest path found with A* search."""
        return self.a_star_search_details(nodo_inicio, nodo_final).path
