"""FastAPI endpoints for financial debt analysis."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analysis_service import (
    FinancialAnalysisService,
    ReportGenerationService,
)
from app.services.data_loader import DataLoader
from app.schemas.debt import CustomerAnalysis
from app.models import Customer
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "financial-restructuring-assistant"}


@router.post("/load-data")
async def load_sample_data(
    background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """Load sample data from CSV and JSON files."""
    try:
        loader = DataLoader()
        results = loader.load_all_data(db)

        return {"message": "Data loaded successfully", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@router.get("/customers")
async def get_customers(db: Session = Depends(get_db)):
    """Get list of all customers."""
    try:
        customers = db.query(Customer).all()
        customer_list = [
            {
                "customer_id": customer.id,
                "created_at": customer.created_at.isoformat()
                if customer.created_at
                else None,
            }
            for customer in customers
        ]

        return {"customers": customer_list, "total_count": len(customer_list)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching customers: {str(e)}"
        )


@router.get("/customers/{customer_id}/profile")
async def get_customer_profile(customer_id: str, db: Session = Depends(get_db)):
    """Get detailed customer profile including debts and financial info."""
    try:
        analysis_service = FinancialAnalysisService(db)
        customer_info = analysis_service._get_customer_info(customer_id)

        if not customer_info:
            raise HTTPException(
                status_code=404, detail=f"Customer {customer_id} not found"
            )

        # Get debt details
        debts = analysis_service.debt_calculator.get_customer_debts(customer_id)
        debt_details = [
            {
                "debt_id": debt.id,
                "debt_type": debt.debt_type,
                "balance": debt.balance,
                "annual_rate_pct": debt.annual_rate_pct,
                "minimum_payment": debt.minimum_payment,
                "days_past_due": debt.days_past_due,
                "priority_score": debt.priority_score,
            }
            for debt in debts
        ]

        return {"customer_profile": customer_info, "debts": debt_details}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching customer profile: {str(e)}"
        )


@router.post("/customers/{customer_id}/analyze")
async def analyze_customer_debt(customer_id: str, db: Session = Depends(get_db)):
    """Perform comprehensive debt analysis for a customer."""
    try:
        analysis_service = FinancialAnalysisService(db)
        analysis_result = await analysis_service.analyze_customer_debt(customer_id)

        if "error" in analysis_result:
            raise HTTPException(status_code=404, detail=analysis_result["error"])

        return analysis_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing customer debt: {str(e)}"
        )


@router.post("/customers/{customer_id}/report")
async def generate_client_report(customer_id: str, db: Session = Depends(get_db)):
    """Generate a formatted report for client presentation."""
    try:
        analysis_service = FinancialAnalysisService(db)
        report_service = ReportGenerationService()

        # Perform analysis
        analysis_result = await analysis_service.analyze_customer_debt(customer_id)

        if "error" in analysis_result:
            raise HTTPException(status_code=404, detail=analysis_result["error"])

        # Format for client
        client_report = report_service.format_analysis_for_client(analysis_result)

        return client_report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating report: {str(e)}"
        )


@router.get("/customers/{customer_id}/scenarios/{scenario_type}")
async def get_scenario_analysis(
    customer_id: str, scenario_type: str, db: Session = Depends(get_db)
):
    """Get analysis for a specific scenario type."""
    try:
        if scenario_type not in ["minimum", "optimized", "consolidation"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid scenario type. Must be: minimum, optimized, or consolidation",
            )

        analysis_service = FinancialAnalysisService(db)
        customer_info = analysis_service._get_customer_info(customer_id)

        if not customer_info:
            raise HTTPException(
                status_code=404, detail=f"Customer {customer_id} not found"
            )

        # Calculate specific scenario
        if scenario_type == "minimum":
            scenario = (
                analysis_service.debt_calculator.calculate_minimum_payment_scenario(
                    customer_id
                )
            )
        elif scenario_type == "optimized":
            scenario = analysis_service.debt_calculator.calculate_optimized_scenario(
                customer_id
            )
        elif scenario_type == "consolidation":
            scenario = (
                analysis_service.debt_calculator.calculate_consolidation_scenario(
                    customer_id
                )
            )

        scenario_dict = analysis_service._scenario_to_dict(scenario)

        # Get individual agent analysis
        from app.agents.parallel_executor import ParallelAgentExecutor

        executor = ParallelAgentExecutor()

        agent_analysis = await executor.execute_individual_analysis(
            scenario_type, scenario_dict, customer_info
        )

        return {
            "customer_id": customer_id,
            "scenario_type": scenario_type,
            "scenario_data": scenario_dict,
            "agent_analysis": agent_analysis,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing scenario: {str(e)}"
        )


@router.get("/offers")
async def get_consolidation_offers(db: Session = Depends(get_db)):
    """Get available consolidation offers."""
    try:
        from app.models import BankOffer

        offers = db.query(BankOffer).all()
        offer_list = [
            {
                "offer_id": offer.id,
                "product_types_eligible": offer.product_types_eligible,
                "max_consolidated_balance": offer.max_consolidated_balance,
                "new_rate_pct": offer.new_rate_pct,
                "max_term_months": offer.max_term_months,
                "conditions": offer.conditions,
            }
            for offer in offers
        ]

        return {"offers": offer_list, "total_count": len(offer_list)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching offers: {str(e)}")


@router.get("/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get analytics summary of all customers and scenarios."""
    try:
        from app.models import Customer, Loan, Card

        # Basic counts
        total_customers = db.query(Customer).count()
        total_loans = db.query(Loan).count()
        total_cards = db.query(Card).count()

        # Calculate some basic metrics
        loans = db.query(Loan).all()
        cards = db.query(Card).all()

        total_loan_balance = sum(loan.principal for loan in loans)
        total_card_balance = sum(card.balance for card in cards)

        avg_loan_rate = (
            sum(loan.annual_rate_pct for loan in loans) / len(loans) if loans else 0
        )
        avg_card_rate = (
            sum(card.annual_rate_pct for card in cards) / len(cards) if cards else 0
        )

        customers_with_past_due = len(
            set(
                [loan.customer_id for loan in loans if loan.days_past_due > 0]
                + [card.customer_id for card in cards if card.days_past_due > 0]
            )
        )

        return {
            "total_customers": total_customers,
            "total_loans": total_loans,
            "total_cards": total_cards,
            "total_debt_balance": total_loan_balance + total_card_balance,
            "average_loan_rate": round(avg_loan_rate, 2),
            "average_card_rate": round(avg_card_rate, 2),
            "customers_with_past_due": customers_with_past_due,
            "past_due_rate": round(customers_with_past_due / total_customers * 100, 2)
            if total_customers > 0
            else 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating analytics: {str(e)}"
        )


@router.post("/customers/{customer_id}/intelligent-consolidation-analysis")
async def intelligent_consolidation_analysis(
    customer_id: str, db: Session = Depends(get_db)
):
    """Perform intelligent consolidation analysis using LLM-powered eligibility assessment."""
    try:
        from app.services.enhanced_consolidation_service import (
            EnhancedConsolidationService,
        )

        enhanced_service = EnhancedConsolidationService(db)
        (
            scenario,
            eligibility_details,
        ) = await enhanced_service.calculate_intelligent_consolidation_scenario(
            customer_id
        )

        return {
            "customer_id": customer_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "consolidation_scenario": {
                "scenario_name": scenario.scenario_name,
                "total_monthly_payment": scenario.total_monthly_payment,
                "total_payoff_months": scenario.total_payoff_months,
                "total_interest": scenario.total_interest,
                "total_payments": scenario.total_payments,
                "savings_vs_minimum": scenario.savings_vs_minimum,
                "description": scenario.description,
            },
            "intelligent_eligibility_analysis": eligibility_details,
            "analysis_type": "LLM-powered intelligent analysis",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in intelligent analysis: {str(e)}"
        )


@router.get("/customers/{customer_id}/offers/{offer_id}/detailed-analysis")
async def get_detailed_offer_analysis(
    customer_id: str, offer_id: str, db: Session = Depends(get_db)
):
    """Get detailed LLM-powered analysis for a specific offer and customer."""
    try:
        from app.services.enhanced_consolidation_service import (
            EnhancedConsolidationService,
        )

        enhanced_service = EnhancedConsolidationService(db)
        analysis = await enhanced_service.get_detailed_offer_analysis(
            customer_id, offer_id
        )

        return {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "detailed_analysis": analysis,
            "analysis_type": "LLM-powered detailed offer analysis",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in detailed analysis: {str(e)}"
        )
