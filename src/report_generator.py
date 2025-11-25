"""
Módulo para generación de reportes en CSV y PDF.
"""

import csv
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportGenerator:
    """
    Genera reportes de simulación en múltiples formatos.
    """
    
    def __init__(self, simulator):
        """
        Inicializa el generador de reportes.
        
        Args:
            simulator: Instancia del simulador
        """
        self.simulator = simulator
        self.results = simulator.get_results()
        
    def export_csv(self, filename):
        """
        Exporta resultados a formato CSV.
        
        Args:
            filename (str): Nombre del archivo
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Encabezado
            writer.writerow(['REPORTE DE SIMULACIÓN - BALANCEO DE ENERGÍA'])
            writer.writerow(['Fecha:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Configuración
            writer.writerow(['CONFIGURACIÓN'])
            writer.writerow(['Procesadores:', self.results['num_processors']])
            writer.writerow(['Tareas Totales:', self.results['total_tasks']])
            writer.writerow(['Escenario:', self.results['scenario']])
            writer.writerow(['Estrategia:', self.results['strategy']])
            writer.writerow([])
            
            # Resultados Globales
            writer.writerow(['RESULTADOS GLOBALES'])
            writer.writerow(['Makespan (Tiempo Total):', f"{self.results['makespan']:.2f}"])
            writer.writerow(['Energía Total Consumida:', f"{self.results['total_energy']:.2f} J"])
            writer.writerow(['Eficiencia Energética:', f"{self.results['efficiency']:.4f} tareas/J"])
            writer.writerow(['Tareas Completadas:', self.results['completed_tasks']])
            writer.writerow(['Balance de Carga (σ):', f"{self.results['load_balance_std']:.2f}"])
            writer.writerow(['Utilización Promedio:', f"{self.results['avg_utilization']:.1f}%"])
            writer.writerow([])
            
            # Métricas por Procesador
            writer.writerow(['MÉTRICAS POR PROCESADOR'])
            writer.writerow([
                'ID', 'Frecuencia (GHz)', 'Energía (J)', 'Tiempo Ejecución',
                'Tareas Completadas', 'Utilización (%)', 'Eficiencia (tareas/J)'
            ])
            
            for proc in self.results['processors']:
                writer.writerow([
                    proc['id'],
                    f"{proc['frequency']:.2f}",
                    f"{proc['energy']:.2f}",
                    f"{proc['execution_time']:.2f}",
                    proc['completed_tasks'],
                    f"{proc['utilization']:.1f}",
                    f"{proc['efficiency']:.4f}"
                ])
    
    def export_pdf(self, filename):
        """
        Exporta resultados a formato PDF con gráficos.
        
        Args:
            filename (str): Nombre del archivo
        """
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Contenedor para elementos del PDF
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para secciones
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Título
        elements.append(Paragraph("Reporte de Simulación", title_style))
        elements.append(Paragraph("Sistema Multiprocesador - Balanceo de Energía", styles['Heading3']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Fecha
        date_text = f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Configuración
        elements.append(Paragraph("Configuración", section_style))
        config_data = [
            ['Parámetro', 'Valor'],
            ['Procesadores', str(self.results['num_processors'])],
            ['Tareas Totales', str(self.results['total_tasks'])],
            ['Escenario', self._get_scenario_name(self.results['scenario'])],
            ['Estrategia', self._get_strategy_name(self.results['strategy'])]
        ]
        
        config_table = Table(config_data, colWidths=[3*inch, 3*inch])
        config_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(config_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Resultados Globales
        elements.append(Paragraph("Resultados Globales", section_style))
        results_data = [
            ['Métrica', 'Valor'],
            ['Makespan (Tiempo Total)', f"{self.results['makespan']:.2f} unidades"],
            ['Energía Total Consumida', f"{self.results['total_energy']:.2f} J"],
            ['Eficiencia Energética', f"{self.results['efficiency']:.4f} tareas/J"],
            ['Tareas Completadas', f"{self.results['completed_tasks']} / {self.results['total_tasks']}"],
            ['Balance de Carga (σ)', f"{self.results['load_balance_std']:.2f}"],
            ['Utilización Promedio', f"{self.results['avg_utilization']:.1f}%"]
        ]
        
        results_table = Table(results_data, colWidths=[3*inch, 3*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(results_table)
        elements.append(PageBreak())
        
        # Métricas por Procesador
        elements.append(Paragraph("Métricas por Procesador", section_style))
        elements.append(Spacer(1, 0.2*inch))
        
        proc_data = [['ID', 'Freq (GHz)', 'Energía (J)', 'Tiempo', 'Tareas', 'Util (%)']]
        
        for proc in self.results['processors']:
            proc_data.append([
                str(proc['id']),
                f"{proc['frequency']:.2f}",
                f"{proc['energy']:.2f}",
                f"{proc['execution_time']:.2f}",
                str(proc['completed_tasks']),
                f"{proc['utilization']:.1f}"
            ])
        
        proc_table = Table(proc_data, colWidths=[0.7*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
        proc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white])
        ]))
        
        elements.append(proc_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Análisis y Conclusiones
        elements.append(Paragraph("Análisis y Conclusiones", section_style))
        
        analysis = self._generate_analysis()
        for paragraph in analysis:
            elements.append(Paragraph(paragraph, styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Generar PDF
        doc.build(elements)
    
    def _get_scenario_name(self, scenario):
        """Obtiene el nombre legible del escenario."""
        names = {
            'high_cpu': 'Alta carga CPU',
            'intermittent': 'Carga intermitente',
            'heterogeneous': 'Núcleos heterogéneos',
            'spike': 'Picos inesperados'
        }
        return names.get(scenario, scenario)
    
    def _get_strategy_name(self, strategy):
        """Obtiene el nombre legible de la estrategia."""
        names = {
            'performance': 'Performance-First',
            'energy': 'Energy-First',
            'balanced': 'Balanceado (DVFS)'
        }
        return names.get(strategy, strategy)
    
    def _generate_analysis(self):
        """Genera análisis automático de los resultados."""
        analysis = []
        
        # Análisis de eficiencia
        if self.results['efficiency'] > 0.1:
            analysis.append(
                f"<b>Eficiencia Energética:</b> El sistema mostró una excelente eficiencia "
                f"energética de {self.results['efficiency']:.4f} tareas por Joule, indicando "
                f"un uso óptimo de los recursos energéticos."
            )
        else:
            analysis.append(
                f"<b>Eficiencia Energética:</b> La eficiencia energética de "
                f"{self.results['efficiency']:.4f} tareas/J sugiere oportunidades de "
                f"optimización en el consumo energético."
            )
        
        # Análisis de balance
        if self.results['load_balance_std'] < 2.0:
            analysis.append(
                f"<b>Balance de Carga:</b> Se logró un excelente balance de carga con "
                f"una desviación estándar de {self.results['load_balance_std']:.2f}, "
                f"distribuyendo el trabajo equitativamente entre procesadores."
            )
        else:
            analysis.append(
                f"<b>Balance de Carga:</b> La desviación estándar de "
                f"{self.results['load_balance_std']:.2f} indica desbalance en la "
                f"distribución de tareas, posiblemente debido al escenario elegido."
            )
        
        # Análisis de utilización
        if self.results['avg_utilization'] > 70:
            analysis.append(
                f"<b>Utilización:</b> Los procesadores mantuvieron una alta utilización "
                f"promedio de {self.results['avg_utilization']:.1f}%, maximizando el "
                f"aprovechamiento de los recursos disponibles."
            )
        elif self.results['avg_utilization'] > 50:
            analysis.append(
                f"<b>Utilización:</b> La utilización promedio de "
                f"{self.results['avg_utilization']:.1f}% es moderada, con margen para "
                f"optimización según la estrategia seleccionada."
            )
        else:
            analysis.append(
                f"<b>Utilización:</b> La baja utilización de "
                f"{self.results['avg_utilization']:.1f}% puede deberse a la estrategia "
                f"Energy-First, que prioriza ahorro energético sobre uso de recursos."
            )
        
        return analysis
    
    def generate_text_report(self):
        """
        Genera un reporte en formato texto plano.
        
        Returns:
            str: Reporte en texto
        """
        report = []
        report.append("=" * 70)
        report.append("REPORTE DE SIMULACIÓN - BALANCEO DE ENERGÍA")
        report.append("=" * 70)
        report.append(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        report.append("CONFIGURACIÓN:")
        report.append(f"  Procesadores: {self.results['num_processors']}")
        report.append(f"  Tareas: {self.results['total_tasks']}")
        report.append(f"  Escenario: {self._get_scenario_name(self.results['scenario'])}")
        report.append(f"  Estrategia: {self._get_strategy_name(self.results['strategy'])}\n")
        
        report.append("RESULTADOS GLOBALES:")
        report.append(f"  Makespan: {self.results['makespan']:.2f} unidades")
        report.append(f"  Energía Total: {self.results['total_energy']:.2f} J")
        report.append(f"  Eficiencia: {self.results['efficiency']:.4f} tareas/J")
        report.append(f"  Completadas: {self.results['completed_tasks']} / {self.results['total_tasks']}")
        report.append(f"  Balance (σ): {self.results['load_balance_std']:.2f}")
        report.append(f"  Utilización: {self.results['avg_utilization']:.1f}%\n")
        
        report.append("MÉTRICAS POR PROCESADOR:")
        for proc in self.results['processors']:
            report.append(f"\n  Procesador {proc['id']}:")
            report.append(f"    Frecuencia: {proc['frequency']:.2f} GHz")
            report.append(f"    Energía: {proc['energy']:.2f} J")
            report.append(f"    Tiempo: {proc['execution_time']:.2f}")
            report.append(f"    Tareas: {proc['completed_tasks']}")
            report.append(f"    Utilización: {proc['utilization']:.1f}%")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)