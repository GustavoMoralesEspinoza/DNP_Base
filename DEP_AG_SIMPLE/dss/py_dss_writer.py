"""
PyDSSWriter: generador de archivos .dss por estagio.

Este modulo solo escribe archivos OpenDSS. No ejecuta OpenDSS ni calcula
perdidas electricas.
"""

import os
import re
import math


class PyDSSWriter:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.line_ids = self._get_line_ids()
        self.project_root = self._get_project_root()
        self._missing_der_warnings_reported = set()

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
            if getattr(self.config, "dss_use_loadshapes", False):
                self.write_loadshapes(file)
            self.write_lines(file, stage_vector, stage_index)
            self.write_loads(file, stage_index)
            if getattr(self.config, "use_ders", False):
                self.write_ders_redirect(file, stage_index - 1)
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

    def write_loadshapes(self, file):
        if self.config.dss_write_comments:
            file.write("! ==========================\n")
            file.write("! LoadShapes\n")
            file.write("! ==========================\n\n")

        load_curves = self.get_load_curves()

        for consumer_type in ["R", "C", "I", "I4"]:
            values = load_curves.get(consumer_type, [1.0] * 24)
            loadshape_name = self.get_loadshape_name(consumer_type)
            values_text = self.format_loadshape_values(values)
            file.write(
                f"New Loadshape.{loadshape_name} "
                f"npts=24 interval=1 mult=[{values_text}]\n"
            )

        default_name = self.sanitize_dss_name(
            getattr(self.config, "dss_default_loadshape_name", "LS_DEFAULT")
        )
        default_values = self.format_loadshape_values([1.0] * 24)
        file.write(
            f"New Loadshape.{default_name} "
            f"npts=24 interval=1 mult=[{default_values}]\n\n"
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

            consumer_type = self.get_consumer_type_for_load(load_data, stage_index)
            load_name = self._build_load_name(bus, consumer_type, load_id)
            dss_bus = self.get_bus_name_for_dss(bus)
            loadshape_name = self.get_loadshape_name(consumer_type)

            file.write(
                f"New Load.{load_name} "
                f"Bus1={dss_bus}.1.2.3 "
                f"Phases=3 "
                f"Conn={self.config.dss_load_connection} "
                f"Model={self.config.dss_load_model} "
                f"kV={self.config.dss_base_kv} "
                f"kW={p_kw} "
                f"kVAR={q_kvar} "
            )
            if getattr(self.config, "dss_use_loadshapes", False):
                file.write(f"Daily={loadshape_name}")
            file.write("\n")

        file.write("\n")

    def write_ders_redirect(self, file, stage_index):
        if not getattr(self.config, "use_ders", False):
            return

        stage_number = stage_index + 1
        ders_path = self.get_ders_file_path(stage_index)

        if ders_path is None:
            self._warn_missing_der(stage_number)
            if getattr(self.config, "ders_continue_if_missing", True):
                return
            filename = self.config.ders_file_pattern.format(stage=stage_number)
            raise FileNotFoundError(
                f"Archivo DER no encontrado para etapa {stage_number}: {filename}"
            )

        if self.config.dss_write_comments:
            file.write("! ==========================\n")
            file.write("! DERs\n")
            file.write("! ==========================\n\n")

        file.write(f'Redirect "{ders_path}"\n\n')

    def get_ders_file_path(self, stage_index):
        stage_number = stage_index + 1
        filename = self.config.ders_file_pattern.format(stage=stage_number)
        candidate_paths = []

        candidate_paths.append(os.path.join(self.config.ders_folder, filename))
        candidate_paths.append(os.path.join("Initialdata", "DERs", filename))

        input_data_folder = getattr(self.config, "input_data_folder", None)
        if input_data_folder:
            candidate_paths.append(
                os.path.join(input_data_folder, "DERs", filename)
            )

            network_folder = getattr(self.config, "network_folder", None)
            if network_folder:
                candidate_paths.append(
                    os.path.join(input_data_folder, network_folder, "DERs", filename)
                )

        data_dir = self.data.get("data_dir")
        if data_dir:
            candidate_paths.append(os.path.join(data_dir, "DERs", filename))

        for path in candidate_paths:
            absolute_path = self._absolute_project_path(path)
            if os.path.exists(absolute_path):
                return absolute_path

        return None

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

    def get_load_curves(self):
        raw_curves = self.data.get("load_curves", {})
        curves = {}

        if isinstance(raw_curves, dict):
            for raw_name, raw_values in raw_curves.items():
                consumer_type = self.get_consumer_type_for_load(
                    {"consumer_type": raw_name},
                    None
                )

                if isinstance(raw_values, dict):
                    values = [
                        raw_values[key]
                        for key in sorted(raw_values.keys())
                    ]
                else:
                    values = list(raw_values)

                curves[consumer_type] = self._prepare_loadshape_values(values)

        for consumer_type in ["R", "C", "I", "I4"]:
            if consumer_type not in curves:
                curves[consumer_type] = [1.0] * 24

        return curves

    def format_loadshape_values(self, values):
        prepared_values = self._prepare_loadshape_values(values)
        return " ".join(f"{value:.6g}" for value in prepared_values)

    def get_consumer_type_for_load(self, load_data, stage_index):
        type_map = {
            1: "R",
            2: "C",
            3: "I",
            4: "I4",
            "1": "R",
            "2": "C",
            "3": "I",
            "4": "I4",
            "R": "R",
            "C": "C",
            "I": "I",
            "I4": "I4",
        }
        keys = [
            "consumer_type",
            "consumer_label",
            "type",
            "consumer",
            "load_type",
            "consumer_class",
        ]

        for key in keys:
            value = load_data.get(key)
            if value is None:
                continue

            normalized_value = str(value).strip().upper()
            if normalized_value in type_map:
                return type_map[normalized_value]

            if value in type_map:
                return type_map[value]

        default_type = getattr(self.config, "default_consumer_type", "R")
        return type_map.get(str(default_type).strip().upper(), "R")

    def get_loadshape_name(self, consumer_type):
        valid_types = {"R", "C", "I", "I4"}
        if consumer_type in valid_types:
            return self.sanitize_dss_name(f"LS_{consumer_type}")

        default_name = getattr(self.config, "dss_default_loadshape_name", "LS_DEFAULT")
        return self.sanitize_dss_name(default_name)

    def sanitize_dss_name(self, name):
        return self._safe_name(name)

    def _get_line_ids(self):
        line_catalog = self.data.get("line_catalog", {})
        if isinstance(line_catalog, dict):
            return sorted(line_catalog.keys())
        return list(range(len(line_catalog)))

    def _get_project_root(self):
        data_dir = self.data.get("data_dir")
        if data_dir:
            return os.path.abspath(os.path.dirname(data_dir))
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _absolute_project_path(self, path):
        if os.path.isabs(path):
            return os.path.abspath(path)
        return os.path.abspath(os.path.join(self.project_root, path))

    def _warn_missing_der(self, stage_number):
        filename = self.config.ders_file_pattern.format(stage=stage_number)
        warning_key = f"stage_{stage_number}_{filename}"

        if (
            getattr(self.config, "ders_warn_once", True)
            and warning_key in self._missing_der_warnings_reported
        ):
            return

        print(
            "WARNING: Archivo DER no encontrado para etapa "
            f"{stage_number}: {filename}"
        )
        self._missing_der_warnings_reported.add(warning_key)

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

    def _prepare_loadshape_values(self, values):
        prepared = []

        for value in values:
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                numeric_value = 1.0

            if math.isnan(numeric_value) or math.isinf(numeric_value):
                numeric_value = 1.0

            prepared.append(numeric_value)

        if not prepared:
            prepared = [1.0]

        if len(prepared) < 24:
            last_value = prepared[-1]
            prepared.extend([last_value] * (24 - len(prepared)))
        elif len(prepared) > 24:
            prepared = prepared[:24]

        if getattr(self.config, "dss_normalize_loadshapes", False):
            max_value = max(abs(value) for value in prepared)
            if max_value > 0:
                prepared = [value / max_value for value in prepared]

        return prepared

    def _build_load_name(self, bus, consumer_type, load_id):
        parts = ["Load", self._safe_name(bus)]

        if consumer_type:
            parts.append(self._safe_name(consumer_type))
        elif load_id:
            parts.append(self._safe_name(load_id))

        return "_".join(parts)
