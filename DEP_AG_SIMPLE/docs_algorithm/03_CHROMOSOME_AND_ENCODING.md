# Cromosoma y codificacion

## Codificacion matricial

El cromosoma se representa con `PyChromosome` como una matriz:

```text
filas    = etapas de planeamiento
columnas = lineas
valor    = opcion de linea
```

Ejemplo:

```python
[
    [0, 0, -1, 1],
    [0, 1,  2, 1],
    [1, 1,  2, 3],
]
```

| Elemento | Significado |
|---|---|
| Fila | Decisiones de todas las lineas en una etapa. |
| Gen `[i][j]` | Opcion seleccionada para la linea `j` en la etapa `i`. |
| `-1` | Linea apagada/no instalada/removida. |
| `0, 1, 2, ...` | Opciones tecnicas del catalogo. |

Las columnas se ordenan con `sorted(data['line_catalog'].keys())`.

## `valid_options_by_line`

`data['valid_options_by_line']` define las opciones permitidas por linea. Se construye desde `line_valid_options.csv` y se usa en poblacion inicial, mutacion, reparacion y validacion de costos.

## `PyChromosome`

| Metodo | Funcion |
|---|---|
| `copy()` | Devuelve una copia profunda del cromosoma. |
| `to_key()` | Convierte la matriz en una clave textual unica. |
| `n_stages()` | Numero de filas/etapas. |
| `n_genes()` | Numero de columnas/lineas. |
| `print_chromosome()` | Imprime una tabla del cromosoma. |

## Cache con `to_key()`

`PyPlanningProblem` usa `chromosome.to_key()` como clave de cache. Si un cromosoma ya fue evaluado, retorna el `PyEvaluationResult` guardado sin recalcular topologia, costos, DSS ni fitness.

Ejemplo:

```text
0_1_-1_2__0_1_0_2__1_2_0_3
```
