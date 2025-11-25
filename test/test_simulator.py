"""
Pruebas unitarias para el simulador.
"""

import pytest
import sys
sys.path.insert(0, '../src')

from simulator import Simulator
from processor import Processor, ProcessorPool
from task import Task, TaskGenerator
from energy_manager import EnergyManager


class TestSimulator:
    """Tests para la clase Simulator."""
    
    def test_simulator_initialization(self):
        """Verifica que el simulador se inicialice correctamente."""
        sim = Simulator(4, 20, 'high_cpu', 'balanced')
        
        assert sim.num_processors == 4
        assert sim.num_tasks == 20
        assert sim.scenario == 'high_cpu'
        assert sim.strategy == 'balanced'
        assert sim.current_time == 0.0
        assert sim.completed_tasks == 0
        
    def test_simulator_step(self):
        """Verifica que el simulador ejecute pasos correctamente."""
        sim = Simulator(2, 5, 'high_cpu', 'performance')
        
        initial_time = sim.current_time
        sim.step()
        
        assert sim.current_time > initial_time
        
    def test_simulator_run_completes(self):
        """Verifica que la simulación se complete."""
        sim = Simulator(4, 10, 'high_cpu', 'balanced')
        results = sim.run()
        
        assert results['completed_tasks'] == 10
        assert results['makespan'] > 0
        assert results['total_energy'] > 0
        
    def test_simulator_different_strategies(self):
        """Verifica que diferentes estrategias produzcan resultados distintos."""
        sim_perf = Simulator(4, 20, 'high_cpu', 'performance')
        results_perf = sim_perf.run()
        
        sim_energy = Simulator(4, 20, 'high_cpu', 'energy')
        results_energy = sim_energy.run()
        
        # Performance debería consumir más energía
        assert results_perf['total_energy'] > results_energy['total_energy']
        
    def test_simulator_reset(self):
        """Verifica que el reset funcione correctamente."""
        sim = Simulator(4, 20, 'high_cpu', 'balanced')
        sim.run()
        
        sim.reset()
        
        assert sim.current_time == 0.0
        assert sim.completed_tasks == 0
        assert not sim.is_running


class TestProcessor:
    """Tests para la clase Processor."""
    
    def test_processor_initialization(self):
        """Verifica inicialización del procesador."""
        proc = Processor(0, capacity=1.0, base_frequency=2.5)
        
        assert proc.processor_id == 0
        assert proc.capacity == 1.0
        assert proc.frequency == 2.5
        assert proc.load == 0.0
        assert proc.energy_consumed == 0.0
        
    def test_processor_add_task(self):
        """Verifica que se puedan añadir tareas."""
        proc = Processor(0)
        task = Task(1, 100, 0.8)
        
        success = proc.add_task(task)
        
        assert success
        assert len(proc.active_tasks) == 1
        assert proc.is_active
        
    def test_processor_task_limit(self):
        """Verifica el límite de tareas concurrentes."""
        proc = Processor(0)
        
        # Añadir 5 tareas (límite)
        for i in range(5):
            task = Task(i, 100, 0.8)
            proc.add_task(task)
        
        # Intentar añadir una más
        extra_task = Task(6, 100, 0.8)
        success = proc.add_task(extra_task)
        
        assert not success
        assert len(proc.active_tasks) == 5
        
    def test_processor_execute_step(self):
        """Verifica ejecución de pasos."""
        proc = Processor(0, base_frequency=2.0)
        task = Task(1, 10, 0.8)
        proc.add_task(task)
        
        initial_energy = proc.energy_consumed
        completed = proc.execute_step(1.0, 1.0)
        
        assert proc.energy_consumed > initial_energy
        assert task.remaining < task.duration


class TestTask:
    """Tests para la clase Task."""
    
    def test_task_initialization(self):
        """Verifica inicialización de tarea."""
        task = Task(1, 100, 0.8, 0)
        
        assert task.task_id == 1
        assert task.duration == 100
        assert task.intensity == 0.8
        assert not task.assigned
        assert not task.completed
        
    def test_task_update_progress(self):
        """Verifica actualización de progreso."""
        task = Task(1, 100, 0.8)
        
        completed = task.update_progress(50)
        
        assert not completed
        assert task.remaining == 50
        
        completed = task.update_progress(50)
        
        assert completed
        assert task.completed
        assert task.remaining == 0
        
    def test_task_generator(self):
        """Verifica generación de tareas."""
        tasks = TaskGenerator.generate_tasks(10, 'high_cpu')
        
        assert len(tasks) == 10
        assert all(isinstance(t, Task) for t in tasks)
        assert all(t.intensity >= 0.8 for t in tasks)


class TestEnergyManager:
    """Tests para la clase EnergyManager."""
    
    def test_energy_manager_initialization(self):
        """Verifica inicialización del gestor."""
        em = EnergyManager('balanced')
        
        assert em.strategy == 'balanced'
        assert em.config is not None
        
    def test_energy_manager_strategies(self):
        """Verifica que las estrategias tengan configuraciones distintas."""
        em_perf = EnergyManager('performance')
        em_energy = EnergyManager('energy')
        em_balanced = EnergyManager('balanced')
        
        assert em_perf.config['base_freq'] > em_energy.config['base_freq']
        assert em_perf.config['power_multiplier'] > em_energy.config['power_multiplier']
        
    def test_adjust_frequency(self):
        """Verifica ajuste de frecuencia."""
        em = EnergyManager('balanced')
        proc = Processor(0, base_frequency=2.5)
        
        # Sin carga
        freq1 = em.adjust_frequency(proc)
        
        # Con carga
        task = Task(1, 100, 0.8)
        proc.add_task(task)
        freq2 = em.adjust_frequency(proc)
        
        assert freq2 > freq1
        
    def test_should_migrate_task(self):
        """Verifica lógica de migración."""
        em = EnergyManager('balanced')
        proc1 = Processor(0)
        proc2 = Processor(1)
        
        # Añadir carga alta a proc1
        for i in range(3):
            proc1.add_task(Task(i, 100, 0.8))
        
        should_migrate = em.should_migrate_task(proc1, proc2)
        
        assert should_migrate


class TestProcessorPool:
    """Tests para ProcessorPool."""
    
    def test_pool_initialization(self):
        """Verifica inicialización del pool."""
        pool = ProcessorPool(4, 'balanced')
        
        assert len(pool.processors) == 4
        assert all(isinstance(p, Processor) for p in pool.processors)
        
    def test_get_least_loaded(self):
        """Verifica obtención del procesador menos cargado."""
        pool = ProcessorPool(3, 'balanced')
        
        # Añadir carga a procesador 0
        pool.processors[0].add_task(Task(1, 100, 0.8))
        
        least_loaded = pool.get_least_loaded()
        
        assert least_loaded.processor_id in [1, 2]
        
    def test_heterogeneous_pool(self):
        """Verifica pool heterogéneo."""
        pool = ProcessorPool(4, 'heterogeneous')
        
        # Primeros procesadores deberían ser más potentes
        assert pool.processors[0].capacity > pool.processors[2].capacity


def run_all_tests():
    """Ejecuta todas las pruebas."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_all_tests()