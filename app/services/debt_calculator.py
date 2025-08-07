"""Financial calculation engine for debt optimization."""

from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models import Customer, Loan, Card, BankOffer, CustomerCashflow, CreditScore


@dataclass
class DebtItem:
    """Unified debt item for calculations."""
    id: str
    debt_type: str  # 'loan' or 'card'
    balance: float
    annual_rate_pct: float
    minimum_payment: float
    days_past_due: int
    priority_score: float
    customer_id: str


@dataclass
class PaymentPlan:
    """Payment plan for a specific debt."""
    debt_id: str
    monthly_payment: float
    payoff_months: int
    total_interest: float
    total_payments: float


@dataclass
class ScenarioResult:
    """Complete scenario calculation result."""
    scenario_name: str
    total_monthly_payment: float
    total_payoff_months: int
    total_interest: float
    total_payments: float
    savings_vs_minimum: float
    payment_plans: List[PaymentPlan]
    description: str


class DebtCalculator:
    """Financial calculation engine for debt scenarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_debts(self, customer_id: str) -> List[DebtItem]:
        """Get all debts for a customer as unified debt items."""
        debts = []
        
        # Get loans
        loans = self.db.query(Loan).filter(Loan.customer_id == customer_id).all()
        for loan in loans:
            debt = DebtItem(
                id=loan.id,
                debt_type='loan',
                balance=loan.principal,
                annual_rate_pct=loan.annual_rate_pct,
                minimum_payment=loan.minimum_payment,
                days_past_due=loan.days_past_due,
                priority_score=loan.priority_score,
                customer_id=customer_id
            )
            debts.append(debt)
        
        # Get cards
        cards = self.db.query(Card).filter(Card.customer_id == customer_id).all()
        for card in cards:
            debt = DebtItem(
                id=card.id,
                debt_type='card',
                balance=card.balance,
                annual_rate_pct=card.annual_rate_pct,
                minimum_payment=card.minimum_payment,
                days_past_due=card.days_past_due,
                priority_score=card.priority_score,
                customer_id=customer_id
            )
            debts.append(debt)
        
        return debts
    
    def calculate_minimum_payment_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate scenario where customer only pays minimums."""
        debts = self.get_customer_debts(customer_id)
        payment_plans = []
        total_monthly = 0
        total_interest = 0
        total_payments = 0
        max_months = 0
        
        for debt in debts:
            plan = self._calculate_debt_payoff(debt, debt.minimum_payment)
            payment_plans.append(plan)
            total_monthly += plan.monthly_payment
            total_interest += plan.total_interest
            total_payments += plan.total_payments
            max_months = max(max_months, plan.payoff_months)
        
        return ScenarioResult(
            scenario_name="Pago Mínimo",
            total_monthly_payment=total_monthly,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=0,  # This is the baseline
            payment_plans=payment_plans,
            description="Escenario donde solo se pagan los montos mínimos requeridos."
        )
    
    def calculate_optimized_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate optimized payment scenario using avalanche method."""
        debts = self.get_customer_debts(customer_id)
        cashflow = self.db.query(CustomerCashflow).filter(
            CustomerCashflow.customer_id == customer_id
        ).first()
        
        if not cashflow:
            # Fallback to minimum payment if no cashflow data
            return self.calculate_minimum_payment_scenario(customer_id)
        
        # Calculate available payment budget
        available_budget = cashflow.conservative_cashflow
        minimum_total = sum(debt.minimum_payment for debt in debts)
        extra_payment = max(0, available_budget - minimum_total)
        
        # Sort debts by priority (avalanche method - highest rate first)
        sorted_debts = sorted(debts, key=lambda x: x.priority_score, reverse=True)
        
        # Allocate extra payment to highest priority debts
        payment_plans = []
        remaining_extra = extra_payment
        total_monthly = 0
        total_interest = 0
        total_payments = 0
        max_months = 0
        
        for debt in sorted_debts:
            # Allocate extra payment to this debt
            extra_for_debt = min(remaining_extra, debt.balance)
            monthly_payment = debt.minimum_payment + extra_for_debt
            remaining_extra -= extra_for_debt
            
            plan = self._calculate_debt_payoff(debt, monthly_payment)
            payment_plans.append(plan)
            total_monthly += plan.monthly_payment
            total_interest += plan.total_interest
            total_payments += plan.total_payments
            max_months = max(max_months, plan.payoff_months)
        
        # Calculate savings vs minimum
        minimum_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = minimum_scenario.total_interest - total_interest
        
        return ScenarioResult(
            scenario_name="Plan Optimizado",
            total_monthly_payment=total_monthly,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description="Plan optimizado priorizando deudas con mayor tasa de interés."
        )
    
    def calculate_consolidation_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate debt consolidation scenario."""
        debts = self.get_customer_debts(customer_id)
        
        # Get customer data for eligibility
        customer_data = self._get_customer_eligibility_data(customer_id)
        
        # Find eligible consolidation offers
        offers = self.db.query(BankOffer).all()
        eligible_offers = []
        
        for offer in offers:
            if offer.is_eligible_for_customer(customer_data):
                eligible_offers.append(offer)
        
        if not eligible_offers:
            # No consolidation available, return optimized scenario
            result = self.calculate_optimized_scenario(customer_id)
            result.scenario_name = "Consolidación"
            result.description = "No hay ofertas de consolidación disponibles. Se muestra plan optimizado."
            return result
        
        # Find best consolidation offer
        best_offer = min(eligible_offers, key=lambda x: x.new_rate_pct)
        
        # Calculate consolidatable balance
        consolidatable_debts = [
            debt for debt in debts 
            if debt.debt_type in best_offer.product_types_eligible
        ]
        total_consolidatable = sum(debt.balance for debt in consolidatable_debts)
        
        if total_consolidatable > best_offer.max_consolidated_balance:
            # Partial consolidation - consolidate highest rate debts first
            consolidatable_debts.sort(key=lambda x: x.annual_rate_pct, reverse=True)
            remaining_balance = best_offer.max_consolidated_balance
            consolidated_debts = []
            unconsolidated_debts = []
            
            for debt in consolidatable_debts:
                if debt.balance <= remaining_balance:
                    consolidated_debts.append(debt)
                    remaining_balance -= debt.balance
                else:
                    unconsolidated_debts.append(debt)
            
            # Add non-eligible debts to unconsolidated
            for debt in debts:
                if debt.debt_type not in best_offer.product_types_eligible:
                    unconsolidated_debts.append(debt)
        else:
            # Full consolidation
            consolidated_debts = consolidatable_debts
            unconsolidated_debts = [
                debt for debt in debts 
                if debt.debt_type not in best_offer.product_types_eligible
            ]
        
        # Calculate new consolidated payment
        consolidated_balance = sum(debt.balance for debt in consolidated_debts)
        consolidated_payment = best_offer.calculate_new_payment(consolidated_balance)
        
        # Create payment plans
        payment_plans = []
        total_monthly = consolidated_payment
        total_interest = 0
        total_payments = 0
        max_months = best_offer.max_term_months
        
        # Consolidated debt plan
        if consolidated_balance > 0:
            consolidated_interest = (consolidated_payment * best_offer.max_term_months) - consolidated_balance
            plan = PaymentPlan(
                debt_id="CONSOLIDATED",
                monthly_payment=consolidated_payment,
                payoff_months=best_offer.max_term_months,
                total_interest=consolidated_interest,
                total_payments=consolidated_payment * best_offer.max_term_months
            )
            payment_plans.append(plan)
            total_interest += consolidated_interest
            total_payments += plan.total_payments
        
        # Unconsolidated debts
        for debt in unconsolidated_debts:
            plan = self._calculate_debt_payoff(debt, debt.minimum_payment)
            payment_plans.append(plan)
            total_monthly += plan.monthly_payment
            total_interest += plan.total_interest
            total_payments += plan.total_payments
            max_months = max(max_months, plan.payoff_months)
        
        # Calculate savings vs minimum
        minimum_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = minimum_scenario.total_interest - total_interest
        
        return ScenarioResult(
            scenario_name="Consolidación",
            total_monthly_payment=total_monthly,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description=f"Consolidación con oferta {best_offer.id} al {best_offer.new_rate_pct}% anual."
        )
    
    def _calculate_debt_payoff(self, debt: DebtItem, monthly_payment: float) -> PaymentPlan:
        """Calculate payoff plan for a single debt."""
        if monthly_payment <= 0 or debt.balance <= 0:
            return PaymentPlan(
                debt_id=debt.id,
                monthly_payment=0,
                payoff_months=0,
                total_interest=0,
                total_payments=0
            )
        
        monthly_rate = debt.annual_rate_pct / 100 / 12
        balance = debt.balance
        total_interest = 0
        months = 0
        
        # Simulate month by month payment
        while balance > 0.01 and months < 600:  # Max 50 years
            months += 1
            interest_payment = balance * monthly_rate
            principal_payment = min(monthly_payment - interest_payment, balance)
            
            if principal_payment <= 0:
                # Payment doesn't cover interest - debt grows
                months = 999
                total_interest = debt.balance * 10  # Penalty
                break
            
            total_interest += interest_payment
            balance -= principal_payment
        
        total_payments = monthly_payment * months
        
        return PaymentPlan(
            debt_id=debt.id,
            monthly_payment=monthly_payment,
            payoff_months=months,
            total_interest=total_interest,
            total_payments=total_payments
        )
    
    def _get_customer_eligibility_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer data for consolidation eligibility."""
        debts = self.get_customer_debts(customer_id)
        
        # Get latest credit score
        latest_score = self.db.query(CreditScore).filter(
            CreditScore.customer_id == customer_id
        ).order_by(CreditScore.date.desc()).first()
        
        return {
            "credit_score": latest_score.credit_score if latest_score else 0,
            "has_past_due": any(debt.days_past_due > 0 for debt in debts),
            "max_days_past_due": max((debt.days_past_due for debt in debts), default=0)
        }
