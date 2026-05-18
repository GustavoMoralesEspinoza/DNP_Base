"""
PyGAReport: reportes CSV y graficos del algoritmo genetico.

Este modulo solo registra resultados ya calculados por el AG. No modifica la
logica evolutiva, la funcion objetivo ni la evaluacion electrica.
"""

import csv
import os


class PyGAReport:
    def __init__(self, config):
        self.config = config

    def write_reports(self, ga):
        if not getattr(self.config, "use_ga_reports", False):
            return []

        os.makedirs(self.config.ga_reports_output_folder, exist_ok=True)
        written_files = []
        written_files.append(self.write_history_csv(ga))

        if getattr(self.config, "save_all_ga_evaluations", False):
            written_files.append(self.write_evaluations_csv(ga))

        return written_files

    def write_history_csv(self, ga):
        path = os.path.join(
            self.config.ga_reports_output_folder,
            "ga_history.csv"
        )

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "iteration",
                    "best_fitness",
                    "mean_fitness",
                    "global_best_fitness",
                    "feasible_count",
                    "population_size",
                ]
            )
            writer.writeheader()

            for index, best_fitness in enumerate(ga.history_best):
                writer.writerow({
                    "iteration": index + 1,
                    "best_fitness": best_fitness,
                    "mean_fitness": ga.history_mean[index],
                    "global_best_fitness": ga.history_global[index],
                    "feasible_count": ga.history_feasible[index],
                    "population_size": ga.history_population_size[index],
                })

        return path

    def write_evaluations_csv(self, ga):
        path = os.path.join(
            self.config.ga_reports_output_folder,
            "ga_evaluations.csv"
        )

        fieldnames = [
            "iteration",
            "individual",
            "fitness",
            "c_inv",
            "c_ele",
            "penalty",
            "is_feasible",
            "c_inv_pu",
            "c_ele_pu",
            "weighted_investment",
            "weighted_electrical_losses",
            "topology_valid",
            "repair_success",
            "total_repair_changes",
            "daily_losses_kwh_total",
            "chromosome_key",
        ]

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for record in ga.evaluation_records:
                result = record["result"]
                objective_result = getattr(result, "objective_result", {}) or {}
                topology_result = getattr(result, "topology_result", None)
                repair_result = getattr(result, "repair_result", None)
                dss_results = getattr(result, "dss_results", None)

                writer.writerow({
                    "iteration": record["iteration"],
                    "individual": record["individual"],
                    "fitness": result.fitness,
                    "c_inv": result.c_inv,
                    "c_ele": result.c_ele,
                    "penalty": result.penalty,
                    "is_feasible": result.is_feasible,
                    "c_inv_pu": objective_result.get("c_inv_pu"),
                    "c_ele_pu": objective_result.get("c_ele_pu"),
                    "weighted_investment": objective_result.get(
                        "weighted_investment"
                    ),
                    "weighted_electrical_losses": objective_result.get(
                        "weighted_electrical_losses"
                    ),
                    "topology_valid": (
                        topology_result.get("is_valid")
                        if topology_result is not None else None
                    ),
                    "repair_success": (
                        repair_result.get("success")
                        if repair_result is not None else None
                    ),
                    "total_repair_changes": (
                        repair_result.get("total_changes")
                        if repair_result is not None else None
                    ),
                    "daily_losses_kwh_total": (
                        dss_results.total_energy_losses_kwh
                        if dss_results is not None else None
                    ),
                    "chromosome_key": result.chromosome.to_key(),
                })

        return path

    def write_plots(self, ga):
        if not getattr(self.config, "use_ga_plots", False):
            return []

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("WARNING: matplotlib no disponible. Graficos AG omitidos.")
            return []

        os.makedirs(self.config.ga_plots_output_folder, exist_ok=True)
        written_files = []
        written_files.append(self.plot_fitness_evolution(ga, plt))
        written_files.append(self.plot_feasible_count(ga, plt))

        if ga.evaluation_records:
            written_files.append(self.plot_cost_scatter(ga, plt))

        return written_files

    def plot_fitness_evolution(self, ga, plt):
        path = os.path.join(
            self.config.ga_plots_output_folder,
            "ga_fitness_evolution.png"
        )
        iterations = list(range(1, len(ga.history_best) + 1))

        plt.figure(figsize=(8, 4.5))
        plt.plot(iterations, ga.history_best, marker="o", label="Best iteration")
        plt.plot(iterations, ga.history_mean, marker="s", label="Mean")
        plt.plot(iterations, ga.history_global, marker="^", label="Global best")
        plt.xlabel("Iteration")
        plt.ylabel("Fitness")
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.legend()

        if getattr(self.config, "use_log_scale_for_fitness_plots", False):
            positive_values = [
                value for value in (
                    ga.history_best + ga.history_mean + ga.history_global
                )
                if value > 0
            ]
            if positive_values:
                plt.yscale("log")
                plt.ylim(
                    bottom=max(
                        min(positive_values),
                        self.config.plot_min_positive_value
                    )
                )

        plt.tight_layout()
        plt.savefig(path, dpi=self.config.plot_dpi)
        plt.close()
        return path

    def plot_feasible_count(self, ga, plt):
        path = os.path.join(
            self.config.ga_plots_output_folder,
            "ga_feasible_count.png"
        )
        iterations = list(range(1, len(ga.history_feasible) + 1))

        plt.figure(figsize=(8, 4.5))
        plt.bar(iterations, ga.history_feasible)
        plt.xlabel("Iteration")
        plt.ylabel("Feasible individuals")
        plt.ylim(0, max(ga.history_population_size or [1]))
        plt.grid(True, axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(path, dpi=self.config.plot_dpi)
        plt.close()
        return path

    def plot_cost_scatter(self, ga, plt):
        path = os.path.join(
            self.config.ga_plots_output_folder,
            "ga_cost_comparison.png"
        )
        c_inv = [record["result"].c_inv for record in ga.evaluation_records]
        c_ele = [record["result"].c_ele for record in ga.evaluation_records]
        fitness = [record["result"].fitness for record in ga.evaluation_records]

        plt.figure(figsize=(6, 5))
        scatter = plt.scatter(c_inv, c_ele, c=fitness, cmap="viridis", s=28)
        plt.xlabel("Cinv VP")
        plt.ylabel("Cele VP")
        plt.grid(True, linestyle="--", alpha=0.35)
        plt.colorbar(scatter, label="Fitness")

        if ga.best_result is not None:
            plt.scatter(
                [ga.best_result.c_inv],
                [ga.best_result.c_ele],
                marker="*",
                s=180,
                color="red",
                edgecolors="black",
                label="Best"
            )
            plt.legend()

        plt.tight_layout()
        plt.savefig(path, dpi=self.config.plot_dpi)
        plt.close()
        return path
