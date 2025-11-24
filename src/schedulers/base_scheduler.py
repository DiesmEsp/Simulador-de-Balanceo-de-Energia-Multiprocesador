"""
Clase base abstracta para schedulers/estrategias de balanceo.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.multiprocessor import MultiprocessorSystem
    from ..core.task import Task


class BaseScheduler(ABC):
    """
    Clase base para todos los schedulers.
    Define la interfaz común que deben implementar todas las estrategias.
    """
    
    __slots__ = ('_config', '_name', '_system')
    
    def __init__(self, config: dict, name: str = "BaseScheduler"):
        self._config = config
        self._name = name
        self._system: Optional['MultiprocessorSystem'] = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def config(self) -> dict:
        return self._config
    
    def attach_system(self, system: 'MultiprocessorSystem'):
        """Vincula el scheduler a un sistema multiprocesador."""
        self._system = system
    
    @abstractmethod
    def assign_tasks(self, tasks: List['Task']) -> List[tuple]:
        """
        Decide a qué procesador asignar cada tarea.
        
        Args:
            tasks: Lista de tareas pendientes de asignar
            
        Returns:
            Lista de tuplas (task, processor_id)
        """
        pass
    
    @abstractmethod
    def adjust_frequencies(self):
        """
        Ajusta las frecuencias de los procesadores según la estrategia.
        """
        pass
    
    @abstractmethod
    def check_migrations(self) -> List[tuple]:
        """
        Verifica si se deben realizar migraciones.
        
        Returns:
            Lista de tuplas (from_proc_id, to_proc_id, task_count)
        """
        pass
    
    @abstractmethod
    def manage_power_states(self):
        """
        Gestiona estados de energía (sleep/active) de los procesadores.
        """
        pass
    
    def step(self, dt: float):
        """
        Ejecuta un paso del scheduler.
        Puede ser sobrescrito para lógica adicional.
        """
        if self._system is None:
            return
        
        # Asignar tareas pendientes
        pending = self._system.get_pending_tasks()
        if pending:
            assignments = self.assign_tasks(pending)
            for task, proc_id in assignments:
                self._system.assign_task_to_processor(task, proc_id)
        
        # Ajustar frecuencias
        self.adjust_frequencies()
        
        # Verificar migraciones
        migrations = self.check_migrations()
        for from_id, to_id, count in migrations:
            for _ in range(count):
                self._system.migrate_task(from_id, to_id)
        
        # Gestionar estados de energía
        self.manage_power_states()
    
    def get_stats(self) -> dict:
        """Retorna estadísticas específicas del scheduler."""
        return {
            'name': self._name,
            'config': self._config
        }


class RoundRobinMixin:
    """Mixin que provee asignación round-robin."""
    
    _rr_counter: int = 0
    
    def _round_robin_assign(self, n_processors: int) -> int:
        """Retorna el siguiente procesador en round-robin."""
        proc_id = self._rr_counter % n_processors
        self._rr_counter += 1
        return proc_id


class LoadAwareMixin:
    """Mixin que provee asignación basada en carga."""
    
    def _least_loaded_assign(self, system: 'MultiprocessorSystem') -> int:
        """Retorna el procesador con menor carga."""
        return system.find_least_loaded_processor()
    
    def _weighted_assign(self, system: 'MultiprocessorSystem', 
                         weights: List[float]) -> int:
        """Asigna basado en pesos (mayor peso = más probable)."""
        import numpy as np
        loads = system.get_loads()
        # Invertir: menor carga = mayor peso
        inv_loads = 1.0 - loads + 0.1  # +0.1 para evitar ceros
        combined = inv_loads * np.array(weights)
        combined /= combined.sum()
        return int(np.random.choice(len(combined), p=combined))