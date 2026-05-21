# Reportes y graficos

## Carpetas

Los reportes y graficos se generan en:

```text
outputs/ga_reports/
outputs/ga_plots/
outputs/topology_debug/
```

## CSVs

| Archivo real | Contenido |
|---|---|
| `ga_history.csv` | Historico por iteracion. |
| `ga_evaluations.csv` | Todas las evaluaciones guardadas del AG. |

Nota: la solicitud menciona `all_ga_evaluations.csv`; en el codigo actual el archivo se llama `ga_evaluations.csv`.

### `ga_history.csv`

Columnas: `iteration`, `best_fitness`, `mean_fitness`, `global_best_fitness`, `feasible_count`, `population_size`.

### `ga_evaluations.csv`

Guarda fitness, costos, penalidad, factibilidad, componentes normalizados, estado topologico, reparacion, perdidas diarias y clave del cromosoma.

## Graficos reales implementados

| Archivo real | Significado |
|---|---|
| `ga_fitness_evolution.png` | Evolucion del mejor fitness, fitness promedio y mejor global. |
| `ga_feasible_count.png` | Numero de individuos factibles por iteracion. |
| `ga_cost_comparison.png` | Comparacion entre costo de inversion VP, costo de perdidas VP y fitness por color. |

## Relacion con nombres esperados

| Nombre esperado | Estado en el codigo actual |
|---|---|
| `ga_convergence.png` | Implementado con el nombre `ga_fitness_evolution.png`. |
| `cost_fitness_comparison.png` | Parcialmente representado por `ga_cost_comparison.png`. |
| `investment_vs_fitness.png` | No existe como archivo separado. |
| `electrical_losses_vs_fitness.png` | No existe como archivo separado. |
| `cinv_cele_fitness_3d.png` | No implementado. |

## Escala logaritmica

`PyGAReport.plot_fitness_evolution()` puede usar escala logaritmica cuando `use_log_scale_for_fitness_plots=True`. Esto ayuda cuando las penalidades son muy grandes.

## Debug topologico

Si `use_topology_debug_plots=True`, `PyTopologyDebugPlot` genera `best_solution_stage_n.png` y `best_solution_stage_n_no_labels.png` por etapa.
