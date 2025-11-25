"""
Interfaz gráfica principal del simulador usando Tkinter.
Proporciona controles interactivos y visualización en tiempo real.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime

# Importar módulos del simulador
from simulator import Simulator
from report_generator import ReportGenerator


class SimulatorGUI:
    """
    Interfaz gráfica principal del simulador de balanceo de energía.
    """
    
    def __init__(self, root):
        """
        Inicializa la interfaz gráfica.
        
        Args:
            root: Ventana principal de Tkinter
        """
        self.root = root
        self.root.title("Simulador de Balanceo de Energía - Sistema Multiprocesador")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e293b')
        
        # Variables de estado
        self.simulator = None
        self.is_running = False
        self.is_paused = False
        self.simulation_thread = None
        self.update_interval = 100  # ms
        
        # Variables de configuración
        self.num_processors = tk.IntVar(value=4)
        self.num_tasks = tk.IntVar(value=20)
        self.scenario = tk.StringVar(value='high_cpu')
        self.strategy = tk.StringVar(value='balanced')
        
        # Datos de visualización
        self.processor_frames = []
        self.processor_labels = {}
        self.progress_var = tk.DoubleVar(value=0)
        
        # Crear interfaz
        self._create_widgets()
        
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # Frame principal con scroll
        main_container = tk.Frame(self.root, bg='#1e293b')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === SECCIÓN: TÍTULO ===
        self._create_header(main_container)
        
        # === SECCIÓN: CONFIGURACIÓN ===
        self._create_configuration_panel(main_container)
        
        # === SECCIÓN: CONTROLES ===
        self._create_control_panel(main_container)
        
        # === SECCIÓN: MÉTRICAS GLOBALES ===
        self._create_metrics_panel(main_container)
        
        # === SECCIÓN: PROCESADORES ===
        self._create_processors_panel(main_container)
        
        # === SECCIÓN: REPORTE ===
        self._create_report_panel(main_container)
        
    def _create_header(self, parent):
        """Crea el encabezado de la aplicación."""
        header_frame = tk.Frame(parent, bg='#0f172a', relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="🖥️ Simulador de Balanceo de Energía",
            font=('Arial', 24, 'bold'),
            bg='#0f172a',
            fg='#38bdf8'
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Sistema Multiprocesador con Gestión Energética Dinámica",
            font=('Arial', 12),
            bg='#0f172a',
            fg='#94a3b8'
        )
        subtitle_label.pack(pady=(0, 10))
        
    def _create_configuration_panel(self, parent):
        """Crea el panel de configuración."""
        config_frame = tk.LabelFrame(
            parent,
            text="⚙️ Configuración",
            font=('Arial', 12, 'bold'),
            bg='#334155',
            fg='#f1f5f9',
            relief=tk.RIDGE,
            bd=2
        )
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid de configuración
        config_grid = tk.Frame(config_frame, bg='#334155')
        config_grid.pack(padx=20, pady=15)
        
        # Fila 1: Procesadores y Tareas
        tk.Label(
            config_grid,
            text="Procesadores:",
            font=('Arial', 10, 'bold'),
            bg='#334155',
            fg='#e2e8f0'
        ).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        processors_spinbox = tk.Spinbox(
            config_grid,
            from_=2,
            to=16,
            textvariable=self.num_processors,
            width=10,
            font=('Arial', 10),
            state='readonly'
        )
        processors_spinbox.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(
            config_grid,
            text="Tareas:",
            font=('Arial', 10, 'bold'),
            bg='#334155',
            fg='#e2e8f0'
        ).grid(row=0, column=2, sticky='w', padx=10, pady=5)
        
        tasks_spinbox = tk.Spinbox(
            config_grid,
            from_=5,
            to=200,
            textvariable=self.num_tasks,
            width=10,
            font=('Arial', 10),
            state='readonly'
        )
        tasks_spinbox.grid(row=0, column=3, padx=10, pady=5)
        
        # Fila 2: Escenario
        tk.Label(
            config_grid,
            text="Escenario:",
            font=('Arial', 10, 'bold'),
            bg='#334155',
            fg='#e2e8f0'
        ).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        scenario_combo = ttk.Combobox(
            config_grid,
            textvariable=self.scenario,
            values=[
                ('high_cpu', 'Alta carga CPU'),
                ('intermittent', 'Carga intermitente'),
                ('heterogeneous', 'Núcleos heterogéneos'),
                ('spike', 'Picos inesperados')
            ],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        scenario_combo['values'] = [
            'Alta carga CPU',
            'Carga intermitente',
            'Núcleos heterogéneos',
            'Picos inesperados'
        ]
        scenario_combo.current(0)
        scenario_combo.grid(row=1, column=1, columnspan=3, sticky='w', padx=10, pady=5)
        
        # Fila 3: Estrategia
        tk.Label(
            config_grid,
            text="Estrategia:",
            font=('Arial', 10, 'bold'),
            bg='#334155',
            fg='#e2e8f0'
        ).grid(row=2, column=0, sticky='w', padx=10, pady=5)
        
        strategy_combo = ttk.Combobox(
            config_grid,
            textvariable=self.strategy,
            values=[
                'Performance-first',
                'Energy-first',
                'Balanceado (DVFS)'
            ],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        strategy_combo.current(2)
        strategy_combo.grid(row=2, column=1, columnspan=3, sticky='w', padx=10, pady=5)
        
        # Mapeo de valores para comboboxes
        self.scenario_map = {
            'Alta carga CPU': 'high_cpu',
            'Carga intermitente': 'intermittent',
            'Núcleos heterogéneos': 'heterogeneous',
            'Picos inesperados': 'spike'
        }
        
        self.strategy_map = {
            'Performance-first': 'performance',
            'Energy-first': 'energy',
            'Balanceado (DVFS)': 'balanced'
        }
        
    def _create_control_panel(self, parent):
        """Crea el panel de controles."""
        control_frame = tk.Frame(parent, bg='#1e293b')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Botones de control
        self.start_button = tk.Button(
            control_frame,
            text="▶ Iniciar Simulación",
            command=self.start_simulation,
            font=('Arial', 12, 'bold'),
            bg='#10b981',
            fg='white',
            activebackground='#059669',
            width=20,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(
            control_frame,
            text="⏸ Pausar",
            command=self.pause_simulation,
            font=('Arial', 12, 'bold'),
            bg='#f59e0b',
            fg='white',
            activebackground='#d97706',
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = tk.Button(
            control_frame,
            text="🔄 Reiniciar",
            command=self.reset_simulation,
            font=('Arial', 12, 'bold'),
            bg='#ef4444',
            fg='white',
            activebackground='#dc2626',
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.export_csv_button = tk.Button(
            control_frame,
            text="💾 Exportar CSV",
            command=self.export_csv,
            font=('Arial', 12, 'bold'),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.export_csv_button.pack(side=tk.RIGHT, padx=5)
        
        self.export_pdf_button = tk.Button(
            control_frame,
            text="📄 Exportar PDF",
            command=self.export_pdf,
            font=('Arial', 12, 'bold'),
            bg='#8b5cf6',
            fg='white',
            activebackground='#7c3aed',
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.export_pdf_button.pack(side=tk.RIGHT, padx=5)
        
    def _create_metrics_panel(self, parent):
        """Crea el panel de métricas globales."""
        metrics_frame = tk.LabelFrame(
            parent,
            text="📊 Métricas Globales",
            font=('Arial', 12, 'bold'),
            bg='#334155',
            fg='#f1f5f9',
            relief=tk.RIDGE,
            bd=2
        )
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid de métricas
        metrics_grid = tk.Frame(metrics_frame, bg='#334155')
        metrics_grid.pack(padx=20, pady=15)
        
        # Métricas individuales
        self.time_label = self._create_metric_box(
            metrics_grid, "⏱️ Tiempo Total", "0.0", 0, 0
        )
        self.energy_label = self._create_metric_box(
            metrics_grid, "⚡ Energía Total", "0.0 J", 0, 1
        )
        self.completed_label = self._create_metric_box(
            metrics_grid, "✅ Completadas", "0 / 0", 0, 2
        )
        self.efficiency_label = self._create_metric_box(
            metrics_grid, "📈 Eficiencia", "0.000", 0, 3
        )
        
        # Barra de progreso
        progress_frame = tk.Frame(metrics_frame, bg='#334155')
        progress_frame.pack(fill=tk.X, padx=20, pady=(10, 15))
        
        tk.Label(
            progress_frame,
            text="Progreso General:",
            font=('Arial', 10, 'bold'),
            bg='#334155',
            fg='#e2e8f0'
        ).pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=1000,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0.0%",
            font=('Arial', 10),
            bg='#334155',
            fg='#94a3b8'
        )
        self.progress_label.pack()
        
    def _create_metric_box(self, parent, title, value, row, col):
        """Crea una caja de métrica individual."""
        box = tk.Frame(parent, bg='#475569', relief=tk.RAISED, bd=2)
        box.grid(row=row, column=col, padx=10, pady=5, sticky='nsew')
        
        tk.Label(
            box,
            text=title,
            font=('Arial', 9),
            bg='#475569',
            fg='#cbd5e1'
        ).pack(pady=(8, 2))
        
        value_label = tk.Label(
            box,
            text=value,
            font=('Arial', 14, 'bold'),
            bg='#475569',
            fg='#f1f5f9'
        )
        value_label.pack(pady=(2, 8))
        
        return value_label
        
    def _create_processors_panel(self, parent):
        """Crea el panel de procesadores."""
        processors_container = tk.LabelFrame(
            parent,
            text="💻 Estado de Procesadores",
            font=('Arial', 12, 'bold'),
            bg='#334155',
            fg='#f1f5f9',
            relief=tk.RIDGE,
            bd=2
        )
        processors_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Canvas con scroll para procesadores
        canvas = tk.Canvas(processors_container, bg='#334155', highlightthickness=0)
        scrollbar = tk.Scrollbar(processors_container, orient=tk.VERTICAL, command=canvas.yview)
        self.processors_frame = tk.Frame(canvas, bg='#334155')
        
        self.processors_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.processors_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_report_panel(self, parent):
        """Crea el panel de reporte."""
        self.report_frame = tk.LabelFrame(
            parent,
            text="📋 Reporte Final",
            font=('Arial', 12, 'bold'),
            bg='#334155',
            fg='#f1f5f9',
            relief=tk.RIDGE,
            bd=2
        )
        # Se mostrará solo al finalizar
        
    def start_simulation(self):
        """Inicia la simulación."""
        if self.is_running:
            return
            
        # Obtener configuración
        num_proc = self.num_processors.get()
        num_task = self.num_tasks.get()
        scen = self.scenario_map.get(self.scenario.get(), 'high_cpu')
        strat = self.strategy_map.get(self.strategy.get(), 'balanced')
        
        # Crear simulador
        self.simulator = Simulator(num_proc, num_task, scen, strat)
        
        # Actualizar UI
        self.is_running = True
        self.is_paused = False
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL, text="⏸ Pausar")
        self.export_csv_button.config(state=tk.DISABLED)
        self.export_pdf_button.config(state=tk.DISABLED)
        
        # Crear visualización de procesadores
        self._create_processor_widgets(num_proc)
        
        # Iniciar thread de simulación
        self.simulation_thread = threading.Thread(target=self._run_simulation, daemon=True)
        self.simulation_thread.start()
        
        # Iniciar actualización de UI
        self._update_ui()
        
    def pause_simulation(self):
        """Pausa o reanuda la simulación."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="▶ Reanudar")
        else:
            self.pause_button.config(text="⏸ Pausar")
            
    def reset_simulation(self):
        """Reinicia la simulación."""
        self.is_running = False
        self.is_paused = False
        
        if self.simulator:
            self.simulator.reset()
        
        # Limpiar visualización
        for widget in self.processors_frame.winfo_children():
            widget.destroy()
        self.processor_frames = []
        self.processor_labels = {}
        
        # Resetear métricas
        self.progress_var.set(0)
        self.progress_label.config(text="0.0%")
        self.time_label.config(text="0.0")
        self.energy_label.config(text="0.0 J")
        self.completed_label.config(text="0 / 0")
        self.efficiency_label.config(text="0.000")
        
        # Resetear botones
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.export_csv_button.config(state=tk.DISABLED)
        self.export_pdf_button.config(state=tk.DISABLED)
        
        # Ocultar reporte si existe
        if hasattr(self, 'report_frame'):
            self.report_frame.pack_forget()
            
    def _run_simulation(self):
        """Ejecuta la simulación en un thread separado."""
        while self.is_running and self.simulator:
            if not self.is_paused:
                completed = self.simulator.step()
                
                if completed:
                    self.is_running = False
                    self.root.after(0, self._simulation_completed)
                    break
                    
            time.sleep(0.1)
            
    def _update_ui(self):
        """Actualiza la interfaz con datos de la simulación."""
        if not self.is_running or not self.simulator:
            return
            
        # Obtener estado
        state = self.simulator.get_state()
        
        # Actualizar métricas globales
        self.time_label.config(text=f"{state['total_time']:.1f}")
        self.energy_label.config(text=f"{state['total_energy']:.1f} J")
        self.completed_label.config(
            text=f"{state['completed_tasks']} / {state['total_tasks']}"
        )
        
        if state['total_energy'] > 0:
            efficiency = state['completed_tasks'] / state['total_energy']
            self.efficiency_label.config(text=f"{efficiency:.3f}")
        
        # Actualizar progreso
        progress = (state['completed_tasks'] / state['total_tasks']) * 100
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.1f}%")
        
        # Actualizar procesadores
        for i, proc in enumerate(state['processors']):
            if i < len(self.processor_labels):
                labels = self.processor_labels[i]
                labels['freq'].config(text=f"{proc['frequency']:.2f} GHz")
                labels['load'].config(text=f"{proc['load']*100:.1f}%")
                labels['energy'].config(text=f"{proc['energy']:.1f} J")
                labels['time'].config(text=f"{proc['execution_time']:.1f}")
                labels['completed'].config(text=str(proc['completed_tasks']))
                labels['active'].config(text=str(proc['active_tasks']))
                
                # Actualizar barra de carga
                labels['load_bar']['value'] = proc['load'] * 100
                
                # Color según carga
                if proc['load'] > 0.7:
                    labels['load_bar'].config(style='Red.Horizontal.TProgressbar')
                elif proc['load'] > 0.4:
                    labels['load_bar'].config(style='Yellow.Horizontal.TProgressbar')
                else:
                    labels['load_bar'].config(style='Green.Horizontal.TProgressbar')
        
        # Continuar actualizando
        if self.is_running:
            self.root.after(self.update_interval, self._update_ui)
            
    def _create_processor_widgets(self, num_processors):
        """Crea widgets para visualizar procesadores."""
        # Limpiar widgets anteriores
        for widget in self.processors_frame.winfo_children():
            widget.destroy()
        self.processor_labels = {}
        
        # Configurar estilos de barras de progreso
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Green.Horizontal.TProgressbar', background='#10b981')
        style.configure('Yellow.Horizontal.TProgressbar', background='#f59e0b')
        style.configure('Red.Horizontal.TProgressbar', background='#ef4444')
        
        # Crear grid de procesadores (2 columnas)
        cols = 2
        for i in range(num_processors):
            row = i // cols
            col = i % cols
            
            proc_frame = tk.Frame(
                self.processors_frame,
                bg='#475569',
                relief=tk.RAISED,
                bd=3
            )
            proc_frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            # Título del procesador
            title = tk.Label(
                proc_frame,
                text=f"Procesador {i}",
                font=('Arial', 11, 'bold'),
                bg='#475569',
                fg='#38bdf8'
            )
            title.pack(pady=(8, 5))
            
            # Información del procesador
            info_frame = tk.Frame(proc_frame, bg='#475569')
            info_frame.pack(padx=10, pady=5, fill=tk.X)
            
            labels = {}
            
            # Frecuencia
            self._add_info_row(info_frame, "Frecuencia:", "2.5 GHz", labels, 'freq', 0)
            
            # Carga con barra
            load_frame = tk.Frame(info_frame, bg='#475569')
            load_frame.grid(row=1, column=0, columnspan=2, pady=2, sticky='ew')
            tk.Label(
                load_frame,
                text="Carga:",
                font=('Arial', 9),
                bg='#475569',
                fg='#cbd5e1'
            ).pack(side=tk.LEFT)
            labels['load'] = tk.Label(
                load_frame,
                text="0.0%",
                font=('Arial', 9, 'bold'),
                bg='#475569',
                fg='#f1f5f9'
            )
            labels['load'].pack(side=tk.RIGHT)
            
            labels['load_bar'] = ttk.Progressbar(
                info_frame,
                maximum=100,
                length=200,
                mode='determinate',
                style='Green.Horizontal.TProgressbar'
            )
            labels['load_bar'].grid(row=2, column=0, columnspan=2, pady=2, sticky='ew')
            
            # Energía
            self._add_info_row(info_frame, "Energía:", "0.0 J", labels, 'energy', 3)
            
            # Tiempo
            self._add_info_row(info_frame, "Tiempo:", "0.0", labels, 'time', 4)
            
            # Tareas completadas
            self._add_info_row(info_frame, "Completadas:", "0", labels, 'completed', 5)
            
            # Tareas activas
            self._add_info_row(info_frame, "Activas:", "0", labels, 'active', 6)
            
            self.processor_labels[i] = labels
            
    def _add_info_row(self, parent, label_text, value_text, labels_dict, key, row):
        """Añade una fila de información."""
        tk.Label(
            parent,
            text=label_text,
            font=('Arial', 9),
            bg='#475569',
            fg='#cbd5e1'
        ).grid(row=row, column=0, sticky='w', pady=2)
        
        labels_dict[key] = tk.Label(
            parent,
            text=value_text,
            font=('Arial', 9, 'bold'),
            bg='#475569',
            fg='#f1f5f9'
        )
        labels_dict[key].grid(row=row, column=1, sticky='e', pady=2)
        
    def _simulation_completed(self):
        """Maneja la finalización de la simulación."""
        messagebox.showinfo(
            "Simulación Completada",
            "¡La simulación ha finalizado exitosamente!\n\n"
            "Puede exportar los resultados en CSV o PDF."
        )
        
        self.pause_button.config(state=tk.DISABLED)
        self.export_csv_button.config(state=tk.NORMAL)
        self.export_pdf_button.config(state=tk.NORMAL)
        
    def export_csv(self):
        """Exporta resultados a CSV."""
        if not self.simulator:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            generator = ReportGenerator(self.simulator)
            generator.export_csv(filename)
            messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filename}")
            
    def export_pdf(self):
        """Exporta resultados a PDF."""
        if not self.simulator:
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if filename:
            generator = ReportGenerator(self.simulator)
            generator.export_pdf(filename)
            messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filename}")


def main():
    """Función principal."""
    root = tk.Tk()
    app = SimulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()