import sqlite3
import os

# Ścieżka do pliku bazy — relatywna do głównego folderu projektu
DB_PATH = "data/investments.db"

def get_connection():
    """Zwraca połączenie z bazą SQLite. Tworzy plik jeśli nie istnieje."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # wyniki jako słowniki, nie tupple
    return conn

def init_db():
    """Tworzy tabele i wypełnia funds. Uruchamiana przy starcie aplikacji."""
    conn = get_connection()
    
    with open("backend/database/schema.sql", "r") as f:
        conn.executescript(f.read())
    
    conn.commit()
    conn.close()