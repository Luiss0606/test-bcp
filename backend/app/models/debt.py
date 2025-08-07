"""Debt-related models (loans and cards) using dataclasses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Loan:
    """Personal loans and microloans."""
    id: str
    customer_id: Optional[str] = None
    product_type: Optional[str] = None  # personal, micro
    principal: float = 0.0
    annual_rate_pct: float = 0.0
    remaining_term_months: int = 0
    collateral: bool = False
    days_past_due: int = 0
    created_at: Optional[datetime] = None
    
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
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Loan':
        """Create Loan instance from dictionary."""
        return cls(
            id=data.get('id'),
            customer_id=data.get('customer_id'),
            product_type=data.get('product_type'),
            principal=float(data.get('principal', 0)),
            annual_rate_pct=float(data.get('annual_rate_pct', 0)),
            remaining_term_months=int(data.get('remaining_term_months', 0)),
            collateral=bool(data.get('collateral', False)),
            days_past_due=int(data.get('days_past_due', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert Loan to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_type': self.product_type,
            'principal': self.principal,
            'annual_rate_pct': self.annual_rate_pct,
            'remaining_term_months': self.remaining_term_months,
            'collateral': self.collateral,
            'days_past_due': self.days_past_due,
            'created_at': self.created_at
        }


@dataclass
class Card:
    """Credit cards."""
    id: str
    customer_id: Optional[str] = None
    balance: float = 0.0
    annual_rate_pct: float = 0.0
    min_payment_pct: float = 0.0  # Minimum payment as percentage of balance
    payment_due_day: int = 0
    days_past_due: int = 0
    created_at: Optional[datetime] = None
    
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
        import math
        months = -(math.log(1 - (self.balance * monthly_rate) / monthly_payment)) / math.log(1 + monthly_rate)
        
        return max(1, int(months) + 1)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """Create Card instance from dictionary."""
        return cls(
            id=data.get('id'),
            customer_id=data.get('customer_id'),
            balance=float(data.get('balance', 0)),
            annual_rate_pct=float(data.get('annual_rate_pct', 0)),
            min_payment_pct=float(data.get('min_payment_pct', 0)),
            payment_due_day=int(data.get('payment_due_day', 0)),
            days_past_due=int(data.get('days_past_due', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert Card to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'balance': self.balance,
            'annual_rate_pct': self.annual_rate_pct,
            'min_payment_pct': self.min_payment_pct,
            'payment_due_day': self.payment_due_day,
            'days_past_due': self.days_past_due,
            'created_at': self.created_at
        }