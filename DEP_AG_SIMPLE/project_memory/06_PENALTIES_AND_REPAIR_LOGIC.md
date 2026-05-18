# Penalties And Repair Logic

## Penalidades

La funcion objetivo acepta un `penalty_breakdown` con estas claves:

- `invalid_option`
- `warnings`
- `topology_cycle`
- `topology_nodes_in_cycles`
- `topology_isolated_bus`
- `topology_disconnected_load`
- `topology_component_without_source`
- `topology_multiple_sources`
- `extra_penalties`
- `total`

Valores actuales:

- opcion invalida: `1e8`
- componente sin fuente: `1e8`
- carga desconectada: `8e7`
- bus/carga aislada: `7e7`
- ciclo: `5e7`
- nodos en ciclos: `1e7`
- multiples fuentes: `3e7`
- warning general: `0`

Las restricciones criticas deben dominar al costo economico. Los warnings estan actualmente desactivados como penalidad para no castigar remociones validas durante debug.

## Reparacion

La reparacion ocurre antes del calculo final de fitness dentro de `PyPlanningProblem.evaluate()`.

Flujo:

```text
cromosoma original
-> reparacion opcional
-> cromosoma reparado
-> inversion
-> valor presente
-> topologia final
-> funcion objetivo
-> PyEvaluationResult.chromosome = cromosoma reparado
```

El cromosoma reparado debe reemplazar al cromosoma original y pasar a la siguiente generacion via seleccion/elitismo.

## Reconexion

`reconnect_components()` busca lineas apagadas (`-1`) que conecten componentes sin fuente con componentes con fuente. Activa una opcion valida no negativa.

## Reparacion de ciclos

`remove_cycles()` usa `nx.cycle_basis(graph)`. Con `repair_strategy = "random"` elige un ciclo aleatorio y una linea removible aleatoria. Con `cheapest`, remueve preferentemente la linea de mayor costo actual.

## Separacion de fuentes multiples

`separate_multiple_sources()` solo actua si:

```python
collapse_sources == False
allow_multiple_sources_per_component == False
use_multiple_sources_repair == True
```

Busca un camino entre fuentes y apaga una linea del camino.

## `collapse_sources`

Si `collapse_sources=True`, todas las fuentes `SE_*` se interpretan como una fuente equivalente (`SE_1`) en topologia/reparacion. En DSS, si `dss_collapse_sources=True`, se escriben como `sourcebus`.

