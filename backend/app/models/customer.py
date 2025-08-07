"""Customer data models."""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Customer(Base):
    """Customer base information."""
    
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loans = relationship("Loan", back_populates="customer")
    cards = relationship("Card", back_populates="customer")
    cashflow = relationship("CustomerCashflow", back_populates="customer", uselist=False)
    credit_scores = relationship("CreditScore", back_populates="customer")
    payment_history = relationship("PaymentHistory", back_populates="customer")


class CustomerCashflow(Base):
    """Customer cash flow information."""
    
    __tablename__ = "customer_cashflow"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), index=True)
    monthly_income_avg = Column(Float)
    income_variability_pct = Column(Float)
    essential_expenses_avg = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="cashflow")
    
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


class CreditScore(Base):
    """Customer credit score history."""
    
    __tablename__ = "credit_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), index=True)
    date = Column(DateTime)
    credit_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="credit_scores")
