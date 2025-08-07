"""FastAPI endpoints for financial debt analysis."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.database import get_supabase
from app.services.analysis_service import FinancialAnalysisService
from app.services.data_loader import DataLoader
from app.models import Customer, Loan, Card, BankOffer
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "financial-restructuring-assistant"}


@router.post("/load-data")
async def load_sample_data(background_tasks: BackgroundTasks):
    """Load sample data from CSV and JSON files."""
    try:
        loader = DataLoader()
        results = loader.load_all_data()

        return {"message": "Data loaded successfully", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@router.get("/customers")
async def get_customers():
    """Get list of all customers."""
    try:
        supabase = get_supabase()
        response = supabase.table('customers').select('*').execute()
        customers = response.data if response.data else []
        
        customer_list = [
            {
                "customer_id": customer['id'],
                "created_at": customer.get('created_at')
            }
            for customer in customers
        ]
        
        return {
            "customers": customer_list,
            "total": len(customer_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str):
    """Get detailed customer profile including debts and financial info."""
    try:
        supabase = get_supabase()
        service = FinancialAnalysisService()
        
        # Get customer
        customer_response = supabase.table('customers').select('*').eq('id', customer_id).single().execute()
        if not customer_response.data:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        customer_data = customer_response.data
        
        # Get customer info with all relations
        customer_info = service._get_customer_info(customer_id)
        debt_details = service._get_debt_details(customer_id)
        
        return {
            "customer_id": customer_id,
            "profile": customer_info,
            "debts": debt_details,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching customer profile: {str(e)}")


@router.post("/customers/{customer_id}/analyze")
async def analyze_customer_debt(customer_id: str):
    """Perform comprehensive debt analysis for a customer."""
    try:
        service = FinancialAnalysisService()
        analysis = await service.analyze_customer_debt(customer_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing analysis: {str(e)}")


@router.post("/customers/{customer_id}/report")
async def generate_client_report(customer_id: str):
    """Generate a formatted report for client presentation."""
    try:
        service = FinancialAnalysisService()
        report = await service.generate_report(customer_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/customers/{customer_id}/scenarios/{scenario_type}")
async def get_scenario_analysis(customer_id: str, scenario_type: str):
    """Get analysis for a specific scenario type."""
    
    if scenario_type not in ["minimum", "optimized", "consolidation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario type. Must be one of: minimum, optimized, consolidation"
        )
    
    try:
        service = FinancialAnalysisService()
        scenario = service.get_scenario_analysis(customer_id, scenario_type)
        
        if not scenario:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate {scenario_type} scenario for customer {customer_id}"
            )
        
        return {
            "customer_id": customer_id,
            "scenario_type": scenario_type,
            "scenario": scenario,
            "generated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating scenario: {str(e)}"
        )


@router.get("/offers")
async def get_consolidation_offers():
    """Get available consolidation offers."""
    try:
        supabase = get_supabase()
        response = supabase.table('bank_offers').select('*').execute()
        offers = response.data if response.data else []
        
        return {
            "offers": offers,
            "total": len(offers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching offers: {str(e)}")


@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary of all customers and scenarios."""
    try:
        supabase = get_supabase()
        
        # Get all customers
        customers_response = supabase.table('customers').select('*').execute()
        customers = customers_response.data if customers_response.data else []
        
        # Get all loans
        loans_response = supabase.table('loans').select('*').execute()
        loans = loans_response.data if loans_response.data else []
        
        # Get all cards
        cards_response = supabase.table('cards').select('*').execute()
        cards = cards_response.data if cards_response.data else []
        
        # Calculate summary statistics
        total_debt_balance = sum(loan['principal'] for loan in loans) + sum(card['balance'] for card in cards)
        
        past_due_loans = [l for l in loans if l['days_past_due'] > 0]
        past_due_cards = [c for c in cards if c['days_past_due'] > 0]
        
        avg_loan_rate = sum(l['annual_rate_pct'] for l in loans) / len(loans) if loans else 0
        avg_card_rate = sum(c['annual_rate_pct'] for c in cards) / len(cards) if cards else 0
        
        return {
            "summary": {
                "total_customers": len(customers),
                "total_loans": len(loans),
                "total_cards": len(cards),
                "total_debt_balance": total_debt_balance,
                "loans_past_due": len(past_due_loans),
                "cards_past_due": len(past_due_cards),
                "average_loan_rate": avg_loan_rate,
                "average_card_rate": avg_card_rate,
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")


@router.post("/customers/{customer_id}/consolidation-eligibility")
async def check_consolidation_eligibility(customer_id: str):
    """Check customer eligibility for consolidation offers."""
    try:
        from app.agents.eligibility_agent import EligibilityAgent
        
        supabase = get_supabase()
        service = FinancialAnalysisService()
        
        # Get customer info
        customer_info = service._get_customer_info(customer_id)
        if not customer_info:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        # Get all offers
        offers_response = supabase.table('bank_offers').select('*').execute()
        offers = offers_response.data if offers_response.data else []
        
        # Evaluate eligibility
        agent = EligibilityAgent()
        eligible_offers = await agent.evaluate_eligibility(customer_info, offers)
        
        return {
            "customer_id": customer_id,
            "total_offers": len(offers),
            "eligible_offers": eligible_offers,
            "eligibility_summary": {
                "is_eligible": len(eligible_offers) > 0,
                "best_offer": eligible_offers[0] if eligible_offers else None,
                "evaluation_criteria": {
                    "credit_score": customer_info.get("credit_score"),
                    "has_past_due": customer_info.get("has_past_due"),
                    "debt_to_income_ratio": customer_info.get("debt_to_income_ratio")
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking eligibility: {str(e)}")


@router.post("/customers/{customer_id}/intelligent-consolidation-analysis")
async def intelligent_consolidation_analysis(customer_id: str):
    """Perform intelligent consolidation analysis using LLM-powered eligibility assessment."""
    try:
        from app.services.enhanced_consolidation_service import EnhancedConsolidationService
        
        service = EnhancedConsolidationService()
        
        # Perform comprehensive analysis
        analysis_result = await service.analyze_consolidation_with_llm(customer_id)
        
        if analysis_result["status"] == "error":
            raise HTTPException(status_code=404, detail=analysis_result["message"])
        
        return analysis_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in intelligent consolidation analysis: {str(e)}"
        )


@router.get("/customers/{customer_id}/offers/{offer_id}/detailed-analysis")
async def get_detailed_offer_analysis(customer_id: str, offer_id: str):
    """Get detailed LLM-powered analysis for a specific offer and customer."""
    try:
        from app.agents.eligibility_agent import EligibilityAgent
        
        supabase = get_supabase()
        service = FinancialAnalysisService()
        
        # Get customer info
        customer_info = service._get_customer_info(customer_id)
        if not customer_info:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        # Get specific offer
        offer_response = supabase.table('bank_offers').select('*').eq('id', offer_id).single().execute()
        if not offer_response.data:
            raise HTTPException(status_code=404, detail=f"Offer {offer_id} not found")
        
        offer = offer_response.data
        
        # Get detailed analysis from LLM
        agent = EligibilityAgent()
        analysis = await agent.analyze_specific_offer(customer_info, offer)
        
        return {
            "customer_id": customer_id,
            "offer_id": offer_id,
            "analysis": analysis,
            "generated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing offer: {str(e)}"
        )