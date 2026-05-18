# Project Overview

`DEP_AG_SIMPLE` es un proyecto Python para un modelo basico de Distribution Expansion Planning usando Algoritmo Genetico y codificacion matricial.

La solucion se representa como un cromosoma:

```text
filas = estadios de planeamiento
columnas = lineas del sistema
valor = opcion seleccionada para cada linea
```

El proyecto actualmente integra:
- lectura de datos normalizados desde CSV;
- cromosoma matricial;
- costo de inversion multiestagio;
- valor presente;
- funcion objetivo simple por pesos;
- algoritmo genetico simple;
- validacion topologica con NetworkX;
- reparacion/reconexion de red;
- opcion `collapse_sources` para interpretar varias subestaciones como una fuente equivalente;
- generacion de archivos OpenDSS `.dss` por estadio.

Todavia no implementa:
- ejecucion de OpenDSS;
- simulacion 24 h;
- perdidas electricas reales;
- costos de perdidas;
- loadshapes en DSS;
- PV, BESS, EV, Wind;
- SAIDI/SAIFI;
- CCIFI/CCIDI.

