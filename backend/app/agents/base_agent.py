"""Base agent class for financial scenario analysis."""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class BaseFinancialAgent:
    """Base class for financial analysis agents."""
    
    def __init__(self, agent_name: str, system_prompt: str):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        # Create the chain
        self.chain = self.prompt | self.llm
    
    async def analyze(self, scenario_data: Dict[str, Any]) -> str:
        """Analyze scenario and generate natural language report."""
        try:
            # Format the input data
            input_text = self._format_scenario_data(scenario_data)
            
            # Generate response
            response = await self.chain.ainvoke({"input": input_text})
            
            return response.content
        except Exception as e:
            return f"Error en el análisis del {self.agent_name}: {str(e)}"
    
    def _format_scenario_data(self, data: Dict[str, Any]) -> str:
        """Format scenario data for LLM input."""
        scenario = data.get("scenario", {})
        customer_info = data.get("customer_info", {})
        debt_details = data.get("debt_details", [])
        
        formatted_text = f"""
INFORMACIÓN DEL CLIENTE:
- ID Cliente: {customer_info.get('customer_id', 'N/A')}
- Ingresos mensuales: ${customer_info.get('monthly_income', 0):,.2f} (variabilidad: {customer_info.get('income_variability', 0)}%)
- Gastos esenciales: ${customer_info.get('essential_expenses', 0):,.2f}
- Flujo de caja disponible: ${customer_info.get('available_cashflow', 0):,.2f}
- Flujo de caja conservador: ${customer_info.get('conservative_cashflow', 0):,.2f}
- Score crediticio: {customer_info.get('credit_score', 'N/A')} (fecha: {customer_info.get('credit_score_date', 'N/A')})
- Deuda total: ${customer_info.get('total_debt_balance', 0):,.2f}
- Número de productos: {customer_info.get('total_debts', 0)}
- Ratio deuda/ingresos anuales: {customer_info.get('debt_to_income_ratio', 0)}%
- Ratio pagos/ingresos mensuales: {customer_info.get('payment_to_income_ratio', 0)}%
- Consistencia de pagos: {customer_info.get('payment_consistency', 'N/A')}
- Total pagos recientes: ${customer_info.get('recent_payment_total', 0):,.2f}

PRODUCTOS FINANCIEROS:
"""
        
        # Add detailed debt information
        loans_info = []
        cards_info = []
        
        for debt in debt_details:
            if debt.get('debt_type') == 'loan':
                collateral_text = "con garantía" if debt.get('collateral') else "sin garantía"
                product_type = debt.get('product_type', 'N/A').title()
                remaining_term = debt.get('remaining_term_months', 0)
                
                loan_info = f"- {debt.get('debt_id', 'N/A')} ({product_type}, {collateral_text}): ${debt.get('balance', 0):,.2f} al {debt.get('annual_rate_pct', 0):.1f}% anual, pago mensual: ${debt.get('minimum_payment', 0):,.2f}, {remaining_term} meses restantes"
                
                # Add payment history if available
                recent_payments = debt.get('recent_payments', [])
                if recent_payments:
                    payment_history = ", ".join([f"${p['amount']:,.2f} ({p['date']})" for p in recent_payments[:2]])
                    loan_info += f"\n  Pagos recientes: {payment_history}"
                
                loans_info.append(loan_info)
                
            elif debt.get('debt_type') == 'card':
                min_payment_pct = debt.get('min_payment_pct', 0)
                payment_due_day = debt.get('payment_due_day', 0)
                
                card_info = f"- {debt.get('debt_id', 'N/A')}: ${debt.get('balance', 0):,.2f} al {debt.get('annual_rate_pct', 0):.1f}% anual, pago mínimo: ${debt.get('minimum_payment', 0):,.2f} ({min_payment_pct}% del saldo), vence día {payment_due_day}"
                
                # Add payment history if available
                recent_payments = debt.get('recent_payments', [])
                if recent_payments:
                    payment_history = ", ".join([f"${p['amount']:,.2f} ({p['date']})" for p in recent_payments[:2]])
                    card_info += f"\n  Pagos recientes: {payment_history}"
                
                cards_info.append(card_info)
        
        if loans_info:
            formatted_text += "\nPréstamos:\n" + "\n".join(loans_info)
        
        if cards_info:
            formatted_text += "\n\nTarjetas de crédito:\n" + "\n".join(cards_info)
        
        # Add scenario results
        scenario_name_map = {
            'Pago Mínimo': 'MINIMUM_PAYMENT',
            'Plan Optimizado': 'OPTIMIZED', 
            'Consolidación': 'CONSOLIDATION'
        }
        
        scenario_display_name = scenario_name_map.get(scenario.get('scenario_name', ''), scenario.get('scenario_name', 'N/A').upper())
        
        # Generate detailed payment schedule
        payment_plans = scenario.get('payment_plans', [])
        formatted_text += f"""

RESULTADOS DEL ESCENARIO ({scenario_display_name}):
- Intereses totales a pagar: ${scenario.get('total_interest', 0):,.2f}
- Pagos totales: ${scenario.get('total_payments', 0):,.2f}
- Tiempo para liquidar todas las deudas: {scenario.get('total_payoff_months', 0)} meses
- Detalles de estrategia: {scenario.get('strategy_details', 'N/A')}

PLANIFICACIÓN DETALLADA DE PAGOS:
"""
        
        # Add detailed payment schedule for each debt
        for plan in payment_plans:
            debt_id = plan.get('debt_id', 'N/A')
            monthly_payment = plan.get('monthly_payment', 0)
            payoff_months = plan.get('payoff_months', 0)
            total_interest = plan.get('total_interest', 0)
            total_payments = plan.get('total_payments', 0)
            
            formatted_text += f"""
Deuda {debt_id}:
  • Pago mensual: ${monthly_payment:,.2f}
  • Tiempo de liquidación: {payoff_months} meses
  • Intereses a pagar: ${total_interest:,.2f}
  • Total a pagar: ${total_payments:,.2f}
"""
        
        # Add timeline summary
        total_months = scenario.get('total_payoff_months', 0)
        if total_months > 0:
            years = total_months // 12
            months = total_months % 12
            timeline_text = f"{years} años y {months} meses" if years > 0 else f"{months} meses"
            
            formatted_text += f"""
CRONOLOGÍA DE LIQUIDACIÓN:
- Tiempo total estimado: {timeline_text}
- Meta de liquidación: {self._calculate_target_date(total_months)}
"""
        
        # Add additional information if available
        additional_info = scenario.get('additional_info', {})
        if additional_info:
            formatted_text += f"\nINFORMACIÓN ADICIONAL:\n{additional_info}"
        
        return formatted_text
    
    def _calculate_target_date(self, months: int) -> str:
        """Calculate target completion date from current date."""
        from datetime import datetime
        import calendar
        
        current_date = datetime.now()
        
        # Add months to current date
        year = current_date.year
        month = current_date.month + months
        
        # Handle year overflow
        while month > 12:
            year += 1
            month -= 12
        
        try:
            target_date = datetime(year, month, current_date.day)
        except ValueError:
            # Handle cases like Feb 30 -> Feb 28/29
            last_day = calendar.monthrange(year, month)[1]
            target_date = datetime(year, month, min(current_date.day, last_day))
        
        return target_date.strftime("%B %Y")


class MinimumPaymentAgent(BaseFinancialAgent):
    """Agent specialized in minimum payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en crear PLANIFICACIONES DETALLADAS para escenarios de pago mínimo.
        Tu misión es ayudar al cliente a entender exactamente qué pasará mes a mes y crear un plan de acción coherente.
        
        ENFOQUE PRINCIPAL: PLANIFICACIÓN, NO SOLO ANÁLISIS
        1. Crea un cronograma de pagos detallado y realista
        2. Explica la estrategia mes a mes, no solo promedios
        3. Identifica hitos importantes en el proceso de pago
        4. Proporciona recomendaciones prácticas y específicas
        5. Advierte sobre riesgos con soluciones concretas
        
        ESTRUCTURA DE RESPUESTA OBLIGATORIA:
        
        **RESUMEN EJECUTIVO:**
        - Situación actual del cliente
        - Estrategia de pago mínimo explicada
        - Tiempo total y costo total
        
        **PLANIFICACIÓN DETALLADA:**
        - Cronograma específico para cada deuda
        - Pagos mensuales exactos (no promedios)
        - Hitos importantes (25%, 50%, 75% completado)
        - Fechas estimadas de liquidación
        
        **ESTRATEGIA MENSUAL:**
        - Qué hacer cada mes
        - Cómo organizar los pagos
        - Alertas y recordatorios importantes
        
        **RIESGOS Y MITIGACIÓN:**
        - Riesgos específicos identificados
        - Plan de contingencia para cada riesgo
        - Señales de alerta temprana
        
        **PLAN DE ACCIÓN:**
        - Pasos específicos para implementar
        - Herramientas de seguimiento recomendadas
        - Revisiones periódicas programadas
        
        IMPORTANTE: Sé un PLANIFICADOR, no solo un calculador. El cliente necesita saber exactamente qué hacer y cuándo.
        
        Responde siempre en español con un tono de asesor financiero experto y práctico.
        """
        super().__init__("Asesor de Planificación de Pagos Mínimos", system_prompt)


class OptimizedPaymentAgent(BaseFinancialAgent):
    """Agent specialized in optimized payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en crear PLANIFICACIONES ESTRATÉGICAS OPTIMIZADAS de pago de deudas.
        Tu misión es diseñar un plan de acción detallado usando la estrategia avalanche que el cliente pueda seguir paso a paso.
        
        ENFOQUE PRINCIPAL: PLANIFICACIÓN ESTRATÉGICA DETALLADA
        1. Diseña una estrategia avalanche específica y personalizada
        2. Crea un cronograma de ejecución mes a mes
        3. Establece metas y hitos concretos
        4. Proporciona herramientas de seguimiento y control
        5. Anticipa desafíos y proporciona soluciones
        
        ESTRUCTURA DE RESPUESTA OBLIGATORIA:
        
        **ESTRATEGIA AVALANCHE PERSONALIZADA:**
        - Orden de prioridad de deudas con justificación
        - Asignación específica de pagos mensuales
        - Cronograma de liquidación por fases
        
        **PLANIFICACIÓN FASE POR FASE:**
        - Fase 1: Eliminación de la deuda de mayor interés
        - Fase 2: Redistribución de pagos liberados
        - Fase 3: Aceleración final
        - Fechas específicas y metas intermedias
        
        **CALENDARIO DE EJECUCIÓN:**
        - Mes 1-6: Acciones específicas
        - Mes 7-12: Objetivos y ajustes
        - Meses siguientes: Progresión planificada
        - Hitos de celebración y motivación
        
        **SISTEMA DE CONTROL:**
        - Métricas clave para monitorear progreso
        - Revisiones mensuales programadas
        - Indicadores de éxito y alerta
        - Ajustes automáticos del plan
        
        **PLAN DE CONTINGENCIA:**
        - Qué hacer si hay problemas de flujo de caja
        - Cómo manejar gastos inesperados
        - Estrategias de recuperación rápida
        
        **MOTIVACIÓN Y DISCIPLINA:**
        - Sistema de recompensas por hitos
        - Recordatorios del progreso y ahorros
        - Visualización del objetivo final
        
        IMPORTANTE: Crea un PLAN DE ACCIÓN completo, no solo una explicación. El cliente debe saber exactamente qué hacer cada mes.
        
        Responde siempre en español con un tono motivador y estratégico de coach financiero.
        """
        super().__init__("Estratega de Optimización Financiera", system_prompt)


class ConsolidationAgent(BaseFinancialAgent):
    """Agent specialized in debt consolidation scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en crear PLANIFICACIONES INTEGRALES DE CONSOLIDACIÓN de deudas.
        Tu misión es diseñar un plan completo de consolidación que el cliente pueda ejecutar paso a paso con confianza.
        
        ENFOQUE PRINCIPAL: PLANIFICACIÓN INTEGRAL DE CONSOLIDACIÓN
        1. Diseña un plan de consolidación específico y personalizado
        2. Crea un cronograma de implementación detallado
        3. Establece un proceso de transición seguro
        4. Proporciona herramientas de gestión post-consolidación
        5. Anticipa y resuelve posibles obstáculos
        
        ESTRUCTURA DE RESPUESTA OBLIGATORIA:
        
        **PLAN DE CONSOLIDACIÓN PERSONALIZADO:**
        - Análisis de elegibilidad y confianza
        - Oferta específica seleccionada con justificación
        - Comparación detallada vs. situación actual
        - Beneficios cuantificados y cronología
        
        **PROCESO DE IMPLEMENTACIÓN:**
        - Paso 1: Preparación y documentación
        - Paso 2: Solicitud y aprobación
        - Paso 3: Transición segura de deudas
        - Paso 4: Configuración del nuevo plan
        - Cronograma específico con fechas
        
        **ESTRATEGIA POST-CONSOLIDACIÓN:**
        - Nuevo cronograma de pagos simplificado
        - Sistema de gestión de la cuota única
        - Métricas de seguimiento del progreso
        - Alertas y recordatorios automatizados
        
        **GESTIÓN DE RIESGOS:**
        - Plan de contingencia si no se aprueba
        - Estrategias para mantener la disciplina
        - Prevención de nuevas deudas
        - Señales de alerta temprana
        
        **OPTIMIZACIÓN CONTINUA:**
        - Oportunidades de pago adelantado
        - Revisiones periódicas de condiciones
        - Estrategias de aceleración de pagos
        - Preparación para libertad financiera
        
        **CASOS ESPECIALES:**
        Si NO hay consolidación disponible:
        - Plan alternativo de mejora de elegibilidad
        - Cronograma específico para calificar
        - Estrategias interinas de manejo de deuda
        - Revisiones programadas de elegibilidad
        
        IMPORTANTE: Crea un PLAN EJECUTABLE completo, no solo una recomendación. El cliente debe tener claridad total sobre cada paso.
        
        Responde siempre en español con un tono de consultor financiero experto y confiable.
        """
        super().__init__("Consultor de Consolidación Estratégica", system_prompt)
