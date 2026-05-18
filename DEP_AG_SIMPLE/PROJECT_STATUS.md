# Project Status

`DEP_AG_SIMPLE` tiene implementadas las fases 2 a 9: lectura de datos, cromosoma matricial, inversion, valor presente, funcion objetivo, AG simple, topologia con NetworkX, reparacion/reconexion y generacion DSS.

Estado actual:
- `main.py` ejecuta el AG, repara topologia, genera reportes de debug y escribe DSS por estadio.
- Los DSS se guardan en `outputs/dss_files/`.
- OpenDSS aun no se ejecuta.
- Proximo paso: FASE 10, crear `PyDSSRunner` para compilar y correr simulacion 24 h con `py_dss_interface`.

