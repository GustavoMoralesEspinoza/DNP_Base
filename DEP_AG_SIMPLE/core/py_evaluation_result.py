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
                 topology_result=None, dss_results=None, is_feasible=True,
                 repair_result=None):
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
        self.repair_result = repair_result
        self.loss_cost_result = None
        self.electrical_loss_pv_result = None

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

        loss_cost_result = getattr(self, "loss_cost_result", None)
        if loss_cost_result is not None:
            print("\n[PÉRDIDAS ELÉCTRICAS]")
            print(
                "  Pérdidas diarias por estágio: "
                f"{loss_cost_result.get('losses_kwh_day_by_stage', [])}"
            )
            print(
                "  Costo anual por estágio: "
                f"{loss_cost_result.get('annual_cost_by_stage', [])}"
            )

        electrical_loss_pv_result = getattr(self, "electrical_loss_pv_result", None)
        if electrical_loss_pv_result is not None:
            print(
                "  Costo pérdidas eléctricas VP: "
                f"{electrical_loss_pv_result.get('total_pv', 0.0):.6f}"
            )
        
        print("\n[RESTRICCIONES]")
        print(f"  Penalidad:               {self.penalty:.6f}")
        
        print("\n[FACTIBILIDAD]")
        feasible_str = "SÍ" if self.is_feasible else "NO"
        print(f"  ¿Factible?:              {feasible_str}")
        
        if self.topology_result is not None:
            print("\n[TOPOLOGÍA]")
            print(f"  Topología válida:         {self.topology_result.get('is_valid')}")
            print(
                "  Penalidad topológica:     "
                f"{self.topology_result.get('total_penalty', 0.0):.6f}"
            )

        if self.repair_result is not None:
            print("\n[REPARACIÓN]")
            print("  Reparación activa:        True")
            print(f"  Fue reparado:             {self.repair_result.get('was_repaired')}")
            print(f"  Cambios de reparación:    {self.repair_result.get('total_changes')}")
            print(f"  Reparación exitosa:       {self.repair_result.get('success')}")

        objective_result = getattr(self, "objective_result", None)
        if objective_result is not None:
            self.print_penalty_breakdown(objective_result.get("penalty_breakdown"))
            technical_keys = ["voltage_violations", "current_violations"]
            penalty_breakdown = objective_result.get("penalty_breakdown", {})
            if any(penalty_breakdown.get(key, 0.0) for key in technical_keys):
                print("\n[PENALIDADES TÉCNICAS]")
                for key in technical_keys:
                    print(f"  {key}: {penalty_breakdown.get(key, 0.0):.2f}")
        
        if self.dss_results is not None:
            print("\n[FLUJO DE POTENCIA]")
            if hasattr(self.dss_results, "stage_results"):
                print(f"  Etapas simuladas:         {len(self.dss_results.stage_results)}")
                print(
                    "  Perdidas totales kWh:     "
                    f"{self.dss_results.total_energy_losses_kwh:.6f}"
                )
            else:
                for key, value in self.dss_results.items():
                    print(f"  {key}:                    {value}")
        
        print("\n" + "="*60 + "\n")

    def print_penalty_breakdown(self, penalty_breakdown=None):
        """
        Imprime desglose global y por estágio de penalidades si existe.
        """
        if not penalty_breakdown:
            return

        print("\n[RESUMEN DE PENALIDADES]")
        for key, value in penalty_breakdown.items():
            print(f"  {key}: {value:.2f}")

        if self.topology_result is None:
            return

        stage_results = self.topology_result.get("stage_results", [])
        if not stage_results:
            return

        print("\n[PENALIDADES POR ESTÁGIO]")
        for stage_result in stage_results:
            print(f"  Estágio {stage_result.get('stage_index')}:")
            stage_breakdown = stage_result.get("penalty_breakdown", {})
            for key, value in stage_breakdown.items():
                print(f"    {key}: {value:.2f}")
