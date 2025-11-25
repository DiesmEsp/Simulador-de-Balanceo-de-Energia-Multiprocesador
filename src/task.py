"""
Módulo para la gestión de tareas en el simulador.
Define la clase Task y métodos para generar tareas según diferentes escenarios.
"""

from random import random, randint


class Task:
    """
    Representa una tarea a ser ejecutada en el sistema multiprocesador.
    
    Attributes:
        task_id (int): Identificador único de la tarea
        duration (float): Duración base de la tarea en unidades de tiempo
        remaining (float): Tiempo restante para completar la tarea
        intensity (float): Intensidad computacional (0.0-1.0)
        assigned (bool): Indica si la tarea está asignada a un procesador
        completed (bool): Indica si la tarea fue completada
        processor_id (int): ID del procesador asignado (None si no está asignada)
        arrival_time (float): Tiempo en que la tarea llega al sistema
    """
    
    def __init__(self, task_id, duration, intensity, arrival_time=0):
        """
        Inicializa una nueva tarea.
        
        Args:
            task_id (int): Identificador único
            duration (float): Duración de la tarea
            intensity (float): Intensidad computacional (0.0-1.0)
            arrival_time (float): Tiempo de llegada al sistema
        """
        self.task_id = task_id
        self.duration = duration
        self.remaining = duration
        self.intensity = intensity
        self.assigned = False
        self.completed = False
        self.processor_id = None
        self.arrival_time = arrival_time
        self.start_time = None
        self.completion_time = None
    
    def assign_to_processor(self, processor_id):
        """
        Asigna la tarea a un procesador específico.
        
        Args:
            processor_id (int): ID del procesador
        """
        self.assigned = True
        self.processor_id = processor_id
    
    def update_progress(self, work_done):
        """
        Actualiza el progreso de la tarea.
        
        Args:
            work_done (float): Cantidad de trabajo realizado en este paso
            
        Returns:
            bool: True si la tarea se completó, False en caso contrario
        """
        self.remaining -= work_done
        
        if self.remaining <= 0:
            self.completed = True
            self.remaining = 0
            return True
        return False
    
    def get_progress_percentage(self):
        """
        Calcula el porcentaje de progreso de la tarea.
        
        Returns:
            float: Porcentaje completado (0-100)
        """
        if self.duration == 0:
            return 100.0
        return ((self.duration - self.remaining) / self.duration) * 100
    
    def reset(self):
        """Reinicia la tarea a su estado inicial."""
        self.remaining = self.duration
        self.assigned = False
        self.completed = False
        self.processor_id = None
        self.start_time = None
        self.completion_time = None
    
    def __repr__(self):
        return (f"Task(id={self.task_id}, duration={self.duration:.2f}, "
                f"intensity={self.intensity:.2f}, completed={self.completed})")


class TaskGenerator:
    """
    Generador de tareas para diferentes escenarios de carga.
    """
    
    @staticmethod
    def generate_tasks(num_tasks, scenario='high_cpu'):
        """
        Genera un conjunto de tareas según el escenario especificado.
        
        Args:
            num_tasks (int): Número de tareas a generar
            scenario (str): Tipo de escenario de carga
                - 'high_cpu': Alta carga CPU constante
                - 'intermittent': Carga intermitente (mix CPU-bound/IO-bound)
                - 'heterogeneous': Tareas variadas
                - 'spike': Picos de carga repentinos
        
        Returns:
            list: Lista de objetos Task
        """
        tasks = []
        
        for i in range(num_tasks):
            if scenario == 'high_cpu':
                # Procesos CPU-bound intensivos
                duration = 50 + random() * 100
                intensity = 0.8 + random() * 0.2
                arrival = i * 2  # Llegada espaciada
                
            elif scenario == 'intermittent':
                # Mezcla de CPU-bound e I/O-bound
                if random() > 0.5:
                    # CPU-bound
                    duration = 60 + random() * 80
                    intensity = 0.85 + random() * 0.15
                else:
                    # I/O-bound (menor intensidad)
                    duration = 30 + random() * 50
                    intensity = 0.2 + random() * 0.3
                arrival = i * 3
                
            elif scenario == 'heterogeneous':
                # Tareas muy variadas
                duration = 20 + random() * 150
                intensity = 0.3 + random() * 0.7
                arrival = i * 2.5
                
            elif scenario == 'spike':
                # Picos de procesos inesperados
                if i < num_tasks * 0.3:
                    # Carga normal al inicio
                    duration = 40 + random() * 60
                    intensity = 0.5 + random() * 0.3
                    arrival = i * 5
                else:
                    # Pico repentino
                    duration = 50 + random() * 70
                    intensity = 0.7 + random() * 0.3
                    arrival = num_tasks * 0.3 * 5 + (i - num_tasks * 0.3) * 0.5
            else:
                # Por defecto: carga balanceada
                duration = 50 + random() * 80
                intensity = 0.5 + random() * 0.5
                arrival = i * 3
            
            task = Task(
                task_id=i,
                duration=duration,
                intensity=intensity,
                arrival_time=arrival
            )
            tasks.append(task)
        
        return tasks
    
    @staticmethod
    def generate_custom_task(duration, intensity, arrival_time=0):
        """
        Genera una tarea personalizada.
        
        Args:
            duration (float): Duración de la tarea
            intensity (float): Intensidad computacional
            arrival_time (float): Tiempo de llegada
            
        Returns:
            Task: Nueva tarea personalizada
        """
        return Task(
            task_id=-1,  # ID temporal
            duration=duration,
            intensity=intensity,
            arrival_time=arrival_time
        )