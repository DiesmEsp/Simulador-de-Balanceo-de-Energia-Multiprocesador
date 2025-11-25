"""
Módulo para la gestión de estrategias energéticas.
Implementa DVFS y diferentes políticas de balanceo de carga.
"""


class EnergyManager:
    """
    Gestiona las estrategias de consumo energético y DVFS.
    
    Implementa tres estrategias principales:
    - Performance-first: Máximo rendimiento
    - Energy-first: Mínimo consumo energético
    - Balanced (DVFS): Balance dinámico
    """
    
    def __init__(self, strategy='balanced'):
        """
        Inicializa el gestor de energía.
        
        Args:
            strategy (str): Estrategia a utilizar
                - 'performance': Máximo rendimiento
                - 'energy': Mínimo consumo
                - 'balanced': Balance con DVFS
        """
        self.strategy = strategy
        self.config = self._get_strategy_config()
        self.history = []
        
    def _get_strategy_config(self):
        """
        Obtiene la configuración de la estrategia seleccionada.
        
        Returns:
            dict: Configuración de la estrategia
        """
        configs = {
            'performance': {
                'base_freq': 3.5,           # Frecuencia máxima
                'min_freq': 3.0,            # Frecuencia mínima
                'max_freq': 4.0,            # Frecuencia pico
                'power_multiplier': 1.5,    # Mayor consumo
                'migration_threshold': 0.9, # Alta carga antes de migrar
                'scale_factor': 0.1,        # Ajuste mínimo de frecuencia
                'idle_power': 0.8,          # Consumo en idle alto
                'consolidate': False        # No consolidar tareas
            },
            'energy': {
                'base_freq': 1.8,           # Frecuencia baja
                'min_freq': 0.8,            # Frecuencia muy baja
                'max_freq': 2.5,            # Límite bajo
                'power_multiplier': 0.6,    # Menor consumo
                'migration_threshold': 0.5, # Migrar con carga baja
                'scale_factor': 0.3,        # Ajuste agresivo
                'idle_power': 0.1,          # Consumo en idle mínimo
                'consolidate': True         # Consolidar tareas
            },
            'balanced': {
                'base_freq': 2.5,           # Frecuencia moderada
                'min_freq': 1.2,            # Mínimo razonable
                'max_freq': 3.5,            # Máximo razonable
                'power_multiplier': 1.0,    # Consumo balanceado
                'migration_threshold': 0.7, # Umbral medio
                'scale_factor': 0.2,        # Ajuste moderado
                'idle_power': 0.3,          # Consumo idle moderado
                'consolidate': True         # Consolidar si es eficiente
            }
        }
        return configs.get(self.strategy, configs['balanced'])
    
    def adjust_frequency(self, processor):
        """
        Ajusta la frecuencia del procesador según su carga actual (DVFS).
        
        Args:
            processor (Processor): Procesador a ajustar
            
        Returns:
            float: Nueva frecuencia asignada
        """
        if self.strategy == 'performance':
            # Siempre máxima frecuencia
            new_freq = self.config['max_freq'] * processor.capacity
            
        elif self.strategy == 'energy':
            # Frecuencia mínima si hay tareas, apagar si no hay
            if processor.active_tasks:
                new_freq = self.config['min_freq'] * processor.capacity
            else:
                new_freq = 0.8 * processor.capacity  # Estado ultra-bajo
                
        else:  # balanced (DVFS)
            # Ajustar frecuencia según carga
            if not processor.active_tasks:
                new_freq = self.config['min_freq'] * processor.capacity
            else:
                # Frecuencia proporcional a la carga
                load_factor = 0.5 + (processor.load * 0.5)  # 50% base + 50% por carga
                new_freq = (self.config['base_freq'] * load_factor) * processor.capacity
                
                # Limitar entre mín y máx
                new_freq = max(self.config['min_freq'], 
                             min(new_freq, self.config['max_freq']))
        
        processor.set_frequency(new_freq)
        return new_freq
    
    def should_migrate_task(self, source_processor, target_processor):
        """
        Determina si se debe migrar una tarea entre procesadores.
        
        Args:
            source_processor (Processor): Procesador origen
            target_processor (Processor): Procesador destino
            
        Returns:
            bool: True si se debe migrar
        """
        # No migrar si el origen está por debajo del umbral
        if source_processor.load < self.config['migration_threshold']:
            return False
        
        # No migrar si el destino está muy cargado
        if target_processor.load > 0.7:
            return False
        
        # Migrar si hay diferencia significativa de carga
        load_diff = source_processor.load - target_processor.load
        
        if self.strategy == 'energy':
            # Energy-first: consolidar tareas
            return load_diff > 0.2 and self.config['consolidate']
            
        elif self.strategy == 'performance':
            # Performance-first: distribuir carga
            return load_diff > 0.4
            
        else:  # balanced
            # Balanced: migrar si hay desbalance moderado
            return load_diff > 0.3
    
    def select_target_processor(self, processors, current_processor):
        """
        Selecciona el mejor procesador destino para migración.
        
        Args:
            processors (list): Lista de procesadores disponibles
            current_processor (Processor): Procesador actual
            
        Returns:
            Processor: Mejor procesador destino, o None
        """
        candidates = [p for p in processors 
                     if p != current_processor and p.can_accept_task()]
        
        if not candidates:
            return None
        
        if self.strategy == 'energy' and self.config['consolidate']:
            # Energy: consolidar en procesadores ya activos
            active = [p for p in candidates if p.is_active]
            if active:
                return min(active, key=lambda p: p.load)
            return min(candidates, key=lambda p: p.load)
            
        elif self.strategy == 'performance':
            # Performance: usar procesador más potente disponible
            return max(candidates, key=lambda p: p.capacity)
            
        else:  # balanced
            # Balanced: procesador con menor carga
            return min(candidates, key=lambda p: p.load)
    
    def optimize_processor_states(self, processors):
        """
        Optimiza el estado de todos los procesadores según la estrategia.
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            dict: Estadísticas de optimización
        """
        adjustments = 0
        
        for processor in processors:
            old_freq = processor.frequency
            new_freq = self.adjust_frequency(processor)
            
            if abs(old_freq - new_freq) > 0.1:
                adjustments += 1
        
        # Estadísticas
        active_count = sum(1 for p in processors if p.is_active)
        total_load = sum(p.load for p in processors) / len(processors)
        total_energy = sum(p.energy_consumed for p in processors)
        
        stats = {
            'adjustments': adjustments,
            'active_processors': active_count,
            'avg_load': total_load,
            'total_energy': total_energy
        }
        
        self.history.append(stats)
        return stats
    
    def get_power_multiplier(self):
        """
        Obtiene el multiplicador de potencia para la estrategia actual.
        
        Returns:
            float: Multiplicador de potencia
        """
        return self.config['power_multiplier']
    
    def should_consolidate_tasks(self):
        """
        Indica si la estrategia debe consolidar tareas.
        
        Returns:
            bool: True si debe consolidar
        """
        return self.config.get('consolidate', False)
    
    def get_idle_power(self):
        """
        Obtiene el consumo de energía en estado idle.
        
        Returns:
            float: Potencia en idle
        """
        return self.config['idle_power']
    
    def get_strategy_info(self):
        """
        Obtiene información sobre la estrategia actual.
        
        Returns:
            dict: Información de la estrategia
        """
        strategy_names = {
            'performance': 'Performance-First',
            'energy': 'Energy-First',
            'balanced': 'Balanced (DVFS)'
        }
        
        return {
            'name': strategy_names.get(self.strategy, 'Unknown'),
            'strategy': self.strategy,
            'config': self.config,
            'description': self._get_strategy_description()
        }
    
    def _get_strategy_description(self):
        """Obtiene descripción de la estrategia actual."""
        descriptions = {
            'performance': 'Maximiza el rendimiento utilizando frecuencias altas constantemente.',
            'energy': 'Minimiza el consumo energético consolidando tareas y reduciendo frecuencia.',
            'balanced': 'Balancea rendimiento y energía ajustando frecuencia dinámicamente (DVFS).'
        }
        return descriptions.get(self.strategy, '')
    
    def reset(self):
        """Reinicia el historial del gestor de energía."""
        self.history = []


class DVFSController:
    """
    Controlador específico para DVFS (Dynamic Voltage and Frequency Scaling).
    """
    
    def __init__(self, min_freq=1.0, max_freq=4.0):
        """
        Inicializa el controlador DVFS.
        
        Args:
            min_freq (float): Frecuencia mínima en GHz
            max_freq (float): Frecuencia máxima en GHz
        """
        self.min_freq = min_freq
        self.max_freq = max_freq
        
    def calculate_optimal_frequency(self, load, base_freq):
        """
        Calcula la frecuencia óptima basada en la carga.
        
        Args:
            load (float): Carga del procesador (0.0-1.0)
            base_freq (float): Frecuencia base
            
        Returns:
            float: Frecuencia óptima en GHz
        """
        if load < 0.2:
            # Carga muy baja: frecuencia mínima
            target = self.min_freq
        elif load < 0.5:
            # Carga baja-media: escalar linealmente
            target = self.min_freq + (load - 0.2) * (base_freq - self.min_freq) / 0.3
        elif load < 0.8:
            # Carga media-alta: escalar hacia máxima
            target = base_freq + (load - 0.5) * (self.max_freq - base_freq) / 0.3
        else:
            # Carga alta: frecuencia máxima
            target = self.max_freq
        
        return max(self.min_freq, min(target, self.max_freq))