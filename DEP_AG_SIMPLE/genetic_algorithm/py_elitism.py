"""
PyElitism: preservacion de mejores individuos.
"""


class PyElitism:
    def __init__(self, config):
        self.config = config

    def get_elites(self, evaluated_population):
        sorted_population = sorted(
            evaluated_population,
            key=lambda result: result.fitness
        )
        n_elites = max(1, int(self.config.elitism_rate * self.config.n_individuals))
        n_elites = min(n_elites, len(sorted_population))

        return [
            result.chromosome.copy()
            for result in sorted_population[:n_elites]
        ]
