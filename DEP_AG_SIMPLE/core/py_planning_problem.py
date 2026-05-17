"""
PyPlanningProblem: evaluador central del problema DEP.

En FASE 6 evalua cromosomas usando solo costo de inversion,
valor presente y funcion objetivo simple. No llama OpenDSS ni topologia.
"""

from core.py_evaluation_result import PyEvaluationResult


class PyPlanningProblem:
    """
    Problema de planeamiento usado por el algoritmo genetico simple.
    """

    def __init__(self, config, data, investment_cost, present_value, objective_function):
        self.config = config
        self.data = data
        self.investment_cost = investment_cost
        self.present_value = present_value
        self.objective_function = objective_function
        self.cache = {}

    def evaluate(self, chromosome):
        """
        Evalua un cromosoma y guarda el resultado en cache.
        """
        chromosome_key = chromosome.to_key()
        if chromosome_key in self.cache:
            return self.cache[chromosome_key]

        investment_result = self._calculate_investment(chromosome)
        investment_pv_result = self._calculate_present_value(
            investment_result["cost_by_stage"]
        )

        warnings = investment_result.get(
            "warnings",
            investment_result.get("validation_warnings", [])
        )

        objective_result = self.objective_function.calculate(
            investment_pv_result=investment_pv_result,
            electrical_loss_pv_result=None,
            warnings=warnings
        )

        evaluation_result = PyEvaluationResult(
            chromosome=chromosome.copy(),
            fitness=objective_result["fitness"],
            c_inv=objective_result["c_inv_total"],
            c_ele=objective_result["c_ele_total"],
            penalty=objective_result["penalty"],
            topology_result=None,
            dss_results=None,
            is_feasible=objective_result["is_feasible"]
        )

        evaluation_result.investment_result = investment_result
        evaluation_result.investment_pv_result = investment_pv_result
        evaluation_result.objective_result = objective_result
        evaluation_result.warnings = warnings

        self.cache[chromosome_key] = evaluation_result
        return evaluation_result

    def _calculate_investment(self, chromosome):
        if hasattr(self.investment_cost, "calculate"):
            return self.investment_cost.calculate(chromosome)
        return self.investment_cost.evaluate_chromosome(chromosome)

    def _calculate_present_value(self, cost_by_stage):
        if hasattr(self.present_value, "investment"):
            return self.present_value.investment(cost_by_stage)
        return self.present_value.calculate_pv_investment(cost_by_stage)
