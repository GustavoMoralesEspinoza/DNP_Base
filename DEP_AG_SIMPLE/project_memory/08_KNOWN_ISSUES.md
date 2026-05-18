# Known Issues

- Posibles penalidades excesivas por warnings si `penalty_warning` vuelve a activarse.
- Revisar si una remocion valida esta siendo tratada como warning penalizable.
- Verificar diferencias de comportamiento entre `collapse_sources=True` y `collapse_sources=False`.
- Revisar que el generador DSS use siempre `best_result.chromosome`, no un cromosoma original sin reparar.
- Validar que los archivos `.dss` generados sean compatibles con OpenDSS real.
- `dss_equivalent_source_name = "sourcebus"` se usa para colapsar fuentes; verificar que el circuito generado interprete correctamente ese bus.
- `repair_allow_remove_non_candidate=True` esta activo y permite reparacion agresiva; revisar antes de usar resultados formales.
- Aun falta FASE 10: runner OpenDSS 24 h.
- Aun falta FASE 11: costo de perdidas electricas.
- No hay penalidades por tension, corriente o capacidad de fuente.

