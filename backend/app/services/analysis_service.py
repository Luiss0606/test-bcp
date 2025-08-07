"""Main analysis service that orchestrates debt analysis and report generation."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.database import get_supabase
from app.models import (
    Customer, CustomerCashflow, CreditScore, Loan, Card,
    PaymentHistory, BankOffer
)
from app.services.debt_calculator import DebtCalculator
from app.agents import AgentOrchestrator, MasterConsolidatorAgent
# Imports removed: CustomerAnalysis, ScenarioResult (not used)


class FinancialAnalysisService:
    """Main service for comprehensive financial debt analysis."""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.debt_calculator = DebtCalculator()
        self.agent_orchestrator = AgentOrchestrator()
        self.master_agent = MasterConsolidatorAgent()
    
    async def analyze_customer_debt(self, customer_id: str) -> Dict[str, Any]:
        """Perform complete debt analysis for a customer."""
        
        # 1. Get customer data
        customer_info = self._get_customer_info(customer_id)
        if not customer_info:
            return {
                "error": f"Cliente {customer_id} no encontrado",
                "customer_id": customer_id
            }
        
        # 2. Calculate all scenarios
        scenarios = await self._calculate_all_scenarios(customer_id)
        
        # 3. Get detailed debt information
        debt_details = self._get_debt_details(customer_id)
        
        # 4. Execute parallel agent analysis
        agent_results = await self.agent_orchestrator.executor.execute_parallel_analysis(
            scenarios, customer_info, debt_details
        )
        
        # 5. Generate master consolidated report
        consolidated_report = await self.master_agent.consolidate_reports(
            customer_id, scenarios, agent_results, customer_info
        )
        
        # 6. Prepare final response
        analysis_result = {
            "customer_id": customer_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "customer_profile": customer_info,
            "scenarios": scenarios,
            "individual_analyses": agent_results,
            "consolidated_report": consolidated_report,
            "recommendations": self._extract_recommendations(scenarios),
            "summary_metrics": self._calculate_summary_metrics(scenarios)
        }
        
        return analysis_result
    
    async def _calculate_all_scenarios(self, customer_id: str) -> Dict[str, Any]:
        """Calculate all three debt scenarios using intelligent consolidation analysis."""
        scenarios = {}
        
        try:
            # Calculate minimum payment scenario first (needed for comparisons)
            min_scenario = self.debt_calculator.calculate_minimum_payment_scenario(customer_id)
            self._minimum_scenario_reference = min_scenario  # Store for metadata generation
            scenarios["minimum"] = self._scenario_to_dict(min_scenario)
            
            # Optimized payment scenario  
            opt_scenario = self.debt_calculator.calculate_optimized_scenario(customer_id)
            scenarios["optimized"] = self._scenario_to_dict(opt_scenario)
            
            # Consolidation scenario with intelligent eligibility analysis
            cons_scenario = await self._calculate_intelligent_consolidation_scenario(customer_id)
            scenarios["consolidation"] = self._scenario_to_dict(cons_scenario)
            
        except Exception as e:
            scenarios["error"] = f"Error calculando escenarios: {str(e)}"
        
        return scenarios
    
    async def _calculate_intelligent_consolidation_scenario(self, customer_id: str):
        """Calculate consolidation scenario using intelligent eligibility analysis."""
        try:
            from app.agents.eligibility_agent import EligibilityAgent
            from app.models import BankOffer
            
            # Get customer profile for eligibility analysis
            customer_profile = self._get_customer_info(customer_id)
            if not customer_profile:
                # Fallback to basic consolidation
                return self.debt_calculator.calculate_consolidation_scenario(customer_id)
            
            # Get all available offers from Supabase
            offers_response = self.supabase.table('bank_offers').select('*').execute()
            offers = [BankOffer.from_dict(offer) for offer in offers_response.data] if offers_response.data else []
            
            offer_dicts = [offer.to_dict() for offer in offers]
            
            # Perform intelligent eligibility analysis
            eligibility_agent = EligibilityAgent()
            eligibility_results = await eligibility_agent.batch_evaluate_offers(
                offer_dicts, customer_profile
            )
            
            # Filter eligible offers with good confidence
            eligible_offers_data = []
            for offer_id, eligibility in eligibility_results:
                if eligibility.is_eligible and eligibility.confidence_score >= 0.7:
                    # Find the corresponding offer
                    offer = next((o for o in offers if o.id == offer_id), None)
                    if offer:
                        eligible_offers_data.append({
                            "offer_id": offer_id,
                            "offer": offer,
                            "eligibility": eligibility,
                            "score": offer.new_rate_pct * (2 - eligibility.confidence_score)  # Lower is better
                        })
            
            # Sort by combined score (rate + confidence)
            eligible_offers_data.sort(key=lambda x: x["score"])
            
            # Use the filtered offers in consolidation calculation
            if eligible_offers_data:
                # Pass the best eligible offers to the debt calculator
                best_offers_info = [
                    {
                        "offer_id": item["offer_id"],
                        "eligibility_score": item["eligibility"].confidence_score,
                        "reasons": item["eligibility"].reasons_eligible
                    }
                    for item in eligible_offers_data[:3]  # Top 3 offers
                ]
                
                scenario = self.debt_calculator.calculate_consolidation_scenario(
                    customer_id, best_offers_info
                )
                
                # Enhance description with intelligent analysis insights
                best_eligibility = eligible_offers_data[0]["eligibility"]
                enhanced_description = f"""Consolidación inteligente con {eligible_offers_data[0]["offer_id"]}:
- Elegibilidad confirmada con {best_eligibility.confidence_score:.1%} de confianza
- Razones principales: {', '.join(best_eligibility.reasons_eligible[:2])}
- Tasa: {eligible_offers_data[0]["offer"].new_rate_pct}% anual
- Evaluación automatizada de {len(eligibility_results)} ofertas disponibles"""
                
                scenario.description = enhanced_description
                return scenario
            else:
                # No eligible offers found through intelligent analysis
                # Create a special "no consolidation" scenario instead of showing alternatives
                
                # Collect detailed reasons why consolidation is not available
                all_reasons = []
                all_recommendations = []
                
                for offer_id, eligibility in eligibility_results:
                    if not eligibility.is_eligible:
                        all_reasons.extend(eligibility.reasons_not_eligible)
                        all_recommendations.extend(eligibility.recommendations)
                
                # Remove duplicates while preserving order
                unique_reasons = list(dict.fromkeys(all_reasons))
                unique_recommendations = list(dict.fromkeys(all_recommendations))
                
                # Create a "no consolidation available" scenario
                from app.services.debt_calculator import ScenarioResult, PaymentPlan
                
                scenario = ScenarioResult(
                    scenario_name="Consolidación",
                    total_monthly_payment=0,
                    total_payoff_months=0,
                    total_interest=0,
                    total_payments=0,
                    savings_vs_minimum=0,
                    payment_plans=[],
                    description=f"""CONSOLIDACIÓN NO DISPONIBLE - Análisis de Elegibilidad:

EVALUACIÓN REALIZADA:
- Se analizaron {len(eligibility_results)} ofertas bancarias disponibles
- Ninguna oferta cumple los criterios de elegibilidad requeridos

RAZONES DE INELEGIBILIDAD:
{chr(10).join(f'• {reason}' for reason in unique_reasons[:5])}

RECOMENDACIONES PARA MEJORAR ELEGIBILIDAD:
{chr(10).join(f'• {rec}' for rec in unique_recommendations[:4])}

RESULTADO: No es posible ofrecer consolidación en este momento.
Para explorar otras opciones de manejo de deudas, consulte los escenarios de pago mínimo y optimizado."""
                )
                
                return scenario
                
        except Exception as e:
            # Fallback to basic consolidation on any error
            print(f"Error en análisis inteligente de consolidación: {str(e)}")
            return self.debt_calculator.calculate_consolidation_scenario(customer_id)
    
    def _get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive customer information."""
        
        # Get customer record
        customer_response = self.supabase.table('customers').select('*').eq('id', customer_id).single().execute()
        if not customer_response.data:
            return None
        
        customer_data = customer_response.data
        
        # Get cashflow data
        cashflow_response = self.supabase.table('customer_cashflow').select('*').eq('customer_id', customer_id).single().execute()
        cashflow = CustomerCashflow.from_dict(cashflow_response.data) if cashflow_response.data else None
        
        # Get latest credit score
        credit_response = self.supabase.table('credit_scores').select('*').eq(
            'customer_id', customer_id
        ).order('date', desc=True).limit(1).execute()
        latest_score = credit_response.data[0] if credit_response.data else None
        
        # Get debts summary
        debts = self.debt_calculator.get_customer_debts(customer_id)
        
        # Get payment behavior analysis
        total_recent_payments = 0
        payment_consistency = "N/A"
        
        if debts:
            payment_response = self.supabase.table('payment_history').select('*').eq(
                'customer_id', customer_id
            ).order('date', desc=True).limit(6).execute()
            recent_payments = payment_response.data if payment_response.data else []
            
            if recent_payments:
                total_recent_payments = sum(p['amount'] for p in recent_payments)
                # Simple consistency check - if they've made regular payments
                payment_consistency = "Buena" if len(recent_payments) >= 2 else "Limitada"
        
        customer_info = {
            "customer_id": customer_id,
            "monthly_income": cashflow.monthly_income_avg if cashflow else 0,
            "essential_expenses": cashflow.essential_expenses_avg if cashflow else 0,
            "available_cashflow": cashflow.available_cashflow if cashflow else 0,
            "conservative_cashflow": cashflow.conservative_cashflow if cashflow else 0,
            "income_variability": cashflow.income_variability_pct if cashflow else 0,
            "credit_score": latest_score['credit_score'] if latest_score else None,
            "credit_score_date": latest_score['date'] if latest_score else "N/A",
            "total_debts": len(debts),
            "total_debt_balance": sum(debt.balance for debt in debts),
            "total_minimum_payment": sum(debt.minimum_payment for debt in debts),
            "has_past_due": any(debt.days_past_due > 0 for debt in debts),
            "max_days_past_due": max((debt.days_past_due for debt in debts), default=0),
            "payment_consistency": payment_consistency,
            "recent_payment_total": total_recent_payments,
            "debt_to_income_ratio": round((sum(debt.balance for debt in debts) / (cashflow.monthly_income_avg * 12)) * 100, 1) if cashflow and cashflow.monthly_income_avg > 0 else 0,
            "payment_to_income_ratio": round((sum(debt.minimum_payment for debt in debts) / cashflow.monthly_income_avg) * 100, 1) if cashflow and cashflow.monthly_income_avg > 0 else 0
        }
        
        return customer_info
    
    def _get_debt_details(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get detailed debt information for agents."""
        from app.models.debt import Loan, Card
        from app.models.payment import PaymentHistory
        
        debt_details = []
        
        # Get loans with full details
        loans_response = self.supabase.table('loans').select('*').eq('customer_id', customer_id).execute()
        loans = [Loan.from_dict(loan) for loan in loans_response.data] if loans_response.data else []
        
        for loan in loans:
            # Get recent payment history
            payment_response = self.supabase.table('payment_history').select('*').match({
                'product_id': loan.id,
                'customer_id': customer_id
            }).order('date', desc=True).limit(3).execute()
            recent_payments = payment_response.data if payment_response.data else []
            
            debt_detail = {
                "debt_id": loan.id,
                "debt_type": "loan",
                "product_type": loan.product_type,  # personal, micro, etc.
                "balance": loan.principal,
                "annual_rate_pct": loan.annual_rate_pct,
                "minimum_payment": loan.minimum_payment,
                "remaining_term_months": loan.remaining_term_months,
                "collateral": loan.collateral,
                "days_past_due": loan.days_past_due,
                "priority_score": loan.priority_score,
                "recent_payments": [
                    {
                        "date": payment['date'],
                        "amount": payment['amount']
                    } for payment in recent_payments
                ]
            }
            debt_details.append(debt_detail)
        
        # Get cards with full details
        cards_response = self.supabase.table('cards').select('*').eq('customer_id', customer_id).execute()
        cards = [Card.from_dict(card) for card in cards_response.data] if cards_response.data else []
        
        for card in cards:
            # Get recent payment history
            payment_response = self.supabase.table('payment_history').select('*').match({
                'product_id': card.id,
                'customer_id': customer_id
            }).order('date', desc=True).limit(3).execute()
            recent_payments = payment_response.data if payment_response.data else []
            
            debt_detail = {
                "debt_id": card.id,
                "debt_type": "card",
                "balance": card.balance,
                "annual_rate_pct": card.annual_rate_pct,
                "minimum_payment": card.minimum_payment,
                "min_payment_pct": card.min_payment_pct,
                "payment_due_day": card.payment_due_day,
                "days_past_due": card.days_past_due,
                "priority_score": card.priority_score,
                "recent_payments": [
                    {
                        "date": payment['date'],
                        "amount": payment['amount']
                    } for payment in recent_payments
                ]
            }
            debt_details.append(debt_detail)
        
        return debt_details
    
    def _generate_scenario_metadata(self, scenario) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate strategy details and additional info for scenarios."""
        scenario_name = scenario.scenario_name.lower()
        
        if "mínimo" in scenario_name or "minimum" in scenario_name:
            strategy_details = {
                'description': 'Pago mínimo mensual en todas las deudas',
                'risk_level': 'Alto',
                'pros': ['Pagos mensuales más bajos'],
                'cons': ['Mayor costo total por intereses', 'Tiempo de pago más largo']
            }
            
        elif "optimizado" in scenario_name or "optimized" in scenario_name:
            strategy_details = {
                'description': 'Estrategia avalanche: prioriza deudas con mayor tasa de interés',
                'risk_level': 'Medio',
                'method': 'Avalanche',
                'pros': ['Menor costo total por intereses', 'Tiempo de pago reducido'],
                'cons': ['Pagos mensuales más altos', 'Requiere disciplina financiera']
            }
            
        elif "consolidación" in scenario_name or "consolidation" in scenario_name:
            # Check if consolidation is actually available or not
            if "CONSOLIDACIÓN NO DISPONIBLE" in scenario.description:
                # No consolidation available - show clear ineligibility message
                strategy_details = {
                    'description': 'Cliente no elegible para consolidación de deudas',
                    'risk_level': 'N/A',
                    'availability': 'No elegible',
                    'status': 'Consolidación no disponible',
                    'pros': [],
                    'cons': [],
                    'note': 'Se requiere mejorar perfil crediticio para acceder a consolidación'
                }
            else:
                # Real consolidation available
                # Extract consolidation details from description
                offer_id = "OF-CONSO-36M"  # Default
                new_rate = 17.5  # Default
                term_months = scenario.total_payoff_months
                consolidated_amount = sum(plan.total_payments - plan.total_interest for plan in scenario.payment_plans if hasattr(plan, 'debt_id') and plan.debt_id == "CONSOLIDATED")
                
                if consolidated_amount == 0:
                    # If no consolidated debt found, use total debt
                    consolidated_amount = scenario.total_payments - scenario.total_interest
                
                strategy_details = {
                    'description': f'Consolidación con oferta {offer_id}',
                    'risk_level': 'Bajo',
                    'offer_id': offer_id,
                    'new_rate': new_rate,
                    'term_months': term_months,
                    'consolidated_amount': consolidated_amount,
                    'pros': ['Una sola cuota mensual', 'Tasa de interés reducida', 'Mejor control del presupuesto'],
                    'cons': ['Puede extender el tiempo de pago', 'Requiere aprobación crediticia']
                }
        else:
            strategy_details = {
                'description': scenario.description,
                'risk_level': 'Medio'
            }
        
        # Generate additional info with savings comparison
        additional_info = {}
        if scenario.savings_vs_minimum > 0:
            # Calculate time savings using minimum scenario reference
            time_savings_months = 0
            if hasattr(self, '_minimum_scenario_reference') and self._minimum_scenario_reference:
                time_savings_months = max(0, self._minimum_scenario_reference.total_payoff_months - scenario.total_payoff_months)
            
            additional_info = {
                'savings_vs_minimum': {
                    'interest_savings': scenario.savings_vs_minimum,
                    'time_savings_months': time_savings_months,
                    'total_savings': scenario.savings_vs_minimum
                }
            }
        
        return strategy_details, additional_info
    
    def _scenario_to_dict(self, scenario) -> Dict[str, Any]:
        """Convert scenario result to dictionary."""
        payment_plans = []
        for plan in scenario.payment_plans:
            if hasattr(plan, 'debt_id'):
                # PaymentPlan object
                plan_dict = {
                    "debt_id": plan.debt_id,
                    "monthly_payment": plan.monthly_payment,
                    "payoff_months": plan.payoff_months,
                    "total_interest": plan.total_interest,
                    "total_payments": plan.total_payments
                }
            else:
                # Already a dictionary
                plan_dict = plan
            payment_plans.append(plan_dict)
        
        # Generate strategy details and additional info based on scenario type
        strategy_details, additional_info = self._generate_scenario_metadata(scenario)
        
        return {
            "scenario_name": scenario.scenario_name,
            "total_monthly_payment": scenario.total_monthly_payment,
            "total_payoff_months": scenario.total_payoff_months,
            "total_interest": scenario.total_interest,
            "total_payments": scenario.total_payments,
            "savings_vs_minimum": scenario.savings_vs_minimum,
            "description": scenario.description,
            "payment_plans": payment_plans,
            "strategy_details": strategy_details,
            "additional_info": additional_info
        }
    
    def _extract_recommendations(self, scenarios: Dict[str, Any]) -> List[str]:
        """Extract key recommendations from scenarios."""
        recommendations = []
        
        # Find best scenario by savings
        best_scenario = None
        max_savings = 0
        
        for scenario_name, scenario in scenarios.items():
            if isinstance(scenario, dict):
                savings = scenario.get('savings_vs_minimum', 0)
                if savings > max_savings:
                    max_savings = savings
                    best_scenario = scenario_name
        
        if best_scenario and max_savings > 0:
            scenario_names = {
                'optimized': 'plan optimizado',
                'consolidation': 'consolidación de deudas'
            }
            
            recommendations.append(
                f"Implementar {scenario_names.get(best_scenario, best_scenario)} "
                f"para ahorrar ${max_savings:,.2f} en intereses"
            )
        
        recommendations.extend([
            "Evitar pagar solo los montos mínimos",
            "Priorizar deudas con mayores tasas de interés",
            "Considerar incrementar pagos cuando sea posible",
            "Monitorear regularmente el progreso de pagos"
        ])
        
        return recommendations
    
    def _calculate_summary_metrics(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary metrics across all scenarios."""
        
        if not scenarios or "error" in scenarios:
            return {"error": "No se pudieron calcular métricas"}
        
        metrics = {}
        
        # Get minimum scenario as baseline
        if "minimum" in scenarios:
            min_scenario = scenarios["minimum"]
            metrics["baseline_monthly"] = min_scenario.get("total_monthly_payment", 0)
            metrics["baseline_total_interest"] = min_scenario.get("total_interest", 0)
            metrics["baseline_months"] = min_scenario.get("total_payoff_months", 0)
        
        # Calculate best savings
        max_savings = 0
        best_option = None
        
        for scenario_name, scenario in scenarios.items():
            if isinstance(scenario, dict) and scenario_name != "minimum":
                savings = scenario.get("savings_vs_minimum", 0)
                if savings > max_savings:
                    max_savings = savings
                    best_option = scenario_name
        
        metrics["max_potential_savings"] = max_savings
        metrics["best_option"] = best_option
        
        # Calculate time savings
        if "minimum" in scenarios and best_option and best_option in scenarios:
            min_months = scenarios["minimum"].get("total_payoff_months", 0)
            best_months = scenarios[best_option].get("total_payoff_months", 0)
            metrics["time_savings_months"] = max(0, min_months - best_months)
        
        return metrics


class ReportGenerationService:
    """Service for generating and formatting financial reports."""
    
    def __init__(self):
        pass
    
    def format_analysis_for_client(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis results for client presentation."""
        
        formatted_report = {
            "cliente": analysis.get("customer_id"),
            "fecha_analisis": analysis.get("analysis_timestamp"),
            "informe_consolidado": analysis.get("consolidated_report"),
            "resumen_escenarios": [],
            "recomendaciones": analysis.get("recommendations", []),
            "metricas_clave": analysis.get("summary_metrics", {})
        }
        
        # Format scenarios for client
        scenarios = analysis.get("scenarios", {})
        for scenario_name, scenario_data in scenarios.items():
            if isinstance(scenario_data, dict) and "error" not in scenario_data:
                scenario_names = {
                    "minimum": "Pago Mínimo",
                    "optimized": "Plan Optimizado", 
                    "consolidation": "Consolidación"
                }
                
                formatted_scenario = {
                    "nombre": scenario_names.get(scenario_name, scenario_name),
                    "pago_mensual": f"${scenario_data.get('total_monthly_payment', 0):,.2f}",
                    "tiempo_pago": f"{scenario_data.get('total_payoff_months', 0)} meses",
                    "intereses_totales": f"${scenario_data.get('total_interest', 0):,.2f}",
                    "ahorro_vs_minimo": f"${scenario_data.get('savings_vs_minimum', 0):,.2f}"
                }
                
                formatted_report["resumen_escenarios"].append(formatted_scenario)
        
        return formatted_report
