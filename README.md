# A-maze-ing Challenge

Solucionador de laberintos en Python con DFS, BFS y A*, acompañado de una
interfaz gráfica mínima hecha únicamente con `tkinter`.

## Ejecutar la interfaz

Desde la raíz del proyecto:

```bash
python3 -m src.Maze_solver.main
```

Pulsa **Load maze**, selecciona un archivo `.txt` y luego elige **BFS**, **DFS**
o **A\***. Las celdas azules representan nodos explorados y las amarillas la
ruta solución. El control **Delay** cambia la velocidad de la animación.

## Formato del archivo

La primera línea es la coordenada de la meta (con índices desde cero), no las
dimensiones. Las demás líneas forman la matriz:

- `0`: espacio libre
- `1`: pared
- `2`: salida o inicio
- `3`: meta

Ejemplo:

```text
(2, 2)
[2, 0, 1]
[1, 0, 1]
[0, 0, 3]
```

El lector también acepta que la posición indicada en la primera línea contenga
un `0`; en ese caso la convierte en la meta. La matriz debe ser rectangular y
contener exactamente un inicio.

## Ejecutar las pruebas

```bash
python3 -m unittest discover -s tests -v
```
