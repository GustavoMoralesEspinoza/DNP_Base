"""
PySimpleGA: algoritmo genetico simple sin OpenDSS.
"""

from genetic_algorithm.py_population import PyPopulation
from genetic_algorithm.py_selection import PySelection
from genetic_algorithm.py_crossover import PyCrossover
from genetic_algorithm.py_mutation import PyMutation
from genetic_algorithm.py_elitism import PyElitism
from reports.py_ga_report import PyGAReport


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
        self.history_global = []
        self.history_feasible = []
        self.history_population_size = []
        self.evaluation_records = []
        self._current_iteration = None

    def run(self):
        if getattr(self.config, "use_topology_validation", False):
            print("\nIniciando AG simple con validacion topologica...")
        else:
            print("\nIniciando AG simple sin OpenDSS...")

        population = self.population_creator.create_initial_population()

        for iteration in range(1, self.config.n_iterations + 1):
            self._current_iteration = iteration
            evaluated_population = self.evaluate_population(population)
            self.update_history(evaluated_population, iteration)
            self.print_iteration_summary(iteration, evaluated_population)

            if iteration < self.config.n_iterations:
                population = self.create_next_generation(evaluated_population)

        self.print_final_summary()
        self.write_reports()
        return self.best_result

    def evaluate_population(self, population):
        evaluated_population = []

        for individual_index, chromosome in enumerate(population, start=1):
            # PyPlanningProblem.evaluate() may repair the chromosome. From this
            # point on, the AG must use result.chromosome as the individual.
            evaluated_result = self.problem.evaluate(chromosome)
            evaluated_population.append(evaluated_result)
            self.record_evaluation(evaluated_result, individual_index)

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
        self.history_global.append(self.best_result.fitness)
        self.history_feasible.append(feasible_count)
        self.history_population_size.append(len(evaluated_population))

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

    def record_evaluation(self, evaluated_result, individual_index):
        if not (
            getattr(self.config, "use_ga_reports", False)
            or getattr(self.config, "use_ga_plots", False)
        ):
            return

        if (
            not getattr(self.config, "save_all_ga_evaluations", False)
            and not getattr(self.config, "use_ga_plots", False)
        ):
            return

        self.evaluation_records.append({
            "iteration": self._current_iteration,
            "individual": individual_index,
            "result": evaluated_result,
        })

    def write_reports(self):
        reporter = PyGAReport(self.config)
        report_files = reporter.write_reports(self)
        plot_files = reporter.write_plots(self)

        if report_files:
            print("Reportes AG guardados:")
            for path in report_files:
                print(" -", path)

        if plot_files:
            print("Graficos AG guardados:")
            for path in plot_files:
                print(" -", path)

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
