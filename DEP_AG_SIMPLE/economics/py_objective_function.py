"""
PyObjectiveFunction: funcion objetivo simple por pesos.

Calcula:
    fitness = w_inv * c_inv_pu + w_ele * c_ele_pu + penalty

La FASE 5 solo usa inversion en valor presente. Las perdidas electricas
quedan en cero hasta integrar OpenDSS y el calculo de perdidas.
"""


class PyObjectiveFunction:
    """
    Funcion objetivo multiobjetivo simple con pesos.
    """

    def __init__(self, config):
        self.config = config
        self.validate_weights()

    def calculate(
        self,
        investment_pv_result,
        electrical_loss_pv_result=None,
        extra_penalties=None,
        warnings=None
    ):
        """
        Calcula el fitness total a partir de costos en valor presente.
        """
        if warnings is None:
            warnings = []

        c_inv_total = investment_pv_result["total_pv"]

        if electrical_loss_pv_result is None:
            c_ele_total = 0.0
        else:
            c_ele_total = electrical_loss_pv_result["total_pv"]

        c_inv_pu = self.normalize(c_inv_total, self.config.c_inv_max, "inversion")
        c_ele_pu = self.normalize(c_ele_total, self.config.c_ele_max, "perdidas electricas")

        weighted_investment = self.config.w_inv * c_inv_pu
        weighted_electrical_losses = self.config.w_ele * c_ele_pu
        penalty = self.calculate_penalty(warnings, extra_penalties)
        fitness = weighted_investment + weighted_electrical_losses + penalty

        return {
            "fitness": fitness,
            "c_inv_total": c_inv_total,
            "c_ele_total": c_ele_total,
            "c_inv_pu": c_inv_pu,
            "c_ele_pu": c_ele_pu,
            "weighted_investment": weighted_investment,
            "weighted_electrical_losses": weighted_electrical_losses,
            "penalty": penalty,
            "is_feasible": penalty == 0,
            "warnings": warnings if warnings is not None else []
        }

    def normalize(self, value, max_value, label):
        """
        Normaliza un costo usando el maximo configurado.
        """
        minimum_value = self.config.minimum_normalization_value

        if max_value is None or max_value <= minimum_value:
            print(
                f"Advertencia: maximo de normalizacion para {label} invalido "
                f"({max_value}). Se usa {minimum_value}."
            )
            max_value = minimum_value

        return value / max_value

    def calculate_penalty(self, warnings=None, extra_penalties=None):
        """
        Calcula penalidades por warnings y penalidades adicionales.
        """
        penalty = 0.0

        if warnings:
            penalty += len(warnings) * self.config.penalty_warning

        if isinstance(extra_penalties, (int, float)):
            penalty += extra_penalties
        elif isinstance(extra_penalties, list):
            penalty += sum(extra_penalties)

        return float(penalty)

    def validate_weights(self):
        """
        Valida pesos de la funcion objetivo.
        """
        if self.config.w_inv < 0:
            raise ValueError("w_inv debe ser mayor o igual a 0")

        if self.config.w_ele < 0:
            raise ValueError("w_ele debe ser mayor o igual a 0")

        weight_sum = self.config.w_inv + self.config.w_ele
        if abs(weight_sum - 1.0) > 1e-6:
            print(
                "Advertencia: w_inv + w_ele = "
                f"{weight_sum:.6f}, se esperaba aproximadamente 1.0."
            )

    def print_objective_summary(self, objective_result):
        """
        Imprime un resumen legible de la funcion objetivo.
        """
        print("\n" + "-" * 70)
        print("Resumen de funcion objetivo:")
        print("-" * 70)
        print(f"Costo inversion total VP: {objective_result['c_inv_total']:.2f}")
        print(f"Costo perdidas electricas total VP: {objective_result['c_ele_total']:.2f}")
        print(f"Cinv p.u.: {objective_result['c_inv_pu']:.6f}")
        print(f"Cele p.u.: {objective_result['c_ele_pu']:.6f}")
        print(
            "Componente inversion ponderado: "
            f"{objective_result['weighted_investment']:.6f}"
        )
        print(
            "Componente perdidas electricas ponderado: "
            f"{objective_result['weighted_electrical_losses']:.6f}"
        )
        print(f"Penalidad: {objective_result['penalty']:.2f}")
        print(f"Fitness final: {objective_result['fitness']:.6f}")
        print(f"Factible: {objective_result['is_feasible']}")

        warnings = objective_result.get("warnings", [])
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        print("-" * 70 + "\n")
