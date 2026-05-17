"""
PyPresentValue: Cálculo de valor presente para flujos de caja multiestágio.

Convierte costos distribuidos en tiempo a valor presente (año 0).
"""


class PyPresentValue:
    """
    Calcula valor presente de costos multiestágio.
    
    Transforma costos distribuidos en tiempo a valor presente (año 0)
    usando una tasa de descuento.
    """

    def __init__(self, config):
        """
        Inicializa el calculador de valor presente.
        
        Args:
            config (PyConfigBase): parámetros (interest_rate, stage_years)
        """
        self.config = config
        self.interest_rate = config.interest_rate
        self.stage_years = config.stage_years
        
        # Calcular años acumulados
        self.cumulative_years = self._calculate_cumulative_years()

    def _calculate_cumulative_years(self):
        """
        Calcula años acumulados al inicio de cada etapa.
        
        Ejemplo:
        stage_years = [1, 1, 2]
        cumulative_years = [0, 1, 2, 4]  # Al inicio de etapas 1,2,3,4
        
        Returns:
            list: años acumulados
        """
        cumulative = [0]
        total_years = 0
        for years in self.stage_years:
            total_years += years
            cumulative.append(total_years)
        return cumulative

    def get_discount_factor(self, stage_idx):
        """
        Obtiene factor de descuento para una etapa.
        
        DF = 1 / (1 + interest_rate) ^ year
        
        Args:
            stage_idx (int): índice de etapa (0-based)
        
        Returns:
            float: factor de descuento
        """
        if stage_idx < 0 or stage_idx >= len(self.stage_years):
            raise ValueError(f"Índice de etapa {stage_idx} fuera de rango")
        
        year = self.cumulative_years[stage_idx]
        
        if self.interest_rate == 0:
            return 1.0
        
        df = 1.0 / ((1.0 + self.interest_rate) ** year)
        return df

    def calculate_pv_investment(self, costs_by_stage):
        """
        Calcula valor presente de inversiones.
        
        Inversión ocurre al INICIO de cada etapa.
        
        Args:
            costs_by_stage (dict): {1: cost1, 2: cost2, 3: cost3}
        
        Returns:
            dict: {
                "pv_by_stage": {1: pv1, 2: pv2, 3: pv3},
                "total_pv": float,
                "discount_factors": {1: df1, 2: df2, 3: df3}
            }
        """
        pv_by_stage = {}
        discount_factors = {}
        total_pv = 0.0
        
        for stage_num in sorted(costs_by_stage.keys()):
            stage_idx = stage_num - 1
            cost = costs_by_stage[stage_num]
            
            # Calcular factor de descuento
            df = self.get_discount_factor(stage_idx)
            discount_factors[stage_num] = df
            
            # Calcular PV
            pv = cost * df
            pv_by_stage[stage_num] = pv
            total_pv += pv
        
        return {
            "pv_by_stage": pv_by_stage,
            "total_pv": total_pv,
            "discount_factors": discount_factors
        }

    def calculate_pv_operational(self, annual_costs_by_stage):
        """
        Calcula valor presente de costos operativos anuales.
        
        Los costos operativos se repiten cada año dentro de la etapa.
        
        Ejemplo:
        - Etapa 1 (1 año): costo anual 100
          → PV = 100 / (1.1)^0 = 100
        - Etapa 2 (1 año): costo anual 100
          → PV = 100 / (1.1)^1 = 90.91
        - Etapa 3 (2 años): costo anual 100
          → PV = 100/(1.1)^2 + 100/(1.1)^3 = 82.64 + 75.13 = 157.77
        
        Args:
            annual_costs_by_stage (dict): {1: annual_cost1, 2: annual_cost2, 3: annual_cost3}
        
        Returns:
            dict: {
                "pv_by_stage": {1: pv1, 2: pv2, 3: pv3},
                "total_pv": float,
                "explanation": str
            }
        """
        pv_by_stage = {}
        total_pv = 0.0
        explanation_lines = []
        
        for stage_num in sorted(annual_costs_by_stage.keys()):
            stage_idx = stage_num - 1
            annual_cost = annual_costs_by_stage[stage_num]
            years_in_stage = self.stage_years[stage_idx]
            
            stage_pv = 0.0
            exp = f"Etapa {stage_num} ({years_in_stage} años): "
            
            # Sumar PV para cada año en la etapa
            start_year = self.cumulative_years[stage_idx]
            for year_offset in range(years_in_stage):
                year = start_year + year_offset
                if self.interest_rate == 0:
                    df = 1.0
                else:
                    df = 1.0 / ((1.0 + self.interest_rate) ** year)
                pv_year = annual_cost * df
                stage_pv += pv_year
                exp += f" "
            
            pv_by_stage[stage_num] = stage_pv
            total_pv += stage_pv
            explanation_lines.append(f"{exp}= ")
        
        return {
            "pv_by_stage": pv_by_stage,
            "total_pv": total_pv,
            "explanation": "\n".join(explanation_lines)
        }

    def calculate_total_pv(self, investment_costs, operational_costs=None):
        """
        Suma valor presente de inversión + operacionales.
        
        Args:
            investment_costs (dict): {1: cost1, 2: cost2, ...}
            operational_costs (dict, optional): {1: cost1, 2: cost2, ...}
        
        Returns:
            float: valor presente total
        """
        pv_inv = self.calculate_pv_investment(investment_costs)
        total = pv_inv['total_pv']
        
        if operational_costs:
            pv_op = self.calculate_pv_operational(operational_costs)
            total += pv_op['total_pv']
        
        return total
