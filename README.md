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

La primera línea puede ser la coordenada de la meta (con índices desde cero) o
las dimensiones de la matriz. Las demás líneas forman la matriz:

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

Cuando la primera línea es una coordenada, el lector también acepta que esa
posición contenga un `0`; en ese caso la convierte en la meta. Cuando la
primera línea coincide con las dimensiones reales, la meta debe estar marcada
con un `3` dentro de la matriz. La matriz debe ser rectangular y contener
exactamente un inicio y una meta.

## Ejecutar las pruebas

```bash
python3 -m unittest discover -s tests -v
```

## Flujo completo del programa

El recorrido general de la información dentro de la aplicación es:

```text
El usuario selecciona un archivo
              |
              v
      mazeToMatrix(file_path)
              |
              v
   Matriz rectangular list[list[int]]
              |
              v
         mazeToGraph(maze)
              |
              v
 Grafo + coordenada inicial + coordenada meta
              |
              v
          DFS / BFS / A*
              |
              v
     SearchResult(visited, path)
              |
              v
 Animacion: explorados en azul y ruta en amarillo
```

Los archivos que participan principalmente en este flujo son:

- [`src/Maze_solver/main.py`](src/Maze_solver/main.py): interfaz, selección del
  archivo, ejecución del algoritmo y animación.
- [`src/Maze_solver/graph/maze_to_graph.py`](src/Maze_solver/graph/maze_to_graph.py):
  lectura, validación y transformación del laberinto.
- [`src/Maze_solver/graph/grafo.py`](src/Maze_solver/graph/grafo.py): estructura
  del grafo y algoritmos DFS, BFS y A*.
- [`mazes/laberinto.txt`](mazes/laberinto.txt): laberinto de ejemplo.

### 1. Inicio de la aplicación

Al ejecutar el módulo, se llama a la función `main`:

```python
def main() -> None:
    root = tk.Tk()
    MazeApp(root)
    root.mainloop()
```

Cada instrucción tiene una responsabilidad diferente:

1. `tk.Tk()` crea la ventana principal.
2. `MazeApp(root)` crea los botones, etiquetas, canvas y variables de estado.
3. `root.mainloop()` mantiene la aplicación esperando eventos, como clics,
   redimensionamientos y temporizadores.

Inicialmente todavía no se ha cargado información:

```python
self.maze = []
self.graph = None
self.start = None
self.goal = None
```

Por esa razón, los botones `BFS`, `DFS` y `A*` empiezan deshabilitados. Solo se
habilitan después de leer y validar correctamente un laberinto.

### 2. Selección del archivo

Al pulsar **Load maze**, Tkinter ejecuta el método `load_maze`:

```python
file_path = filedialog.askopenfilename(
    title="Select maze file",
    filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
)
```

Si el usuario cierra el selector sin escoger un archivo, `file_path` queda
vacío y el método termina sin modificar el estado actual:

```python
if not file_path:
    return
```

Si se selecciona un archivo, se realizan dos transformaciones consecutivas:

```python
maze = mazeToMatrix(file_path)
graph, start, goal = mazeToGraph(maze)
```

Primero se crea la matriz y después se crea el grafo. Si alguno de los pasos
lanza un `ValueError`, la interfaz muestra el mensaje correspondiente y no
permite ejecutar los algoritmos con datos inválidos.

### 3. Lectura del archivo y creación de la matriz

La función `mazeToMatrix`, definida en `maze_to_graph.py`, recibe la ruta del
archivo:

```python
path = Path(file_path)
```

Luego abre el archivo en modo lectura, elimina espacios exteriores y saltos de
línea e ignora las líneas vacías:

```python
with path.open("r", encoding="utf-8") as file:
    lines = [line.strip() for line in file if line.strip()]
```

Para el archivo incluido, la estructura conceptual de `lines` es:

```python
lines = [
    "(17,17)",
    "[2, 1, 0, ...]",
    "[0, 0, 1, ...]",
    # ...
]
```

La primera línea no es una fila de la matriz. Puede ser la coordenada de la
meta o las dimensiones. Las demás líneas sí representan las filas del
laberinto:

```python
header_value = literal_eval(lines[0])
maze = [list(literal_eval(line)) for line in lines[1:]]
```

En `laberinto.txt`, lo anterior produce:

```python
header_value = (17, 17)

maze = [
    [2, 1, 0, 0, ...],  # fila 0
    [0, 0, 1, 0, ...],  # fila 1
    # ...
]
```

Se utiliza `literal_eval` porque permite interpretar literales como tuplas,
listas y enteros sin ejecutar código arbitrario como lo haría `eval`.

Las coordenadas se representan siempre en el orden:

```text
(fila, columna)
```

Por ejemplo, `maze[17][17]` accede a la fila 17 y a la columna 17. Tanto las
filas como las columnas comienzan en cero.

Los valores permitidos son:

| Valor | Significado | ¿Es transitable? |
|---:|---|:---:|
| `0` | Espacio libre | Sí |
| `1` | Pared | No |
| `2` | Inicio | Sí |
| `3` | Meta | Sí |

El lector verifica que:

- Existan la primera línea y al menos una fila de la matriz.
- La primera línea sea una tupla con dos enteros.
- La matriz no esté vacía.
- Todas las filas tengan el mismo número de columnas.
- Todas las celdas contengan únicamente `0`, `1`, `2` o `3`.
- Exista exactamente una celda inicial marcada con `2`.
- La meta esté dentro de los límites de la matriz.
- La meta no corresponda a una pared.
- Si la primera línea contiene dimensiones, exista exactamente una celda `3`.
- Si contiene una coordenada, una celda marcada con `3` coincida con ella.

Para localizar las celdas especiales se usa `_find_cells`:

```python
return [
    (row, column)
    for row, values in enumerate(maze)
    for column, cell in enumerate(values)
    if cell == value
]
```

La comprensión recorre cada fila y cada columna y guarda las coordenadas de las
celdas que contienen el valor solicitado.

Si la cabecera no coincide con las dimensiones, se interpreta como coordenada
de meta y se considera autoritativa:

```python
maze[goal[0]][goal[1]] = 3
```

Esto significa que, aunque `(17, 17)` contenga inicialmente un `0`, esa celda
se convierte en la meta. Si la cabecera coincide con las dimensiones reales,
por ejemplo `(101, 101)` para una matriz de 101 por 101, la meta se obtiene de
la única celda marcada con `3`. Para el archivo original, el resultado es:

```text
Dimensiones: 34 filas x 34 columnas
Inicio:      (0, 0)
Meta:        (17, 17)
```

### 4. Conversión de la matriz en un grafo

Los algoritmos no buscan directamente sobre la matriz. La función
`mazeToGraph` convierte primero cada celda transitable en un nodo y cada
movimiento válido en una arista.

El grafo utiliza una lista de adyacencia:

```python
self.lista_adyacencia: dict[Coordinate, set[Coordinate]] = {}
```

Una versión reducida podría tener esta forma:

```python
{
    (0, 0): {(1, 0)},
    (1, 0): {(0, 0), (1, 1)},
    (1, 1): {(1, 0), (2, 1)},
}
```

Cada clave es una celda transitable y el conjunto asociado contiene sus
vecinos accesibles.

La matriz se recorre de izquierda a derecha y de arriba abajo:

```python
for row in range(row_count):
    for column in range(column_count):
```

Las paredes se ignoran:

```python
if maze[row][column] not in WALKABLE_VALUES:
    continue
```

Para una celda transitable se crea una coordenada y se registra el nodo:

```python
current = (row, column)
graph.add_node(current)
```

Después se prueban los cuatro movimientos ortogonales:

```python
for next_row, next_column in (
    (row - 1, column),  # arriba
    (row, column + 1),  # derecha
    (row + 1, column),  # abajo
    (row, column - 1),  # izquierda
):
```

Antes de consultar la matriz se comprueba que el vecino no se salga de sus
límites:

```python
inside_maze = (
    0 <= next_row < row_count
    and 0 <= next_column < column_count
)
```

Si está dentro y es transitable, se crea la arista:

```python
if inside_maze and maze[next_row][next_column] in WALKABLE_VALUES:
    graph.add_edge(current, (next_row, next_column))
```

#### Ejemplo con la celda inicial

La celda `(0, 0)` contiene el inicio. Sus cuatro posibles vecinos son:

```text
Arriba:    (-1, 0) -> fuera de la matriz
Derecha:   (0, 1)  -> pared
Abajo:     (1, 0)  -> transitable
Izquierda: (0, -1) -> fuera de la matriz
```

Por tanto, inicialmente se crea:

```python
(0, 0) -> {(1, 0)}
```

Aunque `add_edge` registra formalmente una arista dirigida, cada celda se
procesa por separado. Cuando se procesa `(1, 0)`, se crea también la conexión
inversa hacia `(0, 0)`. De esta manera, los movimientos del laberinto quedan
disponibles en ambos sentidos.

Para el laberinto incluido se generan:

```text
698 nodos transitables
1410 aristas dirigidas
```

### 5. Resultado de una búsqueda

Los métodos detallados de los tres algoritmos devuelven un `SearchResult`:

```python
@dataclass
class SearchResult:
    visited: list[Coordinate]
    path: list[Coordinate]
```

Las dos listas tienen propósitos diferentes:

- `visited` guarda el orden en que se procesaron los nodos. Se usa para pintar
  la exploración en azul.
- `path` guarda únicamente la ruta final desde el inicio hasta la meta. Se usa
  para pintar la solución en amarillo.

Un nodo puede aparecer en `visited` y no aparecer en `path`: fue explorado,
pero pertenecía a una rama que finalmente no formó parte de la solución.

### 6. Recorrido DFS

La búsqueda en profundidad comienza con:

```python
stack = [start]
discovered = {start}
parents = {start: None}
visited = []
```

DFS utiliza una pila: el último nodo que entra es el primero que sale.

```python
current = stack.pop()
visited.append(current)
```

Después registra los vecinos todavía no descubiertos:

```python
for neighbour in sorted(self.obtener_vecinos(current), reverse=True):
    if neighbour not in discovered:
        discovered.add(neighbour)
        parents[neighbour] = current
        stack.append(neighbour)
```

Los vecinos se ordenan en reversa porque `pop()` invierte nuevamente el orden
efectivo. El conjunto `discovered` evita introducir varias veces el mismo nodo
en la pila.

DFS profundiza todo lo posible por una rama antes de probar otra. Encuentra una
ruta cuando existe, pero no garantiza que sea la más corta.

En `laberinto.txt`, DFS visita 414 nodos y devuelve una ruta de 301 nodos, es
decir, 300 movimientos.

### 7. Recorrido BFS

BFS cambia la pila por una cola:

```python
queue = deque([start])
```

En cada iteración extrae el nodo que lleva más tiempo esperando:

```python
current = queue.popleft()
visited.append(current)
```

Los vecinos nuevos se añaden al final:

```python
queue.append(neighbour)
```

Esto hace que BFS explore por niveles:

```text
Distancia 0 -> inicio
Distancia 1 -> vecinos del inicio
Distancia 2 -> vecinos de los vecinos
...
```

Como todos los movimientos cuestan uno, la primera vez que BFS procesa la meta
ha encontrado una ruta mínima. En el laberinto incluido visita 147 nodos y
devuelve una ruta de 65 nodos, equivalente a 64 movimientos.

## Funcionamiento detallado de A*

A* combina el costo que ya se ha pagado con una estimación del costo restante:

```text
f(n) = g(n) + h(n)
```

- `g(n)` es el costo real desde el inicio hasta el nodo `n`.
- `h(n)` es una estimación desde `n` hasta la meta.
- `f(n)` es el costo total estimado de una solución que pasa por `n`.

### Heurística Manhattan

La función `h` calcula la distancia Manhattan:

```python
def h(self, current: Coordinate, goal: Coordinate) -> int:
    return abs(current[0] - goal[0]) + abs(current[1] - goal[1])
```

Para el inicio `(0, 0)` y la meta `(17, 17)`:

```text
h(0, 0) = |0 - 17| + |0 - 17|
        = 17 + 17
        = 34
```

Manhattan ignora las paredes y calcula cuántos movimientos serían necesarios
si se pudiera avanzar directamente. Por eso es una estimación inferior: la
ruta real puede ser más larga, pero nunca más corta que esta distancia cuando
solo se permiten movimientos ortogonales de costo uno.

### Inicialización de A*

El método `a_star_search_details` empieza así:

```python
open_nodes = {start}
closed_nodes: set[Coordinate] = set()
parents: dict[Coordinate, Optional[Coordinate]] = {start: None}
real_cost = {start: 0}
visited = []
```

Con el laberinto incluido, el estado inicial es:

```python
open_nodes = {(0, 0)}
closed_nodes = set()
parents = {(0, 0): None}
real_cost = {(0, 0): 0}
visited = []
```

Cada variable representa lo siguiente:

- `open_nodes`: nodos descubiertos pero todavía pendientes de procesar.
- `closed_nodes`: nodos que ya fueron procesados.
- `parents`: mejor predecesor conocido de cada nodo.
- `real_cost`: costo real `g(n)` conocido para cada nodo.
- `visited`: orden definitivo de procesamiento usado por la animación.

### Primera iteración, instrucción por instrucción

El ciclo continúa mientras exista al menos un candidato pendiente:

```python
while open_nodes:
```

Como `open_nodes` contiene `(0, 0)`, se entra al ciclo. A continuación se busca
el nodo con menor `f = g + h`:

```python
current = min(
    open_nodes,
    key=lambda node: (real_cost[node] + self.h(node, goal), node),
)
```

Solo hay un candidato:

| Nodo | `g` | `h` | `f` |
|---|---:|---:|---:|
| `(0, 0)` | 0 | 34 | 34 |

Por tanto, `current = (0, 0)`. El segundo elemento de la clave, `node`, se usa
como desempate determinista cuando dos nodos tienen el mismo `f`.

El nodo seleccionado sale del conjunto de abiertos y entra en el orden de
visita:

```python
open_nodes.remove(current)
visited.append(current)
```

El estado se convierte en:

```python
open_nodes = set()
visited = [(0, 0)]
```

Luego se comprueba si ya se llegó a la meta:

```python
if current == goal:
    return SearchResult(visited, self._build_path(parents, goal))
```

Como `(0, 0)` no es `(17, 17)`, el nodo se marca como cerrado:

```python
closed_nodes.add(current)
```

Ahora `closed_nodes = {(0, 0)}`. Después se recorren ordenadamente sus vecinos:

```python
for neighbour in sorted(self.obtener_vecinos(current)):
```

El único vecino de `(0, 0)` es `(1, 0)`. Primero se evita regresar a nodos ya
cerrados:

```python
if neighbour in closed_nodes:
    continue
```

Como `(1, 0)` todavía no está cerrado, se calcula el costo de llegar a él. Cada
arista cuesta una unidad:

```python
new_cost = real_cost[current] + 1
```

En este caso:

```text
new_cost = g(0, 0) + 1 = 0 + 1 = 1
```

Finalmente se determina si el vecino es nuevo o si se encontró una ruta más
barata hacia él:

```python
if neighbour not in real_cost or new_cost < real_cost[neighbour]:
    real_cost[neighbour] = new_cost
    parents[neighbour] = current
    open_nodes.add(neighbour)
```

Como `(1, 0)` es nuevo, el estado al terminar la primera iteración es:

```python
open_nodes = {(1, 0)}
closed_nodes = {(0, 0)}
visited = [(0, 0)]
parents = {
    (0, 0): None,
    (1, 0): (0, 0),
}
real_cost = {
    (0, 0): 0,
    (1, 0): 1,
}
```

### Primeras decisiones reales de A*

Las primeras iteraciones sobre `laberinto.txt` son:

| Iteración | Nodo elegido | `g` | `h` | `f` |
|---:|---|---:|---:|---:|
| 1 | `(0, 0)` | 0 | 34 | 34 |
| 2 | `(1, 0)` | 1 | 33 | 34 |
| 3 | `(1, 1)` | 2 | 32 | 34 |
| 4 | `(2, 1)` | 3 | 31 | 34 |
| 5 | `(2, 2)` | 4 | 30 | 34 |
| 6 | `(3, 2)` | 5 | 29 | 34 |
| 7 | `(3, 3)` | 6 | 28 | 34 |
| 8 | `(4, 3)` | 7 | 27 | 34 |
| 9 | `(4, 4)` | 8 | 26 | 34 |
| 10 | `(4, 5)` | 9 | 25 | 34 |
| 11 | `(3, 5)` | 10 | 26 | 36 |
| 12 | `(3, 6)` | 11 | 25 | 36 |
| 13 | `(2, 6)` | 12 | 26 | 38 |
| 14 | `(2, 7)` | 13 | 25 | 38 |
| 15 | `(2, 8)` | 14 | 24 | 38 |
| 16 | `(3, 8)` | 15 | 23 | 38 |
| 17 | `(4, 8)` | 16 | 22 | 38 |
| 18 | `(1, 7)` | 14 | 26 | 40 |

Durante el primer corredor solo existe una alternativa válida, por lo que A*
avanza de forma continua. El valor `f` aumenta cuando una pared obliga a tomar
un desvío que no reduce suficientemente `h`.

### Primera bifurcación importante

Al procesar `(2, 7)`, sus vecinos relevantes son:

```text
(1, 7) -> transitable y todavía no visitado
(2, 6) -> ya cerrado
(2, 8) -> transitable y todavía no visitado
```

A los dos vecinos nuevos se llega con `g = 14`, pero sus evaluaciones son:

```text
(1, 7): g=14, h=26, f=40
(2, 8): g=14, h=24, f=38
```

A* selecciona `(2, 8)` porque `38 < 40`. El nodo `(1, 7)` no se descarta:
permanece en `open_nodes` como una alternativa pendiente.

Después de procesar `(4, 8)`, aparecen dos candidatos con el mismo valor:

```text
(1, 7): g=14, h=26, f=40
(4, 7): g=17, h=23, f=40
```

El código desempata por coordenada usando la clave `(f, node)`. Como `(1, 7)`
es menor lexicográficamente que `(4, 7)`, se procesa primero `(1, 7)`.

Esto también explica por qué la animación azul puede saltar entre ramas. A* no
se mueve físicamente desde el último nodo coloreado: en cada iteración elige
globalmente el mejor nodo que siga pendiente.

### Actualización de costos y padres

La condición de actualización es:

```python
if neighbour not in real_cost or new_cost < real_cost[neighbour]:
```

Un vecino se actualiza cuando nunca había sido descubierto o cuando aparece
una ruta más barata. Por ejemplo, si previamente se conocía:

```python
real_cost[(x, y)] = 20
```

y se encuentra un camino con `new_cost = 18`, se reemplazan tanto el costo
como el padre:

```python
real_cost[(x, y)] = 18
parents[(x, y)] = current
```

De esta manera, `parents` conserva el mejor camino conocido y no simplemente
el primer camino encontrado.

### Llegada a la meta

Las últimas selecciones reales de A* son:

```text
Iteración 98:  (15, 17), g=62, h=2, f=64
Iteración 99:  (16, 9),  g=55, h=9, f=64
Iteración 100: (16, 17), g=63, h=1, f=64
Iteración 101: (17, 9),  g=56, h=8, f=64
Iteración 102: (17, 17), g=64, h=0, f=64
```

Aunque la meta se descubre cuando se procesa `(16, 17)`, A* no termina en ese
instante. El algoritmo finaliza cuando la meta es extraída de `open_nodes` y se
convierte en `current`.

En la iteración 101 todavía existe un empate con `f = 64`. La coordenada
`(17, 9)` gana el desempate frente a `(17, 17)`, por lo que la meta se procesa
en la iteración 102.

Si `open_nodes` se vaciara antes de encontrar la meta, significaría que no hay
una ruta alcanzable y el método devolvería `SearchResult(visited, [])`.

### Reconstrucción de la ruta

Al seleccionar la meta se llama a `_build_path`:

```python
path = []
current = goal

while current is not None:
    path.append(current)
    current = parents[current]

path.reverse()
return path
```

Los padres se recorren inicialmente desde la meta hacia el inicio:

```text
(17, 17)
<- (16, 17)
<- (15, 17)
<- (15, 16)
<- ...
<- (1, 0)
<- (0, 0)
<- None
```

Como esta secuencia está invertida, `path.reverse()` la convierte en una ruta
desde el inicio hasta la meta. La parte final de la solución de A* es:

```text
(13, 13)
-> (13, 14)
-> (13, 15)
-> (14, 15)
-> (14, 16)
-> (15, 16)
-> (15, 17)
-> (16, 17)
-> (17, 17)
```

### Comparación de los recorridos

Los resultados para `mazes/laberinto.txt` son:

| Algoritmo | Nodos explorados | Nodos en la ruta | Movimientos | ¿Ruta mínima? |
|---|---:|---:|---:|:---:|
| DFS | 414 | 301 | 300 | No |
| BFS | 147 | 65 | 64 | Sí |
| A* | 102 | 65 | 64 | Sí |

BFS y A* encuentran una ruta del mismo tamaño. A* procesa menos nodos porque
la heurística Manhattan orienta la búsqueda hacia la meta. DFS encuentra una
ruta mucho más larga porque profundiza por una rama sin comparar distancias ni
costos globales.

### 8. Ejecución y animación en la interfaz

Al pulsar el botón de un algoritmo, `start_search` selecciona el método
correspondiente:

```python
search_functions = {
    "BFS": self.graph.breadth_first_search_details,
    "DFS": self.graph.depth_first_search_details,
    "A*": self.graph.a_star_search_details,
}

result = search_functions[algorithm](self.start, self.goal)
```

El algoritmo se ejecuta completamente antes de comenzar la animación. La
interfaz no observa la búsqueda en tiempo real; recibe las listas terminadas y
las reproduce después.

`_animate_result` selecciona cuál lista y color debe utilizar:

```python
cells = result.path if drawing_path else result.visited
color = PATH_COLOR if drawing_path else EXPLORED_COLOR
```

La animación tiene dos fases:

1. Recorre `result.visited` y pinta cada nodo explorado de azul.
2. Si se encontró una solución, recorre `result.path` y la pinta de amarillo.

Cada celda se programa mediante `root.after`:

```python
self.root.after(
    max(1, int(self.delay.get())),
    self._animate_result,
    algorithm,
    result,
    index + 1,
    drawing_path,
)
```

El control **Delay** modifica el tiempo entre dos celdas de la animación, pero
no cambia las decisiones ni el tiempo de cálculo interno del algoritmo.

En conclusión, las celdas azules muestran todo lo que el algoritmo procesó y
las celdas amarillas muestran únicamente la cadena de padres que conecta el
inicio `(0, 0)` con la meta `(17, 17)`.
