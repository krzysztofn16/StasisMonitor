import streamlit as st
import pandas as pd
import sys
import os

# Dodaj główny folder projektu do Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import init_db, get_all_funds
from backend.services.auth import get_current_user, show_auth_page, logout
from backend.services.notifications import get_user_alerts, create_alert, delete_alert, send_demo_notification
from backend.services.prices import get_latest_price

# ── Inicjalizacja ─────────────────────────────────────────────────────────────
init_db()

# ── Konfiguracja strony ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Powiadomienia - MarketSTI Monitor",
    page_icon="🔔",
    layout="wide"
)

# ── Auth ──────────────────────────────────────────────────────────────────────
user_id = get_current_user()
if user_id is None:
    show_auth_page()
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{user_id}**")
    if st.button("wyloguj", use_container_width=True):
        logout()
    st.divider()
    st.markdown("[📝 Prześlij feedback](https://forms.gle/uDh9U5EAzcZ2s3yP6)")
    st.markdown("[☕ Postaw kawę](https://buymeacoffee.com/monitorsti)")

st.title("🔔 Powiadomienia o funduszach")

st.markdown("""
Ustawiaj powiadomienia o cenach funduszów. Otrzymaj maila gdy:
- 📉 Cena spadnie poniżej określonego progu (kupno)
- 📈 Cena wzrośnie powyżej określonego progu (sprzedaż)
- 📊 Fundusz zanotuje znaczący spadek (okazja)
""")

# ── Sekcja: Nowe powiadomienie ────────────────────────────────────────────────
st.subheader("➕ Utwórz nowe powiadomienie")

all_funds = {f["code"]: f for f in get_all_funds()}
fund_codes = list(all_funds.keys())
fund_names = [all_funds[c]["name"] for c in fund_codes]

col1, col2 = st.columns(2)

with col1:
    selected_fund_idx = st.selectbox(
        "Wybierz fundusz",
        range(len(fund_names)),
        format_func=lambda x: fund_names[x]
    )
    selected_fund_code = fund_codes[selected_fund_idx]
    selected_fund = all_funds[selected_fund_code]
    
    # Get current price
    current_price, _ = get_latest_price(selected_fund["stooq_ticker"])
    st.info(f"📊 Aktualna cena: **{current_price:.2f} PLN**")

with col2:
    alert_type = st.radio(
        "Typ powiadomienia",
        ["📉 Cena spadnie poniżej", "📈 Cena wzrośnie powyżej", "📊 Znaczący spadek (drawback)"],
        format_func=lambda x: x
    )

# Alert type mapping
alert_type_map = {
    "📉 Cena spadnie poniżej": "BELOW",
    "📈 Cena wzrośnie powyżej": "ABOVE",
    "📊 Znaczący spadek (drawback)": "DRAWBACK"
}
alert_type_value = alert_type_map[alert_type]

col1, col2, col3 = st.columns(3)

with col1:
    email = st.text_input(
        "Twój email",
        value="investor@example.com",
        placeholder="mail@example.com"
    )

with col2:
    if alert_type_value in ["BELOW", "ABOVE"]:
        threshold_price = st.number_input(
            "Próg ceny (PLN)",
            min_value=0.01,
            value=current_price * 0.95 if alert_type_value == "BELOW" else current_price * 1.05,
            step=0.01
        )
    else:
        drawback_percent = st.number_input(
            "Spadek %",
            min_value=1.0,
            max_value=50.0,
            value=5.0,
            step=0.5,
            help="Powiadomienie gdy cena spadnie o X% od średniej"
        )

with col3:
    if st.button("🚀 Ustaw powiadomienie", use_container_width=True):
        # Create alert in database
        threshold = threshold_price if alert_type_value in ["BELOW", "ABOVE"] else None
        drawback = drawback_percent if alert_type_value == "DRAWBACK" else None
        
        success = create_alert(
            user_id=user_id,
            fund_code=selected_fund_code,
            alert_type=alert_type_value,
            email=email,
            threshold_price=threshold,
            drawback_percent=drawback
        )
        
        if success:
            # Send demo notification immediately
            send_demo_notification(
                email_to=email,
                fund_name=selected_fund["name"],
                alert_type=alert_type_value,
                current_price=current_price,
                threshold=threshold,
                drawback=drawback
            )
            
            st.success("✅ Powiadomienie ustawione! Wiadomość demo wysłana.")
            st.info(f"📧 Wiadomość wysłana na: {email}")
        else:
            st.error("❌ Błąd przy tworzeniu powiadomienia")

st.divider()

# ── Sekcja: Moje powiadomienia ────────────────────────────────────────────────
st.subheader("📋 Twoje powiadomienia")

alerts = get_user_alerts(user_id)

if alerts:
    # Create dataframe for display
    alert_rows = []
    for alert in alerts:
        if alert["alert_type"] == "BELOW":
            alert_desc = f"📉 Cena < {alert['threshold_price']:.2f} PLN"
        elif alert["alert_type"] == "ABOVE":
            alert_desc = f"📈 Cena > {alert['threshold_price']:.2f} PLN"
        else:
            alert_desc = f"📊 Spadek ≥ {alert['drawback_percent']:.1f}%"
        
        status = "✅ Aktywne" if alert["is_active"] else "⏸ Wznowione"
        
        alert_rows.append({
            "Fundusz": alert["fund_name"],
            "Powiadomienie": alert_desc,
            "Email": alert["email"],
            "Status": status,
            "id": alert["id"]
        })
    
    alerts_df = pd.DataFrame(alert_rows)
    
    # Display as table
    st.dataframe(
        alerts_df[["Fundusz", "Powiadomienie", "Email", "Status"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Delete buttons
    st.markdown("#### Zarządzaj powiadomieniami")
    cols = st.columns(len(alert_rows))
    
    for idx, (col, alert_row) in enumerate(zip(cols, alert_rows)):
        with col:
            if st.button(f"🗑 Usuń: {alert_row['Fundusz'][:15]}...", key=f"delete_{alert_row['id']}"):
                delete_alert(alert_row["id"])
                st.success("Powiadomienie usunięte")
                st.rerun()

else:
    st.info("📭 Nie masz jeszcze żadnych powiadomień. Utwórz jedno powyżej!")

st.divider()

# ── Info sekcja ───────────────────────────────────────────────────────────────
st.subheader("ℹ️ Jak to działa?")

with st.expander("📖 Wyjaśnienie typów powiadomień"):
    st.markdown("""
    **📉 Cena spadnie poniżej**
    - Idealny do kupna
    - Dostaniesz maila gdy cena osiągnie Twój próg
    - Przykład: Chcesz kupić gdy cena spadnie do 100 PLN
    
    **📈 Cena wzrośnie powyżej**
    - Idealny do sprzedaży
    - Dostaniesz maila gdy cena przekroczy Twój próg
    - Przykład: Chcesz sprzedać gdy cena wzrośnie do 150 PLN
    
    **📊 Znaczący spadek (drawback)**
    - Okazja inwestycyjna
    - Powiadamiamy gdy cena spadnie o X% od historycznej średniej
    - Mimic rzeczywistych anomalii ceny
    """)

with st.expander("⚙️ Tryb demo"):
    st.markdown("""
    Obecnie powiadomienia wysyłane są w **trybie demo**:
    - ✅ Zapisujemy powiadomienie w bazie
    - ✅ Wysyłamy demo maila natychmiast
    - 📝 Logi dostępne w: `data/notifications_log.txt`
    
    W produkcji powiadomienia będą wysyłane gdy cena spełni warunki!
    """)
