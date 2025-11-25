# Simulador de Balanceo de Energía para Sistemas Multiprocesador

## 📋 Descripción del Proyecto

Este simulador permite analizar el impacto de diferentes estrategias de balanceo de carga en sistemas multiprocesador, considerando tanto el rendimiento como el consumo energético. El proyecto implementa tres estrategias principales:

- **Performance-first**: Maximiza el rendimiento utilizando la máxima frecuencia en todos los núcleos
- **Energy-first**: Prioriza el ahorro de energía, consolidando tareas y apagando núcleos innecesarios
- **Balanceado (DVFS)**: Ajusta dinámicamente frecuencia y voltaje según la carga actual

### Características Principales

✅ Interfaz gráfica intuitiva con Tkinter
✅ Simulación en tiempo real con visualización de métricas
✅ Cuatro escenarios de carga predefinidos
✅ Exportación de reportes en CSV y PDF
✅ Gráficos de rendimiento y consumo energético
✅ Arquitectura modular y extensible

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Miniconda (recomendado) o Anaconda

### Instalación con Miniconda

1. **Descargar e instalar Miniconda**
   
   Descarga desde: https://docs.conda.io/en/latest/miniconda.html
   
   - Windows: Ejecuta el instalador `.exe`
   - Linux/Mac: 
     ```bash
     bash Miniconda3-latest-Linux-x86_64.sh
     ```

2. **Crear entorno virtual**
   
   ```bash
   conda create --name balanceo-energia python=3.10
   ```

3. **Activar el entorno**
   
   ```bash
   # Windows
   conda activate balanceo-energia
   
   # Linux/Mac
   source activate balanceo-energia
   ```

4. **Clonar o descargar el proyecto**
   
   ```bash
   cd /ruta/a/tu/proyecto
   ```

5. **Instalar dependencias**
   
   ```bash
   pip install -r requirements.txt
   ```

## 📦 Estructura del Proyecto

```
balanceo-energia-simulator/
│
├── src/
│   ├── __init__.py
│   ├── gui.py                 # Interfaz gráfica principal
│   ├── simulator.py           # Motor de simulación
│   ├── processor.py           # Clase Procesador
│   ├── task.py                # Clase Tarea
│   ├── energy_manager.py      # Gestión de energía y estrategias
│   ├── scheduler.py           # Planificador de tareas
│   ├── metrics.py             # Cálculo de métricas
│   └── report_generator.py    # Generación de reportes
│
├── tests/
│   ├── __init__.py
│   ├── test_simulator.py
│   └── test_energy_manager.py
│
├── docs/
│   └── arquitectura.md
│
├── outputs/                    # Carpeta para reportes generados
│
├── README.md
├── requirements.txt
└── .gitignore
```

## 🎮 Uso

### Ejecución Básica

```bash
python src/gui.py
```

### Ejecución desde línea de comandos (sin GUI)

```bash
python src/simulator.py --processors 8 --tasks 50 --scenario high_cpu --strategy balanced
```

### Parámetros Disponibles

- `--processors`: Número de procesadores (2-16, default: 4)
- `--tasks`: Número de tareas (5-200, default: 20)
- `--scenario`: Escenario de carga
  - `high_cpu`: Alta carga CPU
  - `intermittent`: Carga intermitente
  - `heterogeneous`: Núcleos heterogéneos
  - `spike`: Picos inesperados
- `--strategy`: Estrategia de balanceo
  - `performance`: Performance-first
  - `energy`: Energy-first
  - `balanced`: Balanceado (DVFS)

## 📊 Uso de la Interfaz Gráfica

### Panel de Configuración

1. **Configurar parámetros**:
   - Selecciona el número de procesadores
   - Define la cantidad de tareas
   - Elige un escenario de carga
   - Selecciona una estrategia de balanceo

2. **Iniciar simulación**:
   - Presiona el botón "Iniciar Simulación"
   - Observa el progreso en tiempo real

3. **Controlar la simulación**:
   - Pausa/Reanuda la ejecución
   - Reinicia para cambiar parámetros

4. **Exportar resultados**:
   - Botón "Exportar CSV": Guarda métricas en formato CSV
   - Botón "Exportar PDF": Genera reporte completo con gráficos

### Interpretación de Resultados

#### Métricas Principales

- **Makespan**: Tiempo total de ejecución (menor es mejor)
- **Consumo Energético Total**: Energía consumida en Joules
- **Eficiencia Energética**: Tareas completadas por Joule (mayor es mejor)
- **Balance de Carga**: Desviación estándar de tareas por núcleo (menor es mejor)

#### Indicadores Visuales

- **Barra Verde**: Carga normal (0-40%)
- **Barra Amarilla**: Carga moderada (40-70%)
- **Barra Roja**: Carga alta (70-100%)

## 🔧 Personalización y Extensión

### Agregar Nueva Estrategia

Edita `src/energy_manager.py`:

```python
class EnergyManager:
    def get_strategy_config(self, strategy):
        configs = {
            'performance': {...},
            'energy': {...},
            'balanced': {...},
            'tu_estrategia': {
                'base_freq': 2.8,
                'power_multiplier': 1.2,
                'migration_threshold': 0.6
            }
        }
        return configs.get(strategy, configs['balanced'])
```

### Agregar Nuevo Escenario

Edita `src/task.py`:

```python
def generate_task(self, scenario):
    scenarios = {
        'high_cpu': {...},
        'intermittent': {...},
        'tu_escenario': {
            'duration': lambda: 60 + random() * 80,
            'intensity': lambda: 0.7 + random() * 0.3
        }
    }
```

### Agregar Nueva Métrica

Edita `src/metrics.py`:

```python
class MetricsCalculator:
    def calculate_custom_metric(self, processors):
        # Tu implementación aquí
        return valor
```

## 🧪 Pruebas

Ejecutar todas las pruebas:

```bash
python -m pytest tests/
```

Ejecutar pruebas con cobertura:

```bash
python -m pytest tests/ --cov=src
```

## 📈 Ejemplos de Uso

### Ejemplo 1: Comparar Estrategias

```python
from src.simulator import Simulator

# Crear simulador
sim = Simulator(processors=8, tasks=50, scenario='high_cpu')

# Probar Performance-first
results_perf = sim.run('performance')

# Probar Energy-first
results_energy = sim.run('energy')

# Comparar
print(f"Performance - Makespan: {results_perf['makespan']}")
print(f"Energy - Makespan: {results_energy['makespan']}")
```

### Ejemplo 2: Análisis de Sensibilidad

```bash
# Probar diferentes números de procesadores
for p in 4 8 16; do
    python src/simulator.py --processors $p --tasks 100 --strategy balanced
done
```

## 🤝 Contribución

### Cómo Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

### Guía de Estilo

- Seguir PEP 8 para código Python
- Documentar funciones con docstrings
- Agregar pruebas unitarias para nuevas funcionalidades
- Actualizar README.md con nuevas características

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👥 Autores

- Desarrollador Principal - Sistema de Balanceo de Energía

## 🙏 Agradecimientos

- Inspirado en sistemas de gestión de energía de Linux (cpufreq)
- Basado en técnicas DVFS (Dynamic Voltage and Frequency Scaling)
- Implementación de algoritmos de scheduling modernos

## 📞 Soporte

Para reportar bugs o solicitar características:
- Abre un issue en GitHub
- Email: soporte@simulador-energia.com

## 🔄 Historial de Versiones

### v1.0.0 (2024)
- Lanzamiento inicial
- Tres estrategias de balanceo
- Cuatro escenarios de carga
- Exportación CSV y PDF
- Interfaz gráfica completa

---

**Nota**: Este simulador es una herramienta educativa y de investigación. Los valores de energía son aproximados y no reflejan mediciones exactas de hardware real.

