from backend.database.db import init_db

# Uruchom przy każdym starcie — bezpieczne bo używamy IF NOT EXISTS
init_db()