# OpenDSS y perdidas electricas

## Clases

| Clase | Responsabilidad |
|---|---|
| `PyDSSRunner` | Compila y ejecuta archivos DSS por 24 horas. |
| `PyDSSResults` | Acumula resultados por etapa. |
| `PyElectricalLossCost` | Convierte perdidas en kWh a costo anual. |

## Ejecucion 24 horas

`PyDSSRunner.run_files_24h()` recibe una lista de archivos DSS, uno por etapa. Para cada etapa:

```text
compile DSS
for hour in 1..24:
    Set mode=daily
    Set number=hour
    Solve
    extraer resultados
```

En el codigo el bucle usa `range(dss_simulation_hours)` y llama `Set number=hour + 1`.

## Datos extraidos

| Resultado | Metodo |
|---|---|
| Potencia activa total | `extract_total_power()` |
| Potencia reactiva total | `extract_total_power()` |
| Perdidas kW/kVAr | `extract_losses()` |
| Resumen de tension | `extract_voltage_summary()` |
| Resumen de corriente | `extract_line_current_summary()` |

Por etapa se agregan energia perdida kWh/dia, tension minima/maxima, violaciones de tension, corriente maxima y violaciones de corriente.

## Calculo de perdidas

```text
E_loss_day = sum(losses_kw_hourly)
E_loss_year = E_loss_day * days_per_year
C_loss_year = E_loss_year * energy_price
```

## Valor presente de perdidas

Las perdidas son costo operativo anual. Por eso se descuentan ano por ano usando `PyPresentValue.operation()`, respetando `stage_years`.

## Uso dentro del fitness

Si `use_open_dss_in_fitness=True` y `use_electrical_loss_cost=True`, `PyPlanningProblem.evaluate()` genera DSS temporal, ejecuta OpenDSS 24h, calcula costo anual de perdidas, calcula valor presente y agrega penalidades por tension/corriente. Si la topologia es invalida y `skip_opendss_if_topology_invalid=True`, OpenDSS se omite.
