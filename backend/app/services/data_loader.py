"""Data loading service for CSV and JSON files."""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import (
    Customer, CustomerCashflow, CreditScore, Loan, Card, 
    PaymentHistory, BankOffer
)
from app.core.database import get_db, create_tables


class DataLoader:
    """Service to load data from CSV and JSON files into database."""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        
    def load_all_data(self, db: Session) -> Dict[str, int]:
        """Load all data files into database."""
        results = {}
        
        # Create tables if they don't exist
        create_tables()
        
        # Load each data file
        results["customers"] = self._load_customers(db)
        results["cashflow"] = self._load_cashflow(db)
        results["credit_scores"] = self._load_credit_scores(db)
        results["loans"] = self._load_loans(db)
        results["cards"] = self._load_cards(db)
        results["payment_history"] = self._load_payment_history(db)
        results["bank_offers"] = self._load_bank_offers(db)
        
        return results
    
    def _load_customers(self, db: Session) -> int:
        """Create customer records from all data sources."""
        customer_ids = set()
        
        # Collect customer IDs from all sources
        files_to_check = [
            "loans.csv", "cards.csv", "payment_history.csv", 
            "credit_score_history.csv", "customer_cashflow.csv"
        ]
        
        for file_name in files_to_check:
            file_path = self.data_path / file_name
            if file_path.exists():
                df = pd.read_csv(file_path)
                if "customer_id" in df.columns:
                    customer_ids.update(df["customer_id"].unique())
        
        # Create customer records
        count = 0
        for customer_id in customer_ids:
            existing = db.query(Customer).filter(Customer.id == customer_id).first()
            if not existing:
                customer = Customer(id=customer_id)
                db.add(customer)
                count += 1
        
        db.commit()
        return count
    
    def _load_cashflow(self, db: Session) -> int:
        """Load customer cashflow data."""
        file_path = self.data_path / "customer_cashflow.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        count = 0
        
        for _, row in df.iterrows():
            existing = db.query(CustomerCashflow).filter(
                CustomerCashflow.customer_id == row["customer_id"]
            ).first()
            
            if not existing:
                cashflow = CustomerCashflow(
                    customer_id=row["customer_id"],
                    monthly_income_avg=float(row["monthly_income_avg"]),
                    income_variability_pct=float(row["income_variability_pct"]),
                    essential_expenses_avg=float(row["essential_expenses_avg"])
                )
                db.add(cashflow)
                count += 1
        
        db.commit()
        return count
    
    def _load_credit_scores(self, db: Session) -> int:
        """Load credit score history."""
        file_path = self.data_path / "credit_score_history.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        count = 0
        
        for _, row in df.iterrows():
            credit_score = CreditScore(
                customer_id=row["customer_id"],
                date=pd.to_datetime(row["date"]),
                credit_score=int(row["credit_score"])
            )
            db.add(credit_score)
            count += 1
        
        db.commit()
        return count
    
    def _load_loans(self, db: Session) -> int:
        """Load loan data."""
        file_path = self.data_path / "loans.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        count = 0
        
        for _, row in df.iterrows():
            existing = db.query(Loan).filter(Loan.id == row["loan_id"]).first()
            if not existing:
                loan = Loan(
                    id=row["loan_id"],
                    customer_id=row["customer_id"],
                    product_type=row["product_type"],
                    principal=float(row["principal"]),
                    annual_rate_pct=float(row["annual_rate_pct"]),
                    remaining_term_months=int(row["remaining_term_months"]),
                    collateral=bool(row["collateral"]) if row["collateral"] != "false" else False,
                    days_past_due=int(row["days_past_due"])
                )
                db.add(loan)
                count += 1
        
        db.commit()
        return count
    
    def _load_cards(self, db: Session) -> int:
        """Load credit card data."""
        file_path = self.data_path / "cards.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        count = 0
        
        for _, row in df.iterrows():
            existing = db.query(Card).filter(Card.id == row["card_id"]).first()
            if not existing:
                card = Card(
                    id=row["card_id"],
                    customer_id=row["customer_id"],
                    balance=float(row["balance"]),
                    annual_rate_pct=float(row["annual_rate_pct"]),
                    min_payment_pct=float(row["min_payment_pct"]),
                    payment_due_day=int(row["payment_due_day"]),
                    days_past_due=int(row["days_past_due"])
                )
                db.add(card)
                count += 1
        
        db.commit()
        return count
    
    def _load_payment_history(self, db: Session) -> int:
        """Load payment history."""
        file_path = self.data_path / "payment_history.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        count = 0
        
        for _, row in df.iterrows():
            payment = PaymentHistory(
                product_id=row["product_id"],
                product_type=row["product_type"],
                customer_id=row["customer_id"],
                date=pd.to_datetime(row["date"]),
                amount=float(row["amount"])
            )
            db.add(payment)
            count += 1
        
        db.commit()
        return count
    
    def _load_bank_offers(self, db: Session) -> int:
        """Load bank consolidation offers."""
        file_path = self.data_path / "bank_offers.json"
        if not file_path.exists():
            return 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            offers_data = json.load(f)
        
        count = 0
        for offer_data in offers_data:
            existing = db.query(BankOffer).filter(
                BankOffer.id == offer_data["offer_id"]
            ).first()
            
            if not existing:
                offer = BankOffer(
                    id=offer_data["offer_id"],
                    product_types_eligible=offer_data["product_types_eligible"],
                    max_consolidated_balance=float(offer_data["max_consolidated_balance"]),
                    new_rate_pct=float(offer_data["new_rate_pct"]),
                    max_term_months=int(offer_data["max_term_months"]),
                    conditions=offer_data["conditions"]
                )
                db.add(offer)
                count += 1
        
        db.commit()
        return count


def load_sample_data():
    """Load sample data into database."""
    loader = DataLoader()
    db = next(get_db())
    try:
        results = loader.load_all_data(db)
        print("Data loading results:")
        for table, count in results.items():
            print(f"  {table}: {count} records loaded")
        return results
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_data()
