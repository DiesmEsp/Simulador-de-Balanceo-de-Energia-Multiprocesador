"""
Módulo de planificación de tareas.
Implementa algoritmos de asignación y migración de tareas.
"""


class Scheduler:
    """
    Planificador de tareas para el sistema multiprocesador.
    Gestiona la asignación y migración de tareas según la estrategia energética.
    """
    
    def __init__(self, processor_pool, energy_manager):
        """
        Inicializa el planificador.
        
        Args:
            processor_pool (ProcessorPool): Pool de procesadores
            energy_manager (EnergyManager): Gestor de energía
        """
        self.processor_pool = processor_pool
        self.energy_manager = energy_manager
        self.assignment_history = []
        self.migration_count = 0
        
    def assign_tasks(self, tasks):
        """
        Asigna tareas a procesadores según la estrategia actual.
        
        Args:
            tasks (list): Lista de tareas a asignar
            
        Returns:
            int: Número de tareas asignadas
        """
        assigned_count = 0
        strategy = self.energy_manager.strategy
        
        for task in tasks:
            if task.assigned or task.completed:
                continue
            
            processor = self._select_processor_for_task(task, strategy)
            
            if processor and processor.add_task(task):
                self.assignment_history.append({
                    'task_id': task.task_id,
                    'processor_id': processor.processor_id,
                    'timestamp': 0  # Será actualizado por el simulador
                })
                assigned_count += 1
        
        return assigned_count
    
    def _select_processor_for_task(self, task, strategy):
        """
        Selecciona el mejor procesador para una tarea según la estrategia.
        
        Args:
            task (Task): Tarea a asignar
            strategy (str): Estrategia energética
            
        Returns:
            Processor: Procesador seleccionado o None
        """
        processors = self.processor_pool.processors
        available = [p for p in processors if p.can_accept_task()]
        
        if not available:
            return None
        
        if strategy == 'performance':
            # Performance-first: usar el procesador más rápido disponible
            return max(available, key=lambda p: p.frequency)
            
        elif strategy == 'energy':
            # Energy-first: consolidar en procesadores ya activos
            if self.energy_manager.should_consolidate_tasks():
                active = [p for p in available if p.is_active]
                if active:
                    # Usar el procesador activo con menor carga
                    return min(active, key=lambda p: p.load)
                else:
                    # Si no hay activos, usar el primero disponible
                    return available[0]
            else:
                # Si no consolidar, usar el menos cargado
                return min(available, key=lambda p: p.load)
                
        else:  # balanced
            # Balanced: balancear carga entre procesadores
            return min(available, key=lambda p: p.load)
    
    def migrate_tasks(self):
        """
        Intenta migrar tareas entre procesadores para mejorar balance.
        
        Returns:
            int: Número de migraciones realizadas
        """
        migrations = 0
        processors = self.processor_pool.processors
        
        # Ordenar por carga (descendente)
        sorted_procs = sorted(processors, key=lambda p: p.load, reverse=True)
        
        for source in sorted_procs:
            if not source.active_tasks:
                continue
            
            for target in processors:
                if source == target:
                    continue
                
                # Verificar si se debe migrar
                if self.energy_manager.should_migrate_task(source, target):
                    if self._migrate_one_task(source, target):
                        migrations += 1
                        self.migration_count += 1
                        break  # Solo una migración por iteración
        
        return migrations
    
    def _migrate_one_task(self, source, target):
        """
        Migra una tarea de un procesador a otro.
        
        Args:
            source (Processor): Procesador origen
            target (Processor): Procesador destino
            
        Returns:
            bool: True si la migración fue exitosa
        """
        if not source.active_tasks or not target.can_accept_task():
            return False
        
        # Seleccionar tarea a migrar (la de mayor duración restante)
        task_to_migrate = max(source.active_tasks, key=lambda t: t.remaining)
        
        # Remover de origen
        source.active_tasks.remove(task_to_migrate)
        source._update_load()
        
        # Añadir a destino
        task_to_migrate.processor_id = target.processor_id
        success = target.add_task(task_to_migrate)
        
        if not success:
            # Si falla, regresar a origen
            source.active_tasks.append(task_to_migrate)
            source._update_load()
            task_to_migrate.processor_id = source.processor_id
            return False
        
        return True
    
    def get_assignment_statistics(self):
        """
        Obtiene estadísticas de asignación de tareas.
        
        Returns:
            dict: Estadísticas
        """
        processors = self.processor_pool.processors
        
        assignments_per_proc = {}
        for proc in processors:
            assignments_per_proc[proc.processor_id] = proc.completed_tasks
        
        return {
            'total_assignments': sum(assignments_per_proc.values()),
            'assignments_per_processor': assignments_per_proc,
            'total_migrations': self.migration_count,
            'avg_assignments': sum(assignments_per_proc.values()) / len(processors)
        }
    
    def get_load_distribution(self):
        """
        Obtiene la distribución de carga actual.
        
        Returns:
            list: Lista de cargas por procesador
        """
        return [p.load for p in self.processor_pool.processors]
    
    def reset(self):
        """Reinicia el planificador."""
        self.assignment_history = []
        self.migration_count = 0


class RoundRobinScheduler(Scheduler):
    """
    Planificador Round-Robin simple.
    Asigna tareas de forma circular entre procesadores.
    """
    
    def __init__(self, processor_pool, energy_manager):
        super().__init__(processor_pool, energy_manager)
        self.current_index = 0
    
    def _select_processor_for_task(self, task, strategy):
        """Selecciona procesador en orden circular."""
        processors = self.processor_pool.processors
        attempts = 0
        
        while attempts < len(processors):
            processor = processors[self.current_index]
            self.current_index = (self.current_index + 1) % len(processors)
            
            if processor.can_accept_task():
                return processor
            
            attempts += 1
        
        return None


class LoadBalancingScheduler(Scheduler):
    """
    Planificador con énfasis en balance de carga.
    Siempre asigna al procesador con menor carga.
    """
    
    def _select_processor_for_task(self, task, strategy):
        """Selecciona procesador con menor carga."""
        available = [p for p in self.processor_pool.processors if p.can_accept_task()]
        
        if not available:
            return None
        
        return min(available, key=lambda p: p.load)


class PriorityScheduler(Scheduler):
    """
    Planificador basado en prioridades.
    Las tareas con mayor intensidad se asignan a procesadores más potentes.
    """
    
    def _select_processor_for_task(self, task, strategy):
        """Selecciona procesador según prioridad de tarea."""
        available = [p for p in self.processor_pool.processors if p.can_accept_task()]
        
        if not available:
            return None
        
        if task.intensity > 0.7:
            # Tarea intensiva: procesador más potente
            return max(available, key=lambda p: p.capacity)
        else:
            # Tarea ligera: procesador menos cargado
            return min(available, key=lambda p: p.load)