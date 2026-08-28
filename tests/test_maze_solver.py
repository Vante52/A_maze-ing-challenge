"""Tests for maze parsing, graph creation, and search algorithms."""

import tempfile
import unittest
from pathlib import Path

from src.Maze_solver.graph.maze_to_graph import mazeToGraph, mazeToMatrix


class MazeSolverTests(unittest.TestCase):
    """Verify the public maze solver behavior."""

    def setUp(self) -> None:
        """Create a small maze with a known solution."""
        self.maze = [
            [2, 0, 1],
            [1, 0, 1],
            [0, 0, 3],
        ]

    def test_all_algorithms_reach_goal(self) -> None:
        """Every algorithm should return a continuous start-to-goal path."""
        graph, start, goal = mazeToGraph(self.maze)

        for path in (
            graph.primero_profundidad(start, goal),
            graph.primero_anchura(start, goal),
            graph.a_estrella(start, goal),
        ):
            self.assertEqual(path[0], start)
            self.assertEqual(path[-1], goal)
            self.assertTrue(
                all(
                    abs(first[0] - second[0]) + abs(first[1] - second[1]) == 1
                    for first, second in zip(path, path[1:])
                )
            )

    def test_first_line_is_goal_coordinate(self) -> None:
        """The parser should use the first line as the goal coordinate."""
        contents = "(2, 2)\n[2, 0, 1]\n[1, 0, 1]\n[0, 0, 0]\n"

        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "maze.txt"
            file_path.write_text(contents, encoding="utf-8")
            maze = mazeToMatrix(file_path)

        self.assertEqual(maze[2][2], 3)
        self.assertEqual((len(maze), len(maze[0])), (3, 3))

    def test_goal_cell_has_incoming_edges(self) -> None:
        """Walkable neighbours must connect to the goal cell."""
        graph, _start, goal = mazeToGraph(self.maze)
        self.assertIn(goal, graph.obtener_vecinos((2, 1)))


if __name__ == "__main__":
    unittest.main()
