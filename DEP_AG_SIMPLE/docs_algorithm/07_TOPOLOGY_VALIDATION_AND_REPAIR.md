# Validacion y reparacion topologica

## Clases

| Clase | Responsabilidad |
|---|---|
| `PyTopologyValidator` | Evalua si cada etapa tiene una topologia valida. |
| `PyTopologyRepair` | Intenta corregir cromosomas antes de calcular fitness. |

## Construccion del grafo NetworkX

La red se modela como grafo no dirigido:

```text
nodos  = barras
aristas = lineas activas
opcion -1 = linea apagada
```

Si un gen es distinto de `-1`, se agrega una arista entre `bar_1` y `bar_2`.

## Validaciones

| Validacion | Descripcion |
|---|---|
| Ciclos | Usa `nx.cycle_basis(graph)`. |
| Componentes sin fuente | Componentes conectadas que no contienen fuente. |
| Cargas aisladas | Barras con carga fuera del grafo o en componente sin fuente. |
| Multiples fuentes | Componentes con mas de una fuente, salvo que se permita. |

## `collapse_sources`

Si `collapse_sources=True`, todas las `SE_*` se interpretan como una fuente equivalente (`equivalent_source_name`). Si `collapse_sources=False`, cada fuente se analiza por separado.

## Reparacion

`PyTopologyRepair.repair()` trabaja sobre una copia del cromosoma, etapa por etapa:

1. Reconecta componentes sin fuente activando lineas apagadas.
2. Remueve lineas en ciclos.
3. Separa multiples fuentes si las fuentes no estan colapsadas.
4. Repite hasta que la etapa sea valida o hasta `repair_max_iterations`.

## Variables importantes

| Variable | Efecto |
|---|---|
| `use_topology_repair` | Activa/desactiva reparacion antes del fitness. |
| `use_reconnection_repair` | Permite reconectar componentes sin fuente. |
| `use_cycle_repair` | Permite remover lineas para romper ciclos. |
| `use_multiple_sources_repair` | Permite separar componentes con multiples fuentes. |
| `repair_strategy` | `random` elige candidatos aleatorios; otra estrategia usa criterios de costo. |
| `repair_only_removable_lines` | Restringe remocion a lineas con `-1` como opcion valida. |
| `repair_allow_remove_non_candidate` | Si es `True`, permite remover aunque la linea no sea candidata removible. |

## Efecto sobre el AG

El cromosoma reparado reemplaza al original dentro de `PyEvaluationResult`. `PySimpleGA` usa `result.chromosome`, por lo que la solucion reparada pasa a la siguiente generacion.
