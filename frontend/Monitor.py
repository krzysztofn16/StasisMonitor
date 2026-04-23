import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

import sys
import os

# Dodaj główny folder projektu do Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db import init_db
from backend.services.transactions import get_transactions
from backend.services.prices import get_price_history, get_latest_price
from backend.services.portfolio import get_portfolio_summary, get_portfolio_history
from backend.services.auth import get_current_user, show_auth_page, logout

# ── Inicjalizacja bazy przy każdym starcie ────────────────────────────────────
init_db()

# ── Konfiguracja strony ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSTI Monitor",
    page_icon="📊",
    layout="wide"
)

# ── Auth — jeśli nie zalogowany pokaż ekran logowania ────────────────────────
user_id = get_current_user()
if user_id is None:
    show_auth_page()
    st.stop()

# ── Sidebar — info o użytkowniku ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"👤 **{user_id}**")
    if st.button("wyloguj", use_container_width=True):
        logout()
    st.divider()
    st.markdown("[📝 Prześlij feedback](https://forms.google.com/)")
    st.markdown("[☕ Postaw kawę](https://buymeacoffee.com/)")

st.title("📊 MarketSTI Monitor")

# ── Pobierz dane ──────────────────────────────────────────────────────────────
transactions_df = get_transactions(user_id) #get_transactions("default")
latest_price, latest_date = get_latest_price("3965.n")

# ── Obsługa pustej bazy ───────────────────────────────────────────────────────
if transactions_df.empty:
    st.info("Nie masz jeszcze żadnych transakcji. Przejdź do strony **Transakcje** żeby dodać pierwszą, albo zaimportuj plik CSV.")
    st.stop()

# ── Oblicz statystyki ─────────────────────────────────────────────────────────
summary = get_portfolio_summary(transactions_df, latest_price)

# ── 4 metryki ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Wartość portfela",
    value=f"{summary['current_value']:,.2f} PLN"
)
col2.metric(
    label="Zysk / Strata",
    value=f"{summary['profit_pln']:,.2f} PLN",
    delta=f"{summary['profit_pct']:.2f}%"
)
col3.metric(
    label="Zainwestowano",
    value=f"{summary['total_invested']:,.2f} PLN"
)
col4.metric(
    label="Ostatnia wycena",
    value=f"{latest_price:.2f} PLN",
    delta=latest_date
)

st.divider()

# ── Wykres z przełącznikiem okresu ────────────────────────────────────────────
st.subheader("Wartość portfela w czasie")

period = st.radio(
    label="Okres",
    options=["1M", "3M", "6M", "1Y", "2Y", "5Y", "MAX"],
    index=1,          # domyślnie 3M
    horizontal=True
)

prices_df = get_price_history("3965.n", period=period)
history_df = get_portfolio_history(transactions_df, prices_df)

if not history_df.empty:
    fig = go.Figure()

    # Linia — zainwestowano (baseline)
    fig.add_trace(go.Scatter(
        x=history_df["date"],
        y=history_df["invested"],
        name="Zainwestowano",
        line=dict(color="#888888", width=2, dash="dot")
    ))

    # Linia — wartość portfela
    fig.add_trace(go.Scatter(
        x=history_df["date"],
        y=history_df["value"],
        name="Wartość portfela",
        line=dict(color="#2E75B6", width=2),
        fill="tonexty",
        fillcolor="rgba(39, 174, 96, 0.1)"
    ))

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Tabela podsumowania funduszu ──────────────────────────────────────────────
st.subheader("Podsumowanie")

summary_table = pd.DataFrame([{
    "Fundusz":           "Generali Stabilny Wzrost",
    "Jednostki":         f"{summary['units_held']:.4f}",
    "Śr. cena zakupu":   f"{summary['avg_buy_price']:.2f} PLN",
    "Aktualna cena":     f"{summary['latest_price']:.2f} PLN",
    "Wartość":           f"{summary['current_value']:,.2f} PLN",
    "Zysk / Strata":     f"{summary['profit_pln']:,.2f} PLN ({summary['profit_pct']:.2f}%)",
}])

st.dataframe(summary_table, use_container_width=True, hide_index=True)

# ── Eksport CSV ───────────────────────────────────────────────────────────────
st.divider()

csv = transactions_df.to_csv(index=False)
st.download_button(
    label="📥 Eksportuj transakcje CSV",
    data=csv,
    file_name="fund_tracker_backup.csv",
    mime="text/csv"
)