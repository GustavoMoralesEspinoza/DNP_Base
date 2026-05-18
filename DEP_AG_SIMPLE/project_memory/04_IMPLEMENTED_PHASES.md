# Implemented Phases

## FASE 2: lector de datos

Archivo principal: `data/py_data_reader.py`.

Lee CSVs normalizados desde `Initialdata/` y arma `data` con buses, cargas, lineas, opciones validas, catalogo tecnico y validaciones basicas.

## FASE 3: costo de inversion

Archivo principal: `economics/py_investment_cost.py`.

Calcula costo multiestagio comparando estado base, estadio actual y estadio anterior. Maneja instalaciones, reemplazos y remociones.

Incluye `calculate_max_investment_reference()`:

```python
Cinv_max = n_stages * sum(max_cost_by_line)
```

## FASE 4: valor presente

Archivo principal: `economics/py_present_value.py`.

Convierte costos por estadio a valor presente usando `interest_rate` y `stage_years`.

## FASE 5: funcion objetivo simple por pesos

Archivo principal: `economics/py_objective_function.py`.

Calcula:

```python
fitness = w_inv * c_inv_pu + w_ele * c_ele_pu + penalty
```

Soporta `penalty_breakdown`.

## FASE 6: AG simple sin OpenDSS

Carpeta: `genetic_algorithm/`.

Implementa poblacion, seleccion, crossover, mutacion, elitismo y `PySimpleGA`.

## FASE 7: validacion topologica con NetworkX

Archivo principal: `topology/py_topology_validator.py`.

Valida ciclos, componentes sin fuente, cargas aisladas y multiples fuentes. Respeta `collapse_sources`.

## FASE 8: reparacion/reconexion de red

Archivo principal: `topology/py_topology_repair.py`.

Repara por estadio antes de evaluar fitness. El cromosoma reparado reemplaza al original en `PyEvaluationResult.chromosome` y puede pasar a seleccion/elitismo.

## FASE 9: generador DSS

Archivo principal: `dss/py_dss_writer.py`.

Genera archivos `.dss` por estadio a partir de `best_result.chromosome`. No ejecuta OpenDSS.

