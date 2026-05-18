"""
PyDSSRunner: ejecuta OpenDSS 24 h para archivos DSS generados.

FASE 10 compila los archivos de la mejor solucion final, ejecuta modo daily
durante 24 horas y extrae potencias, perdidas, tensiones y corrientes. No
modifica el fitness.

Nota FASE 11: el costo de perdidas en valor presente debe respetar
stage_years. Con stage_years = [1, 1, 2], la etapa 3 aplica las mismas
perdidas anuales en los anos 3 y 4 antes de descontar ambos flujos.
"""

import math
import os

import numpy as np

try:
    import py_dss_interface
except ImportError:
    py_dss_interface = None

from dss.py_dss_results import PyDSSResults


class PyDSSRunner:
    def __init__(self, config):
        self.config = config
        self.warnings = []
        self.base_working_dir = os.getcwd()

    def run_files_24h(self, dss_files):
        results = PyDSSResults()

        for stage_index, dss_file in enumerate(dss_files, start=1):
            stage_result = self.run_stage_24h(dss_file, stage_index)
            results.add_stage_result(stage_result)

            if getattr(self.config, "dss_runner_verbose", False):
                self.print_stage_summary(stage_result)

            if (
                not stage_result["success"]
                and not getattr(self.config, "dss_continue_on_error", True)
            ):
                break

        return results

    def run_stage_24h(self, dss_file, stage_index):
        dss_file = self._resolve_dss_file(dss_file)
        stage_result = self._empty_stage_result(dss_file, stage_index)

        try:
            dss = self.create_dss_instance()
            ok = self.compile_dss_file(dss, dss_file)
        except Exception as exc:
            ok = False
            stage_result["errors"].append(
                f"Etapa {stage_index}: error creando/compilando OpenDSS: {exc}"
            )

        if not ok:
            stage_result["success"] = False
            if not stage_result["errors"]:
                stage_result["errors"].append(
                    f"Etapa {stage_index}: no se pudo compilar {dss_file}"
                )
            return stage_result

        try:
            for hour in range(getattr(self.config, "dss_simulation_hours", 24)):
                self.solve_hour(dss, hour)
                hour_result = self.extract_hour_results(dss, hour)

                stage_result["hourly_active_power_kw"].append(
                    hour_result["active_power_kw"]
                )
                stage_result["hourly_reactive_power_kvar"].append(
                    hour_result["reactive_power_kvar"]
                )
                stage_result["hourly_losses_kw"].append(hour_result["losses_kw"])
                stage_result["hourly_losses_kvar"].append(hour_result["losses_kvar"])
                stage_result["hourly_voltage_summary"].append(
                    hour_result["voltage_summary"]
                )
                stage_result["hourly_line_current_summary"].append(
                    hour_result["current_summary"]
                )

            self._aggregate_stage_result(stage_result)
        except Exception as exc:
            stage_result["success"] = False
            stage_result["errors"].append(
                f"Etapa {stage_index}: error durante simulacion 24 h: {exc}"
            )

        return stage_result

    def _resolve_dss_file(self, dss_file):
        if os.path.isabs(dss_file):
            return dss_file
        return os.path.abspath(os.path.join(self.base_working_dir, dss_file))

    def create_dss_instance(self):
        if py_dss_interface is None:
            raise ImportError(
                "py_dss_interface no esta instalado en este entorno Python"
            )

        try:
            return py_dss_interface.DSS()
        except Exception:
            return py_dss_interface.DSSDLL()

    def compile_dss_file(self, dss, dss_file):
        if not os.path.exists(dss_file):
            return False

        try:
            dss.text(f"compile [{dss_file}]")
            return True
        except Exception:
            try:
                dss.text(f'compile "{dss_file}"')
                return True
            except Exception:
                return False

    def solve_hour(self, dss, hour):
        dss.text(f"Set mode={getattr(self.config, 'dss_mode', 'daily')}")
        dss.text(f"Set number={hour + 1}")
        dss.text("Solve")

    def extract_hour_results(self, dss, hour):
        losses_kw, losses_kvar = self.extract_losses(dss)
        p_kw, q_kvar = self.extract_total_power(dss)
        voltage_summary = self.extract_voltage_summary(dss)
        current_summary = self.extract_line_current_summary(dss)

        return {
            "hour": hour + 1,
            "losses_kw": losses_kw,
            "losses_kvar": losses_kvar,
            "active_power_kw": p_kw,
            "reactive_power_kvar": q_kvar,
            "voltage_summary": voltage_summary,
            "current_summary": current_summary,
        }

    def extract_losses(self, dss):
        losses = None

        for accessor in [
            lambda: dss.circuit.losses,
            lambda: dss.circuit._losses(),
        ]:
            try:
                losses = accessor()
                break
            except Exception:
                continue

        if losses is None:
            self.warnings.append("No se pudieron extraer perdidas de OpenDSS")
            return 0.0, 0.0

        return abs(losses[0]) / 1000.0, abs(losses[1]) / 1000.0

    def extract_total_power(self, dss):
        total_power = None

        for accessor in [
            lambda: dss.circuit._total_power(),
            lambda: dss.circuit.total_power,
        ]:
            try:
                total_power = accessor()
                break
            except Exception:
                continue

        if total_power is None:
            self.warnings.append("No se pudo extraer potencia total de OpenDSS")
            return 0.0, 0.0

        return abs(total_power[0]), abs(total_power[1])

    def extract_voltage_summary(self, dss):
        bus_names = dss.circuit.buses_names
        all_valid_voltages = []
        n_voltage_violations = 0

        for bus in bus_names:
            dss.circuit.set_active_bus(bus)
            voltages_pu = list(dss.bus.vmag_angle_pu[::2])
            valid_voltages = []

            for voltage in voltages_pu:
                if not self._is_valid_number(voltage):
                    continue
                if voltage < 0.05:
                    continue
                valid_voltages.append(voltage)

            if not valid_voltages:
                continue

            all_valid_voltages.extend(valid_voltages)

            for voltage in valid_voltages:
                if (
                    voltage < self.config.v_min_pu
                    or voltage > self.config.v_max_pu
                ):
                    n_voltage_violations += 1

        if not all_valid_voltages:
            return {
                "min_voltage_pu": None,
                "max_voltage_pu": None,
                "n_voltage_violations": 0
            }

        return {
            "min_voltage_pu": min(all_valid_voltages),
            "max_voltage_pu": max(all_valid_voltages),
            "n_voltage_violations": n_voltage_violations
        }

    def extract_line_current_summary(self, dss):
        line_names = dss.lines.names
        max_current = 0.0
        n_current_violations = 0

        for line in line_names:
            dss.lines.name = line
            norm_amps = dss.lines.norm_amps

            dss.circuit.set_active_element(f"Line.{line}")
            currents = list(dss.cktelement.currents_mag_ang[:6:2])
            valid_currents = []

            for current in currents:
                if not self._is_valid_number(current):
                    continue
                valid_currents.append(abs(current))

            if not valid_currents:
                continue

            line_current = max(valid_currents)
            max_current = max(max_current, line_current)

            if norm_amps is not None and norm_amps > 0:
                if line_current > norm_amps:
                    n_current_violations += 1

        return {
            "max_line_current_a": max_current,
            "n_current_violations": n_current_violations
        }

    def print_stage_summary(self, stage_result):
        print("\n" + "-" * 70)
        print(f"OpenDSS etapa {stage_result['stage_index']}")
        print("-" * 70)
        print(f"Archivo DSS: {stage_result['dss_file']}")
        print(f"Exito: {stage_result['success']}")
        print(f"Perdidas kWh: {stage_result['energy_losses_kwh']:.6f}")
        print(f"Vmin pu: {stage_result['min_voltage_pu']}")
        print(f"Vmax pu: {stage_result['max_voltage_pu']}")
        print(f"Violaciones tension: {stage_result['n_voltage_violations']}")
        print(f"Corriente maxima A: {stage_result['max_line_current_a']}")
        print(f"Violaciones corriente: {stage_result['n_current_violations']}")
        if stage_result["errors"]:
            print("Errores:")
            for error in stage_result["errors"]:
                print(f"  - {error}")
        print("-" * 70 + "\n")

    def _empty_stage_result(self, dss_file, stage_index):
        return {
            "stage_index": stage_index,
            "dss_file": dss_file,
            "success": True,
            "errors": [],
            "hourly_active_power_kw": [],
            "hourly_reactive_power_kvar": [],
            "hourly_losses_kw": [],
            "hourly_losses_kvar": [],
            "energy_losses_kwh": 0.0,
            "min_voltage_pu": None,
            "max_voltage_pu": None,
            "n_voltage_violations": 0,
            "max_line_current_a": None,
            "n_current_violations": 0,
            "hourly_voltage_summary": [],
            "hourly_line_current_summary": [],
        }

    def _aggregate_stage_result(self, stage_result):
        stage_result["energy_losses_kwh"] = sum(stage_result["hourly_losses_kw"])

        voltage_mins = [
            item["min_voltage_pu"]
            for item in stage_result["hourly_voltage_summary"]
            if item.get("min_voltage_pu") is not None
        ]
        voltage_maxs = [
            item["max_voltage_pu"]
            for item in stage_result["hourly_voltage_summary"]
            if item.get("max_voltage_pu") is not None
        ]
        current_maxs = [
            item["max_line_current_a"]
            for item in stage_result["hourly_line_current_summary"]
            if item.get("max_line_current_a") is not None
        ]

        stage_result["min_voltage_pu"] = min(voltage_mins) if voltage_mins else None
        stage_result["max_voltage_pu"] = max(voltage_maxs) if voltage_maxs else None
        stage_result["n_voltage_violations"] = sum(
            item.get("n_voltage_violations", 0)
            for item in stage_result["hourly_voltage_summary"]
        )
        stage_result["max_line_current_a"] = max(current_maxs) if current_maxs else None
        stage_result["n_current_violations"] = sum(
            item.get("n_current_violations", 0)
            for item in stage_result["hourly_line_current_summary"]
        )

    def _is_valid_number(self, value):
        if value is None:
            return False

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return False

        if math.isnan(numeric_value) or math.isinf(numeric_value):
            return False

        return np.isfinite(numeric_value)
