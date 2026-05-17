"""
PySimpleGA: algoritmo genetico simple sin OpenDSS.
"""

from genetic_algorithm.py_population import PyPopulation
from genetic_algorithm.py_selection import PySelection
from genetic_algorithm.py_crossover import PyCrossover
from genetic_algorithm.py_mutation import PyMutation
from genetic_algorithm.py_elitism import PyElitism


class PySimpleGA:
    def __init__(self, config, problem, data):
        self.config = config
        self.problem = problem
        self.data = data

        self.population_creator = PyPopulation(config, data)
        self.selection = PySelection(config)
        self.crossover = PyCrossover(config)
        self.mutation = PyMutation(config, data)
        self.elitism = PyElitism(config)

        self.best_result = None
        self.history_best = []
        self.history_mean = []
        self.history_feasible = []

    def run(self):
        if getattr(self.config, "use_topology_validation", False):
            print("\nIniciando AG simple con validacion topologica...")
        else:
            print("\nIniciando AG simple sin OpenDSS...")

        population = self.population_creator.create_initial_population()

        for iteration in range(1, self.config.n_iterations + 1):
            evaluated_population = self.evaluate_population(population)
            self.update_history(evaluated_population, iteration)
            self.print_iteration_summary(iteration, evaluated_population)

            if iteration < self.config.n_iterations:
                population = self.create_next_generation(evaluated_population)

        self.print_final_summary()
        return self.best_result

    def evaluate_population(self, population):
        evaluated_population = []

        for chromosome in population:
            evaluated_population.append(self.problem.evaluate(chromosome))

        return evaluated_population

    def update_history(self, evaluated_population, iteration):
        best_iteration_result = min(
            evaluated_population,
            key=lambda result: result.fitness
        )

        if (
            self.best_result is None
            or best_iteration_result.fitness < self.best_result.fitness
        ):
            self.best_result = best_iteration_result

        fitness_values = [result.fitness for result in evaluated_population]
        feasible_count = sum(1 for result in evaluated_population if result.is_feasible)

        self.history_best.append(best_iteration_result.fitness)
        self.history_mean.append(sum(fitness_values) / len(fitness_values))
        self.history_feasible.append(feasible_count)

    def create_next_generation(self, evaluated_population):
        next_population = self.elitism.get_elites(evaluated_population)

        while len(next_population) < self.config.n_individuals:
            parent_1, parent_2 = self.selection.select_parents(
                evaluated_population,
                n_parents=2
            )
            child_1, child_2 = self.crossover.crossover(parent_1, parent_2)

            child_1 = self.mutation.mutate(child_1)
            next_population.append(child_1)

            if len(next_population) < self.config.n_individuals:
                child_2 = self.mutation.mutate(child_2)
                next_population.append(child_2)

        return next_population[:self.config.n_individuals]

    def print_iteration_summary(self, iteration, evaluated_population):
        best_iteration_result = min(
            evaluated_population,
            key=lambda result: result.fitness
        )
        mean_fitness = self.history_mean[-1]
        feasible_count = self.history_feasible[-1]

        print(f"\nIteracion {iteration}/{self.config.n_iterations}")
        print(f"Mejor fitness: {best_iteration_result.fitness:.6f}")
        print(f"Fitness promedio: {mean_fitness:.6f}")
        print(f"Mejor global: {self.best_result.fitness:.6f}")
        print(f"Factibles: {feasible_count}/{len(evaluated_population)}")

    def print_final_summary(self):
        print("\n" + "=" * 70)
        print("Resumen final AG:")
        print("=" * 70)

        if self.best_result is None:
            print("No se encontro resultado.")
            print("=" * 70 + "\n")
            return

        print(f"Mejor fitness global: {self.best_result.fitness:.6f}")
        print(f"Costo inversion VP: {self.best_result.c_inv:.2f}")
        print(f"Costo perdidas electricas VP: {self.best_result.c_ele:.2f}")
        print(f"Penalidad: {self.best_result.penalty:.2f}")
        print(f"Factible: {self.best_result.is_feasible}")
        print("=" * 70 + "\n")
