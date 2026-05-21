# Estructura de datos de entrada

Los datos se leen desde `Initialdata/` con `PyDataReader.read_all()`. El lector construye un diccionario `data` que usan los demas modulos.

## `bus_catalog.csv`

Representa el catalogo de barras.

| Columna | Uso |
|---|---|
| `bus` | Nombre de la barra. |
| `bus_type` | Tipo de barra; se usa para detectar fuentes. |
| `has_load` | Indica si la barra tiene carga. |
| `load_count` | Numero de cargas asociadas. |

Estructuras internas: `buses`, `source_buses`, `load_buses`, `n_buses`.

## `loads_projection_master.csv`

Representa las cargas por etapa.

| Columna | Uso |
|---|---|
| `load_id` | Identificador de carga. |
| `bus` | Barra donde se conecta la carga. |
| `P_stage_n_kW`, `Q_stage_n_kVAr` | Potencia activa/reactiva por etapa. |
| `consumer_stage_n`, `consumer_class_stage_n` | Tipo/clase de consumidor por etapa. |

Estructuras internas: `loads_by_stage`, `consumer_types_by_stage`, `n_loads`.

## `load_curves_by_consumer_type_template.csv`

Define curvas horarias por tipo de consumidor. Las columnas actuales son `hour`, `R`, `C`, `I`, `I4`. `PyDataReader` genera `data['load_curves']` y `PyDSSWriter` las transforma en `Loadshape.LS_R`, `LS_C`, `LS_I` y `LS_I4`.

## `line_valid_options.csv`

Define que opciones puede tomar cada linea.

| Columna | Uso |
|---|---|
| `line_id` | Identificador de linea. |
| `bar_1`, `bar_2` | Barras extremas. |
| `valid_options` | Lista separada por `|`. |
| `first_valid_option` | Opcion base usada para comparar la etapa 1. |

Estructuras internas: `valid_options_by_line`, `base_option_by_line`, `line_index_map`, `n_lines`.

## Significado de `-1`

`-1` significa linea desconectada, no instalada o removida. Conceptualmente una linea solo deberia tomar `-1` si `-1` aparece en sus opciones validas.

```text
[0, 1, 2, 3]        -> linea obligatoria, no removible.
[-1, 0, 1, 2, 3]    -> linea existente/candidata removible.
[-1, 1, 2, 3]       -> linea candidata nueva.
```

Nota de implementacion: `PyPopulation` y `PyMutation` agregan `-1` a la lista de opciones si no existe, para explorar apagados. La validez final se controla por costos, validacion y reparacion topologica.

## `line_options_long_normalized.csv`

Catalogo tecnico/economico de opciones de linea.

| Columna | Uso |
|---|---|
| `line_id` | Identificador de linea. |
| `bar_1`, `bar_2` | Barras conectadas. |
| `length_km` | Longitud. |
| `option_id` | Codigo de opcion. |
| `imax_A` | Corriente maxima. |
| `r1_ohm_km`, `x1_ohm_km` | Parametros electricos. |
| `cost_usd` | Costo de la opcion. |

Estructuras internas: `line_catalog` y `line_topology`.

## `ccifi_ccidi_limits_improved.csv`

Existe como entrada con limites/indicadores de continuidad, por ejemplo `CCIFI_stage_*` y `CCIDI_stage_*`. En el codigo actual no se lee dentro de `PyDataReader` ni participa en el fitness. Debe tratarse como dato preparado para fases futuras.

## Carpeta `DERs/`

Contiene archivos `DERs_Stage1.dss`, `DERs_Stage2.dss`, `DERs_Stage3.dss`. `PyDSSWriter` los inserta mediante `Redirect`. Los DERs no son variables de decision del AG en la version actual.
