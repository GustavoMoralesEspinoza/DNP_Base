# Prompt For Next Session

Copia este prompt en una nueva sesion de Codex:

```text
Estoy trabajando en el proyecto Python DEP_AG_SIMPLE.

Lee primero todos los archivos en project_memory/. Luego revisa el estado del codigo y ejecuta python main.py. No implementes nada hasta entender la arquitectura. Continua desde la FASE 10 — Runner OpenDSS 24 h, usando PyDSSWriter y los archivos DSS generados en outputs/dss_files/.

Contexto importante:
- Ya existen lector CSV, cromosoma matricial, costo de inversion, valor presente, funcion objetivo, AG simple, validacion topologica, reparacion/reconexion, debug topologico y generador DSS.
- No implementes PV/BESS/EV/Wind todavia.
- No implementes FASE 11 hasta validar FASE 10.
- El comando python main.py puede fallar en esta maquina por alias de Microsoft Store; py main.py ha funcionado.
- Usa best_result.chromosome porque contiene el cromosoma reparado cuando use_topology_repair=True.
```

