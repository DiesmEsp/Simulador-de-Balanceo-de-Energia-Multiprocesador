"""
Estrategia Performance-First: Prioriza máximo rendimiento sin considerar energía.
"""
from typing import List, TYPE_CHECKING
import numpy as np

from .base_scheduler import BaseScheduler, LoadAwareMixin

if TYPE_CHECKING:
    from ..core.task import Task


class PerformanceFirstScheduler(BaseScheduler, LoadAwareMixin):
    """
    Scheduler que prioriza rendimiento máximo.
    
    Características:
    - Todos los procesadores a máxima frecuencia
    - Todos los procesadores siempre activos
    - Balanceo de carga agresivo para minimizar tiempo de ejecución
    - Migración cuando hay desbalance significativo
    """
    
    __slots__ = ('_migration_threshold', '_check_interval', '_steps_since_check')
    
    def __init__(self, config: dict):
        super().__init__(config, name="Performance-First")
        self._migration_threshold = config.get('migration_threshold', 0.3)
        self._check_interval = config.get('check_interval', 5)
        self._steps_since_check = 0
    
    def assign_tasks(self, tasks: List['Task']) -> List[tuple]:
        """Asigna tareas al procesador menos cargado."""
        if self._system is None:
            return []
        
        assignments = []
        # Obtener cargas actuales
        queue_lengths = self._system.get_queue_lengths().astype(np.float64)
        
        for task in tasks:
            # Encontrar procesador con menor cola
            proc_id = int(np.argmin(queue_lengths))
            assignments.append((task, proc_id))
            # Actualizar contador local para siguiente asignación
            queue_lengths[proc_id] += 1
        
        return assignments
    
    def adjust_frequencies(self):
        """Establece todas las frecuencias al máximo."""
        if self._system is None:
            return
        
        for i in range(self._system.n_processors):
            proc = self._system.get_processor(i)
            max_level = proc.energy_profile.frequency_steps - 1
            self._system.set_frequency_level(i, max_level)
    
    def check_migrations(self) -> List[tuple]:
        """Migra tareas si hay desbalance significativo."""
        if self._system is None:
            return []
        
        self._steps_since_check += 1
        if self._steps_since_check < self._check_interval:
            return []
        self._steps_since_check = 0
        
        migrations = []
        queue_lengths = self._system.get_queue_lengths()
        
        if len(queue_lengths) < 2:
            return []
        
        avg_load = np.mean(queue_lengths)
        if avg_load == 0:
            return []
        
        # Encontrar procesadores sobrecargados y subcargados
        threshold_high = avg_load * (1 + self._migration_threshold)
        threshold_low = avg_load * (1 - self._migration_threshold)
        
        overloaded = np.where(queue_lengths > threshold_high)[0]
        underloaded = np.where(queue_lengths < threshold_low)[0]
        
        # Migrar tareas de sobrecargados a subcargados
        for from_id in overloaded:
            if len(underloaded) == 0:
                break
            
            excess = int(queue_lengths[from_id] - avg_load)
            if excess > 0:
                to_id = underloaded[0]
                migrate_count = min(excess, 2)  # Máximo 2 tareas por migración
                migrations.append((int(from_id), int(to_id), migrate_count))
                underloaded = underloaded[1:]  # Rotar destinos
        
        return migrations
    
    def manage_power_states(self):
        """Mantiene todos los procesadores activos."""
        if self._system is None:
            return
        
        for i in range(self._system.n_processors):
            self._system.set_processor_sleep(i, False)
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            'strategy': 'max_performance',
            'migration_threshold': self._migration_threshold,
            'frequency_policy': 'always_max'
        })
        return stats