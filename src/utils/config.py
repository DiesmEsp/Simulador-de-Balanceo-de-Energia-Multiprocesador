"""
Gestión de configuración del simulador.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import fields
import yaml
import json

from ..simulation.engine import SimulationConfig


def load_yaml(filepath: str) -> Dict[str, Any]:
    """Carga configuración desde archivo YAML."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def load_json(filepath: str) -> Dict[str, Any]:
    """Carga configuración desde archivo JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def load_config(filepath: str) -> Dict[str, Any]:
    """Carga configuración detectando formato automáticamente."""
    path = Path(filepath)
    
    if path.suffix in ('.yaml', '.yml'):
        return load_yaml(filepath)
    elif path.suffix == '.json':
        return load_json(filepath)
    else:
        # Intentar YAML primero
        try:
            return load_yaml(filepath)
        except:
            return load_json(filepath)


def build_simulation_config(
    config_dict: Optional[Dict] = None,
    scenario: Optional[str] = None,
    **overrides
) -> SimulationConfig:
    """
    Construye SimulationConfig desde diccionario y overrides.
    
    Args:
        config_dict: Diccionario de configuración base
        scenario: Nombre de escenario predefinido
        **overrides: Valores que sobreescriben la configuración
        
    Returns:
        SimulationConfig configurado
    """
    # Valores por defecto
    params = {
        'duration': 1000.0,
        'time_step': 1.0,
        'random_seed': 42,
        'n_processors': 8,
        'heterogeneous': False,
        'processor_config': {},
        'task_mode': 'mixed',
        'arrival_rate': 0.5,
        'total_tasks': 100,
        'task_config': {},
        'strategy': 'dvfs',
        'strategy_config': {},
        'scenario': None,
        'burst_times': [],
        'burst_size': 10
    }
    
    # Aplicar configuración del archivo
    if config_dict:
        sim_cfg = config_dict.get('simulation', {})
        proc_cfg = config_dict.get('processors', {})
        task_cfg = config_dict.get('tasks', {})
        strat_cfg = config_dict.get('strategies', {})
        
        params['duration'] = sim_cfg.get('duration', params['duration'])
        params['time_step'] = sim_cfg.get('time_step', params['time_step'])
        params['random_seed'] = sim_cfg.get('random_seed', params['random_seed'])
        
        params['n_processors'] = proc_cfg.get('count', params['n_processors'])
        params['heterogeneous'] = proc_cfg.get('heterogeneous', params['heterogeneous'])
        params['processor_config'] = proc_cfg.get('default', {})
        
        gen_cfg = task_cfg.get('generation', {})
        params['task_mode'] = gen_cfg.get('mode', params['task_mode'])
        params['arrival_rate'] = gen_cfg.get('arrival_rate', params['arrival_rate'])
        params['total_tasks'] = gen_cfg.get('total_tasks', params['total_tasks'])
        params['task_config'] = {
            'cpu_bound': task_cfg.get('cpu_bound', {}),
            'io_bound': task_cfg.get('io_bound', {})
        }
    
    # Aplicar escenario predefinido
    if scenario:
        scenario_params = get_scenario_params(scenario, config_dict)
        params.update(scenario_params)
    
    # Aplicar overrides
    params.update(overrides)
    
    # Configuración específica de estrategia
    if config_dict and params['strategy'] in config_dict.get('strategies', {}):
        params['strategy_config'] = config_dict['strategies'][params['strategy']]
    
    return SimulationConfig(**params)


def get_scenario_params(scenario: str, config_dict: Optional[Dict] = None) -> Dict:
    """Obtiene parámetros para un escenario predefinido."""
    
    # Escenarios integrados
    scenarios = {
        'high_load': {
            'task_mode': 'cpu_bound',
            'arrival_rate': 2.0,
            'total_tasks': 200
        },
        'intermittent': {
            'task_mode': 'mixed',
            'arrival_rate': 0.8,
            'burst_times': [200, 400, 600, 800],
            'burst_size': 15
        },
        'heterogeneous': {
            'heterogeneous': True,
            'task_mode': 'mixed'
        },
        'unexpected_burst': {
            'task_mode': 'cpu_bound',
            'arrival_rate': 0.3,
            'burst_times': [200, 500, 800],
            'burst_size': 25
        },
        'low_load': {
            'task_mode': 'io_bound',
            'arrival_rate': 0.2,
            'total_tasks': 50
        },
        'stress_test': {
            'task_mode': 'cpu_bound',
            'arrival_rate': 5.0,
            'total_tasks': 500,
            'duration': 2000
        }
    }
    
    # Verificar escenarios del archivo de configuración
    if config_dict and 'scenarios' in config_dict:
        scenarios.update(config_dict['scenarios'])
    
    return scenarios.get(scenario, {})


def list_scenarios(config_dict: Optional[Dict] = None) -> list:
    """Lista escenarios disponibles."""
    base = ['high_load', 'intermittent', 'heterogeneous', 
            'unexpected_burst', 'low_load', 'stress_test']
    
    if config_dict and 'scenarios' in config_dict:
        base.extend(config_dict['scenarios'].keys())
    
    return list(set(base))


def list_strategies() -> list:
    """Lista estrategias disponibles."""
    return ['performance', 'energy', 'dvfs']