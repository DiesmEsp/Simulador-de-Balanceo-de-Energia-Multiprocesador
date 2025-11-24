"""
Punto de entrada principal del simulador.
Permite ejecutar simulaciones desde línea de comandos.
"""
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Optional

from .simulation.engine import SimulationEngine, SimulationConfig, SimulationResults
from .metrics.collector import MetricsCollector, ResultsExporter
from .utils.config import (
    load_config, build_simulation_config, 
    list_scenarios, list_strategies
)


def print_banner():
    """Imprime banner del simulador."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║     Simulador de Balanceo de Energía en Multiprocesador      ║
║                    v1.0 - Python                             ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_results(results: SimulationResults, strategy: str):
    """Imprime resultados de forma formateada."""
    print(f"\n{'='*60}")
    print(f"  RESULTADOS - Estrategia: {strategy.upper()}")
    print(f"{'='*60}")
    
    print("\n📊 RENDIMIENTO:")
    print(f"   • Makespan:            {results.makespan:>10.2f} unidades")
    print(f"   • Tareas completadas:  {results.completed_tasks:>10d} / {results.total_tasks}")
    print(f"   • Throughput:          {results.throughput:>10.4f} tareas/tiempo")
    print(f"   • Tiempo respuesta:    {results.avg_response_time:>10.2f} promedio")
    
    print("\n⚡ ENERGÍA:")
    print(f"   • Energía total:       {results.total_energy:>10.2f} Joules")
    print(f"   • Potencia promedio:   {results.avg_power:>10.2f} Watts")
    print(f"   • Eficiencia:          {results.energy_efficiency:>10.6f} tareas/J")
    
    print("\n⚖️  BALANCE:")
    print(f"   • Score de balance:    {results.load_balance_score:>10.2%}")
    print(f"   • Utilización media:   {results.utilization_avg:>10.2%}")
    print(f"   • Desv. utilización:   {results.utilization_std:>10.2%}")
    print(f"   • Migraciones:         {results.total_migrations:>10d}")
    
    print(f"\n{'='*60}\n")


def run_single_simulation(
    n_processors: int,
    strategy: str,
    scenario: Optional[str] = None,
    config_file: Optional[str] = None,
    duration: float = 1000,
    arrival_rate: float = 0.5,
    total_tasks: int = 100,
    heterogeneous: bool = False,
    show_progress: bool = True,
    export_path: Optional[str] = None
) -> SimulationResults:
    """
    Ejecuta una simulación individual.
    
    Args:
        n_processors: Número de procesadores
        strategy: Estrategia de balanceo ('performance', 'energy', 'dvfs')
        scenario: Escenario predefinido (opcional)
        config_file: Archivo de configuración (opcional)
        duration: Duración de la simulación
        arrival_rate: Tasa de llegada de tareas
        total_tasks: Número total de tareas
        heterogeneous: Si usar procesadores heterogéneos
        show_progress: Mostrar barra de progreso
        export_path: Ruta para exportar resultados
        
    Returns:
        SimulationResults con los resultados
    """
    # Cargar configuración base
    config_dict = None
    if config_file:
        config_dict = load_config(config_file)
    
    # Construir configuración
    sim_config = build_simulation_config(
        config_dict=config_dict,
        scenario=scenario,
        n_processors=n_processors,
        strategy=strategy,
        duration=duration,
        arrival_rate=arrival_rate,
        total_tasks=total_tasks,
        heterogeneous=heterogeneous
    )
    
    # Crear engine
    engine = SimulationEngine(sim_config)
    
    # Configurar recolector de métricas
    collector = MetricsCollector(collect_interval=10)
    
    def on_step_callback():
        if collector.should_collect(engine.current_time):
            collector.collect(engine.current_time, engine.system)
    
    engine.register_callback('on_step', lambda: on_step_callback())
    
    # Progress callback
    if show_progress:
        def progress_cb(p):
            bar_len = 40
            filled = int(bar_len * p)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f'\r  Progreso: [{bar}] {p*100:.1f}%', end='', flush=True)
        
        progress_callback = progress_cb
    else:
        progress_callback = None
    
    # Ejecutar
    print("\n🚀 Iniciando simulación...")
    print(f"   Procesadores: {n_processors}")
    print(f"   Estrategia: {strategy}")
    print(f"   Escenario: {scenario or 'default'}")
    print(f"   Tareas: {total_tasks}")
    print()
    
    start_time = time.perf_counter()
    results = engine.run(progress_callback=progress_callback)
    elapsed = time.perf_counter() - start_time
    
    if show_progress:
        print()  # Nueva línea después de la barra
    
    print(f"\n✅ Simulación completada en {elapsed:.2f}s")
    
    # Exportar si se solicita
    if export_path:
        path = Path(export_path)
        ResultsExporter.export_results(results, str(path / f'{strategy}_results.json'))
        collector.export_csv(str(path / f'{strategy}_metrics.csv'))
        print(f"📁 Resultados exportados a: {export_path}")
    
    return results


def run_comparison(
    n_processors: int,
    strategies: list = None,
    scenario: Optional[str] = None,
    config_file: Optional[str] = None,
    **kwargs
) -> Dict[str, SimulationResults]:
    """
    Ejecuta comparación entre múltiples estrategias.
    """
    if strategies is None:
        strategies = ['performance', 'energy', 'dvfs']
    
    results_dict = {}
    
    print("\n🔄 Ejecutando comparación de estrategias...")
    print(f"   Estrategias: {', '.join(strategies)}")
    print()
    
    for strategy in strategies:
        print(f"\n--- {strategy.upper()} ---")
        results = run_single_simulation(
            n_processors=n_processors,
            strategy=strategy,
            scenario=scenario,
            config_file=config_file,
            **kwargs
        )
        results_dict[strategy] = results
        print_results(results, strategy)
    
    # Imprimir tabla comparativa
    print("\n" + "="*80)
    print("  TABLA COMPARATIVA")
    print("="*80)
    print(f"{'Métrica':<25} | ", end="")
    for s in strategies:
        print(f"{s:>15} | ", end="")
    print()
    print("-"*80)
    
    metrics = [
        ('Makespan', 'makespan', '.2f'),
        ('Energía Total (J)', 'total_energy', '.2f'),
        ('Eficiencia (tareas/J)', 'energy_efficiency', '.6f'),
        ('Throughput', 'throughput', '.4f'),
        ('Balance de Carga', 'load_balance_score', '.2%'),
        ('Utilización', 'utilization_avg', '.2%'),
        ('Migraciones', 'total_migrations', 'd')
    ]
    
    for name, attr, fmt in metrics:
        print(f"{name:<25} | ", end="")
        for s in strategies:
            val = getattr(results_dict[s], attr)
            print(f"{val:>15{fmt}} | ", end="")
        print()
    
    print("="*80)
    
    return results_dict


def main():
    """Función principal CLI."""
    parser = argparse.ArgumentParser(
        description='Simulador de Balanceo de Energía en Multiprocesador',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m src.main -n 8 -s dvfs
  python -m src.main -n 16 -s performance --scenario high_load
  python -m src.main -n 8 --compare
  python -m src.main -n 32 -s energy --tasks 500 --duration 2000
        """
    )
    
    parser.add_argument('-n', '--processors', type=int, default=8,
                       help='Número de procesadores (default: 8)')
    parser.add_argument('-s', '--strategy', type=str, default='dvfs',
                       choices=['performance', 'energy', 'dvfs'],
                       help='Estrategia de balanceo')
    parser.add_argument('--scenario', type=str, default=None,
                       help='Escenario predefinido')
    parser.add_argument('--config', type=str, default=None,
                       help='Archivo de configuración YAML/JSON')
    parser.add_argument('--duration', type=float, default=1000,
                       help='Duración de simulación')
    parser.add_argument('--tasks', type=int, default=100,
                       help='Número de tareas')
    parser.add_argument('--arrival-rate', type=float, default=0.5,
                       help='Tasa de llegada de tareas')
    parser.add_argument('--heterogeneous', action='store_true',
                       help='Usar procesadores heterogéneos')
    parser.add_argument('--compare', action='store_true',
                       help='Comparar todas las estrategias')
    parser.add_argument('--export', type=str, default=None,
                       help='Directorio para exportar resultados')
    parser.add_argument('--no-progress', action='store_true',
                       help='No mostrar barra de progreso')
    parser.add_argument('--list-scenarios', action='store_true',
                       help='Listar escenarios disponibles')
    parser.add_argument('--plot', action='store_true',
                       help='Generar gráficas (requiere matplotlib)')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.list_scenarios:
        scenarios = list_scenarios()
        print("Escenarios disponibles:")
        for s in scenarios:
            print(f"  • {s}")
        return 0
    
    try:
        if args.compare:
            results = run_comparison(
                n_processors=args.processors,
                scenario=args.scenario,
                config_file=args.config,
                duration=args.duration,
                total_tasks=args.tasks,
                arrival_rate=args.arrival_rate,
                heterogeneous=args.heterogeneous,
                show_progress=not args.no_progress,
                export_path=args.export
            )
            
            if args.plot:
                try:
                    from .visualization.plots import plot_comparison
                    fig, _ = plot_comparison(results)
                    if args.export:
                        fig.savefig(f"{args.export}/comparison.png", dpi=150)
                    import matplotlib.pyplot as plt
                    plt.show()
                except ImportError:
                    print("⚠️  matplotlib no disponible para gráficas")
        else:
            results = run_single_simulation(
                n_processors=args.processors,
                strategy=args.strategy,
                scenario=args.scenario,
                config_file=args.config,
                duration=args.duration,
                total_tasks=args.tasks,
                arrival_rate=args.arrival_rate,
                heterogeneous=args.heterogeneous,
                show_progress=not args.no_progress,
                export_path=args.export
            )
            print_results(results, args.strategy)
            
            if args.plot:
                try:
                    from .visualization.plots import create_summary_dashboard
                    fig = create_summary_dashboard(results, args.strategy)
                    if args.export:
                        fig.savefig(f"{args.export}/dashboard_{args.strategy}.png", dpi=150)
                    import matplotlib.pyplot as plt
                    plt.show()
                except ImportError:
                    print("⚠️  matplotlib no disponible para gráficas")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())