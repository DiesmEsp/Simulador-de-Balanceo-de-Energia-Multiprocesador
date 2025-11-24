"""
Panel de gráficos estadísticos usando matplotlib.
"""
import tkinter as tk
from tkinter import ttk
from typing import List
import numpy as np

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class StatisticsCharts(ttk.Frame):
    """Panel con gráficos estadísticos."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        # Crear figura con subplots
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor='#1a1a2e')
        
        # Subplot 1: Energía y Potencia (arriba izquierda)
        self.ax_energy = self.fig.add_subplot(221)
        self._configure_axis(self.ax_energy, '⚡ Energía y Potencia')
        
        # Subplot 2: Rendimiento (arriba derecha)
        self.ax_perf = self.fig.add_subplot(222)
        self._configure_axis(self.ax_perf, '📊 Rendimiento')
        
        # Subplot 3: Carga por procesador (abajo izquierda)
        self.ax_load = self.fig.add_subplot(223)
        self._configure_axis(self.ax_load, '📉 Carga por Procesador')
        
        # Subplot 4: Energía por procesador (abajo derecha)
        self.ax_proc_energy = self.fig.add_subplot(224)
        self._configure_axis(self.ax_proc_energy, '🔋 Energía por Procesador')
        
        self.fig.tight_layout(pad=2.0)
        
        # Canvas de matplotlib en Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def _configure_axis(self, ax, title):
        """Configura el estilo de un eje."""
        ax.set_facecolor('#1a1a2e')
        ax.set_title(title, color='white', fontsize=10)
        ax.tick_params(colors='gray', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#404060')
    
    def update_plots(self, data: dict):
        """Actualiza todos los gráficos."""
        # Limpiar ejes
        for ax in [self.ax_energy, self.ax_perf, self.ax_load, self.ax_proc_energy]:
            ax.clear()
            self._configure_axis(ax, ax.get_title())
        
        # Gráfico 1: Energía y Potencia
        if data.get('time_history'):
            self._plot_energy(data)
        
        # Gráfico 2: Rendimiento
        if data.get('time_history'):
            self._plot_performance(data)
        
        # Gráfico 3: Carga por procesador
        if data.get('processor_loads'):
            self._plot_processor_loads(data)
        
        # Gráfico 4: Energía por procesador
        if data.get('processor_energies'):
            self._plot_processor_energy(data)
        
        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()
    
    def _plot_energy(self, data: dict):
        """Gráfico de energía y potencia."""
        ax = self.ax_energy
        time_hist = data['time_history']
        power_hist = data['power_history']
        energy_hist = data['energy_history']
        
        # Potencia
        ax.fill_between(time_hist, power_hist, alpha=0.3, color='#f39c12')
        ax.plot(time_hist, power_hist, color='#f39c12', linewidth=1.5, label='Potencia (W)')
        ax.set_ylabel('Potencia (W)', color='#f39c12', fontsize=8)
        ax.set_xlabel('Tiempo', color='gray', fontsize=8)
        
        # Energía en eje secundario
        ax2 = ax.twinx()
        ax2.plot(time_hist, energy_hist, color='#3498db', linewidth=2, label='Energía (J)')
        ax2.set_ylabel('Energía (J)', color='#3498db', fontsize=8)
        ax2.tick_params(colors='gray', labelsize=8)
        ax2.spines['right'].set_color('#404060')
        
        ax.legend(loc='upper left', fontsize=7, facecolor='#2d2d44', edgecolor='#404060', labelcolor='white')
    
    def _plot_performance(self, data: dict):
        """Gráfico de rendimiento."""
        ax = self.ax_perf
        time_hist = data['time_history']
        load_hist = data['load_history']
        completed_hist = data['completed_history']
        
        # Carga media
        ax.fill_between(time_hist, load_hist, alpha=0.3, color='#2ecc71')
        ax.plot(time_hist, load_hist, color='#2ecc71', linewidth=1.5, label='Carga (%)')
        ax.axhline(y=50, color='#666', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_ylim(0, 100)
        ax.set_ylabel('Carga (%)', color='#2ecc71', fontsize=8)
        ax.set_xlabel('Tiempo', color='gray', fontsize=8)
        
        # Tareas completadas
        ax2 = ax.twinx()
        ax2.plot(time_hist, completed_hist, color='#9b59b6', linewidth=2, label='Completadas')
        ax2.set_ylabel('Tareas', color='#9b59b6', fontsize=8)
        ax2.tick_params(colors='gray', labelsize=8)
        ax2.spines['right'].set_color('#404060')
        
        ax.legend(loc='upper left', fontsize=7, facecolor='#2d2d44', edgecolor='#404060', labelcolor='white')
    
    def _plot_processor_loads(self, data: dict):
        """Gráfico de carga por procesador."""
        ax = self.ax_load
        loads = data['processor_loads']
        n_procs = len(loads)
        
        x = range(n_procs)
        loads_pct = [l * 100 for l in loads]
        
        colors = ['#e74c3c' if l > 80 else '#f39c12' if l > 50 else '#2ecc71' if l > 20 else '#3498db' 
                 for l in loads_pct]
        
        ax.bar(x, loads_pct, color=colors, alpha=0.8, edgecolor='#404060', width=0.8)
        ax.set_ylim(0, 100)
        ax.set_ylabel('Carga (%)', color='white', fontsize=8)
        ax.set_xlabel('Procesador', color='gray', fontsize=8)
        
        # Mostrar solo algunas etiquetas si hay muchos procesadores
        if n_procs > 32:
            step = max(1, n_procs // 16)
            ax.set_xticks([i for i in range(0, n_procs, step)])
            ax.set_xticklabels([f'P{i}' for i in range(0, n_procs, step)], fontsize=6)
        elif n_procs > 16:
            ax.set_xticks(x[::2])
            ax.set_xticklabels([f'P{i}' for i in x[::2]], fontsize=7)
        else:
            ax.set_xticks(x)
            ax.set_xticklabels([f'P{i}' for i in x], fontsize=7)
    
    def _plot_processor_energy(self, data: dict):
        """Gráfico de energía por procesador."""
        ax = self.ax_proc_energy
        energies = data['processor_energies']
        n_procs = len(energies)
        
        x = range(n_procs)
        
        ax.bar(x, energies, color='#f39c12', alpha=0.8, edgecolor='#404060', width=0.8)
        ax.set_ylabel('Energía (J)', color='white', fontsize=8)
        ax.set_xlabel('Procesador', color='gray', fontsize=8)
        
        # Etiquetas según número de procesadores
        if n_procs > 32:
            step = max(1, n_procs // 16)
            ax.set_xticks([i for i in range(0, n_procs, step)])
            ax.set_xticklabels([f'P{i}' for i in range(0, n_procs, step)], fontsize=6)
        elif n_procs > 16:
            ax.set_xticks(x[::2])
            ax.set_xticklabels([f'P{i}' for i in x[::2]], fontsize=7)
        else:
            ax.set_xticks(x)
            ax.set_xticklabels([f'P{i}' for i in x], fontsize=7)
    
    def clear_plots(self):
        """Limpia todos los gráficos."""
        for ax in [self.ax_energy, self.ax_perf, self.ax_load, self.ax_proc_energy]:
            ax.clear()
            self._configure_axis(ax, '')
        self.canvas.draw()