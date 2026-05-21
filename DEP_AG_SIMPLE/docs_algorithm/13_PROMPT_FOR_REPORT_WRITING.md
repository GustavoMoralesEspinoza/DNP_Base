# Prompt para redactar el informe tecnico

Usa este prompt en ChatGPT cuando quieras redactar el informe academico a partir de esta documentacion.

```text
Voy a escribir un informe tecnico sobre el proyecto DEP_AG_SIMPLE.

Lee los archivos dentro de docs_algorithm/ y ayudame a redactar un informe academico explicando la metodologia, arquitectura del algoritmo genetico, modelamiento de costos, validacion topologica, simulacion OpenDSS y analisis de resultados.

Requisitos:
- No inventes cosas que no estan en el codigo.
- Si algo no esta implementado, dilo claramente como limitacion o trabajo futuro.
- Usa lenguaje tecnico, claro y organizado.
- Escribe en espanol.
- Usa tablas cuando ayuden.
- Usa diagramas de flujo en texto cuando sea util.
- Diferencia entre lo implementado actualmente y lo propuesto como extension futura.
- Manten coherencia con los nombres reales de clases, carpetas, archivos y salidas del proyecto.

Estructura sugerida del informe:

1. Introduccion
2. Descripcion del problema
3. Datos de entrada
4. Modelamiento del cromosoma
5. Algoritmo genetico propuesto
6. Funcion objetivo
7. Restricciones y reparacion topologica
8. Integracion con OpenDSS
9. Calculo de costos
10. Resultados
11. Conclusiones

En la seccion de resultados, usa los archivos generados en outputs/ga_reports/, outputs/ga_plots/, outputs/dss_files/ y outputs/topology_debug/ si estan disponibles.

En la seccion de limitaciones, menciona que DERs se insertan por archivos DSS externos y no se optimizan, que CCIFI/CCIDI aun no participa en el fitness, que las penalidades tecnicas son simples por conteo y que OpenDSS dentro del fitness puede ser computacionalmente costoso.
```
