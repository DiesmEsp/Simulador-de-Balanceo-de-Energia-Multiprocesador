"""
Estrategia Energy-First: Prioriza ahorro de energía sobre rendimiento.
"""
from typing import List, TYPE_CHECKING
import numpy as np

from .base_scheduler import BaseScheduler
from ..core.processor import ProcessorState

if TYPE_CHECKING:
    from ..core.task import Task


class EnergyFirstScheduler(BaseScheduler):
    """
    Scheduler que prioriza eficiencia energética.
    
    Características:
    - Frecuencias lo más bajas posible
    - Consolida tareas en menos procesadores
    - Pone procesadores ociosos en sleep
    - Evita migraciones (consumen energía)
    """
    
    __slots__ = (
        '_idle_threshold', '_consolidation_threshold', '_min_active_procs',
        '_frequency_level', '_wake_threshold'
    )
    
    def __init__(self, config: dict):
        super().__init__(config, name="Energy-First")
        self._idle_threshold = config.get('idle_threshold', 0.1)
        self._consolidation_threshold = config.get('consolidation_threshold', 0.7)
        self._min_active_procs = config.get('min_active_processors', 1)
        self._frequency_level = config.get('preferred_frequency_level', 1)  # Bajo
        self._wake_threshold = config.get('wake_threshold', 0.8)
    
    def assign_tasks(self, tasks: List['Task']) -> List[tuple]:
        """Asigna tareas consolidando en menos procesadores."""
        if self._system is None:
            return []
        
        assignments = []
        n_procs = self._system.n_processors
        
        # Obtener procesadores activos ordenados por carga
        active_procs = []
        for i in range(n_procs):
            proc = self._system.get_processor(i)
            if proc.state != ProcessorState.SLEEP:
                active_procs.append((i, proc.load, proc.queue_length))
        
        # Ordenar por carga (llenar los que ya tienen trabajo primero)
        active_procs.sort(key=lambda x: -x[1])
        
        sleeping_procs = [
            i for i in range(n_procs) 
            if self._system.get_processor(i).state == ProcessorState.SLEEP
        ]
        
        for task in tasks:
            assigned = False
            
            # Intentar asignar a procesadores activos sin sobrecargar
            for proc_id, load, queue_len in active_procs:
                if load < self._consolidation_threshold:
                    assignments.append((task, proc_id))
                    assigned = True
                    # Actualizar carga local
                    idx = next(j for j, (p, _, _) in enumerate(active_procs) if p == proc_id)
                    active_procs[idx] = (proc_id, load + 0.1, queue_len + 1)
                    break
            
            # Si todos están muy cargados, despertar uno
            if not assigned:
                if sleeping_procs:
                    wake_id = sleeping_procs.pop(0)
                    self._system.set_processor_sleep(wake_id, False)
                    assignments.append((task, wake_id))
                    active_procs.append((wake_id, 0.1, 1))
                else:
                    # Asignar al menos cargado si no hay sleeping
                    proc_id = min(active_procs, key=lambda x: x[1])[0]
                    assignments.append((task, proc_id))
        
        return assignments
    
    def adjust_frequencies(self):
        """Mantiene frecuencias bajas, aumenta solo si hay mucha carga."""
        if self._system is None:
            return
        
        for i in range(self._system.n_processors):
            proc = self._system.get_processor(i)
            
            if proc.state == ProcessorState.SLEEP:
                continue
            
            load = proc.load
            max_level = proc.energy_profile.frequency_steps - 1
            
            if load > 0.8:
                # Alta carga: subir un poco
                level = min(self._frequency_level + 2, max_level)
            elif load > 0.5:
                # Carga media: nivel intermedio bajo
                level = min(self._frequency_level + 1, max_level)
            else:
                # Carga baja: frecuencia mínima
                level = self._frequency_level
            
            self._system.set_frequency_level(i, level)
    
    def check_migrations(self) -> List[tuple]:
        """Migra solo para consolidar (reducir procesadores activos)."""
        if self._system is None:
            return []
        
        migrations = []
        n_procs = self._system.n_processors
        
        # Encontrar procesadores con muy poca carga
        light_procs = []
        for i in range(n_procs):
            proc = self._system.get_processor(i)
            if proc.state != ProcessorState.SLEEP and proc.load < self._idle_threshold:
                if proc.queue_length > 0:
                    light_procs.append((i, proc.queue_length))
        
        # Consolidar tareas de procesadores ligeros
        for from_id, queue_len in light_procs:
            # Buscar destino con espacio
            for to_id in range(n_procs):
                if to_id == from_id:
                    continue
                to_proc = self._system.get_processor(to_id)
                if to_proc.state != ProcessorState.SLEEP:
                    if to_proc.load < self._consolidation_threshold:
                        migrations.append((from_id, to_id, queue_len))
                        break
        
        return migrations
    
    def manage_power_states(self):
        """Pone en sleep procesadores ociosos."""
        if self._system is None:
            return
        
        n_procs = self._system.n_processors
        active_count = sum(
            1 for i in range(n_procs) 
            if self._system.get_processor(i).state != ProcessorState.SLEEP
        )
        
        for i in range(n_procs):
            proc = self._system.get_processor(i)
            
            # No dormir si ya está dormido o tiene trabajo
            if proc.state == ProcessorState.SLEEP:
                continue
            
            if proc.current_task is not None or proc.queue_length > 0:
                continue
            
            # Mantener mínimo de procesadores activos
            if active_count <= self._min_active_procs:
                continue
            
            # Poner en sleep si está ocioso
            if proc.load < self._idle_threshold:
                self._system.set_processor_sleep(i, True)
                active_count -= 1
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            'strategy': 'energy_efficient',
            'idle_threshold': self._idle_threshold,
            'consolidation_threshold': self._consolidation_threshold,
            'frequency_policy': 'prefer_low'
        })
        return stats