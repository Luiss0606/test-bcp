"""Pydantic schemas for debt-related data."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class DebtBase(BaseModel):
    """Base debt information."""
    customer_id: str
    balance: float = Field(gt=0, description="Outstanding balance")
    annual_rate_pct: float = Field(ge=0, le=100, description="Annual interest rate percentage")
    days_past_due: int = Field(ge=0, description="Days past due")


class LoanSchema(DebtBase):
    """Loan schema."""
    id: str
    product_type: str = Field(description="Type of loan (personal, micro)")
    principal: float = Field(gt=0, description="Original loan amount")
    remaining_term_months: int = Field(gt=0, description="Remaining term in months")
    collateral: bool = Field(default=False, description="Whether loan is secured")
    
    class Config:
        from_attributes = True


class CardSchema(DebtBase):
    """Credit card schema."""
    id: str
    min_payment_pct: float = Field(gt=0, le=100, description="Minimum payment percentage")
    payment_due_day: int = Field(ge=1, le=31, description="Payment due day of month")
    
    class Config:
        from_attributes = True


class ScenarioResult(BaseModel):
    """Result of a debt payment scenario."""
    scenario_name: str
    total_payments: float
    total_interest: float
    payoff_months: int
    monthly_payment: float
    savings_vs_minimum: float = 0
    description: str
    detailed_plan: List[dict] = []


class CustomerAnalysis(BaseModel):
    """Complete customer debt analysis."""
    customer_id: str
    current_situation: dict
    scenarios: List[ScenarioResult]
    recommendations: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ConsolidationOffer(BaseModel):
    """Bank consolidation offer."""
    offer_id: str
    eligible_products: List[str]
    max_balance: float
    new_rate_pct: float
    max_term_months: int
    conditions: str
    estimated_payment: Optional[float] = None
    estimated_savings: Optional[float] = None
