"""Minimal graphical interface for loading and solving maze files."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .graph.grafo import Coordinate, Grafo, SearchResult
from .graph.maze_to_graph import mazeToGraph, mazeToMatrix


CELL_COLORS = {
    0: "white",
    1: "#263238",
    2: "#43a047",
    3: "#e53935",
}
EXPLORED_COLOR = "#81d4fa"
PATH_COLOR = "#ffd54f"


def solve_maze(
    maze: list[list[int]],
    dimensions: tuple[int, int],
    start: Coordinate,
    goal: Coordinate,
) -> dict[str, list[Coordinate]]:
    """Solve a maze with DFS, BFS, and A*.

    This function explicitly receives the four inputs requested by the project
    statement: maze matrix, dimensions, start coordinate, and goal coordinate.

    Args:
        maze: Matrix that represents the maze.
        dimensions: Number of rows and columns in the matrix.
        start: Coordinate containing the start cell.
        goal: Coordinate containing the goal cell.

    Returns:
        A dictionary with the solution path produced by each algorithm.

    Raises:
        ValueError: If dimensions, start, or goal do not match the matrix.
    """
    real_dimensions = (len(maze), len(maze[0]))
    if dimensions != real_dimensions:
        raise ValueError(f"Expected dimensions {real_dimensions}, got {dimensions}.")

    graph, detected_start, detected_goal = mazeToGraph(maze)
    if start != detected_start or goal != detected_goal:
        raise ValueError("The given start or goal does not match the maze.")

    return {
        "DFS": graph.primero_profundidad(start, goal),
        "BFS": graph.primero_anchura(start, goal),
        "A*": graph.a_estrella(start, goal),
    }


class MazeApp:
    """Display a maze and animate the selected search algorithm."""

    def __init__(self, root: tk.Tk) -> None:
        """Create the window and its controls."""
        self.root = root
        self.root.title("A-maze-ing Challenge")
        self.root.minsize(620, 680)

        self.maze: list[list[int]] = []
        self.graph: Grafo | None = None
        self.start: Coordinate | None = None
        self.goal: Coordinate | None = None
        self.rectangles: dict[Coordinate, int] = {}
        self.animation_id: str | None = None
        self.algorithm_buttons: list[ttk.Button] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Build the basic interface widgets."""
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill="x")

        ttk.Button(controls, text="Load maze", command=self.load_maze).pack(
            side="left", padx=(0, 12)
        )

        for name in ("BFS", "DFS", "A*"):
            button = ttk.Button(
                controls,
                text=name,
                command=lambda algorithm=name: self.start_search(algorithm),
                state="disabled",
            )
            button.pack(side="left", padx=3)
            self.algorithm_buttons.append(button)

        ttk.Label(controls, text="Delay (ms):").pack(side="left", padx=(16, 4))
        self.delay = tk.DoubleVar(value=20)
        ttk.Scale(
            controls,
            from_=1,
            to=150,
            variable=self.delay,
            orient="horizontal",
            length=110,
        ).pack(side="left")

        self.file_label = ttk.Label(
            self.root, text="Select a .txt maze file", padding=(10, 0, 10, 8)
        )
        self.file_label.pack(fill="x")

        self.canvas = tk.Canvas(
            self.root,
            width=650,
            height=570,
            background="#eceff1",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self.draw_maze())

        self.status = ttk.Label(self.root, text="No maze loaded", padding=10)
        self.status.pack(fill="x")

    def load_maze(self) -> None:
        """Ask the user for a file and load its maze."""
        file_path = filedialog.askopenfilename(
            title="Select maze file",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if not file_path:
            return

        self._cancel_animation()

        try:
            maze = mazeToMatrix(file_path)
            graph, start, goal = mazeToGraph(maze)
        except ValueError as error:
            messagebox.showerror("Invalid maze", str(error))
            return

        self.maze = maze
        self.graph = graph
        self.start = start
        self.goal = goal
        self.file_label.config(text=Path(file_path).name)
        self.status.config(
            text=(
                f"Loaded {len(maze)} x {len(maze[0])} maze | "
                f"Start: {start} | Goal: {goal}"
            )
        )

        for button in self.algorithm_buttons:
            button.config(state="normal")
        self.draw_maze()

    def draw_maze(self) -> None:
        """Draw the current maze so it fits inside the canvas."""
        self.canvas.delete("all")
        self.rectangles.clear()
        if not self.maze:
            return

        rows = len(self.maze)
        columns = len(self.maze[0])
        cell_size = min(
            max(self.canvas.winfo_width(), 1) / columns,
            max(self.canvas.winfo_height(), 1) / rows,
        )
        maze_width = columns * cell_size
        maze_height = rows * cell_size
        offset_x = (self.canvas.winfo_width() - maze_width) / 2
        offset_y = (self.canvas.winfo_height() - maze_height) / 2

        for row, values in enumerate(self.maze):
            for column, value in enumerate(values):
                x1 = offset_x + column * cell_size
                y1 = offset_y + row * cell_size
                rectangle = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x1 + cell_size,
                    y1 + cell_size,
                    fill=CELL_COLORS[value],
                    outline="#b0bec5",
                    width=1,
                )
                self.rectangles[(row, column)] = rectangle

    def start_search(self, algorithm: str) -> None:
        """Calculate a search and start its canvas animation."""
        if self.graph is None or self.start is None or self.goal is None:
            return

        self._cancel_animation()
        self.draw_maze()

        search_functions = {
            "BFS": self.graph.breadth_first_search_details,
            "DFS": self.graph.depth_first_search_details,
            "A*": self.graph.a_star_search_details,
        }
        result = search_functions[algorithm](self.start, self.goal)

        if not result.path:
            self.status.config(
                text=f"{algorithm}: no path found after {len(result.visited)} nodes"
            )
        else:
            self.status.config(
                text=(
                    f"{algorithm}: exploring {len(result.visited)} nodes | "
                    f"path length: {len(result.path)}"
                )
            )

        self._set_algorithm_buttons("disabled")
        self._animate_result(algorithm, result, 0, False)

    def _animate_result(
        self,
        algorithm: str,
        result: SearchResult,
        index: int,
        drawing_path: bool,
    ) -> None:
        """Color one explored or solution cell per timer tick."""
        cells = result.path if drawing_path else result.visited
        color = PATH_COLOR if drawing_path else EXPLORED_COLOR

        if index < len(cells):
            coordinate = cells[index]
            if coordinate not in (self.start, self.goal):
                self.canvas.itemconfig(self.rectangles[coordinate], fill=color)
            self.animation_id = self.root.after(
                max(1, int(self.delay.get())),
                self._animate_result,
                algorithm,
                result,
                index + 1,
                drawing_path,
            )
            return

        if not drawing_path and result.path:
            self.animation_id = self.root.after(
                200, self._animate_result, algorithm, result, 0, True
            )
            return

        self.animation_id = None
        self._set_algorithm_buttons("normal")
        if result.path:
            self.status.config(
                text=(
                    f"{algorithm} finished | explored: {len(result.visited)} | "
                    f"path length: {len(result.path)}"
                )
            )

    def _cancel_animation(self) -> None:
        """Cancel the active timer, if one exists."""
        if self.animation_id is not None:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self._set_algorithm_buttons("normal" if self.graph else "disabled")

    def _set_algorithm_buttons(self, state: str) -> None:
        """Enable or disable every search button."""
        for button in self.algorithm_buttons:
            button.config(state=state)


def main() -> None:
    """Start the graphical maze solver."""
    root = tk.Tk()
    MazeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
