"""
Recolector y exportador de métricas.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
import json
import csv
from pathlib import Path


@dataclass
class MetricSnapshot:
    """Snapshot de métricas en un punto de tiempo."""
    time: float
    total_power: float
    power_per_proc: List[float]
    loads: List[float]
    frequencies: List[int]
    queue_lengths: List[int]
    active_processors: int
    tasks_in_system: int
    tasks_completed_total: int


class MetricsCollector:
    """
    Recolector de métricas optimizado.
    Almacena snapshots periódicos y calcula estadísticas.
    """
    
    __slots__ = ('_snapshots', '_interval', '_last_collect', '_summary_cache')
    
    def __init__(self, collect_interval: int = 10):
        self._snapshots: List[MetricSnapshot] = []
        self._interval = collect_interval
        self._last_collect = -collect_interval
        self._summary_cache: Optional[Dict] = None
    
    def should_collect(self, current_time: float) -> bool:
        """Verifica si debe recolectar en este tiempo."""
        return current_time - self._last_collect >= self._interval
    
    def collect(self, time: float, system: 'MultiprocessorSystem'):
        """Recolecta métricas del sistema."""
        from ..core.processor import ProcessorState
        
        self._last_collect = time
        self._summary_cache = None
        
        powers = system.get_instant_power()
        loads = system.get_loads()
        freqs = system.get_frequency_levels()
        queues = system.get_queue_lengths()
        
        active = sum(
            1 for i in range(system.n_processors)
            if system.get_processor(i).state != ProcessorState.SLEEP
        )
        
        snapshot = MetricSnapshot(
            time=time,
            total_power=float(np.sum(powers)),
            power_per_proc=powers.tolist(),
            loads=loads.tolist(),
            frequencies=freqs.tolist(),
            queue_lengths=queues.tolist(),
            active_processors=active,
            tasks_in_system=system.get_total_queue_length(),
            tasks_completed_total=len(system.completed_tasks)
        )
        
        self._snapshots.append(snapshot)
    
    def get_snapshots(self) -> List[MetricSnapshot]:
        """Retorna todos los snapshots."""
        return self._snapshots
    
    def get_summary(self) -> Dict[str, Any]:
        """Calcula resumen estadístico de todas las métricas."""
        if self._summary_cache is not None:
            return self._summary_cache
        
        if not self._snapshots:
            return {}
        
        # Extraer arrays
        powers = np.array([s.total_power for s in self._snapshots])
        tasks = np.array([s.tasks_in_system for s in self._snapshots])
        active = np.array([s.active_processors for s in self._snapshots])
        
        # Cargas por procesador a lo largo del tiempo
        n_procs = len(self._snapshots[0].loads)
        all_loads = np.array([s.loads for s in self._snapshots])
        
        summary = {
            'power': {
                'mean': float(np.mean(powers)),
                'std': float(np.std(powers)),
                'min': float(np.min(powers)),
                'max': float(np.max(powers)),
                'total_energy': float(np.sum(powers) * self._interval)
            },
            'tasks_in_system': {
                'mean': float(np.mean(tasks)),
                'max': float(np.max(tasks))
            },
            'active_processors': {
                'mean': float(np.mean(active)),
                'min': int(np.min(active)),
                'max': int(np.max(active))
            },
            'load_per_processor': {}
        }
        
        for i in range(n_procs):
            proc_loads = all_loads[:, i]
            summary['load_per_processor'][f'proc_{i}'] = {
                'mean': float(np.mean(proc_loads)),
                'std': float(np.std(proc_loads))
            }
        
        self._summary_cache = summary
        return summary
    
    def export_csv(self, filepath: str):
        """Exporta snapshots a CSV."""
        if not self._snapshots:
            return
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            n_procs = len(self._snapshots[0].loads)
            header = ['time', 'total_power', 'active_processors', 'tasks_in_system']
            header.extend([f'load_p{i}' for i in range(n_procs)])
            header.extend([f'power_p{i}' for i in range(n_procs)])
            header.extend([f'freq_p{i}' for i in range(n_procs)])
            writer.writerow(header)
            
            # Data
            for s in self._snapshots:
                row = [s.time, s.total_power, s.active_processors, s.tasks_in_system]
                row.extend(s.loads)
                row.extend(s.power_per_proc)
                row.extend(s.frequencies)
                writer.writerow(row)
    
    def export_json(self, filepath: str):
        """Exporta snapshots y resumen a JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'summary': self.get_summary(),
            'snapshots': [asdict(s) for s in self._snapshots]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear(self):
        """Limpia todos los snapshots."""
        self._snapshots.clear()
        self._summary_cache = None


class ResultsExporter:
    """Exportador de resultados de simulación."""
    
    @staticmethod
    def export_results(results: 'SimulationResults', filepath: str, format: str = 'json'):
        """Exporta resultados a archivo."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir a diccionario serializable
        data = {
            'makespan': results.makespan,
            'avg_response_time': results.avg_response_time,
            'avg_wait_time': results.avg_wait_time,
            'total_energy': results.total_energy,
            'energy_per_processor': results.energy_per_processor.tolist(),
            'avg_power': results.avg_power,
            'energy_efficiency': results.energy_efficiency,
            'throughput': results.throughput,
            'load_balance_score': results.load_balance_score,
            'utilization_avg': results.utilization_avg,
            'utilization_std': results.utilization_std,
            'total_tasks': results.total_tasks,
            'completed_tasks': results.completed_tasks,
            'total_migrations': results.total_migrations
        }
        
        if format == 'json':
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == 'csv':
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(data.keys())
                writer.writerow(data.values())
    
    @staticmethod
    def export_comparison(results_dict: Dict[str, 'SimulationResults'], 
                         filepath: str):
        """Exporta comparación de múltiples resultados."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        metrics = [
            'makespan', 'total_energy', 'energy_efficiency',
            'throughput', 'load_balance_score', 'utilization_avg',
            'completed_tasks', 'total_migrations'
        ]
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['strategy'] + metrics)
            
            for strategy, results in results_dict.items():
                row = [strategy]
                for m in metrics:
                    row.append(getattr(results, m, 0))
                writer.writerow(row)