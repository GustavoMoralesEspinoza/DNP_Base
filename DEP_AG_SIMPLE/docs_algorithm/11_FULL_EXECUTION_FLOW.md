# Flujo completo al ejecutar `python main.py`

## Flujo principal

1. `main.py` imprime el encabezado del proyecto.
2. Crea `PyConfigBase()` con parametros del AG, topologia, DSS, economia y reportes.
3. Define `data_dir = Initialdata`.
4. Crea `PyDataReader(data_dir)` y ejecuta `read_all()`.
5. Lee buses, cargas, curvas, opciones validas y catalogo tecnico de lineas.
6. Valida consistencia basica de lineas, buses y cargas.
7. Crea `PyInvestmentCost` y calcula `config.c_inv_max`.
8. Crea `PyPresentValue`, `PyObjectiveFunction`, `PyDSSWriter`, `PyDSSRunner`, `PyElectricalLossCost`, `PyTopologyValidator` y `PyTopologyRepair`.
9. Crea `PyPlanningProblem(...)` inyectando todos los modulos.
10. Crea `PySimpleGA(config, problem, data)`.
11. Ejecuta `ga.run()`.

## Dentro de `ga.run()`

1. Crear poblacion inicial.
2. Evaluar poblacion.
3. Guardar mejor solucion de la iteracion y mejor global.
4. Guardar historicos.
5. Aplicar elitismo.
6. Seleccionar padres.
7. Aplicar crossover uniforme.
8. Aplicar mutacion por gen.
9. Crear nueva generacion.
10. Repetir hasta `n_iterations`.
11. Crear reportes y graficos.

## Dentro de `PyPlanningProblem.evaluate()`

1. Calcular `chromosome.to_key()` y revisar cache.
2. Reparar topologia si `use_topology_repair=True`.
3. Calcular inversion por etapa.
4. Calcular valor presente de inversion.
5. Validar topologia y sumar penalidades.
6. Generar DSS temporal si OpenDSS esta habilitado.
7. Ejecutar OpenDSS 24h.
8. Extraer perdidas, tensiones y corrientes.
9. Calcular costo anual de perdidas.
10. Calcular valor presente de perdidas.
11. Agregar penalidades tecnicas o `penalty_dss_error` si falla OpenDSS.
12. Calcular fitness con `PyObjectiveFunction`.
13. Crear `PyEvaluationResult` y guardar en cache.

## Despues del AG

1. Imprimir mejor cromosoma.
2. Imprimir resumen de evaluacion, funcion objetivo, DSS, perdidas, topologia y reparacion.
3. Generar graficos topologicos si esta activo.
4. Generar DSS finales de la mejor solucion en `outputs/dss_files`.
5. Imprimir la lista de archivos DSS finales.

## Diagrama resumido

```text
python main.py
   ↓
config + CSVs
   ↓
modulos economicos/topologicos/DSS
   ↓
PyPlanningProblem
   ↓
PySimpleGA.run()
   ↓
poblacion inicial
   ↓
evaluacion: reparacion -> topologia -> inversion -> DSS -> perdidas -> fitness
   ↓
seleccion + crossover + mutacion + elitismo
   ↓
mejor solucion
   ↓
DSS finales + CSVs + graficos
```
