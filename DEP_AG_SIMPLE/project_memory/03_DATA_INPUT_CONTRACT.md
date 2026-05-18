# Data Input Contract

Los datos principales viven en `Initialdata/`. Actualmente hay archivos para el caso principal y subcarpetas `18 bus/` y `54 bus/`.

## `bus_catalog.csv`

Columnas principales esperadas:
- `bus`
- `bus_type`
- `has_load`
- `load_count`

`PyDataReader` construye:
- `data["buses"]`
- `data["source_buses"]`
- `data["load_buses"]`

Las fuentes se detectan si `bus_type` contiene `source` o si el nombre del bus contiene `SE`.

## `loads_projection_master.csv`

Columnas principales esperadas:
- identificador de carga;
- `bus`;
- `P_stage_1_kW`, `Q_stage_1_kVAr`;
- `P_stage_2_kW`, `Q_stage_2_kVAr`;
- `P_stage_3_kW`, `Q_stage_3_kVAr`;
- `consumer_stage_N`;
- `consumer_class_stage_N`.

`PyDataReader` construye:
- `data["loads_by_stage"][stage][load_id]`
- `P_kW`
- `Q_kVAr`
- `consumer_type`
- `consumer_class`

Si `P_kW <= 0`, el DSS writer no escribe esa carga.

## `line_options_long_normalized.csv`

Columnas principales esperadas:
- `line_id`
- `bar_1`
- `bar_2`
- `option_id`
- `cost_usd`
- `imax_A`
- `r1_ohm_km`
- `x1_ohm_km`
- `length_km`

`PyDataReader` construye `data["line_catalog"][line_id]` con:
- `bar_1`
- `bar_2`
- `options_detail[option_id]`

## `line_valid_options.csv`

Define opciones validas por linea en `data["valid_options_by_line"]`.

Regla critica:

`-1` significa linea apagada/no instalada/removida, pero una linea solo puede tomar `-1` si `-1` aparece dentro de sus opciones validas en `line_valid_options.csv`.

Ejemplos:
- `[0, 1, 2, 3]`: linea obligatoria, no removible.
- `[-1, 0, 1, 2, 3]`: linea existente o candidata removible.
- `[-1, 1, 2, 3]`: linea candidata nueva.

## `load_curves_by_consumer_type_template.csv`

Plantilla de curvas por tipo de consumidor. Aun no se usa en el DSS writer actual. Queda para fases de simulacion 24 h/loadshapes.

## `ccifi_ccidi_limits_improved.csv`

Existe en `Initialdata/`, pero aun no esta integrado al fitness ni a restricciones.

