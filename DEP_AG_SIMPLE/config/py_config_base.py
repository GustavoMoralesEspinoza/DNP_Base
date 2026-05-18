"""
PyConfigBase: Configuración centralizada para DEP con Algoritmo Genético.

Esta clase almacena todos los parámetros de configuración del proyecto,
incluyendo parámetros del AG, del problema de DEP, y de módulos opcionales.
"""


class PyConfigBase:
    """
    Clase de configuración para el proyecto DEP_AG_SIMPLE.
    
    Almacena parámetros del algoritmo genético, problema, topología,
    módulos y objetivos de optimización.
    """

    def __init__(self):
        """
        Inicializa la configuración con valores por defecto.
        
        Parámetros del AG (Algoritmo Genético):
        - n_individuals: número de individuos en la población
        - n_iterations: número de iteraciones/generaciones
        - crossover_rate: tasa de cruzamiento [0, 1]
        - mutation_rate: tasa de mutación [0, 1]
        - elitism_rate: tasa de elitismo [0, 1]
        - random_seed: semilla para reproducibilidad
        
        Parámetros del problema:
        - n_stages: número de etapas de planeamiento
        - stage_years: años en cada etapa [lista]
        
        Parámetros de topología:
        - use_topology_repair: aplicar reparación de topología
        - use_reconnection: permitir reconexión de líneas
        - use_radiality_repair: reparar radialidad de red
        
        Parámetros de módulos:
        - use_open_dss: ejecutar flujo de potencia con OpenDSS
        - use_investment_cost: considerar costo de inversión
        - use_electrical_loss_cost: considerar costo de pérdidas
        - use_present_value: usar valor presente en flujo de caja
        
        Parámetros de objetivos:
        - w_inv: peso del costo de inversión
        - w_ele: peso del costo de pérdidas eléctricas
        
        Parámetros económicos:
        - interest_rate: tasa de interés anual
        - energy_price: precio de la energía [$/kWh]
        
        Parámetros de límites:
        - v_min_pu: tensión mínima [pu]
        - v_max_pu: tensión máxima [pu]
        - c_inv_max: costo máximo de inversión normalizado
        - c_ele_max: costo máximo de pérdidas normalizado
        """
        
        # Parámetros del AG
        self.n_individuals = 20
        self.n_iterations = 30
        self.crossover_rate = 0.8
        self.mutation_rate = 0.05
        self.elitism_rate = 0.2
        self.random_seed = 10
        
        # Parámetros del problema
        self.n_stages = 3
        self.stage_years = [1, 1, 2]
        
        # Parámetros de topología
        self.use_topology_validation = True

        # -1 significa línea apagada, no instalada o removida.
        # Pero una línea solo puede tomar -1 si -1 aparece dentro de sus opciones válidas.
        # Si valid_options_by_line[line_id] = [0, 1, 2, 3], la línea es obligatoria:
        # puede cambiar de opción, pero no puede desaparecer.
        # Si valid_options_by_line[line_id] = [-1, 0, 1, 2, 3], la línea es removible/candidata:
        # puede apagarse, mantenerse o reforzarse.
        # Si valid_options_by_line[line_id] = [-1, 1, 2, 3], la línea es candidata nueva:
        # puede no instalarse o instalarse con alguna opción válida.

        # Activa la reparación topológica previa a evaluar fitness.
        # Conviene apagarlo para depurar el AG "crudo" y prenderlo para buscar soluciones factibles.
        self.use_topology_repair = True
        self.use_reconnection = True
        self.use_radiality_repair = True

        # Intenta conectar componentes sin fuente o cargas aisladas activando líneas disponibles.
        self.use_reconnection_repair = True

        # Intenta romper ciclos apagando líneas removibles.
        self.use_cycle_repair = True

        # Si las fuentes no están colapsadas, intenta separar componentes con múltiples fuentes.
        self.use_multiple_sources_repair = True

        # Límite de iteraciones por estágio para evitar bucles infinitos de reparación.
        self.repair_max_iterations = 20

        # Estrategia de reparación: "random" explora más alternativas; "cheapest" es determinística por costo.
        self.repair_strategy = "random"

        # Semilla usada solo por la reparación cuando repair_strategy == "random".
        self.repair_random_seed = 42

        # Imprime/guarda más detalle de reparación cuando se use en reportes.
        self.repair_verbose = True

        # Si True, solo apaga líneas cuyo catálogo permita -1 explícitamente.
        self.repair_only_removable_lines = True

        # Si True, permite apagar líneas aunque -1 no sea opción válida. Útil solo para debug agresivo.
        self.repair_allow_remove_non_candidate = True
        self.use_topology_debug_plots = True
        self.topology_debug_output_folder = "outputs/topology_debug"
        self.topology_debug_with_labels = True
        self.topology_debug_layout_seed = 42

        # Si True, todas las subestaciones SE_* se interpretan como una fuente equivalente.
        # Conviene prenderlo cuando el modelo eléctrico representa una misma fuente agregada.
        self.collapse_sources = True

        # Nombre del nodo equivalente usado al colapsar fuentes.
        self.equivalent_source_name = "SE_1"

        # Si True, no penaliza una componente con varias fuentes reales.
        # Normalmente se deja False salvo estudios donde las fuentes paralelas son aceptables.
        self.allow_multiple_sources_per_component = False
        
        # Parámetros de módulos
        self.use_open_dss = False
        self.use_investment_cost = True
        self.use_electrical_loss_cost = False
        self.use_present_value = True

        # Generación de archivos DSS. Solo escribe archivos; no ejecuta OpenDSS.
        self.use_dss_writer = True
        self.dss_output_folder = "outputs/dss_files"
        self.dss_base_filename = "network_stage"
        self.dss_base_kv = 13.8
        self.dss_pu_source = 1.0
        self.dss_angle = 0.0
        self.dss_load_connection = "Wye"
        self.dss_load_model = 1
        self.dss_collapse_sources = True
        self.dss_equivalent_source_name = "sourcebus"
        self.dss_write_comments = True

        # Ejecucion OpenDSS 24 h para la mejor solucion final.
        self.use_dss_runner = True
        self.dss_simulation_hours = 24
        self.dss_mode = "daily"
        self.dss_runner_verbose = True
        self.dss_continue_on_error = True
        
        # Parámetros de objetivos
        self.w_inv = 0.7
        self.w_ele = 0.3
        
        # Parámetros económicos
        self.interest_rate = 0.10
        self.energy_price = 0.1
        self.removal_factor = 0.30  # Factor de costo para remover/reemplazar líneas
        
        # Parámetros de límites
        self.v_min_pu = 0.95
        self.v_max_pu = 1.05
        self.c_inv_max = 1.0
        self.c_ele_max = 1.0
        
        # Parámetros de penalidades y normalización
        # Penalidades por errores graves de codificación/opciones.
        self.penalty_invalid_option = 1e8

        # Penalidades topológicas críticas.
        self.penalty_component_without_source = 1e8
        self.penalty_disconnected_load = 8e7
        self.penalty_isolated_bus = 7e7

        # Penalidades de radialidad/ciclos.
        self.penalty_cycle = 5e7
        self.penalty_nodes_in_cycles = 1e7

        # Penalidades por múltiples fuentes.
        self.penalty_multiple_sources = 3e7

        # Penalidades por warnings generales.
        self.penalty_warning = 0
        self.minimum_normalization_value = 1e-9 # Mínimo para evitar división por cero

    def show(self):
        """
        Imprime en consola los parámetros principales de la configuración.
        
        Organiza la salida en secciones temáticas para legibilidad.
        """
        print("\n" + "="*60)
        print("CONFIGURACIÓN DEL PROYECTO DEP_AG_SIMPLE")
        print("="*60)
        
        print("\n[ALGORITMO GENÉTICO]")
        print(f"  Individuos:              {self.n_individuals}")
        print(f"  Iteraciones:             {self.n_iterations}")
        print(f"  Tasa de cruzamiento:     {self.crossover_rate}")
        print(f"  Tasa de mutación:        {self.mutation_rate}")
        print(f"  Tasa de elitismo:        {self.elitism_rate}")
        print(f"  Semilla aleatoria:       {self.random_seed}")
        
        print("\n[PROBLEMA]")
        print(f"  Etapas de planeamiento:  {self.n_stages}")
        print(f"  Años por etapa:          {self.stage_years}")
        
        print("\n[TOPOLOGÍA]")
        print(f"  Validación de topología: {self.use_topology_validation}")
        print(f"  Reparación de topología: {self.use_topology_repair}")
        print(f"  Reconexión permitida:    {self.use_reconnection}")
        print(f"  Reparación de radialidad:{self.use_radiality_repair}")
        print(f"  Reparación reconexión:   {self.use_reconnection_repair}")
        print(f"  Reparación ciclos:       {self.use_cycle_repair}")
        print(f"  Reparación múltiples fuentes: {self.use_multiple_sources_repair}")
        print(f"  Máx. iteraciones reparación: {self.repair_max_iterations}")
        print(f"  Estrategia reparación:   {self.repair_strategy}")
        print(f"  Remover solo líneas removibles: {self.repair_only_removable_lines}")
        print(f"  Debug plots topología:   {self.use_topology_debug_plots}")
        print(f"  Carpeta debug topología: {self.topology_debug_output_folder}")
        print(f"  Colapsar fuentes:        {self.collapse_sources}")
        print(f"  Fuente equivalente:      {self.equivalent_source_name}")
        print(f"  Permitir múltiples fuentes/componente: {self.allow_multiple_sources_per_component}")
        
        print("\n[MÓDULOS ACTIVOS]")
        print(f"  OpenDSS:                 {self.use_open_dss}")
        print(f"  Costo de inversión:      {self.use_investment_cost}")
        print(f"  Costo de pérdidas:       {self.use_electrical_loss_cost}")
        print(f"  Valor presente:          {self.use_present_value}")
        print(f"  DSS writer:              {self.use_dss_writer}")
        print(f"  DSS runner:              {self.use_dss_runner}")
        print(f"  Carpeta DSS:             {self.dss_output_folder}")
        print(f"  Base kV DSS:             {self.dss_base_kv}")
        print(f"  Colapsar fuentes DSS:    {self.dss_collapse_sources}")
        print(f"  Horas simulacion DSS:    {self.dss_simulation_hours}")
        print(f"  Modo DSS:                {self.dss_mode}")
        
        print("\n[OBJETIVOS]")
        print(f"  Peso inversión (w_inv):  {self.w_inv}")
        print(f"  Peso pérdidas (w_ele):   {self.w_ele}")
        
        print("\n[ECONOMÍA]")
        print(f"  Tasa de interés:         {self.interest_rate}")
        print(f"  Precio energía:          {self.energy_price} $/kWh")
        print(f"  Factor de remoción:      {self.removal_factor}")
        
        print("\n[LÍMITES]")
        print(f"  Tensión mínima:          {self.v_min_pu} pu")
        print(f"  Tensión máxima:          {self.v_max_pu} pu")
        print(f"  Costo inv. máximo:       {self.c_inv_max}")
        print(f"  Costo pérd. máximo:      {self.c_ele_max}")
        
        print("\n[PENALIDADES Y NORMALIZACIÓN]")
        print(f"  Penalidad opción inválida: {self.penalty_invalid_option:.0e}")
        print(f"  Penalidad por advertencia: {self.penalty_warning:.0e}")
        print(f"  Penalidad por ciclo:     {self.penalty_cycle:.0e}")
        print(f"  Penalidad nodos en ciclo:{self.penalty_nodes_in_cycles:.0e}")
        print(f"  Penalidad bus aislado:   {self.penalty_isolated_bus:.0e}")
        print(f"  Penalidad comp. sin fuente: {self.penalty_component_without_source:.0e}")
        print(f"  Penalidad múltiples fuentes: {self.penalty_multiple_sources:.0e}")
        print(f"  Penalidad carga desconectada: {self.penalty_disconnected_load:.0e}")
        print(f"  Mínimo normalización:    {self.minimum_normalization_value:.0e}")
        
        print("\n" + "="*60 + "\n")
