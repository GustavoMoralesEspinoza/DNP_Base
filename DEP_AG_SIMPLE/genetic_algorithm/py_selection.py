"""
PySelection: seleccion de padres para el AG simple.
"""

import random


class PySelection:
    def __init__(self, config):
        self.config = config
        self.random = random.Random(config.random_seed + 1)

    def tournament_selection(self, evaluated_population, tournament_size=3):
        tournament_size = min(tournament_size, len(evaluated_population))
        candidates = self.random.sample(evaluated_population, tournament_size)
        return min(candidates, key=lambda result: result.fitness)

    def select_parents(self, evaluated_population, n_parents):
        parents = []
        for _ in range(n_parents):
            selected_result = self.tournament_selection(evaluated_population)
            parents.append(selected_result.chromosome.copy())
        return parents
