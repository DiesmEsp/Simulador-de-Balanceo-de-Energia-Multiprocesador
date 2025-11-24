"""Módulo core del simulador."""
from .processor import Processor, ProcessorState
from .multiprocessor import MultiprocessorSystem
from .task import Task, TaskType, TaskState, TaskGenerator
from .energy_model import EnergyProfile, EnergyCalculator

__all__ = [
    'Processor', 'ProcessorState',
    'MultiprocessorSystem',
    'Task', 'TaskType', 'TaskState', 'TaskGenerator',
    'EnergyProfile', 'EnergyCalculator'
]
