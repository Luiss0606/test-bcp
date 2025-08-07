"""Master agent for consolidating reports from specialized agents."""

import os
from typing import Dict, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class MasterConsolidatorAgent:
    """Master agent that consolidates reports from the three specialized agents."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",  # Using more powerful model for consolidation
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        self.system_prompt = """
        Eres el Director de Estrategia Financiera y Asesor Principal, responsable de crear un INFORME INTEGRAL DETALLADO
        que consolide todos los análisis especializados y proporcione una visión completa y sustentada de la situación.
        
        ESPECIALISTAS QUE HAS SUPERVISADO:
        1. Asesor de Planificación de Pagos Mínimos: Analizó las implicaciones y riesgos
        2. Estratega de Optimización Financiera: Diseñó la estrategia avalanche optimizada
        3. Consultor de Consolidación Estratégica: Evaluó opciones de unificación de deudas
        
        TU MISIÓN PRINCIPAL:
        Crear un INFORME MAESTRO DETALLADO que:
        - Integre y sintetice TODOS los análisis especializados
        - Proporcione una COMPARACIÓN EXHAUSTIVA de todas las opciones
        - Presente una RECOMENDACIÓN SUSTENTADA con evidencia clara
        - Incluya un PLAN DE IMPLEMENTACIÓN DETALLADO paso a paso
        - Anticipe TODOS los escenarios y contingencias posibles
        
        ESTRUCTURA OBLIGATORIA DEL INFORME INTEGRAL:
        
        **1. RESUMEN EJECUTIVO ESTRATÉGICO**
        - Síntesis de la situación actual del cliente
        - Hallazgos clave de los tres análisis especializados
        - Recomendación principal con justificación clara
        - Impacto financiero proyectado
        
        **2. ANÁLISIS COMPARATIVO DETALLADO**
        Tabla comparativa completa:
        | Escenario | Pago Mensual | Tiempo Total | Intereses | Ahorro | Riesgo | Viabilidad |
        - Análisis de ventajas y desventajas de cada opción
        - Proyecciones financieras a corto, mediano y largo plazo
        - Evaluación de riesgos específicos por escenario
        
        **3. SÍNTESIS DE ANÁLISIS ESPECIALIZADOS**
        Para cada análisis especializado:
        - Puntos clave identificados
        - Recomendaciones específicas
        - Alertas y consideraciones importantes
        - Estrategias propuestas
        
        **4. RECOMENDACIÓN ESTRATÉGICA FUNDAMENTADA**
        - Opción recomendada con JUSTIFICACIÓN DETALLADA
        - Análisis de por qué es la mejor para este cliente específico
        - Comparación punto por punto con otras opciones
        - Evidencia numérica y cualitativa de la recomendación
        
        **5. PLAN DE IMPLEMENTACIÓN MAESTRO**
        Fase 1 (Mes 1-3): Preparación y Organización
        - Acciones específicas con fechas
        - Documentación requerida
        - Preparativos necesarios
        
        Fase 2 (Mes 4-12): Ejecución Inicial
        - Implementación de la estrategia
        - Métricas de seguimiento
        - Puntos de control
        
        Fase 3 (Año 2+): Optimización y Ajustes
        - Revisiones periódicas
        - Oportunidades de mejora
        - Estrategias de aceleración
        
        **6. ANÁLISIS DE RIESGOS Y MITIGACIÓN**
        - Matriz de riesgos por escenario
        - Planes de contingencia específicos
        - Señales de alerta temprana
        - Estrategias de recuperación
        
        **7. CONSIDERACIONES ESPECIALES**
        - Impacto en score crediticio
        - Implicaciones fiscales
        - Efectos en capacidad de endeudamiento futuro
        - Consideraciones familiares y personales
        
        **8. HERRAMIENTAS Y RECURSOS**
        - Calculadoras y plantillas recomendadas
        - Aplicaciones de seguimiento
        - Recursos educativos
        - Contactos de apoyo
        
        **9. CRONOGRAMA DE SEGUIMIENTO**
        - Revisiones mensuales programadas
        - Hitos de evaluación trimestral
        - Ajustes semestrales
        - Evaluación anual completa
        
        **10. CONCLUSIÓN Y LLAMADA A LA ACCIÓN**
        - Resumen de beneficios principales
        - Pasos inmediatos a seguir (próximas 48 horas)
        - Motivación y visión del futuro financiero
        - Compromiso de apoyo continuo
        
        IMPORTANTE: Tu informe debe ser EXHAUSTIVO pero CLARO, TÉCNICO pero ACCESIBLE, 
        DETALLADO pero ORGANIZADO. Cada recomendación debe estar SUSTENTADA con datos y análisis.
        
        Usa un tono de consultor senior experto, inspirador pero realista, técnico pero humano.
        """

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", self.system_prompt), ("human", "{input}")]
        )

        self.chain = self.prompt | self.llm

    async def consolidate_reports(
        self,
        customer_id: str,
        scenarios: Dict[str, Any],
        agent_analyses: Dict[str, str],
        customer_info: Dict[str, Any],
    ) -> str:
        """Consolidate all agent reports into a comprehensive financial report."""

        # Format input for the master agent
        input_text = self._format_consolidation_input(
            customer_id, scenarios, agent_analyses, customer_info
        )

        try:
            # Generate consolidated report
            response = await self.chain.ainvoke({"input": input_text})
            return response.content
        except Exception as e:
            return self._generate_fallback_report(customer_id, scenarios, str(e))

    def _format_consolidation_input(
        self,
        customer_id: str,
        scenarios: Dict[str, Any],
        agent_analyses: Dict[str, str],
        customer_info: Dict[str, Any],
    ) -> str:
        """Format all information for the master consolidation agent."""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        input_text = f"""
        INFORME DE REESTRUCTURACIÓN FINANCIERA
        Cliente: {customer_id}
        Fecha: {current_time}
        
        PERFIL DEL CLIENTE:
        - Ingresos mensuales: ${customer_info.get("monthly_income", 0):,.2f}
        - Gastos esenciales: ${customer_info.get("essential_expenses", 0):,.2f}
        - Flujo disponible: ${customer_info.get("available_cashflow", 0):,.2f}
        - Score crediticio: {customer_info.get("credit_score", "N/A")}
        - Variabilidad de ingresos: {customer_info.get("income_variability", 0)}%
        
        ESCENARIOS ANALIZADOS:
        """

        # Add scenario summaries
        for scenario_name, scenario_data in scenarios.items():
            scenario_title = {
                "minimum": "PAGO MÍNIMO",
                "optimized": "PLAN OPTIMIZADO",
                "consolidation": "CONSOLIDACIÓN",
            }.get(scenario_name, scenario_name.upper())

            input_text += f"""
        
        {scenario_title}:
        - Pago mensual: ${scenario_data.get("total_monthly_payment", 0):,.2f}
        - Tiempo de pago: {scenario_data.get("total_payoff_months", 0)} meses
        - Intereses totales: ${scenario_data.get("total_interest", 0):,.2f}
        - Pagos totales: ${scenario_data.get("total_payments", 0):,.2f}
        - Ahorro vs mínimo: ${scenario_data.get("savings_vs_minimum", 0):,.2f}
            """

        # Add specialist analyses
        input_text += "\n\nANÁLISIS DE ESPECIALISTAS:\n"

        if "minimum_analysis" in agent_analyses:
            input_text += f"\n--- ANÁLISIS DEL ESPECIALISTA EN PAGO MÍNIMO ---\n"
            input_text += agent_analyses["minimum_analysis"]

        if "optimized_analysis" in agent_analyses:
            input_text += f"\n\n--- ANÁLISIS DEL ESPECIALISTA EN PLAN OPTIMIZADO ---\n"
            input_text += agent_analyses["optimized_analysis"]

        if "consolidation_analysis" in agent_analyses:
            input_text += f"\n\n--- ANÁLISIS DEL ESPECIALISTA EN CONSOLIDACIÓN ---\n"
            input_text += agent_analyses["consolidation_analysis"]

        input_text += f"""
        
        INSTRUCCIONES PARA EL INFORME FINAL:
        Consolida toda esta información en un informe integral que:
        1. Sea fácil de entender para el cliente
        2. Destaque la mejor opción financiera
        3. Proporcione pasos claros a seguir
        4. Incluya advertencias importantes
        5. Motive al cliente a tomar acción positiva
        
        El informe debe ser profesional pero accesible, empático pero directo.
        """

        return input_text

    def _generate_fallback_report(
        self, customer_id: str, scenarios: Dict[str, Any], error_message: str
    ) -> str:
        """Generate a basic fallback report if the AI consolidation fails."""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Find best scenario by savings
        best_scenario = None
        max_savings = 0

        for scenario_name, scenario in scenarios.items():
            savings = scenario.get("savings_vs_minimum", 0)
            if savings > max_savings:
                max_savings = savings
                best_scenario = scenario_name

        fallback_report = f"""
        INFORME DE REESTRUCTURACIÓN FINANCIERA
        Cliente: {customer_id}
        Fecha: {current_time}
        
        RESUMEN EJECUTIVO:
        Se han analizado múltiples escenarios para optimizar el pago de sus deudas.
        
        ESCENARIOS EVALUADOS:
        """

        for scenario_name, scenario in scenarios.items():
            scenario_title = {
                "minimum": "Pago Mínimo",
                "optimized": "Plan Optimizado",
                "consolidation": "Consolidación",
            }.get(scenario_name, scenario_name)

            fallback_report += f"""
        
        {scenario_title}:
        - Pago mensual: ${scenario.get("total_monthly_payment", 0):,.2f}
        - Tiempo: {scenario.get("total_payoff_months", 0)} meses
        - Intereses: ${scenario.get("total_interest", 0):,.2f}
        - Ahorro: ${scenario.get("savings_vs_minimum", 0):,.2f}
            """

        if best_scenario:
            scenario_name = {
                "minimum": "pago mínimo",
                "optimized": "plan optimizado",
                "consolidation": "consolidación",
            }.get(best_scenario, best_scenario)

            fallback_report += f"""
        
        RECOMENDACIÓN:
        El {scenario_name} ofrece el mayor beneficio financiero con un ahorro de ${max_savings:,.2f}.
        
        PRÓXIMOS PASOS:
        1. Revisar detalladamente el escenario recomendado
        2. Consultar con su asesor financiero
        3. Implementar la estrategia seleccionada
        
        Nota: Este es un informe generado automáticamente debido a un error técnico: {error_message}
        Para un análisis más detallado, consulte con su asesor financiero.
            """

        return fallback_report
