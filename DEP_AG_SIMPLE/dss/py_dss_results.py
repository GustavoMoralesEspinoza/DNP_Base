"""
PyDSSResults: contenedor de resultados de simulacion OpenDSS 24 h.

FASE 10 solo registra resultados para la mejor solucion final. Las perdidas
electricas todavia no se integran al fitness ni al valor presente.
"""


class PyDSSResults:
    def __init__(self):
        self.stage_results = []
        self.total_energy_losses_kwh = 0.0
        self.total_losses_by_stage_kwh = []
        self.has_errors = False
        self.errors = []

    def add_stage_result(self, stage_result):
        self.stage_results.append(stage_result)

        energy_losses = stage_result.get("energy_losses_kwh", 0.0) or 0.0
        self.total_losses_by_stage_kwh.append(energy_losses)
        self.total_energy_losses_kwh += energy_losses

        if not stage_result.get("success", False):
            self.has_errors = True

        for error in stage_result.get("errors", []):
            self.errors.append(error)

    def print_summary(self):
        print("\n" + "=" * 70)
        print("Resumen OpenDSS:")
        print("=" * 70)
        print(f"  Etapas simuladas: {len(self.stage_results)}")
        print(f"  Perdidas totales kWh: {self.total_energy_losses_kwh:.6f}")

        if self.errors:
            print("  Errores:")
            for error in self.errors:
                print(f"   - {error}")

        for stage_result in self.stage_results:
            hourly_active_power = stage_result.get("hourly_active_power_kw", [])
            max_active_power = max(hourly_active_power) if hourly_active_power else 0.0
            min_active_power = min(hourly_active_power) if hourly_active_power else 0.0

            vmin = self._format_optional(stage_result.get("min_voltage_pu"))
            vmax = self._format_optional(stage_result.get("max_voltage_pu"))
            max_current = self._format_optional(stage_result.get("max_line_current_a"))

            print(f"\nEtapa {stage_result.get('stage_index')}:")
            print(f"  Exito: {stage_result.get('success')}")
            print(
                "  Energia perdida kWh: "
                f"{stage_result.get('energy_losses_kwh', 0.0):.6f}"
            )
            print(f"  P activa minima kW: {min_active_power:.6f}")
            print(f"  P activa maxima kW: {max_active_power:.6f}")
            if (
                hourly_active_power
                and abs(max_active_power - min_active_power) <= 1e-6
            ):
                print(
                    "  WARNING: La potencia activa diaria no vario. "
                    "Verificar LoadShapes."
                )
            print(f"  Vmin pu: {vmin}")
            print(f"  Vmax pu: {vmax}")
            print(
                "  Violaciones de tension: "
                f"{stage_result.get('n_voltage_violations', 0)}"
            )
            print(f"  Corriente maxima A: {max_current}")
            print(
                "  Violaciones de corriente: "
                f"{stage_result.get('n_current_violations', 0)}"
            )

        print("=" * 70 + "\n")

    def _format_optional(self, value):
        if value is None:
            return "None"
        return f"{value:.6f}"
