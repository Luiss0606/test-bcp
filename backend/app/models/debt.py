"""Debt-related models (loans and cards)."""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Loan(Base):
    """Personal loans and microloans."""
    
    __tablename__ = "loans"
    
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), index=True)
    product_type = Column(String)  # personal, micro
    principal = Column(Float)
    annual_rate_pct = Column(Float)
    remaining_term_months = Column(Integer)
    collateral = Column(Boolean, default=False)
    days_past_due = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="loans")
    
    @property
    def monthly_rate(self) -> float:
        """Monthly interest rate."""
        return self.annual_rate_pct / 100 / 12
    
    @property
    def minimum_payment(self) -> float:
        """Calculate minimum monthly payment using loan amortization formula."""
        if self.remaining_term_months <= 0:
            return self.principal
        
        monthly_rate = self.monthly_rate
        if monthly_rate == 0:
            return self.principal / self.remaining_term_months
        
        # Standard loan amortization formula
        payment = self.principal * (monthly_rate * (1 + monthly_rate) ** self.remaining_term_months) / \
                  ((1 + monthly_rate) ** self.remaining_term_months - 1)
        return payment
    
    @property
    def is_in_default(self) -> bool:
        """Check if loan is in default (>30 days past due)."""
        return self.days_past_due > 30
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score for debt optimization (higher = pay first)."""
        score = self.annual_rate_pct  # Base score is interest rate
        
        # Penalty for being past due
        if self.days_past_due > 0:
            score += self.days_past_due * 0.5
        
        # Higher priority for unsecured debt
        if not self.collateral:
            score += 5
        
        return score


class Card(Base):
    """Credit cards."""
    
    __tablename__ = "cards"
    
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), index=True)
    balance = Column(Float)
    annual_rate_pct = Column(Float)
    min_payment_pct = Column(Float)  # Minimum payment as percentage of balance
    payment_due_day = Column(Integer)
    days_past_due = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="cards")
    
    @property
    def monthly_rate(self) -> float:
        """Monthly interest rate."""
        return self.annual_rate_pct / 100 / 12
    
    @property
    def minimum_payment(self) -> float:
        """Calculate minimum monthly payment."""
        return self.balance * (self.min_payment_pct / 100)
    
    @property
    def is_in_default(self) -> bool:
        """Check if card is in default (>30 days past due)."""
        return self.days_past_due > 30
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score for debt optimization (higher = pay first)."""
        score = self.annual_rate_pct  # Base score is interest rate
        
        # Penalty for being past due
        if self.days_past_due > 0:
            score += self.days_past_due * 0.5
        
        # Credit cards typically have higher priority due to revolving nature
        score += 10
        
        return score
    
    def calculate_payoff_time(self, monthly_payment: float) -> int:
        """Calculate months to pay off card with given monthly payment."""
        if monthly_payment <= 0 or self.balance <= 0:
            return 0
        
        monthly_rate = self.monthly_rate
        if monthly_payment <= self.balance * monthly_rate:
            return 999  # Never pays off with minimum interest
        
        if monthly_rate == 0:
            return int(self.balance / monthly_payment)
        
        # Formula for credit card payoff time
        months = -(1/12) * (1/monthly_rate) * \
                 (1 + (1/monthly_rate) * 
                  (monthly_payment / self.balance - monthly_rate)) * \
                 (1 - (monthly_payment / (monthly_payment - self.balance * monthly_rate)))
        
        return max(1, int(months) + 1)
