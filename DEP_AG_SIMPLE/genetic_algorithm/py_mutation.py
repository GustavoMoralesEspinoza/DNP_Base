"""
PyMutation: operador de mutacion para el AG simple.
"""

import random

from core.py_chromosome import PyChromosome


class PyMutation:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.random = random.Random(config.random_seed + 3)
        self.line_ids = sorted(data["line_catalog"].keys())

    def mutate(self, chromosome):
        mutated_matrix = [row[:] for row in chromosome.matrix]

        for stage_idx, row in enumerate(mutated_matrix):
            for line_idx, current_option in enumerate(row):
                if self.random.random() < self.config.mutation_rate:
                    line_id = self.line_ids[line_idx]
                    valid_options = self.get_valid_options_for_line(line_id)
                    alternative_options = [
                        option for option in valid_options
                        if option != current_option
                    ]

                    if alternative_options:
                        row[line_idx] = self.random.choice(alternative_options)

        return PyChromosome(mutated_matrix)

    def get_valid_options_for_line(self, line_id):
        valid_options = list(self.data["valid_options_by_line"].get(line_id, []))

        if not valid_options:
            valid_options = [-1]

        return valid_options
