"""
PyElectricalLossCost: costo anual de perdidas electricas desde OpenDSS.
"""


class PyElectricalLossCost:
    def __init__(self, config, data=None):
        self.config = config
        self.data = data

    def calculate(self, dss_results):
        warnings = []
        losses_kwh_day_by_stage = []
        stage_results = getattr(dss_results, "stage_results", [])
        n_stages = getattr(self.config, "n_stages", len(stage_results))

        for stage_index in range(n_stages):
            if stage_index >= len(stage_results):
                losses_kwh_day_by_stage.append(0.0)
                warnings.append(
                    f"Falta resultado OpenDSS para etapa {stage_index + 1}"
                )
                continue

            losses_kwh = stage_results[stage_index].get("energy_losses_kwh", 0.0)
            if losses_kwh is None:
                losses_kwh = 0.0
                warnings.append(
                    f"Perdidas electricas ausentes en etapa {stage_index + 1}"
                )
            losses_kwh_day_by_stage.append(float(losses_kwh))

        losses_kwh_year_by_stage = [
            value * self.config.days_per_year
            for value in losses_kwh_day_by_stage
        ]
        annual_cost_by_stage = self.calculate_annual_costs_by_stage(
            losses_kwh_day_by_stage
        )

        return {
            "losses_kwh_day_by_stage": losses_kwh_day_by_stage,
            "losses_kwh_year_by_stage": losses_kwh_year_by_stage,
            "annual_cost_by_stage": annual_cost_by_stage,
            "total_annual_cost": sum(annual_cost_by_stage),
            "warnings": warnings
        }

    def calculate_annual_costs_by_stage(self, losses_kwh_by_stage):
        annual_costs = []
        for losses_kwh_day in losses_kwh_by_stage:
            losses_kwh_year = losses_kwh_day * self.config.days_per_year
            annual_costs.append(losses_kwh_year * self.config.energy_price)
        return annual_costs

    def calculate_max_electrical_loss_reference(self):
        return max(float(getattr(self.config, "c_ele_max", 1.0)), 1.0)

    def print_loss_cost_summary(self, loss_cost_result):
        if not loss_cost_result:
            return

        print("\n" + "-" * 70)
        print("Perdidas electricas:")
        print("-" * 70)

        losses_day = loss_cost_result.get("losses_kwh_day_by_stage", [])
        losses_year = loss_cost_result.get("losses_kwh_year_by_stage", [])
        annual_costs = loss_cost_result.get("annual_cost_by_stage", [])

        for index, daily_loss in enumerate(losses_day):
            yearly_loss = losses_year[index] if index < len(losses_year) else 0.0
            annual_cost = annual_costs[index] if index < len(annual_costs) else 0.0
            print(f"  Stage {index + 1}:")
            print(f"    kWh/dia: {daily_loss:.6f}")
            print(f"    kWh/ano: {yearly_loss:.6f}")
            print(f"    costo anual: {annual_cost:.6f}")

        print(
            "  Costo anual total: "
            f"{loss_cost_result.get('total_annual_cost', 0.0):.6f}"
        )

        warnings = loss_cost_result.get("warnings", [])
        if warnings:
            print("  Warnings:")
            for warning in warnings:
                print(f"    - {warning}")

        print("-" * 70 + "\n")
