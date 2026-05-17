"""
PyTopologyValidator: validacion topologica con NetworkX.

FASE 7 valida radialidad, fuentes por componente y cargas aisladas.
No repara cromosomas ni llama OpenDSS.
"""

import networkx as nx


class PyTopologyValidator:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.line_ids = self._get_line_ids()

    def validate(self, chromosome):
        stage_results = []
        warnings = []
        total_penalty = 0.0

        for stage_index, stage_vector in enumerate(chromosome.matrix, start=1):
            stage_result = self.validate_stage(stage_vector, stage_index)
            stage_results.append(stage_result)
            warnings.extend(stage_result["warnings"])
            total_penalty += stage_result["penalty"]

        is_valid = all(stage_result["penalty"] == 0 for stage_result in stage_results)

        return {
            "is_valid": is_valid,
            "total_penalty": total_penalty,
            "stage_results": stage_results,
            "warnings": warnings
        }

    def validate_stage(self, stage_vector, stage_index):
        graph = self.build_graph(stage_vector)
        cycles = nx.cycle_basis(graph)
        nodes_in_cycles = sorted({node for cycle in cycles for node in cycle})
        sources = set(self._get_source_buses())
        load_buses = self._get_load_buses(sources)

        isolated_loads = []
        components_without_source = []
        components_with_multiple_sources = []
        warnings = []

        for component in nx.connected_components(graph):
            component_set = set(component)
            component_sources = sorted(component_set.intersection(sources))
            component_loads = sorted(component_set.intersection(load_buses))

            if len(component_sources) == 0:
                components_without_source.append(sorted(component_set))
                isolated_loads.extend(component_loads)
            elif len(component_sources) > 1:
                components_with_multiple_sources.append({
                    "sources": component_sources,
                    "nodes": sorted(component_set)
                })

        graph_nodes = set(graph.nodes())
        for load_bus in load_buses:
            if load_bus not in graph_nodes:
                isolated_loads.append(load_bus)

        isolated_loads = sorted(set(isolated_loads))

        if cycles:
            warnings.append(f"Etapa {stage_index}: {len(cycles)} ciclo(s) detectado(s)")
        if isolated_loads:
            warnings.append(f"Etapa {stage_index}: {len(isolated_loads)} carga(s) aislada(s)")
        if components_without_source:
            warnings.append(
                f"Etapa {stage_index}: {len(components_without_source)} componente(s) sin fuente"
            )
        if components_with_multiple_sources:
            warnings.append(
                f"Etapa {stage_index}: {len(components_with_multiple_sources)} componente(s) con multiples fuentes"
            )

        stage_result = {
            "stage_index": stage_index,
            "is_radial": len(cycles) == 0,
            "has_cycles": len(cycles) > 0,
            "n_cycles": len(cycles),
            "nodes_in_cycles": nodes_in_cycles,
            "has_isolated_loads": len(isolated_loads) > 0,
            "isolated_loads": isolated_loads,
            "components_without_source": components_without_source,
            "components_with_multiple_sources": components_with_multiple_sources,
            "n_components": nx.number_connected_components(graph),
            "n_edges": graph.number_of_edges(),
            "n_nodes": graph.number_of_nodes(),
            "penalty": 0.0,
            "warnings": warnings
        }
        stage_result["penalty"] = self.calculate_stage_penalty(stage_result)

        return stage_result

    def build_graph(self, stage_vector):
        graph = nx.Graph()

        for bus in self._get_all_buses():
            graph.add_node(bus)

        for line_idx, option_id in enumerate(stage_vector):
            if option_id == -1 or line_idx >= len(self.line_ids):
                continue

            line_id = self.line_ids[line_idx]
            bus_1, bus_2 = self.get_line_buses(line_id)
            if bus_1 is not None and bus_2 is not None:
                graph.add_edge(bus_1, bus_2, line_id=line_id, option_id=option_id)

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
                ("from", "to")
            ]:
                if bus_1_key in line and bus_2_key in line:
                    return line[bus_1_key], line[bus_2_key]

        line_topology = self.data.get("line_topology", {})
        if isinstance(line_topology, dict) and line_id in line_topology:
            bus_pair = line_topology[line_id]
            return bus_pair[0], bus_pair[1]

        return None, None

    def calculate_stage_penalty(self, stage_result):
        penalty = 0.0
        penalty += self.config.penalty_cycle * stage_result["n_cycles"]
        penalty += self.config.penalty_isolated_bus * len(stage_result["isolated_loads"])
        penalty += (
            self.config.penalty_component_without_source
            * len(stage_result["components_without_source"])
        )
        penalty += (
            self.config.penalty_multiple_sources
            * len(stage_result["components_with_multiple_sources"])
        )
        return penalty

    def print_topology_summary(self, topology_result):
        print("\n" + "=" * 70)
        print("Resumen topologico:")
        print("=" * 70)
        print(f"Topologia valida: {topology_result['is_valid']}")
        print(f"Penalidad total: {topology_result['total_penalty']:.2f}")

        for stage_result in topology_result["stage_results"]:
            print(f"\nEstagio {stage_result['stage_index']}:")
            print(f"  Radial: {stage_result['is_radial']}")
            print(f"  Ciclos: {stage_result['n_cycles']}")
            print(f"  Cargas aisladas: {len(stage_result['isolated_loads'])}")
            print(
                "  Componentes sin fuente: "
                f"{len(stage_result['components_without_source'])}"
            )
            print(
                "  Componentes con multiples fuentes: "
                f"{len(stage_result['components_with_multiple_sources'])}"
            )
            print(f"  Componentes: {stage_result['n_components']}")
            print(f"  Nodos: {stage_result['n_nodes']}")
            print(f"  Aristas: {stage_result['n_edges']}")
            print(f"  Penalidad: {stage_result['penalty']:.2f}")

        print("=" * 70 + "\n")

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

    def _get_source_buses(self):
        source_buses = self.data.get("source_buses")
        if source_buses:
            return list(source_buses)

        detected_sources = []
        for bus in self._get_all_buses():
            bus_lower = str(bus).lower()
            if "se" in bus_lower or "source" in bus_lower:
                detected_sources.append(bus)
        return detected_sources

    def _get_load_buses(self, sources):
        load_buses = self.data.get("load_buses")
        if load_buses:
            return list(load_buses)

        return [
            bus for bus in self._get_all_buses()
            if bus not in sources
        ]
