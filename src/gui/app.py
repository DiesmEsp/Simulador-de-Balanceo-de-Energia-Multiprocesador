"""
Interfaz gráfica principal del simulador.
Integra todos los componentes modulares.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
from typing import Optional
from dataclasses import dataclass, field
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.simulation.engine import SimulationEngine, SimulationConfig, SimulationResults
from src.utils.config import build_simulation_config
from src.core.processor import ProcessorState

# Importar widgets
from .widgets import NumericEntry, ProcessorGrid, MetricsPanel, ControlPanel
from .charts import StatisticsCharts


@dataclass
class GUIState:
    """Estado compartido de la simulación."""
    running: bool = False
    paused: bool = False
    current_time: float = 0.0
    total_energy: float = 0.0
    completed_tasks: int = 0
    total_tasks: int = 0
    instant_power: float = 0.0
    avg_load: float = 0.0
    active_processors: int = 0
    total_processors: int = 0
    processor_loads: list = field(default_factory=list)
    processor_states: list = field(default_factory=list)
    processor_energies: list = field(default_factory=list)
    time_history: list = field(default_factory=list)
    power_history: list = field(default_factory=list)
    energy_history: list = field(default_factory=list)
    load_history: list = field(default_factory=list)
    completed_history: list = field(default_factory=list)


class SimulatorGUI:
    """Aplicación principal del simulador."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("⚡ Simulador de Balanceo de Energía en Multiprocesador")
        self.root.geometry("1400x800")
        self.root.configure(bg='#0d1117')
        
        # Estado
        self.state = GUIState()
        self.engine: Optional[SimulationEngine] = None
        self.sim_thread: Optional[threading.Thread] = None
        self.update_queue = queue.Queue()
        
        # Configurar estilo
        self._setup_style()
        
        # Crear interfaz
        self._create_widgets()
        
        # Iniciar loop de actualización
        self._schedule_update()
    
    def _setup_style(self):
        """Configura el estilo visual."""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#0d1117')
        style.configure('TLabelframe', background='#0d1117', foreground='white')
        style.configure('TLabelframe.Label', background='#0d1117', foreground='white', font=('Arial', 10, 'bold'))
        style.configure('TLabel', background='#0d1117', foreground='white')
        style.configure('TButton', padding=6, font=('Arial', 9, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 18, 'bold'), foreground='#3498db')
    
    def _create_widgets(self):
        """Crea la interfaz principal."""
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        header = ttk.Label(
            header_frame,
            text="⚡ Simulador de Balanceo de Energía en Multiprocesador",
            style='Header.TLabel'
        )
        header.pack()
        
        # Contenedor principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Panel izquierdo (controles)
        left_panel = ttk.Frame(main_frame, width=280)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Panel derecho (visualización)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Crear paneles
        self._create_left_panel(left_panel)
        self._create_right_panel(right_panel)
    
    def _create_left_panel(self, parent):
        """Crea el panel izquierdo con controles."""
        # Panel de control
        self.control_panel = ControlPanel(
            parent,
            callbacks={
                'on_start': self._start_simulation,
                'on_pause': self._toggle_pause,
                'on_stop': self._stop_simulation
            },
            padding=10
        )
        self.control_panel.pack(fill='x', pady=(0, 10))
        
        # Panel de métricas
        self.metrics_panel = MetricsPanel(parent, padding=10)
        self.metrics_panel.pack(fill='x', pady=(0, 10))
        
        # Leyenda
        legend_frame = ttk.LabelFrame(parent, text="🎨 Leyenda", padding=10)
        legend_frame.pack(fill='x')
        
        legends = [
            ('🟢 Carga baja (<50%)', None),
            ('🟡 Carga media (50-80%)', None),
            ('🔴 Carga alta (>80%)', None),
            ('⚫ En sleep', None),
        ]
        
        for text, _ in legends:
            ttk.Label(legend_frame, text=text, font=('Arial', 9)).pack(anchor='w', pady=1)
    
    def _create_right_panel(self, parent):
        """Crea el panel derecho con visualización."""
        # Barra de progreso
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Progreso: 0%")
        self.progress_label.pack(side='left')
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        # Notebook con pestañas
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # Pestaña de gráficos
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text='📊 Estadísticas')
        
        self.charts_panel = StatisticsCharts(stats_frame)
        self.charts_panel.pack(fill='both', expand=True)
        
        # Pestaña de procesadores
        procs_frame = ttk.Frame(notebook)
        notebook.add(procs_frame, text='🖥️ Procesadores')
        
        self.processor_grid = ProcessorGrid(procs_frame)
        self.processor_grid.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Listo para iniciar simulación")
        status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w'
        )
        status_bar.pack(fill='x', side='bottom', pady=(10, 0))
    
    def _start_simulation(self):
        """Inicia la simulación."""
        if self.state.running:
            return
        
        # Obtener configuración
        config_dict = self.control_panel.get_config()
        n_procs = config_dict['n_processors']
        
        # Inicializar grid de procesadores
        self.processor_grid.set_processors(n_procs)
        self.charts_panel.clear_plots()
        
        # Crear configuración de simulación
        config = build_simulation_config(
            n_processors=n_procs,
            strategy=config_dict['strategy'],
            scenario=config_dict['scenario'],
            total_tasks=config_dict['total_tasks'],
            duration=10000,  # Duración suficiente
            arrival_rate=0.8
        )
        
        # Crear engine
        self.engine = SimulationEngine(config)
        
        # Inicializar estado
        self.state = GUIState(
            running=True,
            total_tasks=config_dict['total_tasks'],
            total_processors=n_procs,
            processor_loads=[0.0] * n_procs,
            processor_states=[ProcessorState.IDLE] * n_procs,
            processor_energies=[0.0] * n_procs
        )
        
        # Actualizar UI
        self.control_panel.set_running(True)
        self.status_var.set(f"Simulación en curso - {config_dict['strategy'].upper()}")
        
        # Iniciar hilo de simulación
        speed = config_dict['speed']
        self.sim_thread = threading.Thread(
            target=self._simulation_loop,
            args=(speed,),
            daemon=True
        )
        self.sim_thread.start()
    
    def _simulation_loop(self, speed: float):
        """Loop principal de simulación."""
        max_history = 200
        
        while self.state.running:
            if self.state.paused:
                time.sleep(0.1)
                continue
            
            try:
                # Ejecutar paso
                should_continue = self.engine.step()
                
                # Actualizar estado
                system = self.engine.system
                
                self.state.current_time = self.engine.current_time
                self.state.total_energy = system.get_total_energy()
                self.state.completed_tasks = len(system.completed_tasks)
                self.state.instant_power = float(sum(system.get_instant_power()))
                
                # Cargas y estados
                loads = system.get_loads()
                states = system.get_states()
                energies = system.get_energy_per_processor()
                
                self.state.processor_loads = loads.tolist()
                self.state.processor_states = states.tolist()
                self.state.processor_energies = energies.tolist()
                self.state.avg_load = float(loads.mean()) * 100
                self.state.active_processors = int(sum(s != ProcessorState.SLEEP for s in states))
                
                # Históricos (limitar tamaño)
                self.state.time_history.append(self.state.current_time)
                self.state.power_history.append(self.state.instant_power)
                self.state.energy_history.append(self.state.total_energy)
                self.state.load_history.append(self.state.avg_load)
                self.state.completed_history.append(self.state.completed_tasks)
                
                if len(self.state.time_history) > max_history:
                    self.state.time_history.pop(0)
                    self.state.power_history.pop(0)
                    self.state.energy_history.pop(0)
                    self.state.load_history.pop(0)
                    self.state.completed_history.pop(0)
                
                # Encolar actualización
                self.update_queue.put(('update', self.state))
                
                # Verificar fin: todas las tareas completadas
                if self.state.completed_tasks >= self.state.total_tasks:
                    self.state.running = False
                    self.update_queue.put(('finished', self.engine.results))
                    break
                
                # Verificar si no quedan tareas y nada en cola
                if not should_continue and system.get_total_queue_length() == 0:
                    self.state.running = False
                    self.update_queue.put(('finished', self.engine.results))
                    break
                
                # Control de velocidad
                time.sleep(max(0.01, 0.05 / speed))
                
            except Exception as e:
                print(f"Error en simulación: {e}")
                import traceback
                traceback.print_exc()
                self.state.running = False
                break
    
    def _stop_simulation(self):
        """Detiene la simulación."""
        self.state.running = False
        self.state.paused = False
        self.control_panel.set_running(False)
        self.status_var.set("Simulación detenida")
    
    def _toggle_pause(self):
        """Pausa/reanuda la simulación."""
        self.state.paused = not self.state.paused
        status = "Pausada" if self.state.paused else "En curso"
        self.status_var.set(f"Simulación {status}")
    
    def _schedule_update(self):
        """Programa actualización de UI (30 FPS)."""
        try:
            while True:
                msg_type, data = self.update_queue.get_nowait()
                
                if msg_type == 'update':
                    self._update_ui(data)
                elif msg_type == 'finished':
                    self._on_simulation_finished(data)
        except queue.Empty:
            pass
        
        self.root.after(33, self._schedule_update)
    
    def _update_ui(self, state: GUIState):
        """Actualiza la interfaz con el nuevo estado."""
        # Métricas
        metrics_data = {
            'current_time': state.current_time,
            'completed_tasks': state.completed_tasks,
            'total_tasks': state.total_tasks,
            'total_energy': state.total_energy,
            'instant_power': state.instant_power,
            'avg_load': state.avg_load,
            'active_processors': state.active_processors,
            'total_processors': state.total_processors
        }
        self.metrics_panel.update_metrics(metrics_data)
        
        # Procesadores
        for i, (load, proc_state, energy) in enumerate(zip(
            state.processor_loads,
            state.processor_states,
            state.processor_energies
        )):
            self.processor_grid.update_processor(i, load, proc_state, energy)
        
        # Gráficos (actualizar cada 10 pasos para eficiencia)
        if int(state.current_time) % 10 == 0:
            chart_data = {
                'time_history': state.time_history,
                'power_history': state.power_history,
                'energy_history': state.energy_history,
                'load_history': state.load_history,
                'completed_history': state.completed_history,
                'processor_loads': state.processor_loads,
                'processor_energies': state.processor_energies
            }
            self.charts_panel.update_plots(chart_data)
        
        # Progreso
        if state.total_tasks > 0:
            progress = (state.completed_tasks / state.total_tasks) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"Progreso: {progress:.1f}%")
    
    def _on_simulation_finished(self, results: SimulationResults):
        """Callback cuando termina la simulación."""
        self.control_panel.set_running(False)
        self.status_var.set("Simulación completada")
        
        # Mostrar resultados
        msg = f"""✅ Simulación Completada!

📊 Resultados:
• Makespan: {results.makespan:.2f} unidades
• Tareas completadas: {results.completed_tasks}/{results.total_tasks}
• Energía total: {results.total_energy:.2f} J
• Eficiencia: {results.energy_efficiency:.6f} tareas/J
• Balance de carga: {results.load_balance_score:.2%}
• Utilización promedio: {results.utilization_avg:.2%}
• Migraciones: {results.total_migrations}
"""
        messagebox.showinfo("Resultados", msg)
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()


def main():
    """Punto de entrada."""
    app = SimulatorGUI()
    app.run()


if __name__ == '__main__':
    main()