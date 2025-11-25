"""
Motor principal de simulación.
Coordina procesadores, tareas y estrategias energéticas.
"""

import argparse
from task import TaskGenerator
from processor import ProcessorPool
from energy_manager import EnergyManager
from scheduler import Scheduler
from metrics import MetricsCalculator


class Simulator:
    """
    Simulador principal del sistema multiprocesador.
    """
    
    def __init__(self, num_processors, num_tasks, scenario='high_cpu', strategy='balanced'):
        """
        Inicializa el simulador.
        
        Args:
            num_processors (int): Número de procesadores
            num_tasks (int): Número de tareas a simular
            scenario (str): Escenario de carga
            strategy (str): Estrategia energética
        """
        self.num_processors = num_processors
        self.num_tasks = num_tasks
        self.scenario = scenario
        self.strategy = strategy
        
        # Componentes del simulador
        self.processor_pool = ProcessorPool(
            num_processors,
            'heterogeneous' if scenario == 'heterogeneous' else 'balanced'
        )
        self.tasks = TaskGenerator.generate_tasks(num_tasks, scenario)
        self.energy_manager = EnergyManager(strategy)
        self.scheduler = Scheduler(self.processor_pool, self.energy_manager)
        self.metrics = MetricsCalculator()
        
        # Estado de la simulación
        self.current_time = 0.0
        self.time_step = 1.0
        self.completed_tasks = 0
        self.is_running = False
        
    def step(self):
        """
        Ejecuta un paso de simulación.
        
        Returns:
            bool: True si la simulación ha terminado
        """
        # Obtener tareas que han llegado
        available_tasks = [
            t for t in self.tasks 
            if not t.assigned and not t.completed and t.arrival_time <= self.current_time
        ]
        
        # Asignar tareas a procesadores
        if available_tasks:
            self.scheduler.assign_tasks(available_tasks)
        
        # Optimizar frecuencias
        self.energy_manager.optimize_processor_states(self.processor_pool.processors)
        
        # Ejecutar paso en cada procesador
        power_mult = self.energy_manager.get_power_multiplier()
        for processor in self.processor_pool.processors:
            completed = processor.execute_step(self.time_step, power_mult)
            self.completed_tasks += len(completed)
        
        # Intentar migrar tareas si es necesario
        if self.current_time % 10 == 0:  # Cada 10 unidades de tiempo
            self.scheduler.migrate_tasks()
        
        # Avanzar tiempo
        self.current_time += self.time_step
        
        # Verificar si terminó
        return self.completed_tasks >= self.num_tasks
    
    def run(self, max_steps=10000):
        """
        Ejecuta la simulación completa.
        
        Args:
            max_steps (int): Número máximo de pasos
            
        Returns:
            dict: Resultados de la simulación
        """
        self.is_running = True
        steps = 0
        
        while self.completed_tasks < self.num_tasks and steps < max_steps:
            if self.step():
                break
            steps += 1
        
        self.is_running = False
        return self.get_results()
    
    def get_state(self):
        """
        Obtiene el estado actual de la simulación.
        
        Returns:
            dict: Estado actual
        """
        processors_state = [p.get_status() for p in self.processor_pool.processors]
        total_energy = sum(p.energy_consumed for p in self.processor_pool.processors)
        
        return {
            'total_time': self.current_time,
            'total_energy': total_energy,
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.num_tasks,
            'processors': processors_state,
            'is_running': self.is_running
        }
    
    def get_results(self):
        """
        Obtiene los resultados finales de la simulación.
        
        Returns:
            dict: Resultados completos
        """
        state = self.get_state()
        processors = self.processor_pool.processors
        
        # Calcular métricas
        makespan = self.current_time
        total_energy = state['total_energy']
        efficiency = self.completed_tasks / total_energy if total_energy > 0 else 0
        
        # Balance de carga
        completed_per_proc = [p.completed_tasks for p in processors]
        load_balance = self.metrics.calculate_load_balance(completed_per_proc)
        
        # Utilización promedio
        avg_utilization = sum(p.get_utilization() for p in processors) / len(processors)
        
        return {
            'makespan': makespan,
            'total_energy': total_energy,
            'efficiency': efficiency,
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.num_tasks,
            'load_balance_std': load_balance,
            'avg_utilization': avg_utilization,
            'processors': [p.get_status() for p in processors],
            'strategy': self.strategy,
            'scenario': self.scenario,
            'num_processors': self.num_processors
        }
    
    def reset(self):
        """Reinicia el simulador."""
        self.current_time = 0.0
        self.completed_tasks = 0
        self.is_running = False
        
        # Reiniciar componentes
        self.processor_pool.reset_all()
        self.tasks = TaskGenerator.generate_tasks(self.num_tasks, self.scenario)
        self.energy_manager.reset()


def main():
    """Función principal para ejecución desde línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Simulador de Balanceo de Energía para Sistemas Multiprocesador'
    )
    
    parser.add_argument(
        '--processors',
        type=int,
        default=4,
        help='Número de procesadores (default: 4)'
    )
    
    parser.add_argument(
        '--tasks',
        type=int,
        default=20,
        help='Número de tareas (default: 20)'
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        default='high_cpu',
        choices=['high_cpu', 'intermittent', 'heterogeneous', 'spike'],
        help='Escenario de carga (default: high_cpu)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        default='balanced',
        choices=['performance', 'energy', 'balanced'],
        help='Estrategia energética (default: balanced)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SIMULADOR DE BALANCEO DE ENERGÍA")
    print("=" * 60)
    print("\nConfiguración:")
    print(f"  Procesadores: {args.processors}")
    print(f"  Tareas: {args.tasks}")
    print(f"  Escenario: {args.scenario}")
    print(f"  Estrategia: {args.strategy}")
    print("\nIniciando simulación...\n")
    
    # Crear y ejecutar simulador
    simulator = Simulator(
        args.processors,
        args.tasks,
        args.scenario,
        args.strategy
    )
    
    results = simulator.run()
    
    # Mostrar resultados
    print("=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    print(f"\nTiempo Total (Makespan): {results['makespan']:.2f} unidades")
    print(f"Energía Total Consumida: {results['total_energy']:.2f} J")
    print(f"Eficiencia Energética: {results['efficiency']:.4f} tareas/J")
    print(f"Tareas Completadas: {results['completed_tasks']} / {results['total_tasks']}")
    print(f"Balance de Carga (σ): {results['load_balance_std']:.2f}")
    print(f"Utilización Promedio: {results['avg_utilization']:.1f}%")
    
    print("\nEstado por Procesador:")
    for proc_state in results['processors']:
        print(f"\n  Procesador {proc_state['id']}:")
        print(f"    Frecuencia: {proc_state['frequency']:.2f} GHz")
        print(f"    Energía: {proc_state['energy']:.2f} J")
        print(f"    Tiempo Ejecución: {proc_state['execution_time']:.2f}")
        print(f"    Tareas Completadas: {proc_state['completed_tasks']}")
        print(f"    Utilización: {proc_state['utilization']:.1f}%")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()