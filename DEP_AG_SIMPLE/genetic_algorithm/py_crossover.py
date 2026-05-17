"""
PyCrossover: operadores de cruzamiento para el AG simple.
"""

import random

from core.py_chromosome import PyChromosome


class PyCrossover:
    def __init__(self, config):
        self.config = config
        self.random = random.Random(config.random_seed + 2)

    def crossover(self, parent_1, parent_2):
        if self.random.random() > self.config.crossover_rate:
            return parent_1.copy(), parent_2.copy()

        child_1_matrix = []
        child_2_matrix = []

        for row_1, row_2 in zip(parent_1.matrix, parent_2.matrix):
            child_1_row = []
            child_2_row = []

            for gene_1, gene_2 in zip(row_1, row_2):
                if self.random.random() < 0.5:
                    child_1_row.append(gene_1)
                    child_2_row.append(gene_2)
                else:
                    child_1_row.append(gene_2)
                    child_2_row.append(gene_1)

            child_1_matrix.append(child_1_row)
            child_2_matrix.append(child_2_row)

        return PyChromosome(child_1_matrix), PyChromosome(child_2_matrix)
