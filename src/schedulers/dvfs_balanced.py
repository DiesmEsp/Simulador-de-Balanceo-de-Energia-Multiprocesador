"""
Estrategia DVFS Balanceada: Equilibrio entre rendimiento y eficiencia energética.
Dynamic Voltage and Frequency Scaling adaptativo.
"""
from typing import List, TYPE_CHECKING
import numpy as np

from .base_scheduler import BaseScheduler
from ..core.processor import ProcessorState

if TYPE_CHECKING:
    from ..core.task import Task


class DVFSBalancedScheduler(BaseScheduler):
    """
    Scheduler con DVFS adaptativo.
    
    Características:
    - Ajusta frecuencia dinámicamente según carga
    - Balancea carga entre procesadores
    - Activa/desactiva procesadores según demanda
    - Migración inteligente considerando costo energético
    """
    
    __slots__ = (
        '_load_low', '_load_high', '_migration_cooldown', '_last_migration',
        '_frequency_history', '_ewma_alpha', '_sleep_threshold', '_wake_threshold'
    )
    
    def __init__(self, config: dict):
        super().__init__(config, name="DVFS-Balanced")
        self._load_low = config.get('load_low_threshold', 0.3)
        self._load_high = config.get('load_high_threshold', 0.7)
        self._migration_cooldown = config.get('migration_cooldown', 10)
        self._last_migration = -self._migration_cooldown
        self._ewma_alpha = config.get('ewma_alpha', 0.3)
        self._sleep_threshold = config.get('sleep_threshold', 0.05)
        self._wake_threshold = config.get('wake_threshold', 0.6)
        self._frequency_history: dict = {}
    
    def assign_tasks(self, tasks: List['Task']) -> List[tuple]:
        """Asigna tareas balanceando carga y considerando eficiencia."""
        if self._system is None:
            return []
        
        assignments = []
        n_procs = self._system.n_processors
        
        # Calcular scores para cada procesador
        scores = np.zeros(n_procs, dtype=np.float64)
        
        for i in range(n_procs):
            proc = self._system.get_processor(i)
            
            if proc.state == ProcessorState.SLEEP:
                # Penalizar despertar (pero no prohibir)
                scores[i] = -0.5
            else:
                # Score basado en capacidad disponible y eficiencia
                available_capacity = 1.0 - proc.load
                efficiency = 1.0 / (proc.current_power + 1)
                scores[i] = available_capacity * 0.7 + efficiency * 0.3
        
        for task in tasks:
            # Seleccionar mejor procesador
            best_id = int(np.argmax(scores))
            
            # Si el mejor está dormido, despertarlo
            if self._system.get_processor(best_id).state == ProcessorState.SLEEP:
                self._system.set_processor_sleep(best_id, False)
            
            assignments.append((task, best_id))
            # Actualizar score local
            scores[best_id] -= 0.15
        
        return assignments
    
    def adjust_frequencies(self):
        """Ajusta frecuencias dinámicamente usando DVFS."""
        if self._system is None:
            return
        
        for i in range(self._system.n_processors):
            proc = self._system.get_processor(i)
            
            if proc.state == ProcessorState.SLEEP:
                continue
            
            load = proc.load
            max_level = proc.energy_profile.frequency_steps - 1
            
            # Obtener nivel actual
            current_level = proc.current_frequency_level
            
            # EWMA de carga para suavizar cambios
            if i not in self._frequency_history:
                self._frequency_history[i] = load
            else:
                self._frequency_history[i] = (
                    self._ewma_alpha * load + 
                    (1 - self._ewma_alpha) * self._frequency_history[i]
                )
            
            smoothed_load = self._frequency_history[i]
            
            # Determinar nivel objetivo basado en carga
            if smoothed_load > self._load_high:
                # Alta carga: aumentar frecuencia
                target_level = min(current_level + 1, max_level)
            elif smoothed_load < self._load_low:
                # Baja carga: reducir frecuencia
                target_level = max(current_level - 1, 0)
            else:
                # Carga media: nivel proporcional
                normalized = (smoothed_load - self._load_low) / (self._load_high - self._load_low)
                target_level = int(normalized * max_level)
            
            # Aplicar cambio gradual
            if target_level != current_level:
                # Cambio de un nivel a la vez para evitar oscilaciones
                if target_level > current_level:
                    new_level = current_level + 1
                else:
                    new_level = current_level - 1
                
                self._system.set_frequency_level(i, new_level)
    
    def check_migrations(self) -> List[tuple]:
        """Migra tareas para balancear carga, considerando costo."""
        if self._system is None:
            return []
        
        current_time = self._system.current_time
        
        # Cooldown entre migraciones
        if current_time - self._last_migration < self._migration_cooldown:
            return []
        
        migrations = []
        n_procs = self._system.n_processors
        
        # Calcular cargas
        loads = self._system.get_loads()
        active_mask = np.array([
            self._system.get_processor(i).state != ProcessorState.SLEEP 
            for i in range(n_procs)
        ])
        
        active_loads = loads[active_mask]
        if len(active_loads) < 2:
            return []
        
        avg_load = np.mean(active_loads)
        std_load = np.std(active_loads)
        
        # Solo migrar si hay desbalance significativo
        if std_load < 0.15:
            return []
        
        # Encontrar origen (más cargado) y destino (menos cargado)
        active_indices = np.where(active_mask)[0]
        active_loads_list = [(i, loads[i]) for i in active_indices]
        active_loads_list.sort(key=lambda x: x[1], reverse=True)
        
        most_loaded_id, most_load = active_loads_list[0]
        least_loaded_id, least_load = active_loads_list[-1]
        
        # Verificar que valga la pena migrar
        load_diff = most_load - least_load
        if load_diff > 0.3 and most_load > self._load_high:
            # Calcular cuántas tareas migrar
            migrate_count = max(1, int(load_diff * 3))
            migrate_count = min(migrate_count, 
                               self._system.get_processor(most_loaded_id).queue_length)
            
            if migrate_count > 0:
                migrations.append((most_loaded_id, least_loaded_id, migrate_count))
                self._last_migration = current_time
        
        return migrations
    
    def manage_power_states(self):
        """Gestiona estados de energía adaptativamente."""
        if self._system is None:
            return
        
        n_procs = self._system.n_processors
        loads = self._system.get_loads()
        total_load = np.sum(loads)
        
        # Calcular procesadores necesarios
        needed_procs = max(1, int(np.ceil(total_load / self._load_high)))
        needed_procs = min(needed_procs, n_procs)
        
        # Contar activos actuales
        active_procs = []
        sleeping_procs = []
        
        for i in range(n_procs):
            proc = self._system.get_processor(i)
            if proc.state == ProcessorState.SLEEP:
                sleeping_procs.append(i)
            else:
                active_procs.append((i, proc.load))
        
        current_active = len(active_procs)
        
        # Despertar si necesitamos más
        if current_active < needed_procs and sleeping_procs:
            to_wake = min(needed_procs - current_active, len(sleeping_procs))
            for i in range(to_wake):
                self._system.set_processor_sleep(sleeping_procs[i], False)
        
        # Dormir si tenemos de más
        elif current_active > needed_procs:
            # Ordenar activos por carga
            active_procs.sort(key=lambda x: x[1])
            to_sleep = current_active - needed_procs
            
            for i in range(to_sleep):
                proc_id, load = active_procs[i]
                proc = self._system.get_processor(proc_id)
                
                # Solo dormir si realmente está ocioso
                if load < self._sleep_threshold and proc.queue_length == 0:
                    self._system.set_processor_sleep(proc_id, True)
    
    def get_stats(self) -> dict:
        stats = super().get_stats()
        stats.update({
            'strategy': 'dvfs_balanced',
            'load_thresholds': (self._load_low, self._load_high),
            'frequency_policy': 'adaptive',
            'migration_cooldown': self._migration_cooldown
        })
        return stats