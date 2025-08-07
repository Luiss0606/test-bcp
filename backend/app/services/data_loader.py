"""Data loading service for CSV and JSON files using Supabase."""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from app.core.database import get_supabase
from app.models import (
    Customer, CustomerCashflow, CreditScore, Loan, Card, 
    PaymentHistory, BankOffer
)


class DataLoader:
    """Service to load data from CSV and JSON files into Supabase database."""
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.supabase = get_supabase()
        
    def load_all_data(self) -> Dict[str, int]:
        """Load all data files into database."""
        results = {}
        
        # Load each data file
        results["customers"] = self._load_customers()
        results["cashflow"] = self._load_cashflow()
        results["credit_scores"] = self._load_credit_scores()
        results["loans"] = self._load_loans()
        results["cards"] = self._load_cards()
        results["payment_history"] = self._load_payment_history()
        results["bank_offers"] = self._load_bank_offers()
        
        return results
    
    def _load_customers(self) -> int:
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
        
        # Check existing customers in database
        existing_response = self.supabase.table('customers').select('id').execute()
        existing_ids = {c['id'] for c in existing_response.data} if existing_response.data else set()
        
        # Create customer records for new customers
        new_customers = []
        for customer_id in customer_ids:
            if customer_id not in existing_ids:
                new_customers.append({
                    'id': customer_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                })
        
        # Insert new customers if any
        if new_customers:
            self.supabase.table('customers').insert(new_customers).execute()
        
        return len(new_customers)
    
    def _load_cashflow(self) -> int:
        """Load customer cashflow data."""
        file_path = self.data_path / "customer_cashflow.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        
        # Get existing cashflow records
        existing_response = self.supabase.table('customer_cashflow').select('customer_id').execute()
        existing_customer_ids = {c['customer_id'] for c in existing_response.data} if existing_response.data else set()
        
        # Prepare new records
        new_records = []
        for _, row in df.iterrows():
            if row["customer_id"] not in existing_customer_ids:
                new_records.append({
                    'customer_id': row["customer_id"],
                    'monthly_income_avg': float(row["monthly_income_avg"]),
                    'income_variability_pct': float(row["income_variability_pct"]),
                    'essential_expenses_avg': float(row["essential_expenses_avg"]),
                    'created_at': datetime.utcnow().isoformat()
                })
        
        # Insert new records
        if new_records:
            self.supabase.table('customer_cashflow').insert(new_records).execute()
        
        return len(new_records)
    
    def _load_credit_scores(self) -> int:
        """Load credit score history."""
        file_path = self.data_path / "credit_score_history.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        
        # Prepare all records (allowing duplicates for history)
        new_records = []
        for _, row in df.iterrows():
            new_records.append({
                'customer_id': row["customer_id"],
                'date': pd.to_datetime(row["date"]).isoformat(),
                'credit_score': int(row["credit_score"]),
                'created_at': datetime.utcnow().isoformat()
            })
        
        # Insert all records
        if new_records:
            self.supabase.table('credit_scores').insert(new_records).execute()
        
        return len(new_records)
    
    def _load_loans(self) -> int:
        """Load loan data."""
        file_path = self.data_path / "loans.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        
        # Get existing loans
        existing_response = self.supabase.table('loans').select('id').execute()
        existing_ids = {l['id'] for l in existing_response.data} if existing_response.data else set()
        
        # Prepare new records
        new_records = []
        for _, row in df.iterrows():
            if row["loan_id"] not in existing_ids:
                new_records.append({
                    'id': row["loan_id"],
                    'customer_id': row["customer_id"],
                    'product_type': row["product_type"],
                    'principal': float(row["principal"]),
                    'annual_rate_pct': float(row["annual_rate_pct"]),
                    'remaining_term_months': int(row["remaining_term_months"]),
                    'collateral': bool(row["collateral"]) if row["collateral"] != "false" else False,
                    'days_past_due': int(row["days_past_due"]),
                    'created_at': datetime.utcnow().isoformat()
                })
        
        # Insert new records
        if new_records:
            self.supabase.table('loans').insert(new_records).execute()
        
        return len(new_records)
    
    def _load_cards(self) -> int:
        """Load credit card data."""
        file_path = self.data_path / "cards.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        
        # Get existing cards
        existing_response = self.supabase.table('cards').select('id').execute()
        existing_ids = {c['id'] for c in existing_response.data} if existing_response.data else set()
        
        # Prepare new records
        new_records = []
        for _, row in df.iterrows():
            if row["card_id"] not in existing_ids:
                new_records.append({
                    'id': row["card_id"],
                    'customer_id': row["customer_id"],
                    'balance': float(row["balance"]),
                    'annual_rate_pct': float(row["annual_rate_pct"]),
                    'min_payment_pct': float(row["min_payment_pct"]),
                    'payment_due_day': int(row["payment_due_day"]),
                    'days_past_due': int(row["days_past_due"]),
                    'created_at': datetime.utcnow().isoformat()
                })
        
        # Insert new records
        if new_records:
            self.supabase.table('cards').insert(new_records).execute()
        
        return len(new_records)
    
    def _load_payment_history(self) -> int:
        """Load payment history."""
        file_path = self.data_path / "payment_history.csv"
        if not file_path.exists():
            return 0
        
        df = pd.read_csv(file_path)
        
        # Prepare all records (allowing duplicates for history)
        new_records = []
        for _, row in df.iterrows():
            new_records.append({
                'product_id': row["product_id"],
                'product_type': row["product_type"],
                'customer_id': row["customer_id"],
                'date': pd.to_datetime(row["date"]).isoformat(),
                'amount': float(row["amount"]),
                'created_at': datetime.utcnow().isoformat()
            })
        
        # Insert all records
        if new_records:
            self.supabase.table('payment_history').insert(new_records).execute()
        
        return len(new_records)
    
    def _load_bank_offers(self) -> int:
        """Load bank consolidation offers."""
        file_path = self.data_path / "bank_offers.json"
        if not file_path.exists():
            return 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            offers_data = json.load(f)
        
        # Get existing offers
        existing_response = self.supabase.table('bank_offers').select('id').execute()
        existing_ids = {o['id'] for o in existing_response.data} if existing_response.data else set()
        
        # Prepare new records
        new_records = []
        for offer_data in offers_data:
            if offer_data["offer_id"] not in existing_ids:
                new_records.append({
                    'id': offer_data["offer_id"],
                    'product_types_eligible': offer_data["product_types_eligible"],
                    'max_consolidated_balance': float(offer_data["max_consolidated_balance"]),
                    'new_rate_pct': float(offer_data["new_rate_pct"]),
                    'max_term_months': int(offer_data["max_term_months"]),
                    'conditions': offer_data["conditions"],
                    'created_at': datetime.utcnow().isoformat()
                })
        
        # Insert new records
        if new_records:
            self.supabase.table('bank_offers').insert(new_records).execute()
        
        return len(new_records)


def load_sample_data():
    """Load sample data into database."""
    loader = DataLoader()
    results = loader.load_all_data()
    print("Data loading results:")
    for table, count in results.items():
        print(f"  {table}: {count} records loaded")
    return results


if __name__ == "__main__":
    load_sample_data()