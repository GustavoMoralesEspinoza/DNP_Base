# Flujo del algoritmo genetico

## Clases principales

| Clase | Responsabilidad |
|---|---|
| `PySimpleGA` | Coordina el ciclo evolutivo completo. |
| `PyPopulation` | Crea la poblacion inicial aleatoria. |
| `PySelection` | Selecciona padres por torneo. |
| `PyCrossover` | Aplica crossover uniforme. |
| `PyMutation` | Aplica mutacion por gen. |
| `PyElitism` | Conserva los mejores individuos. |

## Paso a paso

1. Crear poblacion inicial con `PyPopulation.create_initial_population()`.
2. Evaluar cada individuo con `PyPlanningProblem.evaluate()`.
3. Identificar el mejor individuo de la iteracion.
4. Actualizar el mejor global.
5. Guardar historicos: mejor fitness, fitness promedio, mejor global, factibles y tamano de poblacion.
6. Aplicar elitismo y copiar los mejores cromosomas.
7. Seleccionar padres por torneo.
8. Aplicar crossover uniforme con probabilidad `crossover_rate`.
9. Aplicar mutacion por gen con probabilidad `mutation_rate`.
10. Formar la nueva generacion.
11. Repetir hasta `n_iterations`.
12. Guardar reportes y graficos si estan habilitados.

## Operadores

La seleccion es por torneo de tamano 3 y escoge el menor fitness. El crossover es uniforme: cada gen se hereda/intercambia con probabilidad 0.5. La mutacion recorre cada gen y, si se activa, selecciona una opcion alternativa valida para la linea.

## Elitismo

`PyElitism.get_elites()` ordena la poblacion evaluada por fitness y conserva:

```text
max(1, int(elitism_rate * n_individuals))
```

## Reparacion dentro del AG

`PyPlanningProblem.evaluate()` puede reparar el cromosoma. Desde ese punto, el AG usa `result.chromosome` como individuo, por lo que el cromosoma reparado puede pasar a seleccion, elitismo y generaciones futuras.

## Historial del AG

| Atributo | Significado |
|---|---|
| `history_best` | Mejor fitness de cada iteracion. |
| `history_mean` | Fitness promedio de cada iteracion. |
| `history_global` | Mejor fitness global acumulado. |
| `history_feasible` | Numero de individuos factibles por iteracion. |
| `history_population_size` | Tamano evaluado por iteracion. |

## Evaluaciones guardadas

`PySimpleGA.record_evaluation()` guarda registros con iteracion, individuo y `PyEvaluationResult`. Luego `PyGAReport` escribe `ga_history.csv` y `ga_evaluations.csv`.
