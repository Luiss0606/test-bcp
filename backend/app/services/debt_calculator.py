"""Financial calculation engine for debt optimization."""

from typing import List, Dict, Any
from dataclasses import dataclass
from app.core.database import get_supabase
from app.models import Loan, Card, BankOffer, CustomerCashflow


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
    monthly_breakdown: List['MonthlyPaymentDetail'] = None  # Optional detailed breakdown
    
    def get_payment_schedule_summary(self) -> Dict[str, Any]:
        """Get a summary of the payment schedule for this debt."""
        if not self.monthly_breakdown:
            return {
                "debt_id": self.debt_id,
                "initial_payment": self.monthly_payment,
                "total_months": self.payoff_months,
                "total_interest": self.total_interest,
                "total_payments": self.total_payments,
                "schedule_type": "fixed"
            }
        
        # Calculate variable payment details
        payments = [detail.payment_amount for detail in self.monthly_breakdown]
        return {
            "debt_id": self.debt_id,
            "initial_payment": payments[0] if payments else self.monthly_payment,
            "final_payment": payments[-1] if payments else self.monthly_payment,
            "average_payment": sum(payments) / len(payments) if payments else self.monthly_payment,
            "total_months": self.payoff_months,
            "total_interest": self.total_interest,
            "total_payments": self.total_payments,
            "schedule_type": "variable",
            "min_payment": min(payments) if payments else self.monthly_payment,
            "max_payment": max(payments) if payments else self.monthly_payment
        }


@dataclass
class MonthlyPaymentDetail:
    """Detailed monthly payment breakdown."""
    month: int
    debt_id: str
    payment_amount: float
    principal_payment: float
    interest_payment: float
    remaining_balance: float


@dataclass
class ScenarioResult:
    """Result of a debt repayment scenario."""
    scenario_name: str
    total_monthly_payment: float
    total_payoff_months: int
    total_interest: float
    total_payments: float
    savings_vs_minimum: float
    payment_plans: List[PaymentPlan]
    description: str
    consolidation_details: Dict[str, Any] = None
    cashflow_usage_pct: float = 0
    
    def get_monthly_payment_distribution(self) -> Dict[str, float]:
        """Get distribution of monthly payments by debt type."""
        distribution = {"loans": 0, "cards": 0}
        for plan in self.payment_plans:
            debt_type = "loans" if "LN" in plan.debt_id else "cards"
            distribution[debt_type] += plan.monthly_payment
        return distribution
    
    def get_completion_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of when each debt will be paid off."""
        timeline = []
        for plan in self.payment_plans:
            timeline.append({
                "debt_id": plan.debt_id,
                "months_to_payoff": plan.payoff_months,
                "completion_year": plan.payoff_months // 12,
                "completion_month": plan.payoff_months % 12
            })
        # Sort by payoff time
        timeline.sort(key=lambda x: x["months_to_payoff"])
        return timeline
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario result to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "total_monthly_payment": self.total_monthly_payment,
            "total_payoff_months": self.total_payoff_months,
            "total_interest": self.total_interest,
            "total_payments": self.total_payments,
            "savings_vs_minimum": self.savings_vs_minimum,
            "payment_plans": [
                {
                    "debt_id": plan.debt_id,
                    "monthly_payment": plan.monthly_payment,
                    "payoff_months": plan.payoff_months,
                    "total_interest": plan.total_interest,
                    "total_payments": plan.total_payments
                } for plan in self.payment_plans
            ],
            "description": self.description,
            "consolidation_details": self.consolidation_details,
            "cashflow_usage_pct": self.cashflow_usage_pct,
            "payment_distribution": self.get_monthly_payment_distribution(),
            "completion_timeline": self.get_completion_timeline()
        }


@dataclass
class ConsolidationOffer:
    """Consolidation offer details."""
    offer_id: str
    eligible_balance: float
    new_monthly_payment: float
    new_rate: float
    term_months: int
    total_interest: float
    total_payments: float
    savings_vs_current: float


class DebtCalculator:
    """Main debt calculation service."""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    def get_customer_debts(self, customer_id: str) -> List[DebtItem]:
        """Get all debts for a customer as unified DebtItems."""
        debts = []
        
        # Get loans from Supabase
        loans_response = self.supabase.table('loans').select('*').eq('customer_id', customer_id).execute()
        loans = [Loan.from_dict(loan) for loan in loans_response.data] if loans_response.data else []
        
        for loan in loans:
            debts.append(DebtItem(
                id=loan.id,
                debt_type='loan',
                balance=loan.principal,
                annual_rate_pct=loan.annual_rate_pct,
                minimum_payment=loan.minimum_payment,
                days_past_due=loan.days_past_due,
                priority_score=loan.priority_score,
                customer_id=customer_id
            ))
        
        # Get cards from Supabase
        cards_response = self.supabase.table('cards').select('*').eq('customer_id', customer_id).execute()
        cards = [Card.from_dict(card) for card in cards_response.data] if cards_response.data else []
        
        for card in cards:
            debts.append(DebtItem(
                id=card.id,
                debt_type='card',
                balance=card.balance,
                annual_rate_pct=card.annual_rate_pct,
                minimum_payment=card.minimum_payment,
                days_past_due=card.days_past_due,
                priority_score=card.priority_score,
                customer_id=customer_id
            ))
        
        return debts
    
    def calculate_minimum_payment_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate scenario paying only minimum payments."""
        debts = self.get_customer_debts(customer_id)
        
        if not debts:
            return ScenarioResult(
                scenario_name="Pago Mínimo",
                total_monthly_payment=0,
                total_payoff_months=0,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas activas"
            )
        
        payment_plans = []
        total_monthly_payment = 0
        total_interest = 0
        total_payments = 0
        max_months = 0
        
        for debt in debts:
            # Calculate payoff for each debt with minimum payment
            payoff_result = self._calculate_debt_payoff(debt, debt.minimum_payment)
            
            payment_plans.append(PaymentPlan(
                debt_id=debt.id,
                monthly_payment=debt.minimum_payment,
                payoff_months=payoff_result['months'],
                total_interest=payoff_result['total_interest'],
                total_payments=payoff_result['total_payments']
            ))
            
            total_monthly_payment += debt.minimum_payment
            total_interest += payoff_result['total_interest']
            total_payments += payoff_result['total_payments']
            max_months = max(max_months, payoff_result['months'])
        
        # Get cashflow info from Supabase
        cashflow_response = self.supabase.table('customer_cashflow').select('*').eq(
            'customer_id', customer_id
        ).single().execute()
        cashflow = CustomerCashflow.from_dict(cashflow_response.data) if cashflow_response.data else None
        
        cashflow_usage = 0
        if cashflow and cashflow.available_cashflow > 0:
            cashflow_usage = (total_monthly_payment / cashflow.available_cashflow) * 100
        
        return ScenarioResult(
            scenario_name="Pago Mínimo",
            total_monthly_payment=total_monthly_payment,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=0,
            payment_plans=payment_plans,
            description="Pagando solo el mínimo requerido en cada deuda",
            cashflow_usage_pct=cashflow_usage
        )
    
    def calculate_optimized_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate optimized payment scenario using debt avalanche method."""
        debts = self.get_customer_debts(customer_id)
        
        if not debts:
            return ScenarioResult(
                scenario_name="Plan Optimizado",
                total_monthly_payment=0,
                total_payoff_months=0,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas activas"
            )
        
        # Sort debts by priority score (highest first - debt avalanche)
        sorted_debts = sorted(debts, key=lambda x: x.priority_score, reverse=True)
        
        # Calculate extra payment available
        total_minimum = sum(d.minimum_payment for d in debts)
        
        # Get available cashflow from Supabase
        cashflow_response = self.supabase.table('customer_cashflow').select('*').eq(
            'customer_id', customer_id
        ).single().execute()
        cashflow = CustomerCashflow.from_dict(cashflow_response.data) if cashflow_response.data else None
        
        if cashflow and cashflow.conservative_cashflow > total_minimum:
            extra_payment = cashflow.conservative_cashflow - total_minimum
        else:
            # If no extra cashflow, add 20% to minimum as optimization
            extra_payment = total_minimum * 0.2
        
        # Simulate month-by-month payment with debt avalanche
        remaining_debts = [
            {
                'debt': debt,
                'balance': debt.balance,
                'paid_off': False,
                'months_to_payoff': 0,
                'total_interest': 0,
                'total_payments': 0
            }
            for debt in sorted_debts
        ]
        
        month = 0
        max_months = 600  # Safety limit
        
        while any(not d['paid_off'] for d in remaining_debts) and month < max_months:
            month += 1
            remaining_extra = extra_payment
            
            # Pay minimums first
            for debt_info in remaining_debts:
                if not debt_info['paid_off']:
                    debt = debt_info['debt']
                    balance = debt_info['balance']
                    
                    # Calculate interest for this month
                    monthly_rate = debt.annual_rate_pct / 100 / 12
                    interest_payment = balance * monthly_rate
                    
                    # Minimum payment allocation
                    payment = min(debt.minimum_payment, balance + interest_payment)
                    principal_payment = payment - interest_payment
                    
                    # Special handling for credit cards with percentage-based minimum
                    if debt.debt_type == 'card' and payment < interest_payment:
                        # For cards, if minimum payment doesn't cover interest, adjust
                        payment = interest_payment * 1.1  # Pay at least 110% of interest
                        principal_payment = payment - interest_payment
                        # Also try to get this from the actual card data
                        card_response = self.supabase.table('cards').select('*').eq('id', debt.id).single().execute()
                        if card_response.data:
                            card = Card.from_dict(card_response.data)
                            if card and card.min_payment_pct:
                                # Recalculate based on actual percentage
                                min_payment = balance * (card.min_payment_pct / 100)
                                payment = max(min_payment, interest_payment * 1.1)
                                principal_payment = payment - interest_payment
                    
                    # Update balance
                    debt_info['balance'] = max(0, balance - principal_payment)
                    debt_info['total_interest'] += interest_payment
                    debt_info['total_payments'] += payment
                    
                    if debt_info['balance'] <= 0.01:
                        debt_info['paid_off'] = True
                        debt_info['months_to_payoff'] = month
            
            # Apply extra payment to highest priority debt
            for debt_info in remaining_debts:
                if not debt_info['paid_off'] and remaining_extra > 0:
                    debt = debt_info['debt']
                    balance = debt_info['balance']
                    
                    # Apply extra payment
                    extra_for_debt = min(remaining_extra, balance)
                    debt_info['balance'] -= extra_for_debt
                    debt_info['total_payments'] += extra_for_debt
                    remaining_extra -= extra_for_debt
                    
                    if debt_info['balance'] <= 0.01:
                        debt_info['paid_off'] = True
                        debt_info['months_to_payoff'] = month
                    
                    # Only apply to one debt at a time (avalanche method)
                    if remaining_extra <= 0:
                        break
        
        # Build payment plans from simulation results
        payment_plans = []
        total_interest = 0
        total_payments = 0
        
        for debt_info in remaining_debts:
            debt = debt_info['debt']
            monthly_payment = debt_info['total_payments'] / debt_info['months_to_payoff'] if debt_info['months_to_payoff'] > 0 else debt.minimum_payment
            
            payment_plans.append(PaymentPlan(
                debt_id=debt.id,
                monthly_payment=monthly_payment,
                payoff_months=debt_info['months_to_payoff'],
                total_interest=debt_info['total_interest'],
                total_payments=debt_info['total_payments']
            ))
            
            total_interest += debt_info['total_interest']
            total_payments += debt_info['total_payments']
        
        # Calculate savings vs minimum
        min_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = min_scenario.total_interest - total_interest
        
        cashflow_usage = 0
        if cashflow and cashflow.conservative_cashflow > 0:
            cashflow_usage = ((total_minimum + extra_payment) / cashflow.conservative_cashflow) * 100
        
        return ScenarioResult(
            scenario_name="Plan Optimizado",
            total_monthly_payment=total_minimum + extra_payment,
            total_payoff_months=month,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description=f"Estrategia de avalancha de deudas con ${extra_payment:.2f} extra mensual",
            cashflow_usage_pct=cashflow_usage
        )
    
    def calculate_consolidation_scenario(self, customer_id: str, offer_id: str = None, 
                                        eligible_offers_data: List[Dict[str, Any]] = None) -> ScenarioResult:
        """Calculate consolidation scenario with a specific offer or find best offer."""
        debts = self.get_customer_debts(customer_id)
        
        if not debts:
            return ScenarioResult(
                scenario_name="Consolidación",
                total_monthly_payment=0,
                total_payoff_months=0,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas para consolidar"
            )
        
        # Determine best offer to use
        best_offer = None
        
        if offer_id:
            # Use specific offer
            offer_response = self.supabase.table('bank_offers').select('*').eq('id', offer_id).single().execute()
            best_offer = BankOffer.from_dict(offer_response.data) if offer_response.data else None
        elif eligible_offers_data:
            # Use pre-evaluated eligible offers (from intelligent analysis)
            best_offer_id = eligible_offers_data[0]["offer_id"]
            offer_response = self.supabase.table('bank_offers').select('*').eq('id', best_offer_id).single().execute()
            best_offer = BankOffer.from_dict(offer_response.data) if offer_response.data else None
        else:
            # Fallback to basic method - get all offers from Supabase
            offers_response = self.supabase.table('bank_offers').select('*').execute()
            offers = [BankOffer.from_dict(offer) for offer in offers_response.data] if offers_response.data else []
            
            # Simple eligibility check - find offer with lowest rate
            if offers:
                best_offer = min(offers, key=lambda x: x.new_rate_pct)
        
        if not best_offer:
            # No eligible offers, return minimum scenario
            return self.calculate_minimum_payment_scenario(customer_id)
        
        # Determine which debts can be consolidated
        consolidatable_debts = []
        unconsolidated_debts = []
        total_consolidatable = 0
        
        for debt in debts:
            debt_type = 'personal' if debt.debt_type == 'loan' else 'card'
            # Check if debt type is eligible and within balance limits
            if (debt_type in best_offer.product_types_eligible and 
                debt.days_past_due <= 30 and  # Not severely past due
                total_consolidatable + debt.balance <= best_offer.max_consolidated_balance):
                consolidatable_debts.append(debt)
                total_consolidatable += debt.balance
            else:
                unconsolidated_debts.append(debt)
        
        if not consolidatable_debts:
            return ScenarioResult(
                scenario_name="Consolidación",
                total_monthly_payment=sum(d.minimum_payment for d in debts),
                total_payoff_months=120,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas elegibles para consolidación",
                consolidation_details={
                    "offer_evaluated": best_offer.id,
                    "reason": "Ninguna deuda cumple los criterios"
                }
            )
        
        # Calculate consolidated loan payment
        consolidated_payment = best_offer.calculate_new_payment(total_consolidatable)
        consolidated_interest = (consolidated_payment * best_offer.max_term_months) - total_consolidatable
        
        payment_plans = []
        
        # Add consolidated loan plan
        payment_plans.append(PaymentPlan(
            debt_id=f"CONS-{best_offer.id}",
            monthly_payment=consolidated_payment,
            payoff_months=best_offer.max_term_months,
            total_interest=consolidated_interest,
            total_payments=consolidated_payment * best_offer.max_term_months
        ))
        
        total_monthly_payment = consolidated_payment
        total_interest = consolidated_interest
        total_payments = consolidated_payment * best_offer.max_term_months
        max_months = best_offer.max_term_months
        
        # Calculate payments for unconsolidated debts
        # Use optimized payment strategy for unconsolidated debts if there's cashflow available
        cashflow_response = self.supabase.table('customer_cashflow').select('*').eq(
            'customer_id', customer_id
        ).single().execute()
        cashflow = CustomerCashflow.from_dict(cashflow_response.data) if cashflow_response.data else None
        
        unconsolidated_total_min = sum(d.minimum_payment for d in unconsolidated_debts)
        extra_for_unconsolidated = 0
        
        if cashflow and cashflow.conservative_cashflow > (consolidated_payment + unconsolidated_total_min):
            extra_for_unconsolidated = cashflow.conservative_cashflow - consolidated_payment - unconsolidated_total_min
        
        # Sort unconsolidated by priority for avalanche method
        unconsolidated_debts.sort(key=lambda x: x.priority_score, reverse=True)
        
        for i, debt in enumerate(unconsolidated_debts):
            # Allocate extra payment to highest priority unconsolidated debt
            extra_for_this = extra_for_unconsolidated if i == 0 else 0
            payment_amount = debt.minimum_payment + extra_for_this
            
            payoff_result = self._calculate_debt_payoff(debt, payment_amount)
            
            payment_plans.append(PaymentPlan(
                debt_id=debt.id,
                monthly_payment=payment_amount,
                payoff_months=payoff_result['months'],
                total_interest=payoff_result['total_interest'],
                total_payments=payoff_result['total_payments']
            ))
            
            total_monthly_payment += payment_amount
            total_interest += payoff_result['total_interest']
            total_payments += payoff_result['total_payments']
            max_months = max(max_months, payoff_result['months'])
        
        # Calculate savings
        min_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = min_scenario.total_interest - total_interest
        
        cashflow_usage = 0
        if cashflow and cashflow.conservative_cashflow > 0:
            cashflow_usage = (total_monthly_payment / cashflow.conservative_cashflow) * 100
        
        consolidation_details = {
            "offer_id": best_offer.id,
            "consolidated_balance": total_consolidatable,
            "new_rate": best_offer.new_rate_pct,
            "new_term": best_offer.max_term_months,
            "consolidated_payment": consolidated_payment,
            "consolidated_debts": [d.id for d in consolidatable_debts],
            "unconsolidated_debts": [d.id for d in unconsolidated_debts],
            "total_debts": len(debts),
            "debts_consolidated": len(consolidatable_debts)
        }
        
        return ScenarioResult(
            scenario_name="Consolidación",
            total_monthly_payment=total_monthly_payment,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description=f"Consolidando {len(consolidatable_debts)} deudas al {best_offer.new_rate_pct}% por {best_offer.max_term_months} meses",
            consolidation_details=consolidation_details,
            cashflow_usage_pct=cashflow_usage
        )
    
    def _calculate_debt_payoff(self, debt: DebtItem, monthly_payment: float) -> Dict[str, Any]:
        """Calculate payoff details for a single debt."""
        balance = debt.balance
        monthly_rate = debt.annual_rate_pct / 100 / 12
        total_interest = 0
        total_payments = 0
        months = 0
        max_months = 600  # Safety limit
        
        # Handle credit cards with special minimum payment rules
        if debt.debt_type == 'card':
            # Get actual card details from Supabase
            card_response = self.supabase.table('cards').select('*').eq('id', debt.id).single().execute()
            if card_response.data:
                card = Card.from_dict(card_response.data)
                # Ensure payment covers at least minimum percentage
                min_required = balance * (card.min_payment_pct / 100)
                monthly_payment = max(monthly_payment, min_required)
        
        # Simulate month by month payment
        while balance > 0.01 and months < max_months:
            months += 1
            
            # Calculate interest for this month
            interest_payment = balance * monthly_rate
            
            # Principal payment
            principal_payment = monthly_payment - interest_payment
            
            # Handle case where payment doesn't cover interest
            if principal_payment <= 0:
                # Payment doesn't cover interest, debt grows
                if debt.debt_type == 'card':
                    # For credit cards, assume minimum payment that at least reduces balance slowly
                    monthly_payment = interest_payment * 1.1
                    principal_payment = monthly_payment - interest_payment
                else:
                    # For loans, this shouldn't happen with proper minimum payments
                    principal_payment = 0.01  # Minimal reduction to avoid infinite loop
            
            # Ensure we don't overpay
            if principal_payment > balance:
                principal_payment = balance
                monthly_payment = balance + interest_payment
            
            # Update balance
            balance -= principal_payment
            total_interest += interest_payment
            total_payments += monthly_payment
        
        return {
            'months': months,
            'total_interest': total_interest,
            'total_payments': total_payments
        }
    
    def calculate_custom_scenario(self, customer_id: str, extra_payment: float) -> ScenarioResult:
        """Calculate a custom scenario with specified extra payment amount."""
        debts = self.get_customer_debts(customer_id)
        
        if not debts:
            return ScenarioResult(
                scenario_name="Plan Personalizado",
                total_monthly_payment=0,
                total_payoff_months=0,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas activas"
            )
        
        # Similar to optimized scenario but with custom extra payment
        sorted_debts = sorted(debts, key=lambda x: x.priority_score, reverse=True)
        total_minimum = sum(d.minimum_payment for d in debts)
        
        # Use provided extra payment amount
        actual_extra = max(0, extra_payment)
        
        # Rest of calculation follows optimized scenario logic...
        # (Implementation similar to calculate_optimized_scenario but with custom extra_payment)
        
        return self._calculate_with_extra_payment(customer_id, sorted_debts, actual_extra)