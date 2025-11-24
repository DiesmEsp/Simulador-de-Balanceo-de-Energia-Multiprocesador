"""
Widgets reutilizables para la GUI.
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, List
import math


class NumericEntry(ttk.Entry):
    """Entry que solo acepta números sin ceros a la izquierda."""
    
    def __init__(self, master, min_val=1, max_val=1000, **kwargs):
        self.var = tk.StringVar()
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(master, textvariable=self.var, **kwargs)
        self.var.trace_add('write', self._validate)
        self.var.set(str(min_val))
    
    def _validate(self, *args):
        value = self.var.get()
        cleaned = ''.join(c for c in value if c.isdigit())
        cleaned = cleaned.lstrip('0') or '0'
        
        try:
            num = int(cleaned)
            if num < self.min_val:
                cleaned = str(self.min_val)
            elif num > self.max_val:
                cleaned = str(self.max_val)
        except ValueError:
            cleaned = str(self.min_val)
        
        if cleaned != value:
            self.var.set(cleaned)
    
    def get_value(self) -> int:
        try:
            return int(self.var.get())
        except ValueError:
            return self.min_val
    
    def set_value(self, val: int):
        self.var.set(str(val))


class ProcessorGrid(ttk.Frame):
    """Grid scrollable de procesadores con soporte para cantidad ilimitada."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.processors = []
        self.n_processors = 0
        self._create_widgets()
    
    def _create_widgets(self):
        # Canvas con scrollbars
        self.canvas = tk.Canvas(self, bg='#1a1a2e', highlightthickness=0, height=400)
        
        # Scrollbars
        self.scrollbar_y = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        
        # Frame interior que contendrá los procesadores
        self.inner_frame = ttk.Frame(self.canvas)
        
        # Configurar canvas
        self.canvas.configure(
            yscrollcommand=self.scrollbar_y.set,
            xscrollcommand=self.scrollbar_x.set
        )
        
        # Layout
        self.scrollbar_y.pack(side='right', fill='y')
        self.scrollbar_x.pack(side='bottom', fill='x')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Crear ventana en canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.inner_frame, 
            anchor='nw'
        )
        
        # Bindings para actualizar scroll region
        self.inner_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Binding para scroll con mouse wheel
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
    
    def _on_frame_configure(self, event=None):
        """Actualiza el scroll region cuando cambia el frame interior."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Ajusta el ancho del frame interior al ancho del canvas."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _on_mousewheel(self, event):
        """Maneja el scroll con la rueda del mouse."""
        if self.canvas.winfo_containing(event.x_root, event.y_root) == self.canvas:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_processors(self, n: int):
        """Configura el número de procesadores a visualizar."""
        if n == self.n_processors:
            return  # No hacer nada si es el mismo número
        
        self.n_processors = n
        
        # Limpiar procesadores existentes
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.processors = []
        
        # Calcular layout - máximo 16 columnas
        cols = min(16, n)
        rows = math.ceil(n / cols)
        
        # Crear cada procesador
        for i in range(n):
            row = i // cols
            col = i % cols
            
            proc_frame = self._create_processor_widget(i)
            proc_frame.grid(row=row, column=col, padx=3, pady=3, sticky='n')
            
            self.processors.append(proc_frame)
        
        # Actualizar scroll region
        self.inner_frame.update_idletasks()
        self._on_frame_configure()
    
    def _create_processor_widget(self, proc_id: int):
        """Crea el widget de un procesador individual."""
        frame = ttk.Frame(self.inner_frame, padding=2)
        
        # Label ID
        lbl_id = ttk.Label(frame, text=f"P{proc_id}", font=('Consolas', 8))
        lbl_id.pack()
        
        # Canvas para barra de carga (más pequeño para permitir más procesadores)
        bar_canvas = tk.Canvas(
            frame, 
            width=28, 
            height=45, 
            bg='#2d2d44',
            highlightthickness=1,
            highlightbackground='#404060'
        )
        bar_canvas.pack()
        
        # Barra de carga
        load_bar = bar_canvas.create_rectangle(2, 43, 26, 43, fill='#27ae60', outline='')
        
        # Label de porcentaje
        lbl_pct = ttk.Label(frame, text="0%", font=('Consolas', 7))
        lbl_pct.pack()
        
        # Guardar referencias
        frame.canvas = bar_canvas
        frame.load_bar = load_bar
        frame.lbl_pct = lbl_pct
        
        return frame
    
    def update_processor(self, idx: int, load: float, state: int, energy: float):
        """Actualiza la visualización de un procesador."""
        if idx >= len(self.processors):
            return
        
        proc_frame = self.processors[idx]
        canvas = proc_frame.canvas
        
        # Color según estado y carga
        from src.core.processor import ProcessorState
        
        if state == ProcessorState.SLEEP:
            color = '#333344'
        elif load > 0.8:
            color = '#e74c3c'
        elif load > 0.5:
            color = '#f39c12'
        elif load > 0.2:
            color = '#27ae60'
        else:
            color = '#3498db'
        
        # Actualizar barra (altura 43px)
        bar_height = max(2, int(load * 41))
        canvas.coords(proc_frame.load_bar, 2, 43 - bar_height, 26, 43)
        canvas.itemconfig(proc_frame.load_bar, fill=color)
        
        # Actualizar label
        proc_frame.lbl_pct.config(text=f"{int(load*100)}%")
    
    def clear(self):
        """Limpia todos los procesadores."""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.processors = []
        self.n_processors = 0


class MetricsPanel(ttk.LabelFrame):
    """Panel de métricas en tiempo real."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, text="📊 Métricas en Tiempo Real", **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        # Variables
        self.metrics = {
            'time': tk.StringVar(value="0"),
            'tasks': tk.StringVar(value="0 / 0"),
            'energy': tk.StringVar(value="0.0 J"),
            'power': tk.StringVar(value="0.0 W"),
            'efficiency': tk.StringVar(value="0.0000"),
            'load': tk.StringVar(value="0.0%"),
            'active_procs': tk.StringVar(value="0"),
        }
        
        metrics_data = [
            ('time', '⏱️ Tiempo:'),
            ('tasks', '✅ Tareas:'),
            ('energy', '⚡ Energía:'),
            ('power', '🔌 Potencia:'),
            ('efficiency', '📈 Eficiencia:'),
            ('load', '📉 Carga Media:'),
            ('active_procs', '🖥️ Procesadores Activos:'),
        ]
        
        for i, (key, label) in enumerate(metrics_data):
            row = ttk.Frame(self)
            row.pack(fill='x', pady=2, padx=5)
            
            ttk.Label(row, text=label, width=22, font=('Arial', 9)).pack(side='left')
            ttk.Label(
                row, 
                textvariable=self.metrics[key],
                font=('Arial', 10, 'bold'),
                foreground='#3498db'
            ).pack(side='right')
    
    def update_metrics(self, state_dict: dict):
        """Actualiza las métricas mostradas."""
        self.metrics['time'].set(f"{state_dict.get('current_time', 0):.1f}")
        self.metrics['tasks'].set(
            f"{state_dict.get('completed_tasks', 0)} / {state_dict.get('total_tasks', 0)}"
        )
        self.metrics['energy'].set(f"{state_dict.get('total_energy', 0):.1f} J")
        self.metrics['power'].set(f"{state_dict.get('instant_power', 0):.1f} W")
        
        energy = state_dict.get('total_energy', 0)
        completed = state_dict.get('completed_tasks', 0)
        if energy > 0 and completed > 0:
            eff = completed / energy
            self.metrics['efficiency'].set(f"{eff:.4f} t/J")
        
        avg_load = state_dict.get('avg_load', 0)
        self.metrics['load'].set(f"{avg_load:.1f}%")
        
        active = state_dict.get('active_processors', 0)
        total = state_dict.get('total_processors', 0)
        self.metrics['active_procs'].set(f"{active} / {total}")


class ControlPanel(ttk.LabelFrame):
    """Panel de controles de configuración."""
    
    def __init__(self, master, callbacks: dict, **kwargs):
        super().__init__(master, text="🎛️ Configuración", **kwargs)
        self.callbacks = callbacks
        self._create_widgets()
    
    def _create_widgets(self):
        # Número de procesadores
        ttk.Label(self, text="Procesadores:").pack(anchor='w', padx=5, pady=(5, 0))
        self.n_procs_entry = NumericEntry(self, min_val=1, max_val=512, width=15)
        self.n_procs_entry.set_value(8)
        self.n_procs_entry.pack(fill='x', padx=5, pady=(0, 10))
        
        # Estrategia
        ttk.Label(self, text="Estrategia:").pack(anchor='w', padx=5)
        self.strategy_var = tk.StringVar(value='dvfs')
        self.strategy_combo = ttk.Combobox(
            self,
            textvariable=self.strategy_var,
            state='readonly',
            width=18
        )
        self.strategy_combo['values'] = ['performance', 'energy', 'dvfs']
        self.strategy_combo.pack(fill='x', padx=5, pady=(0, 10))
        
        # Escenario
        ttk.Label(self, text="Escenario:").pack(anchor='w', padx=5)
        self.scenario_var = tk.StringVar(value='default')
        self.scenario_combo = ttk.Combobox(
            self,
            textvariable=self.scenario_var,
            state='readonly',
            width=18
        )
        self.scenario_combo['values'] = [
            'default',
            'high_load',
            'intermittent',
            'unexpected_burst'
        ]
        self.scenario_combo.pack(fill='x', padx=5, pady=(0, 10))
        
        # Total de tareas
        ttk.Label(self, text="Total de Tareas:").pack(anchor='w', padx=5)
        self.tasks_entry = NumericEntry(self, min_val=1, max_val=10000, width=15)
        self.tasks_entry.set_value(100)
        self.tasks_entry.pack(fill='x', padx=5, pady=(0, 10))
        
        # Velocidad
        ttk.Label(self, text="Velocidad:").pack(anchor='w', padx=5)
        speed_frame = ttk.Frame(self)
        speed_frame.pack(fill='x', padx=5, pady=(0, 10))
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(
            speed_frame,
            from_=0.5,
            to=10.0,
            variable=self.speed_var,
            orient='horizontal'
        )
        self.speed_scale.pack(side='left', fill='x', expand=True)
        
        self.speed_label = ttk.Label(speed_frame, text="1.0x", width=5)
        self.speed_label.pack(side='right')
        self.speed_var.trace_add(
            'write',
            lambda *_: self.speed_label.config(text=f"{self.speed_var.get():.1f}x")
        )
        
        # Botones de control
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=5, pady=(10, 5))
        
        self.start_btn = ttk.Button(
            btn_frame,
            text="▶ Iniciar",
            command=self.callbacks.get('on_start')
        )
        self.start_btn.pack(fill='x', pady=2)
        
        self.pause_btn = ttk.Button(
            btn_frame,
            text="⏸ Pausar",
            command=self.callbacks.get('on_pause'),
            state='disabled'
        )
        self.pause_btn.pack(fill='x', pady=2)
        
        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹ Detener",
            command=self.callbacks.get('on_stop'),
            state='disabled'
        )
        self.stop_btn.pack(fill='x', pady=2)
    
    def set_running(self, running: bool):
        """Actualiza el estado de los controles."""
        state = 'disabled' if running else 'normal'
        
        self.n_procs_entry.config(state=state)
        self.strategy_combo.config(state=state)
        self.scenario_combo.config(state=state)
        self.tasks_entry.config(state=state)
        
        if running:
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='normal')
            self.stop_btn.config(state='normal')
        else:
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.stop_btn.config(state='disabled')
    
    def get_config(self) -> dict:
        """Retorna la configuración actual."""
        scenario = self.scenario_var.get()
        return {
            'n_processors': self.n_procs_entry.get_value(),
            'strategy': self.strategy_var.get(),
            'scenario': None if scenario == 'default' else scenario,
            'total_tasks': self.tasks_entry.get_value(),
            'speed': self.speed_var.get()
        }