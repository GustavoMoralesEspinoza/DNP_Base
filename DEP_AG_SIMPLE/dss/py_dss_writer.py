"""
PyDSSWriter: generador de archivos .dss por estagio.

Este modulo solo escribe archivos OpenDSS. No ejecuta OpenDSS ni calcula
perdidas electricas.
"""

import os
import re


class PyDSSWriter:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.line_ids = self._get_line_ids()

    def write_chromosome(self, chromosome, prefix=None):
        os.makedirs(self.config.dss_output_folder, exist_ok=True)

        dss_files = []
        for stage_index, stage_vector in enumerate(chromosome.matrix, start=1):
            dss_files.append(self.write_stage(stage_vector, stage_index, prefix))

        return dss_files

    def write_stage(self, stage_vector, stage_index, prefix=None):
        file_path = self.build_stage_file_path(stage_index, prefix)

        with open(file_path, "w", encoding="utf-8") as file:
            self.write_header(file, stage_index)
            self.write_lines(file, stage_vector, stage_index)
            self.write_loads(file, stage_index)
            self.write_footer(file)

        return file_path

    def build_stage_file_path(self, stage_index, prefix=None):
        filename_prefix = prefix if prefix is not None else self.config.dss_base_filename
        filename = f"{filename_prefix}_stage_{stage_index}.dss"
        return os.path.join(self.config.dss_output_folder, filename)

    def write_header(self, file, stage_index):
        circuit_name = f"{self.config.dss_base_filename}_{stage_index}"

        file.write("Clear\n\n")
        file.write(f"New Circuit.{circuit_name}\n")
        file.write(
            f"~ basekv={self.config.dss_base_kv} "
            f"pu={self.config.dss_pu_source} "
            f"angle={self.config.dss_angle}\n\n"
        )

    def write_lines(self, file, stage_vector, stage_index):
        if self.config.dss_write_comments:
            file.write("! ==========================\n")
            file.write("! Lines\n")
            file.write("! ==========================\n\n")

        for line_idx, option_id in enumerate(stage_vector):
            if option_id == -1:
                continue

            if line_idx >= len(self.line_ids):
                print(f"WARNING: Índice de línea {line_idx} fuera de rango. Línea omitida.")
                continue

            line_id = self.line_ids[line_idx]
            line_data = self.get_line_data(line_id)
            option_data = self.get_line_option_data(line_id, option_id)

            if line_data is None or option_data is None:
                continue

            try:
                bar_1, bar_2 = self._get_line_buses(line_data)
                bus_1 = self.get_bus_name_for_dss(bar_1)
                bus_2 = self.get_bus_name_for_dss(bar_2)
                length = self._get_value(option_data, ["length_km", "length"], 1.0)
                r1 = self._get_value(option_data, ["r1_ohm_km", "r1"], 0.0)
                x1 = self._get_value(option_data, ["x1_ohm_km", "x1"], 0.0)
                normamps = self._get_value(option_data, ["imax_A", "normamps"], 150.0)
            except KeyError as exc:
                print(f"WARNING: {exc}. Línea {line_id} omitida.")
                continue

            safe_line_name = self._safe_name(line_id)
            file.write(
                f"New Line.{safe_line_name} "
                f"Phases=3 "
                f"Bus1={bus_1}.1.2.3 "
                f"Bus2={bus_2}.1.2.3 "
                f"length={length} "
                f"r1={r1} x1={x1} "
                f"r0={r1} x0={x1} "
                f"c1=0 c0=0 "
                f"units=km "
                f"normamps={normamps}\n"
            )

        file.write("\n")

    def write_loads(self, file, stage_index):
        if self.config.dss_write_comments:
            file.write("! ==========================\n")
            file.write("! Loads\n")
            file.write("! ==========================\n\n")

        loads = self.get_loads_for_stage(stage_index)

        for load_id, load_data in loads.items():
            bus = load_data.get("bus")
            p_kw = self._get_value(load_data, ["P_kW", "p_kw", "kW"], 0.0)
            q_kvar = self._get_value(load_data, ["Q_kVAr", "q_kvar", "kVAR"], 0.0)

            if bus is None:
                print(f"WARNING: Carga {load_id} sin bus. Carga omitida.")
                continue

            if p_kw <= 0:
                continue

            consumer_type = (
                load_data.get("consumer_type")
                or load_data.get("consumer_label")
                or load_data.get("consumer_class")
                or ""
            )
            load_name = self._build_load_name(bus, consumer_type, load_id)
            dss_bus = self.get_bus_name_for_dss(bus)

            file.write(
                f"New Load.{load_name} "
                f"Bus1={dss_bus}.1.2.3 "
                f"Phases=3 "
                f"Conn={self.config.dss_load_connection} "
                f"Model={self.config.dss_load_model} "
                f"kV={self.config.dss_base_kv} "
                f"kW={p_kw} "
                f"kVAR={q_kvar}\n"
            )

        file.write("\n")

    def write_footer(self, file):
        file.write(f"Set VoltageBases=[{self.config.dss_base_kv}]\n")
        file.write("CalcVoltageBases\n")
        file.write("Solve\n")

    def get_line_data(self, line_id):
        line_catalog = self.data.get("line_catalog", {})

        if isinstance(line_catalog, dict):
            line_data = line_catalog.get(line_id)
        elif isinstance(line_catalog, list):
            line_data = line_catalog[line_id] if isinstance(line_id, int) else None
        else:
            line_data = None

        if line_data is None:
            print(f"WARNING: No se encontró línea {line_id}. Línea omitida.")

        return line_data

    def get_line_option_data(self, line_id, option_id):
        line_data = self.get_line_data(line_id)
        if line_data is None:
            return None

        options_detail = line_data.get("options_detail", {})
        option_data = options_detail.get(option_id)

        if option_data is None:
            print(
                f"WARNING: No se encontró opción {option_id} "
                f"para línea {line_id}. Línea omitida."
            )

        return option_data

    def get_bus_name_for_dss(self, bus_name):
        if self.config.dss_collapse_sources and self._is_source_bus(bus_name):
            return self.config.dss_equivalent_source_name

        return self._safe_name(bus_name)

    def get_loads_for_stage(self, stage_index):
        loads_by_stage = self.data.get("loads_by_stage", {})
        return loads_by_stage.get(stage_index, {})

    def _get_line_ids(self):
        line_catalog = self.data.get("line_catalog", {})
        if isinstance(line_catalog, dict):
            return sorted(line_catalog.keys())
        return list(range(len(line_catalog)))

    def _get_line_buses(self, line_data):
        for key_1, key_2 in [
            ("bar_1", "bar_2"),
            ("bus_1", "bus_2"),
            ("from_bus", "to_bus"),
            ("from", "to"),
            ("Bar_1", "Bar_2")
        ]:
            if key_1 in line_data and key_2 in line_data:
                return line_data[key_1], line_data[key_2]

        raise KeyError("No se encontraron barras bar_1/bar_2 o equivalentes")

    def _get_value(self, data_dict, keys, default_value):
        for key in keys:
            if key in data_dict:
                return data_dict[key]
        return default_value

    def _is_source_bus(self, bus_name):
        if bus_name in self.data.get("source_buses", []):
            return True

        bus_lower = str(bus_name).lower()
        return "se" in bus_lower or "source" in bus_lower

    def _safe_name(self, value):
        safe_value = re.sub(r"[^A-Za-z0-9_]", "_", str(value))
        if not safe_value:
            return "unnamed"
        return safe_value

    def _build_load_name(self, bus, consumer_type, load_id):
        parts = ["Load", self._safe_name(bus)]

        if consumer_type:
            parts.append(self._safe_name(consumer_type))
        elif load_id:
            parts.append(self._safe_name(load_id))

        return "_".join(parts)
