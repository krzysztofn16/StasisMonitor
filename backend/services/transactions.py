import pandas as pd
from backend.database.db import get_connection


def get_transactions(user_id: str = "default") -> pd.DataFrame:
    """Pobiera wszystkie transakcje użytkownika"""
    conn = get_connection()
    df = pd.read_sql("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    """, conn, params=(user_id,))
    conn.close()
    return df


def add_transaction(user_id, fund_code, type, date, units, price_per_unit, notes=""):
    """Dodaje nową transakcję do bazy"""
    total_value = units * price_per_unit
    conn = get_connection()
    conn.execute("""
        INSERT INTO transactions
            (user_id, fund_code, type, date, units, price_per_unit, total_value, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, fund_code, type, date, units, price_per_unit, total_value, notes))
    conn.commit()
    conn.close()


def delete_transaction(transaction_id: int):
    """Usuwa transakcję po ID"""
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()