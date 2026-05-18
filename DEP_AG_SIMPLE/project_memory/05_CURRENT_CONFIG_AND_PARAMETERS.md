# Current Config And Parameters

Valores actuales observados en `config/py_config_base.py`.

## AG

- `n_individuals = 20`
- `n_iterations = 30`
- `crossover_rate = 0.8`
- `mutation_rate = 0.05`
- `elitism_rate = 0.2`
- `random_seed = 10`

## Planeamiento y economia

- `n_stages = 3`
- `stage_years = [1, 1, 2]`
- `interest_rate = 0.10`
- `energy_price = 0.1`
- `removal_factor = 0.30`

## Objetivo

- `w_inv = 0.7`
- `w_ele = 0.3`
- `c_inv_max` se actualiza en `main.py` con `calculate_max_investment_reference()`.
- `c_ele_max = 1.0`, aun sin uso real porque no hay perdidas OpenDSS.

## Topologia y fuentes

- `use_topology_validation = True`
- `collapse_sources = True`
- `equivalent_source_name = "SE_1"`
- `allow_multiple_sources_per_component = False`

## Reparacion

- `use_topology_repair = True`
- `use_reconnection_repair = True`
- `use_cycle_repair = True`
- `use_multiple_sources_repair = True`
- `repair_max_iterations = 20`
- `repair_strategy = "random"`
- `repair_random_seed = 42`
- `repair_verbose = True`
- `repair_only_removable_lines = True`
- `repair_allow_remove_non_candidate = True`

Nota: `repair_allow_remove_non_candidate=True` es un modo agresivo de debug. Revisar antes de estudios formales.

## Penalidades

- `penalty_invalid_option = 1e8`
- `penalty_component_without_source = 1e8`
- `penalty_disconnected_load = 8e7`
- `penalty_isolated_bus = 7e7`
- `penalty_cycle = 5e7`
- `penalty_nodes_in_cycles = 1e7`
- `penalty_multiple_sources = 3e7`
- `penalty_warning = 0`

Nota: `penalty_warning = 0` evita que remociones validas dominen el fitness.

## DSS

- `use_dss_writer = True`
- `dss_output_folder = "outputs/dss_files"`
- `dss_base_filename = "network_stage"`
- `dss_base_kv = 13.8`
- `dss_pu_source = 1.0`
- `dss_angle = 0.0`
- `dss_load_connection = "Wye"`
- `dss_load_model = 1`
- `dss_collapse_sources = True`
- `dss_equivalent_source_name = "sourcebus"`
- `dss_write_comments = True`

