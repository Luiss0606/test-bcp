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
        
        formatted_text += f"""

RESULTADOS DEL ESCENARIO ({scenario_display_name}):
- Intereses totales a pagar: ${scenario.get('total_interest', 0):,.2f}
- Pagos totales: ${scenario.get('total_payments', 0):,.2f}
- Tiempo para liquidar: {scenario.get('total_payoff_months', 0)} meses
- Pago mensual promedio: ${scenario.get('total_monthly_payment', 0):,.2f}
- Detalles de estrategia: {scenario.get('strategy_details', 'N/A')}
"""
        
        # Add additional information if available
        additional_info = scenario.get('additional_info', {})
        if additional_info:
            formatted_text += f"\nINFORMACIÓN ADICIONAL:\n{additional_info}"
        
        return formatted_text


class MinimumPaymentAgent(BaseFinancialAgent):
    """Agent specialized in minimum payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en analizar escenarios de pago mínimo de deudas.
        Tu rol es explicar de manera clara y comprensible las implicaciones de pagar solo los montos mínimos requeridos.
        
        INSTRUCCIONES ESPECÍFICAS:
        1. Presenta TODA la información del cliente y productos financieros tal como se proporciona
        2. Analiza detalladamente las consecuencias del pago mínimo
        3. Explica por qué esta estrategia es costosa a largo plazo
        4. Incluye advertencias claras sobre los riesgos financieros
        5. Usa un lenguaje empático pero directo sobre los riesgos
        6. Proporciona contexto educativo sobre intereses compuestos
        
        FORMATO DE RESPUESTA OBLIGATORIO:
        - Reproduce EXACTAMENTE la información del cliente y productos financieros
        - Presenta los resultados del escenario con todos los detalles proporcionados
        - Explica las implicaciones financieras específicas
        - Destaca los costos ocultos del pago mínimo
        - Concluye con advertencias y recomendaciones claras
        
        IMPORTANTE: Debes incluir TODA la información proporcionada sobre el cliente, productos financieros, 
        y resultados del escenario. No omitas ningún dato importante.
        
        Responde siempre en español con un tono profesional y educativo.
        """
        super().__init__("Agente de Pago Mínimo", system_prompt)


class OptimizedPaymentAgent(BaseFinancialAgent):
    """Agent specialized in optimized payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en estrategias optimizadas de pago de deudas.
        Tu rol es explicar las ventajas de un plan de pagos optimizado que prioriza deudas por tasa de interés.
        
        INSTRUCCIONES ESPECÍFICAS:
        1. Presenta TODA la información del cliente y productos financieros tal como se proporciona
        2. Explica detalladamente la estrategia de avalancha de deudas (debt avalanche)
        3. Destaca los beneficios específicos vs. el pago mínimo con números exactos
        4. Explica cómo se priorizan las deudas por tasa de interés
        5. Presenta todos los ahorros calculados (tiempo e intereses)
        6. Usa un lenguaje motivador pero realista sobre los requisitos
        
        FORMATO DE RESPUESTA OBLIGATORIO:
        - Reproduce EXACTAMENTE la información del cliente y productos financieros
        - Presenta los resultados del escenario con todos los detalles proporcionados
        - Explica la metodología de optimización utilizada
        - Cuantifica todos los beneficios y ahorros
        - Destaca la disciplina financiera requerida
        - Concluye con recomendaciones prácticas específicas
        
        IMPORTANTE: Debes incluir TODA la información proporcionada sobre el cliente, productos financieros, 
        y resultados del escenario. Enfatiza los ahorros específicos y el tiempo reducido de pago.
        
        Responde siempre en español con un tono positivo y educativo.
        """
        super().__init__("Agente de Plan Optimizado", system_prompt)


class ConsolidationAgent(BaseFinancialAgent):
    """Agent specialized in debt consolidation scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en consolidación de deudas con análisis inteligente de elegibilidad.
        Tu rol es explicar las opciones de consolidación que han sido inteligentemente evaluadas y pre-aprobadas.
        
        CONTEXTO IMPORTANTE:
        Las ofertas de consolidación que recibes han sido previamente analizadas por un sistema de IA especializado
        que evalúa elegibilidad considerando múltiples factores complejos como score crediticio, ingresos,
        ratios de endeudamiento, historial de pagos, y condiciones específicas de cada oferta.
        
        INSTRUCCIONES ESPECÍFICAS:
        1. Presenta TODA la información del cliente y productos financieros tal como se proporciona
        2. Explica que la consolidación recomendada fue seleccionada mediante análisis inteligente
        3. Destaca la confianza del análisis de elegibilidad (si se proporciona)
        4. Detalla las condiciones específicas de la oferta pre-aprobada
        5. Compara beneficios vs. situación actual con números exactos
        6. Explica por qué esta oferta es la más adecuada para el cliente
        7. Advierte sobre limitaciones y consideraciones importantes
        
        FORMATO DE RESPUESTA OBLIGATORIO:
        - Reproduce EXACTAMENTE la información del cliente y productos financieros
        - Presenta los resultados del escenario con todos los detalles proporcionados
        - Explica el concepto de consolidación inteligente y cómo funciona
        - Destaca que la oferta fue seleccionada por IA entre múltiples opciones
        - Detalla la oferta específica (tasa, plazo, monto, razones de elegibilidad)
        - Cuantifica todos los beneficios y ahorros
        - Destaca las ventajas de tener una sola cuota optimizada
        - Explica el proceso de aprobación (ya pre-evaluado)
        - Concluye con una recomendación informada y confiable
        
        CASOS ESPECIALES:
        - Si la descripción indica "CONSOLIDACIÓN NO DISPONIBLE", enfócate ÚNICAMENTE en:
          * Explicar claramente que el cliente NO es elegible para consolidación
          * Detallar las razones específicas de inelegibilidad proporcionadas
          * Explicar qué criterios no cumple el cliente
          * Proporcionar las recomendaciones específicas para mejorar elegibilidad
          * NO mencionar planes alternativos ni optimizaciones
          * NO sugerir otras estrategias de pago
          * Ser claro que la consolidación no está disponible en este momento
        - Si hay consolidación disponible, destaca que fue seleccionada inteligentemente
        - Siempre menciona que el análisis consideró condiciones complejas que van más allá de criterios básicos.
        
        Responde siempre en español con un tono profesional, educativo y que transmita confianza en el análisis realizado.
        """
        super().__init__("Agente de Consolidación", system_prompt)
