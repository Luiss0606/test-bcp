"""Financial calculation engine for debt optimization."""

from typing import List, Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
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
            "first_6_months": payments[:6] if len(payments) >= 6 else payments,
            "milestones": self._calculate_milestones()
        }
    
    def _calculate_milestones(self) -> List[Dict[str, Any]]:
        """Calculate important milestones in the payment schedule."""
        if not self.monthly_breakdown:
            return []
        
        milestones = []
        total_paid = 0
        
        for i, detail in enumerate(self.monthly_breakdown):
            total_paid += detail.payment_amount
            
            # Add milestone at 25%, 50%, 75%, and 100%
            progress = (i + 1) / len(self.monthly_breakdown)
            if progress >= 0.25 and not any(m.get('type') == '25%' for m in milestones):
                milestones.append({
                    "type": "25%",
                    "month": i + 1,
                    "remaining_balance": detail.remaining_balance,
                    "total_paid_so_far": total_paid,
                    "progress": "25% completado"
                })
            elif progress >= 0.50 and not any(m.get('type') == '50%' for m in milestones):
                milestones.append({
                    "type": "50%",
                    "month": i + 1,
                    "remaining_balance": detail.remaining_balance,
                    "total_paid_so_far": total_paid,
                    "progress": "Mitad del camino"
                })
            elif progress >= 0.75 and not any(m.get('type') == '75%' for m in milestones):
                milestones.append({
                    "type": "75%",
                    "month": i + 1,
                    "remaining_balance": detail.remaining_balance,
                    "total_paid_so_far": total_paid,
                    "progress": "75% completado"
                })
        
        # Final milestone
        if self.monthly_breakdown:
            milestones.append({
                "type": "100%",
                "month": len(self.monthly_breakdown),
                "remaining_balance": 0,
                "total_paid_so_far": self.total_payments,
                "progress": "¡Deuda liquidada!"
            })
        
        return milestones


@dataclass
class MonthlyPaymentDetail:
    """Monthly payment breakdown for a specific month."""
    month: int
    debt_id: str
    payment_amount: float
    interest_portion: float
    principal_portion: float
    remaining_balance: float


@dataclass
class ScenarioResult:
    """Complete scenario calculation result."""
    scenario_name: str
    total_monthly_payment: float  # Sum of all monthly payments across debts
    total_payoff_months: int
    total_interest: float
    total_payments: float
    savings_vs_minimum: float
    payment_plans: List[PaymentPlan]
    description: str
    monthly_breakdown: List[MonthlyPaymentDetail] = None  # Optional detailed breakdown
    
    @property
    def weighted_average_monthly_payment(self) -> float:
        """Calculate the true weighted average monthly payment."""
        if self.total_payoff_months == 0:
            return 0
        return self.total_payments / self.total_payoff_months


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
    
    def calculate_minimum_payment_scenario(self, customer_id: str, generate_breakdown: bool = True) -> ScenarioResult:
        """Calculate scenario where customer only pays minimums."""
        debts = self.get_customer_debts(customer_id)
        payment_plans = []
        total_monthly = 0
        total_interest = 0
        total_payments = 0
        max_months = 0
        all_monthly_breakdown = []
        
        for debt in debts:
            plan = self._calculate_debt_payoff(debt, debt.minimum_payment, generate_breakdown)
            payment_plans.append(plan)
            total_monthly += plan.monthly_payment
            total_interest += plan.total_interest
            total_payments += plan.total_payments
            max_months = max(max_months, plan.payoff_months)
            
            # Collect monthly breakdown if generated
            if generate_breakdown and hasattr(plan, 'monthly_breakdown') and plan.monthly_breakdown:
                all_monthly_breakdown.extend(plan.monthly_breakdown)
        
        return ScenarioResult(
            scenario_name="Pago Mínimo",
            total_monthly_payment=total_monthly,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=0,  # This is the baseline
            payment_plans=payment_plans,
            description="Escenario donde solo se pagan los montos mínimos requeridos.",
            monthly_breakdown=all_monthly_breakdown if generate_breakdown else None
        )
    
    def calculate_optimized_scenario(self, customer_id: str) -> ScenarioResult:
        """Calculate optimized payment scenario using TRUE avalanche method with cascading."""
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
        
        # If no extra payment available, return minimum scenario
        if extra_payment <= 0:
            result = self.calculate_minimum_payment_scenario(customer_id)
            result.scenario_name = "Plan Optimizado"
            result.description = "Sin flujo extra disponible. Se muestra escenario de pagos mínimos."
            return result
        
        # Sort debts by interest rate (avalanche method - highest rate first)
        sorted_debts = sorted(debts, key=lambda x: x.annual_rate_pct, reverse=True)
        
        # Simulate month-by-month avalanche payments with cascading
        monthly_breakdown_all = []
        debt_balances = {debt.id: debt.balance for debt in sorted_debts}
        debt_rates = {debt.id: debt.annual_rate_pct / 100 / 12 for debt in sorted_debts}
        debt_minimums = {debt.id: debt.minimum_payment for debt in sorted_debts}
        debt_paid_off_month = {}
        
        total_interest_paid = 0
        total_amount_paid = 0
        month = 0
        max_months = 600  # Safety limit
        
        while any(balance > 0.01 for balance in debt_balances.values()) and month < max_months:
            month += 1
            monthly_payment_total = available_budget
            remaining_payment = available_budget
            
            # First pass: pay minimums on all active debts
            for debt in sorted_debts:
                if debt_balances[debt.id] > 0.01:
                    interest = debt_balances[debt.id] * debt_rates[debt.id]
                    
                    # For credit cards, recalculate minimum if needed
                    min_payment = debt_minimums[debt.id]
                    if debt.debt_type == 'card':
                        from app.models.debt import Card
                        card = self.db.query(Card).filter(Card.id == debt.id).first()
                        if card and card.min_payment_pct:
                            min_payment = max(debt_balances[debt.id] * (card.min_payment_pct / 100), 10.0)
                            min_payment = min(min_payment, debt_balances[debt.id] + interest)
                    
                    payment_to_debt = min(min_payment, remaining_payment, debt_balances[debt.id] + interest)
                    principal = max(0, payment_to_debt - interest)
                    
                    debt_balances[debt.id] -= principal
                    total_interest_paid += interest
                    total_amount_paid += payment_to_debt
                    remaining_payment -= payment_to_debt
                    
                    # Record payment detail
                    monthly_breakdown_all.append(MonthlyPaymentDetail(
                        month=month,
                        debt_id=debt.id,
                        payment_amount=payment_to_debt,
                        interest_portion=interest,
                        principal_portion=principal,
                        remaining_balance=debt_balances[debt.id]
                    ))
                    
                    if debt_balances[debt.id] <= 0.01:
                        debt_balances[debt.id] = 0
                        debt_paid_off_month[debt.id] = month
            
            # Second pass: apply remaining payment to highest interest debt still active
            for debt in sorted_debts:
                if debt_balances[debt.id] > 0.01 and remaining_payment > 0:
                    # Apply all remaining payment to this debt
                    extra_payment_to_debt = min(remaining_payment, debt_balances[debt.id])
                    debt_balances[debt.id] -= extra_payment_to_debt
                    total_amount_paid += extra_payment_to_debt
                    
                    # Update the payment detail for this debt
                    for detail in monthly_breakdown_all:
                        if detail.month == month and detail.debt_id == debt.id:
                            detail.payment_amount += extra_payment_to_debt
                            detail.principal_portion += extra_payment_to_debt
                            detail.remaining_balance = debt_balances[debt.id]
                            break
                    
                    remaining_payment -= extra_payment_to_debt
                    
                    if debt_balances[debt.id] <= 0.01:
                        debt_balances[debt.id] = 0
                        debt_paid_off_month[debt.id] = month
                    
                    break  # Only apply to the highest priority debt
        
        # Create payment plans from the simulation
        payment_plans = []
        for debt in sorted_debts:
            debt_details = [d for d in monthly_breakdown_all if d.debt_id == debt.id]
            payoff_month = debt_paid_off_month.get(debt.id, month)
            
            if debt_details:
                total_paid = sum(d.payment_amount for d in debt_details)
                total_interest = sum(d.interest_portion for d in debt_details)
                avg_payment = total_paid / len(debt_details) if debt_details else 0
                
                plan = PaymentPlan(
                    debt_id=debt.id,
                    monthly_payment=avg_payment,
                    payoff_months=payoff_month,
                    total_interest=total_interest,
                    total_payments=total_paid,
                    monthly_breakdown=debt_details
                )
            else:
                # Fallback if no details
                plan = PaymentPlan(
                    debt_id=debt.id,
                    monthly_payment=debt.minimum_payment,
                    payoff_months=0,
                    total_interest=0,
                    total_payments=0
                )
            
            payment_plans.append(plan)
        
        # Calculate savings vs minimum
        minimum_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = minimum_scenario.total_payments - total_amount_paid
        
        return ScenarioResult(
            scenario_name="Plan Optimizado",
            total_monthly_payment=available_budget,
            total_payoff_months=month,
            total_interest=total_interest_paid,
            total_payments=total_amount_paid,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description=f"Método avalancha con cascada: ${extra_payment:,.2f}/mes extra aplicado estratégicamente.",
            monthly_breakdown=monthly_breakdown_all
        )
    
    def calculate_consolidation_scenario(self, customer_id: str, eligible_offers_data: List[Dict] = None) -> ScenarioResult:
        """Calculate CORRECTED debt consolidation scenario with proper math."""
        debts = self.get_customer_debts(customer_id)
        
        # If no debts, return empty scenario
        if not debts:
            return ScenarioResult(
                scenario_name="Consolidación",
                total_monthly_payment=0,
                total_payoff_months=0,
                total_interest=0,
                total_payments=0,
                savings_vs_minimum=0,
                payment_plans=[],
                description="No hay deudas para consolidar."
            )
        
        # Get bank offers
        if eligible_offers_data is None:
            # Fallback to basic method
            offers = self.db.query(BankOffer).all()
            
            if not offers:
                # No offers available, return optimized scenario
                result = self.calculate_optimized_scenario(customer_id)
                result.scenario_name = "Consolidación"
                result.description = "No hay ofertas de consolidación disponibles. Se muestra plan optimizado."
                return result
            
            # Use the offer with lowest rate
            best_offer = min(offers, key=lambda x: x.new_rate_pct)
        else:
            # Use intelligently filtered offers
            if not eligible_offers_data:
                # No eligible offers
                result = self.calculate_optimized_scenario(customer_id)
                result.scenario_name = "Consolidación"
                result.description = "No hay ofertas de consolidación elegibles. Se muestra plan optimizado."
                return result
            
            # Get the best offer
            best_offer_id = eligible_offers_data[0]["offer_id"]
            best_offer = self.db.query(BankOffer).filter(BankOffer.id == best_offer_id).first()
            
            if not best_offer:
                result = self.calculate_optimized_scenario(customer_id)
                result.scenario_name = "Consolidación"
                result.description = "Error al obtener la oferta. Se muestra plan optimizado."
                return result
        
        # Determine which debts can be consolidated
        consolidatable_debts = []
        unconsolidated_debts = []
        
        for debt in debts:
            # Check if debt type is eligible for consolidation
            if debt.debt_type in best_offer.product_types_eligible:
                consolidatable_debts.append(debt)
            else:
                unconsolidated_debts.append(debt)
        
        # Calculate total consolidatable balance
        total_consolidatable = sum(debt.balance for debt in consolidatable_debts)
        
        # Check if we exceed the maximum consolidation limit
        if total_consolidatable > best_offer.max_consolidated_balance:
            # Partial consolidation - prioritize highest interest debts
            consolidatable_debts.sort(key=lambda x: x.annual_rate_pct, reverse=True)
            
            consolidated_debts = []
            remaining_capacity = best_offer.max_consolidated_balance
            
            for debt in consolidatable_debts:
                if debt.balance <= remaining_capacity:
                    consolidated_debts.append(debt)
                    remaining_capacity -= debt.balance
                else:
                    # This debt doesn't fit, add to unconsolidated
                    unconsolidated_debts.append(debt)
            
            # Update consolidatable_debts to only include what we're actually consolidating
            consolidatable_debts = consolidated_debts
            total_consolidatable = sum(debt.balance for debt in consolidatable_debts)
        
        # If nothing to consolidate, return optimized scenario
        if total_consolidatable <= 0:
            result = self.calculate_optimized_scenario(customer_id)
            result.scenario_name = "Consolidación"
            result.description = "No hay deudas elegibles para consolidar. Se muestra plan optimizado."
            return result
        
        # Calculate the consolidated loan payment using the formula
        consolidated_payment = best_offer.calculate_new_payment(total_consolidatable)
        
        # Calculate interest for consolidated loan properly
        monthly_rate = best_offer.new_rate_pct / 100 / 12
        consolidated_total_payments = consolidated_payment * best_offer.max_term_months
        consolidated_interest = consolidated_total_payments - total_consolidatable
        
        # Create payment plans
        payment_plans = []
        total_monthly = 0
        total_interest = 0
        total_payments = 0
        max_months = 0
        
        # Add consolidated debt plan if we have consolidated debts
        if total_consolidatable > 0:
            # Create detailed breakdown for consolidated debt
            consolidated_breakdown = []
            remaining_balance = total_consolidatable
            
            for month in range(1, best_offer.max_term_months + 1):
                interest_portion = remaining_balance * monthly_rate
                principal_portion = consolidated_payment - interest_portion
                remaining_balance -= principal_portion
                
                if remaining_balance < 0.01:
                    remaining_balance = 0
                
                consolidated_breakdown.append(MonthlyPaymentDetail(
                    month=month,
                    debt_id="CONSOLIDATED",
                    payment_amount=consolidated_payment,
                    interest_portion=interest_portion,
                    principal_portion=principal_portion,
                    remaining_balance=remaining_balance
                ))
                
                if remaining_balance == 0:
                    break
            
            plan = PaymentPlan(
                debt_id=f"CONSOLIDATED ({len(consolidatable_debts)} deudas)",
                monthly_payment=consolidated_payment,
                payoff_months=best_offer.max_term_months,
                total_interest=consolidated_interest,
                total_payments=consolidated_total_payments,
                monthly_breakdown=consolidated_breakdown
            )
            payment_plans.append(plan)
            total_monthly += consolidated_payment
            total_interest += consolidated_interest
            total_payments += consolidated_total_payments
            max_months = best_offer.max_term_months
        
        # Calculate payments for unconsolidated debts
        # Use optimized payment strategy for unconsolidated debts if there's cashflow available
        cashflow = self.db.query(CustomerCashflow).filter(
            CustomerCashflow.customer_id == customer_id
        ).first()
        
        if unconsolidated_debts and cashflow:
            # Calculate remaining budget after consolidated payment
            remaining_budget = cashflow.conservative_cashflow - consolidated_payment
            
            # Sort unconsolidated debts by interest rate (avalanche)
            unconsolidated_debts.sort(key=lambda x: x.annual_rate_pct, reverse=True)
            
            for debt in unconsolidated_debts:
                # Allocate remaining budget to this debt if possible
                if remaining_budget > debt.minimum_payment:
                    payment_amount = min(remaining_budget, debt.minimum_payment + (remaining_budget - debt.minimum_payment))
                else:
                    payment_amount = debt.minimum_payment
                
                plan = self._calculate_debt_payoff(debt, payment_amount, generate_breakdown=True)
                payment_plans.append(plan)
                total_monthly += payment_amount
                total_interest += plan.total_interest
                total_payments += plan.total_payments
                max_months = max(max_months, plan.payoff_months)
                
                remaining_budget -= payment_amount
                if remaining_budget < 0:
                    remaining_budget = 0
        elif unconsolidated_debts:
            # No cashflow data, use minimum payments
            for debt in unconsolidated_debts:
                plan = self._calculate_debt_payoff(debt, debt.minimum_payment, generate_breakdown=True)
                payment_plans.append(plan)
                total_monthly += debt.minimum_payment
                total_interest += plan.total_interest
                total_payments += plan.total_payments
                max_months = max(max_months, plan.payoff_months)
        
        # Calculate savings vs minimum scenario
        minimum_scenario = self.calculate_minimum_payment_scenario(customer_id)
        savings = minimum_scenario.total_payments - total_payments
        
        # Create detailed description
        consolidated_debt_ids = [d.id for d in consolidatable_debts]
        unconsolidated_debt_ids = [d.id for d in unconsolidated_debts]
        
        description = f"""Consolidación con {best_offer.id} al {best_offer.new_rate_pct}% anual.
Deudas consolidadas ({len(consolidated_debt_ids)}): {', '.join(consolidated_debt_ids[:3])}{'...' if len(consolidated_debt_ids) > 3 else ''}
Monto consolidado: ${total_consolidatable:,.2f}
Pago mensual consolidado: ${consolidated_payment:,.2f}
Plazo: {best_offer.max_term_months} meses"""
        
        if unconsolidated_debt_ids:
            description += f"\nDeudas no consolidadas ({len(unconsolidated_debt_ids)}): {', '.join(unconsolidated_debt_ids[:3])}{'...' if len(unconsolidated_debt_ids) > 3 else ''}"
        
        return ScenarioResult(
            scenario_name="Consolidación",
            total_monthly_payment=total_monthly,
            total_payoff_months=max_months,
            total_interest=total_interest,
            total_payments=total_payments,
            savings_vs_minimum=savings,
            payment_plans=payment_plans,
            description=description.strip()
        )
    
    def _calculate_debt_payoff(self, debt: DebtItem, monthly_payment: float, generate_breakdown: bool = False) -> PaymentPlan:
        """Calculate payoff plan for a single debt with optional detailed breakdown."""
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
        monthly_details = []
        total_payments_actual = 0
        
        # For credit cards, get the minimum payment percentage for variable payments
        is_credit_card = debt.debt_type == 'card'
        min_payment_pct = None
        if is_credit_card:
            # Get the card from database to access min_payment_pct
            from app.models.debt import Card
            card = self.db.query(Card).filter(Card.id == debt.id).first()
            if card:
                min_payment_pct = card.min_payment_pct
        
        # Simulate month by month payment
        while balance > 0.01 and months < 600:  # Max 50 years
            months += 1
            interest_payment = balance * monthly_rate
            
            # For credit cards with minimum payments, recalculate payment each month
            current_payment = monthly_payment
            if is_credit_card and min_payment_pct and monthly_payment == debt.minimum_payment:
                # This is a minimum payment scenario for credit card
                current_payment = max(balance * (min_payment_pct / 100), 10.0)  # Minimum $10
                current_payment = min(current_payment, balance + interest_payment)  # Don't overpay
            
            principal_payment = min(current_payment - interest_payment, balance)
            
            if principal_payment <= 0:
                # Payment doesn't cover interest - debt grows
                months = 999
                total_interest = debt.balance * 10  # Penalty
                total_payments_actual = debt.balance * 10  # Penalty
                break
            
            total_interest += interest_payment
            balance -= principal_payment
            total_payments_actual += current_payment
            
            # Store monthly breakdown if requested
            if generate_breakdown:
                monthly_details.append(MonthlyPaymentDetail(
                    month=months,
                    debt_id=debt.id,
                    payment_amount=current_payment,
                    interest_portion=interest_payment,
                    principal_portion=principal_payment,
                    remaining_balance=balance
                ))
        
        # For credit cards with minimum payments, the monthly_payment reported should be the initial payment
        reported_monthly_payment = monthly_payment
        
        plan = PaymentPlan(
            debt_id=debt.id,
            monthly_payment=reported_monthly_payment,
            payoff_months=months,
            total_interest=total_interest,
            total_payments=total_payments_actual,
            monthly_breakdown=monthly_details if generate_breakdown else None
        )
        
        return plan
    
    # MÉTODO ELIMINADO: _get_customer_eligibility_data
    # Ahora se usa el perfil completo del cliente en FinancialAnalysisService._get_customer_info()
    # para análisis inteligente de elegibilidad con EligibilityAgent
