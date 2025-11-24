Simulador de Balanceo de Energía en Multiprocesador
Simulador para analizar cómo distintas estrategias de asignación y migración de procesos afectan el rendimiento y consumo energético en sistemas multiprocesador.
🚀 Instalación
bash# Clonar o copiar los archivos del proyecto
cd multiprocessor_energy_simulator

# Instalar dependencias
pip install -r requirements.txt
📁 Estructura del Proyecto
multiprocessor_energy_simulator/
├── src/
│   ├── core/                 # Modelos fundamentales
│   │   ├── processor.py      # Procesador individual
│   │   ├── multiprocessor.py # Sistema multiprocesador
│   │   ├── task.py           # Tareas/procesos
│   │   └── energy_model.py   # Modelo de consumo energético
│   ├── schedulers/           # Estrategias de balanceo
│   │   ├── performance_first.py
│   │   ├── energy_first.py
│   │   └── dvfs_balanced.py
│   ├── simulation/           # Motor de simulación
│   │   └── engine.py
│   ├── metrics/              # Recolección de métricas
│   │   └── collector.py
│   ├── visualization/        # Gráficas
│   │   └── plots.py
│   ├── utils/                # Utilidades
│   │   └── config.py
│   └── main.py               # Punto de entrada CLI
├── config/
│   └── default_config.yaml
├── examples/
│   └── run_simulation.py
├── requirements.txt
└── README.md
🎯 Uso Básico
Línea de Comandos
bash# Simulación básica con 8 procesadores
python -m src.main -n 8 -s dvfs

# Comparar las 3 estrategias
python -m src.main -n 16 --compare

# Escenario de alta carga
python -m src.main -n 8 -s performance --scenario high_load

# Simulación a gran escala
python -m src.main -n 64 -s dvfs --tasks 500 --duration 2000

# Con gráficas
python -m src.main -n 8 -s dvfs --plot

# Exportar resultados
python -m src.main -n 8 -s dvfs --export ./results/
Desde Python
pythonfrom src import SimulationEngine, SimulationConfig, build_simulation_config

# Configuración simple
config = SimulationConfig(
    n_processors=8,
    strategy='dvfs',
    duration=1000,
    total_tasks=100
)

# Ejecutar simulación
engine = SimulationEngine(config)
results = engine.run()

# Ver resultados
print(f"Makespan: {results.makespan}")
print(f"Energía: {results.total_energy} J")
print(f"Eficiencia: {results.energy_efficiency} tareas/J")
⚡ Estrategias de Balanceo
1. Performance-First

Todos los procesadores a máxima frecuencia
Balanceo agresivo de carga
Todos los cores siempre activos
Uso: Cuando el tiempo es crítico

2. Energy-First

Frecuencias lo más bajas posible
Consolida tareas en menos procesadores
Apaga cores ociosos
Uso: Cuando la energía es prioritaria

3. DVFS Balanced

Ajusta frecuencia dinámicamente según carga
Balance entre rendimiento y energía
Migración inteligente
Uso: Escenarios generales

📊 Escenarios Predefinidos
EscenarioDescripciónhigh_loadAlta carga CPU, muchas tareas simultáneasintermittentMezcla CPU/IO con picos de actividadheterogeneousProcesadores con diferentes capacidadesunexpected_burstLlegadas masivas de tareaslow_loadCarga baja, tareas I/O-boundstress_testPrueba de estrés máximo
📈 Métricas Recolectadas

Makespan: Tiempo total de ejecución
Energía total: Consumo energético en Joules
Eficiencia energética: Tareas completadas por Joule
Throughput: Tareas por unidad de tiempo
Balance de carga: Distribución entre procesadores
Utilización: Porcentaje de uso de cada core
Migraciones: Tareas movidas entre procesadores

🔧 Configuración Avanzada
Usar archivo YAML para configuración detallada:
yamlsimulation:
  duration: 1000
  time_step: 1

processors:
  count: 8
  heterogeneous: false
  default:
    base_frequency: 1.0
    max_frequency: 3.5
    max_power: 95.0

tasks:
  generation:
    mode: "mixed"
    arrival_rate: 0.5
    total_tasks: 100

strategies:
  dvfs:
    load_low_threshold: 0.3
    load_high_threshold: 0.7
bashpython -m src.main -n 8 -s dvfs --config config/mi_config.yaml
📉 Visualización
pythonfrom src.visualization import create_summary_dashboard, plot_comparison

# Dashboard completo
fig = create_summary_dashboard(results, "DVFS")
fig.savefig("dashboard.png")

# Comparación de estrategias
fig, _ = plot_comparison(results_dict)
fig.savefig("comparison.png")
🧪 Ejecutar Tests
bashpytest tests/ -v
📝 Licencia
MIT License