"""Functions for reading a maze and converting it into a graph."""

from ast import literal_eval
from pathlib import Path

from .grafo import Coordinate, Grafo


VALID_VALUES = {0, 1, 2, 3}
WALKABLE_VALUES = {0, 2, 3}


def mazeToMatrix(file_path: str | Path) -> list[list[int]]:
    """Convert a maze text file into a matrix.

    The first line contains the goal coordinate, not the maze dimensions. The
    remaining lines contain the maze, using these values: 0 for free space, 1
    for a wall, 2 for the start, and 3 for the goal.

    Args:
        file_path: Path to the text file containing the maze.

    Returns:
        The maze as a rectangular list of integer lists.

    Raises:
        ValueError: If the file format or maze contents are invalid.
    """
    path = Path(file_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
    except OSError as error:
        raise ValueError(f"Could not read maze file: {error}") from error

    if len(lines) < 2:
        raise ValueError("The file must contain a goal coordinate and a maze.")

    try:
        goal_value = literal_eval(lines[0])
        maze = [list(literal_eval(line)) for line in lines[1:]]
    except (SyntaxError, ValueError, TypeError) as error:
        raise ValueError("The maze file contains invalid Python-style data.") from error

    if (
        not isinstance(goal_value, tuple)
        or len(goal_value) != 2
        or not all(isinstance(value, int) for value in goal_value)
    ):
        raise ValueError("The first line must be a goal coordinate such as (17, 17).")

    if not maze or not maze[0]:
        raise ValueError("The maze cannot be empty.")

    column_count = len(maze[0])
    if any(len(row) != column_count for row in maze):
        raise ValueError("All maze rows must have the same number of columns.")

    if any(value not in VALID_VALUES for row in maze for value in row):
        raise ValueError("Maze cells may only contain 0, 1, 2, or 3.")

    starts = _find_cells(maze, 2)
    marked_goals = _find_cells(maze, 3)
    goal = goal_value

    if len(starts) != 1:
        raise ValueError("The maze must contain exactly one start cell (2).")

    if not (0 <= goal[0] < len(maze) and 0 <= goal[1] < column_count):
        raise ValueError("The goal coordinate is outside the maze.")

    if maze[goal[0]][goal[1]] == 1:
        raise ValueError("The goal coordinate cannot point to a wall.")

    if marked_goals and marked_goals != [goal]:
        raise ValueError("The first-line goal does not match the cell marked with 3.")

    # The first line is authoritative, even if the matrix uses 0 at the goal.
    maze[goal[0]][goal[1]] = 3
    return maze


def _find_cells(maze: list[list[int]], value: int) -> list[Coordinate]:
    """Return the coordinates of every cell containing a value."""
    return [
        (row, column)
        for row, values in enumerate(maze)
        for column, cell in enumerate(values)
        if cell == value
    ]


def mazeToGraph(maze: list[list[int]]) -> tuple[Grafo, Coordinate, Coordinate]:
    """Convert a maze matrix into a graph and find its start and goal.

    Each walkable cell becomes a node. Horizontal and vertical movements become
    graph edges with an implicit weight of one.

    Args:
        maze: Rectangular maze matrix.

    Returns:
        A tuple containing the graph, start coordinate, and goal coordinate.

    Raises:
        ValueError: If the matrix does not contain one start and one goal.
    """
    if not maze or not maze[0]:
        raise ValueError("The maze cannot be empty.")

    column_count = len(maze[0])
    if any(len(row) != column_count for row in maze):
        raise ValueError("All maze rows must have the same number of columns.")

    starts = _find_cells(maze, 2)
    goals = _find_cells(maze, 3)

    if len(starts) != 1 or len(goals) != 1:
        raise ValueError("The maze must contain exactly one start and one goal.")

    graph = Grafo()
    row_count = len(maze)

    for row in range(row_count):
        for column in range(column_count):
            if maze[row][column] not in WALKABLE_VALUES:
                continue

            current = (row, column)
            graph.add_node(current)

            for next_row, next_column in (
                (row - 1, column),
                (row, column + 1),
                (row + 1, column),
                (row, column - 1),
            ):
                inside_maze = (
                    0 <= next_row < row_count and 0 <= next_column < column_count
                )
                if inside_maze and maze[next_row][next_column] in WALKABLE_VALUES:
                    graph.add_edge(current, (next_row, next_column))

    return graph, starts[0], goals[0]
