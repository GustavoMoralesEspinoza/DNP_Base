# Limitaciones actuales y proximos pasos

## Limitaciones actuales

| Limitacion | Comentario |
|---|---|
| DERs externos | Los DERs se insertan mediante archivos DSS externos y `Redirect`; no son variables optimizadas. |
| PV/BESS/EV | No se optimizan PV, baterias ni vehiculos electricos como decisiones del cromosoma. |
| Perdidas financieras | No hay modelo implementado de perdidas financieras por interrupciones o calidad de servicio. |
| SAIDI/SAIFI/CCIFI/CCIDI | Existe un CSV de CCIFI/CCIDI, pero no se lee ni se integra al fitness actual. |
| Penalidades tecnicas simples | Tension y corriente se penalizan por conteo de violaciones; la penalidad proporcional esta desactivada. |
| Perfiles diarios | El costo de perdidas electricas usa una simulacion diaria y anualiza con `days_per_year`. |
| Costo computacional | OpenDSS se puede ejecutar dentro de cada evaluacion de fitness, lo que encarece mucho el AG. |
| Algoritmos multiobjetivo | NSGA-II y PSO no estan implementados. |
| Graficos avanzados | No existen aun graficos separados `investment_vs_fitness`, `electrical_losses_vs_fitness` ni 3D. |

## Proximos pasos posibles

1. Implementar optimizacion multiobjetivo real, por ejemplo NSGA-II.
2. Incorporar DERs como variables de decision del cromosoma.
3. Agregar PV, BESS y EV con restricciones tecnicas propias.
4. Agregar penalidades proporcionales por exceso de tension/corriente.
5. Incluir capacidad de subestacion como restriccion.
6. Integrar indicadores de continuidad como SAIDI, SAIFI, CCIFI y CCIDI.
7. Modelar perdidas financieras por interrupciones y voltage sags.
8. Crear referencias mas robustas para normalizacion de perdidas electricas.
9. Reducir costo computacional con cache mas amplio, evaluacion paralela o filtros topologicos previos.
10. Implementar reporte PDF automatico.
11. Agregar graficos separados inversion-fitness, perdidas-fitness y superficie/3D `Cinv-Cele-Fitness`.
