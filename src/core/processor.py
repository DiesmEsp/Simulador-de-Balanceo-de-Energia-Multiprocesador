"""
Modelo de procesador individual.
"""
from dataclasses import dataclass, field
from typing import Optional, Deque
from collections import deque
from enum import IntEnum
import numpy as np

from .task import Task, TaskState
from .energy_model import EnergyProfile


class ProcessorState(IntEnum):
    """Estados del procesador."""
    ACTIVE = 0       # Procesando tareas
    IDLE = 1         # Sin tareas, pero encendido
    SLEEP = 2        # Modo de bajo consumo


@dataclass
class ProcessorStats:
    """Estadísticas del procesador."""
    total_tasks_processed: int = 0
    total_work_done: float = 0.0
    time_active: float = 0.0
    time_idle: float = 0.0
    time_sleep: float = 0.0
    context_switches: int = 0
    
    @property
    def utilization(self) -> float:
        total = self.time_active + self.time_idle + self.time_sleep
        return self.time_active / total if total > 0 else 0.0


class Processor:
    """
    Representa un núcleo/procesador individual.
    Optimizado para alto rendimiento con __slots__.
    """
    
    __slots__ = (
        'id', 'energy_profile', 'state', 'current_frequency_level',
        '_task_queue', '_current_task', '_stats', '_max_queue_size',
        '_processor_type'
    )
    
    def __init__(self, proc_id: int, energy_profile: EnergyProfile, 
                 max_queue_size: int = 100, processor_type: str = "default"):
        self.id = proc_id
        self.energy_profile = energy_profile
        self.state = ProcessorState.IDLE
        self.current_frequency_level = energy_profile.frequency_steps - 1  # Max por defecto
        self._task_queue: Deque[Task] = deque(maxlen=max_queue_size)
        self._current_task: Optional[Task] = None
        self._stats = ProcessorStats()
        self._max_queue_size = max_queue_size
        self._processor_type = processor_type
    
    @property
    def current_frequency(self) -> float:
        return self.energy_profile.get_frequency_level(self.current_frequency_level)
    
    @property
    def current_power(self) -> float:
        if self.state == ProcessorState.SLEEP:
            return self.energy_profile.idle_power * 0.5
        elif self.state == ProcessorState.IDLE:
            return self.energy_profile.idle_power
        return self.energy_profile.get_power_at_level(self.current_frequency_level)
    
    @property
    def queue_length(self) -> int:
        return len(self._task_queue)
    
    @property
    def load(self) -> float:
        """Carga del procesador (0-1) basada en cola y tarea actual."""
        active_tasks = self.queue_length + (1 if self._current_task else 0)
        return min(active_tasks / max(self._max_queue_size * 0.5, 1), 1.0)
    
    @property
    def stats(self) -> ProcessorStats:
        return self._stats
    
    @property
    def current_task(self) -> Optional[Task]:
        return self._current_task
    
    @property
    def processor_type(self) -> str:
        return self._processor_type
    
    def set_frequency_level(self, level: int):
        """Establece nivel de frecuencia."""
        self.current_frequency_level = max(0, min(level, self.energy_profile.frequency_steps - 1))
    
    def add_task(self, task: Task) -> bool:
        """Añade tarea a la cola. Retorna False si la cola está llena."""
        if len(self._task_queue) >= self._max_queue_size:
            return False
        
        task.assigned_processor = self.id
        task.state = TaskState.WAITING
        self._task_queue.append(task)
        
        if self.state == ProcessorState.SLEEP:
            self.state = ProcessorState.IDLE
        
        return True
    
    def remove_task(self) -> Optional[Task]:
        """Remueve y retorna una tarea de la cola (para migración)."""
        if self._task_queue:
            task = self._task_queue.pop()
            task.assigned_processor = None
            return task
        return None
    
    def step(self, dt: float) -> Optional[Task]:
        """
        Avanza el procesador un paso de tiempo.
        Retorna la tarea si se completó.
        """
        completed = None
        
        # Si no hay tarea actual, tomar una de la cola
        if self._current_task is None and self._task_queue:
            self._current_task = self._task_queue.popleft()
            self._current_task.state = TaskState.RUNNING
            self._stats.context_switches += 1
        
        # Actualizar estado
        if self._current_task is not None:
            self.state = ProcessorState.ACTIVE
            
            # Ejecutar tarea
            work = self._current_task.execute(
                dt, 
                self.current_frequency,
                self.energy_profile.base_frequency
            )
            self._stats.total_work_done += work
            self._stats.time_active += dt
            
            # Verificar si completó
            if self._current_task.is_complete:
                completed = self._current_task
                self._stats.total_tasks_processed += 1
                self._current_task = None
        else:
            # Sin trabajo
            if self.state != ProcessorState.SLEEP:
                self.state = ProcessorState.IDLE
                self._stats.time_idle += dt
            else:
                self._stats.time_sleep += dt
        
        return completed
    
    def enter_sleep(self):
        """Pone el procesador en modo sleep."""
        if self._current_task is None and not self._task_queue:
            self.state = ProcessorState.SLEEP
    
    def wake_up(self):
        """Despierta el procesador del modo sleep."""
        if self.state == ProcessorState.SLEEP:
            self.state = ProcessorState.IDLE
    
    def get_queue_tasks(self) -> list:
        """Retorna lista de tareas en cola (sin removerlas)."""
        return list(self._task_queue)
    
    def get_estimated_completion_time(self) -> float:
        """Estima tiempo para completar todas las tareas en cola."""
        total_work = sum(t.remaining_work for t in self._task_queue)
        if self._current_task:
            total_work += self._current_task.remaining_work
        
        if total_work == 0:
            return 0.0
        
        # Trabajo por unidad de tiempo a frecuencia actual
        work_rate = self.current_frequency / self.energy_profile.base_frequency
        return total_work / work_rate