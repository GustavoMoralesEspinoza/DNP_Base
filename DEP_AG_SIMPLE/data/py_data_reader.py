"""
PyDataReader: Lector robusto de datos DEP desde CSVs normalizados.

Lee los CSVs de Initialdata/ y construye estructura interna unificada
para ser usada por cromosoma, evaluador, topología, OpenDSS y costos.
"""

import os
import csv


class PyDataReader:
    """
    Lee y valida datos de entrada para el modelo DEP con AG.
    """

    def __init__(self, data_dir="Initialdata"):
        self.data_dir = data_dir
        self.data = {}
        self.validation_errors = []
        self.validation_warnings = []

    def read_all(self):
        """Lee y valida todos los datos disponibles."""
        print("\n" + "-"*70)
        print("CARGANDO DATOS INICIALES DEL MODELO DEP")
        print("-"*70)
        
        try:
            self._read_buses()
            self._read_loads()
            self._read_load_curves()
            self._read_line_options()
            self._read_line_catalog()
            
            self._validate_all()
            
            self.data["validated"] = len(self.validation_errors) == 0
            self.data["validation_errors"] = self.validation_errors
            self.data["validation_warnings"] = self.validation_warnings
            self.data["data_dir"] = self.data_dir
            
            return self.data
            
        except Exception as e:
            self.validation_errors.append(f"ERROR CRÍTICO en lectura: {str(e)}")
            raise

    def _read_buses(self):
        """Lee bus_catalog.csv y construye catálogo de buses."""
        filepath = os.path.join(self.data_dir, "bus_catalog.csv")
        
        buses = {}
        source_buses = []
        load_buses = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    bus_name = row['bus'].strip()
                    bus_type = row['bus_type'].strip()
                    has_load = row['has_load'].strip().lower() == 'yes'
                    
                    buses[bus_name] = {
                        'type': bus_type,
                        'has_load': has_load,
                        'load_count': int(row['load_count']) if has_load else 0
                    }
                    
                    if 'source' in bus_type.lower() or 'se' in bus_name.lower():
                        source_buses.append(bus_name)
                    
                    if has_load:
                        load_buses.append(bus_name)
            
            self.data['buses'] = buses
            self.data['source_buses'] = source_buses
            self.data['load_buses'] = load_buses
            self.data['n_buses'] = len(buses)
            
            print(f"\n✓ bus_catalog.csv: {len(buses)} buses cargados")
            print(f"  - Subestaciones: {len(source_buses)} ({', '.join(source_buses)})")
            print(f"  - Buses de carga: {len(load_buses)}")
            
        except FileNotFoundError:
            msg = f"ERROR: No encontrado {filepath}"
            self.validation_errors.append(msg)
            raise FileNotFoundError(msg)

    def _read_loads(self):
        """Lee loads_projection_master.csv y agrupa por etapa."""
        filepath = os.path.join(self.data_dir, "loads_projection_master.csv")
        
        loads_by_stage = {1: {}, 2: {}, 3: {}}
        consumer_types_by_stage = {1: {}, 2: {}, 3: {}}
        load_count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    load_id = row['load_id'].strip()
                    bus = row['bus'].strip()
                    load_count += 1
                    
                    for stage in [1, 2, 3]:
                        p_key = f'P_stage_{stage}_kW'
                        q_key = f'Q_stage_{stage}_kVAr'
                        consumer_key = f'consumer_stage_{stage}'
                        class_key = f'consumer_class_stage_{stage}'
                        
                        if p_key in row and q_key in row:
                            loads_by_stage[stage][load_id] = {
                                'bus': bus,
                                'P_kW': float(row[p_key]),
                                'Q_kVAr': float(row[q_key]),
                                'consumer_type': row[consumer_key].strip(),
                                'consumer_class': row[class_key].strip()
                            }
                            
                            consumer_type = row[consumer_key].strip()
                            if consumer_type not in consumer_types_by_stage[stage]:
                                consumer_types_by_stage[stage][consumer_type] = 0
                            consumer_types_by_stage[stage][consumer_type] += 1
            
            self.data['loads_by_stage'] = loads_by_stage
            self.data['consumer_types_by_stage'] = consumer_types_by_stage
            self.data['n_loads'] = load_count
            
            print(f"\n✓ loads_projection_master.csv: {load_count} cargas cargadas")
            for stage in [1, 2, 3]:
                types_str = ', '.join([f"{k}({v})" for k, v in consumer_types_by_stage[stage].items()])
                print(f"  - Etapa {stage}: {len(loads_by_stage[stage])} cargas ({types_str})")
            
        except FileNotFoundError:
            msg = f"ERROR: No encontrado {filepath}"
            self.validation_errors.append(msg)
            raise FileNotFoundError(msg)

    def _read_load_curves(self):
        """Lee curvas horarias por tipo de consumidor si el CSV existe."""
        filepath = os.path.join(self.data_dir, "load_curves_by_consumer_type_template.csv")
        load_curves = {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    self.data['load_curves'] = load_curves
                    return

                curve_columns = [
                    field for field in reader.fieldnames
                    if field and field.strip().lower() != "hour"
                ]
                load_curves = {field.strip(): [] for field in curve_columns}

                for row in reader:
                    for field in curve_columns:
                        curve_name = field.strip()
                        value = row.get(field, "")
                        try:
                            load_curves[curve_name].append(float(value))
                        except (TypeError, ValueError):
                            load_curves[curve_name].append(1.0)

            self.data['load_curves'] = load_curves
            print(
                "\n✓ load_curves_by_consumer_type_template.csv: "
                f"{len(load_curves)} curvas cargadas"
            )

        except FileNotFoundError:
            self.data['load_curves'] = {}
            warning = f"WARNING: No encontrado {filepath}; se usaran curvas planas"
            self.validation_warnings.append(warning)
            print(f"\n{warning}")

    def _read_line_options(self):
        """Lee line_valid_options.csv y construye mapeo de opciones."""
        filepath = os.path.join(self.data_dir, "line_valid_options.csv")
        
        valid_options_by_line = {}
        base_option_by_line = {}
        line_index_map = {}
        n_lines = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    line_id = row['line_id'].strip()
                    options_str = row['valid_options'].strip()
                    first_valid = int(row['first_valid_option'].strip())
                    
                    options = [int(opt.strip()) for opt in options_str.split('|')]
                    
                    valid_options_by_line[line_id] = options
                    base_option_by_line[line_id] = first_valid
                    line_index_map[line_id] = n_lines
                    n_lines += 1
            
            self.data['valid_options_by_line'] = valid_options_by_line
            self.data['base_option_by_line'] = base_option_by_line
            self.data['line_index_map'] = line_index_map
            self.data['n_lines'] = n_lines
            
            new_lines = [lid for lid, opt in base_option_by_line.items() if opt > 0]
            
            print(f"\n✓ line_valid_options.csv: {n_lines} líneas candidatas")
            print(f"  - Líneas existentes: {n_lines - len(new_lines)}")
            print(f"  - Líneas nuevas (requeridas): {len(new_lines)}")
            if new_lines:
                print(f"    Ejemplo: {new_lines[0]} (opción inicial: {base_option_by_line[new_lines[0]]})")
            
        except FileNotFoundError:
            msg = f"ERROR: No encontrado {filepath}"
            self.validation_errors.append(msg)
            raise FileNotFoundError(msg)

    def _read_line_catalog(self):
        """Lee line_options_long_normalized.csv y construye catálogo técnico."""
        filepath = os.path.join(self.data_dir, "line_options_long_normalized.csv")
        
        line_catalog = {}
        line_topology = {}
        cost_range = [float('inf'), float('-inf')]
        capacity_range = [float('inf'), float('-inf')]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    line_id = row['line_id'].strip()
                    bar_1 = row['bar_1'].strip()
                    bar_2 = row['bar_2'].strip()
                    option_id = int(row['option_id'].strip())
                    
                    cost = float(row['cost_usd'].strip())
                    imax = float(row['imax_A'].strip())
                    r1 = float(row['r1_ohm_km'].strip())
                    x1 = float(row['x1_ohm_km'].strip())
                    length = float(row['length_km'].strip())
                    
                    cost_range[0] = min(cost_range[0], cost)
                    cost_range[1] = max(cost_range[1], cost)
                    capacity_range[0] = min(capacity_range[0], imax)
                    capacity_range[1] = max(capacity_range[1], imax)
                    
                    if line_id not in line_catalog:
                        line_catalog[line_id] = {
                            'bar_1': bar_1,
                            'bar_2': bar_2,
                            'options_detail': {}
                        }
                        line_topology[line_id] = (bar_1, bar_2)
                    
                    line_catalog[line_id]['options_detail'][option_id] = {
                        'cost': cost,
                        'imax_A': imax,
                        'r1_ohm_km': r1,
                        'x1_ohm_km': x1,
                        'length_km': length
                    }
            
            self.data['line_catalog'] = line_catalog
            self.data['line_topology'] = line_topology
            
            n_records = len(line_catalog)
            avg_options = sum(len(lc['options_detail']) for lc in line_catalog.values()) / max(n_records, 1)
            
            print(f"\n✓ line_options_long_normalized.csv: {n_records} líneas, {sum(len(lc['options_detail']) for lc in line_catalog.values())} registros")
            print(f"  - Opciones promedio/línea: {avg_options:.1f}")
            print(f"  - Costo: ${cost_range[0]:.0f} a ${cost_range[1]:.0f}")
            print(f"  - Capacidad: {capacity_range[0]:.0f}A a {capacity_range[1]:.0f}A")
            
        except FileNotFoundError:
            msg = f"ERROR: No encontrado {filepath}"
            self.validation_errors.append(msg)
            raise FileNotFoundError(msg)

    def _validate_all(self):
        """Valida consistencia entre todos los datos cargados."""
        print(f"\n" + "="*70)
        print("VALIDACIONES")
        print("="*70)
        
        for line_id in self.data['valid_options_by_line'].keys():
            if line_id not in self.data['line_catalog']:
                self.validation_errors.append(
                    f"Línea {line_id} en line_valid_options pero NO en line_options_long"
                )
        print(f"✓ Todas las líneas tienen opciones técnicas definidas")
        
        all_buses = set(self.data['buses'].keys())
        for stage, loads in self.data['loads_by_stage'].items():
            for load_id, load_data in loads.items():
                bus = load_data['bus']
                if bus not in all_buses:
                    self.validation_errors.append(
                        f"Carga {load_id} en etapa {stage} referencia bus {bus} NO definido"
                    )
        print(f"✓ Todas las cargas referenciadas a buses válidos")
        
        n_stages = len(self.data['loads_by_stage'])
        self.data['n_stages'] = n_stages
        print(f"✓ Etapas: {n_stages} confirmadas")
        
        print(f"\n" + "="*70)
        print("RESUMEN DE DATOS CARGADOS")
        print("="*70)
        print(f"Buses:           {self.data['n_buses']}")
        print(f"Líneas:          {self.data['n_lines']}")
        print(f"Cargas:          {self.data['n_loads']}")
        print(f"Etapas:          {self.data['n_stages']}")
        print(f"Validado:        {'SÍ ✓' if self.data.get('validated', False) else 'NO ✗'}")
        print(f"Errores:         {len(self.validation_errors)}")
        print(f"Advertencias:    {len(self.validation_warnings)}")
        print("="*70)
