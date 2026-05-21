# Arquitectura del proyecto

## Vision por carpetas

| Carpeta | Clase/modulo principal | Responsabilidad | Conexion |
|---|---|---|---|
| `config/` | `PyConfigBase` | Centraliza parametros del AG, topologia, DSS, economia, penalidades y reportes. | Es inyectada en casi todos los modulos. |
| `data/` | `PyDataReader` | Lee CSVs y construye el diccionario `data`. | Alimenta cromosomas, costos, topologia y DSS. |
| `core/` | `PyChromosome`, `PyPlanningProblem`, `PyEvaluationResult` | Representa soluciones, evalua cromosomas y guarda resultados. | Une economia, topologia, DSS y AG. |
| `genetic_algorithm/` | `PySimpleGA` | Ejecuta el ciclo evolutivo. | Llama a `problem.evaluate()` para cada individuo. |
| `economics/` | `PyInvestmentCost`, `PyPresentValue`, `PyObjectiveFunction`, `PyElectricalLossCost` | Calcula inversion, valor presente, perdidas electricas monetizadas y fitness. | Consume cromosomas y resultados OpenDSS. |
| `topology/` | `PyTopologyValidator`, `PyTopologyRepair` | Valida radialidad/conectividad/fuentes y repara cromosomas. | Se ejecuta antes de costos/DSS dentro de la evaluacion. |
| `dss/` | `PyDSSWriter`, `PyDSSRunner`, `PyDSSResults` | Genera `.dss`, ejecuta OpenDSS 24h y almacena resultados. | Entrega perdidas y violaciones tecnicas al fitness. |
| `reports/` | `PyGAReport`, `PyTopologyDebugPlot` | Guarda CSVs, graficos del AG y graficos topologicos. | Usa el estado final de `PySimpleGA` y el mejor cromosoma. |
| `Initialdata/` | CSVs y `DERs/` | Datos de red, cargas, opciones y DERs externos. | Entrada de `PyDataReader` y `PyDSSWriter`. |
| `outputs/` | Archivos generados | Reportes, graficos, DSS temporales/finales. | Salida de AG, DSS y debug. |

## Flujo textual

```text
CSV inputs
   ↓
PyDataReader
   ↓
PySimpleGA
   ↓
PyPlanningProblem.evaluate()
   ↓
Topology repair / validation
   ↓
Investment cost
   ↓
DSS generation
   ↓
OpenDSS 24h
   ↓
Electrical losses cost
   ↓
Objective function
   ↓
Fitness
```

## Idea central

`PyPlanningProblem` es el punto de integracion. El AG no calcula costos ni restricciones directamente: solamente crea cromosomas, aplica seleccion/crossover/mutacion/elitismo y delega la evaluacion a `PyPlanningProblem.evaluate()`.

El resultado de cada evaluacion se encapsula en `PyEvaluationResult`, que contiene fitness, costos, penalidad, factibilidad, cromosoma reparado, resultados topologicos, resultados DSS y desglose de la funcion objetivo.
