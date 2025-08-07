"""Supabase database configuration and connection management."""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")

# Create Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def get_db() -> Client:
    """
    Dependency to get Supabase client.
    Maintains compatibility with existing code structure.
    """
    return get_supabase()


def create_tables():
    """
    Tables are already created in Supabase.
    This function is kept for compatibility but does nothing.
    """
    pass


# Helper functions for common queries
async def fetch_customer(customer_id: str) -> dict:
    """Fetch a customer by ID."""
    supabase = get_supabase()
    response = supabase.table('customers').select('*').eq('id', customer_id).single().execute()
    return response.data if response.data else None


async def fetch_customer_with_relations(customer_id: str) -> dict:
    """Fetch a customer with all related data."""
    supabase = get_supabase()
    
    # Fetch customer
    customer = await fetch_customer(customer_id)
    if not customer:
        return None
    
    # Fetch related data in parallel-like manner
    loans = supabase.table('loans').select('*').eq('customer_id', customer_id).execute()
    cards = supabase.table('cards').select('*').eq('customer_id', customer_id).execute()
    cashflow = supabase.table('customer_cashflow').select('*').eq('customer_id', customer_id).single().execute()
    credit_scores = supabase.table('credit_scores').select('*').eq('customer_id', customer_id).order('date', desc=True).execute()
    payment_history = supabase.table('payment_history').select('*').eq('customer_id', customer_id).execute()
    
    # Combine results
    customer['loans'] = loans.data if loans.data else []
    customer['cards'] = cards.data if cards.data else []
    customer['cashflow'] = cashflow.data if cashflow.data else None
    customer['credit_scores'] = credit_scores.data if credit_scores.data else []
    customer['payment_history'] = payment_history.data if payment_history.data else []
    
    return customer


async def fetch_all_customers() -> list:
    """Fetch all customers."""
    supabase = get_supabase()
    response = supabase.table('customers').select('*').execute()
    return response.data if response.data else []


async def fetch_bank_offers() -> list:
    """Fetch all bank offers."""
    supabase = get_supabase()
    response = supabase.table('bank_offers').select('*').execute()
    return response.data if response.data else []