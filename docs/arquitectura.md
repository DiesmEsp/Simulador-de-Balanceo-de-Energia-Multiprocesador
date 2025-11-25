# Arquitectura del Simulador de Balanceo de Energía

## Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Ejecución](#flujo-de-ejecución)
5. [Patrones de Diseño](#patrones-de-diseño)
6. [Estrategias Energéticas](#estrategias-energéticas)
7. [Extensibilidad](#extensibilidad)

---

## Visión General

El simulador implementa un sistema multiprocesador con gestión energética dinámica. Utiliza una arquitectura modular que separa claramente las responsabilidades entre componentes.

### Objetivos Arquitectónicos

- **Modularidad**: Componentes independientes y reutilizables
- **Extensibilidad**: Fácil adición de nuevas estrategias y escenarios
- **Mantenibilidad**: Código claro y bien documentado
- **Performance**: Simulación eficiente con actualización en tiempo real
- **Testabilidad**: Componentes fácilmente testeables

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        GUI (Tkinter)                        │
│  - Visualización en tiempo real                             │
│  - Control de simulación                                    │
│  - Exportación de reportes                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Simulator (Orquestador)                   │
│  - Coordina componentes                                     │
│  - Gestiona ciclo de vida                                   │
│  - Proporciona estado actual                                │
└───┬─────────────┬──────────────┬──────────────┬────────────┘
    │             │              │              │
    ▼             ▼              ▼              ▼
┌────────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐
│Processor│  │   Energy   │  │Scheduler │  │    Metrics   │
│  Pool   │  │  Manager   │  │          │  │  Calculator  │
└────┬───┘  └──────┬─────┘  └────┬─────┘  └──────┬───────┘
     │             │              │                │
     ▼             ▼              ▼                ▼
┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────────────┐
│Processor│  │  DVFS   │  │   Task   │  │     Report     │
│         │  │Controller│  │Generator │  │   Generator    │
└─────────┘  └─────────┘  └──────────┘  └────────────────┘
```

---

## Componentes Principales

### 1. GUI (gui.py)

**Responsabilidad**: Interfaz de usuario y visualización

**Características**:
- Interfaz gráfica con Tkinter
- Panel de configuración interactivo
- Visualización en tiempo real de procesadores
- Métricas globales con actualización dinámica
- Controles de simulación (Iniciar/Pausar/Reiniciar)
- Exportación de reportes

**Interacciones**:
- Crea y controla instancias de `Simulator`
- Ejecuta simulación en thread separado
- Actualiza UI cada 100ms
- Utiliza `ReportGenerator` para exportación

### 2. Simulator (simulator.py)

**Responsabilidad**: Orquestación de la simulación

**Características**:
- Ciclo principal de simulación
- Coordinación entre componentes
- Gestión de tiempo de simulación
- Interfaz para obtener estado y resultados

**Métodos clave**:
```python
- __init__(processors, tasks, scenario, strategy)
- step() -> bool                    # Ejecuta un paso
- run(max_steps) -> dict            # Ejecuta simulación completa
- get_state() -> dict               # Estado actual
- get_results() -> dict             # Resultados finales
- reset()                           # Reinicia simulación
```

### 3. Processor (processor.py)

**Responsabilidad**: Representación de núcleos de procesamiento

**Características**:
- Gestión de tareas activas
- Cálculo de carga dinámica
- Consumo energético basado en frecuencia
- Métricas de utilización y eficiencia

**Ecuaciones**:
```
Carga = (num_tareas * 0.25) + (intensidad_promedio * 0.5)
Potencia = frecuencia² * intensidad * multiplicador
Energía = Potencia * Δt
```

**Estados**:
- Activo: Ejecutando tareas
- Idle: Sin tareas, consumo mínimo
- Capacidad: Factor de rendimiento relativo

### 4. Task (task.py)

**Responsabilidad**: Representación de tareas computacionales

**Características**:
- Duración y progreso
- Intensidad computacional (0.0-1.0)
- Tiempo de llegada al sistema
- Estado (asignada, completada)

**TaskGenerator**:
- Genera tareas según escenarios predefinidos
- Parámetros configurables de duración e intensidad

### 5. EnergyManager (energy_manager.py)

**Responsabilidad**: Gestión de políticas energéticas

**Características**:
- Implementación de DVFS (Dynamic Voltage and Frequency Scaling)
- Tres estrategias predefinidas
- Ajuste dinámico de frecuencia
- Decisiones de migración de tareas

**Estrategias**:

| Estrategia   | Frecuencia Base | Power Mult. | Consolidación |
|--------------|----------------|-------------|---------------|
| Performance  | 3.5 GHz        | 1.5x        | No            |
| Energy       | 1.8 GHz        | 0.6x        | Sí            |
| Balanced     | 2.5 GHz        | 1.0x        | Condicional   |

### 6. Scheduler (scheduler.py)

**Responsabilidad**: Asignación y migración de tareas

**Características**:
- Múltiples algoritmos de scheduling
- Migración dinámica de tareas
- Balance de carga automático
- Historial de asignaciones

**Algoritmos**:
1. **Default**: Según estrategia energética
2. **RoundRobin**: Distribución circular
3. **LoadBalancing**: Minimiza desbalance
4. **Priority**: Basado en intensidad de tareas

### 7. MetricsCalculator (metrics.py)

**Responsabilidad**: Cálculo de métricas de rendimiento

**Métricas calculadas**:
- **Makespan**: Tiempo total de ejecución
- **Energía Total**: Suma de consumo de todos los procesadores
- **Eficiencia Energética**: Tareas/Joule
- **Balance de Carga**: Desviación estándar de tareas
- **Utilización**: Porcentaje de tiempo activo
- **Throughput**: Tareas por unidad de tiempo

### 8. ReportGenerator (report_generator.py)

**Responsabilidad**: Generación de reportes

**Formatos soportados**:
- **CSV**: Datos tabulares para análisis
- **PDF**: Reporte formateado con gráficos
- **TXT**: Reporte en texto plano

---

## Flujo de Ejecución

### Inicialización

```
1. Usuario configura parámetros en GUI
2. GUI crea instancia de Simulator
3. Simulator inicializa:
   - ProcessorPool (según escenario)
   - TaskGenerator (genera tareas)
   - EnergyManager (con estrategia)
   - Scheduler
   - MetricsCalculator
```

### Ciclo de Simulación

```
Mientras haya tareas pendientes:
  1. Obtener tareas disponibles (según tiempo de llegada)
  2. Scheduler asigna tareas a procesadores
  3. EnergyManager ajusta frecuencias (DVFS)
  4. Cada procesador ejecuta un paso:
     - Procesa tareas activas
     - Calcula consumo energético
     - Actualiza progreso
     - Completa tareas terminadas
  5. Scheduler considera migraciones
  6. Actualizar métricas
  7. Avanzar tiempo
  8. GUI actualiza visualización
```

### Finalización

```
1. Todas las tareas completadas
2. MetricsCalculator genera resumen
3. GUI habilita exportación
4. ReportGenerator crea reportes bajo demanda
```

---

## Patrones de Diseño

### 1. Strategy Pattern (Estrategias Energéticas)

```python
class EnergyManager:
    def __init__(self, strategy):
        self.strategy = strategy
        self.config = self._get_strategy_config()
    
    def adjust_frequency(self, processor):
        if self.strategy == 'performance':
            # Lógica de performance
        elif self.strategy == 'energy':
            # Lógica de energía
        else:
            # Lógica balanceada
```

### 2. Observer Pattern (Actualización de GUI)

```python
# GUI observa cambios en Simulator
def _update_ui(self):
    state = self.simulator.get_state()
    self._update_metrics(state)
    self._update_processors(state)
    self.root.after(100, self._update_ui)
```

### 3. Factory Pattern (Generación de Tareas)

```python
class TaskGenerator:
    @staticmethod
    def generate_tasks(num, scenario):
        # Crea tareas según escenario
```

### 4. Facade Pattern (Simulator)

```python
# Simulator oculta complejidad de componentes
simulator = Simulator(...)
results = simulator.run()  # Interfaz simple
```

---

## Estrategias Energéticas

### Performance-First

**Objetivo**: Máximo rendimiento

**Comportamiento**:
- Frecuencia máxima constante (3.5-4.0 GHz)
- No consolida tareas
- Migración solo con alta sobrecarga (>90%)
- Mayor consumo energético

**Casos de uso**:
- Aplicaciones de baja latencia
- Procesamiento en tiempo real
- Cuando energía no es limitante

### Energy-First

**Objetivo**: Mínimo consumo

**Comportamiento**:
- Frecuencia mínima (1.8 GHz)
- Consolidación agresiva de tareas
- Apaga núcleos innecesarios
- Migración con baja carga (>50%)

**Casos de uso**:
- Dispositivos con batería
- Data centers con límites energéticos
- Procesamiento no urgente

### Balanced (DVFS)

**Objetivo**: Balance óptimo

**Comportamiento**:
- Frecuencia dinámica (1.2-3.5 GHz)
- Ajuste según carga:
  ```
  frecuencia = base * (0.5 + carga * 0.5)
  ```
- Consolidación condicional
- Migración moderada (>70%)

**Casos de uso**:
- Uso general
- Workloads variables
- Optimización automática

---

## Extensibilidad

### Añadir Nueva Estrategia

1. **Actualizar EnergyManager**:
```python
def _get_strategy_config(self):
    configs = {
        'mi_estrategia': {
            'base_freq': 2.8,
            'power_multiplier': 1.1,
            'migration_threshold': 0.65,
            # ...
        }
    }
```

2. **Actualizar GUI**:
```python
strategy_combo['values'] = [
    'Performance-first',
    'Energy-first',
    'Balanceado (DVFS)',
    'Mi Estrategia'
]
```

### Añadir Nuevo Escenario

1. **Actualizar TaskGenerator**:
```python
def generate_tasks(num, scenario):
    if scenario == 'mi_escenario':
        duration = lambda: ...
        intensity = lambda: ...
```

2. **Actualizar GUI**:
```python
scenario_combo['values'] = [
    'Alta carga CPU',
    'Mi Escenario'
]
```

### Añadir Nueva Métrica

1. **Actualizar MetricsCalculator**:
```python
def calculate_custom_metric(self, processors):
    # Implementación
    return value
```

2. **Usar en Simulator**:
```python
custom = self.metrics.calculate_custom_metric(processors)
results['custom_metric'] = custom
```

### Añadir Nuevo Scheduler

1. **Heredar de Scheduler**:
```python
class MyScheduler(Scheduler):
    def _select_processor_for_task(self, task, strategy):
        # Lógica personalizada
```

2. **Usar en Simulator**:
```python
self.scheduler = MyScheduler(self.processor_pool, self.energy_manager)
```

---

## Consideraciones de Diseño

### Concurrencia

- **GUI Thread**: Interfaz de usuario
- **Simulation Thread**: Ejecución de simulación
- **Sincronización**: Via estado compartido del Simulator

### Performance

- **Optimizaciones**:
  - Actualización GUI cada 100ms (no cada paso)
  - Cálculos vectorizados con NumPy
  - Migración periódica (no cada paso)

### Escalabilidad

- Soporta 2-16 procesadores
- Soporta 5-200 tareas
- Tiempo de simulación O(n*m) donde n=tareas, m=pasos

### Mantenibilidad

- Docstrings en todos los métodos
- Type hints donde apropiado
- Separación de responsabilidades
- Tests unitarios para componentes críticos

---

## Diagrama de Clases Simplificado

```
Simulator
├── ProcessorPool
│   └── Processor[]
├── TaskGenerator
│   └── Task[]
├── EnergyManager
│   └── DVFSController
├── Scheduler
└── MetricsCalculator

GUI
├── Simulator
└── ReportGenerator
    └── Simulator
```

---

## Referencias

- [DVFS en Linux](https://www.kernel.org/doc/html/latest/admin-guide/pm/cpufreq.html)
- [Task Scheduling Algorithms](https://en.wikipedia.org/wiki/Scheduling_(computing))
- [Energy-Efficient Computing](https://en.wikipedia.org/wiki/Green_computing)

---

**Última actualización**: 2024
**Versión**: 1.0.0