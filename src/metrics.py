"""
Módulo para cálculo de métricas de rendimiento y energía.
"""

import numpy as np


class MetricsCalculator:
    """
    Calcula métricas de rendimiento, energía y balance de carga.
    """
    
    def __init__(self):
        """Inicializa el calculador de métricas."""
        self.history = []
    
    def calculate_makespan(self, processors):
        """
        Calcula el makespan (tiempo total de ejecución).
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            float: Tiempo máximo de ejecución
        """
        if not processors:
            return 0.0
        return max(p.execution_time for p in processors)
    
    def calculate_total_energy(self, processors):
        """
        Calcula la energía total consumida.
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            float: Energía total en Joules
        """
        return sum(p.energy_consumed for p in processors)
    
    def calculate_energy_efficiency(self, processors, tasks_completed):
        """
        Calcula la eficiencia energética.
        
        Args:
            processors (list): Lista de procesadores
            tasks_completed (int): Número de tareas completadas
            
        Returns:
            float: Tareas completadas por Joule
        """
        total_energy = self.calculate_total_energy(processors)
        if total_energy == 0:
            return 0.0
        return tasks_completed / total_energy
    
    def calculate_load_balance(self, task_counts):
        """
        Calcula el balance de carga usando desviación estándar.
        
        Args:
            task_counts (list): Número de tareas por procesador
            
        Returns:
            float: Desviación estándar (menor es mejor balance)
        """
        if not task_counts:
            return 0.0
        return np.std(task_counts)
    
    def calculate_average_utilization(self, processors):
        """
        Calcula la utilización promedio de procesadores.
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            float: Porcentaje de utilización promedio
        """
        if not processors:
            return 0.0
        return sum(p.get_utilization() for p in processors) / len(processors)
    
    def calculate_throughput(self, tasks_completed, total_time):
        """
        Calcula el throughput (tareas por unidad de tiempo).
        
        Args:
            tasks_completed (int): Tareas completadas
            total_time (float): Tiempo total
            
        Returns:
            float: Tareas por unidad de tiempo
        """
        if total_time == 0:
            return 0.0
        return tasks_completed / total_time
    
    def calculate_speedup(self, sequential_time, parallel_time):
        """
        Calcula el speedup comparado con ejecución secuencial.
        
        Args:
            sequential_time (float): Tiempo secuencial teórico
            parallel_time (float): Tiempo paralelo real
            
        Returns:
            float: Factor de speedup
        """
        if parallel_time == 0:
            return 0.0
        return sequential_time / parallel_time
    
    def calculate_efficiency_percentage(self, speedup, num_processors):
        """
        Calcula la eficiencia de paralelización.
        
        Args:
            speedup (float): Factor de speedup
            num_processors (int): Número de procesadores
            
        Returns:
            float: Porcentaje de eficiencia (0-100)
        """
        if num_processors == 0:
            return 0.0
        return (speedup / num_processors) * 100
    
    def calculate_power_consumption_profile(self, processors):
        """
        Calcula el perfil de consumo de energía.
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            dict: Estadísticas de consumo
        """
        energies = [p.energy_consumed for p in processors]
        
        return {
            'total': sum(energies),
            'mean': np.mean(energies),
            'std': np.std(energies),
            'min': min(energies),
            'max': max(energies),
            'variance': np.var(energies)
        }
    
    def calculate_load_distribution(self, processors):
        """
        Calcula la distribución de carga.
        
        Args:
            processors (list): Lista de procesadores
            
        Returns:
            dict: Estadísticas de distribución
        """
        loads = [p.load for p in processors]
        completed = [p.completed_tasks for p in processors]
        
        return {
            'current_loads': loads,
            'avg_load': np.mean(loads),
            'max_load': max(loads),
            'min_load': min(loads),
            'load_std': np.std(loads),
            'completed_tasks': completed,
            'completed_std': np.std(completed)
        }
    
    def calculate_processor_efficiency(self, processor):
        """
        Calcula métricas de eficiencia de un procesador individual.
        
        Args:
            processor: Procesador a analizar
            
        Returns:
            dict: Métricas del procesador
        """
        utilization = processor.get_utilization()
        energy_per_task = (processor.energy_consumed / processor.completed_tasks 
                          if processor.completed_tasks > 0 else 0)
        
        return {
            'processor_id': processor.processor_id,
            'utilization': utilization,
            'efficiency': processor.get_efficiency(),
            'energy_per_task': energy_per_task,
            'completed_tasks': processor.completed_tasks,
            'idle_time': processor.idle_time,
            'idle_percentage': (processor.idle_time / processor.execution_time * 100
                               if processor.execution_time > 0 else 0)
        }
    
    def calculate_strategy_performance(self, results):
        """
        Calcula métricas de desempeño de la estrategia.
        
        Args:
            results (dict): Resultados de la simulación
            
        Returns:
            dict: Métricas de la estrategia
        """
        return {
            'strategy': results.get('strategy', 'unknown'),
            'makespan': results.get('makespan', 0),
            'total_energy': results.get('total_energy', 0),
            'efficiency': results.get('efficiency', 0),
            'load_balance': results.get('load_balance_std', 0),
            'utilization': results.get('avg_utilization', 0)
        }
    
    def compare_strategies(self, results_list):
        """
        Compara resultados de múltiples estrategias.
        
        Args:
            results_list (list): Lista de resultados de diferentes estrategias
            
        Returns:
            dict: Comparación de estrategias
        """
        comparison = {}
        
        for results in results_list:
            strategy = results.get('strategy', 'unknown')
            comparison[strategy] = {
                'makespan': results.get('makespan', 0),
                'energy': results.get('total_energy', 0),
                'efficiency': results.get('efficiency', 0),
                'balance': results.get('load_balance_std', 0)
            }
        
        # Encontrar mejor en cada métrica
        best = {
            'makespan': min(comparison.items(), key=lambda x: x[1]['makespan']),
            'energy': min(comparison.items(), key=lambda x: x[1]['energy']),
            'efficiency': max(comparison.items(), key=lambda x: x[1]['efficiency']),
            'balance': min(comparison.items(), key=lambda x: x[1]['balance'])
        }
        
        return {
            'comparison': comparison,
            'best_strategies': best
        }
    
    def generate_summary(self, processors, total_time, tasks_completed, total_tasks):
        """
        Genera un resumen completo de métricas.
        
        Args:
            processors (list): Lista de procesadores
            total_time (float): Tiempo total
            tasks_completed (int): Tareas completadas
            total_tasks (int): Total de tareas
            
        Returns:
            dict: Resumen completo
        """
        return {
            'execution': {
                'makespan': self.calculate_makespan(processors),
                'tasks_completed': tasks_completed,
                'total_tasks': total_tasks,
                'completion_rate': (tasks_completed / total_tasks * 100
                                   if total_tasks > 0 else 0),
                'throughput': self.calculate_throughput(tasks_completed, total_time)
            },
            'energy': {
                'total_consumed': self.calculate_total_energy(processors),
                'efficiency': self.calculate_energy_efficiency(processors, tasks_completed),
                'profile': self.calculate_power_consumption_profile(processors)
            },
            'load_balance': {
                'std_deviation': self.calculate_load_balance(
                    [p.completed_tasks for p in processors]
                ),
                'distribution': self.calculate_load_distribution(processors),
                'avg_utilization': self.calculate_average_utilization(processors)
            },
            'processors': [
                self.calculate_processor_efficiency(p) for p in processors
            ]
        }
    
    def add_snapshot(self, snapshot):
        """
        Añade un snapshot temporal para análisis histórico.
        
        Args:
            snapshot (dict): Datos del snapshot
        """
        self.history.append(snapshot)
    
    def get_history(self):
        """Obtiene el historial de snapshots."""
        return self.history
    
    def reset(self):
        """Reinicia el historial."""
        self.history = []