"""
PyTopologyDebugPlot: diagnostico textual y grafico de topologia.

Genera resumenes por componente y figuras por estagio para una solucion.
"""

import itertools
import os

import matplotlib.pyplot as plt
import networkx as nx


class PyTopologyDebugPlot:
    def __init__(self, config, data):
        self.config = config
        self.data = data
        self.line_ids = self._get_line_ids()

    def plot_chromosome(self, chromosome, prefix="best_solution"):
        output_folder = self.config.topology_debug_output_folder
        os.makedirs(output_folder, exist_ok=True)

        for stage_index, stage_vector in enumerate(chromosome.matrix):
            graph = self.build_graph_from_stage(stage_vector)
            component_summary = self.analyze_components(graph, stage_index)
            self.print_component_summary(component_summary, stage_index)

            output_path = os.path.join(
                output_folder,
                f"{prefix}_stage_{stage_index + 1}.png"
            )
            self.draw_stage_graph(
                graph,
                component_summary,
                stage_index,
                output_path
            )

            no_labels_path = os.path.join(
                output_folder,
                f"{prefix}_stage_{stage_index + 1}_no_labels.png"
            )
            self.draw_stage_graph(
                graph,
                component_summary,
                stage_index,
                no_labels_path,
                with_labels=False
            )

    def build_graph_from_stage(self, stage_vector):
        graph = nx.Graph()

        buses = self._get_all_buses()
        if buses:
            graph.add_nodes_from(buses)
        else:
            for line_id in self.line_ids:
                bar_1, bar_2 = self.get_line_buses(line_id)
                graph.add_node(bar_1)
                graph.add_node(bar_2)

        for line_idx, option_id in enumerate(stage_vector):
            if option_id == -1 or line_idx >= len(self.line_ids):
                continue

            line_id = self.line_ids[line_idx]
            bar_1, bar_2 = self.get_line_buses(line_id)
            graph.add_edge(
                bar_1,
                bar_2,
                line_id=line_id,
                option_id=option_id
            )

        return graph

    def get_line_buses(self, line_id):
        line_catalog = self.data.get("line_catalog", {})

        if isinstance(line_catalog, dict):
            line = line_catalog.get(line_id)
        elif isinstance(line_catalog, list):
            if isinstance(line_id, int):
                line = line_catalog[line_id]
            else:
                line = next(
                    (
                        item for item in line_catalog
                        if item.get("line_id") == line_id
                    ),
                    None
                )
        else:
            line = None

        if isinstance(line, dict):
            for key_1, key_2 in [
                ("bar_1", "bar_2"),
                ("bus_1", "bus_2"),
                ("from_bus", "to_bus"),
                ("from", "to"),
                ("Bar_1", "Bar_2")
            ]:
                if key_1 in line and key_2 in line:
                    return line[key_1], line[key_2]

        line_topology = self.data.get("line_topology", {})
        if isinstance(line_topology, dict) and line_id in line_topology:
            bus_pair = line_topology[line_id]
            return bus_pair[0], bus_pair[1]

        raise KeyError(f"No se encontraron barras para line_id={line_id}")

    def get_sources(self):
        source_buses = self.data.get("source_buses")
        if source_buses:
            return list(source_buses)

        sources = []
        for bus in self._get_all_buses():
            bus_lower = str(bus).lower()
            if "se" in bus_lower or "source" in bus_lower:
                sources.append(bus)
        return sources

    def get_load_buses(self):
        load_buses = self.data.get("load_buses")
        if load_buses:
            return list(load_buses)

        sources = set(self.get_sources())
        return [
            bus for bus in self._get_all_buses()
            if bus not in sources
        ]

    def analyze_components(self, graph, stage_index):
        sources = set(self.get_sources())
        load_buses = set(self.get_load_buses())
        component_summary = []

        for component_id, nodes in enumerate(nx.connected_components(graph), start=1):
            subgraph = graph.subgraph(nodes).copy()
            component_sources = sorted(set(nodes).intersection(sources))
            component_loads = sorted(set(nodes).intersection(load_buses))
            cycles = nx.cycle_basis(subgraph)

            component_info = {
                "component_id": component_id,
                "nodes": sorted(nodes),
                "sources": component_sources,
                "loads": component_loads,
                "n_nodes": subgraph.number_of_nodes(),
                "n_edges": subgraph.number_of_edges(),
                "is_tree": nx.is_tree(subgraph) if subgraph.number_of_nodes() > 0 else False,
                "cycles": cycles,
                "has_no_source": len(component_sources) == 0,
                "has_multiple_sources": len(component_sources) > 1,
                "source_paths": []
            }

            if component_info["has_multiple_sources"]:
                for source_1, source_2 in itertools.combinations(component_sources, 2):
                    path = nx.shortest_path(
                        subgraph,
                        source=source_1,
                        target=source_2
                    )
                    component_info["source_paths"].append({
                        "source_1": source_1,
                        "source_2": source_2,
                        "path": path,
                        "edges": self._path_edges_with_line_ids(subgraph, path)
                    })

            component_summary.append(component_info)

        return component_summary

    def print_component_summary(self, component_summary, stage_index):
        print("\n" + "=" * 60)
        print(f"TOPOLOGY DEBUG - ESTAGIO {stage_index + 1}")
        print("=" * 60)
        print(f"Numero de componentes: {len(component_summary)}")

        for component_info in component_summary:
            print(f"\nComponente {component_info['component_id']}:")
            print(f"  Nodos: {component_info['n_nodes']}")
            print(f"  Aristas: {component_info['n_edges']}")
            print(f"  Es arbol: {component_info['is_tree']}")
            print(f"  Fuentes: {component_info['sources']}")
            print(f"  Cargas: {len(component_info['loads'])}")
            print(f"  Ciclos: {len(component_info['cycles'])}")

            if component_info["has_multiple_sources"]:
                print("  PROBLEMA: multiples fuentes")
                print("  Caminos entre fuentes:")
                for source_path in component_info["source_paths"]:
                    print(
                        f"    {source_path['source_1']} -> "
                        f"{source_path['source_2']}: {source_path['path']}"
                    )
                    print(f"      Lineas: {source_path['edges']}")
            elif component_info["has_no_source"]:
                print("  PROBLEMA: componente sin fuente")
            elif component_info["cycles"]:
                print("  PROBLEMA: ciclos")
            else:
                print("  Estado: OK")

        print("=" * 60)

    def draw_stage_graph(
        self,
        graph,
        component_summary,
        stage_index,
        output_path,
        with_labels=None
    ):
        if with_labels is None:
            with_labels = self.config.topology_debug_with_labels

        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(
            graph,
            seed=self.config.topology_debug_layout_seed
        )

        sources = set(self.get_sources())
        loads = set(self.get_load_buses())
        problem_nodes = set()
        cycle_nodes = set()

        for component_info in component_summary:
            if (
                component_info["has_no_source"]
                or component_info["has_multiple_sources"]
            ):
                problem_nodes.update(component_info["nodes"])

            for cycle in component_info["cycles"]:
                cycle_nodes.update(cycle)

        normal_nodes = [
            node for node in graph.nodes()
            if node not in sources and node not in problem_nodes and node not in cycle_nodes
        ]
        load_nodes = [
            node for node in normal_nodes
            if node in loads
        ]
        neutral_nodes = [
            node for node in normal_nodes
            if node not in loads
        ]

        nx.draw_networkx_edges(
            graph,
            pos,
            edge_color="#9a9a9a",
            width=1.0,
            alpha=0.75
        )
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=neutral_nodes,
            node_color="#d8d8d8",
            node_size=90,
            linewidths=0.7,
            edgecolors="#555555"
        )
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=load_nodes,
            node_color="#8ecae6",
            node_size=110,
            linewidths=0.7,
            edgecolors="#335c67"
        )
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=list(cycle_nodes),
            node_color="#ffb703",
            node_size=150,
            linewidths=1.5,
            edgecolors="#8a5a00"
        )
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=list(problem_nodes),
            node_color="#fb8500",
            node_size=180,
            linewidths=2.0,
            edgecolors="#7f2a00"
        )
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=list(sources.intersection(graph.nodes())),
            node_color="#219ebc",
            node_size=260,
            linewidths=2.2,
            edgecolors="#023047",
            node_shape="s"
        )

        if with_labels:
            nx.draw_networkx_labels(graph, pos, font_size=7)

        plt.title(f"Topology Debug - Stage {stage_index + 1}")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

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

    def _path_edges_with_line_ids(self, graph, path):
        edges = []

        for node_1, node_2 in zip(path, path[1:]):
            edge_data = graph.get_edge_data(node_1, node_2, default={})
            edges.append({
                "from": node_1,
                "to": node_2,
                "line_id": edge_data.get("line_id"),
                "option_id": edge_data.get("option_id")
            })

        return edges
