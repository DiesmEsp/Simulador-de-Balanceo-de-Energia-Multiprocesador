"""
Modelo de tareas/procesos para el simulador.
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
import numpy as np

class TaskState(IntEnum):
    """Estados posibles de una tarea."""
    WAITING = 0      # En cola, esperando asignación
    RUNNING = 1      # Ejecutándose
    IO_WAIT = 2      # Esperando I/O
    COMPLETED = 3    # Finalizada
    MIGRATING = 4    # En proceso de migración

class TaskType(IntEnum):
    """Tipos de tarea según su comportamiento."""
    CPU_BOUND = 0    # Uso intensivo de CPU
    IO_BOUND = 1     # Mucha espera de I/O
    MIXED = 2        # Comportamiento mixto


@dataclass(slots=True)
class Task:
    """Representa una tarea/proceso en el sistema."""
    id: int
    task_type: TaskType
    total_work: float           # Trabajo total requerido (unidades de CPU)
    cpu_intensity: float        # 0-1, qué tan intensivo es el CPU
    arrival_time: float         # Tiempo de llegada al sistema
    priority: int = 1           # Prioridad (mayor = más prioritario)
    
    # Estado mutable
    remaining_work: float = field(init=False)
    state: TaskState = field(default=TaskState.WAITING)
    assigned_processor: Optional[int] = field(default=None)
    start_time: Optional[float] = field(default=None)
    completion_time: Optional[float] = field(default=None)
    wait_time: float = field(default=0.0)
    io_wait_accumulated: float = field(default=0.0)
    migrations: int = field(default=0)
    
    def __post_init__(self):
        self.remaining_work = self.total_work
    
    def execute(self, dt: float, frequency: float, base_freq: float) -> float:
        """
        Ejecuta la tarea por un intervalo dt.
        Retorna el trabajo realizado.
        """
        if self.state != TaskState.RUNNING:
            return 0.0
        
        # Trabajo efectivo escala con frecuencia
        freq_factor = frequency / base_freq
        effective_work = dt * freq_factor * self.cpu_intensity
        
        actual_work = min(effective_work, self.remaining_work)
        self.remaining_work -= actual_work
        
        if self.remaining_work <= 0:
            self.state = TaskState.COMPLETED
        
        return actual_work
    
    def check_io_event(self, rng: np.random.Generator) -> bool:
        """Verifica si ocurre un evento de I/O (para tareas I/O-bound)."""
        if self.task_type == TaskType.CPU_BOUND:
            return False
        
        io_probability = 1.0 - self.cpu_intensity
        return rng.random() < io_probability * 0.1
    
    @property
    def is_complete(self) -> bool:
        return self.state == TaskState.COMPLETED
    
    @property
    def progress(self) -> float:
        """Porcentaje de completado."""
        return (self.total_work - self.remaining_work) / self.total_work


class TaskGenerator:
    """Generador de tareas optimizado."""
    
    __slots__ = ('_rng', '_task_counter', '_config')
    
    def __init__(self, config: dict, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._task_counter = 0
        self._config = config
    
    def generate_task(self, current_time: float, task_type: Optional[TaskType] = None) -> Task:
        """Genera una nueva tarea."""
        if task_type is None:
            task_type = self._rng.choice([TaskType.CPU_BOUND, TaskType.IO_BOUND, TaskType.MIXED])
        
        cfg = self._config.get(task_type.name.lower(), self._config.get('cpu_bound', {}))
        
        duration = self._rng.uniform(
            cfg.get('duration_min', 50),
            cfg.get('duration_max', 200)
        )
        intensity = cfg.get('cpu_intensity', 0.8)
        # Añadir variación
        intensity = np.clip(intensity + self._rng.normal(0, 0.1), 0.1, 1.0)
        
        task = Task(
            id=self._task_counter,
            task_type=task_type,
            total_work=duration,
            cpu_intensity=intensity,
            arrival_time=current_time,
            priority=self._rng.integers(1, 4)
        )
        self._task_counter += 1
        return task
    
    def generate_batch(self, current_time: float, count: int, 
                       task_type: Optional[TaskType] = None) -> list:
        """Genera un lote de tareas."""
        return [self.generate_task(current_time, task_type) for _ in range(count)]
    
    def generate_arrival_times(self, duration: float, rate: float) -> np.ndarray:
        """Genera tiempos de llegada usando proceso de Poisson."""
        if rate <= 0:
            return np.array([])
        
        n_expected = int(duration * rate * 1.5)  # Sobreestimar
        intervals = self._rng.exponential(1.0 / rate, n_expected)
        times = np.cumsum(intervals)
        return times[times < duration]