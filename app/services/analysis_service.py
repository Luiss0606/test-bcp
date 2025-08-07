"""Main analysis service that orchestrates debt analysis and report generation."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Customer, CustomerCashflow, CreditScore
from app.services.debt_calculator import DebtCalculator
from app.agents import AgentOrchestrator, MasterConsolidatorAgent
from app.schemas.debt import CustomerAnalysis, ScenarioResult


class FinancialAnalysisService:
    """Main service for comprehensive financial debt analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.debt_calculator = DebtCalculator(db)
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
        
        # 3. Execute parallel agent analysis
        agent_results = await self.agent_orchestrator.executor.execute_parallel_analysis(
            scenarios, customer_info
        )
        
        # 4. Generate master consolidated report
        consolidated_report = await self.master_agent.consolidate_reports(
            customer_id, scenarios, agent_results, customer_info
        )
        
        # 5. Prepare final response
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
        """Calculate all three debt scenarios."""
        scenarios = {}
        
        try:
            # Minimum payment scenario
            min_scenario = self.debt_calculator.calculate_minimum_payment_scenario(customer_id)
            scenarios["minimum"] = self._scenario_to_dict(min_scenario)
            
            # Optimized payment scenario  
            opt_scenario = self.debt_calculator.calculate_optimized_scenario(customer_id)
            scenarios["optimized"] = self._scenario_to_dict(opt_scenario)
            
            # Consolidation scenario
            cons_scenario = self.debt_calculator.calculate_consolidation_scenario(customer_id)
            scenarios["consolidation"] = self._scenario_to_dict(cons_scenario)
            
        except Exception as e:
            scenarios["error"] = f"Error calculando escenarios: {str(e)}"
        
        return scenarios
    
    def _get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive customer information."""
        
        # Get customer record
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return None
        
        # Get cashflow data
        cashflow = self.db.query(CustomerCashflow).filter(
            CustomerCashflow.customer_id == customer_id
        ).first()
        
        # Get latest credit score
        latest_score = self.db.query(CreditScore).filter(
            CreditScore.customer_id == customer_id
        ).order_by(CreditScore.date.desc()).first()
        
        # Get debts summary
        debts = self.debt_calculator.get_customer_debts(customer_id)
        
        customer_info = {
            "customer_id": customer_id,
            "monthly_income": cashflow.monthly_income_avg if cashflow else 0,
            "essential_expenses": cashflow.essential_expenses_avg if cashflow else 0,
            "available_cashflow": cashflow.available_cashflow if cashflow else 0,
            "conservative_cashflow": cashflow.conservative_cashflow if cashflow else 0,
            "income_variability": cashflow.income_variability_pct if cashflow else 0,
            "credit_score": latest_score.credit_score if latest_score else None,
            "total_debts": len(debts),
            "total_debt_balance": sum(debt.balance for debt in debts),
            "total_minimum_payment": sum(debt.minimum_payment for debt in debts),
            "has_past_due": any(debt.days_past_due > 0 for debt in debts),
            "max_days_past_due": max((debt.days_past_due for debt in debts), default=0)
        }
        
        return customer_info
    
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
        
        return {
            "scenario_name": scenario.scenario_name,
            "total_monthly_payment": scenario.total_monthly_payment,
            "total_payoff_months": scenario.total_payoff_months,
            "total_interest": scenario.total_interest,
            "total_payments": scenario.total_payments,
            "savings_vs_minimum": scenario.savings_vs_minimum,
            "description": scenario.description,
            "payment_plans": payment_plans
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
