"""
main.py: demostracion de FASE 6 - AG simple sin OpenDSS.
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
from genetic_algorithm.py_simple_ga import PySimpleGA


def main():
    print("\n" + "=" * 70)
    print("DEP_AG_SIMPLE - FASE 6: Algoritmo Genetico simple sin OpenDSS")
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

    present_value = PyPresentValue(config)
    objective_function = PyObjectiveFunction(config)

    problem = PyPlanningProblem(
        config=config,
        data=data,
        investment_cost=investment_cost,
        present_value=present_value,
        objective_function=objective_function
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


if __name__ == "__main__":
    main()
