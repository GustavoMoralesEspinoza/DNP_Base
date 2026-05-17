"""
PyEvaluationResult: Contenedor de resultados de evaluación de un cromosoma.

Almacena todos los valores resultantes de evaluar una solución de DEP:
fitness, costos, penalidades, resultados de topología y de flujo de potencia.
"""


class PyEvaluationResult:
    """
    Almacena los resultados de la evaluación de un cromosoma.
    
    Contiene:
    - chromosome: el cromosoma evaluado
    - fitness: valor de aptitud (fitness) general
    - c_inv: costo de inversión normalizado
    - c_ele: costo de pérdidas eléctricas normalizado
    - penalty: penalidad aplicada (restricciones violadas)
    - topology_result: resultado de validación de topología
    - dss_results: resultados de flujo de potencia
    - is_feasible: indicador de factibilidad de la solución
    """

    def __init__(self, chromosome, fitness, c_inv, c_ele, penalty,
                 topology_result=None, dss_results=None, is_feasible=True):
        """
        Inicializa los resultados de evaluación de un cromosoma.
        
        Args:
            chromosome (PyChromosome): el cromosoma evaluado.
            fitness (float): valor de aptitud (fitness) general.
            c_inv (float): costo de inversión normalizado [0, 1].
            c_ele (float): costo de pérdidas eléctricas normalizado [0, 1].
            penalty (float): penalidad por restricciones violadas.
            topology_result (dict, optional): resultado de análisis de topología.
            dss_results (dict, optional): resultado de flujo de potencia.
            is_feasible (bool, optional): indica si la solución es factible.
        """
        self.chromosome = chromosome
        self.fitness = fitness
        self.c_inv = c_inv
        self.c_ele = c_ele
        self.penalty = penalty
        self.topology_result = topology_result
        self.dss_results = dss_results
        self.is_feasible = is_feasible

    def summary(self):
        """
        Imprime en consola un resumen de los resultados de evaluación.
        
        Muestra: fitness, costo de inversión, costo de pérdidas,
        penalidad y factibilidad.
        """
        print("\n" + "="*60)
        print("RESULTADO DE EVALUACIÓN")
        print("="*60)
        
        print("\n[APTITUD (FITNESS)]")
        print(f"  Fitness:                 {self.fitness:.6f}")
        
        print("\n[COSTOS]")
        print(f"  Costo de inversión:      {self.c_inv:.6f}")
        print(f"  Costo de pérdidas:       {self.c_ele:.6f}")
        
        print("\n[RESTRICCIONES]")
        print(f"  Penalidad:               {self.penalty:.6f}")
        
        print("\n[FACTIBILIDAD]")
        feasible_str = "SÍ" if self.is_feasible else "NO"
        print(f"  ¿Factible?:              {feasible_str}")
        
        if self.topology_result is not None:
            print("\n[TOPOLOGÍA]")
            for key, value in self.topology_result.items():
                print(f"  {key}:                    {value}")
        
        if self.dss_results is not None:
            print("\n[FLUJO DE POTENCIA]")
            for key, value in self.dss_results.items():
                print(f"  {key}:                    {value}")
        
        print("\n" + "="*60 + "\n")
