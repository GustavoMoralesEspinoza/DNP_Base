# Generacion DSS

## Clase principal

`PyDSSWriter` genera archivos `.dss` por etapa a partir de un cromosoma. Este modulo no ejecuta OpenDSS; solo escribe archivos.

## Flujo

```text
Cromosoma
   ↓
stage_vector
   ↓
lineas activas
   ↓
cargas por etapa
   ↓
loadshapes por tipo de consumidor
   ↓
DERs mediante Redirect
   ↓
archivo .dss
```

## Archivos generados

`write_chromosome()` crea un archivo por etapa: `{prefix}_stage_1.dss`, `{prefix}_stage_2.dss`, `{prefix}_stage_3.dss`.

Durante fitness se usa `outputs/dss_temp/` con prefijo `eval_current`. Para la mejor solucion final se usa `outputs/dss_files/` con prefijo `best_solution`.

## Secciones del DSS

| Seccion | Funcion |
|---|---|
| `Clear` | Limpia el circuito anterior. |
| `New Circuit` | Crea el circuito de la etapa. |
| `LoadShapes` | Define curvas horarias. |
| `Lines` | Escribe lineas activas. |
| `Loads` | Escribe cargas de la etapa. |
| `DERs Redirect` | Inserta archivos DSS externos de DERs. |
| `VoltageBases` | Define bases de tension. |
| `Solve` | Ejecuta una solucion inicial. |

## Lineas, cargas y curvas

`write_lines()` omite genes con `option_id == -1`. Para lineas activas escribe `New Line` con buses, longitud, `r1`, `x1` y `normamps` tomado de `imax_A`.

`write_loads()` usa `data['loads_by_stage'][stage_index]`. Para cada carga con `P_kW > 0`, escribe `New Load` con `kW`, `kVAR`, conexion, modelo, tension base y `Daily=<loadshape>`.

Los tipos `R`, `C`, `I`, `I4` se asignan a `LS_R`, `LS_C`, `LS_I`, `LS_I4`. Si no hay tipo valido, se usa `LS_DEFAULT`.

## DERs mediante `Redirect`

Si `use_ders=True`, `write_ders_redirect()` busca archivos con el patron `DERs_Stage{stage}.dss` y los inserta con `Redirect`. Si falta el archivo y `ders_continue_if_missing=True`, solo emite warning y continua.

## Fuentes en DSS

Si `dss_collapse_sources=True`, las barras fuente se renombran como `dss_equivalent_source_name` al escribir el DSS. Esto es independiente de `collapse_sources`, que aplica a la validacion topologica.
