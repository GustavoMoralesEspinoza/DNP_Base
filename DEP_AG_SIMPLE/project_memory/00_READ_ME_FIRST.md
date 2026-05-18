# Read Me First

Este directorio guarda memoria de proyecto para continuar `DEP_AG_SIMPLE` en una nueva sesion sin perder decisiones importantes.

Antes de modificar codigo, lee todos los archivos dentro de `project_memory/`, revisa `main.py`, `config/py_config_base.py`, `core/py_planning_problem.py`, `topology/`, `genetic_algorithm/`, `economics/`, `dss/` y ejecuta `python main.py` para verificar el estado actual.

Nota de entorno: en esta maquina, `python main.py` suele fallar porque `python` apunta al alias de Microsoft Store. El comando que ha funcionado durante esta sesion es:

```bash
py main.py
```

No implementes nuevas fases sin entender primero:
- como `PyPlanningProblem.evaluate()` aplica reparacion antes de evaluar;
- que `best_result.chromosome` debe ser el cromosoma reparado;
- que `PyDSSWriter` ya genera archivos `.dss`, pero todavia no se ejecuta OpenDSS.

