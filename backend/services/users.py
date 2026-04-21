import hashlib
from backend.database.db import get_connection

def hash_pin(pin: str) -> str:
    """Hashuje PIN użytkownika za pomocą SHA-256, nigdy nie przechowujemy PINu w czystej formie"""
    return hashlib.sha256(pin.encode()).hexdigest()

def register_user(username: str, pin: str) -> tuple[bool, str]:
    """
    Rejestruje nowego użytkownika. Zwraca (sukces, wiadomość)
    Zwraca (sukces, wiadomosc)
    """
    if len(username.strip()) < 2:
        return False, "Nazwa użytkownika musi mieć co najmniej 2 znaki."
    if len(pin) != 4 or not pin.isdigit():
        return False, "PIN musi mieć dokładnie 4 cyfry."
    
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, pin) VALUES (?, ?)",
            (username.strip().lower(), hash_pin(pin))
        )
        conn.commit()
        return True, f"Konto '{username}' zostało utworzone."
    except Exception:
        return False, f"Nazwa użytkownika '{username}' jest już zajęta - wybierz inną."
    finally:
        conn.close()

def login_user(username: str, pin: str) -> tuple[bool, str]:
    """
    Weryfikuje nick i PIN,
    Zwraca (sukces, wiadomość)
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT pin FROM users WHERE username = ?",
        (username.strip().lower(),)
    ).fetchone()
    conn.close()

    if row is None:
        return False, "Nie ma takiego użytkownika."
    if row["pin"] != hash_pin(pin):
        return False, "Niepoprawny PIN."
    return True, f"Witaj, {username}!"

def user_exists(username: str) -> bool:
    """Sprawdza, czy użytkownik o danym nicku istnieje"""
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username.strip().lower(),)
    ).fetchone()
    conn.close()
    return row is not None
