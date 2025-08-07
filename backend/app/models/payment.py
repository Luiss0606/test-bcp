"""Payment history and bank offers models."""

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class PaymentHistory(Base):
    """Customer payment history."""
    
    __tablename__ = "payment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, index=True)
    product_type = Column(String)  # loan, card
    customer_id = Column(String, ForeignKey("customers.id"), index=True)
    date = Column(DateTime)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("Customer", back_populates="payment_history")


class BankOffer(Base):
    """Bank consolidation offers."""
    
    __tablename__ = "bank_offers"
    
    id = Column(String, primary_key=True, index=True)
    product_types_eligible = Column(JSON)  # List of eligible product types
    max_consolidated_balance = Column(Float)
    new_rate_pct = Column(Float)
    max_term_months = Column(Integer)
    conditions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # MÉTODO ELIMINADO: is_eligible_for_customer
    # Ahora se usa EligibilityAgent para análisis inteligente de elegibilidad
    # El método anterior tenía limitaciones para condiciones complejas
    
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
