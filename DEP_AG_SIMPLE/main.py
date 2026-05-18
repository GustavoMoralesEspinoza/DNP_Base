"""
main.py: demostracion de FASE 7 - AG simple con validacion topologica.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config.py_config_base import PyConfigBase
from core.py_planning_problem import PyPlanningProblem
from data.py_data_reader import PyDataReader
from economics.py_investment_cost import PyInvestmentCost
from economics.py_present_value import PyPresentValue
from economics.py_objective_function import PyObjectiveFunction
from economics.py_electrical_loss_cost import PyElectricalLossCost
from genetic_algorithm.py_simple_ga import PySimpleGA
from topology.py_topology_validator import PyTopologyValidator
from topology.py_topology_repair import PyTopologyRepair
from reports.py_topology_debug_plot import PyTopologyDebugPlot
from dss.py_dss_writer import PyDSSWriter
from dss.py_dss_runner import PyDSSRunner


def main():
    print("\n" + "=" * 70)
    print("DEP_AG_SIMPLE - FASE 7: AG simple con validacion topologica")
    print("=" * 70)

    config = PyConfigBase()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "Initialdata")

    print("\nLeyendo datos iniciales...")
    data_reader = PyDataReader(data_dir)
    data = data_reader.read_all()

    investment_cost = PyInvestmentCost(config, data)
    config.c_inv_max = investment_cost.calculate_max_investment_reference()

    print(f"\nReferencia Cinv max: {config.c_inv_max:.2f}")
    print(f"Individuos: {config.n_individuals}")
    print(f"Iteraciones: {config.n_iterations}")
    print(f"Crossover rate: {config.crossover_rate}")
    print(f"Mutation rate: {config.mutation_rate}")
    print(f"Elitism rate: {config.elitism_rate}")
    print(f"Validacion topologica: {config.use_topology_validation}")
    print(f"use_topology_repair: {config.use_topology_repair}")
    print(f"repair_strategy: {config.repair_strategy}")
    print(f"collapse_sources: {config.collapse_sources}")
    print(f"Equivalent source: {config.equivalent_source_name}")
    print(
        "Allow multiple sources/component:",
        config.allow_multiple_sources_per_component
    )

    present_value = PyPresentValue(config)
    objective_function = PyObjectiveFunction(config)
    dss_writer = PyDSSWriter(config, data)
    dss_runner = PyDSSRunner(config)
    electrical_loss_cost = PyElectricalLossCost(config, data)
    topology_validator = PyTopologyValidator(config, data)
    topology_repair = PyTopologyRepair(
        config=config,
        data=data,
        topology_validator=topology_validator
    )

    problem = PyPlanningProblem(
        config=config,
        data=data,
        investment_cost=investment_cost,
        present_value=present_value,
        objective_function=objective_function,
        topology_validator=topology_validator,
        topology_repair=topology_repair,
        dss_writer=dss_writer,
        dss_runner=dss_runner,
        electrical_loss_cost=electrical_loss_cost
    )

    ga = PySimpleGA(config, problem, data)
    best_result = ga.run()

    print("Mejor cromosoma encontrado:")
    best_result.chromosome.print_chromosome()

    print("Resumen de evaluacion:")
    best_result.summary()

    objective_result = getattr(best_result, "objective_result", None)
    if objective_result is not None:
        objective_function.print_objective_summary(objective_result)

    if best_result.dss_results is not None:
        best_result.dss_results.print_summary()

    if getattr(best_result, "loss_cost_result", None) is not None:
        electrical_loss_cost.print_loss_cost_summary(best_result.loss_cost_result)

    if getattr(best_result, "electrical_loss_pv_result", None) is not None:
        present_value.print_present_value_summary(
            best_result.electrical_loss_pv_result
        )

    if best_result.topology_result is not None:
        topology_validator.print_topology_summary(best_result.topology_result)

    if best_result.repair_result is not None:
        topology_repair.print_repair_summary(best_result.repair_result)

    if config.use_topology_debug_plots:
        topology_debug = PyTopologyDebugPlot(config, data)
        topology_debug.plot_chromosome(
            best_result.chromosome,
            prefix="best_solution"
        )
        print(
            "Graficos de debug topologico guardados en:",
            config.topology_debug_output_folder
        )

    if config.use_dss_writer:
        config.dss_output_folder = "outputs/dss_files"
        dss_files = dss_writer.write_chromosome(
            best_result.chromosome,
            prefix="best_solution"
        )

        print("Archivos DSS generados:")
        for path in dss_files:
            print(" -", path)

        if config.use_dss_runner and not config.use_open_dss_in_fitness:
            dss_runner = PyDSSRunner(config)
            dss_results = dss_runner.run_files_24h(dss_files)
            dss_results.print_summary()


if __name__ == "__main__":
    main()
