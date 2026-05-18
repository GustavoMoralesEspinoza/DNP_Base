"""
PyPlanningProblem: evaluador central del problema DEP.

Evalua cromosomas usando costo de inversion, valor presente,
funcion objetivo simple y validacion topologica opcional.
"""

from core.py_evaluation_result import PyEvaluationResult


class PyPlanningProblem:
    """
    Problema de planeamiento usado por el algoritmo genetico simple.
    """

    def __init__(
        self,
        config,
        data,
        investment_cost,
        present_value,
        objective_function,
        topology_validator=None,
        topology_repair=None
    ):
        self.config = config
        self.data = data
        self.investment_cost = investment_cost
        self.present_value = present_value
        self.objective_function = objective_function
        self.topology_validator = topology_validator
        self.topology_repair = topology_repair
        self.cache = {}

    def evaluate(self, chromosome):
        """
        Evalua un cromosoma y guarda el resultado en cache.
        """
        chromosome_key = chromosome.to_key()
        if chromosome_key in self.cache:
            return self.cache[chromosome_key]

        repair_result = None
        evaluated_chromosome = chromosome

        if (
            getattr(self.config, "use_topology_repair", False)
            and self.topology_repair is not None
        ):
            evaluated_chromosome, repair_result = self.topology_repair.repair(chromosome)

        investment_result = self._calculate_investment(evaluated_chromosome)
        investment_pv_result = self._calculate_present_value(
            investment_result["cost_by_stage"]
        )

        warnings = list(investment_result.get(
            "warnings",
            investment_result.get("validation_warnings", [])
        ))
        validation_errors = investment_result.get("validation_errors", [])

        topology_result = None
        penalty_breakdown = self._empty_penalty_breakdown()
        penalty_breakdown["warnings"] = len(warnings) * self.config.penalty_warning
        penalty_breakdown["invalid_option"] = (
            len(validation_errors) * self.config.penalty_invalid_option
        )

        if (
            getattr(self.config, "use_topology_validation", False)
            and self.topology_validator is not None
        ):
            topology_result = self.topology_validator.validate(evaluated_chromosome)
            warnings.extend(topology_result.get("warnings", []))
            self._merge_penalty_breakdown(
                penalty_breakdown,
                topology_result.get("penalty_breakdown", {})
            )

        penalty_breakdown["warnings"] = len(warnings) * self.config.penalty_warning
        penalty_breakdown["total"] = sum(
            value for key, value in penalty_breakdown.items()
            if key != "total"
        )

        objective_result = self.objective_function.calculate(
            investment_pv_result=investment_pv_result,
            electrical_loss_pv_result=None,
            warnings=warnings,
            penalty_breakdown=penalty_breakdown
        )

        evaluation_result = PyEvaluationResult(
            chromosome=evaluated_chromosome.copy(),
            fitness=objective_result["fitness"],
            c_inv=objective_result["c_inv_total"],
            c_ele=objective_result["c_ele_total"],
            penalty=objective_result["penalty"],
            topology_result=topology_result,
            dss_results=None,
            is_feasible=objective_result["is_feasible"],
            repair_result=repair_result
        )

        evaluation_result.investment_result = investment_result
        evaluation_result.investment_pv_result = investment_pv_result
        evaluation_result.objective_result = objective_result
        evaluation_result.warnings = warnings
        evaluation_result.original_chromosome = chromosome.copy()

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

    def _empty_penalty_breakdown(self):
        return {
            "invalid_option": 0.0,
            "warnings": 0.0,
            "topology_cycle": 0.0,
            "topology_nodes_in_cycles": 0.0,
            "topology_isolated_bus": 0.0,
            "topology_disconnected_load": 0.0,
            "topology_component_without_source": 0.0,
            "topology_multiple_sources": 0.0,
            "extra_penalties": 0.0,
            "total": 0.0
        }

    def _merge_penalty_breakdown(self, target, source):
        for key, value in source.items():
            if key in target and key != "total":
                target[key] += value
            elif key != "total":
                target["extra_penalties"] += value
