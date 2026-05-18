# Architecture

## `config/`

Contiene `PyConfigBase`, configuracion central del proyecto: parametros del AG, pesos, economia, penalidades, topologia, reparacion, debug plots y DSS writer.

## `data/`

Contiene `PyDataReader`, que lee CSVs desde `Initialdata/` y construye el diccionario `data` usado por todos los modulos.

## `core/`

Contiene:
- `PyChromosome`: representacion matricial de soluciones.
- `PyEvaluationResult`: contenedor de fitness, costos, penalidades, topologia, reparacion y resumen.
- `PyPlanningProblem`: evaluador central. Aplica reparacion opcional, calcula inversion, valor presente, topologia y funcion objetivo.

## `genetic_algorithm/`

Contiene el AG simple:
- poblacion inicial;
- seleccion por torneo;
- crossover uniforme;
- mutacion;
- elitismo;
- ciclo principal `PySimpleGA`.

Importante: seleccion y elitismo usan `result.chromosome`, que puede ser el cromosoma reparado.

## `economics/`

Contiene:
- `PyInvestmentCost`: costo de inversion multiestagio.
- `PyPresentValue`: valor presente.
- `PyObjectiveFunction`: fitness por pesos y desglose de penalidades.

## `topology/`

Contiene:
- `PyTopologyValidator`: validacion topologica con NetworkX.
- `PyTopologyRepair`: reparacion/reconexion por estadio.

Ambos respetan `collapse_sources`.

## `dss/`

Contiene `PyDSSWriter`, que genera archivos `.dss` por estadio desde el cromosoma final. No ejecuta OpenDSS.

## `reports/`

Contiene `PyTopologyDebugPlot`, reporte textual/grafico de componentes, fuentes y caminos entre fuentes. Guarda PNGs en `outputs/topology_debug/`.

