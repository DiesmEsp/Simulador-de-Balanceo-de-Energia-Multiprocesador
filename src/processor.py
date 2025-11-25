"""
Módulo para la gestión de procesadores en el simulador.
Define la clase Processor que representa un núcleo de procesamiento.
"""


class Processor:
    """
    Representa un procesador/núcleo en el sistema multiprocesador.
    
    Attributes:
        processor_id (int): Identificador único del procesador
        capacity (float): Capacidad relativa del procesador (1.0 = normal)
        frequency (float): Frecuencia de operación actual en GHz
        base_frequency (float): Frecuencia base del procesador
        load (float): Carga actual del procesador (0.0-1.0)
        energy_consumed (float): Energía total consumida en Joules
        execution_time (float): Tiempo total de ejecución
        completed_tasks (int): Contador de tareas completadas
        active_tasks (list): Lista de tareas actualmente en ejecución
        is_active (bool): Indica si el procesador está activo
        idle_time (float): Tiempo total en estado inactivo
    """
    
    def __init__(self, processor_id, capacity=1.0, base_frequency=2.5):
        """
        Inicializa un nuevo procesador.
        
        Args:
            processor_id (int): Identificador único
            capacity (float): Capacidad relativa (default: 1.0)
            base_frequency (float): Frecuencia base en GHz (default: 2.5)
        """
        self.processor_id = processor_id
        self.capacity = capacity
        self.frequency = base_frequency * capacity
        self.base_frequency = base_frequency
        self.load = 0.0
        self.energy_consumed = 0.0
        self.execution_time = 0.0
        self.completed_tasks = 0
        self.active_tasks = []
        self.is_active = False
        self.idle_time = 0.0
        self.peak_load = 0.0
        
    def add_task(self, task):
        """
        Añade una tarea al procesador.
        
        Args:
            task (Task): Tarea a añadir
            
        Returns:
            bool: True si se añadió exitosamente, False si está lleno
        """
        if len(self.active_tasks) < 5:  # Límite de tareas concurrentes
            self.active_tasks.append(task)
            task.assign_to_processor(self.processor_id)
            self.is_active = True
            self._update_load()
            return True
        return False
    
    def remove_task(self, task):
        """
        Elimina una tarea del procesador.
        
        Args:
            task (Task): Tarea a eliminar
        """
        if task in self.active_tasks:
            self.active_tasks.remove(task)
            self.completed_tasks += 1
            self._update_load()
    
    def _update_load(self):
        """
        Actualiza el nivel de carga del procesador basándose en las tareas activas.
        """
        if not self.active_tasks:
            self.load = 0.0
            self.is_active = False
        else:
            # Carga basada en número de tareas e intensidad promedio
            num_tasks = len(self.active_tasks)
            avg_intensity = sum(t.intensity for t in self.active_tasks) / num_tasks
            self.load = min(1.0, (num_tasks * 0.25) + (avg_intensity * 0.5))
            self.is_active = True
            
            # Actualizar pico de carga
            if self.load > self.peak_load:
                self.peak_load = self.load
    
    def set_frequency(self, frequency):
        """
        Ajusta la frecuencia de operación del procesador.
        
        Args:
            frequency (float): Nueva frecuencia en GHz
        """
        self.frequency = max(0.8, min(frequency, 4.0))  # Límites realistas
    
    def execute_step(self, time_step, power_multiplier=1.0):
        """
        Ejecuta un paso de simulación, procesando tareas y consumiendo energía.
        
        Args:
            time_step (float): Duración del paso de tiempo
            power_multiplier (float): Multiplicador de consumo energético
            
        Returns:
            list: Tareas completadas en este paso
        """
        completed = []
        
        if self.active_tasks:
            # Procesar cada tarea activa
            avg_intensity = sum(t.intensity for t in self.active_tasks) / len(self.active_tasks)
            
            # Calcular potencia consumida (P = C * V^2 * f, aproximado)
            # Frecuencia al cuadrado como aproximación del consumo
            power = (self.frequency ** 2) * avg_intensity * power_multiplier
            self.energy_consumed += power * time_step
            self.execution_time += time_step
            
            # Procesar tareas
            for task in self.active_tasks[:]:  # Copia para poder modificar durante iteración
                work_done = self.frequency * self.capacity * time_step
                if task.update_progress(work_done):
                    completed.append(task)
                    self.remove_task(task)
        else:
            # Procesador inactivo - consumo mínimo
            idle_power = 0.1 * power_multiplier  # Consumo en idle
            self.energy_consumed += idle_power * time_step
            self.idle_time += time_step
        
        return completed
    
    def get_utilization(self):
        """
        Calcula el porcentaje de utilización del procesador.
        
        Returns:
            float: Porcentaje de utilización (0-100)
        """
        if self.execution_time == 0:
            return 0.0
        active_time = self.execution_time - self.idle_time
        return (active_time / self.execution_time) * 100
    
    def get_efficiency(self):
        """
        Calcula la eficiencia energética del procesador.
        
        Returns:
            float: Tareas completadas por Joule de energía
        """
        if self.energy_consumed == 0:
            return 0.0
        return self.completed_tasks / self.energy_consumed
    
    def can_accept_task(self):
        """
        Verifica si el procesador puede aceptar más tareas.
        
        Returns:
            bool: True si puede aceptar más tareas
        """
        return len(self.active_tasks) < 5
    
    def get_status(self):
        """
        Obtiene el estado actual del procesador.
        
        Returns:
            dict: Diccionario con métricas actuales
        """
        return {
            'id': self.processor_id,
            'frequency': self.frequency,
            'load': self.load,
            'energy': self.energy_consumed,
            'execution_time': self.execution_time,
            'completed_tasks': self.completed_tasks,
            'active_tasks': len(self.active_tasks),
            'is_active': self.is_active,
            'utilization': self.get_utilization(),
            'efficiency': self.get_efficiency()
        }
    
    def reset(self):
        """Reinicia el procesador a su estado inicial."""
        self.frequency = self.base_frequency * self.capacity
        self.load = 0.0
        self.energy_consumed = 0.0
        self.execution_time = 0.0
        self.completed_tasks = 0
        self.active_tasks = []
        self.is_active = False
        self.idle_time = 0.0
        self.peak_load = 0.0
    
    def __repr__(self):
        return (f"Processor(id={self.processor_id}, freq={self.frequency:.2f}GHz, "
                f"load={self.load:.2%}, tasks={len(self.active_tasks)})")


class ProcessorPool:
    """
    Administra un conjunto de procesadores.
    """
    
    def __init__(self, num_processors, scenario='balanced'):
        """
        Inicializa un pool de procesadores.
        
        Args:
            num_processors (int): Número de procesadores a crear
            scenario (str): Tipo de configuración ('balanced', 'heterogeneous')
        """
        self.processors = []
        
        for i in range(num_processors):
            if scenario == 'heterogeneous':
                # Mitad de procesadores potentes, mitad débiles
                capacity = 1.3 if i < num_processors // 2 else 0.7
            else:
                capacity = 1.0
            
            processor = Processor(
                processor_id=i,
                capacity=capacity,
                base_frequency=2.5
            )
            self.processors.append(processor)
    
    def get_processor(self, processor_id):
        """Obtiene un procesador por su ID."""
        if 0 <= processor_id < len(self.processors):
            return self.processors[processor_id]
        return None
    
    def get_least_loaded(self):
        """Retorna el procesador con menor carga."""
        return min(self.processors, key=lambda p: p.load)
    
    def get_most_loaded(self):
        """Retorna el procesador con mayor carga."""
        return max(self.processors, key=lambda p: p.load)
    
    def get_active_processors(self):
        """Retorna lista de procesadores activos."""
        return [p for p in self.processors if p.is_active]
    
    def get_idle_processors(self):
        """Retorna lista de procesadores inactivos."""
        return [p for p in self.processors if not p.is_active]
    
    def reset_all(self):
        """Reinicia todos los procesadores."""
        for processor in self.processors:
            processor.reset()