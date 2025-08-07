"""Intelligent eligibility analysis agent for bank offers."""

import os
from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
import json


class EligibilityResult(BaseModel):
    """Structured result from eligibility analysis."""
    is_eligible: bool
    confidence_score: float  # 0.0 to 1.0
    reasons_eligible: List[str]
    reasons_not_eligible: List[str]
    conditions_evaluated: List[str]
    recommendations: List[str]


class EligibilityAgent:
    """Specialized agent for analyzing customer eligibility for financial offers."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.system_prompt = """
        Eres un especialista en análisis de elegibilidad crediticia para productos bancarios.
        Tu rol es evaluar si un cliente cumple con las condiciones específicas de una oferta bancaria.
        
        RESPONSABILIDADES PRINCIPALES:
        1. Analizar detalladamente las condiciones de la oferta en lenguaje natural
        2. Evaluar el perfil del cliente contra estas condiciones
        3. Proporcionar una decisión clara de elegibilidad con justificación
        4. Identificar qué condiciones se cumplen y cuáles no
        5. Sugerir acciones para mejorar la elegibilidad si es necesario
        
        CRITERIOS DE EVALUACIÓN:
        - Score crediticio: Evalúa rangos y requisitos mínimos
        - Historial de mora: Considera días de atraso actuales y históricos
        - Ingresos: Analiza estabilidad y montos mínimos requeridos
        - Experiencia crediticia: Evalúa antigüedad y comportamiento
        - Capacidad de pago: Considera ratios de endeudamiento
        - Condiciones especiales: Cualquier requisito adicional específico
        
        FORMATO DE RESPUESTA:
        Debes responder ÚNICAMENTE con un JSON válido que contenga:
        {{
            "is_eligible": boolean,
            "confidence_score": float (0.0 a 1.0),
            "reasons_eligible": ["razón1", "razón2", ...],
            "reasons_not_eligible": ["razón1", "razón2", ...],
            "conditions_evaluated": ["condición1", "condición2", ...],
            "recommendations": ["recomendación1", "recomendación2", ...]
        }}
        
        IMPORTANTE:
        - Sé conservador en tu evaluación para proteger tanto al banco como al cliente
        - Si hay ambigüedad en las condiciones, solicita clarificación en recommendations
        - Considera el contexto financiero completo, no solo criterios individuales
        - Proporciona confidence_score basado en qué tan clara es la elegibilidad
        """
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm
    
    async def evaluate_eligibility(
        self,
        offer_conditions: str,
        customer_profile: Dict[str, Any],
        offer_details: Dict[str, Any]
    ) -> EligibilityResult:
        """Evaluate customer eligibility for a specific offer."""
        
        # Format input for the LLM
        input_text = self._format_eligibility_input(
            offer_conditions, customer_profile, offer_details
        )
        
        try:
            # Get LLM analysis
            response = await self.chain.ainvoke({"input": input_text})
            
            # Parse JSON response
            result_data = json.loads(response.content)
            
            # Create structured result
            return EligibilityResult(**result_data)
            
        except Exception as e:
            # Fallback to conservative eligibility check
            return self._fallback_eligibility_check(
                offer_conditions, customer_profile, str(e)
            )
    
    async def batch_evaluate_offers(
        self,
        offers: List[Dict[str, Any]],
        customer_profile: Dict[str, Any]
    ) -> List[Tuple[str, EligibilityResult]]:
        """Evaluate multiple offers for a customer."""
        results = []
        
        for offer in offers:
            offer_id = offer.get('offer_id', 'unknown')
            conditions = offer.get('conditions', '')
            
            eligibility = await self.evaluate_eligibility(
                conditions, customer_profile, offer
            )
            
            results.append((offer_id, eligibility))
        
        return results
    
    def _format_eligibility_input(
        self,
        conditions: str,
        customer_profile: Dict[str, Any],
        offer_details: Dict[str, Any]
    ) -> str:
        """Format input data for LLM analysis."""
        
        input_text = f"""
OFERTA BANCARIA A EVALUAR:
ID: {offer_details.get('offer_id', 'N/A')}
Productos elegibles: {', '.join(offer_details.get('product_types_eligible', []))}
Monto máximo consolidación: ${offer_details.get('max_consolidated_balance', 0):,.2f}
Nueva tasa de interés: {offer_details.get('new_rate_pct', 0)}% anual
Plazo máximo: {offer_details.get('max_term_months', 0)} meses

CONDICIONES DE ELEGIBILIDAD:
{conditions}

PERFIL DEL CLIENTE:
- ID Cliente: {customer_profile.get('customer_id', 'N/A')}
- Score crediticio: {customer_profile.get('credit_score', 'N/A')}
- Fecha del score: {customer_profile.get('credit_score_date', 'N/A')}
- Ingresos mensuales promedio: ${customer_profile.get('monthly_income', 0):,.2f}
- Variabilidad de ingresos: {customer_profile.get('income_variability', 0)}%
- Gastos esenciales: ${customer_profile.get('essential_expenses', 0):,.2f}
- Flujo de caja disponible: ${customer_profile.get('available_cashflow', 0):,.2f}
- Flujo de caja conservador: ${customer_profile.get('conservative_cashflow', 0):,.2f}

SITUACIÓN DE DEUDAS:
- Deuda total: ${customer_profile.get('total_debt_balance', 0):,.2f}
- Número de productos: {customer_profile.get('total_debts', 0)}
- Pago mínimo total: ${customer_profile.get('total_minimum_payment', 0):,.2f}
- ¿Tiene mora activa?: {'Sí' if customer_profile.get('has_past_due', False) else 'No'}
- Días máximos de mora: {customer_profile.get('max_days_past_due', 0)}
- Ratio deuda/ingresos anuales: {customer_profile.get('debt_to_income_ratio', 0)}%
- Ratio pagos/ingresos mensuales: {customer_profile.get('payment_to_income_ratio', 0)}%

COMPORTAMIENTO DE PAGOS:
- Consistencia de pagos: {customer_profile.get('payment_consistency', 'N/A')}
- Total pagos recientes: ${customer_profile.get('recent_payment_total', 0):,.2f}

INSTRUCCIONES:
Evalúa si este cliente es elegible para la oferta bancaria basándote en:
1. Las condiciones específicas mencionadas
2. El perfil crediticio completo del cliente
3. Su capacidad de pago y estabilidad financiera
4. Su historial de comportamiento de pagos

Proporciona tu análisis en el formato JSON requerido.
        """
        
        return input_text
    
    def _fallback_eligibility_check(
        self,
        conditions: str,
        customer_profile: Dict[str, Any],
        error_message: str
    ) -> EligibilityResult:
        """Fallback eligibility check if LLM fails."""
        
        # Basic rule-based check as fallback
        is_eligible = True
        reasons_not_eligible = []
        reasons_eligible = []
        
        conditions_lower = conditions.lower()
        
        # Check credit score
        if "score >" in conditions_lower:
            try:
                required_score = int(conditions_lower.split("score >")[1].split()[0])
                customer_score = customer_profile.get("credit_score", 0)
                if customer_score <= required_score:
                    is_eligible = False
                    reasons_not_eligible.append(f"Score crediticio {customer_score} no cumple mínimo de {required_score}")
                else:
                    reasons_eligible.append(f"Score crediticio {customer_score} cumple mínimo de {required_score}")
            except (ValueError, IndexError):
                pass
        
        # Check past due status
        if "sin mora" in conditions_lower or "no mora" in conditions_lower:
            if customer_profile.get("has_past_due", False):
                is_eligible = False
                reasons_not_eligible.append("Cliente tiene mora activa")
            else:
                reasons_eligible.append("Cliente no tiene mora activa")
        
        return EligibilityResult(
            is_eligible=is_eligible,
            confidence_score=0.7 if is_eligible else 0.8,  # Lower confidence due to fallback
            reasons_eligible=reasons_eligible,
            reasons_not_eligible=reasons_not_eligible,
            conditions_evaluated=[conditions],
            recommendations=[
                f"Análisis realizado con sistema de respaldo debido a error: {error_message}",
                "Se recomienda revisión manual para confirmación"
            ]
        )
