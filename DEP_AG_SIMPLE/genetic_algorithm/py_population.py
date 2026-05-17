"""
PyPopulation: creacion de poblaciones para el AG simple.
"""

import random

from core.py_chromosome import PyChromosome


class PyPopulation:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.random = random.Random(config.random_seed)
        self.line_ids = sorted(data["line_catalog"].keys())

    def create_initial_population(self):
        population = []
        for _ in range(self.config.n_individuals):
            population.append(self.create_random_chromosome())
        return population

    def create_random_chromosome(self):
        chromosome_matrix = []

        for _ in range(self.data["n_stages"]):
            stage_row = []
            for line_id in self.line_ids:
                valid_options = self.get_valid_options_for_line(line_id)
                stage_row.append(self.random.choice(valid_options))
            chromosome_matrix.append(stage_row)

        return PyChromosome(chromosome_matrix)

    def get_valid_options_for_line(self, line_id):
        valid_options = list(self.data["valid_options_by_line"].get(line_id, []))

        if -1 not in valid_options:
            valid_options.append(-1)

        if not valid_options:
            valid_options = [-1]

        return valid_options
