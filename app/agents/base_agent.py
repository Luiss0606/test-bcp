"""Base agent class for financial scenario analysis."""

import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import AIMessage


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
        
        formatted_text = f"""
        INFORMACIÓN DEL CLIENTE:
        ID: {customer_info.get('customer_id', 'N/A')}
        Ingresos mensuales promedio: ${customer_info.get('monthly_income', 0):,.2f}
        Gastos esenciales: ${customer_info.get('essential_expenses', 0):,.2f}
        Flujo de caja disponible: ${customer_info.get('available_cashflow', 0):,.2f}
        Score crediticio: {customer_info.get('credit_score', 'N/A')}
        
        ESCENARIO: {scenario.get('scenario_name', 'N/A')}
        
        RESULTADOS FINANCIEROS:
        - Pago mensual total: ${scenario.get('total_monthly_payment', 0):,.2f}
        - Tiempo total de pago: {scenario.get('total_payoff_months', 0)} meses
        - Intereses totales: ${scenario.get('total_interest', 0):,.2f}
        - Pagos totales: ${scenario.get('total_payments', 0):,.2f}
        - Ahorro vs. pago mínimo: ${scenario.get('savings_vs_minimum', 0):,.2f}
        
        DETALLES DE DEUDAS:
        """
        
        # Add payment plans details
        for plan in scenario.get('payment_plans', []):
            formatted_text += f"""
        - Deuda {plan.get('debt_id', 'N/A')}: 
          * Pago mensual: ${plan.get('monthly_payment', 0):,.2f}
          * Meses para liquidar: {plan.get('payoff_months', 0)}
          * Intereses totales: ${plan.get('total_interest', 0):,.2f}
            """
        
        return formatted_text


class MinimumPaymentAgent(BaseFinancialAgent):
    """Agent specialized in minimum payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en analizar escenarios de pago mínimo de deudas.
        Tu rol es explicar de manera clara y comprensible las implicaciones de pagar solo los montos mínimos requeridos.
        
        INSTRUCCIONES:
        1. Analiza el escenario de pago mínimo presentado
        2. Explica las consecuencias financieras a largo plazo
        3. Destaca los riesgos de esta estrategia
        4. Usa un lenguaje claro y accesible para el cliente
        5. Incluye advertencias sobre el alto costo de intereses
        6. Proporciona contexto sobre el tiempo de pago
        
        FORMATO DE RESPUESTA:
        - Comienza con un resumen ejecutivo
        - Explica los números clave
        - Destaca las implicaciones negativas
        - Concluye con una recomendación clara
        
        Responde siempre en español y de forma empática pero directa sobre los riesgos.
        """
        super().__init__("Agente de Pago Mínimo", system_prompt)


class OptimizedPaymentAgent(BaseFinancialAgent):
    """Agent specialized in optimized payment scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en estrategias optimizadas de pago de deudas.
        Tu rol es explicar las ventajas de un plan de pagos optimizado que prioriza deudas por tasa de interés.
        
        INSTRUCCIONES:
        1. Analiza el escenario optimizado presentado
        2. Explica la estrategia de avalancha de deudas (debt avalanche)
        3. Destaca los beneficios vs. el pago mínimo
        4. Explica cómo se priorizan las deudas
        5. Calcula y presenta los ahorros obtenidos
        6. Usa un lenguaje motivador pero realista
        
        FORMATO DE RESPUESTA:
        - Comienza explicando la estrategia utilizada
        - Presenta los beneficios cuantificados
        - Explica el cronograma de pagos
        - Destaca los ahorros en tiempo e intereses
        - Concluye con recomendaciones prácticas
        
        Responde siempre en español con un tono positivo y educativo.
        """
        super().__init__("Agente de Plan Optimizado", system_prompt)


class ConsolidationAgent(BaseFinancialAgent):
    """Agent specialized in debt consolidation scenario analysis."""
    
    def __init__(self):
        system_prompt = """
        Eres un asesor financiero especializado en consolidación de deudas.
        Tu rol es explicar las opciones de consolidación disponibles y sus beneficios.
        
        INSTRUCCIONES:
        1. Analiza el escenario de consolidación presentado
        2. Explica qué deudas se pueden consolidar
        3. Detalla las condiciones de la nueva oferta
        4. Compara beneficios vs. situación actual
        5. Explica requisitos de elegibilidad
        6. Advierte sobre posibles limitaciones
        
        FORMATO DE RESPUESTA:
        - Comienza explicando qué es la consolidación
        - Presenta la oferta específica disponible
        - Compara costos y beneficios
        - Explica los requisitos cumplidos
        - Destaca ventajas y desventajas
        - Concluye con una recomendación informada
        
        Si no hay consolidación disponible, explica por qué y sugiere alternativas.
        Responde siempre en español con un tono profesional y educativo.
        """
        super().__init__("Agente de Consolidación", system_prompt)
