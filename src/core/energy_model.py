"""
Modelo de consumo energético para procesadores.
Implementa la relación entre frecuencia, voltaje y consumo de energía.
"""
from typing import List
import numpy as np


class EnergyProfile:
    """Perfil energético de un procesador."""
    
    __slots__ = (
        'base_frequency', 'max_frequency', 'frequency_steps',
        'base_power', 'max_power', 'idle_power',
        '_frequencies', '_powers'
    )
    
    def __init__(
        self,
        base_frequency: float = 1.0,
        max_frequency: float = 3.5,
        frequency_steps: int = 5,
        base_power: float = 5.0,
        max_power: float = 95.0,
        idle_power: float = 2.0
    ):
        self.base_frequency = base_frequency
        self.max_frequency = max_frequency
        self.frequency_steps = frequency_steps
        self.base_power = base_power
        self.max_power = max_power
        self.idle_power = idle_power
        
        # Precalcular frecuencias disponibles
        self._frequencies = np.linspace(
            self.base_frequency, 
            self.max_frequency, 
            self.frequency_steps
        )
        
        # Precalcular potencias correspondientes (relación cuadrática aproximada)
        norm_freqs = (self._frequencies - self.base_frequency) / (self.max_frequency - self.base_frequency)
        self._powers = self.base_power + (self.max_power - self.base_power) * (norm_freqs ** 2)
    
    @property
    def frequencies(self) -> np.ndarray:
        return self._frequencies
    
    @property
    def powers(self) -> np.ndarray:
        return self._powers
    
    def get_frequency_level(self, level: int) -> float:
        """Obtiene frecuencia para un nivel dado (0 = mínimo)."""
        return self._frequencies[min(level, self.frequency_steps - 1)]
    
    def get_power_at_level(self, level: int) -> float:
        """Obtiene consumo para un nivel de frecuencia."""
        return self._powers[min(level, self.frequency_steps - 1)]
    
    def get_nearest_level(self, frequency: float) -> int:
        """Encuentra el nivel más cercano a una frecuencia."""
        return int(np.argmin(np.abs(self._frequencies - frequency)))


class EnergyCalculator:
    """Calculador de energía optimizado para múltiples procesadores."""
    
    __slots__ = ('_profiles', '_current_levels', '_active_states', '_accumulated_energy')
    
    def __init__(self, profiles: List[EnergyProfile]):
        self._profiles = profiles
        n = len(profiles)
        self._current_levels = np.zeros(n, dtype=np.int32)
        self._active_states = np.ones(n, dtype=np.bool_)
        self._accumulated_energy = np.zeros(n, dtype=np.float64)
    
    def set_frequency_level(self, proc_id: int, level: int):
        """Establece nivel de frecuencia para un procesador."""
        self._current_levels[proc_id] = level
    
    def set_active(self, proc_id: int, active: bool):
        """Establece estado activo/inactivo de un procesador."""
        self._active_states[proc_id] = active
    
    def calculate_instant_power(self) -> np.ndarray:
        """Calcula potencia instantánea de todos los procesadores."""
        powers = np.zeros(len(self._profiles), dtype=np.float64)
        for i, (profile, level, active) in enumerate(
            zip(self._profiles, self._current_levels, self._active_states)
        ):
            if active:
                powers[i] = profile.get_power_at_level(level)
            else:
                powers[i] = profile.idle_power
        return powers
    
    def accumulate_energy(self, dt: float, load_factors: np.ndarray) -> np.ndarray:
        """
        Acumula energía consumida en un intervalo dt.
        load_factors: array de 0-1 indicando carga de cada procesador.
        """
        powers = np.zeros(len(self._profiles), dtype=np.float64)
        for i, (profile, level, active) in enumerate(
            zip(self._profiles, self._current_levels, self._active_states)
        ):
            if active:
                max_power = profile.get_power_at_level(level)
                # Potencia escala con la carga
                powers[i] = profile.idle_power + (max_power - profile.idle_power) * load_factors[i]
            else:
                powers[i] = profile.idle_power * 0.5  # Deep sleep
        
        energy = powers * dt
        self._accumulated_energy += energy
        return energy
    
    def get_total_energy(self) -> float:
        """Retorna energía total acumulada."""
        return float(np.sum(self._accumulated_energy))
    
    def get_energy_per_processor(self) -> np.ndarray:
        """Retorna energía acumulada por procesador."""
        return self._accumulated_energy.copy()
    
    def reset_accumulated(self):
        """Resetea contadores de energía."""
        self._accumulated_energy.fill(0.0)