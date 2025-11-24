"""
Motor principal de simulación.
Coordina todos los componentes del simulador.
"""
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
import numpy as np
import time

from ..core.multiprocessor import MultiprocessorSystem
from ..core.task import Task, TaskGenerator, TaskType
from ..schedulers import BaseScheduler, get_scheduler


@dataclass
class SimulationConfig:
    """Configuración de la simulación."""
    duration: float = 1000.0
    time_step: float = 1.0
    random_seed: int = 42
    
    # Procesadores
    n_processors: int = 8
    heterogeneous: bool = False
    processor_config: dict = field(default_factory=dict)
    
    # Tareas
    task_mode: str = "mixed"  # cpu_bound, io_bound, mixed, burst
    arrival_rate: float = 0.5
    total_tasks: int = 100
    task_config: dict = field(default_factory=dict)
    
    # Estrategia
    strategy: str = "dvfs"
    strategy_config: dict = field(default_factory=dict)
    
    # Escenario especial
    scenario: Optional[str] = None
    burst_times: List[float] = field(default_factory=list)
    burst_size: int = 10


@dataclass 
class SimulationResults:
    """Resultados de la simulación."""
    # Tiempos
    makespan: float = 0.0
    avg_response_time: float = 0.0
    avg_wait_time: float = 0.0
    
    # Energía
    total_energy: float = 0.0
    energy_per_processor: np.ndarray = field(default_factory=lambda: np.array([]))
    avg_power: float = 0.0
    
    # Eficiencia
    energy_efficiency: float = 0.0  # tareas/energía
    throughput: float = 0.0  # tareas/tiempo
    
    # Balance
    load_balance_score: float = 0.0  # 0-1, 1 = perfecto balance
    utilization_avg: float = 0.0
    utilization_std: float = 0.0
    
    # Contadores
    total_tasks: int = 0
    completed_tasks: int = 0
    total_migrations: int = 0
    
    # Históricos
    time_history: List[float] = field(default_factory=list)
    power_history: List[float] = field(default_factory=list)
    load_history: List[np.ndarray] = field(default_factory=list)
    queue_history: List[int] = field(default_factory=list)


class SimulationEngine:
    """
    Motor de simulación optimizado para alto rendimiento.
    """
    
    __slots__ = (
        '_config', '_system', '_scheduler', '_task_gen', '_rng',
        '_current_time', '_results', '_arrival_times', '_arrival_idx',
        '_callbacks', '_running', '_burst_times_set'
    )
    
    def __init__(self, config: SimulationConfig):
        self._config = config
        self._rng = np.random.default_rng(config.random_seed)
        self._current_time = 0.0
        self._results = SimulationResults()
        self._callbacks: Dict[str, List[Callable]] = {
            'on_step': [],
            'on_task_complete': [],
            'on_task_arrive': [],
            'on_finish': []
        }
        self._running = False
        self._arrival_idx = 0
        
        # Inicializar componentes
        self._init_system()
        self._init_scheduler()
        self._init_task_generator()
    
    def _init_system(self):
        """Inicializa el sistema multiprocesador."""
        cfg = self._config
        
        if cfg.heterogeneous:
            # Configuración heterogénea
            configs = self._build_heterogeneous_configs()
        else:
            # Configuración homogénea
            default_proc = {
                'base_frequency': 1.0,
                'max_frequency': 3.5,
                'frequency_steps': 5,
                'base_power': 5.0,
                'max_power': 95.0,
                'idle_power': 2.0,
                'type': 'default'
            }
            default_proc.update(cfg.processor_config)
            configs = [default_proc.copy() for _ in range(cfg.n_processors)]
        
        self._system = MultiprocessorSystem(configs, cfg.heterogeneous)
    
    def _build_heterogeneous_configs(self) -> List[dict]:
        """Construye configuración para sistema heterogéneo."""
        configs = []
        n = self._config.n_processors
        
        # 30% performance cores, 70% efficiency cores
        n_performance = max(1, int(n * 0.3))
        n_efficiency = n - n_performance
        
        perf_config = {
            'base_frequency': 1.5, 'max_frequency': 4.0,
            'frequency_steps': 5, 'base_power': 10.0,
            'max_power': 125.0, 'idle_power': 5.0,
            'type': 'performance'
        }
        
        eff_config = {
            'base_frequency': 0.8, 'max_frequency': 2.5,
            'frequency_steps': 4, 'base_power': 3.0,
            'max_power': 45.0, 'idle_power': 1.0,
            'type': 'efficiency'
        }
        
        for _ in range(n_performance):
            configs.append(perf_config.copy())
        for _ in range(n_efficiency):
            configs.append(eff_config.copy())
        
        return configs
    
    def _init_scheduler(self):
        """Inicializa el scheduler."""
        self._scheduler = get_scheduler(
            self._config.strategy,
            self._config.strategy_config
        )
        self._scheduler.attach_system(self._system)
    
    def _init_task_generator(self):
        """Inicializa el generador de tareas."""
        task_config = {
            'cpu_bound': {
                'duration_min': 50, 'duration_max': 200,
                'cpu_intensity': 0.95
            },
            'io_bound': {
                'duration_min': 30, 'duration_max': 150,
                'cpu_intensity': 0.3
            },
            'mixed': {
                'duration_min': 40, 'duration_max': 180,
                'cpu_intensity': 0.6
            }
        }
        task_config.update(self._config.task_config)
        
        self._task_gen = TaskGenerator(task_config, self._config.random_seed)
        
        # Generar tiempos de llegada
        self._arrival_times = self._task_gen.generate_arrival_times(
            self._config.duration,
            self._config.arrival_rate
        )
        
        # Limitar al total de tareas configurado
        if len(self._arrival_times) > self._config.total_tasks:
            self._arrival_times = self._arrival_times[:self._config.total_tasks]
        
        # Configurar bursts
        self._burst_times_set = set(self._config.burst_times)
    
    @property
    def system(self) -> MultiprocessorSystem:
        return self._system
    
    @property
    def scheduler(self) -> BaseScheduler:
        return self._scheduler
    
    @property
    def results(self) -> SimulationResults:
        return self._results
    
    @property
    def current_time(self) -> float:
        return self._current_time
    
    def register_callback(self, event: str, callback: Callable):
        """Registra un callback para un evento."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _emit_event(self, event: str, *args, **kwargs):
        """Emite un evento a los callbacks registrados."""
        for cb in self._callbacks.get(event, []):
            cb(*args, **kwargs)
    
    def _get_task_type(self) -> TaskType:
        """Determina tipo de tarea según modo."""
        mode = self._config.task_mode.lower()
        
        if mode == 'cpu_bound':
            return TaskType.CPU_BOUND
        elif mode == 'io_bound':
            return TaskType.IO_BOUND
        else:  # mixed
            r = self._rng.random()
            if r < 0.4:
                return TaskType.CPU_BOUND
            elif r < 0.7:
                return TaskType.IO_BOUND
            return TaskType.MIXED
    
    def _process_arrivals(self):
        """Procesa llegadas de tareas en el tiempo actual."""
        # Llegadas normales
        while (self._arrival_idx < len(self._arrival_times) and 
               self._arrival_times[self._arrival_idx] <= self._current_time):
            
            task_type = self._get_task_type()
            task = self._task_gen.generate_task(self._current_time, task_type)
            self._system.add_task(task)
            self._results.total_tasks += 1
            self._emit_event('on_task_arrive', task)
            self._arrival_idx += 1
        
        # Bursts programados
        for burst_time in list(self._burst_times_set):
            if self._current_time >= burst_time:
                tasks = self._task_gen.generate_batch(
                    self._current_time,
                    self._config.burst_size,
                    TaskType.CPU_BOUND
                )
                self._system.add_tasks(tasks)
                self._results.total_tasks += len(tasks)
                self._burst_times_set.remove(burst_time)
                for t in tasks:
                    self._emit_event('on_task_arrive', t)
    
    def step(self) -> bool:
        """
        Ejecuta un paso de simulación.
        Retorna True si la simulación debe continuar.
        """
        dt = self._config.time_step
        
        # Procesar llegadas
        self._process_arrivals()
        
        # Ejecutar scheduler
        self._scheduler.step(dt)
        
        # Avanzar sistema
        completed = self._system.step(dt)
        
        # Procesar completadas
        for task in completed:
            self._results.completed_tasks += 1
            self._results.total_migrations += task.migrations
            self._emit_event('on_task_complete', task)
        
        # Registrar históricos
        self._results.time_history.append(self._current_time)
        self._results.power_history.append(float(np.sum(self._system.get_instant_power())))
        self._results.load_history.append(self._system.get_loads().copy())
        self._results.queue_history.append(self._system.get_total_queue_length())
        
        self._current_time += dt
        
        # Verificar fin
        all_done = (
            self._arrival_idx >= len(self._arrival_times) and
            len(self._burst_times_set) == 0 and
            self._system.get_total_queue_length() == 0
        )
        time_exceeded = self._current_time >= self._config.duration
        
        return not (all_done or time_exceeded)
    
    def run(self, progress_callback: Optional[Callable[[float], None]] = None) -> SimulationResults:
        """
        Ejecuta la simulación completa.
        
        Args:
            progress_callback: Función llamada con progreso 0-1
        """
        self._running = True
        start_real_time = time.perf_counter()
        
        total_steps = int(self._config.duration / self._config.time_step)
        step_count = 0
        
        while self._running and self.step():
            step_count += 1
            if progress_callback and step_count % 100 == 0:
                progress_callback(self._current_time / self._config.duration)
        
        real_elapsed = time.perf_counter() - start_real_time
        
        # Calcular resultados finales
        self._compute_final_results()
        
        self._emit_event('on_finish', self._results)
        self._running = False
        
        return self._results
    
    def stop(self):
        """Detiene la simulación."""
        self._running = False
    
    def _compute_final_results(self):
        """Calcula métricas finales."""
        completed = self._system.completed_tasks
        r = self._results
        
        # Makespan
        if completed:
            r.makespan = max(t.completion_time for t in completed)
            
            # Tiempos promedio
            response_times = [
                t.completion_time - t.arrival_time for t in completed
            ]
            r.avg_response_time = np.mean(response_times)
            r.avg_wait_time = np.mean([t.wait_time for t in completed])
        
        # Energía
        r.total_energy = self._system.get_total_energy()
        r.energy_per_processor = self._system.get_energy_per_processor()
        
        if r.time_history:
            r.avg_power = np.mean(r.power_history)
        
        # Eficiencia
        if r.total_energy > 0:
            r.energy_efficiency = r.completed_tasks / r.total_energy
        if r.makespan > 0:
            r.throughput = r.completed_tasks / r.makespan
        
        # Utilización
        util_stats = self._system.get_utilization_stats()
        r.utilization_avg = util_stats['average']
        r.utilization_std = util_stats['std_dev']
        
        # Balance de carga
        if r.utilization_avg > 0:
            r.load_balance_score = 1.0 - min(r.utilization_std / r.utilization_avg, 1.0)
        else:
            r.load_balance_score = 1.0