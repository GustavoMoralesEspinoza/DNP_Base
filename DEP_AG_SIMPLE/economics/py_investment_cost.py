"""
PyInvestmentCost: Cálculo de costo de inversión multiestágio.

Calcula el costo de inversión para un cromosoma, comparando
decisiones de líneas entre etapas consecutivas.
"""


class PyInvestmentCost:
    """
    Calcula el costo de inversión multiestágio para un cromosoma.
    
    Lógica:
    - Para etapa 1: comparar vs base_option_by_line (estado inicial)
    - Para etapas 2+: comparar vs etapa anterior del cromosoma
    - Aplicar reglas de costo según tipo de transición
    """

    def __init__(self, config, data):
        """
        Inicializa el calculador de costo de inversión.
        
        Args:
            config (PyConfigBase): parámetros (removal_factor, interest_rate, stage_years)
            data (dict): datos del sistema (line_catalog, base_option_by_line, etc.)
        """
        self.config = config
        self.data = data
        self.removal_factor = config.removal_factor
        
        # Construir mapeo determinístico: line_id → índice cromosoma
        self.line_ids = sorted(data['line_catalog'].keys())
        self.line_id_to_idx = {lid: idx for idx, lid in enumerate(self.line_ids)}
        self.idx_to_line_id = {idx: lid for idx, lid in enumerate(self.line_ids)}
        
        self.validation_errors = []
        self.validation_warnings = []

    def calculate_max_investment_reference(self):
        """
        Calcula la referencia maxima de inversion para normalizacion.

        Cinv_max = n_stages * sum(max_cost_by_line)

        Para cada linea se toma el costo mas alto entre sus opciones validas.
        """
        max_cost_sum = 0.0

        for line_id in self.line_ids:
            valid_options = self.data['valid_options_by_line'].get(line_id, [])
            max_cost_by_line = 0.0

            for option_id in valid_options:
                option_cost = self._get_option_cost(line_id, option_id)
                if option_cost > max_cost_by_line:
                    max_cost_by_line = option_cost

            max_cost_sum += max_cost_by_line

        c_inv_max_reference = self.config.n_stages * max_cost_sum
        return c_inv_max_reference

    def evaluate_chromosome(self, chromosome):
        """
        Calcula costo de inversión total multiestágio para un cromosoma.
        
        Args:
            chromosome (PyChromosome): cromosoma a evaluar
        
        Returns:
            dict: {
                "total_cost": float,
                "cost_by_stage": {1: cost1, 2: cost2, 3: cost3},
                "cost_by_line": {line_id: cost},
                "transitions": [list of transition dicts],
                "validation_errors": [],
                "validation_warnings": []
            }
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Validar dimensiones
        if chromosome.n_genes() != len(self.line_ids):
            msg = f"ERROR: Cromosoma tiene {chromosome.n_genes()} genes pero hay {len(self.line_ids)} líneas"
            self.validation_errors.append(msg)
            raise ValueError(msg)
        
        cost_by_stage = {}
        cost_by_line = {lid: 0.0 for lid in self.line_ids}
        all_transitions = []
        total_cost = 0.0
        
        # Procesar cada etapa
        for stage_idx in range(chromosome.n_stages()):
            stage_num = stage_idx + 1
            cost_by_stage[stage_num] = 0.0
            
            # Obtener estado anterior (base o etapa anterior)
            previous_state = self._get_previous_state(chromosome, stage_idx)
            current_state = chromosome.matrix[stage_idx]
            
            # Calcular transición para cada línea
            for line_idx in range(len(self.line_ids)):
                line_id = self.idx_to_line_id[line_idx]
                prev_option = previous_state[line_idx]
                curr_option = current_state[line_idx]
                
                # Calcular costo de transición
                transition = self._calculate_transition_cost(
                    line_id, line_idx, prev_option, curr_option, stage_num
                )
                
                all_transitions.append(transition)
                
                cost = transition['cost']
                cost_by_stage[stage_num] += cost
                cost_by_line[line_id] += cost
                total_cost += cost
                
                # Registrar errores/warnings
                if transition.get('error'):
                    self.validation_errors.append(transition['error'])
                if transition.get('warning'):
                    self.validation_warnings.append(transition['warning'])
        
        return {
            "total_cost": total_cost,
            "cost_by_stage": cost_by_stage,
            "cost_by_line": cost_by_line,
            "transitions": all_transitions,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings
        }

    def _get_previous_state(self, chromosome, stage_idx):
        """
        Obtiene el estado anterior a un stage.
        
        - Si stage_idx == 0: retorna base_option_by_line convertido a lista ordenada
        - Si stage_idx > 0: retorna chromosome.matrix[stage_idx - 1]
        
        Returns:
            list: opciones anteriores indexadas por índice cromosoma
        """
        if stage_idx == 0:
            # Convertir base_option_by_line a lista ordenada por line_id
            base_state = [
                self.data['base_option_by_line'].get(self.idx_to_line_id[idx], 0)
                for idx in range(len(self.line_ids))
            ]
            return base_state
        else:
            return chromosome.matrix[stage_idx - 1]

    def _calculate_transition_cost(self, line_id, line_idx, prev_option, curr_option, stage_num):
        """
        Calcula costo de transición según reglas.
        
        Reglas:
        1. prev == curr → cost = 0 (sin cambios)
        2. -1 → X → cost = cost(X) (instalación)
        3. X → -1 → cost = removal_factor * cost(X) (remoción)
        4. X → Y → cost = cost(Y) + removal_factor * cost(X) (reemplazo)
        
        Returns:
            dict: {line_id, prev_option, curr_option, cost, reason, stage, error, warning}
        """
        result = {
            'line_id': line_id,
            'line_idx': line_idx,
            'stage': stage_num,
            'prev_option': prev_option,
            'curr_option': curr_option,
            'cost': 0.0,
            'reason': 'no_change',
            'error': None,
            'warning': None
        }
        
        # Regla 1: Sin cambios
        if prev_option == curr_option:
            result['reason'] = 'no_change'
            result['cost'] = 0.0
            return result
        
        # Validar opciones
        is_prev_valid, prev_error = self._validate_option(line_id, prev_option)
        is_curr_valid, curr_error = self._validate_option(line_id, curr_option)
        
        if not is_curr_valid and curr_option != -1:
            msg = f"Etapa {stage_num}: Línea {line_id} opción inválida {curr_option}"
            result['error'] = msg
            result['cost'] = 1e6  # Penalidad alta
            result['reason'] = 'invalid_option'
            return result
        
        # Regla 2: Instalación (-1 → X)
        if prev_option == -1 and curr_option != -1:
            cost = self._get_option_cost(line_id, curr_option)
            result['reason'] = 'installation'
            result['cost'] = cost
            return result
        
        # Regla 3: Remoción (X → -1)
        if prev_option != -1 and curr_option == -1:
            prev_cost = self._get_option_cost(line_id, prev_option)
            removal_cost = self.removal_factor * prev_cost
            result['reason'] = 'removal'
            result['cost'] = removal_cost
            msg = f"Etapa {stage_num}: Línea {line_id} removida (opción {prev_option} → -1)"
            result['warning'] = msg
            return result
        
        # Regla 4: Reemplazo (X → Y, ambos != -1 y X != Y)
        if prev_option != -1 and curr_option != -1 and prev_option != curr_option:
            curr_cost = self._get_option_cost(line_id, curr_option)
            prev_cost = self._get_option_cost(line_id, prev_option)
            replacement_cost = curr_cost + self.removal_factor * prev_cost
            result['reason'] = 'replacement'
            result['cost'] = replacement_cost
            return result
        
        return result

    def _validate_option(self, line_id, option_id):
        """
        Valida que una opción sea legal para una línea.
        
        Returns:
            (is_valid: bool, error_msg: str or None)
        """
        # -1 siempre es válido (significa "no existe")
        if option_id == -1:
            return True, None
        
        if line_id not in self.data['valid_options_by_line']:
            return False, f"Línea {line_id} no encontrada en catálogo"
        
        valid_opts = self.data['valid_options_by_line'][line_id]
        if option_id not in valid_opts:
            return False, f"Opción {option_id} no válida para {line_id} (válidas: {valid_opts})"
        
        return True, None

    def _get_option_cost(self, line_id, option_id):
        """
        Obtiene costo de una opción específica.
        
        Returns:
            float: costo en USD
        """
        if option_id == -1:
            return 0.0
        
        try:
            cost = self.data['line_catalog'][line_id]['options_detail'][option_id]['cost']
            return cost
        except KeyError:
            msg = f"Línea {line_id} opción {option_id} no tiene costo definido"
            self.validation_warnings.append(msg)
            return 0.0
