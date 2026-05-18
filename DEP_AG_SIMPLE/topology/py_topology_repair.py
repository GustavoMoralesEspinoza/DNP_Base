"""
PyTopologyRepair: reparacion topologica simple para cromosomas DEP.

La reparacion es opcional y no llama OpenDSS. Trabaja por estagio sobre una
copia del cromosoma, intentando reconectar componentes, romper ciclos y separar
fuentes multiples cuando aplica.
"""

import itertools
import random

import networkx as nx

from core.py_chromosome import PyChromosome


class PyTopologyRepair:
    def __init__(self, config, data, topology_validator=None):
        self.config = config
        self.data = data
        self.topology_validator = topology_validator
        self.random = random.Random(config.repair_random_seed)
        self.line_ids = self._get_line_ids()
        self.line_id_to_idx = {
            line_id: idx for idx, line_id in enumerate(self.line_ids)
        }

    def repair(self, chromosome):
        repaired_matrix = [row[:] for row in chromosome.matrix]
        stage_results = []
        warnings = []
        total_changes = 0

        for stage_index, stage_vector in enumerate(repaired_matrix, start=1):
            repaired_stage, stage_result = self.repair_stage(
                stage_vector,
                stage_index
            )
            repaired_matrix[stage_index - 1] = repaired_stage
            stage_results.append(stage_result)
            warnings.extend(stage_result["warnings"])
            total_changes += stage_result["changes"]

        success = all(stage_result["final_is_valid"] for stage_result in stage_results)
        repair_result = {
            "was_repaired": total_changes > 0,
            "success": success,
            "total_changes": total_changes,
            "stage_results": stage_results,
            "warnings": warnings
        }

        return PyChromosome(repaired_matrix), repair_result

    def repair_stage(self, stage_vector, stage_index):
        working_stage = stage_vector[:]
        initial_graph = self.build_graph(working_stage)
        initial_result = self._validate_stage(working_stage, stage_index)
        actions = []
        warnings = []

        for _ in range(self.config.repair_max_iterations):
            graph = self.build_graph(working_stage)
            stage_result = self._validate_stage(working_stage, stage_index)

            if stage_result["penalty"] == 0:
                break

            changed = False

            if (
                self.config.use_multiple_sources_repair
                and stage_result["components_with_multiple_sources"]
            ):
                action = self.separate_multiple_sources(
                    working_stage,
                    graph,
                    stage_index
                )
                if action is not None:
                    actions.append(action)
                    changed = True
                    continue

            if self.config.use_cycle_repair and stage_result["has_cycles"]:
                action = self.remove_cycles(working_stage, graph, stage_index)
                if action is not None:
                    actions.append(action)
                    if action["type"] == "warning":
                        warnings.append(f"Etapa {stage_index}: {action['reason']}")
                        break
                    changed = True
                    continue

            if (
                self.config.use_reconnection_repair
                and (
                    stage_result["components_without_source"]
                    or stage_result["has_isolated_loads"]
                )
            ):
                action = self.reconnect_components(
                    working_stage,
                    graph,
                    stage_index
                )
                if action is not None:
                    actions.append(action)
                    changed = True
                    continue

            if not changed:
                warning = {
                    "type": "warning",
                    "line_id": None,
                    "bar_1": None,
                    "bar_2": None,
                    "previous_option": None,
                    "new_option": None,
                    "reason": "repair stopped because no valid change was found"
                }
                actions.append(warning)
                warnings.append(
                    f"Etapa {stage_index}: reparación detenida sin cambios posibles"
                )
                break

        final_result = self._validate_stage(working_stage, stage_index)

        stage_repair_result = {
            "stage_index": stage_index,
            "initial_penalty": initial_result["penalty"],
            "final_penalty": final_result["penalty"],
            "initial_is_valid": initial_result["penalty"] == 0,
            "final_is_valid": final_result["penalty"] == 0,
            "changes": len([a for a in actions if a["type"] != "warning"]),
            "actions": actions,
            "warnings": warnings
        }

        return working_stage, stage_repair_result

    def reconnect_components(self, stage_vector, graph, stage_index):
        components = list(nx.connected_components(graph))
        sources = set(self.get_sources())
        node_to_component = {}
        source_component_ids = set()
        no_source_component_ids = set()

        for component_id, component_nodes in enumerate(components):
            for node in component_nodes:
                node_to_component[node] = component_id

            if set(component_nodes).intersection(sources):
                source_component_ids.add(component_id)
            else:
                no_source_component_ids.add(component_id)

        candidates = []
        fallback_candidates = []

        for line_idx, option_id in enumerate(stage_vector):
            if option_id != -1:
                continue

            line_id = self.line_ids[line_idx]
            new_option = self.choose_activation_option(line_id)
            if new_option is None:
                continue

            bar_1, bar_2 = self.get_line_buses(line_id)
            nbar_1 = self.normalize_bus_name(bar_1)
            nbar_2 = self.normalize_bus_name(bar_2)
            comp_1 = node_to_component.get(nbar_1)
            comp_2 = node_to_component.get(nbar_2)

            if comp_1 is None or comp_2 is None or comp_1 == comp_2:
                continue

            connects_no_source = (
                comp_1 in no_source_component_ids
                or comp_2 in no_source_component_ids
            )
            connects_source = (
                comp_1 in source_component_ids
                or comp_2 in source_component_ids
            )

            candidate = {
                "line_idx": line_idx,
                "line_id": line_id,
                "bar_1": bar_1,
                "bar_2": bar_2,
                "new_option": new_option,
                "cost": self._get_option_cost(line_id, new_option)
            }

            if connects_no_source and connects_source:
                candidates.append(candidate)
            elif connects_no_source:
                fallback_candidates.append(candidate)

        selected = self._select_candidate(candidates or fallback_candidates)
        if selected is None:
            return None

        previous_option = stage_vector[selected["line_idx"]]
        stage_vector[selected["line_idx"]] = selected["new_option"]

        return {
            "type": "reconnect",
            "line_id": selected["line_id"],
            "bar_1": selected["bar_1"],
            "bar_2": selected["bar_2"],
            "previous_option": previous_option,
            "new_option": selected["new_option"],
            "reason": "connect component without source to component with source"
        }

    def remove_cycles(self, stage_vector, graph, stage_index):
        cycles = nx.cycle_basis(graph)
        if not cycles:
            return None

        if self.config.repair_strategy == "random":
            cycle = self.random.choice(cycles)
        else:
            cycle = cycles[0]
        removable_edges = []

        for bus_1, bus_2 in zip(cycle, cycle[1:] + cycle[:1]):
            edge_data = graph.get_edge_data(bus_1, bus_2, default={})
            line_id = edge_data.get("line_id")
            if line_id is None or not self.can_remove_line(line_id):
                continue

            line_idx = self.line_id_to_idx[line_id]
            option_id = stage_vector[line_idx]
            removable_edges.append({
                "line_idx": line_idx,
                "line_id": line_id,
                "bar_1": bus_1,
                "bar_2": bus_2,
                "previous_option": option_id,
                "cost": self._get_option_cost(line_id, option_id)
            })

        selected = self._select_removal_candidate(removable_edges)
        if selected is None:
            return {
                "type": "warning",
                "line_id": None,
                "bar_1": None,
                "bar_2": None,
                "previous_option": None,
                "new_option": None,
                "reason": "cycle repair found no removable line in selected cycle"
            }

        stage_vector[selected["line_idx"]] = -1
        reason = "random cycle repair"
        if self.config.repair_strategy != "random":
            reason = "remove edge to break cycle"

        return {
            "type": "remove_cycle_edge",
            "line_id": selected["line_id"],
            "bar_1": selected["bar_1"],
            "bar_2": selected["bar_2"],
            "previous_option": selected["previous_option"],
            "new_option": -1,
            "reason": reason
        }

    def separate_multiple_sources(self, stage_vector, graph, stage_index):
        if self.config.collapse_sources:
            return None

        if self.config.allow_multiple_sources_per_component:
            return None

        sources = set(self.get_sources())

        for component_nodes in nx.connected_components(graph):
            component_sources = sorted(set(component_nodes).intersection(sources))
            if len(component_sources) <= 1:
                continue

            subgraph = graph.subgraph(component_nodes).copy()
            for source_1, source_2 in itertools.combinations(component_sources, 2):
                path = nx.shortest_path(subgraph, source=source_1, target=source_2)
                removable_edges = []

                for bus_1, bus_2 in zip(path, path[1:]):
                    edge_data = subgraph.get_edge_data(bus_1, bus_2, default={})
                    line_id = edge_data.get("line_id")
                    if line_id is None or not self.can_remove_line(line_id):
                        continue

                    line_idx = self.line_id_to_idx[line_id]
                    option_id = stage_vector[line_idx]
                    removable_edges.append({
                        "line_idx": line_idx,
                        "line_id": line_id,
                        "bar_1": bus_1,
                        "bar_2": bus_2,
                        "previous_option": option_id,
                        "cost": self._get_option_cost(line_id, option_id)
                    })

                selected = self._select_removal_candidate(removable_edges)
                if selected is None:
                    continue

                stage_vector[selected["line_idx"]] = -1
                return {
                    "type": "separate_sources",
                    "line_id": selected["line_id"],
                    "bar_1": selected["bar_1"],
                    "bar_2": selected["bar_2"],
                    "previous_option": selected["previous_option"],
                    "new_option": -1,
                    "reason": (
                        "separate multiple sources in same component: "
                        f"{source_1} and {source_2}"
                    )
                }

        return None

    def build_graph(self, stage_vector):
        graph = nx.Graph()

        for bus in self._get_all_buses():
            graph.add_node(self.normalize_bus_name(bus))

        for line_idx, option_id in enumerate(stage_vector):
            if option_id == -1 or line_idx >= len(self.line_ids):
                continue

            line_id = self.line_ids[line_idx]
            bar_1, bar_2 = self.get_line_buses(line_id)
            bar_1 = self.normalize_bus_name(bar_1)
            bar_2 = self.normalize_bus_name(bar_2)
            graph.add_edge(bar_1, bar_2, line_id=line_id, option_id=option_id)

        return graph

    def get_line_buses(self, line_id):
        line_catalog = self.data.get("line_catalog", {})

        if isinstance(line_catalog, dict):
            line = line_catalog.get(line_id, {})
        elif isinstance(line_catalog, list):
            line = line_catalog[line_id] if isinstance(line_id, int) else {}
        else:
            line = {}

        if isinstance(line, dict):
            for bus_1_key, bus_2_key in [
                ("bar_1", "bar_2"),
                ("bus_1", "bus_2"),
                ("from_bus", "to_bus"),
                ("from", "to"),
                ("Bar_1", "Bar_2")
            ]:
                if bus_1_key in line and bus_2_key in line:
                    return line[bus_1_key], line[bus_2_key]

        line_topology = self.data.get("line_topology", {})
        if isinstance(line_topology, dict) and line_id in line_topology:
            bus_pair = line_topology[line_id]
            return bus_pair[0], bus_pair[1]

        raise KeyError(f"No se encontraron barras para line_id={line_id}")

    def get_sources(self):
        if self.config.collapse_sources:
            return [self.config.equivalent_source_name]

        source_buses = self.data.get("source_buses")
        if source_buses:
            return list(source_buses)

        return [
            bus for bus in self._get_all_buses()
            if self.is_source_bus(bus)
        ]

    def is_source_bus(self, bus_name):
        if bus_name in self.data.get("source_buses", []):
            return True

        bus_name_lower = str(bus_name).lower()
        return "se" in bus_name_lower or "source" in bus_name_lower

    def normalize_bus_name(self, bus_name):
        if self.config.collapse_sources and self.is_source_bus(bus_name):
            return self.config.equivalent_source_name
        return bus_name

    def get_valid_options_for_line(self, line_id):
        return list(self.data.get("valid_options_by_line", {}).get(line_id, []))

    def choose_activation_option(self, line_id):
        valid_options = [
            option for option in self.get_valid_options_for_line(line_id)
            if option != -1
        ]

        if not valid_options:
            return None

        if self.config.repair_strategy == "random":
            return self.random.choice(valid_options)

        def option_sort_key(option):
            cost = self._get_option_cost(line_id, option)
            if cost is None:
                return (float("inf"), option)
            return (cost, option)

        return min(valid_options, key=option_sort_key)

    def can_remove_line(self, line_id):
        if self.config.repair_allow_remove_non_candidate:
            return True

        if not self.config.repair_only_removable_lines:
            return True

        return -1 in self.get_valid_options_for_line(line_id)

    def find_line_id_between_buses(self, bus_1, bus_2):
        normalized_1 = self.normalize_bus_name(bus_1)
        normalized_2 = self.normalize_bus_name(bus_2)

        for line_id in self.line_ids:
            line_bus_1, line_bus_2 = self.get_line_buses(line_id)
            line_bus_1 = self.normalize_bus_name(line_bus_1)
            line_bus_2 = self.normalize_bus_name(line_bus_2)

            if {line_bus_1, line_bus_2} == {normalized_1, normalized_2}:
                return line_id

        return None

    def print_repair_summary(self, repair_result):
        print("\n" + "=" * 70)
        print("Resumen de reparacion:")
        print("=" * 70)
        print(f"Fue reparado: {repair_result['was_repaired']}")
        print(f"Exito: {repair_result['success']}")
        print(f"Cambios totales: {repair_result['total_changes']}")

        for stage_result in repair_result["stage_results"]:
            print(f"\nEstagio {stage_result['stage_index']}:")
            print(f"  Penalidad inicial: {stage_result['initial_penalty']:.2f}")
            print(f"  Penalidad final: {stage_result['final_penalty']:.2f}")
            print(f"  Valido inicial: {stage_result['initial_is_valid']}")
            print(f"  Valido final: {stage_result['final_is_valid']}")
            print(f"  Cambios: {stage_result['changes']}")

            for action in stage_result["actions"]:
                if action["type"] == "warning":
                    print(f"  Warning: {action['reason']}")
                else:
                    print(
                        "  Accion: "
                        f"{action['type']} linea {action['line_id']} "
                        f"{action['bar_1']}-{action['bar_2']} "
                        f"opcion {action['previous_option']} -> {action['new_option']}"
                    )

        print("=" * 70 + "\n")

    def _validate_stage(self, stage_vector, stage_index):
        if self.topology_validator is not None:
            return self.topology_validator.validate_stage(stage_vector, stage_index)

        graph = self.build_graph(stage_vector)
        cycles = nx.cycle_basis(graph)
        return {
            "penalty": len(cycles) * self.config.penalty_cycle,
            "has_cycles": len(cycles) > 0,
            "components_without_source": [],
            "components_with_multiple_sources": [],
            "has_isolated_loads": False
        }

    def _get_line_ids(self):
        line_catalog = self.data.get("line_catalog", {})
        if isinstance(line_catalog, dict):
            return sorted(line_catalog.keys())
        return list(range(len(line_catalog)))

    def _get_all_buses(self):
        buses = self.data.get("buses", {})
        if isinstance(buses, dict):
            return list(buses.keys())
        if isinstance(buses, list):
            return buses
        return []

    def _get_option_cost(self, line_id, option_id):
        if option_id == -1:
            return 0.0

        try:
            return self.data["line_catalog"][line_id]["options_detail"][option_id]["cost"]
        except KeyError:
            return None

    def _select_candidate(self, candidates):
        if not candidates:
            return None

        if self.config.repair_strategy == "random":
            return self.random.choice(candidates)

        return min(
            candidates,
            key=lambda candidate: (
                candidate["cost"] if candidate["cost"] is not None else float("inf"),
                str(candidate["line_id"])
            )
        )

    def _select_removal_candidate(self, candidates):
        if not candidates:
            return None

        if self.config.repair_strategy == "random":
            return self.random.choice(candidates)

        return max(
            candidates,
            key=lambda candidate: (
                candidate["cost"] if candidate["cost"] is not None else -1.0,
                str(candidate["line_id"])
            )
        )
