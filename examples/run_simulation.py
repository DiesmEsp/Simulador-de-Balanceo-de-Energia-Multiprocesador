"""
Ejemplo de uso del simulador de balanceo de energía.
Muestra cómo ejecutar simulaciones y comparar estrategias.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    SimulationEngine, SimulationConfig, 
    build_simulation_config, get_scheduler
)
from src.metrics import MetricsCollector, ResultsExporter
from src.visualization import create_summary_dashboard, plot_comparison


def ejemplo_basico():
    """Ejemplo básico de simulación."""
    print("=" * 60)
    print("EJEMPLO 1: Simulación Básica")
    print("=" * 60)
    
    # Configuración simple
    config = SimulationConfig(
        n_processors=8,
        strategy='dvfs',
        duration=500,
        total_tasks=100,
        arrival_rate=0.5
    )
    
    # Crear y ejecutar
    engine = SimulationEngine(config)
    results = engine.run(progress_callback=lambda p: print(f"\rProgreso: {p:.1%}", end=""))
    print()
    
    # Mostrar resultados
    print("\nResultados:")
    print(f"  Makespan: {results.makespan:.2f}")
    print(f"  Energía total: {results.total_energy:.2f} J")
    print(f"  Eficiencia: {results.energy_efficiency:.6f} tareas/J")
    print(f"  Balance: {results.load_balance_score:.2%}")


def ejemplo_comparacion():
    """Compara las tres estrategias."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Comparación de Estrategias")
    print("=" * 60)
    
    strategies = ['performance', 'energy', 'dvfs']
    results_dict = {}
    
    for strategy in strategies:
        print(f"\n--- Ejecutando: {strategy} ---")
        
        config = build_simulation_config(
            n_processors=16,
            strategy=strategy,
            duration=800,
            total_tasks=150,
            arrival_rate=0.8
        )
        
        engine = SimulationEngine(config)
        results = engine.run()
        results_dict[strategy] = results
        
        print(f"  Completado - Makespan: {results.makespan:.1f}, Energía: {results.total_energy:.1f}J")
    
    # Tabla comparativa
    print("\n" + "-" * 70)
    print(f"{'Estrategia':<15} {'Makespan':>10} {'Energía':>12} {'Eficiencia':>12} {'Balance':>10}")
    print("-" * 70)
    
    for name, r in results_dict.items():
        print(f"{name:<15} {r.makespan:>10.1f} {r.total_energy:>12.1f} {r.energy_efficiency:>12.6f} {r.load_balance_score:>10.2%}")
    
    return results_dict


def ejemplo_escenarios():
    """Prueba diferentes escenarios."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Diferentes Escenarios")
    print("=" * 60)
    
    escenarios = [
        ('high_load', 'Alta carga CPU'),
        ('intermittent', 'Carga intermitente'),
        ('unexpected_burst', 'Picos inesperados')
    ]
    
    for scenario, descripcion in escenarios:
        print(f"\n--- Escenario: {descripcion} ---")
        
        config = build_simulation_config(
            scenario=scenario,
            n_processors=12,
            strategy='dvfs'
        )
        
        engine = SimulationEngine(config)
        results = engine.run()
        
        print(f"  Tareas: {results.completed_tasks}/{results.total_tasks}")
        print(f"  Makespan: {results.makespan:.1f}")
        print(f"  Energía: {results.total_energy:.1f} J")
        print(f"  Migraciones: {results.total_migrations}")


def ejemplo_alta_escala():
    """Simulación con muchos procesadores."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Alta Escala (64 procesadores)")
    print("=" * 60)
    
    config = SimulationConfig(
        n_processors=64,
        strategy='dvfs',
        duration=1000,
        total_tasks=500,
        arrival_rate=2.0,
        time_step=1.0
    )
    
    engine = SimulationEngine(config)
    
    import time
    start = time.perf_counter()
    results = engine.run(progress_callback=lambda p: print(f"\rProgreso: {p:.1%}", end=""))
    elapsed = time.perf_counter() - start
    print()
    
    print(f"\n  Tiempo de ejecución: {elapsed:.2f}s")
    print("  Procesadores: 64")
    print(f"  Tareas procesadas: {results.completed_tasks}")
    print(f"  Throughput: {results.throughput:.4f} tareas/tiempo")
    print(f"  Energía total: {results.total_energy:.1f} J")


def ejemplo_heterogeneo():
    """Simulación con procesadores heterogéneos."""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Procesadores Heterogéneos")
    print("=" * 60)
    
    config = build_simulation_config(
        n_processors=8,
        heterogeneous=True,
        strategy='dvfs',
        duration=600,
        total_tasks=120
    )
    
    engine = SimulationEngine(config)
    results = engine.run()
    
    print("\nSistema heterogéneo (2 performance + 6 efficiency):")
    print(f"  Makespan: {results.makespan:.1f}")
    print(f"  Energía total: {results.total_energy:.1f} J")
    print(f"  Eficiencia: {results.energy_efficiency:.6f} tareas/J")
    
    # Mostrar energía por procesador
    print("\n  Energía por procesador:")
    for i, e in enumerate(results.energy_per_processor):
        tipo = "PERF" if i < 2 else "EFF"
        print(f"    P{i} ({tipo}): {e:.1f} J")


def ejemplo_con_metricas():
    """Simulación con recolección detallada de métricas."""
    print("\n" + "=" * 60)
    print("EJEMPLO 6: Métricas Detalladas")
    print("=" * 60)
    
    config = SimulationConfig(
        n_processors=8,
        strategy='dvfs',
        duration=300,
        total_tasks=80
    )
    
    engine = SimulationEngine(config)
    collector = MetricsCollector(collect_interval=5)
    
    # Registrar callback para recolectar métricas
    def collect_callback():
        if collector.should_collect(engine.current_time):
            collector.collect(engine.current_time, engine.system)
    
    # Nota: El callback se ejecuta manualmente aquí para demostración
    # En uso real, se integraría con el engine
    
    results = engine.run()
    
    # Obtener resumen
    print(f"\n  Snapshots recolectados: {len(collector.get_snapshots())}")
    
    summary = collector.get_summary()
    if summary:
        print(f"  Potencia promedio: {summary['power']['mean']:.2f} W")
        print(f"  Potencia máxima: {summary['power']['max']:.2f} W")
        print(f"  Procesadores activos (promedio): {summary['active_processors']['mean']:.1f}")


def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "=" * 70)
    print("   SIMULADOR DE BALANCEO DE ENERGÍA EN MULTIPROCESADOR")
    print("   Ejemplos de Uso")
    print("=" * 70)
    
    ejemplo_basico()
    ejemplo_comparacion()
    ejemplo_escenarios()
    ejemplo_alta_escala()
    ejemplo_heterogeneo()
    ejemplo_con_metricas()
    
    print("\n" + "=" * 70)
    print("   Todos los ejemplos completados exitosamente!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()