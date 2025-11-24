"""Módulo de visualización."""
try:
    from .plots import (
        plot_power_over_time,
        plot_load_distribution,
        plot_queue_over_time,
        plot_comparison,
        plot_energy_breakdown,
        create_summary_dashboard
    )
    __all__ = [
        'plot_power_over_time',
        'plot_load_distribution', 
        'plot_queue_over_time',
        'plot_comparison',
        'plot_energy_breakdown',
        'create_summary_dashboard'
    ]
except ImportError:
    # matplotlib no disponible
    __all__ = []