"""
PyPlanningProblem: evaluador central del problema DEP.

Evalua cromosomas usando costo de inversion, valor presente,
funcion objetivo simple y validacion topologica opcional.
"""

import os

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
        topology_repair=None,
        dss_writer=None,
        dss_runner=None,
        electrical_loss_cost=None
    ):
        self.config = config
        self.data = data
        self.investment_cost = investment_cost
        self.present_value = present_value
        self.objective_function = objective_function
        self.topology_validator = topology_validator
        self.topology_repair = topology_repair
        self.dss_writer = dss_writer
        self.dss_runner = dss_runner
        self.electrical_loss_cost = electrical_loss_cost
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

        dss_results = None
        loss_cost_result = None
        electrical_loss_pv_result = None

        if self._should_run_open_dss(topology_result):
            (
                dss_results,
                loss_cost_result,
                electrical_loss_pv_result,
                dss_warnings,
                dss_error,
            ) = self._evaluate_electrical_losses(evaluated_chromosome)
            warnings.extend(dss_warnings)
            if dss_error:
                penalty_breakdown["dss_error"] += self.config.penalty_dss_error
            elif dss_results is not None:
                self._merge_penalty_breakdown(
                    penalty_breakdown,
                    self.calculate_technical_penalties_from_dss(dss_results)
                )
        elif self._open_dss_enabled():
            warnings.append(
                "OpenDSS omitido porque la topologia final es invalida"
            )

        penalty_breakdown["warnings"] = len(warnings) * self.config.penalty_warning
        penalty_breakdown["total"] = sum(
            value for key, value in penalty_breakdown.items()
            if key != "total"
        )

        objective_result = self.objective_function.calculate(
            investment_pv_result=investment_pv_result,
            electrical_loss_pv_result=electrical_loss_pv_result,
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
            dss_results=dss_results,
            is_feasible=objective_result["is_feasible"],
            repair_result=repair_result
        )

        evaluation_result.investment_result = investment_result
        evaluation_result.investment_pv_result = investment_pv_result
        evaluation_result.loss_cost_result = loss_cost_result
        evaluation_result.electrical_loss_pv_result = electrical_loss_pv_result
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

    def _open_dss_enabled(self):
        return (
            getattr(self.config, "use_open_dss_in_fitness", False)
            and getattr(self.config, "use_electrical_loss_cost", False)
            and self.dss_writer is not None
            and self.dss_runner is not None
            and self.electrical_loss_cost is not None
        )

    def _should_run_open_dss(self, topology_result):
        if not self._open_dss_enabled():
            return False

        if (
            topology_result is not None
            and not topology_result.get("is_valid", False)
            and getattr(self.config, "skip_opendss_if_topology_invalid", True)
        ):
            return False

        return True

    def _evaluate_electrical_losses(self, chromosome):
        warnings = []
        dss_error = False
        old_output_folder = self.config.dss_output_folder
        old_verbose = getattr(self.config, "dss_runner_verbose", False)
        old_working_dir = os.getcwd()

        try:
            self.config.dss_output_folder = self.config.dss_temp_output_folder
            self.config.dss_runner_verbose = False
            os.makedirs(self.config.dss_temp_output_folder, exist_ok=True)

            dss_files = self.dss_writer.write_chromosome(
                chromosome,
                prefix="eval_current"
            )
            dss_results = self.dss_runner.run_files_24h(dss_files)

            if getattr(dss_results, "has_errors", False):
                dss_error = True
                warnings.extend(getattr(dss_results, "errors", []))
                loss_cost_result = None
                electrical_loss_pv_result = None
            else:
                loss_cost_result = self.electrical_loss_cost.calculate(dss_results)
                warnings.extend(loss_cost_result.get("warnings", []))
                electrical_loss_pv_result = self.present_value.operation(
                    loss_cost_result["annual_cost_by_stage"]
                )

            return (
                dss_results,
                loss_cost_result,
                electrical_loss_pv_result,
                warnings,
                dss_error,
            )
        except Exception as exc:
            warnings.append(f"Error OpenDSS en evaluacion: {exc}")
            return None, None, None, warnings, True
        finally:
            self.config.dss_output_folder = old_output_folder
            self.config.dss_runner_verbose = old_verbose
            os.chdir(old_working_dir)

    def calculate_technical_penalties_from_dss(self, dss_results):
        total_voltage_violations = 0
        total_current_violations = 0

        for stage_result in getattr(dss_results, "stage_results", []):
            total_voltage_violations += stage_result.get(
                "n_voltage_violations",
                0
            )
            total_current_violations += stage_result.get(
                "n_current_violations",
                0
            )

        breakdown = {
            "voltage_violations": 0.0,
            "current_violations": 0.0,
            "total": 0.0
        }

        if getattr(self.config, "use_voltage_penalty", False):
            breakdown["voltage_violations"] = (
                self.config.penalty_voltage_violation
                * total_voltage_violations
            )

        if getattr(self.config, "use_current_penalty", False):
            breakdown["current_violations"] = (
                self.config.penalty_current_violation
                * total_current_violations
            )

        breakdown["total"] = (
            breakdown["voltage_violations"]
            + breakdown["current_violations"]
        )
        return breakdown

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
            "dss_error": 0.0,
            "voltage_violations": 0.0,
            "current_violations": 0.0,
            "extra_penalties": 0.0,
            "total": 0.0
        }

    def _merge_penalty_breakdown(self, target, source):
        for key, value in source.items():
            if key in target and key != "total":
                target[key] += value
            elif key != "total":
                target["extra_penalties"] += value
