# DEP_AG_SIMPLE - Documentacion general

## Que es el proyecto

`DEP_AG_SIMPLE` es un proyecto Python para resolver una version basica del problema de `Distribution Network Expansion Planning` usando un Algoritmo Genetico simple.

El objetivo es buscar una configuracion de lineas por etapa de planeamiento que reduzca una funcion objetivo formada por costo de inversion, costo de perdidas electricas y penalidades por restricciones tecnicas/topologicas.

## Entradas principales

Las entradas se leen desde `Initialdata/` mediante `PyDataReader`:

| Entrada | Uso principal |
|---|---|
| `bus_catalog.csv` | Catalogo de barras, fuentes y barras con carga. |
| `loads_projection_master.csv` | Proyeccion de cargas activas/reactivas por etapa. |
| `line_options_long_normalized.csv` | Catalogo tecnico/economico de lineas y opciones. |
| `line_valid_options.csv` | Opciones validas por linea y estado base. |
| `load_curves_by_consumer_type_template.csv` | Curvas horarias por tipo de consumidor. |
| `ccifi_ccidi_limits_improved.csv` | Datos de continuidad disponibles en entrada, aun no integrados al fitness. |
| `Initialdata/DERs/` | Archivos DSS externos de DER por etapa. |

## Salidas principales

El proyecto genera resultados en `outputs/`:

| Carpeta | Resultado |
|---|---|
| `outputs/dss_temp/` | DSS temporales usados durante evaluaciones del fitness. |
| `outputs/dss_files/` | DSS finales de la mejor solucion. |
| `outputs/ga_reports/` | CSVs del historico y evaluaciones del AG. |
| `outputs/ga_plots/` | Graficos de convergencia y comparacion de costos. |
| `outputs/topology_debug/` | Graficos de diagnostico topologico por etapa. |

## Fases implementadas

Actualmente estan implementadas estas fases:

1. Lectura y validacion de CSVs.
2. Codificacion matricial del cromosoma.
3. Algoritmo genetico simple.
4. Calculo de costo de inversion multiestagio.
5. Calculo de valor presente para inversion y costos operativos.
6. Validacion topologica con NetworkX.
7. Reparacion topologica opcional.
8. Generacion de archivos DSS por etapa.
9. Ejecucion OpenDSS de 24 horas dentro del fitness cuando esta habilitada.
10. Calculo de costo de perdidas electricas.
11. Reportes CSV y graficos del AG.
12. Graficos de debug topologico.

## Como ejecutar

Desde la carpeta del proyecto:

```bash
python main.py
```

El flujo principal esta en `main.py`: crea la configuracion, lee los datos, instancia los modulos economicos/topologicos/DSS, crea `PyPlanningProblem`, ejecuta `PySimpleGA` y guarda los resultados de la mejor solucion.

## Carpetas importantes

| Carpeta | Proposito |
|---|---|
| `config/` | Parametros globales del modelo. |
| `data/` | Lectura de CSVs. |
| `core/` | Cromosoma, evaluacion y problema de planeamiento. |
| `genetic_algorithm/` | Operadores y ciclo del AG. |
| `economics/` | Costos, valor presente y funcion objetivo. |
| `topology/` | Validacion y reparacion de red. |
| `dss/` | Escritura y ejecucion de OpenDSS. |
| `reports/` | Reportes CSV, graficos y debug topologico. |
| `Initialdata/` | Datos de entrada. |
| `outputs/` | Resultados generados. |
