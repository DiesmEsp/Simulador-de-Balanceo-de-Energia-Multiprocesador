"""
Módulo de schedulers/estrategias de balanceo.
"""
from .base_scheduler import BaseScheduler
from .performance_first import PerformanceFirstScheduler
from .energy_first import EnergyFirstScheduler
from .dvfs_balanced import DVFSBalancedScheduler

__all__ = [
    'BaseScheduler',
    'PerformanceFirstScheduler', 
    'EnergyFirstScheduler',
    'DVFSBalancedScheduler',
    'get_scheduler'
]

SCHEDULER_REGISTRY = {
    'performance': PerformanceFirstScheduler,
    'performance_first': PerformanceFirstScheduler,
    'energy': EnergyFirstScheduler,
    'energy_first': EnergyFirstScheduler,
    'dvfs': DVFSBalancedScheduler,
    'balanced': DVFSBalancedScheduler,
    'dvfs_balanced': DVFSBalancedScheduler
}


def get_scheduler(strategy: str, config: dict) -> BaseScheduler:
    """
    Factory function para obtener un scheduler por nombre.
    
    Args:
        strategy: Nombre de la estrategia ('performance', 'energy', 'dvfs')
        config: Configuración del scheduler
        
    Returns:
        Instancia del scheduler correspondiente
        
    Raises:
        ValueError: Si la estrategia no existe
    """
    strategy_lower = strategy.lower().replace('-', '_')
    
    if strategy_lower not in SCHEDULER_REGISTRY:
        available = list(set(SCHEDULER_REGISTRY.keys()))
        raise ValueError(
            f"Estrategia '{strategy}' no encontrada. "
            f"Disponibles: {available}"
        )
    
    scheduler_class = SCHEDULER_REGISTRY[strategy_lower]
    return scheduler_class(config)