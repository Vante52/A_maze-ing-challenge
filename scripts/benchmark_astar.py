"""Benchmark A* on the normal graph and the weighted maze macro graph.

Run from the project root with::

    python3 scripts/benchmark_astar.py

The script reads every ``.txt`` file in ``mazes`` and writes one CSV for each
graph representation in ``results``.
"""

from __future__ import annotations

import argparse
import csv
import gc
import statistics
import sys
from pathlib import Path
from time import perf_counter_ns
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.Maze_solver.graph.grafo import Coordinate, Grafo
from src.Maze_solver.graph.maze_to_graph import (
    WALKABLE_VALUES,
    expandMacroPath,
    mazeToGraph,
    mazeToMacroGraph,
    mazeToMatrix,
)


GraphBuilder = Callable[
    [list[list[int]]], tuple[Grafo, Coordinate, Coordinate]
]

CSV_FIELDS = [
    "nombre_laberinto",
    "tipo_grafo",
    "filas",
    "columnas",
    "celdas_transitables",
    "nodos_grafo",
    "aristas_no_dirigidas",
    "grado_promedio",
    "peso_promedio_arista",
    "peso_maximo_arista",
    "reduccion_nodos_porcentaje",
    "nodos_expandidos_astar",
    "porcentaje_grafo_expandido",
    "nodos_ruta_compacta",
    "coordenadas_ruta_completa",
    "pasos_ruta",
    "costo_ruta",
    "tiempo_construccion_ms",
    "tiempo_astar_promedio_ms",
    "tiempo_astar_mediana_ms",
    "desviacion_tiempo_astar_ms",
    "tiempo_expansion_ruta_ms",
    "tiempo_total_promedio_ms",
    "repeticiones_astar",
    "estado",
    "error",
]


def elapsed_milliseconds(start_ns: int) -> float:
    """Return the milliseconds elapsed since a performance-counter reading."""
    return (perf_counter_ns() - start_ns) / 1_000_000


def path_cost(graph: Grafo, path: list[Coordinate]) -> int:
    """Return the sum of the weights along a graph path."""
    return sum(
        graph.obtener_peso(parent, child)
        for parent, child in zip(path, path[1:])
    )


def benchmark_graph(
    maze_name: str,
    maze: list[list[int]],
    graph_type: str,
    builder: GraphBuilder,
    repetitions: int,
    expand_path: bool,
) -> dict[str, object]:
    """Measure graph construction, A* search, and optional path expansion."""
    gc.collect()
    build_start = perf_counter_ns()
    graph, start, goal = builder(maze)
    build_time_ms = elapsed_milliseconds(build_start)

    search_times_ms = []
    result = None
    for _ in range(repetitions):
        search_start = perf_counter_ns()
        result = graph.a_star_search_details(start, goal)
        search_times_ms.append(elapsed_milliseconds(search_start))

    if result is None:
        raise RuntimeError("A* was not executed.")

    expansion_time_ms = 0.0
    complete_path = result.path
    if expand_path and result.path:
        expansion_start = perf_counter_ns()
        complete_path = expandMacroPath(maze, result.path)
        expansion_time_ms = elapsed_milliseconds(expansion_start)

    node_count = len(graph.lista_adyacencia)
    directed_edge_count = sum(
        len(neighbours) for neighbours in graph.lista_adyacencia.values()
    )
    undirected_edge_count = directed_edge_count // 2
    directed_weights = list(graph.pesos_aristas.values())
    walkable_count = sum(
        cell in WALKABLE_VALUES for row in maze for cell in row
    )
    route_cost = path_cost(graph, result.path) if result.path else ""
    route_steps = len(complete_path) - 1 if complete_path else ""
    search_mean_ms = statistics.fmean(search_times_ms)

    if expand_path and result.path and route_cost != route_steps:
        raise ValueError(
            "The expanded path length does not match the macro-graph cost."
        )

    return {
        "nombre_laberinto": maze_name,
        "tipo_grafo": graph_type,
        "filas": len(maze),
        "columnas": len(maze[0]),
        "celdas_transitables": walkable_count,
        "nodos_grafo": node_count,
        "aristas_no_dirigidas": undirected_edge_count,
        "grado_promedio": round(directed_edge_count / node_count, 6)
        if node_count
        else 0,
        "peso_promedio_arista": round(statistics.fmean(directed_weights), 6)
        if directed_weights
        else 0,
        "peso_maximo_arista": max(directed_weights, default=0),
        "reduccion_nodos_porcentaje": round(
            100 * (1 - node_count / walkable_count), 6
        )
        if walkable_count
        else 0,
        "nodos_expandidos_astar": len(result.visited),
        "porcentaje_grafo_expandido": round(
            100 * len(result.visited) / node_count, 6
        )
        if node_count
        else 0,
        "nodos_ruta_compacta": len(result.path),
        "coordenadas_ruta_completa": len(complete_path),
        "pasos_ruta": route_steps,
        "costo_ruta": route_cost,
        "tiempo_construccion_ms": round(build_time_ms, 6),
        "tiempo_astar_promedio_ms": round(search_mean_ms, 6),
        "tiempo_astar_mediana_ms": round(
            statistics.median(search_times_ms), 6
        ),
        "desviacion_tiempo_astar_ms": round(
            statistics.pstdev(search_times_ms), 6
        ),
        "tiempo_expansion_ruta_ms": round(expansion_time_ms, 6),
        "tiempo_total_promedio_ms": round(
            build_time_ms + search_mean_ms + expansion_time_ms, 6
        ),
        "repeticiones_astar": repetitions,
        "estado": "ok" if result.path else "sin_ruta",
        "error": "",
    }


def error_row(
    maze_name: str, graph_type: str, repetitions: int, error: Exception
) -> dict[str, object]:
    """Create a CSV row for a maze that could not be benchmarked."""
    row: dict[str, object] = {field: "" for field in CSV_FIELDS}
    row.update(
        {
            "nombre_laberinto": maze_name,
            "tipo_grafo": graph_type,
            "repeticiones_astar": repetitions,
            "estado": "error",
            "error": str(error),
        }
    )
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    """Write benchmark rows as a UTF-8 CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmarks(
    mazes_directory: Path, output_directory: Path, repetitions: int
) -> tuple[Path, Path]:
    """Benchmark every maze and create the normal and macro CSV files."""
    if repetitions < 1:
        raise ValueError("The number of repetitions must be at least one.")

    maze_paths = sorted(
        mazes_directory.glob("*.txt"),
        key=lambda path: (path.stat().st_size, path.name),
    )
    if not maze_paths:
        raise ValueError(f"No .txt mazes found in {mazes_directory}.")

    normal_rows = []
    macro_rows = []
    normal_csv = output_directory / "astar_grafo_normal.csv"
    macro_csv = output_directory / "astar_macrografo.csv"

    for maze_path in maze_paths:
        print(f"Benchmarking {maze_path.name}...", flush=True)
        try:
            maze = mazeToMatrix(maze_path)
        except (OSError, ValueError) as error:
            normal_rows.append(
                error_row(maze_path.name, "normal", repetitions, error)
            )
            macro_rows.append(
                error_row(maze_path.name, "macro", repetitions, error)
            )
            write_csv(normal_csv, normal_rows)
            write_csv(macro_csv, macro_rows)
            continue

        try:
            normal_rows.append(
                benchmark_graph(
                    maze_path.name,
                    maze,
                    "normal",
                    mazeToGraph,
                    repetitions,
                    False,
                )
            )
        except (MemoryError, RuntimeError, ValueError) as error:
            normal_rows.append(
                error_row(maze_path.name, "normal", repetitions, error)
            )

        gc.collect()

        try:
            macro_rows.append(
                benchmark_graph(
                    maze_path.name,
                    maze,
                    "macro",
                    mazeToMacroGraph,
                    repetitions,
                    True,
                )
            )
        except (MemoryError, RuntimeError, ValueError) as error:
            macro_rows.append(
                error_row(maze_path.name, "macro", repetitions, error)
            )

        gc.collect()
        write_csv(normal_csv, normal_rows)
        write_csv(macro_csv, macro_rows)

    return normal_csv, macro_csv


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Compare A* on normal and macro maze graphs."
    )
    parser.add_argument(
        "--mazes-dir",
        type=Path,
        default=PROJECT_ROOT / "mazes",
        help="Directory containing maze .txt files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results",
        help="Directory where both CSV files will be written.",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Number of A* timing repetitions per graph (default: 1).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the benchmark from the command line."""
    args = parse_args()
    normal_csv, macro_csv = run_benchmarks(
        args.mazes_dir, args.output_dir, args.repetitions
    )
    print(f"Normal graph CSV: {normal_csv}")
    print(f"Macro graph CSV: {macro_csv}")


if __name__ == "__main__":
    main()
