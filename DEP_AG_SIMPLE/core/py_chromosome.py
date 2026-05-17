"""
PyChromosome: Representación de una solución de DEP como matriz cromosómica.

El cromosoma es una matriz donde:
- Filas = etapas de planeamiento
- Columnas = líneas candidatas
- Valores = opción de línea (código de la acción a tomar)
"""


class PyChromosome:
    """
    Representa una solución de DEP como matriz cromosómica.
    
    La matriz almacena decisiones de inversión en líneas a lo largo de las
    etapas de planeamiento. Cada celda contiene un código de acción para
    una línea en una etapa particular.
    
    Ejemplo de matriz (3 etapas x 4 líneas candidatas):
        [
            [0, 1, -1, 2],    # Etapa 1: acciones para cada línea
            [0, 1,  0, 2],    # Etapa 2
            [1, 2,  0, 3],    # Etapa 3
        ]
    
    Convención de valores:
        0 = no construir / línea sin cambios
        1, 2, 3, ... = diferentes opciones de construcción/mejora
        -1 = línea no disponible / prohibida en esa etapa
    """

    def __init__(self, matrix):
        """
        Inicializa el cromosoma con una matriz.
        
        Args:
            matrix: matriz de decisiones (lista de listas o similar).
                   Filas = etapas, Columnas = líneas candidatas.
        """
        self.matrix = matrix

    def copy(self):
        """
        Retorna una copia profunda del cromosoma.
        
        Returns:
            PyChromosome: nuevo cromosoma con copia de la matriz.
        """
        # Copia profunda: crea nueva lista de listas
        matrix_copy = [row[:] for row in self.matrix]
        return PyChromosome(matrix_copy)

    def to_key(self):
        """
        Convierte la matriz del cromosoma a un string único (key).
        
        Útil para usar como clave en diccionarios (cache de evaluaciones).
        
        Returns:
            str: representación string de la matriz separada por guiones.
                Ej: "0_1_-1_2__0_1_0_2__1_2_0_3"
        """
        rows_str = []
        for row in self.matrix:
            row_str = "_".join(str(val) for val in row)
            rows_str.append(row_str)
        return "__".join(rows_str)

    def n_stages(self):
        """
        Retorna el número de etapas de planeamiento (filas de la matriz).
        
        Returns:
            int: número de filas.
        """
        return len(self.matrix)

    def n_genes(self):
        """
        Retorna el número de genes (líneas candidatas, columnas de la matriz).
        
        Asume que todas las filas tienen el mismo número de columnas.
        
        Returns:
            int: número de columnas en la primera fila.
        """
        if len(self.matrix) == 0:
            return 0
        return len(self.matrix[0])

    def print_chromosome(self):
        """
        Imprime en consola la matriz del cromosoma en formato tabla legible.
        """
        print("\n" + "-"*60)
        print("CROMOSOMA (Matriz de Decisiones)")
        print("-"*60)
        print(f"Etapas: {self.n_stages()} | Líneas candidatas: {self.n_genes()}")
        print()
        
        # Encabezado con números de columna
        header = "Etapa |"
        for j in range(self.n_genes()):
            header += f" {j:4d} |"
        print(header)
        print("-" * len(header))
        
        # Filas de datos
        for i, row in enumerate(self.matrix):
            row_str = f"  {i}   |"
            for val in row:
                row_str += f" {val:4d} |"
            print(row_str)
        
        print("-"*60)
        print(f"Key (para cache): {self.to_key()}")
        print("-"*60 + "\n")
