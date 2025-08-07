"""Payment history and bank offers models using dataclasses."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class PaymentHistory:
    """Customer payment history."""
    id: Optional[int] = None
    product_id: Optional[str] = None
    product_type: Optional[str] = None  # loan, card
    customer_id: Optional[str] = None
    date: Optional[datetime] = None
    amount: float = 0.0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PaymentHistory':
        """Create PaymentHistory instance from dictionary."""
        return cls(
            id=data.get('id'),
            product_id=data.get('product_id'),
            product_type=data.get('product_type'),
            customer_id=data.get('customer_id'),
            date=data.get('date'),
            amount=float(data.get('amount', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert PaymentHistory to dictionary."""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_type': self.product_type,
            'customer_id': self.customer_id,
            'date': self.date,
            'amount': self.amount,
            'created_at': self.created_at
        }


@dataclass
class BankOffer:
    """Bank consolidation offers."""
    id: str
    product_types_eligible: List[str] = None  # List of eligible product types
    max_consolidated_balance: float = 0.0
    new_rate_pct: float = 0.0
    max_term_months: int = 0
    conditions: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.product_types_eligible is None:
            self.product_types_eligible = []
    
    def calculate_new_payment(self, consolidated_balance: float) -> float:
        """Calculate new monthly payment after consolidation."""
        if self.max_term_months <= 0 or consolidated_balance <= 0:
            return 0
        
        monthly_rate = self.new_rate_pct / 100 / 12
        if monthly_rate == 0:
            return consolidated_balance / self.max_term_months
        
        # Standard loan payment formula
        payment = consolidated_balance * (monthly_rate * (1 + monthly_rate) ** self.max_term_months) / \
                  ((1 + monthly_rate) ** self.max_term_months - 1)
        return payment
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BankOffer':
        """Create BankOffer instance from dictionary."""
        return cls(
            id=data.get('id'),
            product_types_eligible=data.get('product_types_eligible', []),
            max_consolidated_balance=float(data.get('max_consolidated_balance', 0)),
            new_rate_pct=float(data.get('new_rate_pct', 0)),
            max_term_months=int(data.get('max_term_months', 0)),
            conditions=data.get('conditions'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> dict:
        """Convert BankOffer to dictionary."""
        return {
            'id': self.id,
            'product_types_eligible': self.product_types_eligible,
            'max_consolidated_balance': self.max_consolidated_balance,
            'new_rate_pct': self.new_rate_pct,
            'max_term_months': self.max_term_months,
            'conditions': self.conditions,
            'created_at': self.created_at
        }