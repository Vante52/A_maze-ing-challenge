"""Functions for reading a maze and converting it into a graph."""

from ast import literal_eval
from pathlib import Path

from .grafo import Coordinate, Grafo


VALID_VALUES = {0, 1, 2, 3}
WALKABLE_VALUES = {0, 2, 3}


def mazeToMatrix(file_path: str | Path) -> list[list[int]]:
    """Convert a maze text file into a matrix.

    The first line may contain either the goal coordinate or the maze
    dimensions. The remaining lines contain the maze, using these values: 0
    for free space, 1 for a wall, 2 for the start, and 3 for the goal. When the
    first line contains dimensions, the goal must be marked with 3.

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
        raise ValueError("The file must contain a header and a maze.")

    try:
        header_value = literal_eval(lines[0])
        maze = [list(literal_eval(line)) for line in lines[1:]]
    except (SyntaxError, ValueError, TypeError) as error:
        raise ValueError("The maze file contains invalid Python-style data.") from error

    if (
        not isinstance(header_value, tuple)
        or len(header_value) != 2
        or not all(isinstance(value, int) for value in header_value)
    ):
        raise ValueError(
            "The first line must contain dimensions or a goal coordinate."
        )

    if not maze or not maze[0]:
        raise ValueError("The maze cannot be empty.")

    column_count = len(maze[0])
    if any(len(row) != column_count for row in maze):
        raise ValueError("All maze rows must have the same number of columns.")

    if any(value not in VALID_VALUES for row in maze for value in row):
        raise ValueError("Maze cells may only contain 0, 1, 2, or 3.")

    starts = _find_cells(maze, 2)
    marked_goals = _find_cells(maze, 3)
    dimensions = (len(maze), column_count)

    if len(starts) != 1:
        raise ValueError("The maze must contain exactly one start cell (2).")

    if header_value == dimensions:
        if len(marked_goals) != 1:
            raise ValueError(
                "A maze with dimensions in the first line must contain "
                "exactly one goal cell (3)."
            )
        goal = marked_goals[0]
    else:
        goal = header_value

    if not (0 <= goal[0] < len(maze) and 0 <= goal[1] < column_count):
        raise ValueError("The goal coordinate is outside the maze.")

    if maze[goal[0]][goal[1]] == 1:
        raise ValueError("The goal coordinate cannot point to a wall.")

    if marked_goals and marked_goals != [goal]:
        raise ValueError("The first-line goal does not match the cell marked with 3.")

    # A coordinate header is authoritative even if its matrix cell uses 0.
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

def mazeToMacroGraph(
    maze: list[list[int]],
) -> tuple[Grafo, Coordinate, Coordinate]:
    """Convert a maze matrix into a weighted macro graph.

    Only bifurcations, dead ends, the start, and the goal become graph nodes.
    A corridor becomes one edge whose weight is its number of steps.

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

    def walkable_neighbours(coordinate: Coordinate) -> list[Coordinate]:
        row, column = coordinate
        neighbours = []

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
                neighbours.append((next_row, next_column))

        return neighbours

    start = starts[0]
    goal = goals[0]
    nodes = {start, goal}

    for row in range(row_count):
        for column in range(column_count):
            coordinate = (row, column)
            neighbour_count = len(walkable_neighbours(coordinate))
            if maze[row][column] in WALKABLE_VALUES and (
                neighbour_count == 1 or neighbour_count > 2
            ):
                nodes.add(coordinate)

    for node in nodes:
        graph.add_node(node)

    for node in nodes:
        for neighbour in walkable_neighbours(node):
            previous = node
            current = neighbour
            steps = 1

            while current not in nodes:
                next_cells = [
                    coordinate
                    for coordinate in walkable_neighbours(current)
                    if coordinate != previous
                ]
                if len(next_cells) != 1:
                    break
                previous, current = current, next_cells[0]
                steps += 1

            if current in nodes and current != node:
                graph.add_edge(node, current, steps)

    return graph, start, goal


def expandMacroPath(
    maze: list[list[int]], compact_path: list[Coordinate]
) -> list[Coordinate]:
    """Expand a macro-graph path into every traversed maze coordinate.

    Args:
        maze: Rectangular maze matrix used to create the macro graph.
        compact_path: Sequence of decision nodes returned by a graph search.

    Returns:
        A continuous path containing the decision nodes and all corridor cells.

    Raises:
        ValueError: If the maze is invalid or two consecutive decision nodes
            are not connected by a corridor.
    """
    if not compact_path:
        return []

    if not maze or not maze[0]:
        raise ValueError("The maze cannot be empty.")

    row_count = len(maze)
    column_count = len(maze[0])
    if any(len(row) != column_count for row in maze):
        raise ValueError("All maze rows must have the same number of columns.")

    def walkable_neighbours(coordinate: Coordinate) -> list[Coordinate]:
        row, column = coordinate
        neighbours = []

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
                neighbours.append((next_row, next_column))

        return neighbours

    for coordinate in compact_path:
        row, column = coordinate
        inside_maze = 0 <= row < row_count and 0 <= column < column_count
        if not inside_maze or maze[row][column] not in WALKABLE_VALUES:
            raise ValueError(f"Invalid macro-path node: {coordinate}.")

    macro_nodes = set()
    for row in range(row_count):
        for column in range(column_count):
            coordinate = (row, column)
            if maze[row][column] not in WALKABLE_VALUES:
                continue

            neighbour_count = len(walkable_neighbours(coordinate))
            if (
                maze[row][column] in {2, 3}
                or neighbour_count == 1
                or neighbour_count > 2
            ):
                macro_nodes.add(coordinate)

    expanded_path = [compact_path[0]]

    for parent, child in zip(compact_path, compact_path[1:]):
        if parent == child:
            continue

        possible_corridors = []

        for neighbour in walkable_neighbours(parent):
            corridor = [parent, neighbour]
            previous = parent
            current = neighbour

            while current not in macro_nodes:
                next_cells = [
                    coordinate
                    for coordinate in walkable_neighbours(current)
                    if coordinate != previous
                ]
                if len(next_cells) != 1:
                    break

                previous, current = current, next_cells[0]
                if current in corridor:
                    break
                corridor.append(current)

            if current == child:
                possible_corridors.append(corridor)

        if not possible_corridors:
            raise ValueError(
                f"Macro nodes {parent} and {child} are not connected "
                "by a corridor."
            )

        corridor = min(possible_corridors, key=len)
        expanded_path.extend(corridor[1:])

    return expanded_path
