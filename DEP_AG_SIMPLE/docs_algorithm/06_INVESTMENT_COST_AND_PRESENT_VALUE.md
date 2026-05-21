# Costo de inversion y valor presente

## Costo de inversion

`PyInvestmentCost` calcula el costo comparando el estado anterior de cada linea con el estado actual.

Reglas implementadas:

```python
if previous_option == current_option:
    costo = 0

if previous_option == -1 and current_option != -1:
    costo = costo_instalacion(current_option)

if previous_option != -1 and current_option == -1:
    costo = removal_factor * costo(previous_option)

if previous_option != -1 and current_option != previous_option:
    costo = costo(current_option) + removal_factor * costo(previous_option)
```

## Comparacion por etapa

| Etapa | Comparacion |
|---|---|
| Etapa 1 | Se compara contra `base_option_by_line`. |
| Etapa 2 | Se compara contra la etapa 1 del cromosoma. |
| Etapa 3 | Se compara contra la etapa 2 del cromosoma. |

Esto permite modelar inversiones incrementales, remociones y reemplazos.

## Salida de `PyInvestmentCost`

| Campo | Significado |
|---|---|
| `total_cost` | Costo total sin descuento. |
| `cost_by_stage` | Costo por etapa. |
| `cost_by_line` | Costo acumulado por linea. |
| `transitions` | Lista de transiciones linea-etapa. |
| `validation_errors` | Errores de opciones/dimensiones. |
| `validation_warnings` | Advertencias, por ejemplo remociones. |

## Valor presente

`PyPresentValue.calculate_pv_investment()` descuenta inversiones al inicio de cada etapa:

```text
delta = 1 / (1 + interest_rate)^year
PV_stage = cost_stage * delta
```

Las perdidas electricas son costo operativo anual. Por eso `PyPresentValue.operation()` descuenta cada ano dentro de cada etapa.

Ejemplo con `stage_years = [1, 1, 2]`:

| Etapa | Anos descontados para costos operativos |
|---|---|
| 1 | Ano 1 |
| 2 | Ano 2 |
| 3 | Anos 3 y 4 |

Si `stage_years = [5, 5]`, cada etapa dura 5 anos. Si `stage_years = [1, 1, 2]`, el ultimo estadio dura 2 anos. En el codigo actual la configuracion tiene `stage_years = [5, 5, 2]`.
