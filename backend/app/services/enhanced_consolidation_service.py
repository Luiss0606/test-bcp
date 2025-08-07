"""Enhanced consolidation service with intelligent eligibility analysis."""

from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models import BankOffer
from app.agents.eligibility_agent import EligibilityAgent, EligibilityResult
from app.services.debt_calculator import DebtCalculator, ScenarioResult


class EnhancedConsolidationService:
    """Enhanced consolidation service with LLM-powered eligibility analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.debt_calculator = DebtCalculator(db)
        self.eligibility_agent = EligibilityAgent()
    
    async def calculate_intelligent_consolidation_scenario(
        self, 
        customer_id: str
    ) -> Tuple[ScenarioResult, Dict[str, Any]]:
        """
        Calculate consolidation scenario with intelligent eligibility analysis.
        
        Returns:
            Tuple[ScenarioResult, Dict]: (scenario_result, eligibility_details)
        """
        
        # Get customer debts and profile
        debts = self.debt_calculator.get_customer_debts(customer_id)
        customer_profile = self._get_enhanced_customer_profile(customer_id)
        
        # Get all available offers
        offers = self.db.query(BankOffer).all()
        offer_dicts = [self._offer_to_dict(offer) for offer in offers]
        
        # Perform intelligent eligibility analysis
        eligibility_results = await self.eligibility_agent.batch_evaluate_offers(
            offer_dicts, customer_profile
        )
        
        # Filter and rank eligible offers
        eligible_offers_with_analysis = []
        for offer_id, eligibility in eligibility_results:
            if eligibility.is_eligible and eligibility.confidence_score >= 0.7:
                offer = next((o for o in offers if o.id == offer_id), None)
                if offer:
                    eligible_offers_with_analysis.append((offer, eligibility))
        
        # Prepare detailed eligibility report
        eligibility_details = self._create_eligibility_report(
            eligibility_results, customer_profile
        )
        
        if not eligible_offers_with_analysis:
            # No eligible offers found
            scenario = self._create_no_consolidation_scenario(
                customer_id, eligibility_details
            )
            return scenario, eligibility_details
        
        # Select best offer (considering both rate and confidence)
        best_offer, best_eligibility = self._select_best_offer(
            eligible_offers_with_analysis
        )
        
        # Calculate consolidation scenario with the best offer
        scenario = await self._calculate_consolidation_with_offer(
            customer_id, best_offer, best_eligibility, debts
        )
        
        return scenario, eligibility_details
    
    async def get_detailed_offer_analysis(
        self, 
        customer_id: str, 
        offer_id: str
    ) -> Dict[str, Any]:
        """Get detailed analysis for a specific offer."""
        
        offer = self.db.query(BankOffer).filter(BankOffer.id == offer_id).first()
        if not offer:
            return {"error": f"Oferta {offer_id} no encontrada"}
        
        customer_profile = self._get_enhanced_customer_profile(customer_id)
        offer_dict = self._offer_to_dict(offer)
        
        eligibility = await self.eligibility_agent.evaluate_eligibility(
            offer.conditions, customer_profile, offer_dict
        )
        
        return {
            "offer_id": offer_id,
            "customer_id": customer_id,
            "eligibility_analysis": {
                "is_eligible": eligibility.is_eligible,
                "confidence_score": eligibility.confidence_score,
                "reasons_eligible": eligibility.reasons_eligible,
                "reasons_not_eligible": eligibility.reasons_not_eligible,
                "conditions_evaluated": eligibility.conditions_evaluated,
                "recommendations": eligibility.recommendations
            },
            "offer_details": offer_dict,
            "customer_profile_summary": {
                "credit_score": customer_profile.get("credit_score"),
                "has_past_due": customer_profile.get("has_past_due"),
                "debt_to_income_ratio": customer_profile.get("debt_to_income_ratio")
            }
        }
    
    def _get_enhanced_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get enhanced customer profile for eligibility analysis."""
        # Reuse the existing customer info method from analysis service
        from app.services.analysis_service import FinancialAnalysisService
        
        # Create temporary instance to access the method
        temp_service = FinancialAnalysisService(self.db)
        return temp_service._get_customer_info(customer_id) or {}
    
    def _offer_to_dict(self, offer: BankOffer) -> Dict[str, Any]:
        """Convert BankOffer model to dictionary."""
        return {
            "offer_id": offer.id,
            "product_types_eligible": offer.product_types_eligible,
            "max_consolidated_balance": offer.max_consolidated_balance,
            "new_rate_pct": offer.new_rate_pct,
            "max_term_months": offer.max_term_months,
            "conditions": offer.conditions
        }
    
    def _create_eligibility_report(
        self, 
        eligibility_results: List[Tuple[str, EligibilityResult]],
        customer_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive eligibility report."""
        
        total_offers = len(eligibility_results)
        eligible_offers = sum(1 for _, result in eligibility_results if result.is_eligible)
        
        offers_analysis = []
        for offer_id, result in eligibility_results:
            offers_analysis.append({
                "offer_id": offer_id,
                "is_eligible": result.is_eligible,
                "confidence_score": result.confidence_score,
                "reasons_eligible": result.reasons_eligible,
                "reasons_not_eligible": result.reasons_not_eligible,
                "recommendations": result.recommendations
            })
        
        # Generate overall recommendations
        overall_recommendations = self._generate_overall_recommendations(
            eligibility_results, customer_profile
        )
        
        return {
            "total_offers_evaluated": total_offers,
            "eligible_offers_count": eligible_offers,
            "eligibility_rate": round((eligible_offers / total_offers) * 100, 1) if total_offers > 0 else 0,
            "offers_analysis": offers_analysis,
            "overall_recommendations": overall_recommendations,
            "customer_strengths": self._identify_customer_strengths(customer_profile),
            "areas_for_improvement": self._identify_improvement_areas(eligibility_results)
        }
    
    def _select_best_offer(
        self, 
        eligible_offers: List[Tuple[BankOffer, EligibilityResult]]
    ) -> Tuple[BankOffer, EligibilityResult]:
        """Select the best offer considering rate and confidence."""
        
        # Score each offer: lower rate is better, higher confidence is better
        def offer_score(offer_tuple):
            offer, eligibility = offer_tuple
            # Normalize rate (lower is better) and confidence (higher is better)
            rate_score = 1 / (offer.new_rate_pct + 1)  # Avoid division by zero
            confidence_score = eligibility.confidence_score
            # Weighted combination (rate is more important)
            return (rate_score * 0.7) + (confidence_score * 0.3)
        
        return max(eligible_offers, key=offer_score)
    
    async def _calculate_consolidation_with_offer(
        self,
        customer_id: str,
        offer: BankOffer,
        eligibility: EligibilityResult,
        debts: List
    ) -> ScenarioResult:
        """Calculate consolidation scenario with specific offer and eligibility context."""
        
        # Use the existing consolidation calculation as base
        base_scenario = self.debt_calculator.calculate_consolidation_scenario(customer_id)
        
        # Enhance the description with eligibility insights
        enhanced_description = f"""
Consolidación inteligente con oferta {offer.id}:
- Tasa: {offer.new_rate_pct}% anual
- Plazo: {offer.max_term_months} meses
- Elegibilidad confirmada con {eligibility.confidence_score:.1%} de confianza
- Razones de elegibilidad: {', '.join(eligibility.reasons_eligible[:2])}
        """.strip()
        
        # Update the scenario with enhanced information
        base_scenario.description = enhanced_description
        
        return base_scenario
    
    def _create_no_consolidation_scenario(
        self, 
        customer_id: str, 
        eligibility_details: Dict[str, Any]
    ) -> ScenarioResult:
        """Create scenario when no consolidation is available."""
        
        # Get optimized scenario as fallback
        optimized_scenario = self.debt_calculator.calculate_optimized_scenario(customer_id)
        
        # Update scenario name and description
        optimized_scenario.scenario_name = "Consolidación"
        
        # Create detailed explanation of why consolidation isn't available
        ineligible_reasons = []
        for offer_analysis in eligibility_details.get("offers_analysis", []):
            if not offer_analysis["is_eligible"]:
                ineligible_reasons.extend(offer_analysis["reasons_not_eligible"])
        
        # Remove duplicates
        unique_reasons = list(set(ineligible_reasons))
        
        enhanced_description = f"""
Consolidación no disponible actualmente:
{chr(10).join(f'• {reason}' for reason in unique_reasons[:3])}

Se presenta el plan optimizado como alternativa.
Recomendaciones para futuras consolidaciones:
{chr(10).join(f'• {rec}' for rec in eligibility_details.get("overall_recommendations", [])[:2])}
        """.strip()
        
        optimized_scenario.description = enhanced_description
        
        return optimized_scenario
    
    def _generate_overall_recommendations(
        self,
        eligibility_results: List[Tuple[str, EligibilityResult]],
        customer_profile: Dict[str, Any]
    ) -> List[str]:
        """Generate overall recommendations for improving eligibility."""
        
        recommendations = set()
        
        # Collect all recommendations from individual analyses
        for _, result in eligibility_results:
            recommendations.update(result.recommendations)
        
        # Add profile-specific recommendations
        if customer_profile.get("credit_score", 0) < 650:
            recommendations.add("Mejorar score crediticio mediante pagos puntuales")
        
        if customer_profile.get("has_past_due", False):
            recommendations.add("Regularizar mora activa antes de solicitar consolidación")
        
        if customer_profile.get("debt_to_income_ratio", 0) > 40:
            recommendations.add("Reducir ratio de endeudamiento para mejorar elegibilidad")
        
        return list(recommendations)[:5]  # Limit to top 5
    
    def _identify_customer_strengths(self, customer_profile: Dict[str, Any]) -> List[str]:
        """Identify customer's financial strengths."""
        
        strengths = []
        
        if customer_profile.get("credit_score", 0) >= 700:
            strengths.append("Excelente score crediticio")
        elif customer_profile.get("credit_score", 0) >= 650:
            strengths.append("Buen score crediticio")
        
        if not customer_profile.get("has_past_due", False):
            strengths.append("Sin mora activa")
        
        if customer_profile.get("payment_consistency") == "Buena":
            strengths.append("Historial de pagos consistente")
        
        if customer_profile.get("debt_to_income_ratio", 0) < 30:
            strengths.append("Ratio de endeudamiento saludable")
        
        if customer_profile.get("income_variability", 100) < 20:
            strengths.append("Ingresos estables")
        
        return strengths
    
    def _identify_improvement_areas(
        self, 
        eligibility_results: List[Tuple[str, EligibilityResult]]
    ) -> List[str]:
        """Identify areas where customer could improve for better eligibility."""
        
        improvement_areas = set()
        
        for _, result in eligibility_results:
            if not result.is_eligible:
                # Extract common improvement themes from reasons
                for reason in result.reasons_not_eligible:
                    if "score" in reason.lower():
                        improvement_areas.add("Mejorar score crediticio")
                    elif "mora" in reason.lower():
                        improvement_areas.add("Regularizar situación de mora")
                    elif "ingreso" in reason.lower():
                        improvement_areas.add("Incrementar ingresos o estabilidad")
        
        return list(improvement_areas)
