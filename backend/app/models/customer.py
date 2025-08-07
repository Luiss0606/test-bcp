"""Customer data models using dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Customer:
    """Customer base information."""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data (populated when needed)
    loans: List['Loan'] = field(default_factory=list)
    cards: List['Card'] = field(default_factory=list)
    cashflow: Optional['CustomerCashflow'] = None
    credit_scores: List['CreditScore'] = field(default_factory=list)
    payment_history: List['PaymentHistory'] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Customer':
        """Create Customer instance from dictionary."""
        return cls(
            id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self) -> dict:
        """Convert Customer to dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


@dataclass
class CustomerCashflow:
    """Customer cash flow information."""
    id: Optional[int] = None
    customer_id: Optional[str] = None
    monthly_income_avg: float = 0.0
    income_variability_pct: float = 0.0
    essential_expenses_avg: float = 0.0
    created_at: Optional[datetime] = None
    
    @property
    def available_cashflow(self) -> float:
        """Calculate available monthly cashflow for debt payments."""
        return max(0, self.monthly_income_avg - self.essential_expenses_avg)
    
    @property
    def conservative_cashflow(self) -> float:
        """Calculate conservative cashflow considering income variability."""
        variability_factor = 1 - (self.income_variability_pct / 100)
        conservative_income = self.monthly_income_avg * variability_factor
        return max(0, conservative_income - self.essential_expenses_avg)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomerCashflow':
        """Create CustomerCashflow instance from dictionary."""
        if not data:
            return None
        return cls(
            id=data.get('id'),
            customer_id=data.get('customer_id'),
            monthly_income_avg=float(data.get('monthly_income_avg', 0)),
            income_variability_pct=float(data.get('income_variability_pct', 0)),
            essential_expenses_avg=float(data.get('essential_expenses_avg', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert CustomerCashflow to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'monthly_income_avg': self.monthly_income_avg,
            'income_variability_pct': self.income_variability_pct,
            'essential_expenses_avg': self.essential_expenses_avg,
            'created_at': self.created_at
        }


@dataclass
class CreditScore:
    """Customer credit score history."""
    id: Optional[int] = None
    customer_id: Optional[str] = None
    date: Optional[datetime] = None
    credit_score: int = 0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CreditScore':
        """Create CreditScore instance from dictionary."""
        return cls(
            id=data.get('id'),
            customer_id=data.get('customer_id'),
            date=data.get('date'),
            credit_score=int(data.get('credit_score', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert CreditScore to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'date': self.date,
            'credit_score': self.credit_score,
            'created_at': self.created_at
        }