# Funcion objetivo y fitness

## Forma general

La funcion objetivo esta implementada en `PyObjectiveFunction`:

```text
Fitness = w_inv * Cinv_pu + w_ele * Cele_pu + Penalties
```

El problema es de minimizacion: un fitness menor representa una solucion mejor.

## Componentes

| Componente | Significado | Fuente |
|---|---|---|
| `Cinv` | Costo de inversion en valor presente. | `PyInvestmentCost` + `PyPresentValue.investment()` |
| `Cele` | Costo de perdidas electricas en valor presente. | `PyDSSRunner` + `PyElectricalLossCost` + `PyPresentValue.operation()` |
| `Penalty` | Restricciones violadas. | Topologia, DSS, tension/corriente, opciones invalidas. |

## Normalizacion y pesos

```text
Cinv_pu = Cinv_total / c_inv_max
Cele_pu = Cele_total / c_ele_max
```

`c_inv_max` se calcula en `main.py` con `PyInvestmentCost.calculate_max_investment_reference()`. `c_ele_max` puede actualizarse automaticamente cuando hay resultado de perdidas electricas.

Los pesos actuales son:

```text
w_inv = 0.7
w_ele = 0.3
```

## Penalidades

Las penalidades se agregan al fitness sin normalizar, por eso pueden dominar el resultado.

| Penalidad | Fuente |
|---|---|
| `penalty_invalid_option` | Opcion invalida. |
| `penalty_component_without_source` | Componente sin fuente. |
| `penalty_disconnected_load` | Carga aislada/desconectada. |
| `penalty_cycle` | Ciclos topologicos. |
| `penalty_multiple_sources` | Multiples fuentes en una componente. |
| `penalty_dss_error` | Error al ejecutar/compilar OpenDSS. |
| `penalty_voltage_violation` | Violaciones de tension. |
| `penalty_current_violation` | Violaciones de corriente. |

## Casos especiales

Si `electrical_loss_pv_result` es `None`, `Cele_total = 0`. Esto puede ocurrir si OpenDSS no esta habilitado, si se omite por topologia invalida o si falla la evaluacion electrica.

Si OpenDSS falla, `PyPlanningProblem` agrega warning y suma `penalty_dss_error`.

Una solucion se marca factible cuando `penalty == 0`.
