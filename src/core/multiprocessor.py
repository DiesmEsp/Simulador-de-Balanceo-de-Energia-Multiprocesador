"""
Sistema multiprocesador que coordina múltiples núcleos.
"""
from typing import List, Optional, Tuple
import numpy as np

from .processor import Processor, ProcessorState
from .task import Task
from .energy_model import EnergyProfile, EnergyCalculator


class MultiprocessorSystem:
    """
    Sistema multiprocesador con gestión centralizada.
    Diseñado para alta eficiencia con muchos procesadores.
    """
    
    __slots__ = (
        '_processors', '_energy_calc', '_n_procs', '_completed_tasks',
        '_pending_tasks', '_current_time', '_heterogeneous'
    )
    
    def __init__(self, configs: List[dict], heterogeneous: bool = False):
        """
        Inicializa el sistema multiprocesador.
        
        Args:
            configs: Lista de configuraciones por procesador
            heterogeneous: Si el sistema tiene procesadores heterogéneos
        """
        self._heterogeneous = heterogeneous
        self._processors: List[Processor] = []
        profiles: List[EnergyProfile] = []
        
        for i, cfg in enumerate(configs):
            profile = EnergyProfile(
                base_frequency=cfg.get('base_frequency', 1.0),
                max_frequency=cfg.get('max_frequency', 3.5),
                frequency_steps=cfg.get('frequency_steps', 5),
                base_power=cfg.get('base_power', 5.0),
                max_power=cfg.get('max_power', 95.0),
                idle_power=cfg.get('idle_power', 2.0)
            )
            profiles.append(profile)
            
            proc = Processor(
                proc_id=i,
                energy_profile=profile,
                processor_type=cfg.get('type', 'default')
            )
            self._processors.append(proc)
        
        self._n_procs = len(self._processors)
        self._energy_calc = EnergyCalculator(profiles)
        self._completed_tasks: List[Task] = []
        self._pending_tasks: List[Task] = []
        self._current_time = 0.0
    
    @property
    def processors(self) -> List[Processor]:
        return self._processors
    
    @property
    def n_processors(self) -> int:
        return self._n_procs
    
    @property
    def completed_tasks(self) -> List[Task]:
        return self._completed_tasks
    
    @property
    def current_time(self) -> float:
        return self._current_time
    
    @property
    def is_heterogeneous(self) -> bool:
        return self._heterogeneous
    
    def get_processor(self, proc_id: int) -> Processor:
        return self._processors[proc_id]
    
    def get_loads(self) -> np.ndarray:
        """Retorna array de cargas de todos los procesadores."""
        return np.array([p.load for p in self._processors], dtype=np.float64)
    
    def get_queue_lengths(self) -> np.ndarray:
        """Retorna longitudes de cola de todos los procesadores."""
        return np.array([p.queue_length for p in self._processors], dtype=np.int32)
    
    def get_frequency_levels(self) -> np.ndarray:
        """Retorna niveles de frecuencia actuales."""
        return np.array([p.current_frequency_level for p in self._processors], dtype=np.int32)
    
    def get_states(self) -> np.ndarray:
        """Retorna estados de todos los procesadores."""
        return np.array([p.state for p in self._processors], dtype=np.int32)
    
    def add_task(self, task: Task, proc_id: Optional[int] = None) -> bool:
        """
        Añade una tarea al sistema.
        Si proc_id es None, la tarea queda pendiente para asignación.
        """
        if proc_id is not None:
            return self._processors[proc_id].add_task(task)
        
        self._pending_tasks.append(task)
        return True
    
    def add_tasks(self, tasks: List[Task]):
        """Añade múltiples tareas pendientes."""
        self._pending_tasks.extend(tasks)
    
    def get_pending_tasks(self) -> List[Task]:
        """Retorna y limpia la lista de tareas pendientes."""
        tasks = self._pending_tasks
        self._pending_tasks = []
        return tasks
    
    def assign_task_to_processor(self, task: Task, proc_id: int) -> bool:
        """Asigna una tarea específica a un procesador."""
        return self._processors[proc_id].add_task(task)
    
    def migrate_task(self, from_proc: int, to_proc: int) -> bool:
        """Migra una tarea entre procesadores."""
        task = self._processors[from_proc].remove_task()
        if task is None:
            return False
        
        task.migrations += 1
        return self._processors[to_proc].add_task(task)
    
    def set_frequency_level(self, proc_id: int, level: int):
        """Establece nivel de frecuencia de un procesador."""
        self._processors[proc_id].set_frequency_level(level)
        self._energy_calc.set_frequency_level(proc_id, level)
    
    def set_processor_sleep(self, proc_id: int, sleep: bool):
        """Pone o saca un procesador de modo sleep."""
        proc = self._processors[proc_id]
        if sleep:
            proc.enter_sleep()
        else:
            proc.wake_up()
        self._energy_calc.set_active(proc_id, not sleep)
    
    def step(self, dt: float) -> List[Task]:
        """
        Avanza la simulación un paso de tiempo.
        Retorna lista de tareas completadas en este paso.
        """
        self._current_time += dt
        completed = []
        
        # Ejecutar cada procesador
        for proc in self._processors:
            task = proc.step(dt)
            if task is not None:
                task.completion_time = self._current_time
                completed.append(task)
                self._completed_tasks.append(task)
        
        # Acumular energía
        loads = self.get_loads()
        self._energy_calc.accumulate_energy(dt, loads)
        
        return completed
    
    def get_total_energy(self) -> float:
        """Retorna energía total consumida."""
        return self._energy_calc.get_total_energy()
    
    def get_energy_per_processor(self) -> np.ndarray:
        """Retorna energía por procesador."""
        return self._energy_calc.get_energy_per_processor()
    
    def get_instant_power(self) -> np.ndarray:
        """Retorna potencia instantánea por procesador."""
        return self._energy_calc.calculate_instant_power()
    
    def get_total_queue_length(self) -> int:
        """Retorna suma de todas las colas más tareas activas."""
        total = len(self._pending_tasks)
        for proc in self._processors:
            total += proc.queue_length
            if proc.current_task is not None:
                total += 1
        return total
    
    def get_utilization_stats(self) -> dict:
        """Retorna estadísticas de utilización."""
        stats = {
            'per_processor': [],
            'average': 0.0,
            'std_dev': 0.0,
            'min': 0.0,
            'max': 0.0
        }
        
        utilizations = []
        for proc in self._processors:
            u = proc.stats.utilization
            utilizations.append(u)
            stats['per_processor'].append({
                'id': proc.id,
                'utilization': u,
                'tasks_processed': proc.stats.total_tasks_processed,
                'context_switches': proc.stats.context_switches
            })
        
        utilizations = np.array(utilizations)
        stats['average'] = float(np.mean(utilizations))
        stats['std_dev'] = float(np.std(utilizations))
        stats['min'] = float(np.min(utilizations))
        stats['max'] = float(np.max(utilizations))
        
        return stats
    
    def find_least_loaded_processor(self) -> int:
        """Encuentra el procesador con menor carga."""
        loads = self.get_loads()
        # Excluir procesadores en sleep
        for i, proc in enumerate(self._processors):
            if proc.state == ProcessorState.SLEEP:
                loads[i] = float('inf')
        return int(np.argmin(loads))
    
    def find_most_loaded_processor(self) -> int:
        """Encuentra el procesador con mayor carga."""
        return int(np.argmax(self.get_loads()))
    
    def get_load_imbalance(self) -> float:
        """Retorna medida de desbalance de carga (0 = perfectamente balanceado)."""
        loads = self.get_loads()
        if np.max(loads) == 0:
            return 0.0
        return float(np.std(loads) / np.mean(loads)) if np.mean(loads) > 0 else 0.0